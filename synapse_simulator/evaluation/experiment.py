"""
Experiment Runner and Manifest Management for SYNAPSE Phase 2.
Supports deterministic generation, progressive cohort scaling, multi-seed Monte Carlo assessment,
and execution manifest preservation (RUN_MANIFEST.json).
"""

import hashlib
import json
import os
import resource
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from synapse_simulator.core.ids import reset as reset_ids
from synapse_simulator.population.loader import load_population_profile
from synapse_simulator.modules.loader import load_clinical_module
from synapse_simulator.modules.engine import ClinicalModuleRunner
from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.exporter.csv_exporter import CSVExporter
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.datagen.master_data import MasterDataSnapshot
from synapse_simulator.evaluation.evaluator import DatasetEvaluator, EvaluationReport, MetricStatus
from synapse_simulator.evaluation.report import EvaluationReportFormatter
from synapse_simulator.evaluation.reference_data import ReferenceCatalog, get_default_reference_catalog


DEFAULT_PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "population" / "india_default_v1.yaml"
DEFAULT_MODULES_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "modules"


class ExperimentConfig(BaseModel):
    """Configuration specification for a reproducible simulation experiment."""
    cohort_size: int = 20
    seed: int = 42
    observation_start: datetime = datetime(2024, 1, 1)
    observation_end: datetime = datetime(2024, 1, 1) + timedelta(days=720)  # Exactly 720 days (24 months)
    timestep_days: int = 7
    profile_path: Path = DEFAULT_PROFILE_PATH
    modules_dir: Path = DEFAULT_MODULES_DIR
    output_dir: Path = Path("data/experiments/run_default")
    enable_evaluator: bool = True
    enable_background_mortality: bool = True


def get_git_revision_hash() -> str:
    """Retrieve current git revision hash for manifest auditability."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("ascii").strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def get_memory_usage_mb() -> float:
    """Retrieve peak resident set size (RSS) in megabytes."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # On macOS, ru_maxrss is in bytes; on Linux, in kilobytes
        import sys
        if sys.platform == "darwin":
            return round(usage.ru_maxrss / (1024.0 * 1024.0), 2)
        else:
            return round(usage.ru_maxrss / 1024.0, 2)
    except Exception:
        return 0.0


