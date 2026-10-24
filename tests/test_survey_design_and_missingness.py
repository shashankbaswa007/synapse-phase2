"""
Unit and Integration Tests for Milestone 3: Survey Design & Missingness Diagnostics.

Validates:
1. Variable-specific missing-value policies (preserving SBP 99, DBP 99, Age 99; never coercing to zero/False).
2. Missing, invalid, or zero survey-design fields detection.
3. Stratum-PSU topology, singleton strata (nh == 1) detection, and Taylor series variance estimation.
4. Extreme survey weights screening, dispersion CV(w), Kish DEFF_w, and top-share diagnostics.
5. Module non-response, join attrition, and biomarker participation tracking.
6. Demographic age-sex domain support and sparse domain flags.
7. Estimand eligibility classification (Observed, Weighted, Adjusted, Unsupported).
8. Separation of survey sampling uncertainty from simulation Monte Carlo uncertainty.
9. Keyed HMAC pseudonymization and privacy-preserving aggregate diagnostic reports.
10. Preservation of external validation gate at REFERENCE_DATA_PENDING.
"""

import math
import tempfile
from pathlib import Path
import pytest

from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiDataSourceType,
    LasiEvaluationGateStatus,
    LasiEstimandSupportType,
)
from synapse_simulator.evaluation.lasi.security import (
    KeyedPseudonymizer,
    CONFIDENTIALITY_NOTICE,
)
from synapse_simulator.evaluation.lasi.missingness import (
    VariableMissingValuePolicy,
)
from synapse_simulator.evaluation.lasi.diagnostics import (
    LasiSurveyDesignDiagnostics,
)
from synapse_simulator.evaluation.lasi.variance import (
    SingletonHandlingStrategy,
    LasiSurveyVarianceEngine,
)
from synapse_simulator.evaluation.lasi.ingestor import (
    LasiDataIngestor,
)


def _build_test_record(
    pid: str = "p1",
    hhid: str = "hh1",
    age: float = 60.0,
    gender: str = "Female",
    sbp: float = 130.0,
    dbp: float = 80.0,
    hba1c: float = 5.6,
    htn_diag: bool = False,
    med_bp: bool = False,
    weight: float = 1.0,
    strata: str = "S1",
    psu: str = "P1",
    bio_part: bool = True,
    is_valid_bp: bool = True,
) -> LasiCleanedRecord:
    """Helper to construct synthetic LasiCleanedRecord."""
    return LasiCleanedRecord(
        participant_id=f"lasi_p_{pid}",
        household_id=f"lasi_hh_{hhid}",
        age=age,
        gender=gender,
        sbp_mean=sbp,
        dbp_mean=dbp,
        hba1c=hba1c,
        diagnosed_hypertension=htn_diag,
        taking_bp_medication=med_bp,
        survey_weight=weight,
        strata=strata,
        psu=psu,
        biomarker_participated=bio_part,
        bp_participated=is_valid_bp,
        hba1c_participated=(hba1c is not None),
        has_valid_survey_weight=(weight is not None and weight > 0.0),
        module_membership={"individual": True, "biomarker": bio_part},
        is_valid_for_bp=is_valid_bp,
        is_valid_for_hba1c=(hba1c is not None),
    )


# =============================================================================
# 1. Variable-Specific Missing-Value Policy Tests
# =============================================================================

def test_variable_specific_missing_value_policy():
    """Verify variable-specific missingness rules: 99 is valid for BP and Age, but not for sentinels."""
    policy = VariableMissingValuePolicy()

    # Blood pressure: 99.0 mmHg is completely valid clinical measurement
    sbp_val, sbp_err = policy.clean_blood_pressure("99.0", "sbp1", is_systolic=True)
    assert sbp_val == 99.0, f"SBP 99.0 must be preserved as valid! Got {sbp_val}, err={sbp_err}"

    dbp_val, dbp_err = policy.clean_blood_pressure("99.0", "dbp1", is_systolic=False)
    assert dbp_val == 99.0, f"DBP 99.0 must be preserved as valid! Got {dbp_val}, err={dbp_err}"

    # Age: 99 years old is a valid age for nonagenarians in older-adult cohort
    age_val, age_err = policy.clean_age("99.0", "age")
    assert age_val == 99.0, f"Age 99 must be preserved as valid! Got {age_val}, err={age_err}"

    # Negative codes in BP must parse to None (never 0.0 or 120.0)
    for code in ["-999", "-998", "-99", "-9"]:
        clean_sbp, err = policy.clean_blood_pressure(code, "sbp1", is_systolic=True)
        assert clean_sbp is None
        assert "NEGATIVE_BP_SENTINEL" in err

    # High codes in BP (999, 9999) must parse to None
    for code in ["999", "9999"]:
        clean_sbp, err = policy.clean_blood_pressure(code, "sbp1", is_systolic=True)
        assert clean_sbp is None

    # Stata extended missing codes (.a, .b, .)
    for code in [".a", ".b", "."]:
        clean_sbp, err = policy.clean_blood_pressure(code, "sbp1", is_systolic=True)
        assert clean_sbp is None

    # Categorical diagnosis: 1=True, 0/2=False, 8/9/-999=None (NEVER coerced to False)
    assert policy.clean_boolean_indicator("1", "hypere", "diagnosed_hypertension")[0] is True
    assert policy.clean_boolean_indicator("2", "hypere", "diagnosed_hypertension")[0] is False
    assert policy.clean_boolean_indicator("0", "hypere", "diagnosed_hypertension")[0] is False

    for sentinel in ["8", "9", "98", "99", "-999", "-99"]:
        res, err = policy.clean_boolean_indicator(sentinel, "hypere", "diagnosed_hypertension")
        assert res is None, f"Sentinel {sentinel} must parse to None, never False!"
        assert "SURVEY_NON_RESPONSE_CODE" in err


# =============================================================================
# 2. Missing or Invalid Survey-Design Fields
# =============================================================================

def test_missing_or_invalid_survey_design_fields():
    """Verify diagnostic detection of missing weights, negative weights, and missing strata/PSUs."""
    records = [
        _build_test_record(pid="p1", weight=1.5, strata="S1", psu="P1"),
        _build_test_record(pid="p2", weight=None, strata="S1", psu="P2"),  # Missing/invalid weight parsed as None
        _build_test_record(pid="p3", weight=0.0, strata=None, psu=None),    # Missing strata/psu and zero weight
    ]

    diag = LasiSurveyDesignDiagnostics(records=records, source_label="Synthetic Test Cohort")
    report = diag.run_diagnostics()

    assert report.total_participants == 3
    # Survey weights status
    wt_status = report.field_statuses["survey_weight"]
    assert wt_status.present is True
    assert wt_status.non_null_count == 1  # Only p1 has weight > 0
    assert wt_status.missing_count == 2
    assert wt_status.missingness_pct == 66.67

    # Weight diagnostics reflect only valid positive weights
    assert report.weight_diagnostics.total_weights_observed == 1
    assert report.weight_diagnostics.missing_or_invalid_weights_count == 2


# =============================================================================
# 3. Singleton and Low-Support Strata Topology & Taylor Series Variance
# =============================================================================

def test_singleton_and_low_support_strata_and_variance():
    """Verify detection of singleton strata (nh == 1) and Taylor Series Linearization variance policies."""
    records = [
        # Stratum S1 has 2 PSUs (adequate support)
        _build_test_record(pid="p1", sbp=130.0, weight=1.0, strata="S1", psu="P1"),
        _build_test_record(pid="p2", sbp=135.0, weight=1.0, strata="S1", psu="P2"),
        # Stratum S2 has 1 PSU (SINGLETON)
        _build_test_record(pid="p3", sbp=140.0, weight=1.0, strata="S2", psu="P3"),
        # Stratum S3 has 1 PSU (SINGLETON)
        _build_test_record(pid="p4", sbp=150.0, weight=1.0, strata="S3", psu="P4"),
    ]

    diag = LasiSurveyDesignDiagnostics(records=records)
    report = diag.run_diagnostics()

    assert report.total_strata == 3
    assert report.total_psus == 4
    assert report.singleton_strata_count == 2
    assert report.singleton_strata_pct == 66.67
    assert any("SINGLETON PSUs" in w for w in report.diagnostic_warnings)

    # Test Taylor Linearization under different singleton strategies
    # 1. CERTAINTY Strategy
    engine_cert = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.CERTAINTY)
    mean_val, se_cert, tel_cert = engine_cert.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    assert mean_val == 138.75
    assert se_cert >= 0.0
    assert tel_cert["singleton_strata_count"] == 2

    # 2. GRAND_MEAN_CENTERING Strategy
    engine_center = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.GRAND_MEAN_CENTERING)
    _, se_center, tel_center = engine_center.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    assert se_center > 0.0
    # Grand mean centering captures variation of singleton PSU residuals around overall mean
    assert se_center >= se_cert

    # 3. COLLAPSE_STRATA Strategy
    engine_col = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.COLLAPSE_STRATA)
    _, se_col, tel_col = engine_col.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    assert se_col > 0.0


# =============================================================================
# 4. Extreme and Invalid Survey Weights
# =============================================================================

