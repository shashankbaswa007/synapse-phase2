"""
Laboratory Department Handler.
"""

import uuid
from typing import List
from synapse_simulator.departments.base import BaseDepartmentHandler
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest


class LaboratoryDepartmentHandler(BaseDepartmentHandler):
    department_name = "laboratory"

    def __init__(self, diagnostic_gen=None, patient_contexts=None, state_manager=None):
        self.diagnostic_gen = diagnostic_gen
        self.patient_contexts = patient_contexts or {}
        self.state_manager = state_manager

    def handle_event(self, event: SimulationEvent) -> List[ActionRequest]:
        actions: List[ActionRequest] = []

        if event.event_type == "LabOrderCreated":
            payload = dict(event.payload)
            patient_id = payload.get("patient_id")
            if self.diagnostic_gen:
                lab_res = self.diagnostic_gen.generate_lab_result()
                payload["results"] = lab_res.model_dump().get("components", [])

            # Ensure patient_id is propagated into the lab order state
            lab_order_id = payload.get("lab_order_id", "lab-001")
            if self.state_manager and patient_id:
                lab_state = self.state_manager.get_entity_state("laboratory.laboratory_orders", lab_order_id)
                if lab_state and not lab_state.get("patient_id"):
                    lab_state["patient_id"] = patient_id
                    self.state_manager.set_entity_state("laboratory.laboratory_orders", lab_order_id, lab_state)

            actions.append(
                ActionRequest(
                    action_id=f"act-lab-{uuid.uuid4().hex[:8]}",
                    action_type="COLLECT_LAB_SAMPLE",
                    target_department="laboratory",
                    target_entity_table="laboratory.laboratory_orders",
                    target_entity_id=lab_order_id,
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=payload,
                )
            )

        elif event.event_type == "LabSampleCollected":
            payload = dict(event.payload)
            lab_order_id = payload.get("lab_order_id") or payload.get(
                "laboratory.laboratory_orders", "lab-001"
            )

            lab_state = self.state_manager.get_entity_state("laboratory.laboratory_orders", lab_order_id) if self.state_manager else {}
            test_type = (lab_state.get("test_type") if lab_state else None) or payload.get("test_type", "CBC")
            patient_id = payload.get("patient_id") or (lab_state.get("patient_id") if lab_state else "")
            encounter_id = payload.get("encounter_id") or (lab_state.get("encounter_id") if lab_state else "")

            if self.diagnostic_gen:
                lab_res = self.diagnostic_gen.generate_lab_result(
                    test_type=test_type,
                    simulated_time=event.scheduled_at,
                )
                payload["results"] = lab_res.model_dump().get("components", [])
                payload["is_abnormal"] = lab_res.is_abnormal
                payload["test_name"] = lab_res.test_name
                payload["test_type"] = test_type
            else:
                payload["test_type"] = test_type
                payload["test_name"] = test_type
                payload["is_abnormal"] = False

            ts_str = event.scheduled_at.isoformat() if hasattr(event.scheduled_at, "isoformat") else str(event.scheduled_at)
            payload["completed_at"] = ts_str

            if self.state_manager and lab_state:
                lab_state["test_type"] = test_type
                lab_state["test_name"] = payload.get("test_name", test_type)
                lab_state["results"] = payload.get("results", [])
                lab_state["is_abnormal"] = payload.get("is_abnormal", False)
                lab_state["completed_at"] = ts_str
                if patient_id:
                    lab_state["patient_id"] = patient_id
                if encounter_id:
                    lab_state["encounter_id"] = encounter_id
                self.state_manager.set_entity_state("laboratory.laboratory_orders", lab_order_id, lab_state)

            actions.append(
                ActionRequest(
                    action_id=f"act-labres-{uuid.uuid4().hex[:8]}",
                    action_type="COMPLETE_LAB_RESULT",
                    target_department="laboratory",
                    target_entity_table="laboratory.laboratory_orders",
                    target_entity_id=lab_order_id,
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=payload,
                )
            )

        return actions
