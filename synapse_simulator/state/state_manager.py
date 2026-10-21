"""
State Manager: Maintains in-memory state snapshots and applies approved StateTransitionProposal objects.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from synapse_simulator.state.models import (
    InputContext,
    ActionRequest,
    StateTransitionProposal,
    DecisionResult,
)
from synapse_simulator.transitions.transition_manager import TransitionManager
from synapse_simulator.transitions.interfaces import ITransitionValidator


class StateManager:
    """Authoritative State Manager managing entity state snapshots and transitions."""

    def __init__(self, transition_validator: Optional[ITransitionValidator] = None):
        # In-memory entity state tables: table_name -> { entity_id -> state_dict }
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.transition_validator: ITransitionValidator = transition_validator or TransitionManager

    def get_entity_state(self, table_name: str, entity_id: str) -> Dict[str, Any]:
        """Retrieve entity state dictionary."""
        return self._store.get(table_name, {}).get(entity_id, {})

    def set_entity_state(self, table_name: str, entity_id: str, state: Dict[str, Any]) -> None:
        """Set/initialize entity state dictionary."""
        if table_name not in self._store:
            self._store[table_name] = {}
        self._store[table_name][entity_id] = state

    def build_input_context(
        self,
        proposed_action: ActionRequest,
        simulated_timestamp: datetime,
        scenario_id: str,
        department_id: str,
        patient_id: Optional[str] = None,
    ) -> InputContext:
        """Assemble an InputContext snapshot for Rule Engine evaluation."""
        table = proposed_action.target_entity_table
        entity_id = proposed_action.target_entity_id

        entity_state = self.get_entity_state(table, entity_id)

        # Retrieve patient state if patient_id provided
        patient_state = {}
        if patient_id:
            patient_state = self.get_entity_state("patient.patients", patient_id)

        # Retrieve resource inventory state if available
        batch_id = proposed_action.payload.get("inventory_batch_id") or proposed_action.payload.get("pharmacy.inventory_batches") or ""
        resource_state = self.get_entity_state("pharmacy.inventory_batches", batch_id)

        return InputContext(
            simulated_timestamp=simulated_timestamp,
            scenario_id=scenario_id,
            scenario_instance_id=proposed_action.scenario_instance_id,
            patient_journey_id=proposed_action.patient_journey_id,
            correlation_id=proposed_action.correlation_id,
            department_id=department_id,
            proposed_action=proposed_action,
            patient_state=patient_state,
            entity_state=entity_state,
            resource_state=resource_state,
            extra_context={**proposed_action.payload, **getattr(proposed_action, "extra_context", {})},
        )

    def apply_decision(self, decision: DecisionResult) -> bool:
        """Apply approved StateTransitionProposal objects to update entity state store."""
        if decision.status == "BLOCKED" and not decision.state_transitions:
            return False

        for proposal in decision.state_transitions:
            table = proposal.target_entity_table
            entity_id = proposal.target_entity_id

            # Structural transition check
            is_valid, err_msg = self.transition_validator.validate_transition(
                table, proposal.current_value, proposal.new_value
            )
            if not is_valid:
                print(f"StateManager Error: {err_msg}")
                return False

            # Update entity state status and extra updates
            current_entity_dict = self.get_entity_state(table, entity_id)
            current_entity_dict["status"] = proposal.new_value
            current_entity_dict.update(proposal.additional_updates)

            self.set_entity_state(table, entity_id, current_entity_dict)

        return True
