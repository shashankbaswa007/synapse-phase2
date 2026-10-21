"""
Event Logger for Synapse Phase 2.
Persists domain events in JSON Lines format (events.jsonl) and provides query interfaces.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from synapse_simulator.state.models import DomainEvent


class EventLogger:
    """Manages sequential domain event storage, persistence, and querying."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.file_path = self.output_dir / "events.jsonl"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def persist_events(self, events: List[DomainEvent]) -> Path:
        """Write domain events sequentially to events.jsonl."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            for event in events:
                # Use model_dump to convert pydantic object to dict
                event_dict = event.model_dump()
                f.write(json.dumps(event_dict, default=str) + "\n")
        return self.file_path

    def load_events(self) -> List[Dict[str, Any]]:
        """Read all persisted domain events from events.jsonl."""
        if not self.file_path.exists():
            return []

        events = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line.strip()))
        return events

    def query_by_journey_id(self, journey_id: str) -> List[Dict[str, Any]]:
        """Filter events belonging to a specific patient journey."""
        events = self.load_events()
        return [e for e in events if e.get("patient_journey_id") == journey_id]

    def query_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Filter events belonging to a specific correlation transaction ID."""
        events = self.load_events()
        return [e for e in events if e.get("correlation_id") == correlation_id]

    def query_by_entity_id(self, entity_id: str) -> List[Dict[str, Any]]:
        """Filter events related to a specific operational entity."""
        events = self.load_events()
        return [e for e in events if e.get("entity_id") == entity_id]

    def query_by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Filter events by their event type classification."""
        events = self.load_events()
        return [e for e in events if e.get("event_type") == event_type]
