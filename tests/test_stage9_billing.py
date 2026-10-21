"""
Unit tests for Stage 9 Billing Invoice Document Generation.
"""

import pytest
from pathlib import Path
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentType, DocumentStatus
from synapse_simulator.exporter.document_generator import DocumentGenerator


def test_billing_document_generation(tmp_path):
    state_manager = StateManager()
    output_dir = tmp_path / "output"

    # Set up patient
    state_manager.set_entity_state(
        "patient.patients",
        "pat-003",
        {
            "patient_id": "pat-003",
            "name": "David Miller",
            "allergies": [],
            "status": "Active",
        },
    )

    events = [
        DomainEvent(
            event_id="evt-consult",
            event_type="EncounterStarted",
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
            producer_domain="clinical",
            entity_table="clinical.appointments",
            entity_id="apt-003",
            scenario_instance_id="SCEN-V1-01-inst-3",
            patient_journey_id="pj-003",
            correlation_id="corr-003",
            payload={"patient_id": "pat-003"},
        ),
        DomainEvent(
            event_id="evt-billing-charge",
            event_type="ADD_INVOICE_LINE_ITEM",
            timestamp=datetime(2026, 1, 1, 10, 15, 0),
            producer_domain="finance",
            entity_table="finance.invoices",
            entity_id="inv-003",
            scenario_instance_id="SCEN-V1-01-inst-3",
            patient_journey_id="pj-003",
            correlation_id="corr-003",
            payload={
                "patient_id": "pat-003",
                "invoice_id": "inv-003",
                "service_name": "Lab Pathology Lipid Panel",
                "amount": 600.00,
            },
        ),
    ]

    doc_gen = DocumentGenerator(state_manager, events, output_dir)
    generated = doc_gen.generate_all()

    # Verify Invoice
    assert "doc-bill-003" in generated
    bill_doc = generated["doc-bill-003"]
    assert bill_doc.document_type == DocumentType.INVOICE
    assert bill_doc.patient_id == "pat-003"
    assert Path(bill_doc.file_path).exists()

    with open(bill_doc.file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Base consult fee 500 + Lipid panel fee 600 = 1100 total
    assert "David Miller" in content
    assert "Outpatient Consultation Fee" in content
    assert "Lab Pathology Lipid Panel" in content
    assert "1100.00" in content
    assert "Paid" in content