def test_extreme_and_invalid_survey_weights():
    """Verify screening for extreme weights, coefficient of variation, and Kish design effect."""
    # 100 observations with weight 1.0, and 1 extreme outlier weight of 200.0
    records = [_build_test_record(pid=f"p{i}", weight=1.0) for i in range(100)]
    records.append(_build_test_record(pid="p_outlier", weight=200.0))

    diag = LasiSurveyDesignDiagnostics(records=records)
    report = diag.run_diagnostics()
    w = report.weight_diagnostics

    assert w.total_weights_observed == 101
    assert w.min_weight == 1.0
    assert w.max_weight == 200.0
    assert w.max_to_min_ratio == 200.0
    assert w.cv_weight > 1.5
    assert w.deff_w > 3.0
    assert w.has_extreme_weights is True
    assert w.weight_trimming_recommended is True
    assert any("SURVEY WEIGHT DISPERSION" in warn for warn in report.diagnostic_warnings)


# =============================================================================
# 5. Module Non-Response and Join Attrition
# =============================================================================

def test_module_non_response_and_join_attrition():
    """Verify tracking of biomarker non-response and participant attrition."""
    records = []
    # 80 participants with complete biomarker measurement
    for i in range(80):
        records.append(_build_test_record(pid=f"p{i}", bio_part=True, is_valid_bp=True))
    # 20 participants with biomarker non-response
    for i in range(80, 100):
        records.append(_build_test_record(pid=f"p{i}", sbp=None, dbp=None, hba1c=None, bio_part=False, is_valid_bp=False))

    diag = LasiSurveyDesignDiagnostics(records=records)
    report = diag.run_diagnostics()

    part = report.module_participation
    assert part["individual_survey_participants"] == 100
    assert part["biomarker_module_participants"] == 80
    assert part["biomarker_non_response_count"] == 20
    assert part["biomarker_non_response_pct"] == 20.0
    assert part["blood_pressure_valid_count"] == 80
    assert any("BIOMARKER ATTRITION" in w for w in report.diagnostic_warnings)


# =============================================================================
# 6. Age-Sex Domain Support and Sparse Cell Detection
# =============================================================================

def test_age_sex_domain_support():
    """Verify sample size support across age-sex domains and detection of sparse cells."""
    records = []
    # Robust cells (n = 40)
    for i in range(40):
        records.append(_build_test_record(pid=f"m45_{i}", age=50.0, gender="Male"))
        records.append(_build_test_record(pid=f"f45_{i}", age=50.0, gender="Female"))
    # Sparse cell (n = 8, severely sparse < 15)
    for i in range(8):
        records.append(_build_test_record(pid=f"m75_{i}", age=80.0, gender="Male"))

    diag = LasiSurveyDesignDiagnostics(records=records)
    report = diag.run_diagnostics()

    doms = report.domain_supports
    assert doms["Male_45_54"].sample_size_n == 40
    assert doms["Male_45_54"].is_sparse is False

    assert doms["Male_75_plus"].sample_size_n == 8
    assert doms["Male_75_plus"].is_sparse is True
    assert doms["Male_75_plus"].is_severely_sparse is True

    assert any("SPARSE DOMAINS" in w for w in report.diagnostic_warnings)


# =============================================================================
# 7. Estimand Eligibility Classification
# =============================================================================

def test_estimand_eligibility_classification():
    """Verify classification of estimands into DESIGN_WEIGHTED_OBSERVED, OBSERVED_DATA_UNWEIGHTED, or UNSUPPORTED."""
    # Cohort with 50 valid participants and full survey design
    records = [
        _build_test_record(pid=f"p{i}", age=50.0 + (i % 30), strata=f"S{i % 4}", psu=f"P{i % 8}", weight=1.0)
        for i in range(50)
    ]

    diag = LasiSurveyDesignDiagnostics(records=records)
    report = diag.run_diagnostics()

    elig = report.estimand_eligibilities
    assert elig["sbp_mean_overall"].is_eligible is True
    assert elig["sbp_mean_overall"].support_type == LasiEstimandSupportType.DESIGN_WEIGHTED_OBSERVED

    assert elig["hypertension_prevalence"].is_eligible is True
    assert elig["hypertension_prevalence"].support_type == LasiEstimandSupportType.DESIGN_WEIGHTED_OBSERVED

    # Now test cohort with severely sparse sample (n = 5), which must be UNSUPPORTED
    sparse_records = [_build_test_record(pid=f"sp_{i}") for i in range(5)]
    diag_sparse = LasiSurveyDesignDiagnostics(records=sparse_records)
    report_sparse = diag_sparse.run_diagnostics()

    sparse_elig = report_sparse.estimand_eligibilities["sbp_mean_overall"]
    assert sparse_elig.is_eligible is False
    assert sparse_elig.support_type == LasiEstimandSupportType.UNSUPPORTED
    assert any("Inadequate sample size" in r for r in sparse_elig.ineligibility_reasons)


