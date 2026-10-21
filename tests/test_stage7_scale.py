"""
Stage 7 Integration Test: 100-Patient Scaling Validation.
"""

from synapse_simulator.generator.hospital_generator import HospitalSimulator


def test_hundred_patient_scale_validation():
    sim = HospitalSimulator(random_seed=100)
    sim.spawn_patients(patient_count=100)

    metrics = sim.run(max_events=2000)

    assert metrics["total_patients"] == 100
    assert metrics["total_events_processed"] >= 100
    assert metrics["decisions_allowed"] > 0
    assert metrics["decisions_blocked"] > 0
    assert len(sim.journeys) == 100

    outcomes = metrics["journey_outcomes"]
    assert "SUCCESS_COMPLETED" in outcomes
    assert "RULE-CLIN-ALLERGY-001" in metrics["rule_hits"] or "RULE-GLOB-STOCK-001" in metrics["rule_hits"]
