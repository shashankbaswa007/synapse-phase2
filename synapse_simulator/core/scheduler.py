"""
Future Action Scheduler: Manages scheduled future actions, priority ordering, cancellations, and state-change invalidations.
"""

import heapq
import itertools
from datetime import datetime
from typing import Dict, List, Set, Optional
from pydantic import BaseModel, Field

from synapse_simulator.state.models import ActionRequest


# Atomic sequence counter for deterministic tie-breaking
_sequence_counter = itertools.count()


class ScheduledFutureAction(BaseModel):
    """Represents a scheduled future action in the simulation timeline."""
    action_id: str
    scheduled_at: datetime
    priority: int = 50
    causation_depth: int = 0
    sequence_number: int = Field(default_factory=lambda: next(_sequence_counter))
    action_request: ActionRequest
    status: str = "PENDING"  # PENDING, EXECUTED, CANCELLED, INVALIDATED, EXPIRED
    target_entity_key: str

    def __lt__(self, other: "ScheduledFutureAction") -> bool:
        """Deterministic comparison order: scheduled_at -> priority -> causation_depth -> sequence_number."""
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


class FutureActionScheduler:
    """Heap-based Future Action Scheduler supporting deterministic ordering and state invalidation."""

    def __init__(self):
        self._heap: List[ScheduledFutureAction] = []
        self._actions_map: Dict[str, ScheduledFutureAction] = {}
        self._entity_index: Dict[str, Set[str]] = {}
        self._pending_count: int = 0

    def schedule_action(
        self,
        action_request: ActionRequest,
        scheduled_at: datetime,
        priority: int = 50,
        causation_depth: int = 0,
    ) -> ScheduledFutureAction:
        """Schedule an action for execution at a future simulated timestamp."""
        entity_key = f"{action_request.target_entity_table}:{action_request.target_entity_id}"
        
        scheduled_action = ScheduledFutureAction(
            action_id=action_request.action_id,
            scheduled_at=scheduled_at,
            priority=priority,
            causation_depth=causation_depth,
            action_request=action_request,
            target_entity_key=entity_key,
        )

        heapq.heappush(self._heap, scheduled_action)
        self._actions_map[scheduled_action.action_id] = scheduled_action
        self._pending_count += 1

        if entity_key not in self._entity_index:
            self._entity_index[entity_key] = set()
        self._entity_index[entity_key].add(scheduled_action.action_id)

        return scheduled_action

    def get_due_actions(self, current_time: datetime) -> List[ScheduledFutureAction]:
        """Retrieve all pending actions whose scheduled timestamp is <= current_time in deterministic order."""
        due_actions: List[ScheduledFutureAction] = []
        
        while self._heap and self._heap[0].scheduled_at <= current_time:
            item = heapq.heappop(self._heap)
            if item.status == "PENDING":
                item.status = "EXECUTED"
                self._pending_count -= 1
                due_actions.append(item)
                
        return due_actions

    def peek_next_due_time(self) -> Optional[datetime]:
        """Peek timestamp of the next pending action."""
        while self._heap:
            top = self._heap[0]
            if top.status == "PENDING":
                return top.scheduled_at
            else:
                heapq.heappop(self._heap)
        return None

    def cancel_action(self, action_id: str) -> bool:
        """Mark a pending action as CANCELLED."""
        action = self._actions_map.get(action_id)
        if action and action.status == "PENDING":
            action.status = "CANCELLED"
            self._pending_count -= 1
            return True
        return False

    def reschedule_action(self, action_id: str, new_time: datetime) -> bool:
        """Reschedule a pending action to a new timestamp."""
        action = self._actions_map.get(action_id)
        if action and action.status == "PENDING":
            action.status = "CANCELLED"  # Cancel old item in heap
            self._pending_count -= 1
            
            # Re-schedule with updated timestamp
            self.schedule_action(
                action_request=action.action_request,
                scheduled_at=new_time,
                priority=action.priority,
                causation_depth=action.causation_depth,
            )
            return True
        return False

    def invalidate_entity_actions(self, target_entity_table: str, target_entity_id: str) -> int:
        """Invalidate all pending scheduled actions for an entity whose state changed."""
        entity_key = f"{target_entity_table}:{target_entity_id}"
        action_ids = self._entity_index.get(entity_key, set())
        invalidated_count = 0

        for aid in action_ids:
            action = self._actions_map.get(aid)
            if action and action.status == "PENDING":
                action.status = "INVALIDATED"
                self._pending_count -= 1
                invalidated_count += 1

        return invalidated_count

    def size(self) -> int:
        """Count remaining pending actions in O(1) time."""
        return max(0, self._pending_count)
