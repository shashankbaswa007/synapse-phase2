"""
Deterministic unit and integration tests for SYNAPSE Phase 2C.
Forward Clinical Diagnosis Inference and Treatment-Response Feedback.

Covers all Phase 2C scientific and architectural requirements:
1. Diagnostic delay: non-severe elevated BP requires repeated encounter confirmation before diagnosis.
2. Undiagnosed elevated BP: latent hypertensive patient who does not meet clinical criteria remains undiagnosed in EHR.
3. Severe elevation immediate diagnosis: SBP >= 180 or DBP >= 120 diagnoses immediately at visit 1.
4. Normotensive patient invariance: normal readings never trigger hypertension diagnosis.
5. Prescription timing & point-in-time invariance: prescription at Day 200 does not alter Day 180 latent state or history.
6. Prescription discontinuation: stopping prescription ceases treatment response from that timestamp onward.
7. Prescription possession vs. adherence exposure: non-adherent patient experiences 0 BP reduction despite active Rx in EHR.
8. Pharmacodynamic ramp-up: gradual onset of treatment effect across documented ramp period.
9. Deterministic reproducibility across seeds and process lifecycles.
10. End-to-end integration in ExperimentRunner with CSV export.
"""

import copy
import random
from datetime import datetime, timedelta
import pytest

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.datagen.forward_hemodynamics import (
    ForwardHemodynamicConfig,
    ForwardHemodynamicSimulator,
    LatentHemodynamicState,
    ClinicalDiagnosisEvent,
    PrescriptionEvent,
    derive_hemodynamic_seed,
    HEMODYNAMIC_ENGINE_LEGACY,
    HEMODYNAMIC_ENGINE_FORWARD,
    EvidentialStatus,
)
from synapse_simulator.modules.engine import ClinicalModuleRunner
from synapse_simulator.modules.loader import load_clinical_module
from synapse_simulator.evaluation.experiment import ExperimentRunner, ExperimentConfig
from synapse_simulator.evaluation.medication_status import is_prescription_active_at


def make_patient(
    patient_id: str = "p_c_01",
    age: int = 52,
    gender: str = "Female",
    birth_date: datetime = datetime(1972, 1, 1),
    latent_conditions: dict = None,
    baseline_conditions: dict = None,
) -> PatientContext:
    """Helper to construct a deterministic patient context."""
    return PatientContext(
        patient_id=patient_id,
        name=f"Patient_{patient_id}",
        age=age,
        gender=gender,
        birth_date=birth_date,
        latent_conditions=latent_conditions or {},
        baseline_conditions=baseline_conditions or {},
        chronic_conditions=[],
        prescriptions=[],
        is_alive=True,
    )


# =============================================================================
# Requirement 1 & 2: Diagnostic Delay and Repeated Encounter Confirmation
# =============================================================================

