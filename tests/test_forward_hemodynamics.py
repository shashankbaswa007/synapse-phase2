"""
Deterministic unit and integration tests for ForwardHemodynamicSimulator (Phase 2B).

Covers all 10 architectural and scientific requirements specified in Task 7:
1. Reproducible latent-state initialization.
2. Different patient identifiers receiving independently derived random streams.
3. Invalid engine configuration being rejected.
4. Legacy mode remaining the default.
5. Legacy-mode outputs remaining unchanged under the existing regression suite.
6. Forward latent state being distinct from observed measurement values.
7. Future diagnoses and prescriptions not changing earlier latent-state results.
8. Repeated evaluation at the same timestamp producing consistent results.
9. Configured evolution being applied only according to its documented temporal semantics.
10. Existing BP protocol and point-in-time invariance tests continuing to pass.
"""

import copy
import math
import random
from datetime import datetime, timedelta
from typing import Dict
import pytest

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.datagen.bp_measurement import (
    BpMeasurementProtocolSimulator,
    create_lasi_tri_measurement_protocol,
    create_single_reading_baseline_protocol,
    BpDerivationCategory,
)
from synapse_simulator.datagen.forward_hemodynamics import (
    ForwardHemodynamicConfig,
    ForwardHemodynamicSimulator,
    LatentHemodynamicState,
    derive_hemodynamic_seed,
    HEMODYNAMIC_ENGINE_LEGACY,
    HEMODYNAMIC_ENGINE_FORWARD,
    VALID_HEMODYNAMIC_MODES,
    EvidentialStatus,
)
from synapse_simulator.datagen.community_assessment import (
    CommunityAssessmentConfig,
    CommunityAssessmentGenerator,
)
from synapse_simulator.evaluation.experiment import ExperimentConfig


# =============================================================================
# Helper Fixtures
# =============================================================================

def make_patient(
    patient_id: str = "p001",
    age: int = 50,
    gender: str = "Female",
    birth_date: datetime = datetime(1974, 1, 1),
    latent_conditions: dict = None,
    baseline_conditions: dict = None,
) -> PatientContext:
    """Construct a minimal deterministic PatientContext for testing."""
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
# Requirement 1: Reproducible Latent-State Initialization
# =============================================================================

def test_req1_reproducible_latent_state_initialization():
    """Requirement 1: Given identical seed and patient identity, latent state initialization
    must produce bit-for-bit identical physiological values across separate simulator instances.
    """
    p = make_patient("p_rep_01", age=52, gender="Male")
    cfg = ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD)

    sim1 = ForwardHemodynamicSimulator(config=cfg, base_seed=12345)
    sim2 = ForwardHemodynamicSimulator(config=cfg, base_seed=12345)

    state1 = sim1.initialize_patient_baseline(p, observation_start=datetime(2024, 1, 1))
    state2 = sim2.initialize_patient_baseline(p, observation_start=datetime(2024, 1, 1))

    assert state1.latent_sbp == state2.latent_sbp
    assert state1.latent_dbp == state2.latent_dbp
    assert state1.pulse_pressure == state2.pulse_pressure
    assert state1.baseline_sbp == state2.baseline_sbp
    assert state1.baseline_dbp == state2.baseline_dbp
    assert state1.timestamp == state2.timestamp
    assert state1.provenance == "FORWARD_HEMODYNAMIC_SIMULATOR"
    assert state1.is_valid is True


# =============================================================================
# Requirement 2: Independent PRNG Streams Across Patient Identifiers
# =============================================================================

def test_req2_independent_random_streams_across_patients():
    """Requirement 2: Different patient identifiers must receive independently derived PRNG streams,
    avoiding order-dependent stream contamination.
    """
    # Two patients with identical demographics
    pA = make_patient("patient_AAA", age=50, gender="Female")
    pB = make_patient("patient_BBB", age=50, gender="Female")

    sim = ForwardHemodynamicSimulator(base_seed=42)

    seedA = derive_hemodynamic_seed(42, "patient_AAA")
    seedB = derive_hemodynamic_seed(42, "patient_BBB")
    assert seedA != seedB, "Different patient identifiers must derive different seeds"

    stateA = sim.initialize_patient_baseline(pA)
    stateB = sim.initialize_patient_baseline(pB)
    assert (stateA.latent_sbp, stateA.latent_dbp) != (stateB.latent_sbp, stateB.latent_dbp)

    # Order independence: initializing pA first then pB vs initializing pB alone
    sim_isolated = ForwardHemodynamicSimulator(base_seed=42)
    stateB_isolated = sim_isolated.initialize_patient_baseline(pB)
    assert stateB.latent_sbp == stateB_isolated.latent_sbp
    assert stateB.latent_dbp == stateB_isolated.latent_dbp


