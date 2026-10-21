"""
CLI Tool: Evaluate Synthetic Dataset.
Independently inspects an exported CSV dataset directory and evaluates it against
real-world empirical reference benchmarks.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from synapse_simulator.evaluation.evaluator import DatasetEvaluator
from synapse_simulator.evaluation.reference_data import get_default_reference_catalog
from synapse_simulator.evaluation.report import EvaluationReportFormatter


def main():
    parser = argparse.ArgumentParser(description="SYNAPSE Phase 2 Synthetic Healthcare Data Evaluator")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="data/synthetic",
        help="Path to directory containing exported CSV files (default: data/synthetic)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="config/population/india_default_v1.yaml",
        help="Path to Population Profile YAML (default: config/population/india_default_v1.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for EVALUATION_REPORT.json and .md (defaults to dataset directory)",
    )

    args = parser.parse_args()
    dataset_dir = Path(args.dataset_dir)
    out_dir = Path(args.output_dir) if args.output_dir else dataset_dir

    if not dataset_dir.exists():
        print(f"Error: Dataset directory '{dataset_dir}' does not exist.")
        sys.exit(1)

    print("==================================================================")
    print("SYNAPSE Phase 2 — Synthetic Data Independent Evaluation Pipeline")
    print("==================================================================")
    print(f"Dataset Directory:   {dataset_dir.resolve()}")
    print(f"Population Profile:  {args.profile}")
    print(f"Output Directory:    {out_dir.resolve()}")
    print("==================================================================\n")

    catalog = get_default_reference_catalog(Path(args.profile))
    evaluator = DatasetEvaluator(dataset_dir=dataset_dir, reference_catalog=catalog)

    print("[1/2] Running multi-dimensional quantitative evaluation...")
    report = evaluator.evaluate_all()

    print("[2/2] Exporting evaluation artifacts...")
    json_path = out_dir / "EVALUATION_REPORT.json"
    md_path = out_dir / "EVALUATION_REPORT.md"
    EvaluationReportFormatter.save_json(report, json_path)
    EvaluationReportFormatter.save_markdown(report, md_path)

    print("\n------------------------------------------------------------------")
    print(f"EVALUATION COMPLETE — Overall Verdict: {report.overall_status.value}")
    print("------------------------------------------------------------------")
    print(f"  - Invariants Passed:   {report.invariants_passed}")
    print(f"  - Total Metrics:       {report.total_metrics}")
    print(f"  - PASS:                {report.passed_metrics}")
    print(f"  - WARNING:             {report.warning_metrics}")
    print(f"  - FAIL:                {report.failed_metrics}")
    print(f"  - UNVERIFIED:          {report.unverified_metrics}")
    print(f"  - NOT_APPLICABLE:      {report.not_applicable_metrics}")
    print(f"\nArtifacts generated:")
    print(f"  - JSON Report:     {json_path}")
    print(f"  - Markdown Report: {md_path}")
    print("==================================================================\n")

    if report.overall_status == report.overall_status.FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
