"""
CSV Exporter for SYNAPSE Phase 2 Synthetic Hospital Simulator.
Centralized, deterministic export layer that serializes all validated structured simulation entities,
events, patient journeys, rule decisions, billing, inventory, and validation reports to UTF-8 CSV files.
"""

import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.workflows.model import PatientJourney
from synapse_simulator.datagen.models import MasterDataSnapshot, PatientContext


class CSVExporter:
    """Exports structured simulation state and history into normalized, relational CSV datasets."""

    def __init__(
        self,
        state_manager: StateManager,
        master_data: MasterDataSnapshot,
        patient_contexts: Dict[str, PatientContext],
        committed_events: List[DomainEvent],
        journeys: List[PatientJourney],
        trace_log: Optional[List[Dict[str, Any]]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        module_runner: Optional[Any] = None,
        community_assessments: Optional[List[Any]] = None,
        community_bp_readings: Optional[List[Any]] = None,
    ):
        self.state_manager = state_manager
        self.master_data = master_data
        self.patient_contexts = patient_contexts
        self.committed_events = committed_events
        self.journeys = journeys
        self.trace_log = trace_log or []
        self.metrics = metrics or {}
        self.output_dir = output_dir or Path("./output/phase2")
        self.module_runner = module_runner
        self.community_assessments = community_assessments or []
        self.community_bp_readings = community_bp_readings or []

        # Subdirectories for CSV outputs
        self.dirs = {
            "master_data": self.output_dir / "master_data",
            "patients": self.output_dir / "patients",
            "clinical": self.output_dir / "clinical",
            "diagnostics": self.output_dir / "diagnostics",
            "pharmacy": self.output_dir / "pharmacy",
            "operational": self.output_dir / "operational",
            "billing": self.output_dir / "billing",
            "events": self.output_dir / "events",
            "journeys": self.output_dir / "journeys",
            "validation": self.output_dir / "validation",
            "metadata": self.output_dir / "metadata",
        }
        self._cached_patient_enc_map: Optional[Dict[str, str]] = None

    def get_canonical_encounter_id(self, pid: Optional[str]) -> str:
        """Look up the canonical encounter_id for a patient_id."""
        if not pid:
            return ""
        if self._cached_patient_enc_map is None:
            enc_table = self.state_manager._store.get("clinical.encounters", {})
            self._cached_patient_enc_map = {}
            for enc_id, enc in enc_table.items():
                p = enc.get("patient_id")
                if p:
                    self._cached_patient_enc_map[p] = enc_id
            for p, pctx in self.patient_contexts.items():
                if pctx.encounter_id and p not in self._cached_patient_enc_map:
                    self._cached_patient_enc_map[p] = pctx.encounter_id
        return self._cached_patient_enc_map.get(pid, "")

    def _write_csv(self, file_path: Path, headers: List[str], rows: List[List[Any]]) -> Optional[Path]:
        """Write rows to UTF-8 CSV. Always writes header row so schema contracts are preserved."""
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([str(val) if val is not None else "" for val in row])

        return file_path

    def export_all(self) -> Dict[str, Path]:
        """Export all structured datasets to CSV."""
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        exported_files: Dict[str, Path] = {}

        # 1. Master Data CSVs
        res = self._export_master_data()
        exported_files.update(res)

        # 2. Patient CSVs
        res = self._export_patient_data()
        exported_files.update(res)

        # 3. Clinical CSVs
        res = self._export_clinical_data()
        exported_files.update(res)

        # 4. Diagnostic CSVs
        res = self._export_diagnostic_data()
        exported_files.update(res)

        # 5. Pharmacy CSVs
        res = self._export_pharmacy_data()
        exported_files.update(res)

        # 6. Operational & Inventory CSVs
        res = self._export_operational_data()
        exported_files.update(res)

        # 7. Billing CSVs
        res = self._export_billing_data()
        exported_files.update(res)

        # 8. Event CSV
        res = self._export_events()
        exported_files.update(res)

        # 9. Patient Journey CSVs
        res = self._export_journeys()
        exported_files.update(res)

        # 10. Rule Decisions CSV
        res = self._export_rule_decisions()
        exported_files.update(res)

        # 11. Simulation Metadata CSV
        res = self._export_metadata()
        exported_files.update(res)

        # 12. Simplified Relational CSV Dataset (data/synthetic/*.csv)
        s_target = (self.output_dir / "synthetic") if self.output_dir else None
        res = self.export_simplified_dataset(target_dir=s_target)
        exported_files.update(res)

        return exported_files


    def _export_master_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["master_data"]

        # departments.csv
        dept_rows = [
            [d.get("department_id"), d.get("department_name"), d.get("type", "Clinical"), d.get("status", "Active")]
            for d in self.master_data.departments
        ]
        p = self._write_csv(dir_path / "departments.csv", ["department_id", "department_name", "type", "status"], dept_rows)
        if p: out["departments.csv"] = p

        # doctors.csv
        doc_rows = [
            [s.staff_id, s.department_id, s.name, s.specialization or "General Medicine", s.qualification or "MD", "Active"]
            for s in self.master_data.doctors
        ]
        p = self._write_csv(dir_path / "doctors.csv", ["doctor_id", "department_id", "name", "specialization", "qualification", "status"], doc_rows)
        if p: out["doctors.csv"] = p

        # nurses.csv
        nurse_rows = [
            [s.staff_id, s.department_id, s.name, s.role, "Active"]
            for s in self.master_data.staff if s.role.lower() == "nurse"
        ]
        p = self._write_csv(dir_path / "nurses.csv", ["nurse_id", "department_id", "name", "role", "status"], nurse_rows)
        if p: out["nurses.csv"] = p

        # staff.csv
        staff_rows = [
            [s.staff_id, s.department_id, s.name, s.role, s.specialization or "", s.qualification or "", "Active"]
            for s in self.master_data.staff
        ]
        p = self._write_csv(dir_path / "staff.csv", ["staff_id", "department_id", "name", "role", "specialization", "qualification", "status"], staff_rows)
        if p: out["staff.csv"] = p

        # rooms.csv
        room_rows = [
            [r.room_id, r.room_name, r.department_id, r.floor, r.room_type]
            for r in self.master_data.rooms
        ]
        p = self._write_csv(dir_path / "rooms.csv", ["room_id", "room_name", "department_id", "floor", "room_type"], room_rows)
        if p: out["rooms.csv"] = p

        # beds.csv
        bed_rows = []
        for i, r in enumerate(self.master_data.rooms):
            if r.room_type in ("inpatient", "icu", "ward"):
                for b_num in range(1, 3):
                    bed_rows.append([f"bed-{r.room_id}-{b_num}", r.room_id, r.department_id, f"Bed {b_num}", "Available"])
        p = self._write_csv(dir_path / "beds.csv", ["bed_id", "room_id", "department_id", "bed_number", "status"], bed_rows)
        if p: out["beds.csv"] = p

        # medicines.csv
        med_rows = [
            [inv.batch_id, inv.drug_name, inv.drug_class, "unit", inv.status]
            for inv in self.master_data.inventory
        ]
        p = self._write_csv(dir_path / "medicines.csv", ["medicine_id", "name", "category", "stock_unit", "status"], med_rows)
        if p: out["medicines.csv"] = p

        return out

    def _export_patient_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["patients"]

        patient_rows = []
        allergies_rows = []
        history_rows = []
        chronic_rows = []
        insurance_rows = []
        family_rows = []

        patient_table = self.state_manager._store.get("patient.patients", {})

        for pid, pctx in self.patient_contexts.items():
            p_state = patient_table.get(pid, {})
            status = p_state.get("status", "Active")
            j_id = p_state.get("journey_id", f"j-{pid}")

            patient_rows.append([
                pid, j_id, pctx.scenario_id, pctx.name, pctx.gender, pctx.age, pctx.blood_group, pctx.insurance_type, status
            ])

            for idx, alg in enumerate(pctx.allergies):
                allergies_rows.append([f"alg-{pid}-{idx+1}", pid, alg, "High" if alg == "Penicillin" else "Moderate"])

            for idx, cond in enumerate(pctx.chronic_conditions):
                chronic_rows.append([f"chr-{pid}-{idx+1}", pid, cond, "Managed"])
                history_rows.append([f"hist-{pid}-{idx+1}", pid, f"History of {cond}", "2024-01-01", "Resolved"])

            insurance_rows.append([f"ins-{pid}", pid, f"{pctx.insurance_type} Healthcare", f"POL-{pid}", pctx.insurance_type])
            family_rows.append([f"fam-{pid}-1", pid, "Parent", "Hypertension"])

        p = self._write_csv(dir_path / "patients.csv", ["patient_id", "journey_id", "scenario_id", "name", "gender", "age", "blood_group", "insurance_type", "status"], patient_rows)
        if p: out["patients.csv"] = p

        p = self._write_csv(dir_path / "patient_allergies.csv", ["allergy_id", "patient_id", "allergen", "severity"], allergies_rows)
        if p: out["patient_allergies.csv"] = p

        p = self._write_csv(dir_path / "patient_medical_history.csv", ["history_id", "patient_id", "condition", "onset_date", "status"], history_rows)
        if p: out["patient_medical_history.csv"] = p

        p = self._write_csv(dir_path / "patient_chronic_conditions.csv", ["condition_id", "patient_id", "condition_name", "severity"], chronic_rows)
        if p: out["patient_chronic_conditions.csv"] = p

        p = self._write_csv(dir_path / "patient_insurance.csv", ["insurance_id", "patient_id", "provider", "policy_number", "insurance_type"], insurance_rows)
        if p: out["patient_insurance.csv"] = p

        p = self._write_csv(dir_path / "patient_family_history.csv", ["family_history_id", "patient_id", "relation", "condition"], family_rows)
        if p: out["patient_family_history.csv"] = p

        return out

    def _export_clinical_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["clinical"]

        # appointments.csv
        app_table = self.state_manager._store.get("clinical.appointments", {})
        app_rows = []
        for app_id, app in app_table.items():
            app_rows.append([
                app_id, app.get("patient_id"), app.get("doctor_id", "doc-001"), app.get("department_id", "dept-opd"),
                app.get("scheduled_at", app.get("created_at")), app.get("status", "Scheduled")
            ])
        p = self._write_csv(dir_path / "appointments.csv", ["appointment_id", "patient_id", "doctor_id", "department_id", "scheduled_at", "status"], app_rows)
        if p: out["appointments.csv"] = p

        # consultations.csv
        enc_table = self.state_manager._store.get("clinical.encounters", {})
        consult_rows = []
        for enc_id, enc in enc_table.items():
            pid = enc.get("patient_id")
            pctx = self.patient_contexts.get(pid)
            doc_id = pctx.assigned_doctor_id if pctx and pctx.assigned_doctor_id else "doc-001"
            consult_rows.append([
                enc_id, enc.get("journey_id"), pid, doc_id, enc.get("start_time"), enc.get("end_time"), enc.get("status"), "Routine Consultation"
            ])
        p = self._write_csv(dir_path / "consultations.csv", ["consultation_id", "journey_id", "patient_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"], consult_rows)
        if p: out["consultations.csv"] = p

        # diagnoses.csv
        diag_rows = []
        for pid, pctx in self.patient_contexts.items():
            if pctx.diagnosis_code:
                enc_id = self.get_canonical_encounter_id(pid)
                diag_rows.append([
                    f"diag-{pid}", pid, enc_id, pctx.diagnosis_code, pctx.diagnosis_name or "Clinical Diagnosis", "Confirmed"
                ])
        p = self._write_csv(dir_path / "diagnoses.csv", ["diagnosis_id", "patient_id", "consultation_id", "diagnosis_code", "description", "status"], diag_rows)
        if p: out["diagnoses.csv"] = p

        # prescriptions.csv
        rx_table = self.state_manager._store.get("pharmacy.prescriptions", {})
        rx_rows = []
        for rx_id, rx in rx_table.items():
            pid = rx.get("patient_id")
            enc_id = rx.get("consultation_id") or rx.get("encounter_id") or self.get_canonical_encounter_id(pid)
            rx_rows.append([
                rx_id, pid, enc_id, rx.get("drug_name", "Amoxicillin"), rx.get("drug_name"),
                rx.get("dosage", "500mg"), rx.get("quantity", 10), rx.get("status", "Created")
            ])
        p = self._write_csv(dir_path / "prescriptions.csv", ["prescription_id", "patient_id", "consultation_id", "medicine_id", "drug_name", "dosage", "quantity", "status"], rx_rows)
        if p: out["prescriptions.csv"] = p

        # discharges.csv
        discharge_rows = []
        for evt in self.committed_events:
            if evt.event_type in ("PatientDischarged", "PatientJourneyCompleted"):
                pid = evt.payload.get("patient_id") or (evt.patient_journey_id.replace("j-", "p-") if evt.patient_journey_id else "")
                discharge_rows.append([
                    f"dis-{evt.event_id}", pid, evt.patient_journey_id, evt.timestamp, "doc-001", "Completed"
                ])
        p = self._write_csv(dir_path / "discharges.csv", ["discharge_id", "patient_id", "journey_id", "discharged_at", "discharged_by", "status"], discharge_rows)
        if p: out["discharges.csv"] = p

        return out

    def _export_diagnostic_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["diagnostics"]

        lab_order_table = self.state_manager._store.get("laboratory.laboratory_orders", {})
        lab_order_rows = []
        lab_sample_rows = []
        lab_report_rows = []

        for l_id, l_ord in lab_order_table.items():
            pid = l_ord.get("patient_id")
            status = l_ord.get("status", "Ordered")
            enc_id = l_ord.get("encounter_id") or self.get_canonical_encounter_id(pid)
            lab_order_rows.append([
                l_id, pid, enc_id, "doc-001", l_ord.get("test_type", "CBC"), l_ord.get("ordered_at", l_ord.get("created_at")), status
            ])
            if status in ("Sample-Collected", "Completed", "Reported"):
                lab_sample_rows.append([f"samp-{l_id}", l_id, pid, l_ord.get("ordered_at"), "Collected"])
            if status in ("Completed", "Reported"):
                lab_report_rows.append([f"rep-{l_id}", l_id, pid, l_ord.get("test_type", "CBC"), False, l_ord.get("completed_at"), "Completed"])

        p = self._write_csv(dir_path / "lab_orders.csv", ["order_id", "patient_id", "consultation_id", "doctor_id", "test_type", "ordered_at", "status"], lab_order_rows)
        if p: out["lab_orders.csv"] = p

        p = self._write_csv(dir_path / "lab_samples.csv", ["sample_id", "order_id", "patient_id", "collected_at", "status"], lab_sample_rows)
        if p: out["lab_samples.csv"] = p

        p = self._write_csv(dir_path / "lab_reports.csv", ["report_id", "order_id", "patient_id", "test_name", "is_abnormal", "completed_at", "status"], lab_report_rows)
        if p: out["lab_reports.csv"] = p

        rad_order_table = self.state_manager._store.get("radiology.radiology_orders", {})
        rad_order_rows = []
        rad_report_rows = []

        for r_id, r_ord in rad_order_table.items():
            pid = r_ord.get("patient_id")
            status = r_ord.get("status", "Ordered")
            enc_id = r_ord.get("encounter_id") or self.get_canonical_encounter_id(pid)
            rad_order_rows.append([
                r_id, pid, enc_id, "doc-001", r_ord.get("modality", "Chest X-Ray"), r_ord.get("ordered_at"), status
            ])
            if status in ("Completed", "Reported"):
                rad_report_rows.append([
                    f"radrep-{r_id}", r_id, pid, r_ord.get("modality", "Chest X-Ray"), "Normal lung fields", "Clear", False, r_ord.get("completed_at"), "Completed"
                ])

        p = self._write_csv(dir_path / "radiology_orders.csv", ["order_id", "patient_id", "consultation_id", "doctor_id", "modality", "ordered_at", "status"], rad_order_rows)
        if p: out["radiology_orders.csv"] = p

        p = self._write_csv(dir_path / "radiology_reports.csv", ["report_id", "order_id", "patient_id", "modality", "findings", "impression", "is_abnormal", "completed_at", "status"], rad_report_rows)
        if p: out["radiology_reports.csv"] = p

        return out

    def _export_pharmacy_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["pharmacy"]

        pharmacy_orders_rows = []
        dispensing_rows = []
        pharm_tx_rows = []

        rx_table = self.state_manager._store.get("pharmacy.prescriptions", {})
        for rx_id, rx in rx_table.items():
            pid = rx.get("patient_id")
            status = rx.get("status", "Created")
            drug_name = rx.get("drug_name", "Amoxicillin")

            pharmacy_orders_rows.append([rx_id, pid, drug_name, rx.get("dosage", "500mg"), rx.get("quantity", 10), status])

            if status in ("Dispensed", "Completed"):
                disp_id = f"disp-{rx_id}"
                dispensing_rows.append([disp_id, rx_id, pid, drug_name, rx.get("quantity", 10), rx.get("dispensed_at"), "Dispensed"])
                pharm_tx_rows.append([f"ptx-{rx_id}", disp_id, pid, drug_name, rx.get("quantity", 10), rx.get("dispensed_at")])

        p = self._write_csv(dir_path / "pharmacy_orders.csv", ["prescription_id", "patient_id", "medicine_id", "dosage", "quantity", "status"], pharmacy_orders_rows)
        if p: out["pharmacy_orders.csv"] = p

        p = self._write_csv(dir_path / "medication_dispensing.csv", ["dispensing_id", "prescription_id", "patient_id", "medicine_id", "dispensed_quantity", "dispensed_at", "status"], dispensing_rows)
        if p: out["medication_dispensing.csv"] = p

        p = self._write_csv(dir_path / "pharmacy_transactions.csv", ["transaction_id", "dispensing_id", "patient_id", "medicine_id", "quantity", "timestamp"], pharm_tx_rows)
        if p: out["pharmacy_transactions.csv"] = p

        return out

    def _export_operational_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["operational"]

        inv_table = self.state_manager._store.get("pharmacy.inventory_batches", {})
        inv_rows = []
        for b_id, b_data in inv_table.items():
            inv_rows.append([
                b_id, b_data.get("drug_name"), b_data.get("drug_name"), b_data.get("drug_class", "Antibiotic"),
                b_data.get("quantity_available"), b_data.get("quantity_initial"), b_data.get("unit_cost", 10.0), b_data.get("status", "Active")
            ])
        p = self._write_csv(dir_path / "inventory.csv", ["batch_id", "medicine_id", "drug_name", "drug_class", "quantity_available", "quantity_initial", "unit_cost", "status"], inv_rows)
        if p: out["inventory.csv"] = p

        inv_tx_rows = []
        for evt in self.committed_events:
            if evt.event_type in ("MedicineDispensed", "InventoryDepleted"):
                pid = evt.payload.get("patient_id")
                batch_id = evt.payload.get("batch_id") or evt.payload.get("pharmacy.inventory_batches") or "batch-001"
                inv_tx_rows.append([
                    f"itx-{evt.event_id}", batch_id, pid, evt.event_id, -evt.payload.get("quantity", 1), "Dispensation", evt.timestamp
                ])
        p = self._write_csv(dir_path / "inventory_transactions.csv", ["transaction_id", "batch_id", "patient_id", "event_id", "quantity_change", "transaction_type", "timestamp"], inv_tx_rows)
        if p: out["inventory_transactions.csv"] = p

        return out

    def _export_billing_data(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["billing"]

        inv_table = self.state_manager._store.get("finance.invoices", {})
        bill_rows = []
        item_rows = []
        payment_rows = []

        for inv_id, inv in inv_table.items():
            pid = inv.get("patient_id")
            j_id = inv.get("patient_journey_id", f"j-{pid}")
            status = inv.get("status", "Draft")
            total = inv.get("total_amount", 0.0)
            created = inv.get("created_at")

            bill_rows.append([inv_id, pid, j_id, total, status, created])

            line_items = inv.get("line_items", [])
            for idx, item in enumerate(line_items):
                item_rows.append([
                    f"item-{inv_id}-{idx+1}", inv_id, item.get("service_type", "Consultation"),
                    item.get("service_name", "OPD Consultation"), item.get("quantity", 1),
                    item.get("unit_price", 50.0), item.get("total_price", 50.0), item.get("source_entity_id", "")
                ])

            if status == "Paid":
                payment_rows.append([f"pay-{inv_id}", inv_id, pid, total, "Insurance/Cash", created, "Success"])

        p = self._write_csv(dir_path / "bills.csv", ["bill_id", "patient_id", "journey_id", "total_amount", "status", "created_at"], bill_rows)
        if p: out["bills.csv"] = p

        p = self._write_csv(dir_path / "bill_items.csv", ["item_id", "bill_id", "service_type", "service_name", "quantity", "unit_price", "total_price", "source_entity_id"], item_rows)
        if p: out["bill_items.csv"] = p

        p = self._write_csv(dir_path / "payments.csv", ["payment_id", "bill_id", "patient_id", "amount", "payment_method", "timestamp", "status"], payment_rows)
        if p: out["payments.csv"] = p

        return out

    def _export_events(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["events"]

        evt_rows = [
            [
                e.event_id, e.event_type, e.payload.get("patient_id") or "", e.patient_journey_id,
                e.timestamp, e.causation_id, e.correlation_id, e.causation_depth,
                e.payload.get("source_action", ""), e.producer_domain, e.status
            ]
            for e in self.committed_events
        ]
        p = self._write_csv(
            dir_path / "events.csv",
            ["event_id", "event_type", "patient_id", "patient_journey_id", "timestamp", "causation_id", "correlation_id", "causation_depth", "source_action", "source_department", "status"],
            evt_rows
        )
        if p: out["events.csv"] = p

        return out

    def _export_journeys(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["journeys"]

        journey_rows = []
        step_rows = []

        for j in self.journeys:
            journey_rows.append([
                j.journey_id, j.patient_id, j.scenario_id, j.start_time, j.end_time, j.status.value, j.outcome
            ])

            for step in j.trace_history:
                step_rows.append([
                    j.journey_id, step.get("step_id"), j.patient_id, step.get("action_type") or step.get("step_id"),
                    step.get("department", ""), step.get("timestamp"), step.get("status") or step.get("decision", ""),
                    step.get("event_id") or step.get("event_type", ""), step.get("causation_id", "")
                ])

        p = self._write_csv(dir_path / "patient_journeys.csv", ["journey_id", "patient_id", "scenario_id", "start_time", "end_time", "status", "outcome"], journey_rows)
        if p: out["patient_journeys.csv"] = p

        p = self._write_csv(dir_path / "patient_journey_steps.csv", ["journey_id", "step_id", "patient_id", "action_type", "department", "timestamp", "status", "event_id", "causation_id"], step_rows)
        if p: out["patient_journey_steps.csv"] = p

        return out

    def _export_rule_decisions(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["validation"]

        dec_rows = [
            [
                f"dec-{idx+1}", row.get("target_entity"), row.get("action"), row.get("rule_winning"),
                row.get("status"), row.get("reason", "Rule check passed"), row.get("time"), row.get("domain_event")
            ]
            for idx, row in enumerate(self.trace_log)
        ]
        p = self._write_csv(dir_path / "rule_decisions.csv", ["decision_id", "target_entity", "action", "rule_id", "decision", "reason", "timestamp", "domain_event"], dec_rows)
        if p: out["rule_decisions.csv"] = p

        return out

    def _export_metadata(self) -> Dict[str, Path]:
        out = {}
        dir_path = self.dirs["metadata"]

        meta_rows = [[k, str(v)] for k, v in self.metrics.items()]
        p = self._write_csv(dir_path / "simulation_metadata.csv", ["metric_name", "metric_value"], meta_rows)
        if p: out["simulation_metadata.csv"] = p

        return out

    def _validate_simplified_records(
        self,
        patient_rows: List[List[Any]],
        enc_rows: List[List[Any]],
        cond_rows: List[List[Any]],
        sym_rows: List[List[Any]],
        med_rows: List[List[Any]],
        lab_rows: List[List[Any]],
        rad_rows: List[List[Any]],
        inv_rows: List[List[Any]],
        pay_rows: List[List[Any]],
        evt_rows: List[List[Any]],
        journey_rows: List[List[Any]],
    ) -> None:
        """Validate referential integrity, patient consistency, provenance, and temporal rules before export.
        Fails loudly if any integrity invariant is violated.
        """
        patient_ids = {r[0] for r in patient_rows}
        enc_ids = {r[0] for r in enc_rows}
        enc_patient_map = {r[0]: r[1] for r in enc_rows}
        enc_time_map = {r[0]: (datetime.fromisoformat(r[4]), datetime.fromisoformat(r[5])) for r in enc_rows}
        cond_ids = {r[0] for r in cond_rows}
        inv_ids = {r[0] for r in inv_rows}
        inv_patient_map = {r[0]: r[1] for r in inv_rows}

        # 1. Referential integrity: conditions
        for r in cond_rows:
            cond_id, pid, enc_id = r[0], r[1], r[2]
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in conditions: condition_id='{cond_id}', patient_id='{pid}'")
            if enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in conditions: condition_id='{cond_id}', encounter_id='{enc_id}'")
            if enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in conditions: condition_id='{cond_id}', encounter_id='{enc_id}', enc.patient='{enc_patient_map.get(enc_id)}', cond.patient='{pid}'")

        # 2. Referential integrity: symptoms
        for r in sym_rows:
            sym_id, pid, enc_id, cond_id = r[0], r[1], r[2], r[3]
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in symptoms: symptom_id='{sym_id}', patient_id='{pid}'")
            if enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in symptoms: symptom_id='{sym_id}', encounter_id='{enc_id}'")
            if cond_id not in cond_ids:
                raise ValueError(f"Dangling condition reference in symptoms: symptom_id='{sym_id}', condition_id='{cond_id}'")
            if enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in symptoms: symptom_id='{sym_id}', enc.patient='{enc_patient_map.get(enc_id)}', sym.patient='{pid}'")

        # 3. Referential & provenance integrity: medications
        for r in med_rows:
            rx_id, pid, enc_id, cond_id = r[0], r[1], r[2], r[3]
            source, evidence_ids = r[8], r[9]
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in medications: medication_id='{rx_id}', patient_id='{pid}'")
            if enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in medications: medication_id='{rx_id}', encounter_id='{enc_id}'")
            if cond_id not in cond_ids:
                raise ValueError(f"Dangling condition reference in medications: medication_id='{rx_id}', condition_id='{cond_id}'")
            if enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in medications: medication_id='{rx_id}', encounter_id='{enc_id}', enc.patient='{enc_patient_map.get(enc_id)}', med.patient='{pid}'")
            if source == "pubmed_evidence" and (not evidence_ids or evidence_ids == "None" or evidence_ids == "[]"):
                raise ValueError(f"Missing PubMed evidence for pubmed-backed treatment: medication_id='{rx_id}', source='{source}'")
            if source == "internal_yaml+pubmed_evidence" and (not evidence_ids or evidence_ids == "None" or evidence_ids == "[]"):
                raise ValueError(f"Missing PubMed evidence for composite treatment: medication_id='{rx_id}', source='{source}'")

        # 4. Referential integrity & associations: labs
        for r in lab_rows:
            lab_id, pid, enc_id = r[0], r[1], r[2]
            if not pid or pid == "None":
                raise ValueError(f"NULL patient_id in lab record: lab_id='{lab_id}'")
            if not enc_id or enc_id == "None":
                raise ValueError(f"NULL encounter_id in lab record: lab_id='{lab_id}'")
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in labs: lab_id='{lab_id}', patient_id='{pid}'")
            if enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in labs: lab_id='{lab_id}', encounter_id='{enc_id}'")
            if enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in labs: lab_id='{lab_id}', encounter_id='{enc_id}', enc.patient='{enc_patient_map.get(enc_id)}', lab.patient='{pid}'")

        # 5. Referential integrity: radiology
        for r in rad_rows:
            rad_id, pid, enc_id = r[0], r[1], r[2]
            if not pid or pid == "None":
                raise ValueError(f"NULL patient_id in radiology record: rad_id='{rad_id}'")
            if not enc_id or enc_id == "None":
                raise ValueError(f"NULL encounter_id in radiology record: rad_id='{rad_id}'")
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in radiology: rad_id='{rad_id}', patient_id='{pid}'")
            if enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in radiology: rad_id='{rad_id}', encounter_id='{enc_id}'")
            if enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in radiology: rad_id='{rad_id}', encounter_id='{enc_id}', enc.patient='{enc_patient_map.get(enc_id)}', rad.patient='{pid}'")

        # 6. Referential integrity: invoices
        for r in inv_rows:
            inv_id, pid, enc_id = r[0], r[1], r[2]
            if not pid or pid == "None":
                raise ValueError(f"NULL patient_id in invoice record: inv_id='{inv_id}'")
            if not enc_id or enc_id == "None":
                raise ValueError(f"NULL encounter_id in invoice record: inv_id='{inv_id}'")
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in invoices: inv_id='{inv_id}', patient_id='{pid}'")
            if enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in invoices: inv_id='{inv_id}', encounter_id='{enc_id}'")
            if enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in invoices: inv_id='{inv_id}', encounter_id='{enc_id}', enc.patient='{enc_patient_map.get(enc_id)}', inv.patient='{pid}'")

        # 7. Referential integrity: payments
        for r in pay_rows:
            pay_id, inv_id, pid = r[0], r[1], r[2]
            if inv_id not in inv_ids:
                raise ValueError(f"Dangling invoice reference in payments: pay_id='{pay_id}', inv_id='{inv_id}'")
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in payments: pay_id='{pay_id}', patient_id='{pid}'")
            if inv_patient_map.get(inv_id) != pid:
                raise ValueError(f"Mismatched patient for invoice in payments: pay_id='{pay_id}', inv_id='{inv_id}', inv.patient='{inv_patient_map.get(inv_id)}', pay.patient='{pid}'")

        # 8. Referential integrity: journey traces
        for r in journey_rows:
            j_id, pid = r[0], r[1]
            if pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in journey_traces: journey_id='{j_id}', patient_id='{pid}'")

        # 9. Temporal integrity: encounters
        for r in enc_rows:
            enc_id, pid, st_str, et_str, status = r[0], r[1], r[4], r[5], r[6]
            st = datetime.fromisoformat(st_str)
            et = datetime.fromisoformat(et_str)
            if et < st:
                raise ValueError(f"Negative encounter duration: encounter_id='{enc_id}', start='{st}', end='{et}'")
            if status == "Closed" and et == st:
                raise ValueError(f"Zero duration for closed encounter: encounter_id='{enc_id}', start='{st}', end='{et}'")

        # 10. Temporal integrity & referential integrity: events
        post_encounter_types = {
            "PatientDischarged", "PatientJourneyCompleted", "EncounterCompleted",
            "BillingPaymentProcessed", "PaymentProcessed", "FollowUpScheduled",
        }
        for r in evt_rows:
            evt_id, pid, enc_id, evt_type, ts_str = r[0], r[1], r[2], r[3], r[5]
            if pid and pid not in patient_ids:
                raise ValueError(f"Dangling patient reference in events: event_id='{evt_id}', patient_id='{pid}'")
            if enc_id and enc_id not in enc_ids:
                raise ValueError(f"Dangling encounter reference in events: event_id='{evt_id}', encounter_id='{enc_id}'")
            if enc_id and pid and enc_patient_map.get(enc_id) != pid:
                raise ValueError(f"Mismatched patient for encounter in events: event_id='{evt_id}', encounter_id='{enc_id}', enc.patient='{enc_patient_map.get(enc_id)}', evt.patient='{pid}'")
            if enc_id and enc_id in enc_time_map:
                st, et = enc_time_map[enc_id]
                evt_ts = datetime.fromisoformat(ts_str) if isinstance(ts_str, str) else ts_str
                if evt_ts < st:
                    raise ValueError(f"Event occurred before encounter start: event_id='{evt_id}', type='{evt_type}', ts='{evt_ts}', enc_start='{st}'")
                if evt_type not in post_encounter_types and evt_ts > et:
                    raise ValueError(f"In-encounter event occurred after encounter end: event_id='{evt_id}', type='{evt_type}', ts='{evt_ts}', enc_end='{et}'")

    def export_simplified_dataset(self, target_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export simplified flat relational CSV dataset to target_dir (e.g. data/synthetic/*.csv)."""
        s_dir = target_dir or ((self.output_dir / "synthetic") if self.output_dir else Path("data/synthetic"))
        s_dir.mkdir(parents=True, exist_ok=True)
        exported: Dict[str, Path] = {}

        # Ensure billing documents and finance invoices are generated if not already in state
        if not self.state_manager._store.get("finance.invoices"):
            from synapse_simulator.exporter.document_generator import DocumentGenerator
            import shutil
            tmp_doc_dir = s_dir / ".doc_cache_temp"
            doc_gen = DocumentGenerator(self.state_manager, self.committed_events, tmp_doc_dir)
            doc_gen.generate_all()
            shutil.rmtree(tmp_doc_dir, ignore_errors=True)

        # Pre-compute fast O(1) lookup tables to guarantee linear export performance at scale
        journey_patient_map = {j.journey_id: j.patient_id for j in self.journeys}
        enc_table = self.state_manager._store.get("clinical.encounters", {})
        patient_encounter_map = {
            enc.get("patient_id"): enc_id
            for enc_id, enc in enc_table.items()
            if enc.get("patient_id")
        }

        def get_patient_enc_id(pid: str) -> str:
            return patient_encounter_map.get(pid) or self.get_canonical_encounter_id(pid)

        # 1. patients.csv
        patient_rows = []
        for pid, pctx in self.patient_contexts.items():
            patient_rows.append([
                pid, pctx.name, pctx.age, pctx.gender, pctx.blood_group, pctx.insurance_type, "Active"
            ])

        # 2. encounters.csv
        enc_rows = []
        for enc_id, enc in enc_table.items():
            pid = enc.get("patient_id")
            pctx = self.patient_contexts.get(pid)
            doc_id = pctx.assigned_doctor_id if pctx and pctx.assigned_doctor_id else "doc-001"
            st = enc.get("start_time") or "2026-01-01T08:00:00"
            et = enc.get("end_time") or st
            enc_rows.append([
                enc_id, pid, enc.get("journey_id", f"j-{pid}"), doc_id, st, et, enc.get("status", "Closed"), "Routine OPD Consultation"
            ])

        # 3. conditions.csv
        consult_table = self.state_manager._store.get("clinical.consultations", {})
        cond_rows = []
        patient_conditions: List[Dict[str, str]] = []
        cond_idx_map: Dict[str, int] = {}

        for consult_id, consult in consult_table.items():
            pid = consult.get("patient_id")
            diag_code = consult.get("diagnosis_code") or consult.get("condition_code")
            diag_name = consult.get("diagnosis_name") or consult.get("condition_name")
            if pid and diag_code:
                enc_id = consult.get("encounter_id") or get_patient_enc_id(pid)
                cond_idx_map[pid] = cond_idx_map.get(pid, 0) + 1
                cond_id = consult.get("condition_id") or (f"cond-{pid}" if cond_idx_map[pid] == 1 else f"cond-{pid}-{cond_idx_map[pid]}")
                status = consult.get("status", "Active")
                patient_conditions.append({
                    "patient_id": pid, "condition_id": cond_id, "encounter_id": enc_id, "diagnosis_code": diag_code
                })
                cond_rows.append([
                    cond_id, pid, enc_id, diag_code, diag_name, status
                ])

        # Fallback to patient_contexts if consult_table was empty
        if not cond_rows:
            for pid, pctx in self.patient_contexts.items():
                if pctx.diagnosis_code:
                    enc_id = get_patient_enc_id(pid)
                    cond_id = f"cond-{pid}"
                    patient_conditions.append({
                        "patient_id": pid, "condition_id": cond_id, "encounter_id": enc_id, "diagnosis_code": pctx.diagnosis_code
                    })
                    cond_rows.append([
                        cond_id, pid, enc_id, pctx.diagnosis_code, pctx.diagnosis_name or "Clinical Diagnosis", "Active"
                    ])

        # 4. symptoms.csv
        sym_rows = []
        from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
        kb = MedicalKnowledgeBase()
        kb.load(enable_pubmed=False)

        sym_idx_map: Dict[str, int] = {}
        for p_cond in patient_conditions:
            pid = p_cond["patient_id"]
            cond_id = p_cond["condition_id"]
            enc_id = p_cond["encounter_id"]
            d_code = p_cond["diagnosis_code"]
            diag_entry = kb.get_diagnosis_by_code(d_code)
            symptoms_list = diag_entry.symptoms if diag_entry else ["fatigue", "fever"]
            for sym in symptoms_list:
                sym_idx_map[pid] = sym_idx_map.get(pid, 0) + 1
                sym_rows.append([
                    f"sym-{pid}-{sym_idx_map[pid]}", pid, enc_id, cond_id, sym
                ])

        # 5. medications.csv
        valid_cond_ids = {r[0] for r in cond_rows}
        first_cond_for_patient = {p_cond["patient_id"]: p_cond["condition_id"] for p_cond in patient_conditions}
        enc_to_cond = {p_cond["encounter_id"]: p_cond["condition_id"] for p_cond in patient_conditions if p_cond.get("encounter_id")}
        drug_indication_map = {
            "metformin": "E11.9",
            "glimepiride": "E11.9",
            "insulin": "E11.9",
            "amlodipine": "I10",
            "telmisartan": "I10",
            "losartan": "I10",
            "atenolol": "I10",
            "amoxicillin": "J06.9",
            "azithromycin": "J06.9",
            "paracetamol": "J06.9",
        }
        rx_table = self.state_manager._store.get("pharmacy.prescriptions", {})
        med_rows = []
        for rx_id, rx in rx_table.items():
            pid = rx.get("patient_id")
            enc_id = rx.get("consultation_id") or rx.get("encounter_id") or get_patient_enc_id(pid)
            ev_ids = rx.get("evidence_ids", [])
            ev_str = ";".join(ev_ids) if isinstance(ev_ids, list) else str(ev_ids)
            target_cond_id = rx.get("condition_id")
            drug_name_lower = (rx.get("drug_name") or "").lower()
            indicated_code = None
            for d_key, c_code in drug_indication_map.items():
                if d_key in drug_name_lower:
                    indicated_code = c_code
                    break

            if not target_cond_id or target_cond_id not in valid_cond_ids:
                if indicated_code:
                    for p_cond in patient_conditions:
                        if p_cond["patient_id"] == pid and p_cond["diagnosis_code"] == indicated_code:
                            target_cond_id = p_cond["condition_id"]
                            break
                if not target_cond_id or target_cond_id not in valid_cond_ids:
                    if enc_id in enc_to_cond:
                        target_cond_id = enc_to_cond[enc_id]
                    elif pid in first_cond_for_patient:
                        target_cond_id = first_cond_for_patient[pid]
                    elif f"cond-{pid}" in valid_cond_ids:
                        target_cond_id = f"cond-{pid}"
                    else:
                        continue  # Avoid dangling FK in medications
            med_rows.append([
                rx_id, pid, enc_id, target_cond_id, rx.get("drug_name"), rx.get("drug_class", ""),
                rx.get("dosage", "500mg"), rx.get("frequency", "OD"), rx.get("source", "internal_yaml"),
                ev_str, rx.get("status", "Issued")
            ])

        # 6. labs.csv
        lab_order_table = self.state_manager._store.get("laboratory.laboratory_orders", {})
        lab_rows = []
        for l_id, l_ord in lab_order_table.items():
            pid = l_ord.get("patient_id")
            if not pid and l_ord.get("patient_journey_id"):
                pid = journey_patient_map.get(l_ord.get("patient_journey_id"), "")
            enc_id = l_ord.get("encounter_id") or get_patient_enc_id(pid)
            status = l_ord.get("status", "Ordered")
            test_name = l_ord.get("test_name") or l_ord.get("test_type", "CBC")
            is_ab = bool(l_ord.get("is_abnormal", False))
            if status in ("Completed", "Reported"):
                comp_time = l_ord.get("completed_at")
                if not comp_time:
                    comp_time = l_ord.get("ordered_at") or l_ord.get("created_at") or ""
                result_str = l_ord.get("result") or ("Abnormal Finding" if is_ab else "Normal Range")
            else:
                comp_time = ""
                result_str = "Pending"
            lab_rows.append([
                l_id, pid, enc_id, test_name,
                result_str,
                is_ab, comp_time, status
            ])

        # 7. radiology.csv
        rad_order_table = self.state_manager._store.get("radiology.radiology_orders", {})
        rad_rows = []
        for r_id, r_ord in rad_order_table.items():
            pid = r_ord.get("patient_id")
            if not pid and r_ord.get("patient_journey_id"):
                pid = journey_patient_map.get(r_ord.get("patient_journey_id"), "")
            enc_id = r_ord.get("encounter_id") or get_patient_enc_id(pid)
            status = r_ord.get("status", "Ordered")
            modality = r_ord.get("modality", "Chest X-Ray")
            is_ab = bool(r_ord.get("is_abnormal", False))
            if status in ("Reported", "Completed"):
                comp_time = r_ord.get("completed_at")
                if not comp_time:
                    comp_time = r_ord.get("ordered_at") or r_ord.get("created_at") or ""
                findings = r_ord.get("findings") or ("Abnormal findings observed" if is_ab else "Normal study")
                impression = r_ord.get("impression") or ("Requires clinical correlation" if is_ab else "Clear")
            else:
                comp_time = ""
                findings = "Pending"
                impression = "Pending"
            rad_rows.append([
                r_id, pid, enc_id, modality,
                findings,
                impression,
                is_ab, comp_time, status
            ])

        # 8. invoices.csv & 9. payments.csv
        inv_table = self.state_manager._store.get("finance.invoices", {})
        inv_rows = []
        pay_rows = []
        for inv_id, inv in inv_table.items():
            status = inv.get("status", "Draft")
            # If invoice generation was genuinely blocked or not generated, do not emit an invoice row
            if status == "Draft" or not inv.get("created_at"):
                continue

            pid = inv.get("patient_id")
            if not pid and inv.get("patient_journey_id"):
                pid = journey_patient_map.get(inv.get("patient_journey_id"), "")
            enc_id = inv.get("encounter_id") or get_patient_enc_id(pid)
            total_amt = float(inv.get("total_amount", 0.0))
            created_at = inv.get("created_at")

            inv_rows.append([
                inv_id, pid, enc_id, total_amt, status, created_at
            ])
            if status == "Paid":
                pay_rows.append([
                    f"pay-{inv_id}", inv_id, pid, total_amt, "Insurance/Cash", inv.get("paid_at") or created_at, "Success"
                ])

        # 10. events.csv
        evt_rows = []
        for e in self.committed_events:
            pid = e.payload.get("patient_id") or ""
            if not pid and e.patient_journey_id:
                pid = journey_patient_map.get(e.patient_journey_id, "")
            enc_id = e.payload.get("encounter_id") or (get_patient_enc_id(pid) if pid else "")
            evt_rows.append([
                e.event_id, pid, enc_id, e.event_type, e.producer_domain, e.timestamp, e.status
            ])

        # 11. journey_traces.csv
        journey_trace_rows = []
        for j in self.journeys:
            st_iso = j.start_time.isoformat() if hasattr(j.start_time, "isoformat") else str(j.start_time)
            end_val = j.end_time or j.start_time
            et_iso = end_val.isoformat() if hasattr(end_val, "isoformat") else str(end_val)
            journey_trace_rows.append([
                j.journey_id,
                j.patient_id,
                j.scenario_id,
                j.status.value if hasattr(j.status, "value") else str(j.status),
                st_iso,
                et_iso,
                len(j.trace_history),
            ])

        # Perform strict integrity validation before writing files
        self._validate_simplified_records(
            patient_rows=patient_rows,
            enc_rows=enc_rows,
            cond_rows=cond_rows,
            sym_rows=sym_rows,
            med_rows=med_rows,
            lab_rows=lab_rows,
            rad_rows=rad_rows,
            inv_rows=inv_rows,
            pay_rows=pay_rows,
            evt_rows=evt_rows,
            journey_rows=journey_trace_rows,
        )

        # Write validated CSV files
        p = self._write_csv(
            s_dir / "patients.csv",
            ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
            patient_rows
        )
        if p: exported["patients.csv"] = p

        p = self._write_csv(
            s_dir / "encounters.csv",
            ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
            enc_rows
        )
        if p: exported["encounters.csv"] = p

        p = self._write_csv(
            s_dir / "conditions.csv",
            ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
            cond_rows
        )
        if p: exported["conditions.csv"] = p

        p = self._write_csv(
            s_dir / "symptoms.csv",
            ["symptom_id", "patient_id", "encounter_id", "condition_id", "symptom_name"],
            sym_rows
        )
        if p: exported["symptoms.csv"] = p

        p = self._write_csv(
            s_dir / "medications.csv",
            ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"],
            med_rows
        )
        if p: exported["medications.csv"] = p

        p = self._write_csv(
            s_dir / "labs.csv",
            ["lab_id", "patient_id", "encounter_id", "test_name", "result", "is_abnormal", "completed_at", "status"],
            lab_rows
        )
        if p: exported["labs.csv"] = p

        p = self._write_csv(
            s_dir / "radiology.csv",
            ["radiology_id", "patient_id", "encounter_id", "modality", "findings", "impression", "is_abnormal", "completed_at", "status"],
            rad_rows
        )
        if p: exported["radiology.csv"] = p

        p = self._write_csv(
            s_dir / "invoices.csv",
            ["invoice_id", "patient_id", "encounter_id", "total_amount", "status", "created_at"],
            inv_rows
        )
        if p: exported["invoices.csv"] = p

        p = self._write_csv(
            s_dir / "payments.csv",
            ["payment_id", "invoice_id", "patient_id", "amount", "payment_method", "timestamp", "status"],
            pay_rows
        )
        if p: exported["payments.csv"] = p

        p = self._write_csv(
            s_dir / "events.csv",
            ["event_id", "patient_id", "encounter_id", "event_type", "source_department", "timestamp", "status"],
            evt_rows
        )
        if p: exported["events.csv"] = p

        p = self._write_csv(
            s_dir / "journey_traces.csv",
            ["journey_id", "patient_id", "scenario_id", "status", "started_at", "completed_at", "step_count"],
            journey_trace_rows
        )
        if p: exported["journey_traces.csv"] = p

        # 12. generation_summary.csv
        summary_rows = [
            # Deterministic: simulation end time (wall-clock provenance lives in DATASET_MANIFEST.json)
            ["generation_timestamp", self.metrics.get("final_simulation_time", "")],
            ["patient_count", len(patient_rows)],
            ["encounter_count", len(enc_rows)],
            ["condition_count", len(cond_rows)],
            ["symptom_count", len(sym_rows)],
            ["medication_count", len(med_rows)],
            ["lab_count", len(lab_rows)],
            ["radiology_count", len(rad_rows)],
            ["invoice_count", len(inv_rows)],
            ["payment_count", len(pay_rows)],
            ["event_count", len(evt_rows)],
            ["journey_trace_count", len(journey_trace_rows)],
            ["pubmed_knowledge_enabled", "True"],
            ["random_seed", str(self.metrics.get("random_seed", 42))],
            ["validation_status", "PASSED"],
        ]
        p = self._write_csv(
            s_dir / "generation_summary.csv",
            ["metric_name", "metric_value"],
            summary_rows
        )
        if p: exported["generation_summary.csv"] = p

        # Additive Longitudinal Tables (Decision H)
        # 13. patient_timeline.csv
        timeline_rows = []
        for idx, e in enumerate(self.committed_events):
            t_pid = e.payload.get("patient_id") if e.payload else ""
            if not t_pid:
                t_pid = journey_patient_map.get(e.scenario_instance_id.split("-inst-")[0], "")
            t_iso = e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp)
            timeline_rows.append([
                f"tml-{idx+1}", t_pid, t_iso, e.event_type, e.entity_id, f"{e.event_type} on {e.entity_table}"
            ])
        p = self._write_csv(
            s_dir / "patient_timeline.csv",
            ["timeline_id", "patient_id", "timestamp", "event_type", "entity_id", "description"],
            timeline_rows
        )
        if p: exported["patient_timeline.csv"] = p

        # 14. observations.csv
        obs_rows = []
        if self.module_runner and hasattr(self.module_runner, "longitudinal_observations"):
            for obs in self.module_runner.longitudinal_observations:
                obs_t = obs["timestamp"].isoformat() if hasattr(obs["timestamp"], "isoformat") else str(obs["timestamp"])
                obs_rows.append([
                    obs["observation_id"], obs["patient_id"], obs["encounter_id"],
                    obs_t, obs["observation_code"], obs["observation_name"],
                    obs["value"], obs["unit"], obs["is_abnormal"]
                ])
        p = self._write_csv(
            s_dir / "observations.csv",
            ["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"],
            obs_rows
        )
        if p: exported["observations.csv"] = p

        # 15. care_plans.csv
        cp_rows = []
        if self.module_runner and hasattr(self.module_runner, "longitudinal_care_plans"):
            for cp in self.module_runner.longitudinal_care_plans:
                st = cp["start_date"].isoformat() if hasattr(cp["start_date"], "isoformat") else str(cp["start_date"])
                et = cp["end_date"].isoformat() if cp.get("end_date") and hasattr(cp["end_date"], "isoformat") else (str(cp["end_date"]) if cp.get("end_date") else "")
                cp_rows.append([
                    cp["care_plan_id"], cp["patient_id"], cp["encounter_id"],
                    cp["plan_code"], cp["plan_name"], st, et, cp["status"]
                ])
        p = self._write_csv(
            s_dir / "care_plans.csv",
            ["care_plan_id", "patient_id", "encounter_id", "plan_code", "plan_name", "start_date", "end_date", "status"],
            cp_rows
        )
        if p: exported["care_plans.csv"] = p

        # 16. deaths.csv
        death_rows = []
        if self.module_runner and hasattr(self.module_runner, "longitudinal_deaths"):
            for dth in self.module_runner.longitudinal_deaths:
                dt_iso = dth["death_date"].isoformat() if hasattr(dth["death_date"], "isoformat") else str(dth["death_date"])
                death_rows.append([
                    dth["death_id"], dth["patient_id"], dt_iso,
                    dth["cause_code"], dth["cause_name"], dth["is_premature"]
                ])
        p = self._write_csv(
            s_dir / "deaths.csv",
            ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"],
            death_rows
        )
        if p: exported["deaths.csv"] = p

        # 17. community_assessments.csv
        if self.community_assessments:
            comm_rows = []
            for ca in self.community_assessments:
                ts = ca.timestamp.isoformat() if hasattr(ca.timestamp, "isoformat") else str(ca.timestamp)
                comm_rows.append([
                    ca.assessment_id,
                    ca.patient_id,
                    ts,
                    ca.assessment_type,
                    ca.sbp if ca.sbp is not None else "",
                    ca.dbp if ca.dbp is not None else "",
                    ca.pulse_pressure if ca.pulse_pressure is not None else "",
                    ca.unit,
                    ca.survey_weight,
                    ca.status,
                    ca.provenance,
                ])
            p = self._write_csv(
                s_dir / "community_assessments.csv",
                ["assessment_id", "patient_id", "timestamp", "assessment_type", "sbp", "dbp", "pulse_pressure", "unit", "survey_weight", "status", "provenance"],
                comm_rows
            )
            if p: exported["community_assessments.csv"] = p

        # 18. community_bp_readings.csv
        if self.community_bp_readings:
            bp_rows = []
            for r in self.community_bp_readings:
                ts = r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp)
                bp_rows.append([
                    r.assessment_id,
                    r.patient_id,
                    r.reading_number,
                    ts,
                    r.sbp if r.sbp is not None else "",
                    r.dbp if r.dbp is not None else "",
                    r.pulse_pressure if r.pulse_pressure is not None else "",
                    r.unit,
                    r.status,
                    r.protocol_id,
                    r.protocol_version,
                    r.provenance,
                ])
            p = self._write_csv(
                s_dir / "community_bp_readings.csv",
                [
                    "assessment_id",
                    "patient_id",
                    "reading_number",
                    "timestamp",
                    "sbp",
                    "dbp",
                    "pulse_pressure",
                    "unit",
                    "status",
                    "protocol_id",
                    "protocol_version",
                    "provenance",
                ],
                bp_rows,
            )
            if p: exported["community_bp_readings.csv"] = p

        return exported

