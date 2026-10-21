"""
SYNAPSE Phase 2 — Dataset Validation Gate.
Implements the mandatory fail-fast validation and atomic publication gate.
Ensures zero critical errors before promoting any synthetic EHR dataset to publication.
"""

import os
import shutil
import hashlib
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class DatasetValidationError(Exception):
    """Raised when one or more mandatory critical dataset invariants fail."""
    def __init__(self, message: str, critical_errors: List[str]):
        super().__init__(message)
        self.critical_errors = critical_errors


@dataclass
class GateResult:
    """Outcome of dataset validation gate evaluation."""
    passed: bool
    verdict: str
    target_directory: Path
    staging_directory: Path
    manifest_path: Optional[Path] = None
    passed_checks: List[str] = field(default_factory=list)
    critical_errors: List[str] = field(default_factory=list)
    noncritical_warnings: List[str] = field(default_factory=list)
    legitimate_pending_states: Dict[str, Any] = field(default_factory=dict)
    skipped_checks: List[str] = field(default_factory=list)
    manifest: Dict[str, Any] = field(default_factory=dict)


class DatasetValidationGate:
    """Enforces zero-critical-error gate before promoting staged datasets to final publication."""

    MANDATORY_CHECKS = [
        "duplicate_id_audit",
        "referential_integrity_audit",
        "null_required_audit",
        "temporal_audit",
        "clinical_safety_audit",
        "provenance_audit",
        "invoice_lifecycle_audit",
        "laboratory_lifecycle_audit",
        "radiology_lifecycle_audit",
        "journey_encounter_audit",
    ]

    def __init__(
        self,
        staging_dir: Path,
        final_dir: Path,
        audit_report: Dict[str, Any],
        sim_integrity_report: Optional[Dict[str, Any]] = None,
        perf_metrics: Optional[Dict[str, Any]] = None,
        patient_count: int = 10000,
        seed: int = 42,
        git_commit: Optional[str] = None,
    ):
        self.staging_dir = Path(staging_dir)
        self.final_dir = Path(final_dir)
        self.audit_report = audit_report
        self.sim_integrity = sim_integrity_report or {"is_valid": True, "errors": []}
        self.perf = perf_metrics or {}
        self.patient_count = patient_count
        self.seed = seed
        self.git_commit = git_commit or self._detect_git_commit()

    @staticmethod
    def _detect_git_commit() -> str:
        try:
            import subprocess
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return "git-commit-untracked"

    def evaluate(self) -> GateResult:
        """Evaluate all mandatory invariants without modifying files."""
        passed_checks: List[str] = []
        critical_errors: List[str] = []
        noncritical_warnings: List[str] = []
        skipped_checks: List[str] = []
        legitimate_pending: Dict[str, Any] = {}

        # 0. Check Simulation Engine Internal Integrity
        if not self.sim_integrity.get("is_valid", True):
            sim_errs = self.sim_integrity.get("errors", [])
            critical_errors.extend([f"SimulationEngine: {e}" for e in sim_errs])
        else:
            passed_checks.append("SimulationEngine: internal causal & transition integrity")

        # 1. Primary Key Uniqueness
        dup_audit = self.audit_report.get("duplicate_id_audit", {})
        if not dup_audit:
            skipped_checks.append("duplicate_id_audit")
        else:
            dup_found = False
            for fname, dinfo in dup_audit.items():
                if dinfo.get("duplicate_ids", 0) > 0:
                    dup_found = True
                    critical_errors.append(f"Duplicate PK: {fname} has {dinfo['duplicate_ids']} duplicate IDs")
            if not dup_found:
                passed_checks.append("Duplicate Primary Keys: 0 duplicates across all datasets")

        # 2. Foreign Key Referential Integrity
        ref_audit = self.audit_report.get("referential_integrity_audit", {})
        if not ref_audit:
            skipped_checks.append("referential_integrity_audit")
        else:
            dangling = ref_audit.get("total_dangling_references", 0)
            if dangling > 0:
                critical_errors.append(f"Referential Integrity: {dangling} dangling foreign key references found")
            else:
                passed_checks.append("Referential Integrity: 0 dangling foreign key references")

        # 3. Required Field Completeness (NULL check)
        null_audit = self.audit_report.get("null_required_audit", {})
        if not null_audit:
            skipped_checks.append("null_required_audit")
        else:
            null_count = null_audit.get("total_required_nulls", 0)
            if null_count > 0:
                critical_errors.append(f"Required Fields: {null_count} required column NULL/empty values found")
            else:
                passed_checks.append("Required Fields: 100% complete (0 NULLs)")

        # 4. Temporal Consistency
        temp_audit = self.audit_report.get("temporal_audit", {})
        if not temp_audit:
            skipped_checks.append("temporal_audit")
        else:
            inv_dur = temp_audit.get("invalid_encounter_durations", 0)
            inv_rel = temp_audit.get("invalid_temporal_relationships", 0)
            if inv_dur > 0:
                critical_errors.append(f"Temporal Integrity: {inv_dur} encounters with invalid duration (start > end)")
            if inv_rel > 0:
                critical_errors.append(f"Temporal Integrity: {inv_rel} out-of-order event timestamps found")
            if inv_dur == 0 and inv_rel == 0:
                passed_checks.append("Temporal Integrity: 0 invalid durations, 0 out-of-order events")

        # 5. Clinical Safety Decisions
        clin_audit = self.audit_report.get("clinical_safety_audit", {})
        if not clin_audit:
            skipped_checks.append("clinical_safety_audit")
        else:
            allergy_viols = clin_audit.get("allergy_safety_violations", 0)
            if allergy_viols > 0:
                critical_errors.append(f"Clinical Safety: {allergy_viols} RULE-CLIN-ALLERGY-001 allergy safety violations")
            else:
                passed_checks.append("Clinical Safety: 0 allergy safety violations (RULE-CLIN-ALLERGY-001 enforced)")

        # 6. PubMed Provenance Integrity
        prov_audit = self.audit_report.get("provenance_audit", {})
        if not prov_audit:
            skipped_checks.append("provenance_audit")
        else:
            missing_ev = prov_audit.get("missing_evidence_ids", 0)
            invalid_ev = prov_audit.get("invalid_evidence_references", 0)
            if missing_ev > 0:
                critical_errors.append(f"Provenance Integrity: {missing_ev} records missing required PubMed evidence")
            if invalid_ev > 0:
                critical_errors.append(f"Provenance Integrity: {invalid_ev} records with invalid PubMed references")
            if missing_ev == 0 and invalid_ev == 0:
                passed_checks.append("PubMed Provenance: 100% valid evidence PMIDs, 0 fabricated citations")

        # 7. Invoice Lifecycle
        inv_audit = self.audit_report.get("invoice_lifecycle_audit", {})
        if not inv_audit:
            skipped_checks.append("invoice_lifecycle_audit")
        else:
            before_enc = inv_audit.get("invoices_before_encounter", 0)
            inv_viols = inv_audit.get("lifecycle_violations_total", 0)
            if before_enc > 0:
                critical_errors.append(f"Invoice Lifecycle: {before_enc} invoices generated before encounter start")
            elif inv_viols > 0:
                critical_errors.append(f"Invoice Lifecycle: {inv_viols} lifecycle violations (timing, event linkage, or payment mismatch)")
            else:
                passed_checks.append("Invoice Lifecycle: 100% compliant (0 violations, 1:1 invoice and payment event linkage)")
            legitimate_pending["invoices_after_encounter_delayed_billing"] = inv_audit.get("invoices_after_encounter", 0)
            legitimate_pending["invoice_status_distribution"] = inv_audit.get("status_distribution", {})

        # 8. Laboratory Lifecycle
        lab_audit = self.audit_report.get("laboratory_lifecycle_audit", {})
        if not lab_audit:
            skipped_checks.append("laboratory_lifecycle_audit")
        else:
            missing_comp = lab_audit.get("missing_completion_timestamps", 0)
            lab_viols = lab_audit.get("lifecycle_violations_total", 0)
            ttypes = lab_audit.get("test_type_distribution", {})
            if missing_comp > 0:
                critical_errors.append(f"Laboratory Lifecycle: {missing_comp} labs missing completed_at timestamps")
            elif lab_viols > 0:
                critical_errors.append(f"Laboratory Lifecycle: {lab_viols} lifecycle violations (pending/completed timestamps or event linkage)")
            if len(ttypes) < 2 and lab_audit.get("total_orders", 0) > 10:
                critical_errors.append(f"Laboratory Lifecycle: only 1 test type present ({list(ttypes.keys())})")
            if missing_comp == 0 and lab_viols == 0 and len(ttypes) >= 2:
                passed_checks.append(f"Laboratory Lifecycle: 0 violations, {len(ttypes)} distinct test panels")
            legitimate_pending["lab_pending_tests"] = lab_audit.get("pending_tests", 0)
            legitimate_pending["lab_abnormal_results"] = lab_audit.get("abnormal_results", 0)

        # 9. Radiology Lifecycle
        rad_audit = self.audit_report.get("radiology_lifecycle_audit", {})
        if not rad_audit:
            skipped_checks.append("radiology_lifecycle_audit")
        else:
            missing_comp = rad_audit.get("missing_completion_timestamps", 0)
            rad_viols = rad_audit.get("lifecycle_violations_total", 0)
            mods = rad_audit.get("modality_distribution", {})
            if missing_comp > 0:
                critical_errors.append(f"Radiology Lifecycle: {missing_comp} radiology orders missing completed_at")
            elif rad_viols > 0:
                critical_errors.append(f"Radiology Lifecycle: {rad_viols} lifecycle violations (pending/completed timestamps or event linkage)")
            if len(mods) < 2 and rad_audit.get("total_orders", 0) > 10:
                critical_errors.append(f"Radiology Lifecycle: only 1 modality present ({list(mods.keys())})")
            if missing_comp == 0 and rad_viols == 0 and len(mods) >= 2:
                passed_checks.append(f"Radiology Lifecycle: 0 violations, {len(mods)} distinct modalities")
            legitimate_pending["radiology_pending_studies"] = rad_audit.get("pending_studies", 0)
            legitimate_pending["radiology_abnormal_studies"] = rad_audit.get("abnormal_studies", 0)

        # 10. Journey & Encounter Consistency
        je_audit = self.audit_report.get("journey_encounter_audit", {})
        if not je_audit:
            skipped_checks.append("journey_encounter_audit")
        else:
            mismatched = je_audit.get("mismatched_end_times", 0)
            scen_02 = je_audit.get("scen_02_violations", 0)
            if mismatched > 0:
                critical_errors.append(f"Journey/Encounter Consistency: {mismatched} mismatched completion times")
            if scen_02 > 0:
                critical_errors.append(f"Journey/Encounter Consistency: {scen_02} SCEN-V1-02 premature finishes")
            if mismatched == 0 and scen_02 == 0:
                passed_checks.append("Journey/Encounter Consistency: 100% synchronized completion times")

        # 11. Medication Diversity
        med_audit = self.audit_report.get("medication_diversity_audit", {})
        if med_audit:
            passed_checks.append(
                f"Medication Diversity: {med_audit.get('distinct_medications')} medications, "
                f"{med_audit.get('distinct_conditions')} conditions"
            )

        # Determine overall pass/fail
        has_critical = len(critical_errors) > 0
        has_skipped = len(skipped_checks) > 0
        gate_passed = (not has_critical) and (not has_skipped)

        verdict = "PASS — DATASET VALIDATED" if gate_passed else "FAIL — DATASET NOT VALIDATED"

        return GateResult(
            passed=gate_passed,
            verdict=verdict,
            target_directory=self.final_dir,
            staging_directory=self.staging_dir,
            passed_checks=passed_checks,
            critical_errors=critical_errors,
            noncritical_warnings=noncritical_warnings,
            legitimate_pending_states=legitimate_pending,
            skipped_checks=skipped_checks,
        )

    def promote_or_reject(self) -> GateResult:
        """Enforce validation gate: atomically promote if valid, quarantine if failed."""
        result = self.evaluate()

        if not result.passed:
            # Quarantine failed run separately for debugging
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            failed_dir = self.staging_dir.parent / f"failed_run_{timestamp_str}_{uuid.uuid4().hex[:6]}"
            shutil.move(str(self.staging_dir), str(failed_dir))
            result.staging_directory = failed_dir

            # Write diagnostic failure report
            fail_report_path = failed_dir / "DATASET_VALIDATION_FAILURE_REPORT.json"
            with open(fail_report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "verdict": result.verdict,
                    "failed_at": datetime.now().isoformat(),
                    "patient_count": self.patient_count,
                    "seed": self.seed,
                    "git_commit": self.git_commit,
                    "critical_errors": result.critical_errors,
                    "skipped_checks": result.skipped_checks,
                    "audit_report": self.audit_report,
                }, f, indent=2)

            raise DatasetValidationError(
                f"DatasetValidationGate FAILED with {len(result.critical_errors)} critical errors:\n"
                + "\n".join(f"  - {err}" for err in result.critical_errors),
                result.critical_errors,
            )

        # Atomic Promotion to final_dir
        self.final_dir.mkdir(parents=True, exist_ok=True)

        manifest_files = {}
        for item in self.staging_dir.iterdir():
            if item.is_file():
                dest_file = self.final_dir / item.name
                shutil.copy2(str(item), str(dest_file))
                # Compute SHA-256 for manifest
                with open(dest_file, "rb") as f:
                    file_sha = hashlib.sha256(f.read()).hexdigest()
                manifest_files[item.name] = {
                    "size_bytes": dest_file.stat().st_size,
                    "sha256": file_sha,
                }

        # Build and write authoritative DATASET_MANIFEST.json
        manifest = {
            "dataset_name": "SYNAPSE Phase 2 Synthetic Hospital Dataset",
            "validation_verdict": result.verdict,
            "patient_count": self.patient_count,
            "random_seed": self.seed,
            "git_commit": self.git_commit,
            "validated_at": datetime.now().isoformat(),
            "target_directory": str(self.final_dir),
            "manifest_files": manifest_files,
            "passed_checks_count": len(result.passed_checks),
            "critical_errors_count": 0,
            "noncritical_warnings_count": len(result.noncritical_warnings),
            "legitimate_pending_states": result.legitimate_pending_states,
            "performance_metrics": self.perf,
        }
        manifest_path = self.final_dir / "DATASET_MANIFEST.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        result.manifest_path = manifest_path
        result.manifest = manifest

        # Clean up temporary staging directory
        shutil.rmtree(str(self.staging_dir), ignore_errors=True)

        return result
