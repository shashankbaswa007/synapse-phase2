"""
Regression and Integration Tests for generate_synthetic_data.py.

Verifies:
1. Default invocation routes to the canonical Synthea-inspired Phase 2 longitudinal pipeline (ExperimentRunner).
2. HospitalSimulator is NOT called unless mode='hospital' is explicitly passed.
3. Output directory receives longitudinal CSVs including community assessment and BP reading layers.
4. Determinism: identical random seed produces bit-for-bit identical outputs.
5. Stochastic divergence: distinct random seeds yield distinct outputs.
6. CLI entry point options (--patients, --seed, --days, --output-dir, --mode) work as intended.
"""

import csv
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from generate_synthetic_data import run_data_generation, main
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.evaluation.experiment import ExperimentRunner


def compute_dir_hashes(dir_path: Path) -> dict:
    """Compute sha256 checksums for all CSV files in directory."""
    hashes = {}
    for p in sorted(dir_path.glob("*.csv")):
        with open(p, "rb") as f:
            hashes[p.name] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def test_default_invokes_longitudinal_pipeline_not_hospital(tmp_path):
    """TEST 1: Calling run_data_generation with defaults must invoke ExperimentRunner, not HospitalSimulator."""
    out_dir = tmp_path / "longitudinal_default"

    with patch.object(HospitalSimulator, "__init__", side_effect=AssertionError("HospitalSimulator should NOT be called!")):
        with patch.object(ExperimentRunner, "generate_cohort", wraps=ExperimentRunner.generate_cohort) as mock_gen:
            published_path = run_data_generation(
                patient_count=4,
                seed=42,
                output_dir=str(out_dir),
                observation_days=90,
                run_evaluation=False,
            )

            assert mock_gen.called, "ExperimentRunner.generate_cohort was not invoked!"
            assert published_path == out_dir

    # Check that canonical longitudinal and community assessment tables exist
    assert (out_dir / "patients.csv").exists()
    assert (out_dir / "conditions.csv").exists()
    assert (out_dir / "medications.csv").exists()
    assert (out_dir / "community_assessments.csv").exists()
    assert (out_dir / "community_bp_readings.csv").exists()
    assert (out_dir / "DATASET_MANIFEST.json").exists()
    assert (out_dir / "RUN_MANIFEST.json").exists()

    # Verify manifest architecture statement
    with open(out_dir / "RUN_MANIFEST.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert "Synthea-Inspired Longitudinal" in manifest.get("architecture", "")
    assert manifest["simulation_parameters"]["total_cohort_size"] == 4
    assert manifest["simulation_parameters"]["seed"] == 42
    assert manifest["simulation_parameters"]["observation_window_days"] == 90


def test_reproducibility_with_seed(tmp_path):
    """TEST 2: Same seed produces bit-for-bit identical outputs; different seed diverges."""
    dir_seed42_a = tmp_path / "seed42_a"
    dir_seed42_b = tmp_path / "seed42_b"
    dir_seed99 = tmp_path / "seed99"

    run_data_generation(patient_count=5, seed=42, output_dir=str(dir_seed42_a), observation_days=60, run_evaluation=False)
    run_data_generation(patient_count=5, seed=42, output_dir=str(dir_seed42_b), observation_days=60, run_evaluation=False)
    run_data_generation(patient_count=5, seed=99, output_dir=str(dir_seed99), observation_days=60, run_evaluation=False)

    hashes_a = compute_dir_hashes(dir_seed42_a)
    hashes_b = compute_dir_hashes(dir_seed42_b)
    hashes_99 = compute_dir_hashes(dir_seed99)

    assert len(hashes_a) > 0
    # Bit-for-bit identical for same seed
    assert hashes_a == hashes_b, "Identical seed did not produce identical CSV file hashes!"

    # Divergence for different seed
    assert hashes_a["patients.csv"] != hashes_99["patients.csv"], "Different seeds must produce different patient hashes!"


def test_configurable_observation_window_and_demographics(tmp_path):
    """TEST 3: Configurable observation window and demographic auditing."""
    out_dir = tmp_path / "custom_window"
    run_data_generation(
        patient_count=6,
        seed=42,
        output_dir=str(out_dir),
        observation_days=180,
        run_evaluation=True,
    )

    with open(out_dir / "RUN_MANIFEST.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["simulation_parameters"]["observation_window_days"] == 180
    demo = manifest["demographic_audit"]
    assert demo["total_patients"] == 6
    assert (out_dir / "EVALUATION_REPORT.json").exists()
    assert (out_dir / "EVALUATION_REPORT.md").exists()


def test_legacy_hospital_mode_explicit(tmp_path):
    """TEST 4: Explicit mode='hospital' invokes HospitalSimulator for backward compatibility."""
    out_dir = tmp_path / "legacy_hospital"

    with patch("generate_synthetic_data.HospitalSimulator", wraps=HospitalSimulator) as mock_hosp:
        run_data_generation(
            patient_count=3,
            seed=42,
            output_dir=str(out_dir),
            mode="hospital",
        )
        assert mock_hosp.called, "HospitalSimulator was not invoked when mode='hospital' was explicitly set!"

    assert (out_dir / "patients.csv").exists()
    assert (out_dir / "DATASET_MANIFEST.json").exists()


def test_cli_invocation_via_main(tmp_path, monkeypatch):
    """TEST 5: CLI main() parses arguments and invokes longitudinal pipeline."""
    out_dir = tmp_path / "cli_output"
    test_args = [
        "generate_synthetic_data.py",
        "--patients", "3",
        "--seed", "77",
        "--days", "90",
        "--output-dir", str(out_dir),
        "--no-eval",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    main()

    assert (out_dir / "patients.csv").exists()
    assert (out_dir / "community_assessments.csv").exists()
    with open(out_dir / "RUN_MANIFEST.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["simulation_parameters"]["total_cohort_size"] == 3
    assert manifest["simulation_parameters"]["seed"] == 77
    assert manifest["simulation_parameters"]["observation_window_days"] == 90


def test_csv_exporter_path_isolation_does_not_clobber_data_synthetic(tmp_path):
    """TEST 6: CSVExporter initialized with output_dir must export to output_dir/synthetic,
    strictly never clobbering or writing to the global data/synthetic/ directory.
    """
    from synapse_simulator.generator.hospital_generator import HospitalSimulator

    custom_out = tmp_path / "isolated_hospital_run"
    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(2)
    sim.run(max_events=50, output_dir=str(custom_out))

    # Verify files were exported into custom_out/phase2/synthetic, NOT global data/synthetic
    assert (custom_out / "phase2").exists()
    assert (custom_out / "phase2" / "synthetic" / "patients.csv").exists()

    # Verify global data/synthetic/patients.csv was NOT overwritten with 2 patients
    global_patients = Path("data/synthetic/patients.csv")
    if global_patients.exists():
        with open(global_patients, "r", encoding="utf-8") as f:
            lines = sum(1 for _ in f)
        assert lines == 10001, f"Expected 10,001 lines in global patients.csv, got {lines}"
