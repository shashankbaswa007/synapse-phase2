"""
Unit tests for Stage 9 Integrity Validation, Deep Data Audit, and Consistency Checks.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentMetadata, DocumentType
from synapse_simulator.validation.document_validator import DocumentValidator
from synapse_simulator.validation.integrity_auditor import IntegrityAuditor
from synapse_simulator.validation.consistency_checker import ConsistencyChecker


def test_document_and_data_integrity_validation(tmp_path):
    state_manager = StateManager()
    output_dir = tmp_path / "output"

    # Set up patient, prescription, and inventory
    state_manager.set_entity_state(
        "patient.patients",
        "pat-100",
        {"patient_id": "pat-100", "name": "Thomas A. Anderson", "allergies": [], "status": "Active"},
    )
    state_manager.set_entity_state(
        "clinical.encounters",
        "enc-100",
        {"encounter_id": "enc-100", "patient_id": "pat-100", "status": "Closed"},
    )
    state_manager.set_entity_state(
        "pharmacy.prescriptions",
        "rx-100",
        {
            "prescription_id": "rx-100",
            "patient_id": "pat-100",
            "drug_name": "Metformin",
            "drug_class": "Biguanide",
            "dosage": "500mg",
            "frequency": "BD",
            "duration_days": 30,
            "status": "Dispensed",
            "journey_id": "pj-100",
        },
    )
    state_manager.set_entity_state(
        "pharmacy.inventory_batches",
        "batch-1",
        {
            "batch_id": "batch-1",
            "drug_name": "Metformin",
            "quantity_available": 150,
            "status": "Active",
        },
    )

    events = [
        DomainEvent(
            event_id="evt-arrived",
            event_type="PatientArrived",
            timestamp=datetime(2026, 1, 1, 8, 0, 0),
            producer_domain="clinical",
            entity_table="clinical.appointments",
            entity_id="apt-100",
            scenario_instance_id="SCEN-1",
            patient_journey_id="pj-100",
            correlation_id="corr-100",
            sequence_number=1,
            payload={"patient_id": "pat-100"},
        ),
        DomainEvent(
            event_id="evt-verified",
            event_type="PrescriptionVerified",
            timestamp=datetime(2026, 1, 1, 8, 10, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-100",
            scenario_instance_id="SCEN-1",
            patient_journey_id="pj-100",
            correlation_id="corr-100",
            sequence_number=2,
            payload={"patient_id": "pat-100", "status": "Verification_Passed", "new_value": "Verification_Passed"},
        ),
        DomainEvent(
            event_id="evt-dispensed",
            event_type="MedicineDispensed",
            timestamp=datetime(2026, 1, 1, 8, 20, 0),
            producer_domain="pharmacy",
            entity_table="pharmacy.prescriptions",
            entity_id="rx-100",
            scenario_instance_id="SCEN-1",
            patient_journey_id="pj-100",
            correlation_id="corr-100",
            sequence_number=3,
            payload={"patient_id": "pat-100", "status": "Dispensed", "new_value": "Dispensed"},
        ),
    ]

    docs = {
        "doc-rx-100": DocumentMetadata(
            document_id="doc-rx-100",
            document_type=DocumentType.PRESCRIPTION,
            patient_id="pat-100",
            patient_journey_id="pj-100",
            scenario_id="SCEN-1",
            source_entity_table="pharmacy.prescriptions",
            source_entity_id="rx-100",
            source_action_id="act-dispense",
            source_event_id="evt-dispensed",
            created_at=datetime(2026, 1, 1, 8, 20, 0),
            file_path=str(output_dir / "rx.md"),
            checksum="dummy",
            metadata_payload={
                "drug_name": "Metformin",
                "drug_class": "Biguanide",
                "status": "Dispensed",
            },
        )
    }

    # 1. Document Validator
    validator = DocumentValidator(state_manager)
    is_valid, errors = validator.validate_document(docs["doc-rx-100"])
    assert is_valid
    assert len(errors) == 0

    # Test mismatch validation
    mismatched_doc = docs["doc-rx-100"].model_copy(deep=True)
    mismatched_doc.metadata_payload["drug_name"] = "Insulin" # Mismatch
    is_valid, errors = validator.validate_document(mismatched_doc)
    assert not is_valid
    assert any("drug name" in e.lower() for e in errors)

    # 2. Deep Data Auditor
    auditor = IntegrityAuditor(state_manager, events)
    report = auditor.audit_all()
    assert report["success"]
    assert report["identity_referential"]["success"]
    assert report["temporal_sequencing"]["success"]
    assert report["state_transitions"]["success"]
    assert report["resource_constraints"]["success"]
    assert report["rule_compliance"]["success"]

    # 3. Consistency Checker
    lineage_map_path = output_dir / "lineage_map.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(lineage_map_path, "w", encoding="utf-8") as f:
        f.write('{"journeys": {"pj-100": {"patient_id": "pat-100"}}}')

    checker = ConsistencyChecker(state_manager, events, docs, lineage_map_path, output_dir)
    report_file = checker.check_all()
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        full_report = json.load(f)
    assert full_report["success"]
