"""
Pharmacy Department Handler.
"""

import uuid
from typing import List
from synapse_simulator.departments.base import BaseDepartmentHandler
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest


class PharmacyDepartmentHandler(BaseDepartmentHandler):
    department_name = "pharmacy"

    def __init__(self, clinical_gen=None, patient_contexts=None, state_manager=None):
        self.clinical_gen = clinical_gen
        self.patient_contexts = patient_contexts or {}
        self.state_manager = state_manager

    def handle_event(self, event: SimulationEvent) -> List[ActionRequest]:
        actions: List[ActionRequest] = []

        if event.event_type == "EncounterStarted":
            # Issue prescription verification action
            actions.append(
                ActionRequest(
                    action_id=f"act-verify-{uuid.uuid4().hex[:8]}",
                    action_type="VERIFY_PRESCRIPTION",
                    target_department="pharmacy",
                    target_entity_table="pharmacy.prescriptions",
                    target_entity_id=event.payload.get("prescription_id", "rx-001"),
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=event.payload,
                )
            )

            # Issue medicine dispense confirmation action
            actions.append(
                ActionRequest(
                    action_id=f"act-dispense-{uuid.uuid4().hex[:8]}",
                    action_type="CONFIRM_MEDICINE_DISPENSE",
                    target_department="pharmacy",
                    target_entity_table="pharmacy.prescriptions",
                    target_entity_id=event.payload.get("prescription_id", "rx-001"),
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=event.payload,
                )
            )

        elif event.event_type == "PrescriptionVerified":
            actions.append(
                ActionRequest(
                    action_id=f"act-dispense-{uuid.uuid4().hex[:8]}",
                    action_type="CONFIRM_MEDICINE_DISPENSE",
                    target_department="pharmacy",
                    target_entity_table="pharmacy.prescriptions",
                    target_entity_id=event.payload.get("prescription_id", "rx-001"),
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=event.payload,
                )
            )

        return actions