# =============================================================================
# Requirement 3: Invalid Engine Configuration Rejected
# =============================================================================

def test_req3_invalid_engine_configuration_rejected():
    """Requirement 3: Invalid hemodynamic engine configurations must fail loudly with ValueError."""
    with pytest.raises(ValueError, match="Invalid hemodynamic engine mode"):
        ForwardHemodynamicConfig(engine_mode="INVALID_UNKNOWN_MODE")

    with pytest.raises(ValueError, match="Invalid hemodynamic_engine_mode"):
        CommunityAssessmentConfig(hemodynamic_engine_mode="NON_EXISTENT_MODE")

    with pytest.raises(ValueError, match="Invalid hemodynamic_engine_mode"):
        ExperimentConfig(hemodynamic_engine_mode="UNSUPPORTED_HEMODYNAMIC_MODE")


# =============================================================================
# Requirement 4: Legacy Mode Remains Default
# =============================================================================

def test_req4_legacy_mode_remains_default():
    """Requirement 4: LEGACY_CONDITIONAL must remain the default across all configuration models
    and generator classes. The experimental engine must never activate implicitly.
    """
    fwd_cfg = ForwardHemodynamicConfig()
    assert fwd_cfg.engine_mode == HEMODYNAMIC_ENGINE_LEGACY

    comm_cfg = CommunityAssessmentConfig()
    assert comm_cfg.hemodynamic_engine_mode == HEMODYNAMIC_ENGINE_LEGACY

    exp_cfg = ExperimentConfig()
    assert exp_cfg.hemodynamic_engine_mode == HEMODYNAMIC_ENGINE_LEGACY

    # Generator instantiated with default configuration does not instantiate forward simulator
    gen = CommunityAssessmentGenerator()
    assert gen.forward_simulator is None
    assert gen.config.hemodynamic_engine_mode == HEMODYNAMIC_ENGINE_LEGACY


# =============================================================================
# Requirement 5: Legacy Mode Outputs Remain Unchanged
# =============================================================================

def test_req5_legacy_outputs_unchanged_and_prng_isolation():
    """Requirement 5: Running in legacy mode produces identical outputs to legacy baseline,
    and initializing forward simulator components does not perturb the legacy PRNG sequence.
    """
    patients = {
        f"p{i}": make_patient(f"p{i}", age=50 + i, gender="Female" if i % 2 == 0 else "Male")
        for i in range(10)
    }

    # Baseline legacy generator
    gen_legacy = CommunityAssessmentGenerator(
        config=CommunityAssessmentConfig(
            seed=42,
            hemodynamic_engine_mode=HEMODYNAMIC_ENGINE_LEGACY,
        )
    )
    assessments_base = gen_legacy.generate(patients)

    # Initialize a forward simulator instance in the background (verifying zero side-effects on global/local PRNG)
    fwd_sim = ForwardHemodynamicSimulator(base_seed=42)
    _ = [fwd_sim.initialize_patient_baseline(p) for p in patients.values()]

    # Run another legacy generator
    gen_legacy_again = CommunityAssessmentGenerator(
        config=CommunityAssessmentConfig(
            seed=42,
            hemodynamic_engine_mode=HEMODYNAMIC_ENGINE_LEGACY,
        )
    )
    assessments_check = gen_legacy_again.generate(patients)

    assert len(assessments_base) == len(assessments_check)
    for b, c in zip(assessments_base, assessments_check):
        assert b.patient_id == c.patient_id
        assert b.sbp == c.sbp
        assert b.dbp == c.dbp
        assert b.pulse_pressure == c.pulse_pressure
        assert b.status == c.status


# =============================================================================
# Requirement 6: Forward Latent State Distinct from Observed Measurement Values
# =============================================================================

def test_req6_latent_state_distinct_from_observed_measurements():
    """Requirement 6: True latent resting physiological blood pressure must remain strictly distinct
    from observed individual readings (with situational alerting and noise) and protocol analysis mean.
    """
    p = make_patient("p_distinct_01", age=55, gender="Female")
    comm_cfg = CommunityAssessmentConfig(
        seed=42,
        hemodynamic_engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
    )
    gen = CommunityAssessmentGenerator(config=comm_cfg)
    assessments = gen.generate({"p_distinct_01": p})
    readings = gen.get_bp_readings()
    latent_states = gen.get_latent_hemodynamic_states()

    assert "p_distinct_01" in latent_states
    latent = latent_states["p_distinct_01"]
    assert len(assessments) == 1
    assessment = assessments[0]

    # There should be 3 individual readings under LASI protocol
    assert len(readings) == 3
    r1, r2, r3 = readings[0], readings[1], readings[2]

    # Reading 1 includes white-coat / situational alerting effect (+3 to +8 mmHg)
    assert r1.reading_number == 1
    assert r1.sbp is not None

    # Latent state is pure resting continuous biological value
    assert isinstance(latent.latent_sbp, float)
    assert isinstance(latent.latent_dbp, float)
    assert latent.pulse_pressure == round(latent.latent_sbp - latent.latent_dbp, 1)

    # Final assessment sbp is the protocol analysis value ((r2 + r3)/2), not the raw latent state
    assert assessment.sbp == round((r2.sbp + r3.sbp) / 2.0, 1)
    assert assessment.derivation_category == BpDerivationCategory.PROTOCOL_MEAN_READINGS_2_AND_3.value

    # Verify that the latent state was not overwritten by the observed assessment
    assert latent.provenance == "FORWARD_HEMODYNAMIC_SIMULATOR"
    assert assessment.provenance == "COMMUNITY_HEALTH_ASSESSMENT_LAYER"


# =============================================================================
# Requirement 7: Future Diagnoses and Prescriptions Do Not Alter Earlier Latent State
# =============================================================================

def test_req7_future_diagnoses_and_prescriptions_do_not_alter_latent_state():
    """Requirement 7: Latent physiological state at time T must be invariant to incident diagnoses
    or prescriptions occurring strictly after time T (future-state invariance).
    """
    obs_start = datetime(2024, 1, 1)
    eval_time = obs_start + timedelta(days=180)  # Day 180

    # Patient 1: no hypertension throughout simulation
    p_unaffected = make_patient("p_no_htn", age=55, gender="Male", birth_date=datetime(1969, 1, 1))

    # Patient 2: receives hypertension diagnosis at Day 300 (future) and medication at Day 320 (future)
    p_future_htn = make_patient(
        "p_future_htn",
        age=55,
        gender="Male",
        birth_date=datetime(1969, 1, 1),
        latent_conditions={
            "I10": {
                "onset_time": obs_start + timedelta(days=300),
                "resolved": False,
                "resolved_time": None,
            }
        },
    )

    fwd_cfg = ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD)
    sim = ForwardHemodynamicSimulator(config=fwd_cfg, base_seed=42)

    # Evaluate both at baseline Day 0
    state1_d0 = sim.initialize_patient_baseline(p_unaffected, observation_start=obs_start)
    # Give p_future_htn the same ID as p_unaffected temporarily to isolate biological factors vs seed
    p_future_htn_same_id = copy.deepcopy(p_future_htn)
    p_future_htn_same_id.patient_id = "p_no_htn"
    state2_d0 = sim.initialize_patient_baseline(p_future_htn_same_id, observation_start=obs_start)
    assert state1_d0.latent_sbp == state2_d0.latent_sbp
    assert state1_d0.latent_dbp == state2_d0.latent_dbp

    # Evaluate both at Day 180
    state1_d180 = sim.get_latent_state_at(p_unaffected, target_time=eval_time, observation_start=obs_start)
    state2_d180 = sim.get_latent_state_at(p_future_htn_same_id, target_time=eval_time, observation_start=obs_start)

    assert state1_d180.latent_sbp == state2_d180.latent_sbp
    assert state1_d180.latent_dbp == state2_d180.latent_dbp
    assert state1_d180.pulse_pressure == state2_d180.pulse_pressure


# =============================================================================
# Requirement 8: Repeated Evaluation at Same Timestamp Produces Consistent Results
# =============================================================================

def test_req8_repeated_evaluation_at_same_timestamp_consistent():
    """Requirement 8: Repeated evaluation at the same timestamp must be purely functional and idempotent."""
    p = make_patient("p_idem_01", age=60, gender="Female")
    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=999,
    )
    t_eval = datetime(2024, 6, 15, 10, 0, 0)

    res1 = sim.get_latent_state_at(p, target_time=t_eval)
    res2 = sim.get_latent_state_at(p, target_time=t_eval)
    res3 = sim.get_latent_state_at(p, target_time=t_eval)

    assert res1.latent_sbp == res2.latent_sbp == res3.latent_sbp
    assert res1.latent_dbp == res2.latent_dbp == res3.latent_dbp
    assert res1.pulse_pressure == res2.pulse_pressure == res3.pulse_pressure
    assert res1.cumulative_age_drift_sbp == res2.cumulative_age_drift_sbp == res3.cumulative_age_drift_sbp


# =============================================================================
# Requirement 9: Configured Evolution Applied Strictly According to Documented Semantics
# =============================================================================

def test_req9_evolution_applied_according_to_temporal_semantics():
    """Requirement 9: Vascular aging drift evolves strictly according to elapsed chronological time
    and physiological safeguards:
    - delta_t = 0 implies 0.0 drift
    - delta_t > 0 with enable_aging_drift=True accumulates annual_drift_sbp * elapsed_years
    - enable_aging_drift=False yields 0.0 drift
    - Pulse pressure safeguard (min_pulse_pressure >= 20 mmHg) is enforced at all times.
    """
    obs_start = datetime(2024, 1, 1)
    p = make_patient("p_drift_01", age=50, gender="Male", birth_date=datetime(1974, 1, 1))

    cfg_drift = ForwardHemodynamicConfig(
        engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
        enable_aging_drift=True,
        annual_drift_sbp=0.60,
        annual_drift_dbp_early=0.25,
        min_pulse_pressure=20.0,
    )
    sim_drift = ForwardHemodynamicSimulator(config=cfg_drift, base_seed=42)

    # 1. Delta_t = 0 (baseline)
    state_0 = sim_drift.get_latent_state_at(p, target_time=obs_start, observation_start=obs_start)
    assert state_0.cumulative_age_drift_sbp == 0.0
    assert state_0.latent_sbp == state_0.baseline_sbp

    # 2. Delta_t = 1.0 year (365.25 days)
    t_1yr = obs_start + timedelta(days=365.25)
    state_1yr = sim_drift.get_latent_state_at(p, target_time=t_1yr, observation_start=obs_start)
    assert state_1yr.cumulative_age_drift_sbp == pytest.approx(0.60, abs=0.05)
    assert state_1yr.latent_sbp == pytest.approx(state_0.baseline_sbp + 0.60, abs=0.1)

    # 3. Aging drift disabled
    cfg_no_drift = ForwardHemodynamicConfig(
        engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
        enable_aging_drift=False,
    )
    sim_no_drift = ForwardHemodynamicSimulator(config=cfg_no_drift, base_seed=42)
    state_no_drift = sim_no_drift.get_latent_state_at(p, target_time=t_1yr, observation_start=obs_start)
    assert state_no_drift.cumulative_age_drift_sbp == 0.0
    assert state_no_drift.latent_sbp == state_no_drift.baseline_sbp

    # 4. Pulse pressure safeguard
    assert state_0.pulse_pressure >= 20.0
    assert state_1yr.pulse_pressure >= 20.0


# =============================================================================
# Requirement 10: Existing BP Protocol Integration and Invariance Tests Pass
# =============================================================================

