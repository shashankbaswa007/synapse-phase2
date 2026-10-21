"""
Unit and Integration Tests for SYNAPSE Phase 2 Evaluation Framework.
Covers:
1. Pure Python mathematical fixtures (Wilson score, JSD, Chi-square with pooling, TVD, Cramér's V, OR, O/E)
2. Denominator filtering and age restriction fidelity
3. Independent CSV evaluation without simulation runtime objects
4. Hard invariant violation detection (pre-birth, post-mortem, dangling encounter, allergy safety)
5. Empty and undersized cohort handling
6. Unverified status enforcement (no false PASS)
7. Deterministic evaluation repeatability
8. Experiment runner and manifest preservation
"""

import math
from pathlib import Path
from datetime import datetime
import csv
import json
import pytest

from synapse_simulator.evaluation.metrics import (
    wilson_score_interval,
    jensen_shannon_divergence,
    total_variation_distance,
    chi_square_goodness_of_fit,
    chi_square_p_value,
    cramers_v,
    odds_ratio_and_ci,
    comorbidity_oe_ratio,
)
from synapse_simulator.evaluation.reference_data import (
    ReferenceCatalog,
    ReferenceStatistic,
    get_default_reference_catalog,
)
from synapse_simulator.evaluation.evaluator import (
    DatasetEvaluator,
    EvaluationReport,
    MetricStatus,
    EvaluationDimension,
)
from synapse_simulator.evaluation.experiment import (
    ExperimentRunner,
    ExperimentConfig,
)
from synapse_simulator.evaluation.report import EvaluationReportFormatter


# -------------------------------------------------------------------------
# 1. Mathematical Metrics Unit Tests (Hand-Calculated Fixtures)
# -------------------------------------------------------------------------

def test_wilson_score_interval_hand_calculated():
    """Verify Wilson score confidence intervals against known closed-form statistical values."""
    # Degenerate: n <= 0
    assert wilson_score_interval(0, 0) == (0.0, 0.0)
    assert wilson_score_interval(5, -1) == (0.0, 0.0)

    # Extreme bounds: 0 of 10
    low_0, high_0 = wilson_score_interval(0, 10, confidence=0.95)
    assert low_0 == 0.0
    assert high_0 == pytest.approx(0.2775, abs=1e-3)

    # Extreme bounds: 10 of 10
    low_10, high_10 = wilson_score_interval(10, 10, confidence=0.95)
    assert low_10 == pytest.approx(0.7225, abs=1e-3)
    assert high_10 == 1.0

    # Intermediate: 50 of 100 (p = 0.50)
    # Center = 0.50, margin = 1.96 * sqrt(0.25/100 + 1.96^2 / 40000) / (1 + 1.96^2/100) ~ 0.0962
    low_50, high_50 = wilson_score_interval(50, 100, confidence=0.95)
    assert low_50 == pytest.approx(0.4038, abs=1e-3)
    assert high_50 == pytest.approx(0.5962, abs=1e-3)

    # 2 of 10
    low_2, high_2 = wilson_score_interval(2, 10, confidence=0.95)
    assert low_2 == pytest.approx(0.0567, abs=1e-3)
    assert high_2 == pytest.approx(0.5098, abs=1e-3)


def test_jensen_shannon_divergence_math():
    """Verify mathematical invariants of Jensen-Shannon Divergence (base 2)."""
    # Identical distributions must yield JSD = 0.0
    p1 = [0.2, 0.5, 0.3]
    p2 = [0.2, 0.5, 0.3]
    assert jensen_shannon_divergence(p1, p2) == 0.0

    # Orthogonal distributions must yield maximum JSD = 1.0 (with base 2 log)
    orth_1 = [1.0, 0.0]
    orth_2 = [0.0, 1.0]
    assert jensen_shannon_divergence(orth_1, orth_2) == 1.0

    # Symmetry: JSD(P, Q) == JSD(Q, P)
    dist_a = [0.1, 0.4, 0.5]
    dist_b = [0.3, 0.3, 0.4]
    jsd_ab = jensen_shannon_divergence(dist_a, dist_b)
    jsd_ba = jensen_shannon_divergence(dist_b, dist_a)
    assert jsd_ab == jsd_ba
    assert 0.0 <= jsd_ab <= 1.0

    # Unnormalized arrays should normalize automatically
    unnorm_a = [10.0, 40.0, 50.0]
    assert jensen_shannon_divergence(unnorm_a, dist_b) == jsd_ab

    # Error on mismatched length or empty
    with pytest.raises(ValueError):
        jensen_shannon_divergence([0.5, 0.5], [0.3, 0.3, 0.4])
    with pytest.raises(ValueError):
        jensen_shannon_divergence([], [])


def test_total_variation_distance_math():
    """Verify Total Variation Distance properties."""
    p = [0.6, 0.4]
    q = [0.6, 0.4]
    assert total_variation_distance(p, q) == 0.0

    # Orthogonal: TVD = 0.5 * (|1 - 0| + |0 - 1|) = 1.0
    assert total_variation_distance([1.0, 0.0], [0.0, 1.0]) == 1.0

    # Partial: [0.7, 0.3] vs [0.5, 0.5] -> 0.5 * (0.2 + 0.2) = 0.2
    assert total_variation_distance([0.7, 0.3], [0.5, 0.5]) == pytest.approx(0.2, abs=1e-5)


def test_chi_square_and_sparse_bin_pooling():
    """Verify Chi-Square goodness-of-fit calculation and automated sparse bin pooling."""
    # 1. Exact match: chi2 = 0, p = 1.0
    obs = [50.0, 50.0]
    exp = [50.0, 50.0]
    res = chi_square_goodness_of_fit(obs, exp)
    assert res["chi2_stat"] == 0.0
    assert res["df"] == 1
    assert res["p_value"] == 1.0
    assert not res["was_pooled"]

    # 2. Known chi-square value: obs=[60, 40], exp=[50, 50] -> chi2 = 4.0, df = 1
    res2 = chi_square_goodness_of_fit([60, 40], [50, 50])
    assert res2["chi2_stat"] == 4.0
    assert res2["df"] == 1
    # P(X^2 >= 4.0) with df=1 is ~0.0455
    assert res2["p_value"] == pytest.approx(0.0455, abs=1e-3)

    # 3. Sparse bin pooling: bins with E_i < 5.0 must be pooled
    obs_sparse = [30.0, 2.0, 1.0]
    exp_sparse = [30.0, 2.0, 1.0]  # last two bins sum to 3 < 5
    res_pooled = chi_square_goodness_of_fit(obs_sparse, exp_sparse, min_expected=5.0)
    assert res_pooled["was_pooled"] is True
    # Should pool last bins into first or residual
    assert len(res_pooled["pooled_expected"]) >= 1

    # 4. Cramér's V
    v = cramers_v(chi2_stat=4.0, n=100, k=2)
    # sqrt(4.0 / (100 * 1)) = sqrt(0.04) = 0.2
    assert v == pytest.approx(0.20, abs=1e-3)


def test_odds_ratio_and_comorbidity_oe():
    """Verify Odds Ratio and Observed-to-Expected ratio calculations."""
    # Independence: a=10, b=10, c=10, d=10 -> OR = (10*10)/(10*10) = 1.0
    or_val, low_ci, high_ci = odds_ratio_and_ci(10, 10, 10, 10)
    assert or_val == 1.0
    assert low_ci < 1.0 < high_ci

    # Haldane-Anscombe zero-cell correction: a=0 -> (+0.5 to all cells)
    or_zero, _, _ = odds_ratio_and_ci(0, 10, 10, 10)
    assert or_zero > 0.0

    # Comorbidity O/E:
    # P(A) = 0.20, P(B) = 0.30 -> Expected P(A and B) = 0.06
    # Observed P(A and B) = 0.12 -> O/E = 0.12 / 0.06 = 2.0
    oe = comorbidity_oe_ratio(p_joint=0.12, p_a=0.20, p_b=0.30)
    assert oe == 2.0

    # Degenerate
    assert comorbidity_oe_ratio(0.0, 0.0, 0.30) is None


