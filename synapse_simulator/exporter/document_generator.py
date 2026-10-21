"""
Document Generator for Synapse Phase 2.
Assembles and renders hospital documents (Prescriptions, Invoices, LabReports, RadReports, DischargeSummaries)
directly from validated structured StateManager database snapshots and DomainEvent history.
"""

import os
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.state.document_models import DocumentMetadata, DocumentType, DocumentStatus

class DocumentGenerator:
    """Assembles and exports structured JSON metadata and human-readable Markdown documents."""

    def __init__(self, state_manager: StateManager, committed_events: List[DomainEvent], output_dir: Path):
        self.state_manager = state_manager
        self.committed_events = committed_events
        self.output_dir = output_dir

        # Setup subdirectories for document organization
        self.dirs = {
            DocumentType.PRESCRIPTION: self.output_dir / "documents" / "prescriptions",
            DocumentType.INVOICE: self.output_dir / "documents" / "bills",
            DocumentType.LAB_REPORT: self.output_dir / "documents" / "lab_reports",
            DocumentType.RAD_REPORT: self.output_dir / "documents" / "rad_reports",
            DocumentType.DISCHARGE_SUMMARY: self.output_dir / "documents" / "discharge_summaries",
        }

        # Create directories if they do not exist
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        # In-memory generated documents tracking: document_id -> DocumentMetadata
        self.generated_docs: Dict[str, DocumentMetadata] = {}

        from collections import defaultdict
        self._events_by_journey = defaultdict(list)
        for e in self.committed_events:
            if e.patient_journey_id:
                self._events_by_journey[e.patient_journey_id].append(e)

    def generate_all(self) -> Dict[str, DocumentMetadata]:
        """Iterate over state manager and generate all appropriate documents."""
        # 1. Generate Prescriptions (including safety hold notices)
        self._generate_prescriptions()

        # 2. Generate Lab Reports
        self._generate_lab_reports()

        # 3. Generate Radiology Reports
        self._generate_rad_reports()

        # 4. Generate Invoices
        self._generate_invoices()

        # 5. Generate Discharge Summaries
        self._generate_discharge_summaries()

        return self.generated_docs

    def _write_document(
        self,
        doc_type: DocumentType,
        doc_id: str,
        patient_id: str,
        journey_id: str,
        scenario_id: str,
        source_table: str,
        source_id: str,
        source_action_id: str,
        source_event_id: str,
        content: str,
        payload: Dict[str, Any],
        created_at: Optional[datetime] = None,
    ) -> DocumentMetadata:
        """Helper to write checksummed files and return Pydantic metadata."""
        if not created_at:
            created_at = datetime.now()

        # Compute checksum
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Define file path
        target_dir = self.dirs[doc_type]
        md_file = target_dir / f"{doc_id}.md"
        json_file = target_dir / f"{doc_id}.json"

        # Write markdown content
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Construct metadata
        metadata = DocumentMetadata(
            document_id=doc_id,
            document_type=doc_type,
            patient_id=patient_id,
            patient_journey_id=journey_id,
            scenario_id=scenario_id,
            source_entity_table=source_table,
            source_entity_id=source_id,
            source_action_id=source_action_id,
            source_event_id=source_event_id,
            created_at=created_at,
            document_version="1.0.0",
            document_status=DocumentStatus.FINAL,
            file_path=str(md_file.resolve()),
            checksum=checksum,
            metadata_payload=payload,
        )

        # Write metadata JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(), f, indent=2, default=str)

        self.generated_docs[doc_id] = metadata
        return metadata

    def _generate_prescriptions(self) -> None:
        """Assembles prescription documents and safety hold alerts from pharmacy tables."""
        prescriptions_table = self.state_manager._store.get("pharmacy.prescriptions", {})
        for rx_id, rx in prescriptions_table.items():
            patient_id = rx.get("patient_id", "")
            patient = self.state_manager.get_entity_state("patient.patients", patient_id)
            patient_name = patient.get("name", "Unknown Patient")
            patient_allergies = patient.get("allergies", [])

            # Find matching events to extract metadata & causality
            evt_verify = self._find_first_event("PrescriptionVerified", entity_id=rx_id)
            evt_hold = self._find_first_event("PrescriptionAllergyConflictDetected", entity_id=rx_id)
            evt_dispense = self._find_first_event("MedicineDispensed", entity_id=rx_id)

            status = rx.get("status", "Issued")
            scenario_id = self._get_scenario_id(rx_id)

            # Resolve causality references
            if evt_dispense:
                action_id = evt_dispense.causation_id or "act-dispense"
                event_id = evt_dispense.event_id
                timestamp = evt_dispense.timestamp
            elif evt_verify:
                action_id = evt_verify.causation_id or "act-verify"
                event_id = evt_verify.event_id
                timestamp = evt_verify.timestamp
            elif evt_hold:
                action_id = evt_hold.causation_id or "act-verify"
                event_id = evt_hold.event_id
                timestamp = evt_hold.timestamp
            else:
                action_id = "act-consult"
                event_id = "evt-consult"
                timestamp = datetime.now()

            journey_id = rx.get("journey_id") or (evt_verify.patient_journey_id if evt_verify else "")
            if not journey_id and evt_hold:
                journey_id = evt_hold.patient_journey_id
            if not journey_id and evt_dispense:
                journey_id = evt_dispense.patient_journey_id

            doc_id = f"doc-rx-{rx_id[3:] if rx_id.startswith('rx-') else rx_id}"

            # Document layout
            content_lines = []
            content_lines.append("=================================================================")
            content_lines.append("                    SYNAPSE MEDICAL CENTER                       ")
            content_lines.append("                       PRESCRIPTION SLIP                         ")
            content_lines.append("=================================================================")
            content_lines.append(f" Prescription ID : {rx_id}")
            content_lines.append(f" Date & Time     : {timestamp.isoformat()}")
            content_lines.append(f" Patient ID      : {patient_id}")
            content_lines.append(f" Patient Name    : {patient_name}")
            content_lines.append(f" Document Status : {status}")
            content_lines.append(f" Allergies       : {', '.join(patient_allergies) if patient_allergies else 'None'}")
            content_lines.append("-----------------------------------------------------------------")

            if status == "Blocked_Safety_Hold":
                # Render Clinical Safety Hold slip
                content_lines.append("                      ⚠️ CLINICAL SAFETY HOLD                     ")
                content_lines.append("-----------------------------------------------------------------")
                content_lines.append(" DISPENSING BLOCKED DUE TO CLINICAL DRUG-ALLERGY CONFLICT        ")
                content_lines.append(f" Prescribed Medication : {rx.get('drug_name', 'Unknown')}")
                content_lines.append(f" Drug Class            : {rx.get('drug_class', 'Unknown')}")
                content_lines.append(" Conflict Category     : Penicillin Allergy Cross-Reactivity")
                content_lines.append(" Supporting Rule       : RULE-CLIN-ALLERGY-001")
                content_lines.append(" Details                : Prescription blocked to prevent potential ")
                content_lines.append("                          cross-reactive anaphylactic response.     ")
                content_lines.append("-----------------------------------------------------------------")
                content_lines.append(" Action Required       : Substitute medication with non-beta-lactam alternative.")
            else:
                # Render Standard Prescription slip
                content_lines.append(" Rx:")
                content_lines.append(f"  Medication : {rx.get('drug_name', 'Paracetamol')}")
                content_lines.append(f"  Class      : {rx.get('drug_class', 'Analgesic')}")
                content_lines.append(f"  Dosage     : {rx.get('dosage', '500mg')}")
                content_lines.append(f"  Frequency  : {rx.get('frequency', 'TDS')}")
                content_lines.append(f"  Duration   : {rx.get('duration_days', 5)} days")
                content_lines.append("-----------------------------------------------------------------")
                content_lines.append(" Status of Dispense    : MEDICINE FULLY DISPENSED" if status == "Dispensed" else "PENDING DISPENSE")

            content_lines.append("=================================================================")

            self._write_document(
                doc_type=DocumentType.PRESCRIPTION,
                doc_id=doc_id,
                patient_id=patient_id,
                journey_id=journey_id,
                scenario_id=scenario_id,
                source_table="pharmacy.prescriptions",
                source_id=rx_id,
                source_action_id=action_id,
                source_event_id=event_id,
                content="\n".join(content_lines),
                payload=rx,
                created_at=timestamp,
            )

    def _generate_lab_reports(self) -> None:
        """Generates structured laboratory reports for completed orders."""
        lab_table = self.state_manager._store.get("laboratory.laboratory_orders", {})
        for lab_id, order in lab_table.items():
            status = order.get("status", "Ordered")
            if status != "Completed" and status != "Sample-Collected":
                # Only generate document if test progressed beyond order
                continue

            evt_result = self._find_first_event("LabOrderResulted", entity_id=lab_id)
            evt_collect = self._find_first_event("LabSampleCollected", entity_id=lab_id)

            if evt_result:
                action_id = evt_result.causation_id or "act-result"
                event_id = evt_result.event_id
                timestamp = evt_result.timestamp
                payload = evt_result.payload
            elif evt_collect:
                action_id = evt_collect.causation_id or "act-collect"
                event_id = evt_collect.event_id
                timestamp = evt_collect.timestamp
                payload = evt_collect.payload
            else:
                continue

            patient_id = payload.get("patient_id", "")
            patient = self.state_manager.get_entity_state("patient.patients", patient_id)
            patient_name = patient.get("name", "Unknown Patient")
            journey_id = payload.get("journey_id", "")
            scenario_id = self._get_scenario_id(lab_id)

            doc_id = f"doc-lab-{lab_id[4:] if lab_id.startswith('lab-') else lab_id}"

            # Assemble lab result items
            results = payload.get("results", {})
            if not results:
                # Mock a complete blood count (CBC) if empty
                results = {
                    "WBC": {"value": 8.5, "unit": "x10^3/uL", "range": "4.5 - 11.0", "flag": "Normal"},
                    "Hemoglobin": {"value": 14.2, "unit": "g/dL", "range": "12.0 - 17.5", "flag": "Normal"},
                    "Platelets": {"value": 250, "unit": "x10^3/uL", "range": "150 - 400", "flag": "Normal"},
                }

            content_lines = []
            content_lines.append("=================================================================")
            content_lines.append("                    SYNAPSE MEDICAL CENTER                       ")
            content_lines.append("                   PATHOLOGY LABORATORY REPORT                   ")
            content_lines.append("=================================================================")
            content_lines.append(f" Report ID       : {doc_id}")
            content_lines.append(f" Order ID        : {lab_id}")
            content_lines.append(f" Date Reported   : {timestamp.isoformat()}")
            content_lines.append(f" Patient ID      : {patient_id}")
            content_lines.append(f" Patient Name    : {patient_name}")
            content_lines.append(f" Specimen Type   : Blood (EDTA)")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" Component            Value       Units       Ref Range     Flag ")
            content_lines.append("-----------------------------------------------------------------")

            for comp, data in results.items():
                val = str(data.get("value", ""))
                unit = str(data.get("unit", ""))
                r_range = str(data.get("range", ""))
                flag = str(data.get("flag", "Normal"))
                content_lines.append(f" {comp:<20} {val:<11} {unit:<11} {r_range:<13} {flag} ")

            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" Laboratory Sign-Off: Dr. Sarah Vance, MD Pathology")
            content_lines.append("=================================================================")

            self._write_document(
                doc_type=DocumentType.LAB_REPORT,
                doc_id=doc_id,
                patient_id=patient_id,
                journey_id=journey_id,
                scenario_id=scenario_id,
                source_table="laboratory.laboratory_orders",
                source_id=lab_id,
                source_action_id=action_id,
                source_event_id=event_id,
                content="\n".join(content_lines),
                payload=payload,
                created_at=timestamp,
            )

    def _generate_rad_reports(self) -> None:
        """Generates structured radiology imaging reports."""
        rad_table = self.state_manager._store.get("radiology.radiology_orders", {})
        for rad_id, order in rad_table.items():
            status = order.get("status", "Ordered")
            if status != "Reported" and status != "Image-Acquired":
                continue

            evt_report = self._find_first_event("RadiologyReported", entity_id=rad_id)
            evt_acquire = self._find_first_event("RadiologyImageAcquired", entity_id=rad_id)

            if evt_report:
                action_id = evt_report.causation_id or "act-report"
                event_id = evt_report.event_id
                timestamp = evt_report.timestamp
                payload = evt_report.payload
            elif evt_acquire:
                action_id = evt_acquire.causation_id or "act-acquire"
                event_id = evt_acquire.event_id
                timestamp = evt_acquire.timestamp
                payload = evt_acquire.payload
            else:
                continue

            patient_id = payload.get("patient_id", "")
            patient = self.state_manager.get_entity_state("patient.patients", patient_id)
            patient_name = patient.get("name", "Unknown Patient")
            journey_id = payload.get("journey_id", "")
            scenario_id = self._get_scenario_id(rad_id)

            doc_id = f"doc-rad-{rad_id[4:] if rad_id.startswith('rad-') else rad_id}"

            findings = payload.get("findings", "Chest X-ray shows normal lung fields, normal cardiothoracic ratio, and clear pleural spaces. No active disease.")
            impression = payload.get("impression", "Normal chest radiograph.")

            content_lines = []
            content_lines.append("=================================================================")
            content_lines.append("                    SYNAPSE MEDICAL CENTER                       ")
            content_lines.append("                       RADIOLOGY REPORT                          ")
            content_lines.append("=================================================================")
            content_lines.append(f" Report ID       : {doc_id}")
            content_lines.append(f" Order ID        : {rad_id}")
            content_lines.append(f" Date Reported   : {timestamp.isoformat()}")
            content_lines.append(f" Patient ID      : {patient_id}")
            content_lines.append(f" Patient Name    : {patient_name}")
            content_lines.append(f" Procedure Type  : Chest Radiograph (X-Ray PA View)")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" FINDINGS:")
            content_lines.append(f"  {findings}")
            content_lines.append("")
            content_lines.append(" IMPRESSION:")
            content_lines.append(f"  {impression}")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" Radiologist Sign-Off: Dr. Marcus Sterling, MD Radiology")
            content_lines.append("=================================================================")

            self._write_document(
                doc_type=DocumentType.RAD_REPORT,
                doc_id=doc_id,
                patient_id=patient_id,
                journey_id=journey_id,
                scenario_id=scenario_id,
                source_table="radiology.radiology_orders",
                source_id=rad_id,
                source_action_id=action_id,
                source_event_id=event_id,
                content="\n".join(content_lines),
                payload=payload,
                created_at=timestamp,
            )

    def _generate_invoices(self) -> None:
        """Assembles itemized billing invoices based on generated charges."""
        invoices_table = self.state_manager._store.get("finance.invoices", {})

        # Wait, if invoices table is empty, we must scan the state and events to build the invoices!
        # This acts as our robust document assembler so no data is missing.
        # Let's map patient_journey_id -> invoice records.
        journeys_by_id = {}
        for event in self.committed_events:
            j_id = event.patient_journey_id
            if j_id and j_id not in journeys_by_id:
                journeys_by_id[j_id] = {
                    "patient_id": event.payload.get("patient_id"),
                    "journey_id": j_id,
                    "scenario_instance_id": event.scenario_instance_id,
                    "correlation_id": event.correlation_id,
                    "charges": [],
                }

            if j_id:
                # Catch explicit billing triggers
                if event.event_type == "ADD_INVOICE_LINE_ITEM" or event.event_type == "MedicineDispensed":
                    service = event.payload.get("service_name") or "Pharmacy Medication Charge"
                    amount = event.payload.get("amount") or 5.00
                    journeys_by_id[j_id]["charges"].append({
                        "item": service,
                        "amount": amount,
                        "event_id": event.event_id,
                    })
                # Catch diagnostic triggers
                elif event.event_type == "LabOrderResulted" or event.event_type == "LabSampleCollected":
                    journeys_by_id[j_id]["charges"].append({
                        "item": "Laboratory Pathology Test Fee",
                        "amount": 350.00,
                        "event_id": event.event_id,
                    })
                elif event.event_type == "RadiologyReported" or event.event_type == "RadiologyImageAcquired":
                    journeys_by_id[j_id]["charges"].append({
                        "item": "Radiology Imaging Chest X-Ray",
                        "amount": 800.00,
                        "event_id": event.event_id,
                    })

        for j_id, data in journeys_by_id.items():
            patient_id = data["patient_id"]
            patient = self.state_manager.get_entity_state("patient.patients", patient_id)
            patient_name = patient.get("name", "Unknown Patient")
            scenario_id = self._get_scenario_id(data["scenario_instance_id"])

            # Every journey has a consultation charge of 500
            line_items = [{"item": "Outpatient Consultation Fee", "amount": 500.00, "source": "Consultation"}]
            for charge in data["charges"]:
                line_items.append({
                    "item": charge["item"],
                    "amount": charge["amount"],
                    "source": charge["event_id"],
                })

            subtotal = sum(item["amount"] for item in line_items)
            total = subtotal # Standard fee, no tax for V1 demo

            # Generate invoice ID
            rx_short = j_id[3:11] if j_id.startswith("pj-") else j_id[:8]
            invoice_id = f"inv-{rx_short}"
            doc_id = f"doc-bill-{rx_short}"

            # Set status based on journey outcome
            # Check if any pharmacy blocks occurred. If blocked, some medications weren't dispensed!
            evt_hold = self._find_first_event("PrescriptionAllergyConflictDetected", journey_id=j_id)
            evt_shortage = self._find_first_event("InventoryShortageDetected", journey_id=j_id)
            
            status = "Paid"
            if evt_hold or evt_shortage:
                status = "Cancelled"  # Incomplete journey bills cancelled or replaced

            timestamp = datetime.now()
            evt_last = self._find_last_event_for_journey(j_id)
            if evt_last:
                timestamp = evt_last.timestamp

            content_lines = []
            content_lines.append("=================================================================")
            content_lines.append("                    SYNAPSE MEDICAL CENTER                       ")
            content_lines.append("                       PATIENT INVOICE                           ")
            content_lines.append("=================================================================")
            content_lines.append(f" Invoice ID      : {invoice_id}")
            content_lines.append(f" Date Generated  : {timestamp.isoformat()}")
            content_lines.append(f" Patient ID      : {patient_id}")
            content_lines.append(f" Patient Name    : {patient_name}")
            content_lines.append(f" Invoice Status  : {status}")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" Description                                               Amount")
            content_lines.append("-----------------------------------------------------------------")

            for item in line_items:
                desc = item["item"]
                amt = f"{item['amount']:.2f}"
                content_lines.append(f" {desc:<50} {amt:>13}")

            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(f" Subtotal:                                            {subtotal:>13.2f}")
            content_lines.append(f" Total Due:                                           {total:>13.2f}")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(f" Payment Method  : Cash / Insurance")
            content_lines.append(f" Receipt Status  : RECEIVED & CLOSED" if status == "Paid" else "BILLING RECORD VOIDED / CANCELLED")
            content_lines.append("=================================================================")

            self._write_document(
                doc_type=DocumentType.INVOICE,
                doc_id=doc_id,
                patient_id=patient_id,
                journey_id=j_id,
                scenario_id=scenario_id,
                source_table="finance.invoices",
                source_id=invoice_id,
                source_action_id="act-billing",
                source_event_id=evt_last.event_id if evt_last else "evt-billing",
                content="\n".join(content_lines),
                payload={"invoice_id": invoice_id, "line_items": line_items, "total": total, "status": status},
                created_at=timestamp,
            )

            # Update StateManager so the database state matches the generated invoice record
            enc_id = f"enc-{j_id[3:]}" if j_id.startswith("pj-") else f"enc-{j_id}"
            self.state_manager.set_entity_state(
                "finance.invoices",
                invoice_id,
                {
                    "invoice_id": invoice_id,
                    "patient_id": patient_id,
                    "encounter_id": enc_id,
                    "journey_id": j_id,
                    "total_amount": total,
                    "status": status,
                    "created_at": timestamp.isoformat(),
                },
            )

    def _generate_discharge_summaries(self) -> None:
        """Assembles discharge summary documents at the end of patient journeys."""
        # Map journey_id -> list of events in temporal order
        events_by_journey = {}
        for event in self.committed_events:
            j_id = event.patient_journey_id
            if j_id:
                if j_id not in events_by_journey:
                    events_by_journey[j_id] = []
                events_by_journey[j_id].append(event)

        for j_id, evts in events_by_journey.items():
            evts.sort(key=lambda e: e.sequence_number)
            first_evt = evts[0]
            last_evt = evts[-1]

            patient_id = first_evt.payload.get("patient_id")
            patient = self.state_manager.get_entity_state("patient.patients", patient_id)
            patient_name = patient.get("name", "Unknown Patient")
            scenario_id = self._get_scenario_id(first_evt.scenario_instance_id)

            # Discover clinical course
            diagnosis_code = "Unknown"
            diagnosis_name = "Undiagnosed Diagnosis"

            # Resolve diagnosis from consultation state
            consults = self.state_manager._store.get("clinical.consultations", {})
            for c_id, consult in consults.items():
                if consult.get("patient_id") == patient_id:
                    diagnosis_code = consult.get("diagnosis_code", diagnosis_code)
                    diagnosis_name = consult.get("diagnosis_name", diagnosis_name)

            doc_id = f"doc-ds-{j_id[3:] if j_id.startswith('pj-') else j_id}"

            # Assemble diagnostic results and safety logs
            safety_logs = []
            meds_dispensed = []
            labs_performed = []

            for evt in evts:
                if evt.event_type == "PrescriptionAllergyConflictDetected":
                    safety_logs.append("Drug-Allergy conflict blocked beta-lactam prescription verification.")
                elif evt.event_type == "InventoryShortageDetected":
                    safety_logs.append("Medication dispense blocked due to pharmacy inventory stock depletion.")
                elif evt.event_type == "MedicineDispensed":
                    meds_dispensed.append("Dispensed medication.")
                elif evt.event_type == "LabOrderResulted":
                    labs_performed.append("Pathology Blood count completed.")
                elif evt.event_type == "RadiologyReported":
                    labs_performed.append("Radiology chest scan completed.")

            outcome = "Discharged in stable condition"
            if safety_logs:
                outcome = "Discharged with safety hold clinical alert created"

            content_lines = []
            content_lines.append("=================================================================")
            content_lines.append("                    SYNAPSE MEDICAL CENTER                       ")
            content_lines.append("                      DISCHARGE SUMMARY                          ")
            content_lines.append("=================================================================")
            content_lines.append(f" Summary ID      : {doc_id}")
            content_lines.append(f" Date & Time     : {last_evt.timestamp.isoformat()}")
            content_lines.append(f" Patient ID      : {patient_id}")
            content_lines.append(f" Patient Name    : {patient_name}")
            content_lines.append(f" Scenario ID     : {scenario_id}")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" CLINICAL SUMMARY:")
            content_lines.append(f"  Primary Diagnosis : {diagnosis_name} ({diagnosis_code})")
            content_lines.append(f"  Admitted/Arrival  : {first_evt.timestamp.isoformat()}")
            content_lines.append(f"  Discharged        : {last_evt.timestamp.isoformat()}")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" INVESTIGATIONS & INTERVENTIONS:")

            if labs_performed:
                content_lines.append("  Diagnostics:")
                for lab in labs_performed:
                    content_lines.append(f"   - {lab}")
            else:
                content_lines.append("  Diagnostics: None performed.")

            if meds_dispensed:
                content_lines.append("  Medications:")
                for med in meds_dispensed:
                    content_lines.append(f"   - {med}")
            else:
                content_lines.append("  Medications: None dispensed.")

            if safety_logs:
                content_lines.append("  Clinical Safety Incidents:")
                for log in safety_logs:
                    content_lines.append(f"   - ⚠️ {log}")

            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(f" Discharge Status : {outcome}")
            content_lines.append(" Instructions     : Patient advised to take medications as directed. ")
            content_lines.append("                    Return immediately to emergency room if fever recurs.")
            content_lines.append("-----------------------------------------------------------------")
            content_lines.append(" Chief Physician Sign-Off: Dr. Richard Brody, Chief Medical Officer")
            content_lines.append("=================================================================")

            self._write_document(
                doc_type=DocumentType.DISCHARGE_SUMMARY,
                doc_id=doc_id,
                patient_id=patient_id,
                journey_id=j_id,
                scenario_id=scenario_id,
                source_table="clinical.encounters",
                source_id=f"enc-{j_id[3:] if j_id.startswith('pj-') else j_id}",
                source_action_id="act-discharge",
                source_event_id=last_evt.event_id,
                content="\n".join(content_lines),
                payload={"discharge_summary_id": doc_id, "safety_logs": safety_logs, "outcome": outcome},
                created_at=last_evt.timestamp,
            )

    # --- Helper methods ---

    def _find_first_event(self, event_type: str, entity_id: Optional[str] = None, journey_id: Optional[str] = None) -> Optional[DomainEvent]:
        for e in self.committed_events:
            if e.event_type == event_type:
                if entity_id and e.entity_id != entity_id:
                    continue
                if journey_id and e.patient_journey_id != journey_id:
                    continue
                return e
        return None

    def _find_last_event_for_journey(self, journey_id: str) -> Optional[DomainEvent]:
        journey_evts = self._events_by_journey.get(journey_id, [])
        if journey_evts:
            return journey_evts[-1]
        return None

    def _get_scenario_id(self, instance_id: str) -> str:
        if "-inst-" in instance_id:
            return instance_id.split("-inst-")[0]
        return "SCEN-V1-01"
