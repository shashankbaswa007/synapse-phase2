"""
Unit tests for Stage 9 Event Persistence and Lineage Mapping.
Verifies event logging in JSON Lines format and Action-State-Event-Document mapping correctness.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentMetadata, DocumentType, DocumentStatus
from synapse_simulator.exporter.event_logger import EventLogger
from synapse_simulator.exporter.lineage_mapper import LineageMapper


def test_event_persistence(tmp_path):
    output_dir = tmp_path / "output"
    logger = EventLogger(output_dir)

    events = [
        DomainEvent(
            event_id="evt-1",
            event_type="PatientArrived",
            timestamp=datetime(2026, 1, 1, 8, 0, 0),
            producer_domain="clinical",
            entity_table="clinical.appointments",
            entity_id="apt-1",
            scenario_instance_id="SCEN-1",
            patient_journey_id="pj-1",
            correlation_id="corr-1",
            payload={"patient_id": "pat-1"},
        ),
        DomainEvent(
            event_id="evt-2",
            event_type="MedicineDispensed",
            timestamp=datetime(2026, 1, 1, 8, 15, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-1",
            scenario_instance_id="SCEN-1",
            patient_journey_id="pj-1",
            correlation_id="corr-1",
            payload={"patient_id": "pat-1"},
        ),
    ]

    path = logger.persist_events(events)
    assert path.exists()

    # Load and verify
    loaded = logger.load_events()
    assert len(loaded) == 2
    assert loaded[0]["event_id"] == "evt-1"
    assert loaded[0]["event_type"] == "PatientArrived"
    assert loaded[1]["event_id"] == "evt-2"

    # Query tests
    by_journey = logger.query_by_journey_id("pj-1")
    assert len(by_journey) == 2

    by_type = logger.query_by_event_type("MedicineDispensed")
    assert len(by_type) == 1
    assert by_type[0]["event_id"] == "evt-2"


def test_lineage_mapping(tmp_path):
    output_dir = tmp_path / "output"
    mapper = LineageMapper(output_dir)

    events = [
        DomainEvent(
            event_id="evt-rx-dispense",
            event_type="MedicineDispensed",
            timestamp=datetime(2026, 1, 1, 8, 15, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-123",
            scenario_instance_id="SCEN-V1-01-inst-1",
            patient_journey_id="pj-123",
            correlation_id="corr-123",
            causation_id="act-dispense-123",
            payload={"patient_id": "pat-123"},
        )
    ]

    docs = {
        "doc-rx-123": DocumentMetadata(
            document_id="doc-rx-123",
            document_type=DocumentType.PRESCRIPTION,
            patient_id="pat-123",
            patient_journey_id="pj-123",
            scenario_id="SCEN-V1-01",
            source_entity_table="pharmacy.prescriptions",
            source_entity_id="rx-123",
            source_action_id="act-dispense-123",
            source_event_id="evt-rx-dispense",
            created_at=datetime(2026, 1, 1, 8, 15, 0),
            file_path="/output/doc-rx-123.md",
            checksum="fakechecksum",
        )
    }

    path = mapper.generate_map(events, docs)
    assert path.exists()

    l_map = mapper.load_lineage_map()
    assert "pj-123" in l_map["journeys"]
    journey = l_map["journeys"]["pj-123"]
    assert journey["patient_id"] == "pat-123"
    assert len(journey["steps"]) == 1

    step = journey["steps"][0]
    assert step["action_id"] == "act-dispense-123"
    assert step["event_id"] == "evt-rx-dispense"
    assert step["event_type"] == "MedicineDispensed"
    assert len(step["documents"]) == 1
    assert step["documents"][0]["document_id"] == "doc-rx-123"
