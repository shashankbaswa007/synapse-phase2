"""
Lineage Mapper for Synapse Phase 2.
Maps causal connections across: Action -> State Transition -> Event -> Document.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentMetadata


class LineageMapper:
    """Traces and exports structured lineage connections between events, states, and documents."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.file_path = self.output_dir / "lineage_map.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_map(
        self,
        committed_events: List[DomainEvent],
        generated_docs: Dict[str, DocumentMetadata],
    ) -> Path:
        """Construct and persist lineage_map.json from event log and generated documents."""
        lineage: Dict[str, Any] = {
            "metadata": {
                "generated_at": None,
                "total_events": len(committed_events),
                "total_documents": len(generated_docs),
            },
            "journeys": {},
        }

        # Index documents by their source event/action
        docs_by_event: Dict[str, List[Dict[str, str]]] = {}
        for doc_id, doc in generated_docs.items():
            evt_id = doc.source_event_id
            if evt_id:
                if evt_id not in docs_by_event:
                    docs_by_event[evt_id] = []
                docs_by_event[evt_id].append({
                    "document_id": doc_id,
                    "document_type": doc.document_type.value,
                    "file_path": doc.file_path,
                })

        # Group lineage records by patient journey ID
        for event in committed_events:
            j_id = event.patient_journey_id
            if not j_id:
                continue

            if j_id not in lineage["journeys"]:
                lineage["journeys"][j_id] = {
                    "journey_id": j_id,
                    "patient_id": event.payload.get("patient_id"),
                    "scenario_instance_id": event.scenario_instance_id,
                    "steps": [],
                }

            # Map the event details as a single step/action
            step_record = {
                "action_id": event.causation_id,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else str(event.timestamp),
                "producer_domain": event.producer_domain,
                "target_entity": f"{event.entity_table}:{event.entity_id}",
                "status": event.status,  # COMMITTED or BLOCKED_FAILURE
                "causation_depth": event.causation_depth,
                "sequence_number": event.sequence_number,
                "documents": docs_by_event.get(event.event_id, []),
            }

            lineage["journeys"][j_id]["steps"].append(step_record)

        # Update metadata timestamp
        lineage["metadata"]["generated_at"] = datetime.now().isoformat()

        # Write to JSON
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(lineage, f, indent=2, default=str)

        return self.file_path

    def load_lineage_map(self) -> Dict[str, Any]:
        """Read and return lineage map content."""
        if not self.file_path.exists():
            return {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)
