"""
End-to-End Integration Test for SYNAPSE Large-Scale Synthetic Hospital Simulator.
"""

import pytest
from pathlib import Path
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.exporter.data_exporter import DataExporter


def test_full_hospital_simulation():
    sim = HospitalSimulator(random_seed=42)

    # Spawn 20 patients across all 4 scenarios
    instance_ids = sim.spawn_patients(patient_count=20)
    assert len(instance_ids) == 20

    # Run discrete event simulation
    metrics = sim.run(max_events=1000)

    assert metrics["total_patients"] == 20
    assert metrics["total_events_processed"] >= 20
    assert metrics["decisions_allowed"] > 0
    assert metrics["decisions_blocked"] > 0

    # Verify safety rules were triggered
    rule_hits = metrics["rule_hits"]
    assert "RULE-CLIN-ALLERGY-001" in rule_hits
    assert "RULE-GLOB-STOCK-001" in rule_hits
    assert "RULE-WORK-OPD-010" in rule_hits

    # Test data exporter
    tmp_out = Path("./tmp_test_output")
    saved_file = DataExporter.export_to_json(tmp_out, metrics, "test_metrics.json")
    assert saved_file.exists()

    # Clean up test output directory
    if saved_file.exists():
        saved_file.unlink()
    if tmp_out.exists():
        tmp_out.rmdir()
