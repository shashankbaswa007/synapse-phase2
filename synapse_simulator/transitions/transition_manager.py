"""
Transition Manager: Validates entity structural state transitions.
"""

from typing import Tuple, Optional
from synapse_simulator.transitions.state_machine import ENTITY_STATE_MACHINES, BaseStateMachine


class TransitionManager:
    """Validates whether proposed status transitions comply with entity state machines."""

    @staticmethod
    def validate_transition(entity_table: str, current_state: str, next_state: str) -> Tuple[bool, Optional[str]]:
        sm_class = ENTITY_STATE_MACHINES.get(entity_table)
        if not sm_class:
            # If no explicit state machine defined for table, allow transition by default
            return True, None

        if sm_class.is_valid_transition(current_state, next_state):
            return True, None

        return False, (
            f"Invalid state transition for entity '{entity_table}': "
            f"Cannot transition from '{current_state}' to '{next_state}'. "
            f"Allowed next states: {list(sm_class.valid_transitions.get(current_state, []))}"
        )

    @staticmethod
    def is_terminal_state(entity_table: str, state: str) -> bool:
        sm_class = ENTITY_STATE_MACHINES.get(entity_table)
        if not sm_class:
            return False
        return sm_class.is_terminal(state)
