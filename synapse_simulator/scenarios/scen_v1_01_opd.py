"""
SCEN-V1-01 Routine Outpatient Journey Generator.
"""

from datetime import datetime
from synapse_simulator.scenarios.base_scenario import BaseScenario
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.state_manager import StateManager


class OutpatientRoutineScenario(BaseScenario):
    scenario_id = "SCEN-V1-01"
    name = "Routine Outpatient Journey"
    description = "Standard OPD patient arrival, consultation, prescription verification, dispense, and billing."

    def setup_initial_state(self, state_manager: StateManager) -> None:
        # 1. Patient entity
        state_manager.set_entity_state(
            "patient.patients",
            self.patient_id,
            {
                "patient_id": self.patient_id,
                "name": "Jane Doe",
                "allergies": [],
                "status": "Active",
            },
        )

        # 2. Appointment entity (Set status to 'Checked-In' so rule passes)
        state_manager.set_entity_state(
            "clinical.appointments",
            self.appointment_id,
            {
                "appointment_id": self.appointment_id,
                "patient_id": self.patient_id,
                "status": "Checked-In",
            },
        )

        # 3. Prescription entity
        state_manager.set_entity_state(
            "pharmacy.prescriptions",
            self.prescription_id,
            {
                "prescription_id": self.prescription_id,
                "patient_id": self.patient_id,
                "drug_name": "Paracetamol",
                "drug_class": "Analgesic",
                "status": "Issued",
            },
        )

        # 4. Inventory batch state
        state_manager.set_entity_state(
            "pharmacy.inventory_batches",
            self.batch_id,
            {
                "batch_id": self.batch_id,
                "quantity_available": 100,
                "status": "Active",
            },
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
                "inventory_batch_id": self.batch_id,
            },
        )
