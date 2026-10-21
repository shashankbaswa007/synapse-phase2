"""
Integrity Auditor for Synapse Phase 2.
Performs deep structural validation of patient contexts, temporal sequencing, state machines, and rules.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import DomainEvent
from synapse_simulator.transitions.state_machine import ENTITY_STATE_MACHINES


class IntegrityAuditor:
    """Performs global database integrity, temporal sequencing, and rule constraint verification."""

    def __init__(self, state_manager: StateManager, committed_events: List[DomainEvent]):
        self.state_manager = state_manager
        self.committed_events = committed_events

    def audit_all(self) -> Dict[str, Any]:
        """Perform all audits and compile report."""
        report = {
            "identity_referential": self.audit_referential_integrity(),
            "patient_and_encounter_consistency": self.audit_patient_and_encounter_consistency(),
            "temporal_sequencing": self.audit_temporal_sequencing(),
            "temporal_encounter_boundaries": self.audit_temporal_encounter_boundaries(),
            "causal_event_ordering": self.audit_causal_ordering(),
            "encounter_duration": self.audit_encounter_duration(),
            "provenance_integrity": self.audit_provenance_integrity(),
            "state_transitions": self.audit_state_transitions(),
            "resource_constraints": self.audit_resource_constraints(),
            "rule_compliance": self.audit_rule_compliance(),
        }

        # Calculate final summary flags
        is_success = all(sec.get("success", False) for sec in report.values())
        report["success"] = is_success
        report["is_valid"] = is_success
        all_errors = []
        for sec in report.values():
            if isinstance(sec, dict) and "errors" in sec:
                all_errors.extend(sec["errors"])
        report["errors"] = all_errors
        return report

    def audit_referential_integrity(self) -> Dict[str, Any]:
        """Verify foreign key relationships across all entity tables."""
        errors = []
        patient_keys = set(self.state_manager._store.get("patient.patients", {}).keys())
        encounter_keys = set(self.state_manager._store.get("clinical.encounters", {}).keys())

        # 1. Verify appointments point to existing patients
        appointments = self.state_manager._store.get("clinical.appointments", {})
        for app_id, app in appointments.items():
            p_id = app.get("patient_id")
            if p_id and p_id not in patient_keys:
                errors.append(f"Appointment '{app_id}' references non-existent Patient '{p_id}'.")

        # 2. Verify prescriptions point to existing patients and encounters
        prescriptions = self.state_manager._store.get("pharmacy.prescriptions", {})
        for rx_id, rx in prescriptions.items():
            p_id = rx.get("patient_id")
            if p_id and p_id not in patient_keys:
                errors.append(f"Prescription '{rx_id}' references non-existent Patient '{p_id}'.")
            enc_id = rx.get("encounter_id") or rx.get("consultation_id")
            if enc_id and encounter_keys and enc_id not in encounter_keys:
                errors.append(f"Prescription '{rx_id}' references non-existent Encounter '{enc_id}'.")

        # 3. Verify invoices point to existing patients
        invoices = self.state_manager._store.get("finance.invoices", {})
        for inv_id, inv in invoices.items():
            p_id = inv.get("patient_id")
            if p_id and p_id not in patient_keys:
                errors.append(f"Invoice '{inv_id}' references non-existent Patient '{p_id}'.")

        # 4. Verify encounters point to existing patients
        encounters = self.state_manager._store.get("clinical.encounters", {})
        for enc_id, enc in encounters.items():
            p_id = enc.get("patient_id")
            if p_id and p_id not in patient_keys:
                errors.append(f"Encounter '{enc_id}' references non-existent Patient '{p_id}'.")

        # 5. Verify lab orders point to existing patients and encounters
        labs = self.state_manager._store.get("laboratory.laboratory_orders", {})
        for lab_id, lab in labs.items():
            p_id = lab.get("patient_id")
            if p_id and p_id not in patient_keys:
                errors.append(f"Lab order '{lab_id}' references non-existent Patient '{p_id}'.")
            enc_id = lab.get("encounter_id")
            if enc_id and encounter_keys and enc_id not in encounter_keys:
                errors.append(f"Lab order '{lab_id}' references non-existent Encounter '{enc_id}'.")

        # 6. Verify radiology orders point to existing patients and encounters
        rads = self.state_manager._store.get("radiology.radiology_orders", {})
        for rad_id, rad in rads.items():
            p_id = rad.get("patient_id")
            if p_id and p_id not in patient_keys:
                errors.append(f"Radiology order '{rad_id}' references non-existent Patient '{p_id}'.")
            enc_id = rad.get("encounter_id")
            if enc_id and encounter_keys and enc_id not in encounter_keys:
                errors.append(f"Radiology order '{rad_id}' references non-existent Encounter '{enc_id}'.")

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_patient_and_encounter_consistency(self) -> Dict[str, Any]:
        """Verify cross-record consistency between patient_id and encounter_id."""
        errors = []
        enc_table = self.state_manager._store.get("clinical.encounters", {})
        enc_patient_map = {e_id: e.get("patient_id") for e_id, e in enc_table.items()}

        # Verify labs have valid patient_id, encounter_id, and encounter.patient_id == lab.patient_id
        labs = self.state_manager._store.get("laboratory.laboratory_orders", {})
        for lab_id, lab in labs.items():
            p_id = lab.get("patient_id")
            enc_id = lab.get("encounter_id")
            if not p_id:
                errors.append(f"Lab '{lab_id}' has NULL/missing patient_id.")
            if enc_table and not enc_id:
                errors.append(f"Lab '{lab_id}' has NULL/missing encounter_id.")
            if enc_id and enc_id in enc_patient_map:
                expected_pid = enc_patient_map[enc_id]
                if p_id and expected_pid and p_id != expected_pid:
                    errors.append(f"Lab '{lab_id}' patient mismatch: lab.patient='{p_id}', encounter.patient='{expected_pid}'.")

        # Verify prescriptions match encounter patient
        prescriptions = self.state_manager._store.get("pharmacy.prescriptions", {})
        for rx_id, rx in prescriptions.items():
            p_id = rx.get("patient_id")
            enc_id = rx.get("encounter_id") or rx.get("consultation_id")
            if enc_id and enc_id in enc_patient_map:
                expected_pid = enc_patient_map[enc_id]
                if p_id and expected_pid and p_id != expected_pid:
                    errors.append(f"Prescription '{rx_id}' patient mismatch: rx.patient='{p_id}', encounter.patient='{expected_pid}'.")

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_encounter_duration(self) -> Dict[str, Any]:
        """Verify that encounters have valid non-negative and non-zero duration."""
        errors = []
        encounters = self.state_manager._store.get("clinical.encounters", {})

        for enc_id, enc in encounters.items():
            st_val = enc.get("start_time")
            et_val = enc.get("end_time")
            status = enc.get("status")

            if st_val and et_val:
                try:
                    st = datetime.fromisoformat(st_val) if isinstance(st_val, str) else st_val
                    et = datetime.fromisoformat(et_val) if isinstance(et_val, str) else et_val
                    if et < st:
                        errors.append(f"Negative encounter duration in '{enc_id}': start={st}, end={et}.")
                    if status == "Closed" and et == st:
                        errors.append(f"Zero duration for closed encounter '{enc_id}': start={st}, end={et}.")
                except Exception as e:
                    errors.append(f"Invalid timestamp format in encounter '{enc_id}': {e}")

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_provenance_integrity(self) -> Dict[str, Any]:
        """Verify treatment knowledge provenance (PubMed vs internal_yaml)."""
        errors = []
        prescriptions = self.state_manager._store.get("pharmacy.prescriptions", {})

        for rx_id, rx in prescriptions.items():
            source = rx.get("source", "internal_yaml")
            ev_ids = rx.get("evidence_ids", [])
            has_ev = bool(ev_ids) and ev_ids != "None" and ev_ids != []

            if source == "pubmed_evidence" and not has_ev:
                errors.append(f"Treatment '{rx_id}' with source='pubmed_evidence' has missing evidence_ids.")
            elif source == "internal_yaml+pubmed_evidence" and not has_ev:
                errors.append(f"Treatment '{rx_id}' with source='internal_yaml+pubmed_evidence' has missing evidence_ids.")

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_temporal_encounter_boundaries(self) -> Dict[str, Any]:
        """Verify in-encounter events occur within encounter boundaries."""
        errors = []
        encounters = self.state_manager._store.get("clinical.encounters", {})
        enc_map = {}
        for enc_id, enc in encounters.items():
            st_val = enc.get("start_time")
            et_val = enc.get("end_time")
            if st_val and et_val:
                st = datetime.fromisoformat(st_val) if isinstance(st_val, str) else st_val
                et = datetime.fromisoformat(et_val) if isinstance(et_val, str) else et_val
                enc_map[enc_id] = (st, et)
                j_id = enc.get("journey_id")
                if j_id:
                    enc_map[j_id] = (st, et)

        post_encounter_types = {
            "PatientDischarged", "PatientJourneyCompleted", "EncounterCompleted",
            "BillingPaymentProcessed", "PaymentProcessed", "FollowUpScheduled",
        }

        for e in self.committed_events:
            enc_info = None
            enc_id = e.payload.get("encounter_id")
            if enc_id and enc_id in enc_map:
                enc_info = enc_map[enc_id]
            elif e.patient_journey_id and e.patient_journey_id in enc_map:
                enc_info = enc_map[e.patient_journey_id]

            if enc_info:
                st, et = enc_info
                if e.timestamp < st:
                    errors.append(
                        f"Event '{e.event_type}' ({e.event_id}) occurred before encounter start: {e.timestamp} < {st}"
                    )
                if e.event_type not in post_encounter_types and e.timestamp > et:
                    errors.append(
                        f"In-encounter event '{e.event_type}' ({e.event_id}) occurred after encounter end: {e.timestamp} > {et}"
                    )

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_causal_ordering(self) -> Dict[str, Any]:
        """Ensure causally dependent events occur in valid order."""
        errors = []
        journeys_events: Dict[str, List[DomainEvent]] = {}
        for e in self.committed_events:
            j_id = e.patient_journey_id
            if j_id:
                if j_id not in journeys_events:
                    journeys_events[j_id] = []
                journeys_events[j_id].append(e)

        for j_id, evts in journeys_events.items():
            type_times: Dict[str, List[datetime]] = {}
            for e in evts:
                type_times.setdefault(e.event_type, []).append(e.timestamp)

            # 1. LabOrdered before LabSampleCollected / LabCompleted
            ordered_times = type_times.get("LabOrderCreated", [])
            collected_times = type_times.get("LabSampleCollected", [])
            if ordered_times and collected_times:
                if min(collected_times) < min(ordered_times):
                    errors.append(f"Causal violation in journey '{j_id}': LabSampleCollected occurs before LabOrderCreated.")

            # 2. PrescriptionVerified before MedicineDispensed
            verified_times = type_times.get("PrescriptionVerified", [])
            dispensed_times = type_times.get("MedicineDispensed", [])
            if verified_times and dispensed_times:
                if min(dispensed_times) < min(verified_times):
                    errors.append(f"Causal violation in journey '{j_id}': MedicineDispensed occurs before PrescriptionVerified.")

            # 3. EncounterStarted before PatientDischarged / PatientJourneyCompleted
            enc_start_times = type_times.get("EncounterStarted", [])
            discharged_times = type_times.get("PatientDischarged", []) + type_times.get("PatientJourneyCompleted", [])
            if enc_start_times and discharged_times:
                if min(discharged_times) < min(enc_start_times):
                    errors.append(f"Causal violation in journey '{j_id}': Discharge occurs before EncounterStarted.")

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_temporal_sequencing(self) -> Dict[str, Any]:
        """Verify that event timestamps conform to causal ordering (e.g. consult before dispense)."""
        errors = []
        journeys_events: Dict[str, List[DomainEvent]] = {}

        for e in self.committed_events:
            j_id = e.patient_journey_id
            if j_id:
                if j_id not in journeys_events:
                    journeys_events[j_id] = []
                journeys_events[j_id].append(e)

        for j_id, evts in journeys_events.items():
            # Sort by sequence number to establish causal order
            evts.sort(key=lambda e: e.sequence_number)
            
            # Verify timestamps are monotonically increasing or equal
            last_time = None
            for e in evts:
                if last_time and e.timestamp < last_time:
                    errors.append(
                        f"Temporal violation in journey '{j_id}': Event '{e.event_type}' ({e.event_id}) "
                        f"timestamp {e.timestamp} occurs before prior event timestamp {last_time}."
                    )
                last_time = e.timestamp

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_state_transitions(self) -> Dict[str, Any]:
        """Verify that entity state histories correspond to valid state machine paths."""
        errors = []
        # Since StateManager only stores the *current* state, we reconstruct state transition path from events
        entity_states: Dict[str, str] = {}  # key: "table:id", value: state

        for e in self.committed_events:
            if e.status != "COMMITTED":
                continue

            key = f"{e.entity_table}:{e.entity_id}"
            new_state = e.payload.get("status") or e.payload.get("new_value")

            if not new_state:
                continue

            sm_class = ENTITY_STATE_MACHINES.get(e.entity_table)
            if not sm_class:
                continue

            current_state = entity_states.get(key)
            if current_state is None:
                # First transition: must be initial state or allowed transition from initial
                if new_state != sm_class.initial_state and not sm_class.is_valid_transition(sm_class.initial_state, new_state):
                    errors.append(
                        f"Invalid initial state transition for '{key}': Started with state '{new_state}', "
                        f"expected initial state '{sm_class.initial_state}'."
                    )
            else:
                # Subsequent transition check
                if current_state != new_state and not sm_class.is_valid_transition(current_state, new_state):
                    errors.append(
                        f"Invalid state transition for '{key}': Transition from '{current_state}' to '{new_state}' is disallowed."
                    )

            entity_states[key] = new_state

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_resource_constraints(self) -> Dict[str, Any]:
        """Ensure no inventory batch quantities became negative."""
        errors = []
        batches = self.state_manager._store.get("pharmacy.inventory_batches", {})

        for b_id, batch in batches.items():
            qty = batch.get("quantity_available", 0)
            if qty < 0:
                errors.append(f"Resource violation: Inventory batch '{b_id}' has negative stock ({qty}).")

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }

    def audit_rule_compliance(self) -> Dict[str, Any]:
        """Verify that rules were executed correctly (e.g. blocked actions did not result in success states)."""
        errors = []

        # Verify that for any allergy block event, the prescription status remained "Blocked_Safety_Hold"
        for event in self.committed_events:
            if event.event_type == "PrescriptionAllergyConflictDetected":
                rx_id = event.entity_id
                rx = self.state_manager.get_entity_state("pharmacy.prescriptions", rx_id)
                status = rx.get("status")
                if status != "Blocked_Safety_Hold":
                    errors.append(
                        f"Rule violation for allergy hold: Prescription '{rx_id}' had conflict event but state is '{status}'."
                    )

            # Verify that stock shortages resulted in correct alert state
            elif event.event_type == "InventoryShortageDetected":
                rx_id = event.entity_id
                # Enforce that it was never dispensed
                rx = self.state_manager.get_entity_state("pharmacy.prescriptions", rx_id)
                status = rx.get("status")
                if status == "Dispensed" or status == "Completed":
                    errors.append(
                        f"Rule violation for stock shortage: Prescription '{rx_id}' was dispense-blocked but is marked '{status}'."
                    )

        return {
            "success": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }
