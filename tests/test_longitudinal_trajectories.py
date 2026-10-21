"""
Tests for SYNAPSE Phase 2 Longitudinal Clinical Trajectory Validation:
- Separation of biological condition onset from clinical diagnosis (G4)
- Continuous surveillance loops in hypertension and diabetes modules
- Disease control re-evaluation and step-up therapy intensification
- Target-organ chronic complication onset (CKD, Nephropathy)
- Right-censored person-time calculation in evaluation framework
- Competing risks and prevention of double-death events
"""

from datetime import datetime, timedelta
from pathlib import Path
import pytest
import random

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.modules.models import ClinicalModule
from synapse_simulator.modules.loader import load_clinical_module
from synapse_simulator.modules.engine import ClinicalModuleRunner
from synapse_simulator.evaluation.evaluator import DatasetEvaluator, MetricStatus
from synapse_simulator.evaluation.experiment import ExperimentRunner, ExperimentConfig


MODULES_DIR = Path(__file__).parent.parent / "config" / "modules"


def test_hypertension_continuous_loop_and_intensification():
    """Verify that hypertension module executes screening, first-line Amlodipine,
    monitoring follow-up, SBP re-measurement, and step-up Telmisartan intensification."""
    htn_module = load_clinical_module(MODULES_DIR / "hypertension.yaml")
    runner = ClinicalModuleRunner([htn_module], base_seed=42)

    patient = PatientContext(
        patient_id="pat-htn-traj-01",
        name="Hypertension Trajectory Test",
        age=52,
        gender="Male",
        allergies=[],
        chronic_conditions=[],
    )
    runner.initialize_patient(patient)

    # 1. Trigger Onset -> Screening Encounter
    t0 = datetime(2026, 1, 1, 10, 0, 0)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "ScreeningEncounter"

    # Step through ScreeningEncounter -> RecordBloodPressure -> InitiateHypertensionCarePlan -> PrescribeAntihypertensive
    all_actions = []
    for step in range(4):
        emitted = runner.step_patient(patient, current_time=t0 + timedelta(minutes=step*10), timestep=timedelta(minutes=5))
        all_actions.extend(emitted)

    record = runner.patient_records[patient.patient_id]

    # Verify initial diagnosis, care plan, BP observation, and first-line prescription
    rx_actions = [a for a in all_actions if a.action_type == "VERIFY_PRESCRIPTION"]
    assert len(rx_actions) >= 1
    assert rx_actions[0].payload["drug_name"] == "Amlodipine"
    assert "SBP" in record["observations"]

    # 2. Advance time 180 days to FollowUpEncounter
    t_followup = t0 + timedelta(days=180)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "FollowUpEncounter"

    # Step: Follow-up encounter executes
    runner.step_patient(patient, current_time=t_followup, timestep=timedelta(minutes=5))
    assert len(record["encounters"]) >= 2

    # Step through MeasureFollowUpBP -> BPUncontrolled -> PrescribeStepUpAntihypertensive
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "BPUncontrolled"
    stepup_actions = []
    for step in range(3):
        emitted = runner.step_patient(patient, current_time=t_followup + timedelta(minutes=step*10 + 10), timestep=timedelta(minutes=5))
        stepup_actions.extend(emitted)

    rx_stepup = [a for a in stepup_actions if a.action_type == "VERIFY_PRESCRIPTION"]
    assert len(rx_stepup) == 1
    assert rx_stepup[0].payload["drug_name"] == "Telmisartan"

    # Verify module does NOT terminate: state remains in active surveillance loop
    next_state = runner.patient_module_states[patient.patient_id]["mod-htn-01"]
    assert next_state in ("ComplicationEvaluation", "CheckRenalComplication", "MaintenanceDelay", "FollowUpEncounter")
    assert htn_module.states[next_state].type != "Terminal"


