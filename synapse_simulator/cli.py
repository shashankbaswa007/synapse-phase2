"""
CLI Entry Point for SYNAPSE Synthetic Hospital Simulator.
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="SYNAPSE Synthetic Hospital Simulation CLI")
    parser.add_argument("--patients", type=int, default=20, help="Number of synthetic patient journeys to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="data/synthetic", help="Directory path to save synthetic CSV dataset")
    args = parser.parse_args()

    from generate_synthetic_data import run_data_generation
    run_data_generation(patient_count=args.patients, seed=args.seed, output_dir=args.output)


if __name__ == "__main__":
    main()

