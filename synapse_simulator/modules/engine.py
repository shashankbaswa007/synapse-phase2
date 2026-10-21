"""
Clinical Module Execution Engine.
Drives longitudinal patient clinical module progression, evaluates states and transitions,
handles intra-timestep event offsets, and emits ActionRequests into the simulation.
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Any, Callable
import hashlib

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.modules.models import (
    ClinicalModule,
    ModuleState,
    ControlType,
    ClinicalType,
    DistributedTarget,
)
from synapse_simulator.modules.evaluator import ModuleConditionEvaluator
from synapse_simulator.state.models import ActionRequest, PatientStatus
from synapse_simulator.core.ids import new_id


def derive_patient_seed(base_seed: int, patient_id: str) -> int:
    """Deterministically derive a 32-bit seed for a specific patient."""
    h = hashlib.sha256(f"{base_seed}:{patient_id}".encode("utf-8")).digest()
    return int.from_bytes(h[:4], byteorder="big")


class ClinicalModuleRunner:
    """Manages longitudinal execution of clinical modules across simulated patients."""

    def __init__(self, modules: List[ClinicalModule], base_seed: int = 42):
        self.modules: Dict[str, ClinicalModule] = {m.id: m for m in modules}
        self.base_seed = base_seed

        # State tracking: patient_id -> {module_id -> state_name}
        self.patient_module_states: Dict[str, Dict[str, str]] = {}
        # Delay tracking: patient_id -> {module_id -> resume_datetime}
        self.patient_delays: Dict[str, Dict[str, datetime]] = {}
        # Patient record history: patient_id -> dict of medical observations, symptoms, diagnosed conditions
        self.patient_records: Dict[str, Dict[str, Any]] = {}
        # Dedicated patient RNGs
        self.patient_rngs: Dict[str, random.Random] = {}
        # Emitted actions buffer
        self.emitted_actions: List[ActionRequest] = []
        # Recorded observations, care plans, and deaths for longitudinal export
        self.longitudinal_observations: List[Dict[str, Any]] = []
        self.longitudinal_care_plans: List[Dict[str, Any]] = []
        self.longitudinal_deaths: List[Dict[str, Any]] = []

    def get_patient_rng(self, patient_id: str) -> random.Random:
        if patient_id not in self.patient_rngs:
            p_seed = derive_patient_seed(self.base_seed, patient_id)
            self.patient_rngs[patient_id] = random.Random(p_seed)
        return self.patient_rngs[patient_id]

    def initialize_patient(self, patient: PatientContext) -> None:
        """Register patient and set all active modules to their initial states,
        disentangling baseline chronic prevalence from subsequent incident disease."""
        pid = patient.patient_id
        self.patient_module_states[pid] = {}
        self.patient_delays[pid] = {}
        self.patient_records[pid] = {
            "diagnosed_conditions": list(patient.chronic_conditions),
            "symptoms": [],
            "observations": {},
            "encounters": [],
            "medications": [],
            "care_plans": [],
        }

        # Check baseline conditions
        has_htn = (
            "I10" in patient.baseline_conditions
            or any("Hypertension" in c or c == "I10" for c in patient.chronic_conditions)
        )
        has_t2d = (
            "E11.9" in patient.baseline_conditions
            or any("Diabetes" in c or c == "E11.9" for c in patient.chronic_conditions)
        )

        for mid, module in self.modules.items():
            if mid == "mod-htn-01" and has_htn:
                # Baseline-positive hypertension: route to initial screening/maintenance encounter
                # Ensures clinical history & treatment are initiated without duplicate incident onset!
                b_info = patient.baseline_conditions.get("I10", {})
                onset_dt = b_info.get("onset_date") or (datetime(2026, 1, 1) - timedelta(days=365 * 2))
                patient.latent_conditions["I10"] = {
                    "code": "I10",
                    "name": "Essential (primary) hypertension",
                    "onset_time": onset_dt,
                    "recognized": False,
                    "is_baseline": True,
                }
                self.patient_module_states[pid][mid] = "ScreeningEncounter"
            elif mid == "mod-t2d-01" and has_t2d:
                # Baseline-positive diabetes: route to initial diagnostic/surveillance encounter
                # Ensures HbA1c, care plan, and Metformin without duplicate incident onset!
                b_info = patient.baseline_conditions.get("E11.9", {})
                onset_dt = b_info.get("onset_date") or (datetime(2026, 1, 1) - timedelta(days=365 * 2))
                patient.latent_conditions["E11.9"] = {
                    "code": "E11.9",
                    "name": "Type 2 diabetes mellitus without complications",
                    "onset_time": onset_dt,
                    "recognized": False,
                    "is_baseline": True,
                }
                self.patient_module_states[pid][mid] = "DiagnosticEncounter"
            else:
                self.patient_module_states[pid][mid] = module.initial_state

    def step_patient(
        self,
        patient: PatientContext,
        current_time: datetime,
        timestep: timedelta = timedelta(days=7),
        scheduler: Optional[Any] = None,
    ) -> List[ActionRequest]:
        """Step all clinical modules for a patient across one timestep."""
        if not patient.is_alive:
            return []

        pid = patient.patient_id
        if pid not in self.patient_module_states:
            self.initialize_patient(patient)

        rng = self.get_patient_rng(pid)
        record = self.patient_records[pid]
        newly_emitted: List[ActionRequest] = []

        for mid, module in self.modules.items():
            if not patient.is_alive:
                break

            current_state_name = self.patient_module_states[pid].get(mid, module.initial_state)
            if current_state_name not in module.states:
                continue

            state = module.states[current_state_name]
            if state.type == ControlType.TERMINAL.value:
                continue

            # Check delays
            if pid in self.patient_delays and mid in self.patient_delays[pid]:
                resume_at = self.patient_delays[pid][mid]
                if current_time < resume_at:
                    continue  # Still waiting in delay
                else:
                    del self.patient_delays[pid][mid]

            # Execute state progression (loop up to 5 times for pass-through states)
            depth = 0
            while depth < 5 and patient.is_alive:
                depth += 1
                state = module.states[current_state_name]

                # 1. Guard check
                if state.type == ControlType.GUARD.value and state.guard_condition:
                    evaluator = ModuleConditionEvaluator(patient, record)
                    if not evaluator.evaluate(state.guard_condition):
                        # Guard not satisfied, hold in current state
                        break

                # 2. Intra-timestep event timestamp jitter
                jitter_seconds = int(rng.uniform(0, max(1, int(timestep.total_seconds()))))
                event_time = current_time + timedelta(seconds=jitter_seconds)

                # 3. Execute state actions
                self._execute_state_action(
                    patient=patient,
                    state=state,
                    record=record,
                    event_time=event_time,
                    rng=rng,
                    out_actions=newly_emitted,
                    scheduler=scheduler,
                )

                if not patient.is_alive:
                    break

                # 4. Handle Delay state
                if state.type == ControlType.DELAY.value and state.delay_days:
                    self.patient_delays[pid][mid] = current_time + timedelta(days=state.delay_days)

                # 5. Determine transition
                next_state_name = self._determine_next_state(state, patient, record, rng)
                if not next_state_name or next_state_name == current_state_name:
                    break

                current_state_name = next_state_name
                self.patient_module_states[pid][mid] = current_state_name

                # If next state is not a pass-through simple/set_attr state, stop for this timestep
                next_state = module.states[next_state_name]
                if next_state.type not in [ControlType.SIMPLE.value, ControlType.SET_ATTRIBUTE.value, ControlType.COUNTER.value]:
                    break

        return newly_emitted

    def _execute_state_action(
        self,
        patient: PatientContext,
        state: ModuleState,
        record: Dict[str, Any],
        event_time: datetime,
        rng: random.Random,
        out_actions: List[ActionRequest],
        scheduler: Optional[Any] = None,
    ) -> None:
        """Executes operational side-effects of reaching a state."""
        pid = patient.patient_id

        # --- Control States ---
        if state.type == ControlType.SET_ATTRIBUTE.value:
            if state.attribute_name:
                patient.attributes[state.attribute_name] = state.attribute_value

        elif state.type == ControlType.COUNTER.value:
            if state.counter_attribute:
                current_val = patient.attributes.get(state.counter_attribute, 0)
                if state.counter_action == "decrement":
                    patient.attributes[state.counter_attribute] = current_val - 1
                else:
                    patient.attributes[state.counter_attribute] = current_val + 1

        # --- Clinical States ---
        elif state.type == ClinicalType.CONDITION_ONSET.value:
            # Latent condition onset (G4): stored internally, NOT diagnosed yet!
            code = state.condition_code or "UNKNOWN"
            # Hard Invariant: Baseline-positive or already recognized condition cannot undergo duplicate onset!
            if code in patient.latent_conditions and patient.latent_conditions[code].get("recognized"):
                return
            if code in record["diagnosed_conditions"]:
                return
            patient.latent_conditions[code] = {
                "code": code,
                "name": state.condition_name or code,
                "onset_time": event_time,
                "recognized": False,
                "is_baseline": False,
            }

        elif state.type == ClinicalType.CONDITION_END.value:
            code = state.condition_code or "UNKNOWN"
            if code in patient.latent_conditions:
                patient.latent_conditions[code]["resolved"] = True
                patient.latent_conditions[code]["resolved_time"] = event_time
            if code in record["diagnosed_conditions"]:
                record["diagnosed_conditions"].remove(code)

            # Emit resolution event for downstream state stores and CSV exporters
            resolve_req = ActionRequest(
                action_id=new_id("act-", 8),
                action_type="CONSULTATION_RESOLVE",
                target_department="clinical",
                target_entity_table="clinical.consultations",
                target_entity_id=new_id("con-", 8),
                scenario_instance_id=f"MODULE-{pid}",
                patient_journey_id=f"jny-{pid}",
                correlation_id=new_id("cor-", 8),
                requested_timestamp=event_time,
                payload={
                    "patient_id": pid,
                    "encounter_id": record.get("current_encounter_id", ""),
                    "condition_code": code,
                    "condition_name": code,
                    "status": "Resolved",
                    "resolved_time": event_time.isoformat(),
                },
            )
            out_actions.append(resolve_req)

        elif state.type == ClinicalType.OBSERVATION.value:
            code = state.observation_code or "OBS"
            val = state.observation_value
            if val is None and state.observation_min is not None and state.observation_max is not None:
                val = round(rng.uniform(state.observation_min, state.observation_max), 1)
            elif val is None:
                val = 0.0

            is_abnormal_primary = (code == "SBP" and val >= 140.0)
            record["observations"][code] = val
            obs_id = new_id("obs-", 8)
            enc_id = record.get("current_encounter_id", "")
            self.longitudinal_observations.append({
                "observation_id": obs_id,
                "patient_id": pid,
                "encounter_id": enc_id,
                "timestamp": event_time,
                "observation_code": code,
                "observation_name": state.observation_name or code,
                "value": val,
                "unit": state.observation_unit or "",
                "is_abnormal": is_abnormal_primary,
            })

            # Check if paired/component observation is defined (e.g. DBP paired with SBP)
            if state.paired_observation_code:
                p_code = state.paired_observation_code
                p_val = state.paired_observation_value
                if p_val is None and state.paired_observation_min is not None and state.paired_observation_max is not None:
                    p_val = round(rng.uniform(state.paired_observation_min, state.paired_observation_max), 1)
                elif p_val is None:
                    p_val = 0.0

                # Physiological plausibility guard: For BP pairs, ensure SBP > DBP and pulse pressure >= 20 mmHg
                if code == "SBP" and p_code == "DBP":
                    if p_val >= val:
                        p_val = round(val - 35.0, 1)
                    elif (val - p_val) < 20.0:
                        p_val = round(val - 25.0, 1)

                is_abnormal_paired = (p_code == "DBP" and p_val >= 90.0)
                record["observations"][p_code] = p_val
                p_obs_id = new_id("obs-", 8)
                self.longitudinal_observations.append({
                    "observation_id": p_obs_id,
                    "patient_id": pid,
                    "encounter_id": enc_id,
                    "timestamp": event_time,
                    "observation_code": p_code,
                    "observation_name": state.paired_observation_name or p_code,
                    "value": p_val,
                    "unit": state.paired_observation_unit or state.observation_unit or "",
                    "is_abnormal": is_abnormal_paired,
                })

        elif state.type == ClinicalType.SYMPTOM.value:
            s_name = state.symptom_name or "General"
            if s_name not in record["symptoms"]:
                record["symptoms"].append(s_name)

        elif state.type == ClinicalType.ENCOUNTER.value:
            enc_id = new_id("enc-", 8)
            record["current_encounter_id"] = enc_id
            record["encounters"].append(enc_id)

            req = ActionRequest(
                action_id=new_id("act-", 8),
                action_type="REGISTER_PATIENT" if len(record["encounters"]) == 1 else "SCHEDULE_APPOINTMENT",
                target_department="clinical",
                target_entity_table="clinical.encounters",
                target_entity_id=enc_id,
                scenario_instance_id=f"MODULE-{pid}",
                patient_journey_id=f"jny-{pid}",
                correlation_id=new_id("cor-", 8),
                requested_timestamp=event_time,
                payload={
                    "patient_id": pid,
                    "encounter_id": enc_id,
                    "encounter_type": state.encounter_type,
                    "reason": state.encounter_reason or "Routine / Follow-up",
                    "timestamp": event_time.isoformat(),
                },
            )
            out_actions.append(req)

            # Clinical Recognition (G4): Check if any latent condition is diagnosed during this encounter!
            for l_code, l_info in list(patient.latent_conditions.items()):
                if not l_info.get("recognized"):
                    l_info["recognized"] = True
                    l_info["diagnosis_time"] = event_time
                    l_info["encounter_id"] = enc_id
                    record["diagnosed_conditions"].append(l_code)

                    diag_req = ActionRequest(
                        action_id=new_id("act-", 8),
                        action_type="CONSULTATION_DIAGNOSE",
                        target_department="clinical",
                        target_entity_table="clinical.consultations",
                        target_entity_id=new_id("con-", 8),
                        scenario_instance_id=f"MODULE-{pid}",
                        patient_journey_id=f"jny-{pid}",
                        correlation_id=new_id("cor-", 8),
                        requested_timestamp=event_time,
                        payload={
                            "patient_id": pid,
                            "encounter_id": enc_id,
                            "condition_code": l_code,
                            "condition_name": l_info.get("name", l_code),
                            "timestamp": event_time.isoformat(),
                            "status": "Active",
                            "is_baseline": l_info.get("is_baseline", False),
                        },
                    )
                    out_actions.append(diag_req)

        elif state.type == ClinicalType.MEDICATION_ORDER.value:
            rx_id = new_id("rx-", 8)
            req = ActionRequest(
                action_id=new_id("act-", 8),
                action_type="VERIFY_PRESCRIPTION",
                target_department="pharmacy",
                target_entity_table="pharmacy.prescriptions",
                target_entity_id=rx_id,
                scenario_instance_id=f"MODULE-{pid}",
                patient_journey_id=f"jny-{pid}",
                correlation_id=new_id("cor-", 8),
                requested_timestamp=event_time,
                payload={
                    "patient_id": pid,
                    "prescription_id": rx_id,
                    "encounter_id": record.get("current_encounter_id", ""),
                    "drug_code": state.drug_code,
                    "drug_name": state.drug_name,
                    "dosage": state.dosage or "Standard",
                    "frequency": state.frequency or "Once Daily",
                    "timestamp": event_time.isoformat(),
                },
                extra_context={
                    "drug_class": state.drug_class or "Standard",
                },
            )
            out_actions.append(req)

        elif state.type == ClinicalType.CARE_PLAN_START.value:
            cp_id = new_id("cp-", 8)
            self.longitudinal_care_plans.append({
                "care_plan_id": cp_id,
                "patient_id": pid,
                "encounter_id": record.get("current_encounter_id", ""),
                "plan_code": state.plan_code or "CP-01",
                "plan_name": state.plan_name or "Care Plan",
                "start_date": event_time,
                "end_date": None,
                "status": "Active",
            })

        elif state.type == ClinicalType.CARE_PLAN_END.value:
            for cp in self.longitudinal_care_plans:
                if cp["patient_id"] == pid and cp.get("plan_code") == state.plan_code and cp["status"] == "Active":
                    cp["status"] = "Completed"
                    cp["end_date"] = event_time

        elif state.type == ClinicalType.DEATH.value:
            # Terminal Death state (G5)
            patient.is_alive = False
            patient.death_date = event_time
            death_id = new_id("dth-", 8)
            self.longitudinal_deaths.append({
                "death_id": death_id,
                "patient_id": pid,
                "death_date": event_time,
                "cause_code": state.death_cause_code or "R99",
                "cause_name": state.death_cause_name or "Ill-defined and unknown cause of mortality",
                "is_premature": patient.age < 70,
            })

            # Invalidate all pending future actions in scheduler for this deceased patient
            if scheduler:
                scheduler.invalidate_entity_actions("patient.patients", pid)
                scheduler.invalidate_entity_actions("clinical.encounters", pid)

            death_req = ActionRequest(
                action_id=new_id("act-", 8),
                action_type="RECORD_DEATH",
                target_department="clinical",
                target_entity_table="patient.patients",
                target_entity_id=pid,
                scenario_instance_id=f"MODULE-{pid}",
                patient_journey_id=f"jny-{pid}",
                correlation_id=new_id("cor-", 8),
                requested_timestamp=event_time,
                payload={
                    "patient_id": pid,
                    "death_date": event_time.isoformat(),
                    "cause": state.death_cause_name or "Natural",
                },
            )
            out_actions.append(death_req)

    def _determine_next_state(
        self,
        state: ModuleState,
        patient: PatientContext,
        record: Dict[str, Any],
        rng: random.Random,
    ) -> Optional[str]:
        """Determine transition according to the 4 Synthea transition types."""
        # Invariant guards: Pre-existing condition cannot transition to duplicate onset
        if state.name == "AgeCheck":
            has_htn = (
                "I10" in patient.latent_conditions
                or "I10" in patient.baseline_conditions
                or "I10" in record.get("diagnosed_conditions", [])
            )
            if has_htn:
                return "NormotensiveDelay"

        if state.name == "T2DAgeCheck":
            has_t2d = (
                "E11.9" in patient.latent_conditions
                or "E11.9" in patient.baseline_conditions
                or "E11.9" in record.get("diagnosed_conditions", [])
            )
            if has_t2d:
                return "EuglycemicDelay"

        # 1. Direct Transition
        if state.direct_transition:
            return state.direct_transition

        # 2. Distributed Transition
        if state.distributed_transition:
            weights = [dt.weight for dt in state.distributed_transition]
            targets = [dt.to for dt in state.distributed_transition]
            return rng.choices(targets, weights=weights, k=1)[0]

        # 3. Conditional Transition
        if state.conditional_transition:
            evaluator = ModuleConditionEvaluator(patient, record)
            for ct in state.conditional_transition:
                if evaluator.evaluate(ct.condition):
                    return ct.to
            if state.default_transition:
                return state.default_transition

        # 4. Complex Transition
        if state.complex_transition:
            evaluator = ModuleConditionEvaluator(patient, record)
            for cx in state.complex_transition:
                if evaluator.evaluate(cx.condition):
                    weights = [dt.weight for dt in cx.distributions]
                    targets = [dt.to for dt in cx.distributions]
                    return rng.choices(targets, weights=weights, k=1)[0]
            if state.default_transition:
                return state.default_transition

        return None
