"""
Core Protocols: Defines structural typing contracts for simulation core components (DIP & ISP).
"""

from typing import Protocol, runtime_checkable, Optional, List, Dict, Any
from datetime import datetime
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest


@runtime_checkable
class IClock(Protocol):
    """Monotonic simulation clock protocol."""

    def now(self) -> datetime:
        ...

    def advance_to(self, target_time: datetime) -> datetime:
        ...

    def advance_by_seconds(self, seconds: float) -> datetime:
        ...

    def advance_by_minutes(self, minutes: float) -> datetime:
        ...


@runtime_checkable
class IScheduler(Protocol):
    """Priority heap action scheduler protocol."""

    def schedule_action(
        self, action_request: ActionRequest, scheduled_at: datetime, causation_depth: int = 0
    ) -> None:
        ...

    def peek_next_due_time(self) -> Optional[datetime]:
        ...

    def get_due_actions(self, current_time: datetime) -> List[Any]:
        ...

    def invalidate_entity_actions(self, entity_table: str, entity_id: str) -> int:
        ...


@runtime_checkable
class IEventQueue(Protocol):
    """Priority event queue protocol."""

    def push(self, event: SimulationEvent) -> None:
        ...

    def pop(self) -> Optional[SimulationEvent]:
        ...

    def peek(self) -> Optional[SimulationEvent]:
        ...

    def is_empty(self) -> bool:
        ...


@runtime_checkable
class IEventDispatcher(Protocol):
    """Event-to-handler routing protocol."""

    def register_handler(self, event_type: str, handler: Any) -> None:
        ...

    def dispatch(self, event: SimulationEvent) -> List[ActionRequest]:
        ...
