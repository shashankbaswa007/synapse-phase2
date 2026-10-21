"""
SCEN-V1-04 Inventory Stock Depletion & Shortage Generator.
"""

from datetime import datetime
from synapse_simulator.scenarios.base_scenario import BaseScenario
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.state_manager import StateManager


class InventoryDepletionScenario(BaseScenario):
    scenario_id = "SCEN-V1-04"
    name = "Inventory Stock Depletion"
    description = "Medication dispense request exceeds low stock, triggering RULE-GLOB-STOCK-001 block."

    def setup_initial_state(self, state_manager: StateManager) -> None:
        state_manager.set_entity_state(
            "patient.patients",
            self.patient_id,
            {"patient_id": self.patient_id, "name": "Charlie Green", "allergies": [], "status": "Active"},
        )

        state_manager.set_entity_state(
            "clinical.appointments",
            self.appointment_id,
            {"appointment_id": self.appointment_id, "patient_id": self.patient_id, "status": "Checked-In"},
        )

        state_manager.set_entity_state(
            "pharmacy.prescriptions",
            self.prescription_id,
            {
                "prescription_id": self.prescription_id,
                "patient_id": self.patient_id,
                "drug_name": "Ibuprofen",
                "drug_class": "NSAID",
                "status": "Issued",
            },
        )

        # Depleted stock batch: only 2 items available
        state_manager.set_entity_state(
            "pharmacy.inventory_batches",
            self.batch_id,
            {"batch_id": self.batch_id, "quantity_available": 2, "status": "Low_Stock"},
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
                "requested_quantity": 10,  # 10 requested > 2 available
            },
        )
