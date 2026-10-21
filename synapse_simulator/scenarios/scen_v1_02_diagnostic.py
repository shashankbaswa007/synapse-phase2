"""
SCEN-V1-02 Outpatient Diagnostic Investigation Generator.
"""

from datetime import datetime
from synapse_simulator.scenarios.base_scenario import BaseScenario
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.state_manager import StateManager


class DiagnosticInvestigationScenario(BaseScenario):
    scenario_id = "SCEN-V1-02"
    name = "Outpatient Diagnostic Investigation"
    description = "OPD Consult leading to Lab/Radiology Orders, sample collection, image acquisition, and reporting."

    def setup_initial_state(self, state_manager: StateManager) -> None:
        state_manager.set_entity_state(
            "patient.patients",
            self.patient_id,
            {"patient_id": self.patient_id, "name": "Alice Smith", "allergies": [], "status": "Active"},
        )

        state_manager.set_entity_state(
            "clinical.appointments",
            self.appointment_id,
            {"appointment_id": self.appointment_id, "patient_id": self.patient_id, "status": "Checked-In"},
        )

        state_manager.set_entity_state(
            "laboratory.laboratory_orders",
            self.lab_order_id,
            {"lab_order_id": self.lab_order_id, "patient_id": self.patient_id, "status": "Ordered"},
        )

        state_manager.set_entity_state(
            "radiology.radiology_orders",
            self.rad_order_id,
            {"rad_order_id": self.rad_order_id, "patient_id": self.patient_id, "status": "Ordered"},
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
                "lab_order_id": self.lab_order_id,
                "rad_order_id": self.rad_order_id,
            },
        )
