"""
Stage 7 Unit Tests: Cross-Department Data Consistency and Entity Lineage.
"""

from synapse_simulator.generator.hospital_generator import HospitalSimulator


def test_cross_department_data_consistency():
    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=4)
    sim.run(max_events=100)

    for j in sim.journeys:
        # Verify patient identity consistency
        assert j.patient_id is not None
        assert j.correlation_id is not None
        assert j.journey_id is not None

        # Verify entity references are preserved in journey
        refs = j.entity_references
        assert "patient.patients" in refs
        assert "clinical.appointments" in refs

        # Verify entity states exist in StateManager
        patient_state = sim.state_manager.get_entity_state("patient.patients", refs["patient.patients"])
        assert patient_state != {}

        apt_state = sim.state_manager.get_entity_state("clinical.appointments", refs["clinical.appointments"])
        assert apt_state != {}
