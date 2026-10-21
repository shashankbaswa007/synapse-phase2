"""
CLI Script: Generate and Evaluate Reproducible LASI External Evaluation Cohort.

Generates a dedicated synthetic cohort with >= 500 older adults (age >= 45),
exports CSV datasets, records cryptographic SHA-256 manifests, and executes
the LASI external evaluator using the verified LASI Wave 1 sample fixture.
"""

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from synapse_simulator.evaluation.experiment import (
    ExperimentRunner,
    ExperimentConfig,
    DEFAULT_PROFILE_PATH,
    get_git_revision_hash,
)
from synapse_simulator.evaluation.lasi.ingestor import LasiDataIngestor
from synapse_simulator.evaluation.lasi.evaluator import (
    LasiExternalEvaluator,
    LasiEvaluationReportFormatter,
)


def compute_file_sha256(filepath: Path) -> str:
    """Compute hex SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def audit_cohort_demographics(dataset_dir: Path) -> Dict[str, Any]:
    """Inspect exported patients.csv and summarize age and sex composition."""
    patients_file = dataset_dir / "patients.csv"
    if not patients_file.exists():
        raise FileNotFoundError(f"Missing {patients_file}")

    total_patients = 0
    older_adults = 0
    females_older = 0
    males_older = 0
    age_bands = {"0-14": 0, "15-24": 0, "25-44": 0, "45-64": 0, "65+": 0}

    with open(patients_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_patients += 1
            age = float(row.get("age", 0.0))
            gender = row.get("gender", "").capitalize()

            if age < 15:
                age_bands["0-14"] += 1
            elif age < 25:
                age_bands["15-24"] += 1
            elif age < 45:
                age_bands["25-44"] += 1
            elif age < 65:
                age_bands["45-64"] += 1
            else:
                age_bands["65+"] += 1

            if age >= 45.0:
                older_adults += 1
                if gender == "Female":
                    females_older += 1
                elif gender == "Male":
                    males_older += 1

    pct_older = (older_adults / total_patients * 100) if total_patients > 0 else 0.0
    pct_female_older = (females_older / older_adults * 100) if older_adults > 0 else 0.0

    return {
        "total_patients": total_patients,
        "older_adults_count": older_adults,
        "older_adults_pct": round(pct_older, 2),
        "older_adults_female_count": females_older,
        "older_adults_male_count": males_older,
        "older_adults_female_pct": round(pct_female_older, 2),
        "age_distribution": age_bands,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate and Evaluate Reproducible LASI Synthetic Cohort")
    parser.add_argument("--patients", type=int, default=2200, help="Total synthetic population to simulate (default: 2200 to yield >=500 older adults)")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default="data/evaluation/lasi_cohort_500/seed_42", help="Dedicated output directory")
    parser.add_argument("--profile", type=str, default=str(DEFAULT_PROFILE_PATH), help="Population profile YAML path")
    parser.add_argument("--fixture", type=str, default="data/evaluation/fixtures/lasi_wave1_sample_fixture.csv", help="LASI reference fixture path")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile_path = Path(args.profile)
    fixture_path = Path(args.fixture)

    print("==================================================================")
    print("SYNAPSE Phase 2 — LASI Evaluation Cohort Generation & Audit")
    print("==================================================================")
    print(f"Target Population Size:   {args.patients}")
    print(f"Fixed Random Seed:        {args.seed}")
    print(f"Population Profile:       {profile_path}")
    print(f"Output Directory:         {out_dir}")
    print(f"Reference Fixture:        {fixture_path}")
    print("==================================================================\n")

    # 1. Run simulation cohort generation
    print("[1/4] Running simulation and exporting longitudinal CSVs...")
    cfg = ExperimentConfig(
        cohort_size=args.patients,
        seed=args.seed,
        profile_path=profile_path,
        output_dir=out_dir,
    )
    target_dir, telemetry = ExperimentRunner.generate_cohort(cfg)
    print(f"      Generation finished in {telemetry['total_generation_seconds']}s (Sim: {telemetry['simulation_seconds']}s, Export: {telemetry['export_seconds']}s)")
    print(f"      Peak Memory: {telemetry['peak_memory_mb']} MB")

    # 2. Cryptographic file hashing
    print("[2/4] Generating cryptographic file manifest (SHA-256)...")
    file_hashes: Dict[str, str] = {}
    csv_files = sorted(list(out_dir.glob("*.csv")))
    for csv_path in csv_files:
        file_hashes[csv_path.name] = compute_file_sha256(csv_path)

    # 3. Demographic audit of exported cohort
    demo_audit = audit_cohort_demographics(out_dir)
    print(f"      Total Patients:        {demo_audit['total_patients']}")
    print(f"      Older Adults (>=45):   {demo_audit['older_adults_count']} ({demo_audit['older_adults_pct']}%)")
    print(f"      Female Older Adults:   {demo_audit['older_adults_female_count']} ({demo_audit['older_adults_female_pct']}%)")
    print(f"      Age Band Breakdown:    {demo_audit['age_distribution']}")

    if demo_audit["older_adults_count"] < 500:
        print(f"\n[WARNING] Older adults count ({demo_audit['older_adults_count']}) is less than minimum requirement of 500!")
    else:
        print(f"      [OK] Minimum sample gate (>= 500 older adults) satisfied: {demo_audit['older_adults_count']} >= 500.")

    # 4. Execute LASI External Evaluator
    print("[3/4] Ingesting reference fixture and executing LasiExternalEvaluator...")
    ingestor = LasiDataIngestor(source_path=fixture_path)
    records, quality_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=out_dir,
        reference_records=records,
        quality_report=quality_report,
    )
    lasi_report = evaluator.evaluate()

    # Save LASI evaluation report artifacts
    md_path = out_dir / "LASI_EVALUATION_REPORT.md"
    json_path = out_dir / "LASI_EVALUATION_REPORT.json"
    LasiEvaluationReportFormatter.save_markdown(lasi_report, md_path)
    LasiEvaluationReportFormatter.save_json(lasi_report, json_path)

    print(f"      LASI Evaluation Report written to: {md_path}")
    print(f"      LASI Evaluation JSON written to:   {json_path}")
    print(f"      Overall Gate Status:              {lasi_report.overall_gate_status.value}")

    # 5. Write RUN_MANIFEST.json
    print("[4/4] Writing RUN_MANIFEST.json...")
    manifest = {
        "manifest_version": "1.0.0",
        "run_id": f"lasi-eval-seed{args.seed}-n{args.patients}-{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "git_commit": get_git_revision_hash(),
        "simulation_parameters": {
            "total_cohort_size": args.patients,
            "seed": args.seed,
            "observation_window_days": 720,
            "observation_start": cfg.observation_start.isoformat(),
            "observation_end": cfg.observation_end.isoformat(),
            "profile_path": str(profile_path),
            "modules_dir": str(cfg.modules_dir),
            "background_mortality_enabled": True,
        },
        "demographic_audit": demo_audit,
        "performance_telemetry": telemetry,
        "exported_file_hashes_sha256": file_hashes,
        "lasi_evaluation": {
            "reference_file": str(fixture_path),
            "reference_file_sha256": quality_report.file_sha256,
            "reference_source_type": quality_report.data_source_type.value,
            "overall_gate_status": lasi_report.overall_gate_status.value,
            "calibration_leakage_veto": lasi_report.calibration_leakage_veto,
            "metric_results": [
                {
                    "metric_id": m.metric_id,
                    "metric_name": m.metric_name,
                    "population": m.population,
                    "synthetic_n": m.synthetic_n,
                    "reference_n": m.reference_n,
                    "reference_effective_n": m.reference_effective_n,
                    "synthetic_estimate": m.synthetic_estimate,
                    "reference_estimate": m.reference_estimate,
                    "difference": m.difference,
                    "status": m.status.value,
                }
                for m in lasi_report.metrics
            ],
        },
    }

    manifest_path = out_dir / "RUN_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"      RUN_MANIFEST written to: {manifest_path}")
    print("\n==================================================================")
    print("LASI EVALUATION COHORT PREPARATION COMPLETE")
    print(f"Overall Gate Verdict: {lasi_report.overall_gate_status.value}")
    print("==================================================================")


if __name__ == "__main__":
    main()
