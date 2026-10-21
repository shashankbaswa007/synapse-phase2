"""
Consistency Checker for Synapse Phase 2.
Performs cross-layer validation across database records, event logs, lineage map, and document outputs.
Outputs a machine-readable validation report (integrity_report.json).
"""

import json
from typing import Dict, Any, List
from pathlib import Path

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentMetadata
from synapse_simulator.validation.document_validator import DocumentValidator
from synapse_simulator.validation.integrity_auditor import IntegrityAuditor


class ConsistencyChecker:
    """Verifies that Database, Event Log, Lineage Map, and Documents are consistent across layers."""

    def __init__(
        self,
        state_manager: StateManager,
        committed_events: List[DomainEvent],
        generated_docs: Dict[str, DocumentMetadata],
        lineage_map_path: Path,
        output_dir: Path,
    ):
        self.state_manager = state_manager
        self.committed_events = committed_events
        self.generated_docs = generated_docs
        self.lineage_map_path = lineage_map_path
        self.output_dir = output_dir

        self.doc_validator = DocumentValidator(state_manager)
        self.auditor = IntegrityAuditor(state_manager, committed_events)

    def check_all(self) -> Path:
        """Execute full cross-layer consistency checks and output integrity_report.json."""
        report: Dict[str, Any] = {
            "metadata": {
                "generated_at": None,
                "total_patients": len(self.state_manager._store.get("patient.patients", {})),
                "total_events": len(self.committed_events),
                "total_documents": len(self.generated_docs),
            },
            "document_validation": {
                "success": True,
                "validated_count": 0,
                "failed_count": 0,
                "mismatches": [],
            },
            "deep_data_audit": {},
            "cross_layer_checks": {
                "success": True,
                "errors": [],
            },
        }

        # 1. Document-to-Database Validation
        doc_val_results = report["document_validation"]
        for doc_id, doc in self.generated_docs.items():
            doc_val_results["validated_count"] += 1
            is_valid, doc_errors = self.doc_validator.validate_document(doc)
            if not is_valid:
                doc_val_results["success"] = False
                doc_val_results["failed_count"] += 1
                doc_val_results["mismatches"].append({
                    "document_id": doc_id,
                    "errors": doc_errors,
                })

        # 2. Deep Data Structural Audit
        audit_results = self.auditor.audit_all()
        report["deep_data_audit"] = audit_results

        # 3. Cross-Layer Structural Checks
        cross_results = report["cross_layer_checks"]
        self._run_cross_layer_checks(cross_results)

        # 4. Global outcome check
        global_success = (
            doc_val_results["success"]
            and audit_results.get("success", False)
            and cross_results["success"]
        )
        report["success"] = global_success

        from datetime import datetime
        report["metadata"]["generated_at"] = datetime.now().isoformat()

        # Write to JSON file
        report_file = self.output_dir / "integrity_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        return report_file

    def _run_cross_layer_checks(self, results: Dict[str, Any]) -> None:
        """Run structural consistency checks across Database, Events, and Lineage Map."""
        errors = []

        # Check: Every patient journey has at least one matching document in standard flow
        patient_keys = self.state_manager._store.get("patient.patients", {}).keys()
        docs_by_patient = {}
        for doc in self.generated_docs.values():
            docs_by_patient[doc.patient_id] = docs_by_patient.get(doc.patient_id, 0) + 1

        for p_id in patient_keys:
            if p_id not in docs_by_patient:
                errors.append(f"Cross-layer mismatch: Patient '{p_id}' has database record but 0 generated documents.")

        # Check: Verify lineage map exists and aligns with events count
        if not self.lineage_map_path.exists():
            errors.append("Cross-layer mismatch: Lineage map file does not exist.")
        else:
            try:
                with open(self.lineage_map_path, "r", encoding="utf-8") as f:
                    l_map = json.load(f)
                mapped_journeys = len(l_map.get("journeys", {}))
                db_patients = len(patient_keys)
                if mapped_journeys != db_patients:
                    errors.append(
                        f"Cross-layer mismatch: Lineage map lists {mapped_journeys} patient journeys, "
                        f"but database states list {db_patients} patients."
                    )
            except Exception as e:
                errors.append(f"Failed to read lineage map for checks: {e}")

        results["success"] = len(errors) == 0
        results["errors"] = errors
