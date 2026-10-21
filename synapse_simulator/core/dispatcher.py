"""
Event Dispatcher: Registers event handlers and routes emitted events to downstream domain handlers.
"""

from typing import Dict, List, Callable, Any
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest

# Type alias for event handler callables
EventHandlerCallable = Callable[[SimulationEvent], List[ActionRequest]]


class EventDispatcher:
    """Routes emitted simulation events to registered departmental handlers."""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandlerCallable]] = {}
        self._event_history: List[SimulationEvent] = []

    def register_handler(self, event_type: str, handler: EventHandlerCallable) -> None:
        """Register a handler callback for an event type (prevents duplicates)."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def dispatch(self, event: SimulationEvent) -> List[ActionRequest]:
        """Dispatch event to all matching handlers and collect generated ActionRequests."""
        self._event_history.append(event)
        generated_actions: List[ActionRequest] = []

        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                actions = handler(event)
                if actions:
                    generated_actions.extend(actions)
            except Exception as e:
                print(f"EventDispatcher Error running handler for '{event.event_type}': {e}")

        return generated_actions

    @property
    def event_history(self) -> List[SimulationEvent]:
        return self._event_history
