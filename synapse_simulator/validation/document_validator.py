"""
Document Validator for Synapse Phase 2.
Compares generated document metadata and content against authoritative structured database state.
"""

from typing import Dict, Any, List, Tuple
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.document_models import DocumentMetadata, DocumentType


class DocumentValidationError(Exception):
    """Raised when there is an integrity mismatch between a document and the database state."""
    pass


class DocumentValidator:
    """Validates rendered document data against database snapshots in StateManager."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def validate_document(self, doc: DocumentMetadata) -> Tuple[bool, List[str]]:
        """Validate document fields against the StateManager database records.
        Returns a tuple of (is_valid, list_of_errors)."""
        errors: List[str] = []

        # 1. Base references check
        table = doc.source_entity_table
        entity_id = doc.source_entity_id
        db_record = self.state_manager.get_entity_state(table, entity_id)

        if not db_record:
            errors.append(f"Referenced source record '{table}:{entity_id}' not found in database state.")
            return False, errors

        # 2. Check Patient ID linkage
        db_patient_id = db_record.get("patient_id")
        if db_patient_id and db_patient_id != doc.patient_id:
            errors.append(f"Patient ID mismatch: Document has '{doc.patient_id}' but database has '{db_patient_id}'.")

        # 3. Document-specific field checks
        if doc.document_type == DocumentType.PRESCRIPTION:
            self._validate_prescription(doc, db_record, errors)
        elif doc.document_type == DocumentType.INVOICE:
            self._validate_invoice(doc, db_record, errors)
        elif doc.document_type == DocumentType.LAB_REPORT:
            self._validate_lab_report(doc, db_record, errors)
        elif doc.document_type == DocumentType.RAD_REPORT:
            self._validate_rad_report(doc, db_record, errors)
        elif doc.document_type == DocumentType.DISCHARGE_SUMMARY:
            self._validate_discharge_summary(doc, db_record, errors)

        return len(errors) == 0, errors

    def _validate_prescription(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None:
        payload = doc.metadata_payload
        # Check drug class and drug name
        db_drug = db_record.get("drug_name")
        doc_drug = payload.get("drug_name")
        if db_drug != doc_drug:
            errors.append(f"Drug name mismatch: Prescription doc has '{doc_drug}' but database has '{db_drug}'.")

        db_class = db_record.get("drug_class")
        doc_class = payload.get("drug_class")
        if db_class != doc_class:
            errors.append(f"Drug class mismatch: Prescription doc has '{doc_class}' but database has '{db_class}'.")

        db_status = db_record.get("status")
        doc_status = payload.get("status")
        if db_status != doc_status:
            errors.append(f"Status mismatch: Prescription doc has '{doc_status}' but database has '{db_status}'.")

    def _validate_invoice(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None:
        payload = doc.metadata_payload
        db_total = db_record.get("total_amount")
        doc_total = payload.get("total")
        if db_total is not None and doc_total is not None:
            if abs(db_total - doc_total) > 0.001:
                errors.append(f"Invoice total amount mismatch: Document has {doc_total} but database has {db_total}.")

        db_status = db_record.get("status")
        doc_status = payload.get("status")
        if db_status != doc_status:
            errors.append(f"Invoice status mismatch: Document has '{doc_status}' but database has '{db_status}'.")

    def _validate_lab_report(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None:
        db_status = db_record.get("status")
        if db_status not in ("Completed", "Sample-Collected"):
            errors.append(f"Lab Report status mismatch: Lab order status in database is '{db_status}', should be Completed/Sample-Collected.")

    def _validate_rad_report(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None:
        db_status = db_record.get("status")
        if db_status not in ("Reported", "Image-Acquired"):
            errors.append(f"Radiology Report status mismatch: Radiology order status in database is '{db_status}', should be Reported.")

    def _validate_discharge_summary(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None:
        # Discharge summary source is clinical.encounters. Check status.
        db_status = db_record.get("status")
        # Standard OPD encounters are closed at end of journey
        if db_status != "Closed" and db_record:
            errors.append(f"Discharge Summary status mismatch: Clinical encounter status in database is '{db_status}', should be Closed.")