def test_diagnostic_delay_two_visit_confirmation():
    """Requirement 1: Moderate elevated BP (>= 140/90 mmHg) requires at least two distinct
    clinical encounters before confirming clinical diagnosis (ICMR/AHA guidelines).
    After 1 encounter, condition is pending confirmation and NOT diagnosed in EHR.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=42,
    )
    p = make_patient("p_delay_01", age=55, gender="Male")
    history = {"diagnosed_conditions": []}

    t1 = datetime(2024, 2, 1, 10, 0)
    t2 = datetime(2024, 4, 15, 10, 0)

    # Visit 1: Moderate elevation (SBP 152, DBP 94)
    dx_event_1 = sim.evaluate_clinical_diagnosis(
        patient=p,
        encounter_id="enc-001",
        encounter_time=t1,
        observed_sbp=152.0,
        observed_dbp=94.0,
        clinical_history=history,
    )
    # Diagnostic delay: visit 1 does NOT confirm diagnosis
    assert dx_event_1 is None, "First moderate elevated reading must not trigger immediate diagnosis"
    assert "I10" not in history["diagnosed_conditions"], "EHR must not contain I10 after only 1 visit"
    assert len(p.attributes.get("clinical_bp_visits", [])) == 1

    # Visit 2: Repeated moderate elevation (SBP 148, DBP 92)
    dx_event_2 = sim.evaluate_clinical_diagnosis(
        patient=p,
        encounter_id="enc-002",
        encounter_time=t2,
        observed_sbp=148.0,
        observed_dbp=92.0,
        clinical_history=history,
    )
    # Confirmed diagnosis on visit 2
    assert dx_event_2 is not None, "Second elevated encounter must confirm diagnosis"
    assert isinstance(dx_event_2, ClinicalDiagnosisEvent)
    assert dx_event_2.criteria_met == "REPEATED_ELEVATED_BP_CONFIRMED"
    assert dx_event_2.timestamp == t2
    assert dx_event_2.observed_sbp == 148.0
    assert dx_event_2.observed_dbp == 92.0
    assert dx_event_2.condition_code == "I10"


# =============================================================================
# Requirement 2: Undiagnosed Elevated BP (Community Hypertensive)
# =============================================================================

def test_undiagnosed_elevated_bp_community_hypertensive():
    """Requirement 2: A patient with true latent elevated blood pressure who does not attend
    clinic (0 encounters) remains completely un-diagnosed in EHR, naturally generating the
    undiagnosed community hypertensive cohort.
    """
    cfg = ForwardHemodynamicConfig(
        engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
        mean_sbp_anchor=150.0,  # High baseline anchor
        mean_dbp_anchor=95.0,
    )
    sim = ForwardHemodynamicSimulator(config=cfg, base_seed=42)
    p = make_patient("p_undiag_01", age=60, gender="Female")

    t_eval = datetime(2024, 6, 15, 9, 30)
    latent_state = sim.get_latent_state_at(p, target_time=t_eval)

    # Biological state is elevated (true hypertensive)
    assert latent_state.latent_sbp >= 140.0
    assert latent_state.latent_dbp >= 90.0

    # But patient has attended zero clinical encounters
    assert len(p.attributes.get("clinical_bp_visits", [])) == 0
    assert "I10" not in p.latent_conditions or not p.latent_conditions["I10"].get("recognized")


# =============================================================================
# Requirement 2 & 6: Severe Elevation Immediate Diagnosis
# =============================================================================

def test_severe_hypertension_immediate_diagnosis():
    """Requirement 2: Observed SBP >= 180 or DBP >= 120 triggers immediate clinical diagnosis
    at a single encounter (Hypertensive Crisis / Urgency criteria).
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=42,
    )
    p = make_patient("p_crisis_01", age=62, gender="Male")
    history = {"diagnosed_conditions": []}

    t1 = datetime(2024, 3, 1, 11, 0)
    dx_event = sim.evaluate_clinical_diagnosis(
        patient=p,
        encounter_id="enc-crisis-01",
        encounter_time=t1,
        observed_sbp=188.0,
        observed_dbp=115.0,
        clinical_history=history,
    )

    assert dx_event is not None
    assert dx_event.criteria_met == "SEVERE_ELEVATION_IMMEDIATE"
    assert dx_event.timestamp == t1
    assert dx_event.observed_sbp == 188.0


# =============================================================================
# Requirement 2: Normotensive Patient Never Diagnosed
# =============================================================================

