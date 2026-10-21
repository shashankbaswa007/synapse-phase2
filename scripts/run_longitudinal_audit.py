"""
Multi-Scale Multi-Seed Longitudinal Trajectory Experiment Runner
Runs 5 seeds (42, 101, 202, 303, 404) across N=100, 250, 500.
Generates full synthetic datasets, runs independent evaluations,
computes summary statistics, and saves data/experiments/longitudinal_trajectories/LONGITUDINAL_TRAJECTORY_AUDIT.json.
"""

import json
import math
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from synapse_simulator.evaluation.experiment import (
    ExperimentConfig,
    ExperimentRunner,
    DEFAULT_PROFILE_PATH,
)

SEEDS = [42, 101, 202, 303, 404]
COHORT_SIZES = [100, 250, 500]
BASE_DIR = PROJECT_ROOT / "data" / "experiments" / "longitudinal_trajectories"

def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for n in COHORT_SIZES:
        print(f"\n=======================================================")
        print(f"Running Cohort Size N={n} across 5 seeds: {SEEDS}")
        print(f"=======================================================")
        runs_list = []
        metric_series = {}

        for seed in SEEDS:
            t0 = time.time()
            seed_dir = BASE_DIR / f"n{n}_s{seed}"
            cfg = ExperimentConfig(
                cohort_size=n,
                seed=seed,
                output_dir=seed_dir,
                profile_path=DEFAULT_PROFILE_PATH,
            )
            res = ExperimentRunner.run_experiment(cfg)
            rep = res["report"]
            elapsed = time.time() - t0

            # Extract metrics
            metric_map = {m.metric_id: m for m in rep.metrics}

            enc_per_py = metric_map["long_encounters_per_pt_year"].synthetic_estimate
            inter_enc = metric_map["long_inter_encounter_interval_days"].synthetic_estimate
            mort_res = metric_map["long_crude_mortality_rate"]
            mort_rate = mort_res.synthetic_estimate
            mort_diag = mort_res.acceptance_threshold or {}
            deaths_count = mort_diag.get("deaths_count", mort_res.numerator)
            censored_pt = mort_diag.get("patient_years", mort_res.denominator)
            cause_breakdown = mort_diag.get("cause_breakdown", {})

            intens_res = metric_map["long_treatment_intensification_rate"]
            intens_rate = intens_res.synthetic_estimate
            intens_diag = intens_res.acceptance_threshold or {}

            comp_rate = metric_map["long_chronic_complication_rate"].synthetic_estimate

            htn_res = metric_map["prev_hypertension_adults"]
            htn_period = htn_res.synthetic_estimate
            htn_base = (htn_res.acceptance_threshold or {}).get("baseline_point_prevalence_pct", 0.0)

            t2d_res = metric_map["prev_diabetes_t2_adults"]
            t2d_prev = t2d_res.synthetic_estimate

            run_entry = {
                "seed": seed,
                "cohort_size": n,
                "invariants_passed": res["manifest"]["evaluation_verdict"]["invariants_passed"],
                "elapsed_seconds": round(elapsed, 2),
                "metrics": {
                    "long_encounters_per_pt_year": enc_per_py,
                    "long_inter_encounter_interval_days": inter_enc,
                    "long_crude_mortality_rate": mort_rate,
                    "long_deaths_count": deaths_count,
                    "long_censored_pt_years": censored_pt,
                    "long_treatment_intensification_rate": intens_rate,
                    "long_chronic_complication_rate": comp_rate,
                    "prev_htn_baseline": htn_base,
                    "prev_htn_period": htn_period,
                    "prev_t2d_adults": t2d_prev,
                },
                "diagnostics": {
                    "cause_breakdown": cause_breakdown,
                    "htn_intensified_pct": intens_diag.get("htn_intensified_pct"),
                    "t2d_intensified_pct": intens_diag.get("t2d_intensified_pct"),
                    "person_years_lost_to_death": mort_diag.get("person_years_lost_to_death"),
                }
            }
            runs_list.append(run_entry)

            for k, val in run_entry["metrics"].items():
                metric_series.setdefault(k, []).append(val)

            print(f"  Seed {seed:3d}: Deaths={deaths_count:2d} (Causes: {cause_breakdown}), "
                  f"Pt-Yrs={censored_pt:6.1f}, Intensification={intens_rate*100:.1f}%, "
                  f"Complications={comp_rate*100:.2f}%, Status={res['manifest']['evaluation_verdict']['overall_status']} ({elapsed:.1f}s)")

        # Compute summary
        summary = {}
        for k, values in metric_series.items():
            s_count = len(values)
            mean_v = sum(values) / s_count
            var_v = sum((x - mean_v) ** 2 for x in values) / (s_count - 1) if s_count > 1 else 0.0
            std_v = math.sqrt(var_v)
            summary[k] = {
                "mean": round(mean_v, 4),
                "std": round(std_v, 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
            }

        results[f"n{n}"] = {
            "cohort_size": n,
            "seeds": SEEDS,
            "runs": runs_list,
            "summary": summary,
        }

    out_file = BASE_DIR / "LONGITUDINAL_TRAJECTORY_AUDIT.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n=======================================================")
    print(f"Audit Experiment Complete! Manifest saved to: {out_file}")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