# -------------------------------------------------------------------------
# 2. Reference Catalog and Denominator Verification
# -------------------------------------------------------------------------

def test_reference_catalog_metadata_and_denominators():
    """Verify reference catalog enforces proper eligibility constraints and provenance."""
    catalog = get_default_reference_catalog()

    # Demographics
    sex_stat = catalog.get_statistic("demo_sex_male")
    assert sex_stat is not None
    assert sex_stat.eligible_min_age == 0
    assert sex_stat.denominator_definition == "total_patients"
    assert catalog.is_verified("demo_sex_male") is True

    # Chronic conditions MUST require adult denominator (age >= 20)
    htn_stat = catalog.get_statistic("prev_htn_adults")
    assert htn_stat is not None
    assert htn_stat.eligible_min_age == 20
    assert htn_stat.denominator_definition == "adults_gte_20"
    assert htn_stat.reference_value == 30.7
    assert catalog.is_verified("prev_htn_adults") is True

    t2d_stat = catalog.get_statistic("prev_t2d_adults")
    assert t2d_stat is not None
    assert t2d_stat.eligible_min_age == 20
    assert t2d_stat.denominator_definition == "adults_gte_20"
    assert t2d_stat.reference_value == 11.4
    assert catalog.is_verified("prev_t2d_adults") is True

    # Acute URTI covers all ages
    urti_stat = catalog.get_statistic("prev_urti_all")
    assert urti_stat is not None
    assert urti_stat.eligible_min_age == 0
    assert urti_stat.denominator_definition == "total_patients"


# -------------------------------------------------------------------------
# 3. Independent CSV Evaluation & Invariant Tests
# -------------------------------------------------------------------------