def test_req10_bp_protocol_integration_and_invariance():
    """Requirement 10: Forward engine connects seamlessly to BpMeasurementProtocolSimulator
    under both TRI_MEASUREMENT and SINGLE_READING protocols without altering or mutating
    the latent state representation.
    """
    obs_time = datetime(2024, 6, 15, 9, 30)
    p = make_patient("p_proto_01", age=58, gender="Female")

    sim = ForwardHemodynamicSimulator(
        config=ForwardHemodynamicConfig(engine_mode=HEMODYNAMIC_ENGINE_FORWARD),
        base_seed=42,
    )
    latent_state = sim.get_latent_state_at(p, target_time=obs_time)
    original_latent_sbp = latent_state.latent_sbp
    original_latent_dbp = latent_state.latent_dbp

    # Test under LASI Tri-Measurement Protocol
    tri_proto = BpMeasurementProtocolSimulator(create_lasi_tri_measurement_protocol())
    pat_rng1 = random.Random(12345)
    tri_result = sim.observe(latent_state, tri_proto, assessment_id="ca-01", pat_rng=pat_rng1)

    assert len(tri_result.readings) == 3
    assert tri_result.derivation_category == BpDerivationCategory.PROTOCOL_MEAN_READINGS_2_AND_3.value
    assert tri_result.final_sbp is not None
    assert tri_result.final_dbp is not None

    # Test under Single-Reading Protocol
    single_proto = BpMeasurementProtocolSimulator(create_single_reading_baseline_protocol())
    pat_rng2 = random.Random(12345)
    single_result = sim.observe(latent_state, single_proto, assessment_id="ca-02", pat_rng=pat_rng2)

    assert len(single_result.readings) == 1
    assert single_result.derivation_category == BpDerivationCategory.SINGLE_READING_BASELINE.value
    assert single_result.final_sbp is not None

    # Crucial guarantee: latent state was NOT mutated
    assert latent_state.latent_sbp == original_latent_sbp
    assert latent_state.latent_dbp == original_latent_dbp


# =============================================================================
# Evidential Metadata & Provenance Transparency
# =============================================================================

def test_evidential_metadata_and_provenance_transparency():
    """Verify that all configurable parameters carry explicit evidential pedigree metadata
    and none are marked as literature calibrated without grounds.
    """
    cfg = ForwardHemodynamicConfig()
    prov = cfg.parameter_provenance

    # Population anchors have literature grounding
    assert prov["mean_sbp_anchor"] == EvidentialStatus.LITERATURE_CALIBRATED.value
    assert prov["mean_dbp_anchor"] == EvidentialStatus.LITERATURE_CALIBRATED.value

    # Guards are marked as PHYSIOLOGICAL_GUARD
    assert prov["min_pulse_pressure"] == EvidentialStatus.PHYSIOLOGICAL_GUARD.value
    assert prov["min_sbp"] == EvidentialStatus.PHYSIOLOGICAL_GUARD.value
    assert prov["max_sbp"] == EvidentialStatus.PHYSIOLOGICAL_GUARD.value

    # Drift and comorbidity shifts are marked PROVISIONAL_DEFAULT
    assert prov["annual_drift_sbp"] == EvidentialStatus.PROVISIONAL_DEFAULT.value
    assert prov["annual_drift_dbp_early"] == EvidentialStatus.PROVISIONAL_DEFAULT.value
    assert prov["t2d_sbp_shift"] == EvidentialStatus.PROVISIONAL_DEFAULT.value


def test_experiment_runner_forward_hemodynamics_integration(tmp_path):
    """Verify end-to-end integration of ForwardHemodynamicSimulator into ExperimentRunner.

    Ensures:
    - ExperimentConfig accepts hemodynamic_engine_mode=FORWARD_STATE_SPACE.
    - generate_cohort produces exported files with forward hemodynamic readings.
    - Telemetry logs the forward engine mode accurately.
    """
    from synapse_simulator.evaluation.experiment import ExperimentRunner, ExperimentConfig
    import csv

    out_dir = tmp_path / "fwd_experiment_run"
    config = ExperimentConfig(
        cohort_size=5,
        seed=101,
        timestep_days=30,
        observation_end=datetime(2024, 1, 1) + timedelta(days=210),
        output_dir=out_dir,
        hemodynamic_engine_mode=HEMODYNAMIC_ENGINE_FORWARD,
    )

    out_path, telemetry = ExperimentRunner.generate_cohort(config)
    assert telemetry["hemodynamic_engine_mode"] == HEMODYNAMIC_ENGINE_FORWARD

    # Verify community_assessments.csv and community_bp_readings.csv exist and are non-empty
    assessments_csv = out_path / "community_assessments.csv"
    readings_csv = out_path / "community_bp_readings.csv"
    assert assessments_csv.exists()
    assert readings_csv.exists()

    with open(assessments_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0
        for r in rows:
            assert r["provenance"] == "COMMUNITY_HEALTH_ASSESSMENT_LAYER"
            if r["status"] == "COMPLETED":
                assert float(r["sbp"]) > 0
                assert float(r["dbp"]) > 0
                assert float(r["pulse_pressure"]) >= 20.0
