"""
Unit tests for Stage 9 Diagnostic Report Generation (Laboratory & Radiology).
"""

import pytest
from pathlib import Path
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentType
from synapse_simulator.exporter.document_generator import DocumentGenerator


def test_diagnostic_document_generation(tmp_path):
    state_manager = StateManager()
    output_dir = tmp_path / "output"

    # Set up Lab and Radiology orders
    state_manager.set_entity_state(
        "patient.patients",
        "pat-002",
        {
            "patient_id": "pat-002",
            "name": "Jane Doe",
            "allergies": [],
            "status": "Active",
        },
    )
    state_manager.set_entity_state(
        "laboratory.laboratory_orders",
        "lab-001",
        {
            "lab_order_id": "lab-001",
            "status": "Completed",
        },
    )
    state_manager.set_entity_state(
        "radiology.radiology_orders",
        "rad-001",
        {
            "rad_order_id": "rad-001",
            "status": "Reported",
        },
    )

    events = [
        DomainEvent(
            event_id="evt-lab-result",
            event_type="LabOrderResulted",
            timestamp=datetime(2026, 1, 1, 9, 0, 0),
            producer_domain="laboratory",
            entity_table="laboratory.laboratory_orders",
            entity_id="lab-001",
            scenario_instance_id="SCEN-V1-02-inst-1",
            patient_journey_id="pj-002",
            correlation_id="corr-002",
            payload={
                "patient_id": "pat-002",
                "lab_order_id": "lab-001",
                "journey_id": "pj-002",
                "results": {
                    "WBC": {"value": 12.5, "unit": "x10^3/uL", "range": "4.5 - 11.0", "flag": "High"},
                    "Hemoglobin": {"value": 13.8, "unit": "g/dL", "range": "12.0 - 17.5", "flag": "Normal"},
                },
            },
        ),
        DomainEvent(
            event_id="evt-rad-report",
            event_type="RadiologyReported",
            timestamp=datetime(2026, 1, 1, 9, 15, 0),
            producer_domain="radiology",
            entity_table="radiology.radiology_orders",
            entity_id="rad-001",
            scenario_instance_id="SCEN-V1-02-inst-1",
            patient_journey_id="pj-002",
            correlation_id="corr-002",
            payload={
                "patient_id": "pat-002",
                "rad_order_id": "rad-001",
                "journey_id": "pj-002",
                "findings": "Bilateral lower lobe consolidations.",
                "impression": "Consistent with bacterial pneumonia.",
            },
        ),
    ]

    doc_gen = DocumentGenerator(state_manager, events, output_dir)
    generated = doc_gen.generate_all()

    # Verify Lab Report
    assert "doc-lab-001" in generated
    lab_doc = generated["doc-lab-001"]
    assert lab_doc.document_type == DocumentType.LAB_REPORT
    assert Path(lab_doc.file_path).exists()
    with open(lab_doc.file_path, "r", encoding="utf-8") as f:
        lab_content = f.read()
    assert "12.5" in lab_content
    assert "High" in lab_content

    # Verify Radiology Report
    assert "doc-rad-001" in generated
    rad_doc = generated["doc-rad-001"]
    assert rad_doc.document_type == DocumentType.RAD_REPORT
    assert Path(rad_doc.file_path).exists()
    with open(rad_doc.file_path, "r", encoding="utf-8") as f:
        rad_content = f.read()
    assert "Bilateral lower lobe consolidations" in rad_content
    assert "bacterial pneumonia" in rad_content
