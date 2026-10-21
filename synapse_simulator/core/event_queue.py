"""
Priority Queue for Discrete Event Simulation with deterministic ordering.
"""

import heapq
import uuid
import itertools
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

_evt_sequence_counter = itertools.count()


class SimulationEvent(BaseModel):
    """Event model managed by the simulation priority queue."""
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:10]}")
    scheduled_at: datetime
    priority: int = 50
    event_type: str
    source_department: str
    target_department: Optional[str] = None
    scenario_instance_id: str
    patient_journey_id: str
    correlation_id: str
    causation_id: Optional[str] = None
    causation_depth: int = 0
    sequence_number: int = Field(default_factory=lambda: next(_evt_sequence_counter))
    payload: Dict[str, Any] = Field(default_factory=dict)
    cancelled: bool = False

    def __lt__(self, other: "SimulationEvent") -> bool:
        """Min-heap comparison based on scheduled timestamp, priority, causation depth, and sequence number."""
        return (
            self.scheduled_at,
            self.priority,
            self.causation_depth,
            self.sequence_number,
        ) < (
            other.scheduled_at,
            other.priority,
            other.causation_depth,
            other.sequence_number,
        )


class EventQueue:
    """Min-heap Priority Queue ordered by event timestamp and sequence number."""

    def __init__(self):
        self._heap: List[SimulationEvent] = []
        self._event_lookup: Dict[str, SimulationEvent] = {}

    def push(self, event: SimulationEvent) -> None:
        """Schedule a new event into the priority queue."""
        heapq.heappush(self._heap, event)
        self._event_lookup[event.event_id] = event

    def pop(self) -> Optional[SimulationEvent]:
        """Pop the next non-cancelled event in timestamp order."""
        while self._heap:
            event = heapq.heappop(self._heap)
            if not event.cancelled:
                self._event_lookup.pop(event.event_id, None)
                return event
            else:
                self._event_lookup.pop(event.event_id, None)
        return None

    def peek(self) -> Optional[SimulationEvent]:
        """Peek at the next non-cancelled event without removing it."""
        while self._heap:
            top = self._heap[0]
            if top.cancelled:
                heapq.heappop(self._heap)
                self._event_lookup.pop(top.event_id, None)
            else:
                return top
        return None

    def cancel(self, event_id: str) -> bool:
        """Mark an event as cancelled."""
        event = self._event_lookup.get(event_id)
        if event:
            event.cancelled = True
            return True
        return False

    def is_empty(self) -> bool:
        return self.peek() is None

    def size(self) -> int:
        return len([e for e in self._heap if not e.cancelled])