class ExperimentRunner:
    """Executes controlled generation and independent evaluation experiments."""

    @staticmethod
    def generate_cohort(config: ExperimentConfig) -> Tuple[Path, Dict[str, Any]]:
        """Run deterministic longitudinal generation and export CSV artifacts.
        Returns target directory and execution telemetry.
        """
        t0 = time.perf_counter()
        reset_ids(config.seed)

        profile = load_population_profile(config.profile_path)
        kb = MedicalKnowledgeBase()
        kb.load(enable_pubmed=False)

        import random
        rng = random.Random(config.seed)
        pat_gen = PatientProfileGenerator(kb, rng, population_profile=profile)
        sampler = pat_gen.sampler

        modules = [
            load_clinical_module(config.modules_dir / "hypertension.yaml"),
            load_clinical_module(config.modules_dir / "diabetes_t2.yaml"),
            load_clinical_module(config.modules_dir / "urti.yaml"),
        ]
        runner = ClinicalModuleRunner(modules, base_seed=config.seed)

        obs_start = config.observation_start
        obs_end = config.observation_end
        timestep = timedelta(days=config.timestep_days)

        # 1. Spawn patients
        patients = {}
        for _ in range(config.cohort_size):
            p = pat_gen.generate_patient(observation_start=obs_start)
            patients[p.patient_id] = p
            runner.initialize_patient(p)

        # 2. Step discrete-event simulation
        sm = StateManager()
        curr_time = obs_start
        total_actions = 0

        while curr_time < obs_end:
            for p in patients.values():
                if p.is_alive:
                    # Evaluate background all-cause life-table mortality (Census SRS 2016-2020)
                    if config.enable_background_mortality and sampler:
                        qx = sampler.get_annual_mortality_rate(p.age, p.gender)
                        if qx > 0.0:
                            step_prob = 1.0 - (1.0 - qx) ** (config.timestep_days / 365.25)
                            p_rng = runner.get_patient_rng(p.patient_id)
                            if p_rng.random() < step_prob:
                                p.is_alive = False
                                p.death_date = curr_time
                                from synapse_simulator.core.ids import new_id
                                runner.longitudinal_deaths.append({
                                    "death_id": new_id("dth-", 8),
                                    "patient_id": p.patient_id,
                                    "death_date": curr_time,
                                    "cause_code": "R99",
                                    "cause_name": "All-cause natural mortality (SRS Life Table)",
                                    "is_premature": p.age < 70,
                                })
                                continue

                    emitted = runner.step_patient(p, curr_time, timestep)
                    total_actions += len(emitted)
                    for act in emitted:
                        if act.target_entity_table == "clinical.encounters":
                            st_dt = datetime.fromisoformat(act.payload["timestamp"])
                            et_dt = st_dt + timedelta(minutes=20)
                            sm.set_entity_state("clinical.encounters", act.target_entity_id, {
                                "encounter_id": act.target_entity_id,
                                "patient_id": act.payload["patient_id"],
                                "journey_id": f"jny-{act.payload['patient_id']}",
                                "start_time": st_dt.isoformat(),
                                "end_time": et_dt.isoformat(),
                                "status": "Closed",
                            })
                        elif act.target_entity_table == "clinical.consultations":
                            if act.action_type == "CONSULTATION_RESOLVE":
                                # Mark consultation as resolved
                                for c_id, c_data in sm._store.get("clinical.consultations", {}).items():
                                    if (
                                        c_data.get("patient_id") == act.payload.get("patient_id")
                                        and c_data.get("condition_code") == act.payload.get("condition_code")
                                        and c_data.get("status") == "Active"
                                    ):
                                        c_data["status"] = "Resolved"
                                        c_data["resolved_time"] = act.payload.get("resolved_time")
                            else:
                                sm.set_entity_state("clinical.consultations", act.target_entity_id, {
                                    "consultation_id": act.target_entity_id,
                                    "patient_id": act.payload["patient_id"],
                                    "encounter_id": act.payload["encounter_id"],
                                    "condition_code": act.payload["condition_code"],
                                    "diagnosis_name": act.payload["condition_name"],
                                    "status": act.payload.get("status", "Active"),
                                    "is_baseline": act.payload.get("is_baseline", False),
                                })
                        elif act.target_entity_table == "pharmacy.prescriptions":
                            sm.set_entity_state("pharmacy.prescriptions", act.target_entity_id, {
                                "prescription_id": act.target_entity_id,
                                "patient_id": act.payload["patient_id"],
                                "encounter_id": act.payload.get("encounter_id", ""),
                                "drug_name": act.payload["drug_name"],
                                "dosage": act.payload["dosage"],
                                "frequency": act.payload["frequency"],
                                "status": "Dispensed",
                            })
            curr_time += timestep

        sim_duration = time.perf_counter() - t0

        # 3. Export CSV files
        t_export_start = time.perf_counter()
        out_dir = config.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        exporter = CSVExporter(
            state_manager=sm,
            master_data=MasterDataSnapshot(),
            patient_contexts=patients,
            committed_events=[],
            journeys=[],
            module_runner=runner,
            metrics={"random_seed": config.seed, "final_simulation_time": obs_end.isoformat()},
            output_dir=out_dir / "phase2",
        )
        exported = exporter.export_simplified_dataset(target_dir=out_dir)
        export_duration = time.perf_counter() - t_export_start

        total_duration = time.perf_counter() - t0

        telemetry = {
            "simulation_seconds": round(sim_duration, 3),
            "export_seconds": round(export_duration, 3),
            "total_generation_seconds": round(total_duration, 3),
            "total_actions_emitted": total_actions,
            "exported_file_count": len(exported),
            "peak_memory_mb": get_memory_usage_mb(),
        }

        return out_dir, telemetry

    @staticmethod
    def run_experiment(config: ExperimentConfig) -> Dict[str, Any]:
        """Execute complete generation + evaluation experiment and write RUN_MANIFEST.json."""
        out_dir, gen_telemetry = ExperimentRunner.generate_cohort(config)

        t_eval_start = time.perf_counter()
        catalog = ReferenceCatalog(load_population_profile(config.profile_path))
        evaluator = DatasetEvaluator(
            dataset_dir=out_dir,
            reference_catalog=catalog,
            observation_start=config.observation_start,
            observation_end=config.observation_end,
        )
        report = evaluator.evaluate_all()
        eval_duration = round(time.perf_counter() - t_eval_start, 3)

        # Save evaluation reports
        EvaluationReportFormatter.save_json(report, out_dir / "EVALUATION_REPORT.json")
        EvaluationReportFormatter.save_markdown(report, out_dir / "EVALUATION_REPORT.md")

        # Build execution manifest
        manifest = {
            "manifest_version": "1.0.0",
            "run_id": f"exp-seed{config.seed}-n{config.cohort_size}-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "git_commit": get_git_revision_hash(),
            "configuration": {
                "cohort_size": config.cohort_size,
                "seed": config.seed,
                "observation_start": config.observation_start.isoformat(),
                "observation_end": config.observation_end.isoformat(),
                "timestep_days": config.timestep_days,
                "profile_path": str(config.profile_path),
                "output_dir": str(out_dir),
            },
            "performance_telemetry": {
                **gen_telemetry,
                "evaluation_seconds": eval_duration,
            },
            "evaluation_verdict": {
                "overall_status": report.overall_status.value,
                "invariants_passed": report.invariants_passed,
                "total_metrics": report.total_metrics,
                "passed_metrics": report.passed_metrics,
                "warning_metrics": report.warning_metrics,
                "failed_metrics": report.failed_metrics,
                "unverified_metrics": report.unverified_metrics,
            },
        }

        with open(out_dir / "RUN_MANIFEST.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return {
            "output_dir": out_dir,
            "manifest": manifest,
            "report": report,
        }

    @staticmethod
    def run_multi_seed_experiment(
        seeds: List[int],
        cohort_size: int,
        base_output_dir: Path,
        profile_path: Path = DEFAULT_PROFILE_PATH,
    ) -> Dict[str, Any]:
        """Execute multi-seed Monte Carlo experiment to assess sampling variance vs model bias.
        
        Calculates:
        - Mean synthetic estimate across seeds
        - Standard deviation (sigma) across seeds
        - Monte Carlo standard error (SE = sigma / sqrt(S))
        """
        import math
        runs = []
        metric_series: Dict[str, List[float]] = {}
        metric_refs: Dict[str, Optional[float]] = {}
        metric_names: Dict[str, str] = {}

        for seed in seeds:
            seed_dir = base_output_dir / f"seed_{seed}"
            cfg = ExperimentConfig(
                cohort_size=cohort_size,
                seed=seed,
                output_dir=seed_dir,
                profile_path=profile_path,
            )
            res = ExperimentRunner.run_experiment(cfg)
            runs.append(res)
            rep: EvaluationReport = res["report"]
            for m in rep.metrics:
                metric_series.setdefault(m.metric_id, []).append(m.synthetic_estimate)
                metric_refs[m.metric_id] = m.reference_estimate
                metric_names[m.metric_id] = m.metric_name

        # Calculate Monte Carlo statistics
        mc_summary: Dict[str, Dict[str, Any]] = {}
        s_count = len(seeds)

        for mid, values in metric_series.items():
            mean_val = sum(values) / s_count
            if s_count > 1:
                variance = sum((x - mean_val) ** 2 for x in values) / (s_count - 1)
                std_dev = math.sqrt(variance)
                se = std_dev / math.sqrt(s_count)
            else:
                std_dev = 0.0
                se = 0.0

            ref_val = metric_refs.get(mid)
            bias = round(mean_val - ref_val, 4) if ref_val is not None else None

            mc_summary[mid] = {
                "metric_name": metric_names[mid],
                "seeds_evaluated": seeds,
                "values": [round(v, 4) for v in values],
                "mean": round(mean_val, 4),
                "std_dev": round(std_dev, 4),
                "mc_standard_error": round(se, 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "reference_estimate": ref_val,
                "estimated_bias": bias,
            }

        # Write multi-seed summary files
        base_output_dir.mkdir(parents=True, exist_ok=True)
        summary_json_path = base_output_dir / "MULTI_SEED_EXPERIMENT_SUMMARY.json"
        with open(summary_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "cohort_size": cohort_size,
                "seed_count": s_count,
                "seeds": seeds,
                "timestamp": datetime.now().isoformat(),
                "metrics_summary": mc_summary,
            }, f, indent=2)

        # Markdown report
        lines = [
            f"# Multi-Seed Monte Carlo Evaluation Summary (N={cohort_size:,}, {s_count} Seeds)",
            "",
            f"**Seeds Evaluated:** `{seeds}`  ",
            f"**Timestamp:** `{datetime.now().isoformat()}`  ",
            "",
            "This analysis distinguishes random stochastic sampling variability from systematic structural model bias.",
            "",
            "| Metric ID | Metric Name | Reference | Mean Synthetic | Std Dev (σ) | Monte Carlo SE | Min | Max | Systematic Bias |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        for mid, s in mc_summary.items():
            ref_str = f"{s['reference_estimate']:.2f}" if s["reference_estimate"] is not None else "—"
            bias_str = f"{s['estimated_bias']:+.2f}" if s["estimated_bias"] is not None else "—"
            lines.append(
                f"| `{mid}` | {s['metric_name']} | {ref_str} | **{s['mean']:.2f}** | {s['std_dev']:.2f} | {s['mc_standard_error']:.2f} | {s['min']:.2f} | {s['max']:.2f} | {bias_str} |"
            )

        summary_md_path = base_output_dir / "MULTI_SEED_EXPERIMENT_SUMMARY.md"
        with open(summary_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return {
            "summary_json": summary_json_path,
            "summary_md": summary_md_path,
            "metrics_summary": mc_summary,
        }
