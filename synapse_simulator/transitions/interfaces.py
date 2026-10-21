"""
Transition Protocols: Defines transition validation contract (DIP).
"""

from typing import Protocol, runtime_checkable, Tuple, Optional


@runtime_checkable
class ITransitionValidator(Protocol):
    """Protocol for state machine transition validation."""

    def validate_transition(
        self, entity_table: str, current_state: str, next_state: str
    ) -> Tuple[bool, Optional[str]]:
        ...

    def is_terminal_state(self, entity_table: str, state: str) -> bool:
        ...