def test_normotensive_patient_never_diagnosed():
    """Requirement 2: A normotensive patient attending multiple clinical visits with normal
    readings (< 140/90 mmHg) is never diagnosed with hypertension.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=42,
    )
    p = make_patient("p_normo_01", age=48, gender="Female")
    history = {"diagnosed_conditions": []}

    for i in range(5):
        t = datetime(2024, 1, 1) + timedelta(days=30 * (i + 1))
        dx = sim.evaluate_clinical_diagnosis(
            patient=p,
            encounter_id=f"enc-normo-{i}",
            encounter_time=t,
            observed_sbp=122.0 + i,
            observed_dbp=78.0,
            clinical_history=history,
        )
        assert dx is None, f"Visit {i} with normal BP must not diagnose hypertension"


# =============================================================================
# Requirement 3 & 4: Prescription Timing & Point-in-Time Invariance
# =============================================================================

def test_prescription_timing_and_point_in_time_invariance():
    """Requirements 3 & 4: Antihypertensive prescription starting at Day 200 must:
    1. Have zero treatment effect on earlier timestamps (e.g., Day 180 survey).
    2. Leave past measurements and earlier latent states completely unchanged.
    3. Apply pharmacological reduction only on or after start_time.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            treatment_ramp_days=0.0,  # Immediate for clear step test
            fixed_adherence_factor=1.0,
        ),
        base_seed=42,
    )
    p = make_patient("p_rx_timing", age=55, gender="Male")
    obs_start = datetime(2024, 1, 1)

    t_pre = obs_start + timedelta(days=180)   # Day 180 (survey)
    t_rx_start = obs_start + timedelta(days=200)  # Day 200 (prescription start)
    t_post = obs_start + timedelta(days=220)  # Day 220 (subsequent clinic visit)

    rx_event = sim.create_prescription_event(
        patient_id=p.patient_id,
        prescription_id="rx-test-001",
        encounter_id="enc-test-001",
        drug_name="Amlodipine",
        dosage="5mg",
        start_time=t_rx_start,
        timestamp=t_rx_start,
    )

    # 1. Evaluate Day 180 BEFORE prescription exists
    state_pre_no_rx = sim.get_latent_state_at(p, target_time=t_pre, observation_start=obs_start)
    assert state_pre_no_rx.treatment_effect_sbp == 0.0
    assert state_pre_no_rx.active_prescriptions_count == 0

    # 2. Evaluate Day 180 WITH future prescription in patient's store (point-in-time check)
    state_pre_with_rx = sim.get_latent_state_at(
        p,
        target_time=t_pre,
        observation_start=obs_start,
        prescriptions=[rx_event],
    )
    assert state_pre_with_rx.treatment_effect_sbp == 0.0
    assert state_pre_with_rx.active_prescriptions_count == 0
    assert state_pre_with_rx.latent_sbp == state_pre_no_rx.latent_sbp
    assert state_pre_with_rx.latent_dbp == state_pre_no_rx.latent_dbp

    # 3. Evaluate Day 220 (AFTER prescription active)
    state_post = sim.get_latent_state_at(
        p,
        target_time=t_post,
        observation_start=obs_start,
        prescriptions=[rx_event],
    )
    assert state_post.active_prescriptions_count == 1
    assert state_post.treatment_effect_sbp == 12.0
    assert state_post.treatment_effect_dbp == 7.0
    # Latent pressure is lowered by exactly the treatment effect (plus 20 days aging drift)
    expected_drift = round(0.60 * (220 / 365.25), 2)
    assert state_post.latent_sbp == pytest.approx(state_post.baseline_sbp + expected_drift - 12.0, abs=0.2)


# =============================================================================
# Requirement 3 & 4: Prescription Discontinuation
# =============================================================================

