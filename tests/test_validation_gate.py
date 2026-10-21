"""
Unit and regression tests for DatasetValidationGate.
Verifies fail-fast rejection of invalid datasets, quarantine of failed runs,
atomic promotion of validated datasets, and generation of DATASET_MANIFEST.json.
"""

import json
import pytest
import shutil
from pathlib import Path
from synapse_simulator.validation.validation_gate import DatasetValidationGate, DatasetValidationError


@pytest.fixture
def clean_staged_env(tmp_path):
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    final_dir = tmp_path / "final_dataset"

    # Create dummy dataset files
    (staging_dir / "patients.csv").write_text("patient_id,name\npat-1,Alice\n", encoding="utf-8")
    (staging_dir / "encounters.csv").write_text("encounter_id,patient_id\nenc-1,pat-1\n", encoding="utf-8")

    dummy_audit = {
        "overall_status": "PASS",
        "critical_errors": [],
        "duplicate_id_audit": {"patients.csv": {"duplicate_ids": 0, "unique_ids": 1}},
        "referential_integrity_audit": {"total_dangling_references": 0},
        "null_required_audit": {"total_required_nulls": 0},
        "temporal_audit": {"invalid_encounter_durations": 0, "invalid_temporal_relationships": 0},
        "clinical_safety_audit": {"allergy_safety_violations": 0},
        "provenance_audit": {"missing_evidence_ids": 0, "invalid_evidence_references": 0},
        "invoice_lifecycle_audit": {"invoices_before_encounter": 0, "invoices_during_encounter": 1, "invoices_after_encounter": 0, "status_distribution": {"Paid": 1}},
        "laboratory_lifecycle_audit": {"total_orders": 12, "missing_completion_timestamps": 0, "test_type_distribution": {"CBC": 6, "CRP": 6}},
        "radiology_lifecycle_audit": {"total_orders": 12, "missing_completion_timestamps": 0, "modality_distribution": {"Chest X-Ray": 6, "CT Head": 6}},
        "journey_encounter_audit": {"mismatched_end_times": 0, "scen_02_violations": 0},
        "medication_diversity_audit": {"distinct_medications": 5, "distinct_conditions": 4},
    }

    return staging_dir, final_dir, dummy_audit


def test_gate_passes_clean_dataset(clean_staged_env):
    staging_dir, final_dir, audit = clean_staged_env

    gate = DatasetValidationGate(
        staging_dir=staging_dir,
        final_dir=final_dir,
        audit_report=audit,
        patient_count=100,
        seed=42,
    )

    result = gate.promote_or_reject()
    assert result.passed is True
    assert "PASS — DATASET VALIDATED" in result.verdict
    assert final_dir.exists()
    assert (final_dir / "patients.csv").exists()
    assert (final_dir / "DATASET_MANIFEST.json").exists()
    assert not staging_dir.exists(), "Staging directory should be cleaned after promotion"

    # Verify manifest
    manifest = json.loads((final_dir / "DATASET_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["validation_verdict"] == "PASS — DATASET VALIDATED"
    assert manifest["patient_count"] == 100
    assert "patients.csv" in manifest["manifest_files"]


def test_gate_rejects_missing_lab_completion_timestamps(clean_staged_env):
    staging_dir, final_dir, audit = clean_staged_env
    # Inject missing lab completion timestamps defect
    audit["laboratory_lifecycle_audit"]["missing_completion_timestamps"] = 5

    gate = DatasetValidationGate(
        staging_dir=staging_dir,
        final_dir=final_dir,
        audit_report=audit,
    )

    with pytest.raises(DatasetValidationError) as excinfo:
        gate.promote_or_reject()

    assert "missing completed_at timestamps" in str(excinfo.value)
    assert not final_dir.exists(), "Final directory must NOT be published if validation fails"


def test_gate_rejects_dangling_foreign_keys(clean_staged_env):
    staging_dir, final_dir, audit = clean_staged_env
    # Inject dangling foreign key defect
    audit["referential_integrity_audit"]["total_dangling_references"] = 12

    gate = DatasetValidationGate(
        staging_dir=staging_dir,
        final_dir=final_dir,
        audit_report=audit,
    )

    with pytest.raises(DatasetValidationError) as excinfo:
        gate.promote_or_reject()

    assert "dangling foreign key references" in str(excinfo.value)
    assert not final_dir.exists()


def test_gate_rejects_invoice_timing_violations(clean_staged_env):
    staging_dir, final_dir, audit = clean_staged_env
    # Inject invoice generated before encounter start
    audit["invoice_lifecycle_audit"]["invoices_before_encounter"] = 9975

    gate = DatasetValidationGate(
        staging_dir=staging_dir,
        final_dir=final_dir,
        audit_report=audit,
    )

    with pytest.raises(DatasetValidationError) as excinfo:
        gate.promote_or_reject()

    assert "invoices generated before encounter start" in str(excinfo.value)
    assert not final_dir.exists()


def test_gate_rejects_journey_encounter_mismatches(clean_staged_env):
    staging_dir, final_dir, audit = clean_staged_env
    # Inject journey completed before encounter closure
    audit["journey_encounter_audit"]["mismatched_end_times"] = 256
    audit["journey_encounter_audit"]["scen_02_violations"] = 256

    gate = DatasetValidationGate(
        staging_dir=staging_dir,
        final_dir=final_dir,
        audit_report=audit,
    )

    with pytest.raises(DatasetValidationError) as excinfo:
        gate.promote_or_reject()

    assert "mismatched completion times" in str(excinfo.value)
    assert not final_dir.exists()
