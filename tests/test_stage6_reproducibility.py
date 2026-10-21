"""
Stage 6 Unit Tests: Seed-based Deterministic Simulation Reproducibility.
"""

from synapse_simulator.generator.hospital_generator import HospitalSimulator


def test_seed_reproducibility():
    sim1 = HospitalSimulator(random_seed=42)
    sim1.spawn_patients(patient_count=10)
    metrics1 = sim1.run(max_events=200)

    sim2 = HospitalSimulator(random_seed=42)
    sim2.spawn_patients(patient_count=10)
    metrics2 = sim2.run(max_events=200)

    # Identical seed produces 100% identical simulation metrics
    assert metrics1["total_patients"] == metrics2["total_patients"]
    assert metrics1["total_events_processed"] == metrics2["total_events_processed"]
    assert metrics1["decisions_allowed"] == metrics2["decisions_allowed"]
    assert metrics1["decisions_blocked"] == metrics2["decisions_blocked"]
    assert metrics1["rule_hits"] == metrics2["rule_hits"]
