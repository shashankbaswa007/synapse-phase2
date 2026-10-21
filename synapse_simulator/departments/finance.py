"""
Finance Department Handler.
"""

from typing import List
from synapse_simulator.departments.base import BaseDepartmentHandler
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest
from synapse_simulator.core.ids import new_id


class FinanceDepartmentHandler(BaseDepartmentHandler):
    department_name = "finance"

    def __init__(self, billing_gen=None, patient_contexts=None, state_manager=None):
        self.billing_gen = billing_gen
        self.patient_contexts = patient_contexts or {}
        self.state_manager = state_manager

    def handle_event(self, event: SimulationEvent) -> List[ActionRequest]:
        actions: List[ActionRequest] = []

        if event.event_type == "ADD_INVOICE_LINE_ITEM" or event.event_type == "MedicineDispensed":
            actions.append(
                ActionRequest(
                    action_id=new_id("act-fin-", 8),
                    action_type="GENERATE_INVOICE",
                    target_department="finance",
                    target_entity_table="finance.invoices",
                    target_entity_id=event.payload.get("invoice_id", "inv-001"),
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=event.payload,
                )
            )

        elif event.event_type == "InvoiceGenerated":
            inv_id = event.payload.get("invoice_id")
            if not inv_id and event.patient_journey_id:
                inv_id = f"inv-{event.patient_journey_id[3:]}" if event.patient_journey_id.startswith("pj-") else f"inv-{event.patient_journey_id}"
            if not inv_id:
                inv_id = "inv-001"
            actions.append(
                ActionRequest(
                    action_id=new_id("act-pay-", 8),
                    action_type="PROCESS_PAYMENT",
                    target_department="finance",
                    target_entity_table="finance.invoices",
                    target_entity_id=inv_id,
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload={"invoice_id": inv_id},
                )
            )

        return actions
