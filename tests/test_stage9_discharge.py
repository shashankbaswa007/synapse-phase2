"""
Unit tests for Stage 9 Discharge Summary Generation.
"""

import pytest
from pathlib import Path
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentType
from synapse_simulator.exporter.document_generator import DocumentGenerator


def test_discharge_summary_generation(tmp_path):
    state_manager = StateManager()
    output_dir = tmp_path / "output"

    state_manager.set_entity_state(
        "patient.patients",
        "pat-004",
        {
            "patient_id": "pat-004",
            "name": "Sarah Connor",
            "allergies": ["Penicillin"],
            "status": "Active",
        },
    )

    events = [
        DomainEvent(
            event_id="evt-start",
            event_type="PatientArrived",
            timestamp=datetime(2026, 1, 1, 11, 0, 0),
            producer_domain="clinical",
            entity_table="clinical.appointments",
            entity_id="apt-004",
            scenario_instance_id="SCEN-V1-03-inst-4",
            patient_journey_id="pj-004",
            correlation_id="corr-004",
            payload={"patient_id": "pat-004"},
        ),
        DomainEvent(
            event_id="evt-conflict",
            event_type="PrescriptionAllergyConflictDetected",
            timestamp=datetime(2026, 1, 1, 11, 10, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-004",
            scenario_instance_id="SCEN-V1-03-inst-4",
            patient_journey_id="pj-004",
            correlation_id="corr-004",
            payload={"patient_id": "pat-004", "drug_class": "Beta-Lactam"},
        ),
        DomainEvent(
            event_id="evt-end",
            event_type="PatientDischarged",
            timestamp=datetime(2026, 1, 1, 11, 20, 0),
            producer_domain="clinical",
            entity_table="clinical.encounters",
            entity_id="enc-004",
            scenario_instance_id="SCEN-V1-03-inst-4",
            patient_journey_id="pj-004",
            correlation_id="corr-004",
            payload={"patient_id": "pat-004"},
        ),
    ]

    doc_gen = DocumentGenerator(state_manager, events, output_dir)
    generated = doc_gen.generate_all()

    assert "doc-ds-004" in generated
    ds_doc = generated["doc-ds-004"]
    assert ds_doc.document_type == DocumentType.DISCHARGE_SUMMARY
    assert ds_doc.patient_id == "pat-004"
    assert Path(ds_doc.file_path).exists()

    with open(ds_doc.file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Sarah Connor" in content
    assert "Discharged with safety hold clinical alert created" in content
    assert "Drug-Allergy conflict blocked beta-lactam prescription verification" in content
