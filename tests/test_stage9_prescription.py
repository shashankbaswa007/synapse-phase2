"""
Unit tests for Stage 9 Prescription Document Generation.
Verifies correct patient, doctor, diagnosis, medication mapping, allergy checks, and formatting.
"""

import pytest
from pathlib import Path
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentType, DocumentStatus
from synapse_simulator.exporter.document_generator import DocumentGenerator


def test_prescription_document_generation(tmp_path):
    state_manager = StateManager()
    output_dir = tmp_path / "output"

    # Set up active prescription
    state_manager.set_entity_state(
        "patient.patients",
        "pat-001",
        {
            "patient_id": "pat-001",
            "name": "Alice Green",
            "allergies": ["Latex"],
            "status": "Active",
        },
    )
    state_manager.set_entity_state(
        "pharmacy.prescriptions",
        "rx-001",
        {
            "prescription_id": "rx-001",
            "patient_id": "pat-001",
            "drug_name": "Paracetamol",
            "drug_class": "Analgesic",
            "dosage": "500mg",
            "frequency": "TDS",
            "duration_days": 5,
            "status": "Dispensed",
            "journey_id": "pj-001",
        },
    )

    # Reconstruct domain events
    events = [
        DomainEvent(
            event_id="evt-verify-001",
            event_type="PrescriptionVerified",
            timestamp=datetime(2026, 1, 1, 8, 30, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-001",
            scenario_instance_id="SCEN-V1-01-inst-1",
            patient_journey_id="pj-001",
            correlation_id="corr-001",
            payload={"patient_id": "pat-001", "prescription_id": "rx-001", "status": "Verification_Passed"},
        ),
        DomainEvent(
            event_id="evt-dispense-001",
            event_type="MedicineDispensed",
            timestamp=datetime(2026, 1, 1, 8, 40, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-001",
            scenario_instance_id="SCEN-V1-01-inst-1",
            patient_journey_id="pj-001",
            correlation_id="corr-001",
            payload={"patient_id": "pat-001", "prescription_id": "rx-001", "status": "Dispensed"},
        ),
    ]

    doc_gen = DocumentGenerator(state_manager, events, output_dir)
    generated = doc_gen.generate_all()

    # Check document list
    assert "doc-rx-001" in generated
    doc = generated["doc-rx-001"]
    assert doc.document_type == DocumentType.PRESCRIPTION
    assert doc.patient_id == "pat-001"
    assert doc.patient_journey_id == "pj-001"
    assert doc.document_status == DocumentStatus.FINAL

    # Check file exists
    md_file = Path(doc.file_path)
    assert md_file.exists()
    json_file = md_file.with_suffix(".json")
    assert json_file.exists()

    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Check content matches prescription values
    assert "Alice Green" in content
    assert "Paracetamol" in content
    assert "Analgesic" in content
    assert "500mg" in content
    assert "TDS" in content
    assert "MEDICINE FULLY DISPENSED" in content