def test_prescription_discontinuation_timing():
    """Requirements 3 & 4: When a prescription is discontinued at t_stop, the treatment
    response ceases for subsequent timestamps without altering earlier treatment intervals.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            treatment_ramp_days=0.0,
            fixed_adherence_factor=1.0,
        ),
        base_seed=42,
    )
    p = make_patient("p_discon_01", age=56, gender="Female")
    obs_start = datetime(2024, 1, 1)

    t_start = obs_start + timedelta(days=100)
    t_stop = obs_start + timedelta(days=200)
    t_active = obs_start + timedelta(days=150)
    t_after = obs_start + timedelta(days=250)

    rx_initial = sim.create_prescription_event(
        patient_id=p.patient_id,
        prescription_id="rx-disc-01",
        encounter_id="enc-01",
        start_time=t_start,
        timestamp=t_start,
    )
    rx_discontinued = sim.discontinue_prescription_event(
        rx_initial,
        discontinuation_time=t_stop,
        reason="Patient developed peripheral edema",
    )
    assert rx_discontinued.status == "Discontinued"
    assert rx_discontinued.end_time == t_stop

    # During active window (Day 150): treatment effect is active
    state_active = sim.get_latent_state_at(p, target_time=t_active, prescriptions=[rx_discontinued])
    assert state_active.active_prescriptions_count == 1
    assert state_active.treatment_effect_sbp == 12.0

    # After discontinuation (Day 250): treatment effect ceases
    state_after = sim.get_latent_state_at(p, target_time=t_after, prescriptions=[rx_discontinued])
    assert state_after.active_prescriptions_count == 0
    assert state_after.treatment_effect_sbp == 0.0
    assert state_after.treatment_effect_dbp == 0.0


# =============================================================================
# Requirement 5: Prescription Possession vs. Medication Adherence Exposure
# =============================================================================

def test_prescription_possession_vs_adherence_exposure():
    """Requirement 5: Prescribed medication possession must remain strictly distinct from
    actual biological drug exposure:
    - Adherent patient (theta = 1.0) achieves full blood pressure reduction.
    - Partial adherent (theta = 0.5) achieves 50% blood pressure reduction.
    - Non-adherent patient (theta = 0.0) achieves 0.0 mmHg reduction despite active prescription in EHR!
    """
    obs_start = datetime(2024, 1, 1)
    t_eval = obs_start + timedelta(days=200)

    # 1. Full adherence (theta = 1.0)
    sim_full = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            fixed_adherence_factor=1.0,
            treatment_ramp_days=0.0,
        ),
        base_seed=42,
    )
    p = make_patient("p_adh_test", age=55, gender="Male")

    # 1. Full adherence (theta = 1.0)
    sim_full = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            fixed_adherence_factor=1.0,
            treatment_ramp_days=0.0,
        ),
        base_seed=42,
    )
    rx_full = sim_full.create_prescription_event(p.patient_id, "rx-01", "enc-01", start_time=obs_start)
    state_full = sim_full.get_latent_state_at(p, target_time=t_eval, prescriptions=[rx_full])
    assert state_full.adherence_factor == 1.0
    assert state_full.treatment_effect_sbp == 12.0
    assert state_full.treatment_effect_dbp == 7.0

    # 2. Complete non-adherence (theta = 0.0)
    sim_non = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            fixed_adherence_factor=0.0,
            treatment_ramp_days=0.0,
        ),
        base_seed=42,
    )
    rx_non = sim_non.create_prescription_event(p.patient_id, "rx-02", "enc-02", start_time=obs_start)
    state_non = sim_non.get_latent_state_at(p, target_time=t_eval, prescriptions=[rx_non])
    assert state_non.adherence_factor == 0.0
    assert state_non.treatment_effect_sbp == 0.0
    assert state_non.treatment_effect_dbp == 0.0
    # Latent BP is completely unreduced despite active prescription!
    assert state_non.latent_sbp == pytest.approx(state_full.latent_sbp + 12.0, abs=0.01)
    assert state_non.latent_dbp == pytest.approx(state_full.latent_dbp + 7.0, abs=0.01)

    # 3. Partial adherence (theta = 0.5)
    sim_part = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            fixed_adherence_factor=0.5,
            treatment_ramp_days=0.0,
        ),
        base_seed=42,
    )
    rx_part = sim_part.create_prescription_event(p.patient_id, "rx-03", "enc-03", start_time=obs_start)
    state_part = sim_part.get_latent_state_at(p, target_time=t_eval, prescriptions=[rx_part])
    assert state_part.adherence_factor == 0.5
    assert state_part.treatment_effect_sbp == 6.0
    assert state_part.treatment_effect_dbp == 3.5
    assert state_part.latent_sbp == pytest.approx(state_full.latent_sbp + 6.0, abs=0.01)
    assert state_part.latent_dbp == pytest.approx(state_full.latent_dbp + 3.5, abs=0.01)


# =============================================================================
# Requirement 4: Pharmacodynamic Ramp-Up
# =============================================================================

def test_pharmacodynamic_ramp_up():
    """Requirement 4: Treatment response follows a gradual ramp to steady-state across
    the documented treatment_ramp_days period.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            treatment_ramp_days=14.0,
            fixed_adherence_factor=1.0,
        ),
        base_seed=42,
    )
    p = make_patient("p_ramp_01", age=50, gender="Female")
    obs_start = datetime(2024, 1, 1)

    rx = sim.create_prescription_event("p_ramp_01", "rx-ramp", "enc-01", start_time=obs_start)

    # Day 0: Ramp = 0.0
    s0 = sim.get_latent_state_at(p, target_time=obs_start, prescriptions=[rx])
    assert s0.treatment_effect_sbp == 0.0

    # Day 7 (half ramp): Ramp = 0.5 -> 6.0 mmHg
    s7 = sim.get_latent_state_at(p, target_time=obs_start + timedelta(days=7), prescriptions=[rx])
    assert s7.treatment_effect_sbp == pytest.approx(6.0, abs=0.2)

    # Day 14 (full ramp): Ramp = 1.0 -> 12.0 mmHg
    s14 = sim.get_latent_state_at(p, target_time=obs_start + timedelta(days=14), prescriptions=[rx])
    assert s14.treatment_effect_sbp == pytest.approx(12.0, abs=0.1)

    # Day 30: Still steady-state 12.0 mmHg
    s30 = sim.get_latent_state_at(p, target_time=obs_start + timedelta(days=30), prescriptions=[rx])
    assert s30.treatment_effect_sbp == pytest.approx(12.0, abs=0.1)


# =============================================================================
# Requirement 7: Deterministic Reproducibility
# =============================================================================