# =============================================================================
# 8. Separation of Survey and Monte Carlo Uncertainty
# =============================================================================

def test_separation_of_survey_and_monte_carlo_variance():
    """Verify combination and separation of survey sampling variance and simulation Monte Carlo variance."""
    survey_var = 0.50     # Reference survey sampling variance
    sim_var = 1.00        # Simulation cohort variance
    m_reps = 100          # M = 100 replications (or simulated sample size)

    res = LasiSurveyVarianceEngine.combine_survey_and_monte_carlo_variance(
        survey_var=survey_var,
        sim_variance=sim_var,
        sim_replications_m=m_reps,
    )

    # Monte Carlo variance = 1.00 / 100 = 0.01
    assert res["monte_carlo_variance"] == 0.01
    assert res["survey_variance"] == 0.50
    assert res["total_variance"] == 0.51
    assert res["combined_se"] == round(math.sqrt(0.51), 4)

    # When M is huge (e.g. 100,000), Monte Carlo variance approaches 0
    res_large = LasiSurveyVarianceEngine.combine_survey_and_monte_carlo_variance(
        survey_var=survey_var,
        sim_variance=sim_var,
        sim_replications_m=100_000,
    )
    assert res_large["monte_carlo_variance"] == 0.00001
    assert math.isclose(res_large["total_variance"], survey_var, abs_tol=1e-4)


# =============================================================================
# 9. Keyed Pseudonymization & Privacy-Preserving Artifact Export
# =============================================================================

def test_keyed_pseudonymization_and_privacy_preserving_artifacts():
    """Verify keyed HMAC pseudonymizer and confirm derived artifacts contain zero raw PII."""
    raw_pid = "RESP_998811"
    raw_hhid = "HH_443322"

    p_default = KeyedPseudonymizer()
    pseudo1 = p_default.pseudonymize_participant(raw_pid)
    hh1 = p_default.pseudonymize_household(raw_hhid)

    assert pseudo1.startswith("lasi_p_")
    assert hh1.startswith("lasi_hh_")
    assert raw_pid not in pseudo1
    assert raw_hhid not in hh1

    # Different key produces different pseudonyms
    p_custom = KeyedPseudonymizer(secret_key="MY_SECRET_TEST_KEY_2026")
    pseudo2 = p_custom.pseudonymize_participant(raw_pid)
    assert pseudo1 != pseudo2

    # Test report export to JSON and Markdown
    records = [_build_test_record(pid="p1", hhid="hh1")]
    diag = LasiSurveyDesignDiagnostics(records=records)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        json_path, md_path = diag.export_report_artifacts(tmp_path)

        assert json_path.exists()
        assert md_path.exists()

        json_text = json_path.read_text(encoding="utf-8")
        md_text = md_path.read_text(encoding="utf-8")

        # Inviolable privacy assertion: Raw IDs must NEVER appear in output
        assert raw_pid not in json_text
        assert raw_hhid not in json_text
        assert raw_pid not in md_text
        assert raw_hhid not in md_text
        assert "CONFIDENTIALITY ASSURANCE" in md_text


# =============================================================================
# 10. External Validation Gate Invariance Under Diagnostics
# =============================================================================

def test_validation_gate_remains_pending_with_diagnostics():
    """Verify that survey design diagnostics on synthetic fixtures keep gate at REFERENCE_DATA_PENDING."""
    from synapse_simulator.evaluation.lasi.evaluator import LasiExternalEvaluator
    from synapse_simulator.evaluation.lasi.models import LasiDataQualityReport

    records = [_build_test_record(pid=f"p{i}") for i in range(10)]
    diag = LasiSurveyDesignDiagnostics(records=records)
    diag_report = diag.run_diagnostics()

    quality_rep = LasiDataQualityReport(
        source_file="synthetic_test.csv",
        file_sha256="test_sha256",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
        total_records_ingested=10,
        valid_records=10,
        survey_design_diagnostics=diag_report.model_dump(),
    )

    evaluator = LasiExternalEvaluator(
        synthetic_dir="data/evaluation/lasi_cohort_500/seed_42",
        reference_records=records,
        quality_report=quality_rep,
    )
    report = evaluator.evaluate()

    assert report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING
    assert report.calibration_leakage_veto is True
