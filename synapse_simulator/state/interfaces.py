"""
State Protocols: Segregated interfaces for reading, writing, and context building (ISP & DIP).
"""

from typing import Protocol, runtime_checkable, Dict, Any, Optional
from datetime import datetime
from synapse_simulator.state.models import ActionRequest, InputContext, DecisionResult


@runtime_checkable
class IStateReader(Protocol):
    """Read-only entity state access protocol."""

    def get_entity_state(self, table_name: str, entity_id: str) -> Dict[str, Any]:
        ...


@runtime_checkable
class IStateWriter(Protocol):
    """State mutation and initialization protocol."""

    def set_entity_state(self, table_name: str, entity_id: str, state: Dict[str, Any]) -> None:
        ...


@runtime_checkable
class IContextBuilder(Protocol):
    """Snapshot assembly for RuleEngine evaluation protocol."""

    def build_input_context(
        self,
        proposed_action: ActionRequest,
        simulated_timestamp: datetime,
        scenario_id: str,
        department_id: str,
        patient_id: Optional[str] = None,
    ) -> InputContext:
        ...


@runtime_checkable
class IStateDecisionApplier(Protocol):
    """Transition application protocol for approved decisions."""

    def apply_decision(self, decision: DecisionResult) -> bool:
        ...