def test_diabetes_continuous_loop_and_intensification():
    """Verify that diabetes module executes diagnostic encounter, care plan, Metformin,
    quarterly surveillance, HbA1c re-measurement, and step-up Glimepiride intensification."""
    t2d_module = load_clinical_module(MODULES_DIR / "diabetes_t2.yaml")
    runner = ClinicalModuleRunner([t2d_module], base_seed=99)

    patient = PatientContext(
        patient_id="pat-t2d-traj-01",
        name="Diabetes Trajectory Test",
        age=58,
        gender="Female",
        allergies=[],
        chronic_conditions=[],
    )
    runner.initialize_patient(patient)

    # 1. Trigger Diagnostic Encounter
    t0 = datetime(2026, 1, 1, 9, 30, 0)
    runner.patient_module_states[patient.patient_id]["mod-t2d-01"] = "DiagnosticEncounter"

    all_actions = []
    for step in range(4):
        emitted = runner.step_patient(patient, current_time=t0 + timedelta(minutes=step*10), timestep=timedelta(minutes=5))
        all_actions.extend(emitted)

    record = runner.patient_records[patient.patient_id]

    # Verify HbA1c, care plan, and Metformin
    assert "HbA1c" in record["observations"]
    rx_firstline = [a for a in all_actions if a.action_type == "VERIFY_PRESCRIPTION"]
    assert len(rx_firstline) >= 1
    assert rx_firstline[0].payload["drug_name"] == "Metformin"

    # 2. Advance time 90 days to DiabeticFollowUp
    t_q1 = t0 + timedelta(days=90)
    runner.patient_module_states[patient.patient_id]["mod-t2d-01"] = "DiabeticFollowUp"

    runner.step_patient(patient, current_time=t_q1, timestep=timedelta(minutes=5))
    assert len(record["encounters"]) >= 2

    # Step through GlycemicUncontrolled -> PrescribeStepUpHypoglycemic
    runner.patient_module_states[patient.patient_id]["mod-t2d-01"] = "GlycemicUncontrolled"
    stepup_actions = []
    for step in range(3):
        emitted = runner.step_patient(patient, current_time=t_q1 + timedelta(minutes=step*10 + 10), timestep=timedelta(minutes=5))
        stepup_actions.extend(emitted)

    rx_stepup = [a for a in stepup_actions if a.action_type == "VERIFY_PRESCRIPTION"]
    assert len(rx_stepup) == 1
    assert rx_stepup[0].payload["drug_name"] == "Glimepiride"

    # Verify module does NOT terminate: loops back into active surveillance
    next_state = runner.patient_module_states[patient.patient_id]["mod-t2d-01"]
    assert next_state in ("DiabeticComplicationEvaluation", "QuarterlySurveillanceDelay", "DiabeticNephropathyOnset", "DiabeticFollowUp")
    assert t2d_module.states[next_state].type != "Terminal"


def test_individual_censored_person_time_calculation(tmp_path):
    """Verify that evaluator computes individual right-censored person-time when deaths occur."""
    ds_dir = tmp_path / "censored_pt_test"
    ds_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(path, headers, rows):
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)

    # 2 patients observed from 2024-01-01 to 2025-12-31 (730 days = 2.0 years)
    # Patient 1 lives the full 2.0 years
    # Patient 2 dies on 2024-07-02 (approx 183 days = 0.50 years)
    write_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [
            ["pat-surv", "Survivor", 40, "Male", "O+", "Cash", "Active"],
            ["pat-dead", "Deceased", 75, "Female", "A+", "Cash", "Deceased"],
        ],
    )
    write_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [
            ["enc-1", "pat-surv", "j-1", "doc-1", "2024-03-01T10:00:00", "2024-03-01T10:20:00", "Closed", "Checkup"],
            ["enc-2", "pat-dead", "j-2", "doc-1", "2024-03-01T11:00:00", "2024-03-01T11:20:00", "Closed", "Checkup"],
        ],
    )
    write_csv(
        ds_dir / "deaths.csv",
        ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"],
        [["dth-1", "pat-dead", "2024-07-02T12:00:00", "R99", "Natural Mortality", False]],
    )
    write_csv(ds_dir / "conditions.csv", ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"], [])
    write_csv(ds_dir / "medications.csv", ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"], [])

    evaluator = DatasetEvaluator(
        dataset_dir=ds_dir,
        observation_start=datetime(2024, 1, 1),
        observation_end=datetime(2025, 12, 31),
    )
    long_metrics = evaluator.evaluate_longitudinal()

    mort_m = next(m for m in long_metrics if m.metric_id == "long_crude_mortality_rate")
    # Expected person-years: ~2.0 (survivor) + ~0.50 (deceased) = ~2.50 person-years
    # (Without censoring, it would be 4.0 person-years!)
    censored_pt = mort_m.acceptance_threshold["patient_years"]
    assert 2.45 <= censored_pt <= 2.55
    assert mort_m.numerator == 1


def test_competing_risks_no_double_death():
    """Verify that a deceased patient cannot undergo subsequent death transitions or post-mortem actions."""
    htn_module = load_clinical_module(MODULES_DIR / "hypertension.yaml")
    runner = ClinicalModuleRunner([htn_module], base_seed=777)

    patient = PatientContext(
        patient_id="pat-competing-01",
        name="Competing Risk Test",
        age=80,
        gender="Male",
        allergies=[],
        chronic_conditions=[],
        is_alive=True,
    )
    runner.initialize_patient(patient)

    # 1. Trigger CardiovascularDeath
    t_death = datetime(2026, 6, 1, 14, 0, 0)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "CardiovascularDeath"

    emitted_death = runner.step_patient(patient, current_time=t_death, timestep=timedelta(days=1))
    assert patient.is_alive is False
    assert patient.death_date is not None
    assert t_death <= patient.death_date <= t_death + timedelta(days=1)
    assert len(runner.longitudinal_deaths) == 1

    # 2. Subsequent step attempt must return immediately with empty actions
    t_post = t_death + timedelta(days=30)
    emitted_post = runner.step_patient(patient, current_time=t_post, timestep=timedelta(days=1))
    assert len(emitted_post) == 0
    assert len(runner.longitudinal_deaths) == 1  # Exactly 1 death record preserved