def _write_mock_csv(filepath: Path, headers: list, rows: list):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def test_independent_evaluator_on_clean_mock_csv(tmp_path):
    """Verify DatasetEvaluator operates cleanly on raw CSV files without simulation objects."""
    ds_dir = tmp_path / "mock_clean_dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)

    # 1. patients.csv: 10 patients matching 5 census age bands (2, 2, 3, 2, 1) and alternating sex
    mock_ages = [8, 12, 18, 22, 30, 35, 40, 50, 55, 70]
    mock_sexes = ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"]
    patient_rows = [
        [f"pat-{i}", f"Patient {i}", mock_ages[i], mock_sexes[i], "O+", "General", "Active"]
        for i in range(10)
    ]
    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        patient_rows,
    )

    # 2. encounters.csv
    enc_rows = [
        [f"enc-{i}", f"pat-{i}", f"j-{i}", "doc-01", "2024-06-01T10:00:00", "2024-06-01T10:30:00", "Closed", "Checkup"]
        for i in range(10)
    ]
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        enc_rows,
    )

    # 3. conditions.csv: 2 of the 7 adults with HTN (28.57%), 7 of 10 with URTI (70.0%)
    # 2 adults with HTN out of 7 adults = 28.57% (ref: 30.7%, diff: -2.13% -> PASS)
    cond_rows = [
        ["c-1", "pat-4", "enc-4", "I10", "Hypertension", "Active"],
        ["c-2", "pat-5", "enc-5", "I10", "Hypertension", "Active"],
        ["c-3", "pat-1", "enc-1", "J06.9", "Acute URTI", "Resolved"],
        ["c-4", "pat-2", "enc-2", "J06.9", "Acute URTI", "Resolved"],
        ["c-5", "pat-3", "enc-3", "J06.9", "Acute URTI", "Resolved"],
        ["c-6", "pat-6", "enc-6", "J06.9", "Acute URTI", "Resolved"],
        ["c-7", "pat-7", "enc-7", "J06.9", "Acute URTI", "Resolved"],
        ["c-8", "pat-8", "enc-8", "J06.9", "Acute URTI", "Resolved"],
        ["c-9", "pat-9", "enc-9", "J06.9", "Acute URTI", "Active"],
    ]
    _write_mock_csv(
        ds_dir / "conditions.csv",
        ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
        cond_rows,
    )

    # 4. medications.csv: Amlodipine prescribed for both HTN cases
    med_rows = [
        ["m-1", "pat-4", "enc-4", "c-1", "Amlodipine", "CCB", "5mg", "OD", "pubmed", "123", "Dispensed"],
        ["m-2", "pat-5", "enc-5", "c-2", "Amlodipine", "CCB", "5mg", "OD", "pubmed", "123", "Dispensed"],
    ]
    _write_mock_csv(
        ds_dir / "medications.csv",
        ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"],
        med_rows,
    )

    _write_mock_csv(ds_dir / "deaths.csv", ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"], [])

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    assert report.invariants_passed is True
    assert report.total_metrics >= 10
    assert report.failed_metrics == 0

    # HTN prevalence should be 28.57% (2 of 7 adults), absolute diff = |28.57 - 30.7| = 2.13% -> PASS
    htn_m = next(m for m in report.metrics if m.metric_id == "prev_hypertension_adults")
    assert htn_m.synthetic_estimate == 28.57
    assert htn_m.status == MetricStatus.PASS
    assert htn_m.verification_status == "VERIFIED"


def test_evaluator_detects_post_mortem_violation(tmp_path):
    """Verify that clinical activity after patient death causes hard Invariant FAIL."""
    ds_dir = tmp_path / "mock_post_mortem_fail"
    ds_dir.mkdir(parents=True, exist_ok=True)

    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [["pat-dead", "John Doe", 70, "Male", "O+", "General", "Deceased"]],
    )

    # Encounter occurs on 2024-07-01
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [["enc-post", "pat-dead", "j-1", "doc-1", "2024-07-01T10:00:00", "2024-07-01T10:30:00", "Closed", "Checkup"]],
    )

    # Patient died on 2024-05-01 (Encounter is 2 months post-mortem!)
    _write_mock_csv(
        ds_dir / "deaths.csv",
        ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"],
        [["d-1", "pat-dead", "2024-05-01T00:00:00", "I21.9", "MI", "False"]],
    )

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    assert report.invariants_passed is False
    assert report.overall_status == MetricStatus.FAIL
    inv_post = next(m for m in report.metrics if m.metric_id == "inv_no_event_post_mortem")
    assert inv_post.status == MetricStatus.FAIL
    assert inv_post.synthetic_estimate == 1.0


def test_evaluator_detects_allergy_contraindication(tmp_path):
    """Verify that prescribing a contraindicated drug causes Clinical Safety FAIL."""
    ds_dir = tmp_path / "mock_allergy_fail"
    ds_dir.mkdir(parents=True, exist_ok=True)

    # Patient has documented Penicillin allergy
    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status", "allergies"],
        [["pat-allergic", "Jane Smith", 28, "Female", "A+", "Private", "Active", "Penicillin"]],
    )
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [["enc-1", "pat-allergic", "j-1", "doc-1", "2024-03-01T09:00:00", "2024-03-01T09:20:00", "Closed", "URTI"]],
    )
    _write_mock_csv(
        ds_dir / "conditions.csv",
        ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
        [["c-1", "pat-allergic", "enc-1", "J06.9", "URTI", "Active"]],
    )
    # Prescribing Amoxicillin to Penicillin-allergic patient
    _write_mock_csv(
        ds_dir / "medications.csv",
        ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"],
        [["m-1", "pat-allergic", "enc-1", "c-1", "Amoxicillin", "Beta-Lactam", "500mg", "TDS", "pubmed", "31234513", "Dispensed"]],
    )

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    assert report.invariants_passed is False
    assert report.overall_status == MetricStatus.FAIL
    inv_alg = next(m for m in report.metrics if m.metric_id == "inv_allergy_safety_veto")
    assert inv_alg.status == MetricStatus.FAIL
    assert inv_alg.synthetic_estimate == 1.0