def test_deterministic_reproducibility_phase2c():
    """Requirement 7: All Phase 2C operations (adherence draw, diagnosis evaluation,
    prescription creation) are bit-for-bit reproducible across separate instances with identical seeds.
    """
    p1 = make_patient("p_rep_test", age=58, gender="Male")
    p2 = make_patient("p_rep_test", age=58, gender="Male")

    sim1 = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=12345,
    )
    sim2 = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=12345,
    )

    # Adherence factor reproducibility
    adh1 = sim1.get_patient_adherence("p_rep_test")
    adh2 = sim2.get_patient_adherence("p_rep_test")
    assert adh1 == adh2

    # Latent state reproducibility
    t = datetime(2024, 6, 15, 12, 0)
    st1 = sim1.get_latent_state_at(p1, target_time=t)
    st2 = sim2.get_latent_state_at(p2, target_time=t)
    assert st1.latent_sbp == st2.latent_sbp
    assert st1.latent_dbp == st2.latent_dbp
    assert st1.pulse_pressure == st2.pulse_pressure


# =============================================================================
# End-to-End ExperimentRunner Integration (Phase 2C)
# =============================================================================

def test_end_to_end_forward_cohort_simulation_phase2c(tmp_path):
    """Verify complete end-to-end cohort generation under FORWARD_STATE_SPACE in Phase 2C.
    Ensures:
    - ClinicalModuleRunner steps patients and records BP observations from latent forward state.
    - Prescriptions and clinical diagnoses emit structured ActionRequests.
    - Community assessments query active prescriptions and evaluate treatment response.
    - All exported CSV files exist and adhere to schema.
    """
    import csv

    out_dir = tmp_path / "fwd_phase2c_run"
    config = ExperimentConfig(
        cohort_size=10,
        seed=2024,
        timestep_days=14,
        observation_end=datetime(2024, 1, 1) + timedelta(days=210),
        output_dir=out_dir,
        hemodynamic_engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
    )

    out_path, telemetry = ExperimentRunner.generate_cohort(config)
    assert telemetry["hemodynamic_engine_mode"] == HEMODYNAMIC_ENGINE_FORWARD

    # Verify CSV files exist
    assert (out_path / "community_assessments.csv").exists()
    assert (out_path / "community_bp_readings.csv").exists()
    assert (out_path / "patients.csv").exists()
    assert (out_path / "encounters.csv").exists()
    assert (out_path / "conditions.csv").exists()
    assert (out_path / "medications.csv").exists()

    with open(out_path / "community_assessments.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assessments = list(reader)
        assert len(assessments) > 0
        for a in assessments:
            if a["status"] == "COMPLETED":
                assert float(a["sbp"]) > 0
                assert float(a["dbp"]) > 0
                assert float(a["pulse_pressure"]) >= 20.0


# =============================================================================
# Phase 2C Scientific Verification & Invariant Regression Tests
# =============================================================================

def test_diagnosis_historical_invariance_no_future_lookahead():
    """Verify that historical diagnoses cannot be inferred from future encounters.

    If Visit 1 at Day 10 is evaluated retrospectively when Visit 2 at Day 40 is already
    present in the patient's visit history, the evaluation at Day 10 MUST NOT look into
    the future and confirm a diagnosis prematurely.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=42,
    )
    p = make_patient("p_retro_lookahead", age=52, gender="Female")
    t1 = datetime(2024, 1, 10, 10, 0)
    t2 = datetime(2024, 2, 20, 10, 0)

    # 1. Forward simulation: Visit 1 at t1 (elevated, but pending confirmation)
    d1 = sim.evaluate_clinical_diagnosis(p, encounter_id="enc-01", encounter_time=t1, observed_sbp=148.0, observed_dbp=94.0)
    assert d1 is None

    # 2. Forward simulation: Visit 2 at t2 (elevated -> confirms diagnosis)
    d2 = sim.evaluate_clinical_diagnosis(p, encounter_id="enc-02", encounter_time=t2, observed_sbp=150.0, observed_dbp=95.0)
    assert d2 is not None
    assert d2.criteria_met == "REPEATED_ELEVATED_BP_CONFIRMED"
    assert d2.timestamp == t2

    # 3. Retrospective Point-in-Time Evaluation:
    # Query diagnosis status at t1 on a fresh patient instance that holds the full visit history
    p_retro = make_patient("p_retro_lookahead", age=52, gender="Female")
    p_retro.attributes["clinical_bp_visits"] = [
        {"encounter_id": "enc-01", "timestamp": t1.isoformat(), "sbp": 148.0, "dbp": 94.0, "is_elevated": True},
        {"encounter_id": "enc-02", "timestamp": t2.isoformat(), "sbp": 150.0, "dbp": 95.0, "is_elevated": True},
    ]
    d_retro_at_t1 = sim.evaluate_clinical_diagnosis(
        p_retro,
        encounter_id="enc-01",
        encounter_time=t1,
        observed_sbp=148.0,
        observed_dbp=94.0,
    )
    # At t1, future encounter enc-02 MUST NOT be counted!
    assert d_retro_at_t1 is None, "Future encounter at t2 must not confirm diagnosis at earlier timestamp t1"


def test_multiple_concurrent_prescriptions_do_not_multiply_reduction():
    """Verify that multiple concurrent prescriptions (e.g. refills, re-orders, or overlapping agents)
    do NOT multiply the pharmacological treatment effect repeatedly.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            treatment_ramp_days=14.0,
            fixed_adherence_factor=1.0,
        ),
        base_seed=42,
    )
    p = make_patient("p_multirx", age=55, gender="Male")
    t0 = datetime(2024, 1, 1)

    rx1 = sim.create_prescription_event("p_multirx", "rx-01", "enc-01", start_time=t0)
    rx2 = sim.create_prescription_event("p_multirx", "rx-02", "enc-02", start_time=t0 + timedelta(days=20))
    rx3 = sim.create_prescription_event("p_multirx", "rx-03", "enc-03", start_time=t0 + timedelta(days=40))

    t_eval = t0 + timedelta(days=60)
    st_single = sim.get_latent_state_at(p, target_time=t_eval, prescriptions=[rx1])
    st_triple = sim.get_latent_state_at(p, target_time=t_eval, prescriptions=[rx1, rx2, rx3])

    assert st_single.active_prescriptions_count == 1
    assert st_triple.active_prescriptions_count == 3
    # Treatment reduction must be bounded by delta_drug and NOT tripled (12.0 vs 36.0)
    assert st_triple.treatment_effect_sbp == pytest.approx(12.0, abs=0.01)
    assert st_triple.treatment_effect_dbp == pytest.approx(7.0, abs=0.01)
    assert st_single.latent_sbp == pytest.approx(st_triple.latent_sbp, abs=0.01)


