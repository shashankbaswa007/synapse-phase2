"""
Phase 2 End-to-End Validation Test Suite for Synthetic Hospital Simulator CSV Export & Integrity.
"""

import pytest
import shutil
import csv
from pathlib import Path
from synapse_simulator.generator.hospital_generator import HospitalSimulator


@pytest.fixture
def temp_output_dir(tmp_path):
    out_dir = tmp_path / "output"
    yield out_dir
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)


def test_phase2_end_to_end_csv_export(temp_output_dir):
    """Run full simulation with 20 patients and verify that all CSV files are generated and valid."""
    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=20)
    metrics = sim.run(max_events=2000, output_dir=str(temp_output_dir))

    phase2_dir = temp_output_dir / "phase2"
    assert phase2_dir.exists(), "phase2 output directory must be created"

    # Check required subdirectories
    subdirs = ["master_data", "patients", "clinical", "diagnostics", "pharmacy", "operational", "billing", "events", "journeys", "validation", "metadata"]
    for s in subdirs:
        assert (phase2_dir / s).exists(), f"Subdirectory '{s}' must exist"

    # Verify Master Data CSVs
    dept_csv = phase2_dir / "master_data" / "departments.csv"
    assert dept_csv.exists()
    with open(dept_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) > 1, "departments.csv must contain records"
        assert reader[0] == ["department_id", "department_name", "type", "status"]

    doc_csv = phase2_dir / "master_data" / "doctors.csv"
    assert doc_csv.exists()
    with open(doc_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) > 1, "doctors.csv must contain records"

    # Verify Patient CSVs
    p_csv = phase2_dir / "patients" / "patients.csv"
    assert p_csv.exists()
    with open(p_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 21, f"Expected 20 patient records + 1 header, got {len(reader)}"

    alg_csv = phase2_dir / "patients" / "patient_allergies.csv"
    assert alg_csv.exists()
    with open(alg_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) > 1, "patient_allergies.csv must contain allergy records"

    # Verify Clinical CSVs
    app_csv = phase2_dir / "clinical" / "appointments.csv"
    assert app_csv.exists()

    rx_csv = phase2_dir / "clinical" / "prescriptions.csv"
    assert rx_csv.exists()

    # Verify Events CSV
    evt_csv = phase2_dir / "events" / "events.csv"
    assert evt_csv.exists()
    with open(evt_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) > 10, "events.csv must contain committed domain events"
        headers = reader[0]
        assert "event_id" in headers
        assert "causation_id" in headers
        assert "patient_journey_id" in headers

    # Verify Journeys CSV
    j_csv = phase2_dir / "journeys" / "patient_journeys.csv"
    assert j_csv.exists()

    j_steps_csv = phase2_dir / "journeys" / "patient_journey_steps.csv"
    assert j_steps_csv.exists()

    # Verify Rule Decisions CSV
    rule_csv = phase2_dir / "validation" / "rule_decisions.csv"
    assert rule_csv.exists()

    # Verify Metadata CSV
    meta_csv = phase2_dir / "metadata" / "simulation_metadata.csv"
    assert meta_csv.exists()


def test_10_patient_scale_csv_export(temp_output_dir):
    """Verify 10 patient simulation produces validated CSV datasets."""
    sim = HospitalSimulator(random_seed=123)
    sim.spawn_patients(patient_count=10)
    metrics = sim.run(max_events=1000, output_dir=str(temp_output_dir))

    assert metrics["total_patients"] == 10
    assert metrics["total_events_processed"] > 0

    p_csv = temp_output_dir / "phase2" / "patients" / "patients.csv"
    assert p_csv.exists()
    with open(p_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 11  # 10 patients + header


def test_100_patient_scale_csv_export(temp_output_dir):
    """Verify 100 patient large-scale simulation produces validated CSV datasets."""
    sim = HospitalSimulator(random_seed=999)
    sim.spawn_patients(patient_count=100)
    metrics = sim.run(max_events=10000, output_dir=str(temp_output_dir))

    assert metrics["total_patients"] == 100
    assert metrics["decisions_allowed"] > 0
    assert metrics["decisions_blocked"] > 0  # Penicillin allergy & inventory depletion scenarios block!

    p_csv = temp_output_dir / "phase2" / "patients" / "patients.csv"
    assert p_csv.exists()
    with open(p_csv, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 101  # 100 patients + header
