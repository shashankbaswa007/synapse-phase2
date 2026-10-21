"""
SCEN-V1-03 Clinical Safety Hold & Medication Replacement Generator.
"""

from datetime import datetime
from synapse_simulator.scenarios.base_scenario import BaseScenario
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.state_manager import StateManager


class DrugAllergySafetyHoldScenario(BaseScenario):
    scenario_id = "SCEN-V1-03"
    name = "Drug Allergy Safety Hold"
    description = "Prescription verification triggers Penicillin drug-allergy safety hold and alert notification."

    def setup_initial_state(self, state_manager: StateManager) -> None:
        # Patient with Penicillin allergy
        state_manager.set_entity_state(
            "patient.patients",
            self.patient_id,
            {
                "patient_id": self.patient_id,
                "name": "Robert Brown",
                "allergies": ["Penicillin"],
                "status": "Active",
            },
        )

        state_manager.set_entity_state(
            "clinical.appointments",
            self.appointment_id,
            {"appointment_id": self.appointment_id, "patient_id": self.patient_id, "status": "Checked-In"},
        )

        # Prescription of Beta-Lactam drug (Amoxicillin)
        state_manager.set_entity_state(
            "pharmacy.prescriptions",
            self.prescription_id,
            {
                "prescription_id": self.prescription_id,
                "patient_id": self.patient_id,
                "drug_name": "Amoxicillin",
                "drug_class": "Beta-Lactam",
                "status": "Issued",
            },
        )

        state_manager.set_entity_state(
            "pharmacy.inventory_batches",
            self.batch_id,
            {"batch_id": self.batch_id, "quantity_available": 50, "status": "Active"},
        )

    def generate_initial_events(self, start_time: datetime) -> SimulationEvent:
        return SimulationEvent(
            scheduled_at=start_time,
            event_type="PatientArrived",
            source_department="clinical",
            scenario_instance_id=self.scenario_instance_id,
            patient_journey_id=self.patient_journey_id,
            correlation_id=self.correlation_id,
            payload={
                "patient_id": self.patient_id,
                "appointment_id": self.appointment_id,
                "prescription_id": self.prescription_id,
                "drug_class": "Beta-Lactam",
                "inventory_batch_id": self.batch_id,
            },
        )

    def create_patient_profile(self, patient_gen):
        """Force Penicillin allergy for this scenario instance polymorphically."""
        return patient_gen.generate_patient(force_allergy="Penicillin")

    def should_force_conflict(self) -> bool:
        """Force allergy conflict for safety hold testing."""
        return True