def test_same_encounter_repeated_readings_do_not_trigger_multi_visit_diagnosis():
    """Verify that repeated elevated readings taken within the SAME encounter do NOT satisfy
    the 2-visit confirmation rule (preventing intra-encounter false-positive confirmation).
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=42,
    )
    p = make_patient("p_same_enc", age=49, gender="Male")
    t1_first = datetime(2024, 3, 1, 10, 0)
    t1_second = datetime(2024, 3, 1, 10, 15)

    # Reading 1 in enc-same
    d1 = sim.evaluate_clinical_diagnosis(p, encounter_id="enc-same", encounter_time=t1_first, observed_sbp=152.0, observed_dbp=94.0)
    assert d1 is None

    # Reading 2 in same enc-same
    d2 = sim.evaluate_clinical_diagnosis(p, encounter_id="enc-same", encounter_time=t1_second, observed_sbp=149.0, observed_dbp=92.0)
    assert d2 is None, "Repeated readings in same encounter must not trigger multi-visit confirmed diagnosis"


def test_active_prescriptions_set_input_steady_state():
    """Verify that when active treated patients are provided as a set of patient IDs (e.g., from
    active_antihypertensive_pids), the simulator correctly evaluates steady-state reduction.
    """
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(
            engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
            delta_drug_sbp=12.0,
            delta_drug_dbp=7.0,
            treatment_ramp_days=14.0,
            fixed_adherence_factor=1.0,
        ),
        base_seed=42,
    )
    p = make_patient("p_set_input", age=54, gender="Female")
    t_survey = datetime(2024, 6, 29)  # Day 180

    st_unmedicated = sim.get_latent_state_at(p, target_time=t_survey, prescriptions=None)
    st_medicated = sim.get_latent_state_at(p, target_time=t_survey, prescriptions={p.patient_id})

    assert st_medicated.active_prescriptions_count == 1
    assert st_medicated.treatment_effect_sbp == pytest.approx(12.0, abs=0.01)
    assert st_medicated.latent_sbp == pytest.approx(st_unmedicated.latent_sbp - 12.0, abs=0.01)