def test_evaluator_denominator_isolation(tmp_path):
    """Verify that pediatric patients are excluded from adult-only disease denominators."""
    ds_dir = tmp_path / "mock_pediatric_isolation"
    ds_dir.mkdir(parents=True, exist_ok=True)

    # 5 pediatric patients (age 8) and 5 adults (age 40)
    patients = [
        [f"pat-kid-{i}", f"Kid {i}", 8, "Male", "O+", "General", "Active"]
        for i in range(5)
    ] + [
        [f"pat-adult-{i}", f"Adult {i}", 40, "Female", "B+", "General", "Active"]
        for i in range(5)
    ]
    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        patients,
    )

    # 1 adult has T2D
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [["enc-1", "pat-adult-0", "j-1", "doc-1", "2024-02-01T10:00:00", "2024-02-01T10:30:00", "Closed", "Checkup"]],
    )
    _write_mock_csv(
        ds_dir / "conditions.csv",
        ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
        [["c-1", "pat-adult-0", "enc-1", "E11.9", "Type 2 Diabetes", "Active"]],
    )

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    t2d_m = next(m for m in report.metrics if m.metric_id == "prev_diabetes_t2_adults")
    # Denominator must be 5 (only adults >= 20), NOT 10!
    assert t2d_m.denominator == 5
    assert t2d_m.numerator == 1
    assert t2d_m.synthetic_estimate == 20.0  # 1/5 = 20%


def test_evaluator_unverified_metrics_cannot_pass(tmp_path):
    """Verify that assumptions and unbenchmarked metrics receive status UNVERIFIED, never PASS."""
    ds_dir = tmp_path / "mock_unverified"
    ds_dir.mkdir(parents=True, exist_ok=True)

    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [["pat-1", "John", 45, "Male", "O+", "General", "Active"]],
    )

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    adh_m = next(m for m in report.metrics if m.metric_id == "rx_adherence_assumption")
    assert adh_m.status == MetricStatus.UNVERIFIED
    assert adh_m.verification_status == "UNVERIFIED"


def test_evaluator_empty_and_single_patient(tmp_path):
    """Verify evaluator handles empty and N=1 cohorts gracefully without unhandled exceptions."""
    # Empty dir
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    evaluator_empty = DatasetEvaluator(dataset_dir=empty_dir)
    report_empty = evaluator_empty.evaluate_all()
    assert report_empty.total_metrics >= 0

    # Single patient
    single_dir = tmp_path / "single_dir"
    single_dir.mkdir()
    _write_mock_csv(
        single_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [["pat-single", "Single Patient", 50, "Female", "AB+", "Corporate", "Active"]],
    )
    evaluator_single = DatasetEvaluator(dataset_dir=single_dir)
    report_single = evaluator_single.evaluate_all()
    assert report_single.total_metrics > 0
    assert report_single.invariants_passed is True


# -------------------------------------------------------------------------
# 4. Repeatability & Manifest Preservation
# -------------------------------------------------------------------------

