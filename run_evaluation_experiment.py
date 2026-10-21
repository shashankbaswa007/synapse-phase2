"""
CLI Tool: Run Controlled Synthetic Data Experiment.
Generates deterministic synthetic cohort, executes independent evaluation,
and preserves execution manifests (RUN_MANIFEST.json).
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from synapse_simulator.evaluation.experiment import (
    ExperimentRunner,
    ExperimentConfig,
    DEFAULT_PROFILE_PATH,
    DEFAULT_MODULES_DIR,
)


def main():
    parser = argparse.ArgumentParser(description="SYNAPSE Phase 2 Experiment Runner")
    parser.add_argument("--patients", type=int, default=20, help="Number of synthetic patients (default: 20)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--seeds", type=str, default=None, help="Comma-separated list of seeds for Monte Carlo evaluation (e.g. 42,101,202)")
    parser.add_argument("--output-dir", type=str, default="data/experiments/baseline_run", help="Output directory")
    parser.add_argument("--profile", type=str, default=str(DEFAULT_PROFILE_PATH), help="Population profile path")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)

    if args.seeds:
        seed_list = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
        print("==================================================================")
        print(f"SYNAPSE Phase 2 — Multi-Seed Monte Carlo Experiment ({len(seed_list)} Seeds)")
        print("==================================================================")
        print(f"Cohort Size:     {args.patients}")
        print(f"Seeds:           {seed_list}")
        print(f"Output Base:     {out_dir}")
        print("==================================================================\n")

        res = ExperimentRunner.run_multi_seed_experiment(
            seeds=seed_list,
            cohort_size=args.patients,
            base_output_dir=out_dir,
            profile_path=Path(args.profile),
        )
        print(f"\nMulti-Seed Monte Carlo evaluation completed:")
        print(f"  - Summary JSON: {res['summary_json']}")
        print(f"  - Summary MD:   {res['summary_md']}")
    else:
        print("==================================================================")
        print("SYNAPSE Phase 2 — Single Cohort Experiment Runner")
        print("==================================================================")
        print(f"Cohort Size:     {args.patients}")
        print(f"Random Seed:     {args.seed}")
        print(f"Output Dir:      {out_dir}")
        print("==================================================================\n")

        config = ExperimentConfig(
            cohort_size=args.patients,
            seed=args.seed,
            output_dir=out_dir,
            profile_path=Path(args.profile),
        )
        res = ExperimentRunner.run_experiment(config)
        verdict = res["manifest"]["evaluation_verdict"]
        print(f"\nExperiment execution complete:")
        print(f"  - Output Dir:     {res['output_dir']}")
        print(f"  - Overall Status: {verdict['overall_status']}")
        print(f"  - Invariants OK:  {verdict['invariants_passed']}")
        print(f"  - Total Metrics:  {verdict['total_metrics']} (Pass: {verdict['passed_metrics']}, Warn: {verdict['warning_metrics']}, Fail: {verdict['failed_metrics']})")


if __name__ == "__main__":
    main()
