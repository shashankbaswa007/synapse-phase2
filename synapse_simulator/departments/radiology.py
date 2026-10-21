"""
Radiology Department Handler.
"""

import uuid
from typing import List
from synapse_simulator.departments.base import BaseDepartmentHandler
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest


class RadiologyDepartmentHandler(BaseDepartmentHandler):
    department_name = "radiology"

    def __init__(self, diagnostic_gen=None, patient_contexts=None, state_manager=None):
        self.diagnostic_gen = diagnostic_gen
        self.patient_contexts = patient_contexts or {}
        self.state_manager = state_manager

    def handle_event(self, event: SimulationEvent) -> List[ActionRequest]:
        actions: List[ActionRequest] = []

        if event.event_type == "RadOrderCreated":
            payload = dict(event.payload)
            if self.diagnostic_gen:
                rad_res = self.diagnostic_gen.generate_radiology_report()
                payload["findings"] = rad_res.findings
                payload["impression"] = rad_res.impression

            actions.append(
                ActionRequest(
                    action_id=f"act-rad-{uuid.uuid4().hex[:8]}",
                    action_type="ACQUIRE_RADIOLOGY_IMAGE",
                    target_department="radiology",
                    target_entity_table="radiology.radiology_orders",
                    target_entity_id=payload.get("rad_order_id", "rad-001"),
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=payload,
                )
            )

        elif event.event_type == "RadiologyImageAcquired":
            payload = dict(event.payload)
            rad_order_id = payload.get("rad_order_id") or payload.get(
                "radiology.radiology_orders", "rad-001"
            )

            rad_state = self.state_manager.get_entity_state("radiology.radiology_orders", rad_order_id) if self.state_manager else {}
            modality = (rad_state.get("modality") if rad_state else None) or payload.get("modality", "Chest X-Ray")
            patient_id = payload.get("patient_id") or (rad_state.get("patient_id") if rad_state else "")
            encounter_id = payload.get("encounter_id") or (rad_state.get("encounter_id") if rad_state else "")

            if self.diagnostic_gen:
                rad_res = self.diagnostic_gen.generate_radiology_report(
                    modality=modality,
                    simulated_time=event.scheduled_at,
                )
                payload["findings"] = rad_res.findings
                payload["impression"] = rad_res.impression
                payload["is_abnormal"] = rad_res.is_abnormal
                payload["modality"] = rad_res.imaging_type
            else:
                payload["findings"] = "Normal study with clear lung fields."
                payload["impression"] = "Unremarkable examination."
                payload["is_abnormal"] = False
                payload["modality"] = modality

            ts_str = event.scheduled_at.isoformat() if hasattr(event.scheduled_at, "isoformat") else str(event.scheduled_at)
            payload["completed_at"] = ts_str

            if self.state_manager and rad_state:
                rad_state["modality"] = payload.get("modality", modality)
                rad_state["findings"] = payload.get("findings", "")
                rad_state["impression"] = payload.get("impression", "")
                rad_state["is_abnormal"] = payload.get("is_abnormal", False)
                rad_state["completed_at"] = ts_str
                if patient_id:
                    rad_state["patient_id"] = patient_id
                if encounter_id:
                    rad_state["encounter_id"] = encounter_id
                self.state_manager.set_entity_state("radiology.radiology_orders", rad_order_id, rad_state)

            actions.append(
                ActionRequest(
                    action_id=f"act-radres-{uuid.uuid4().hex[:8]}",
                    action_type="COMPLETE_RADIOLOGY_REPORT",
                    target_department="radiology",
                    target_entity_table="radiology.radiology_orders",
                    target_entity_id=rad_order_id,
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=payload,
                )
            )

        return actions
