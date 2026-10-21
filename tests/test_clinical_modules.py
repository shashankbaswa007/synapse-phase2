"""
Tests for Clinical Module Framework:
- Generic module loading & validation (7 control states, 11 clinical states, 4 transitions)
- Safe condition evaluation
- Latent condition onset preceding encounter diagnosis (G4)
- Terminal death behavior and action cancellation (G5)
- Clinical safety rule veto on contraindicated module proposals (G7)
- Seed-based deterministic reproducibility
"""

from datetime import datetime, timedelta
from pathlib import Path
import random
import pytest

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.modules.models import ClinicalModule, ControlType, ClinicalType
from synapse_simulator.modules.loader import load_clinical_module, load_all_clinical_modules
from synapse_simulator.modules.evaluator import ModuleConditionEvaluator
from synapse_simulator.modules.engine import ClinicalModuleRunner
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.state.models import InputContext, DecisionStatus


MODULES_DIR = Path(__file__).parent.parent / "config" / "modules"


def test_load_all_clinical_modules():
    modules = load_all_clinical_modules(MODULES_DIR)
    module_ids = {m.id for m in modules}
    assert "mod-htn-01" in module_ids
    assert "mod-t2d-01" in module_ids
    assert "mod-urti-01" in module_ids

    htn = next(m for m in modules if m.id == "mod-htn-01")
    assert "AgeCheck" in htn.states
    assert htn.states["AgeCheck"].type == ControlType.GUARD.value
    assert "HypertensionOnset" in htn.states
    assert htn.states["HypertensionOnset"].type == ClinicalType.CONDITION_ONSET.value
    assert "CardiovascularDeath" in htn.states
    assert htn.states["CardiovascularDeath"].type == ClinicalType.DEATH.value


def test_condition_evaluator():
    patient = PatientContext(
        patient_id="pat-eval-01",
        name="Test Patient",
        age=55,
        gender="Male",
        allergies=["Penicillin"],
        chronic_conditions=["I10"],
        attributes={"glycemic_status": "impaired"},
    )
    evaluator = ModuleConditionEvaluator(patient)

    assert evaluator.evaluate("age >= 50") is True
    assert evaluator.evaluate("age < 30") is False
    assert evaluator.evaluate("gender == 'Male'") is True
    assert evaluator.evaluate("has_condition('I10')") is True
    assert evaluator.evaluate("has_condition('E11.9')") is False
    assert evaluator.evaluate("attribute('glycemic_status') == 'impaired'") is True


def test_latent_condition_onset_precedes_encounter_diagnosis():
    """G4 verification: condition onset creates latent condition; diagnosed only at encounter."""
    htn_module = load_clinical_module(MODULES_DIR / "hypertension.yaml")
    runner = ClinicalModuleRunner([htn_module], base_seed=123)

    patient = PatientContext(
        patient_id="pat-latent-01",
        name="Latent Test",
        age=45,
        gender="Female",
        allergies=[],
        chronic_conditions=[],
    )
    runner.initialize_patient(patient)

    # 1. Step to AgeCheck -> HypertensionOnset
    start_time = datetime(2026, 1, 1, 9, 0, 0)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "HypertensionOnset"

    # Step: HypertensionOnset executes
    emitted = runner.step_patient(patient, current_time=start_time, timestep=timedelta(days=1))

    # At this point, latent condition exists in patient context
    assert "I10" in patient.latent_conditions
    latent_info = patient.latent_conditions["I10"]
    assert latent_info["recognized"] is False
    # No diagnosis action emitted yet!
    diag_actions = [a for a in emitted if a.action_type == "CONSULTATION_DIAGNOSE"]
    assert len(diag_actions) == 0

    # 2. Advance time to ScreeningEncounter
    encounter_time = start_time + timedelta(days=95)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "ScreeningEncounter"
    emitted_enc = runner.step_patient(patient, current_time=encounter_time, timestep=timedelta(days=1))

    # Encounter is scheduled and diagnosis action is emitted
    enc_actions = [a for a in emitted_enc if a.action_type in ["REGISTER_PATIENT", "SCHEDULE_APPOINTMENT"]]
    diag_actions = [a for a in emitted_enc if a.action_type == "CONSULTATION_DIAGNOSE"]
    assert len(enc_actions) >= 1
    assert len(diag_actions) == 1

    diag_payload = diag_actions[0].payload
    assert diag_payload["condition_code"] == "I10"
    assert latent_info["recognized"] is True
    # Invariant: onset_time <= diagnosis_time
    assert latent_info["onset_time"] <= latent_info["diagnosis_time"]