def test_experiment_runner_manifest_generation(tmp_path):
    """Verify that running an experiment produces deterministic output and RUN_MANIFEST.json."""
    exp_dir = tmp_path / "test_exp_run"
    config = ExperimentConfig(
        cohort_size=5,
        seed=777,
        output_dir=exp_dir,
    )
    res = ExperimentRunner.run_experiment(config)

    assert (exp_dir / "RUN_MANIFEST.json").exists()
    assert (exp_dir / "EVALUATION_REPORT.json").exists()
    assert (exp_dir / "EVALUATION_REPORT.md").exists()

    with open(exp_dir / "RUN_MANIFEST.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["configuration"]["seed"] == 777
    assert manifest["configuration"]["cohort_size"] == 5
    assert "evaluation_seconds" in manifest["performance_telemetry"]
    assert "overall_status" in manifest["evaluation_verdict"]


# -------------------------------------------------------------------------
# 5. Methodological & Epidemiological Invariant Tests
# -------------------------------------------------------------------------

def test_baseline_prevalence_vs_incident_disease_separation():
    """Verify that baseline-positive patients have pre-observation onset and never duplicate onset."""
    from synapse_simulator.modules.engine import ClinicalModuleRunner
    from synapse_simulator.modules.loader import load_clinical_module
    from synapse_simulator.datagen.models import PatientContext
    from datetime import timedelta

    htn_module = load_clinical_module(Path(__file__).parent.parent / "config" / "modules" / "hypertension.yaml")
    runner = ClinicalModuleRunner([htn_module], base_seed=42)

    # 1. Baseline-positive patient
    past_onset = datetime(2024, 6, 15, 10, 0, 0)
    p_baseline = PatientContext(
        patient_id="pat-baseline-htn",
        name="Baseline Hypertensive",
        age=55,
        gender="Male",
        chronic_conditions=["Essential (primary) hypertension"],
        baseline_conditions={
            "I10": {
                "condition_code": "I10",
                "condition_name": "Essential (primary) hypertension",
                "onset_date": past_onset,
                "is_baseline": True,
                "status": "Active",
            }
        },
    )

    runner.initialize_patient(p_baseline)
    # Must route to ScreeningEncounter, bypassing Initial / AgeCheck / HypertensionOnset
    assert runner.patient_module_states[p_baseline.patient_id]["mod-htn-01"] == "ScreeningEncounter"
    assert "I10" in p_baseline.latent_conditions
    assert p_baseline.latent_conditions["I10"]["is_baseline"] is True
    assert p_baseline.latent_conditions["I10"]["onset_time"] == past_onset

    # Step patient through baseline screening encounter
    obs_start = datetime(2026, 1, 1, 0, 0, 0)
    emitted = runner.step_patient(p_baseline, current_time=obs_start, timestep=timedelta(days=7))

    # Condition is diagnosed and prescribed, but onset transition was never fired during simulation
    diag_acts = [a for a in emitted if a.action_type == "CONSULTATION_DIAGNOSE"]
    assert len(diag_acts) == 1
    assert diag_acts[0].payload["condition_code"] == "I10"
    assert diag_acts[0].payload["is_baseline"] is True

    # Step patient forward 2 years: patient stays in maintenance delay and NEVER re-enters HypertensionOnset
    curr = obs_start + timedelta(days=7)
    for _ in range(104):
        step_acts = runner.step_patient(p_baseline, current_time=curr, timestep=timedelta(days=7))
        # Ensure no second onset diagnosis action is ever emitted
        second_diag = [a for a in step_acts if a.action_type == "CONSULTATION_DIAGNOSE"]
        assert len(second_diag) == 0
        curr += timedelta(days=7)


def test_timestep_dependent_incidence_probability_conversion():
    """Verify discrete transition probability conversion from annual hazard p(dt) = 1 - exp(-lambda * dt)."""
    # 1. Hypertension annual hazard: lambda = 0.035 / year
    lambda_htn = 0.035
    # dt = 1.0 year (365 days): p = 1 - exp(-0.035 * 1.0) = 0.034397...
    p_1yr = 1.0 - math.exp(-lambda_htn * 1.0)
    assert round(p_1yr, 4) == 0.0344

    # dt = 0.5 year (182.5 days): p = 1 - exp(-0.035 * 0.5) = 0.017348...
    p_half_yr = 1.0 - math.exp(-lambda_htn * 0.5)
    assert round(p_half_yr, 4) == 0.0173

    # Compound rule check: (1 - p_half_yr)^2 must equal (1 - p_1yr)
    assert math.isclose((1.0 - p_half_yr) ** 2, 1.0 - p_1yr, rel_tol=1e-6)

    # 2. Type 2 Diabetes annual hazard: lambda = 0.015 / year
    lambda_t2d = 0.015
    p_t2d_1yr = 1.0 - math.exp(-lambda_t2d * 1.0)
    assert round(p_t2d_1yr, 4) == 0.0149


def test_point_prevalence_vs_cumulative_attack_rate_distinction(tmp_path):
    """Verify DatasetEvaluator rigorously separates acute point prevalence from cumulative attack rate."""
    ds_dir = tmp_path / "acute_evaluation_test"
    ds_dir.mkdir(parents=True, exist_ok=True)

    # 10 patients
    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [[f"pat-{i}", f"Patient {i}", 30, "Male", "O+", "General", "Active"] for i in range(10)],
    )

    # 10 encounters across 2 years
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [[f"enc-{i}", f"pat-{i}", f"j-{i}", "doc-01", f"2026-0{i+1}-01T10:00:00", f"2026-0{i+1}-01T10:30:00", "Closed", "Cough"] for i in range(10)],
    )

    # 7 patients had URTI, but 6 of them resolved months ago; only 1 is currently Active
    cond_rows = [
        [f"c-{i}", f"pat-{i}", f"enc-{i}", "J06.9", "Acute URTI", "Resolved"] for i in range(6)
    ]
    cond_rows.append(["c-6", "pat-6", "enc-6", "J06.9", "Acute URTI", "Active"])
    _write_mock_csv(
        ds_dir / "conditions.csv",
        ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
        cond_rows,
    )

    _write_mock_csv(
        ds_dir / "medications.csv",
        ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"],
        [[f"m-{i}", f"pat-{i}", f"enc-{i}", f"c-{i}", "Amoxicillin", "Beta-Lactam", "500mg", "TID", "pubmed", "123", "Dispensed"] for i in range(7)],
    )
    _write_mock_csv(ds_dir / "deaths.csv", ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"], [])

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    # Active point prevalence should be exactly 1 out of 10 = 10.0%
    point_m = next(m for m in report.metrics if m.metric_id == "prev_urti_14day_point")
    assert point_m.synthetic_estimate == 10.0
    assert point_m.numerator == 1

    # Cumulative attack rate should be 7 out of 10 = 70.0%
    cum_m = next(m for m in report.metrics if m.metric_id == "prev_urti_cumulative_attack_rate")
    assert cum_m.synthetic_estimate == 70.0
    assert cum_m.numerator == 7


def test_held_out_data_isolation():
    """Verify that internal subgroup holdouts and independent evaluation statistics have strict role tags."""
    from synapse_simulator.evaluation.reference_data import BenchmarkRole

    catalog = get_default_reference_catalog()

    # Subgroup targets are derived from ICMR-INDIAB and must NOT be labeled external independent validation
    stat_male = catalog.get_statistic("prev_t2d_male_subgroup")
    assert stat_male is not None
    assert stat_male.role == BenchmarkRole.INTERNAL_VALIDATION_HOLDOUT

    stat_female = catalog.get_statistic("prev_t2d_female_subgroup")
    assert stat_female is not None
    assert stat_female.role == BenchmarkRole.INTERNAL_VALIDATION_HOLDOUT

    # Census SRS demographics is external independent evaluation
    stat_demo = catalog.get_statistic("demo_age_pyramid")
    assert stat_demo is not None
    assert stat_demo.role == BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION


def test_baseline_vs_period_prevalence_breakdown(tmp_path):
    """Verify that DatasetEvaluator properly isolates baseline point cases from cumulative period cases."""
    ds_dir = tmp_path / "baseline_period_test"
    ds_dir.mkdir(parents=True, exist_ok=True)

    # 10 adult patients
    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [[f"pat-{i}", f"Patient {i}", 40, "Male", "O+", "Cash", "Active"] for i in range(10)],
    )

    # 4 encounters: 2 at baseline (day 5), 2 incident (day 180)
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [
            ["enc-0", "pat-0", "j-0", "doc-1", "2024-01-05T10:00:00", "2024-01-05T10:20:00", "Closed", "Baseline"],
            ["enc-1", "pat-1", "j-1", "doc-1", "2024-01-05T10:00:00", "2024-01-05T10:20:00", "Closed", "Baseline"],
            ["enc-2", "pat-2", "j-2", "doc-1", "2024-07-01T10:00:00", "2024-07-01T10:20:00", "Closed", "Incident"],
            ["enc-3", "pat-3", "j-3", "doc-1", "2024-07-01T10:00:00", "2024-07-01T10:20:00", "Closed", "Incident"],
        ],
    )

    # 4 HTN condition records: 2 baseline, 2 incident
    _write_mock_csv(
        ds_dir / "conditions.csv",
        ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
        [
            ["c-0", "pat-0", "enc-0", "I10", "Hypertension", "Active"],
            ["c-1", "pat-1", "enc-1", "I10", "Hypertension", "Active"],
            ["c-2", "pat-2", "enc-2", "I10", "Hypertension", "Active"],
            ["c-3", "pat-3", "enc-3", "I10", "Hypertension", "Active"],
        ],
    )

    _write_mock_csv(
        ds_dir / "medications.csv",
        ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"],
        [[f"m-{i}", f"pat-{i}", f"enc-{i}", f"c-{i}", "Amlodipine", "CCB", "5mg", "Daily", "guideline", "", "Dispensed"] for i in range(4)],
    )
    _write_mock_csv(ds_dir / "deaths.csv", ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"], [])

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    htn_m = next(m for m in report.metrics if m.metric_id == "prev_hypertension_adults")
    # Cumulative period prevalence = 4 / 10 = 40.0%
    assert htn_m.synthetic_estimate == 40.0
    assert htn_m.numerator == 4
    # Baseline point cases isolated in threshold dictionary = 2 / 10 = 20.0%
    assert htn_m.acceptance_threshold["baseline_point_cases"] == 2
    assert htn_m.acceptance_threshold["baseline_point_prevalence_pct"] == 20.0
    assert htn_m.acceptance_threshold["incident_cases"] == 2
    assert htn_m.acceptance_threshold["incident_attack_rate_pct"] == 20.0


def test_background_life_table_mortality_and_invariants(tmp_path):
    """Verify that background life-table mortality generates plausible deaths and maintains invariant gates."""
    exp_dir = tmp_path / "exp_mortality_test"
    config = ExperimentConfig(
        cohort_size=50,
        seed=42,
        output_dir=exp_dir,
        enable_background_mortality=True,
    )
    res = ExperimentRunner.run_experiment(config)
    report = res["report"]

    # Invariants must strictly pass with zero violations
    assert report.invariants_passed is True
    post_mort_m = next(m for m in report.metrics if m.metric_id == "inv_no_event_post_mortem")
    assert post_mort_m.status == MetricStatus.PASS
    assert post_mort_m.numerator == 0

    # Verify deaths.csv is generated and contains valid headers
    deaths_csv = exp_dir / "deaths.csv"
    assert deaths_csv.exists()


def test_treatment_rule_conformance_labeling(tmp_path):
    """Verify that pharmacotherapy metrics are formally labeled as rule conformance rather than real-world fidelity."""
    ds_dir = tmp_path / "rx_label_test"
    ds_dir.mkdir(parents=True, exist_ok=True)

    _write_mock_csv(
        ds_dir / "patients.csv",
        ["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"],
        [["pat-1", "Patient 1", 50, "Male", "O+", "Cash", "Active"]],
    )
    _write_mock_csv(
        ds_dir / "encounters.csv",
        ["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"],
        [["enc-1", "pat-1", "j-1", "doc-1", "2024-01-05T10:00:00", "2024-01-05T10:20:00", "Closed", "Routine"]],
    )
    _write_mock_csv(
        ds_dir / "conditions.csv",
        ["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"],
        [["c-1", "pat-1", "enc-1", "I10", "Hypertension", "Active"]],
    )
    _write_mock_csv(
        ds_dir / "medications.csv",
        ["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"],
        [["m-1", "pat-1", "enc-1", "c-1", "Amlodipine", "CCB", "5mg", "Daily", "guideline", "", "Dispensed"]],
    )
    _write_mock_csv(ds_dir / "deaths.csv", ["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"], [])

    evaluator = DatasetEvaluator(dataset_dir=ds_dir)
    report = evaluator.evaluate_all()

    rx_htn = next(m for m in report.metrics if m.metric_id == "rx_firstline_hypertension")
    assert "Rule Conformance" in rx_htn.metric_name
    assert "real-world" in rx_htn.known_limitations