def test_death_state_halts_modules_and_marks_deceased():
    """G5 verification: Death halts subsequent actions and marks patient inactive/deceased."""
    htn_module = load_clinical_module(MODULES_DIR / "hypertension.yaml")
    runner = ClinicalModuleRunner([htn_module], base_seed=999)

    patient = PatientContext(
        patient_id="pat-terminal-01",
        name="Terminal Test",
        age=80,
        gender="Male",
        allergies=[],
        chronic_conditions=["I10"],
    )
    runner.initialize_patient(patient)

    # Force patient into CardiovascularDeath state
    death_time = datetime(2026, 6, 1, 12, 0, 0)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "CardiovascularDeath"

    emitted = runner.step_patient(patient, current_time=death_time, timestep=timedelta(days=1))

    assert patient.is_alive is False
    assert patient.death_date is not None
    assert len(runner.longitudinal_deaths) == 1
    assert runner.longitudinal_deaths[0]["cause_code"] == "I21.9"

    # Subsequent steps produce zero actions because patient is deceased
    subsequent_emitted = runner.step_patient(patient, current_time=death_time + timedelta(days=7), timestep=timedelta(days=7))
    assert len(subsequent_emitted) == 0


def test_allergy_safety_veto_on_module_amoxicillin():
    """G7 verification: RuleEngine blocks module-proposed Amoxicillin when patient is allergic to Penicillin."""
    urti_module = load_clinical_module(MODULES_DIR / "urti.yaml")
    runner = ClinicalModuleRunner([urti_module], base_seed=42)

    patient = PatientContext(
        patient_id="pat-allergy-01",
        name="Allergic Patient",
        age=30,
        gender="Male",
        allergies=["Penicillin"],
        chronic_conditions=[],
    )
    runner.initialize_patient(patient)

    # Step into PrescribeAntibiotic
    step_time = datetime(2026, 2, 1, 10, 0, 0)
    runner.patient_module_states[patient.patient_id]["mod-urti-01"] = "PrescribeAntibiotic"

    emitted = runner.step_patient(patient, current_time=step_time, timestep=timedelta(days=1))
    rx_actions = [a for a in emitted if a.action_type == "VERIFY_PRESCRIPTION"]
    assert len(rx_actions) == 1
    rx_action = rx_actions[0]
    assert rx_action.payload["drug_name"] == "Amoxicillin"
    assert rx_action.extra_context["drug_class"] == "Beta-Lactam"

    # Evaluate action against RuleEngine
    repo = RuleRepository()
    repo.load_rules()
    engine = RuleEngine(repo)

    ctx = InputContext(
        simulated_timestamp=step_time,
        scenario_id="MODULE-pat-allergy-01",
        scenario_instance_id="MODULE-pat-allergy-01-inst-1",
        patient_journey_id="jny-pat-allergy-01",
        correlation_id="cor-01",
        department_id="pharmacy",
        proposed_action=rx_action,
        patient_state={"allergies": patient.allergies},
        entity_state={"status": "Issued"},
        extra_context=rx_action.extra_context,
    )

    decision = engine.evaluate(ctx)
    assert decision.status == DecisionStatus.BLOCKED
    assert decision.winning_rule_id == "RULE-CLIN-ALLERGY-001"


def test_clinical_module_runner_determinism():
    """Criterion 1 & 2: Same seed reproduces exact events, different seed varies."""
    htn_module = load_clinical_module(MODULES_DIR / "hypertension.yaml")

    from synapse_simulator.core.ids import reset as reset_ids

    def run_sim(seed: int):
        reset_ids(seed)
        runner = ClinicalModuleRunner([htn_module], base_seed=seed)
        p = PatientContext(patient_id="pat-det-01", name="Det", age=50, gender="Male")
        runner.initialize_patient(p)
        actions = []
        t = datetime(2026, 1, 1, 0, 0, 0)
        for _ in range(30):
            actions.extend(runner.step_patient(p, t, timedelta(days=7)))
            t += timedelta(days=7)
        return [(a.action_type, a.payload) for a in actions]

    res1 = run_sim(seed=11)
    res2 = run_sim(seed=11)
    res3 = run_sim(seed=42)

    assert res1 == res2
    assert res1 != res3
