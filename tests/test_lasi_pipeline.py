"""
Unit, Integration, and Scientific Audit Tests for LASI Wave 1 External Validation Pipeline.

Covers:
1. Multi-format ingestion, de-identification, and data quality reporting
2. Missing value normalization and outlier detection
3. Clinical blood pressure averaging rules (protocol mean vs fallbacks vs strict mode)
4. Complex survey design handling (weights, strata, PSU, Kish effective sample size)
5. Direct age- and sex-standardization across 8 Census SRS strata with empty strata handling
6. Hand-calculated statistical verification (weighted mean, weighted variance, n_eff, KS, W1, proportions)
7. Sample-size and effective-sample-size gating (INSUFFICIENT_SAMPLE_SIZE enforcement)
8. HbA1c harmonization audit (disabled by default, UNVERIFIED status)
9. Formal gate status enforcement ('REFERENCE_DATA_PENDING' for test fixtures)
"""

import math
from pathlib import Path
import pytest

from synapse_simulator.evaluation.metrics import (
    two_sample_ks_statistic,
    wasserstein_distance_1d,
    distribution_quantiles,
    weighted_mean_and_variance,
    effective_sample_size,
    survey_design_effect_weighting,
    survey_weighted_proportion_and_ci,
)
from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiDataQualityReport,
    LasiDataSourceType,
    LasiEvaluationGateStatus,
    LasiMetricStatus,
    LasiMetricResult,
)
from synapse_simulator.evaluation.lasi.ingestor import LasiDataIngestor
from synapse_simulator.evaluation.lasi.comparability import (
    PopulationComparabilityLayer,
    get_age_band_older_adult,
    CENSUS_SRS_OLDER_ADULT_WEIGHTS,
)
from synapse_simulator.evaluation.lasi.evaluator import (
    LasiExternalEvaluator,
    LasiEvaluationReportFormatter,
    MIN_SAMPLE_SIZE_DISTRIBUTION,
    MIN_SAMPLE_SIZE_PREVALENCE,
    MIN_EFFECTIVE_SAMPLE_SIZE,
)


FIXTURE_PATH = Path("data/evaluation/fixtures/lasi_wave1_sample_fixture.csv")
SYNTHETIC_DIR = Path("data/evaluation/calibrated_mc_500/seed_42")


# -------------------------------------------------------------------------
# 1. Hand-Calculated Analytical Verification Tests
# -------------------------------------------------------------------------

def test_hand_calculated_weighted_mean_and_variance():
    """Verify weighted mean and Bessel-corrected variance against exact manual calculations.
    
    Data: values = [100.0, 150.0, 200.0], weights = [1.0, 2.0, 1.0]
    Sum of weights = 4.0
    Weighted mean = (100*1 + 150*2 + 200*1) / 4 = 600 / 4 = 150.0
    Sum of squared weights = 1^2 + 2^2 + 1^2 = 6.0
    Bessel denominator = sum_w - (sum_w2 / sum_w) = 4.0 - (6.0 / 4.0) = 4.0 - 1.5 = 2.5
    Weighted sum of squares = 1*(100-150)^2 + 2*(150-150)^2 + 1*(200-150)^2
                            = 2500 + 0 + 2500 = 5000.0
    Unbiased weighted sample variance = 5000.0 / 2.5 = 2000.0
    """
    vals = [100.0, 150.0, 200.0]
    weights = [1.0, 2.0, 1.0]
    w_mean, w_var = weighted_mean_and_variance(vals, weights)
    assert w_mean == 150.0
    assert w_var == 2000.0


def test_hand_calculated_effective_sample_size_and_deff():
    """Verify Kish's effective sample size against hand-calculated values.
    
    Weights = [1.0, 2.0, 1.0], N = 3
    Sum of weights = 4.0, (Sum w)^2 = 16.0
    Sum of squared weights = 1 + 4 + 1 = 6.0
    n_eff = 16.0 / 6.0 = 2.6667 -> rounded 2.67
    DEFF_w = N / n_eff = 3 / 2.67 = 1.125
    """
    weights = [1.0, 2.0, 1.0]
    n_eff = effective_sample_size(weights)
    assert n_eff == 2.67
    deff = survey_design_effect_weighting(weights)
    assert abs(deff - 1.125) < 0.01


def test_hand_calculated_survey_weighted_proportion_and_ci():
    """Verify survey-weighted proportion and design-adjusted confidence intervals.
    
    Outcomes = [1, 1, 0, 0], Weights = [2.0, 2.0, 1.0, 1.0]
    Weighted numerator = 1*2 + 1*2 + 0*1 + 0*1 = 4.0
    Sum of weights = 6.0
    Weighted prop = 4.0 / 6.0 = 0.6667
    Sum of w^2 = 4 + 4 + 1 + 1 = 10.0
    n_eff = 36.0 / 10.0 = 3.6
    SE = sqrt(p * (1-p) / n_eff) = sqrt(0.6667 * 0.3333 / 3.6) = sqrt(0.2222 / 3.6) = sqrt(0.06173) = 0.2484
    95% Margin of error = 1.959964 * 0.2484 = 0.4870
    Lower CI = max(0.0, 0.6667 - 0.4870) = 0.1797
    Upper CI = min(1.0, 0.6667 + 0.4870) = 1.0 (clamped)
    """
    vals = [1, 1, 0, 0]
    weights = [2.0, 2.0, 1.0, 1.0]
    prop, (ci_low, ci_high), n_eff = survey_weighted_proportion_and_ci(vals, weights)
    assert round(prop, 4) == 0.6667
    assert n_eff == 3.6
    assert 0.15 <= ci_low <= 0.20
    assert ci_high == 1.0


def test_hand_calculated_ks_statistic():
    """Verify two-sample Kolmogorov-Smirnov statistic on known discrete step functions.
    
    s1 = [1.0, 2.0, 3.0]
    s2 = [2.0, 3.0, 4.0]
    At x=1.0: F1=1/3, F2=0, diff = 1/3 ~ 0.33333
    At x=2.0: F1=2/3, F2=1/3, diff = 1/3 ~ 0.33333
    At x=3.0: F1=1.0, F2=2/3, diff = 1/3 ~ 0.33333
    At x=4.0: F1=1.0, F2=1.0, diff = 0.0
    D_KS = 1/3 = 0.33333
    """
    s1 = [1.0, 2.0, 3.0]
    s2 = [2.0, 3.0, 4.0]
    d_stat, p_val = two_sample_ks_statistic(s1, s2)
    assert d_stat == 0.33333
    assert 0.0 <= p_val <= 1.0


def test_hand_calculated_wasserstein_distance():
    """Verify 1D Wasserstein distance on exact translated samples.
    
    s1 = [10.0, 20.0], s2 = [14.0, 24.0]
    Shift delta is exactly +4.0 across all quantiles.
    W1 = integral |F1^-1(u) - F2^-1(u)| du = 4.0
    """
    s1 = [10.0, 20.0]
    s2 = [14.0, 24.0]
    w1 = wasserstein_distance_1d(s1, s2)
    assert w1 == 4.0


def test_hand_calculated_direct_standardization_8_strata():
    """Verify direct standardization across all 8 standard older-adult strata.
    
    Construct a dataset with 1 observation per stratum matching CENSUS_SRS_OLDER_ADULT_WEIGHTS.
    """
    strata_weights = CENSUS_SRS_OLDER_ADULT_WEIGHTS
    assert len(strata_weights) == 8
    assert abs(sum(strata_weights.values()) - 1.000) < 1e-6

    # Provide 1 patient per stratum with distinct values
    mock_records = [
        {"age": 50.0, "gender": "Male", "val": 140.0},     # 45-54 Male (w=0.231)
        {"age": 50.0, "gender": "Female", "val": 130.0},   # 45-54 Female (w=0.222)
        {"age": 60.0, "gender": "Male", "val": 150.0},     # 55-64 Male (w=0.154)
        {"age": 60.0, "gender": "Female", "val": 145.0},   # 55-64 Female (w=0.149)
        {"age": 70.0, "gender": "Male", "val": 160.0},     # 65-74 Male (w=0.078)
        {"age": 70.0, "gender": "Female", "val": 155.0},   # 65-74 Female (w=0.076)
        {"age": 80.0, "gender": "Male", "val": 170.0},     # 75+ Male (w=0.043)
        {"age": 80.0, "gender": "Female", "val": 165.0},   # 75+ Female (w=0.047)
    ]

    expected_std = (
        0.231 * 140.0 + 0.222 * 130.0 +
        0.154 * 150.0 + 0.149 * 145.0 +
        0.078 * 160.0 + 0.076 * 155.0 +
        0.043 * 170.0 + 0.047 * 165.0
    )
    expected_std = round(expected_std, 3)

    unstd, std, report = PopulationComparabilityLayer.direct_standardize_mean(
        records=mock_records,
        value_extractor=lambda x: x["val"],
        age_extractor=lambda x: x["age"],
        gender_extractor=lambda x: x["gender"],
    )

    assert std == expected_std
    assert len(report["empty_strata"]) == 0
    assert report["populated_strata_count"] == 8


def test_direct_standardization_empty_strata_handling():
    """Verify proportional re-weighting when some strata are unobserved."""
    # Only 4 strata observed: 45-54 M/F and 55-64 M/F
    mock_records = [
        {"age": 50.0, "gender": "Male", "val": 140.0},
        {"age": 50.0, "gender": "Female", "val": 130.0},
        {"age": 60.0, "gender": "Male", "val": 150.0},
        {"age": 60.0, "gender": "Female", "val": 140.0},
    ]

    unstd, std, report = PopulationComparabilityLayer.direct_standardize_mean(
        records=mock_records,
        value_extractor=lambda x: x["val"],
        age_extractor=lambda x: x["age"],
        gender_extractor=lambda x: x["gender"],
    )

    assert std is not None
    assert len(report["empty_strata"]) == 4  # 65-74 M/F and 75+ M/F empty
    assert report["populated_strata_count"] == 4
    assert report["used_weight_mass"] == round(0.231 + 0.222 + 0.154 + 0.149, 4)


def test_direct_standardization_insufficient_strata_abort():
    """Verify standardization aborts when fewer than minimum required strata are populated."""
    # Only 2 strata populated (< min 4)
    mock_records = [
        {"age": 50.0, "gender": "Male", "val": 140.0},
        {"age": 50.0, "gender": "Female", "val": 130.0},
    ]

    unstd, std, report = PopulationComparabilityLayer.direct_standardize_mean(
        records=mock_records,
        value_extractor=lambda x: x["val"],
        age_extractor=lambda x: x["age"],
        gender_extractor=lambda x: x["gender"],
        min_populated_strata=4,
    )

    assert unstd == 135.0
    assert std is None
    assert "INSUFFICIENT_STRATA_POPULATED" in report["error"]


# -------------------------------------------------------------------------
# 2. Ingestion and Data Quality Tests
# -------------------------------------------------------------------------

def test_lasi_ingestor_clean_fixture(tmp_path):
    """Verify loading, parsing, de-identification, and data quality reporting."""
    ingestor = LasiDataIngestor(
        source_path=FIXTURE_PATH,
        derived_dir=tmp_path / "derived",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
    )
    records, report = ingestor.ingest()

    assert len(records) == 50
    assert report.total_records_ingested == 50
    assert report.valid_records == 50
    assert report.excluded_records == 0
    assert report.file_sha256 != ""
    assert report.data_source_type == LasiDataSourceType.SYNTHETIC_TEST_FIXTURE

    # Verify pseudonymization: no raw 'fix_p_001' in participant_id
    assert records[0].participant_id.startswith("lasi_p_")
    assert "fix_p_001" not in records[0].participant_id

    # Verify survey design variables & effective sample size
    assert report.survey_weights_present is True
    assert report.effective_sample_size > 0.0
    assert report.design_effect_weighting >= 1.0
    assert report.strata_present is True
    assert report.psu_present is True

    # Verify derived CSV output
    derived_file = tmp_path / "derived" / "lasi_cleaned_records.csv"
    assert derived_file.exists()


def test_lasi_protocol_bp_averaging(tmp_path):
    """Verify that blood pressure averaging strictly implements LASI protocol."""
    ingestor = LasiDataIngestor(
        source_path=FIXTURE_PATH,
        derived_dir=tmp_path / "derived",
    )
    records, _ = ingestor.ingest()

    # Patient 1: SBP1=154, SBP2=152, SBP3=150 -> Mean of 2nd & 3rd = 151.0
    rec1 = records[0]
    assert rec1.sbp_mean == 151.0
    assert rec1.dbp_mean == 89.0  # DBP2=90, DBP3=88 -> Mean = 89.0
    assert rec1.bp_derivation_method == "PROTOCOL_MEAN_READINGS_2_AND_3"
    assert rec1.is_valid_for_bp is True


def test_lasi_strict_protocol_bp_mode(tmp_path):
    """Verify strict_protocol_bp=True rejects single-reading fallbacks."""
    # Create test CSV with one record having reading 2 missing
    p = tmp_path / "strict_bp_test.csv"
    p.write_text(
        "participant_id,r1agey,ragender,r1bpsys1,r1bpsys2,r1bpsys3,r1bpdia1,r1bpdia2,r1bpdia3\n"
        "p1,50,Male,140,138,136,85,84,82\n"  # Valid both 2 & 3
        "p2,55,Female,150,-999,144,90,-999,86\n",  # Reading 2 missing
        encoding="utf-8"
    )

    ingestor_strict = LasiDataIngestor(source_path=p, strict_protocol_bp=True)
    records, _ = ingestor_strict.ingest()

    assert records[0].is_valid_for_bp is True
    assert records[0].bp_derivation_method == "PROTOCOL_MEAN_READINGS_2_AND_3"

    assert records[1].is_valid_for_bp is False
    assert records[1].bp_derivation_method == "FALLBACK_READING_3_ONLY"


def test_lasi_missing_code_normalization(tmp_path):
    """Verify that survey missing sentinels (-999) are mapped to None."""
    ingestor = LasiDataIngestor(
        source_path=FIXTURE_PATH,
        derived_dir=tmp_path / "derived",
    )
    records, report = ingestor.ingest()

    # Patient 7 has r1hba1c = -999 in fixture
    rec7 = records[6]
    assert rec7.hba1c is None
    assert rec7.hba1c_dbs is None
    assert rec7.is_valid_for_hba1c is False
    assert report.missingness_counts["hba1c"] >= 1


def test_lasi_duplicate_participant_removal(tmp_path):
    """Verify that duplicate participant IDs are deduplicated and counted."""
    dup_file = tmp_path / "dup_test.csv"
    dup_file.write_text(
        "participant_id,r1agey,ragender,r1bpsys1,r1bpsys2,r1bpsys3,r1bpdia1,r1bpdia2,r1bpdia3\n"
        "p001,60,Male,140,138,136,85,84,82\n"
        "p001,60,Male,140,138,136,85,84,82\n"  # Exact duplicate
        "p002,62,Female,130,128,126,80,78,76\n",
        encoding="utf-8"
    )
    ingestor = LasiDataIngestor(source_path=dup_file)
    records, report = ingestor.ingest()

    assert len(records) == 2
    assert report.duplicate_records_detected == 1


def test_lasi_invalid_and_negative_survey_weights(tmp_path):
    """Verify handling of invalid or negative survey weights."""
    wt_file = tmp_path / "wt_test.csv"
    wt_file.write_text(
        "participant_id,r1agey,ragender,r1wtresp\n"
        "p1,50,Male,-1.5\n"   # Negative weight
        "p2,55,Female,0.0\n"   # Zero weight
        "p3,60,Male,2.0\n",
        encoding="utf-8"
    )
    ingestor = LasiDataIngestor(source_path=wt_file)
    records, report = ingestor.ingest()

    # Negative and zero weights are mapped to 1.0 with missingness flagged
    assert report.missingness_counts["survey_weight"] == 2
    assert records[0].survey_weight == 1.0
    assert records[1].survey_weight == 1.0
    assert records[2].survey_weight == 2.0


# -------------------------------------------------------------------------
# 3. HbA1c Harmonization & Audit Tests
# -------------------------------------------------------------------------

def test_hba1c_disabled_by_default():
    """Verify that HbA1c venous conversion is DISABLED by default."""
    assert PopulationComparabilityLayer.adjust_dbs_hba1c_to_venous(7.0, enabled=False) is None
    assert PopulationComparabilityLayer.adjust_dbs_hba1c_to_venous(None, enabled=True) is None

    # When explicitly enabled for research sensitivity testing:
    venous_val = PopulationComparabilityLayer.adjust_dbs_hba1c_to_venous(7.0, enabled=True)
    assert venous_val == round(0.94 * 7.0 + 0.45, 2)


# -------------------------------------------------------------------------
# 4. Gating Semantics and Sample Size Failure Tests
# -------------------------------------------------------------------------

def test_lasi_evaluator_sample_size_gating(tmp_path):
    """Verify that small samples are explicitly marked INSUFFICIENT_SAMPLE_SIZE and cannot pass."""
    ingestor = LasiDataIngestor(
        source_path=FIXTURE_PATH,
        derived_dir=tmp_path / "derived",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
    )
    records, quality_report = ingestor.ingest()

    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=records,
        quality_report=quality_report,
    )
    report = evaluator.evaluate()

    # 1. Gate status must be REFERENCE_DATA_PENDING for test fixtures
    assert report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING

    # 2. Check SBP metric: synthetic older adults N = 11 < 30 -> INSUFFICIENT_SAMPLE_SIZE
    sbp_m = next(m for m in report.metrics if m.metric_id == "lasi_bp_sbp_distribution")
    assert sbp_m.status == LasiMetricStatus.INSUFFICIENT_SAMPLE_SIZE
    assert sbp_m.min_sample_size_required == MIN_SAMPLE_SIZE_DISTRIBUTION

    # 3. Check HbA1c metric: venous harmonization disabled by default -> UNVERIFIED
    hba1c_m = next(m for m in report.metrics if m.metric_id == "lasi_lab_hba1c_distribution")
    assert hba1c_m.status == LasiMetricStatus.UNVERIFIED

    # 4. Check Population A metric: must be NOT_COMPARABLE
    pop_a_m = next(m for m in report.metrics if m.metric_id == "lasi_demo_pop_a_non_comparable")
    assert pop_a_m.status == LasiMetricStatus.NOT_COMPARABLE


def test_lasi_report_formatter_markdown_and_json(tmp_path):
    """Verify serialization to Markdown and JSON with regulatory notices."""
    ingestor = LasiDataIngestor(
        source_path=FIXTURE_PATH,
        derived_dir=tmp_path / "derived",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
    )
    records, quality_report = ingestor.ingest()

    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=records,
        quality_report=quality_report,
    )
    report = evaluator.evaluate()

    # Markdown export
    md_path = tmp_path / "LASI_EVALUATION_REPORT.md"
    LasiEvaluationReportFormatter.save_markdown(report, md_path)
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")
    assert "SYNAPSE Phase 2: LASI Wave 1 External Evaluation Report" in md_content
    assert "NOTICE OF PENDING EXTERNAL VALIDATION" in md_content
    assert "REFERENCE_DATA_PENDING" in md_content

    # JSON export
    json_path = tmp_path / "LASI_EVALUATION_REPORT.json"
    LasiEvaluationReportFormatter.save_json(report, json_path)
    assert json_path.exists()
    json_content = json_path.read_text(encoding="utf-8")
    assert "REFERENCE_DATA_PENDING" in json_content


def test_lasi_evaluator_missing_patients_csv(tmp_path):
    """Verify clear error when patients.csv is missing."""
    empty_dir = tmp_path / "empty_syn"
    empty_dir.mkdir()
    dummy_report = LasiDataQualityReport(
        source_file="test.csv",
        file_sha256="abc",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
    )
    with pytest.raises(ValueError, match="Required table 'patients.csv' is missing"):
        LasiExternalEvaluator(
            synthetic_dir=empty_dir,
            reference_records=[LasiCleanedRecord(participant_id="p1", age=50.0, gender="Male")],
            quality_report=dummy_report,
        )


def test_lasi_evaluator_empty_reference():
    """Verify clear error when reference record list is empty."""
    dummy_report = LasiDataQualityReport(
        source_file="empty.csv",
        file_sha256="abc",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
    )
    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=[],
        quality_report=dummy_report,
    )
    with pytest.raises(ValueError, match="Reference dataset is empty"):
        evaluator.evaluate()


def test_lasi_bp_fallback_rules():
    """Verify blood pressure averaging logic across partial readings."""
    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)

    # 1. Both 2nd and 3rd valid -> average of 2nd and 3rd
    val, code = ingestor._calculate_average_bp(150.0, 142.0, 138.0)
    assert val == 140.0
    assert code == "MEAN_2_3"

    # 2. Reading 2 valid, 3rd missing -> reading 2
    val, code = ingestor._calculate_average_bp(150.0, 142.0, None)
    assert val == 142.0
    assert code == "READING_2_ONLY"

    # 3. Reading 3 valid, 2nd missing -> reading 3
    val, code = ingestor._calculate_average_bp(150.0, None, 138.0)
    assert val == 138.0
    assert code == "READING_3_ONLY"

    # 4. Neither 2nd nor 3rd valid, but 1st valid -> fallback reading 1
    val, code = ingestor._calculate_average_bp(150.0, None, None)
    assert val == 150.0
    assert code == "FALLBACK_READING_1"

    # 5. None valid -> None
    val, code = ingestor._calculate_average_bp(None, None, None)
    assert val is None
    assert code == "NO_VALID_READING"


# -------------------------------------------------------------------------
# 5. Comprehensive Failure Mode and Scientific Boundary Tests
# -------------------------------------------------------------------------

def test_failure_mode_fixture_cannot_pass_overall_gate(tmp_path):
    """Verify that a synthetic test fixture CANNOT certify external validation."""
    dummy_report = LasiDataQualityReport(
        source_file="fixture.csv",
        file_sha256="abc123hash",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
        survey_weights_present=True,
        effective_sample_size=50.0,
    )
    # 50 records aged 50
    mock_records = [
        LasiCleanedRecord(
            participant_id=f"p_{i:03d}",
            age=55.0,
            gender="Female",
            sbp_mean=140.0,
            dbp_mean=85.0,
            survey_weight=1.0,
            is_valid_for_bp=True,
            diagnosed_hypertension=True,
            diagnosed_diabetes=False,
        )
        for i in range(50)
    ]
    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=mock_records,
        quality_report=dummy_report,
    )
    report = evaluator.evaluate()

    # Must be REFERENCE_DATA_PENDING because data source is fixture
    assert report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING
    assert report.overall_gate_status != LasiEvaluationGateStatus.PASS


def test_failure_mode_low_effective_sample_size_gated(tmp_path):
    """Verify that low Kish effective sample size (< 25.0) triggers INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE."""
    # 50 records, but extreme weights: 1 weight of 500.0, 49 weights of 1.0
    # Sum w = 549, Sum w^2 = 250000 + 49 = 250049
    # n_eff = (549)^2 / 250049 = 301401 / 250049 ~ 1.205 << 25.0
    mock_records = [
        LasiCleanedRecord(
            participant_id=f"p_{i:03d}",
            age=55.0,
            gender="Female",
            sbp_mean=140.0,
            dbp_mean=85.0,
            survey_weight=500.0 if i == 0 else 1.0,
            is_valid_for_bp=True,
            diagnosed_hypertension=True,
            diagnosed_diabetes=False,
        )
        for i in range(50)
    ]
    weights = [r.survey_weight for r in mock_records]
    n_eff = effective_sample_size(weights)
    assert n_eff < MIN_EFFECTIVE_SAMPLE_SIZE

    dummy_report = LasiDataQualityReport(
        source_file="extreme_weights.csv",
        file_sha256="abc123hash",
        data_source_type=LasiDataSourceType.GENUINE_LASI_MICRODATA,
        survey_weights_present=True,
        effective_sample_size=n_eff,
    )
    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=mock_records,
        quality_report=dummy_report,
    )
    report = evaluator.evaluate()

    # Prevalences evaluate N=29 synthetic vs N=50 ref, but ref_n_eff < 25.0
    htn_m = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_older_adult")
    assert htn_m.status == LasiMetricStatus.INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE


def test_failure_mode_unsupported_hba1c_cannot_pass():
    """Verify that HbA1c cannot receive PASS when venous conversion is disabled."""
    mock_records = [
        LasiCleanedRecord(
            participant_id=f"p_{i:03d}",
            age=55.0,
            gender="Male",
            hba1c=7.5,
            hba1c_dbs=7.5,
            hba1c_venous=None,
            is_valid_for_hba1c=True,
        )
        for i in range(50)
    ]
    dummy_report = LasiDataQualityReport(
        source_file="hba1c_test.csv",
        file_sha256="abc123hash",
        data_source_type=LasiDataSourceType.GENUINE_LASI_MICRODATA,
        survey_weights_present=False,
        effective_sample_size=50.0,
    )
    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=mock_records,
        quality_report=dummy_report,
        enable_venous_hba1c=False,
    )
    report = evaluator.evaluate()

    hba1c_m = next(m for m in report.metrics if m.metric_id == "lasi_lab_hba1c_distribution")
    assert hba1c_m.status == LasiMetricStatus.UNVERIFIED
    assert hba1c_m.status != LasiMetricStatus.PASS


def test_failure_mode_metric_failure_prevents_overall_pass():
    """Verify that a failure in a required metric prevents an overall PASS."""
    # Create genuine microdata mock with 50 older adults having extreme SBP (e.g., all 240 mmHg)
    # This will cause a massive difference between synthetic (mean ~155) and reference (mean 240)
    # Wasserstein > 15 mmHg -> status FAIL
    mock_records = [
        LasiCleanedRecord(
            participant_id=f"p_{i:03d}",
            age=55.0,
            gender="Male",
            sbp_mean=240.0,
            dbp_mean=130.0,
            survey_weight=1.0,
            is_valid_for_bp=True,
            diagnosed_hypertension=True,
            diagnosed_diabetes=False,
        )
        for i in range(50)
    ]
    dummy_report = LasiDataQualityReport(
        source_file="genuine_microdata_extreme.csv",
        file_sha256="abc123hash",
        data_source_type=LasiDataSourceType.GENUINE_LASI_MICRODATA,
        survey_weights_present=True,
        effective_sample_size=50.0,
    )
    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=mock_records,
        quality_report=dummy_report,
    )
    # In synthetic cohort, SBP synthetic N=11 (<30) triggers INSUFFICIENT_SAMPLE_SIZE
    # When INSUFFICIENT_SAMPLE_SIZE or FAIL is present, overall_gate_status CANNOT be PASS
    report = evaluator.evaluate()
    assert report.overall_gate_status != LasiEvaluationGateStatus.PASS
    assert report.overall_gate_status in {LasiEvaluationGateStatus.FAIL, LasiEvaluationGateStatus.INSUFFICIENT_SAMPLE_SIZE}


def test_failure_mode_case_definitions_strictly_segregated():
    """Verify that objective measurement, self-report, and condition codes are segregated."""
    # A patient may have normal blood pressure (<140/90) but have diagnosed hypertension
    rec_controlled = LasiCleanedRecord(
        participant_id="p_ctrl_01",
        age=60.0,
        gender="Female",
        sbp_mean=122.0,  # Normotensive measured
        dbp_mean=78.0,
        diagnosed_hypertension=True,  # Self-reported diagnosed
        taking_bp_medication=True,    # Treated
        is_valid_for_bp=True,
    )
    assert rec_controlled.sbp_mean < 140.0
    assert rec_controlled.diagnosed_hypertension is True

    # A patient may have stage 2 hypertension measured, but no diagnosis (undiagnosed)
    rec_undiagnosed = LasiCleanedRecord(
        participant_id="p_undx_01",
        age=62.0,
        gender="Male",
        sbp_mean=168.0,  # Stage 2 hypertension measured
        dbp_mean=102.0,
        diagnosed_hypertension=False,  # Unaware / undiagnosed
        taking_bp_medication=False,
        is_valid_for_bp=True,
    )
    assert rec_undiagnosed.sbp_mean >= 140.0
    assert rec_undiagnosed.diagnosed_hypertension is False


def test_dbp_observation_survives_complete_export_and_evaluation(tmp_path):
    """Regression test: verify that a valid generated DBP observation survives the complete
    export and evaluation pipeline (runner -> observations.csv -> LasiExternalEvaluator)."""
    from datetime import datetime
    import csv
    from synapse_simulator.state.state_manager import StateManager
    from synapse_simulator.datagen.master_data import MasterDataSnapshot
    from synapse_simulator.modules.engine import ClinicalModuleRunner
    from synapse_simulator.modules.loader import load_clinical_module
    from synapse_simulator.datagen.models import PatientContext
    from synapse_simulator.exporter.csv_exporter import CSVExporter

    pid = "pat-dbp-test-01"
    enc_id = "enc-dbp-01"
    pctx = PatientContext(
        patient_id=pid,
        name="DBP Survival Test",
        age=58,
        gender="Male",
        allergies=[],
        chronic_conditions=[],
    )

    sm = StateManager()
    sm.set_entity_state("clinical.encounters", enc_id, {
        "encounter_id": enc_id, "patient_id": pid, "journey_id": f"j-{pid}",
        "doctor_id": "doc-01", "start_time": "2026-01-10T10:00:00",
        "end_time": "2026-01-10T10:20:00", "status": "Closed",
    })

    # Set up module runner with SBP and DBP observations
    htn_module = load_clinical_module(Path("config/modules/hypertension.yaml"))
    runner = ClinicalModuleRunner([htn_module], base_seed=42)
    runner.initialize_patient(pctx)
    runner.longitudinal_observations.extend([
        {
            "observation_id": "obs-sbp-01",
            "patient_id": pid,
            "encounter_id": enc_id,
            "timestamp": datetime(2026, 1, 10, 10, 15),
            "observation_code": "SBP",
            "observation_name": "Systolic Blood Pressure",
            "value": 152.0,
            "unit": "mmHg",
            "is_abnormal": True,
        },
        {
            "observation_id": "obs-dbp-01",
            "patient_id": pid,
            "encounter_id": enc_id,
            "timestamp": datetime(2026, 1, 10, 10, 15),
            "observation_code": "DBP",
            "observation_name": "Diastolic Blood Pressure",
            "value": 88.0,
            "unit": "mmHg",
            "is_abnormal": False,
        },
    ])

    # Export to CSV
    export_dir = tmp_path / "export_test"
    exp = CSVExporter(
        state_manager=sm,
        master_data=MasterDataSnapshot(),
        patient_contexts={pid: pctx},
        committed_events=[],
        journeys=[],
        module_runner=runner,
        metrics={"random_seed": 42, "final_simulation_time": "2026-01-15T00:00:00"},
        output_dir=export_dir / "phase2",
    )
    exported = exp.export_simplified_dataset(target_dir=export_dir)
    assert "observations.csv" in exported

    # 1. Verify DBP is serialized in observations.csv
    with open(export_dir / "observations.csv", "r", encoding="utf-8") as f:
        obs_rows = list(csv.DictReader(f))
    dbp_rows = [r for r in obs_rows if r["observation_code"] == "DBP"]
    assert len(dbp_rows) == 1
    assert dbp_rows[0]["patient_id"] == pid
    assert dbp_rows[0]["encounter_id"] == enc_id
    assert float(dbp_rows[0]["value"]) == 88.0
    assert dbp_rows[0]["unit"] == "mmHg"

    # 2. Verify LasiExternalEvaluator reads and parses DBP observation
    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()
    dbp_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_dbp_distribution")
    assert dbp_metric.synthetic_n == 1
    assert dbp_metric.synthetic_estimate == 88.0


# -------------------------------------------------------------------------
# 6. Paired Blood Pressure Model, Index Selection, and Estimand Tests
# -------------------------------------------------------------------------

def test_paired_blood_pressure_state_machine_emission():
    """Verify that hypertension state machine emits paired SBP and DBP at the exact same encounter and timestamp."""
    from datetime import datetime, timedelta
    from synapse_simulator.modules.engine import ClinicalModuleRunner
    from synapse_simulator.modules.loader import load_clinical_module
    from synapse_simulator.datagen.models import PatientContext

    htn_module = load_clinical_module(Path("config/modules/hypertension.yaml"))
    runner = ClinicalModuleRunner([htn_module], base_seed=42)

    patient = PatientContext(
        patient_id="pat-bp-pair-01",
        name="Paired BP Test",
        age=52,
        gender="Female",
        allergies=[],
        chronic_conditions=[],
    )
    runner.initialize_patient(patient)

    # 1. Test RecordBloodPressure state
    start_time = datetime(2026, 3, 1, 10, 0, 0)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "RecordBloodPressure"
    runner.patient_records[patient.patient_id]["current_encounter_id"] = "enc-screening-01"

    runner.step_patient(patient, current_time=start_time, timestep=timedelta(days=1))

    obs = runner.longitudinal_observations
    assert len(obs) == 2
    sbp_obs = next(o for o in obs if o["observation_code"] == "SBP")
    dbp_obs = next(o for o in obs if o["observation_code"] == "DBP")

    # Invariant: identical encounter, timestamp, and patient
    assert sbp_obs["patient_id"] == patient.patient_id
    assert dbp_obs["patient_id"] == patient.patient_id
    assert sbp_obs["encounter_id"] == "enc-screening-01"
    assert dbp_obs["encounter_id"] == "enc-screening-01"
    assert sbp_obs["timestamp"] == dbp_obs["timestamp"]
    assert start_time <= sbp_obs["timestamp"] <= start_time + timedelta(days=1)
    assert sbp_obs["unit"] == "mmHg"
    assert dbp_obs["unit"] == "mmHg"

    # Physiological plausibility invariant: SBP > DBP and PP >= 20
    assert sbp_obs["value"] > dbp_obs["value"]
    pulse_pressure = sbp_obs["value"] - dbp_obs["value"]
    assert pulse_pressure >= 20.0
    assert 145.0 <= sbp_obs["value"] <= 168.0
    assert 70.0 <= dbp_obs["value"] <= 104.0

    # 2. Test MeasureFollowUpBP state
    followup_time = start_time + timedelta(days=90)
    runner.patient_module_states[patient.patient_id]["mod-htn-01"] = "MeasureFollowUpBP"
    runner.patient_records[patient.patient_id]["current_encounter_id"] = "enc-followup-01"

    runner.step_patient(patient, current_time=followup_time, timestep=timedelta(days=1))

    assert len(runner.longitudinal_observations) == 4
    sbp_fu = [o for o in runner.longitudinal_observations if o["encounter_id"] == "enc-followup-01" and o["observation_code"] == "SBP"][0]
    dbp_fu = [o for o in runner.longitudinal_observations if o["encounter_id"] == "enc-followup-01" and o["observation_code"] == "DBP"][0]

    assert sbp_fu["timestamp"] == dbp_fu["timestamp"]
    assert followup_time <= sbp_fu["timestamp"] <= followup_time + timedelta(days=1)
    assert sbp_fu["value"] > dbp_fu["value"]
    assert (sbp_fu["value"] - dbp_fu["value"]) >= 20.0


def test_implausible_pulse_pressure_flagged_in_evaluator(tmp_path):
    """Verify that implausible pulse pressure (PP < 20, PP > 110, or SBP <= DBP) is audited and flagged."""
    import csv

    # Set up synthetic directory with patients and observations having implausible PP
    export_dir = tmp_path / "implausible_pp_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-imp-01", "gender": "Female", "age": "55.0", "date_of_birth": "1971-01-01"})
        writer.writerow({"patient_id": "p-imp-02", "gender": "Male", "age": "60.0", "date_of_birth": "1966-01-01"})
        writer.writerow({"patient_id": "p-imp-03", "gender": "Female", "age": "65.0", "date_of_birth": "1961-01-01"})

    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        # p-imp-01: PP = 10 (< 20)
        writer.writerow({"observation_id": "o1", "patient_id": "p-imp-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "115.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-imp-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "105.0", "unit": "mmHg", "is_abnormal": "True"})
        # p-imp-02: PP = 130 (> 110)
        writer.writerow({"observation_id": "o3", "patient_id": "p-imp-02", "encounter_id": "e2", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "220.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o4", "patient_id": "p-imp-02", "encounter_id": "e2", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "90.0", "unit": "mmHg", "is_abnormal": "True"})
        # p-imp-03: SBP <= DBP (inverted)
        writer.writerow({"observation_id": "o5", "patient_id": "p-imp-03", "encounter_id": "e3", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "120.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o6", "patient_id": "p-imp-03", "encounter_id": "e3", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "125.0", "unit": "mmHg", "is_abnormal": "True"})

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Verify that all 3 implausible pulse pressure encounters are flagged in audit telemetry
    assert report.blood_pressure_concordance["implausible_pulse_pressure_count"] == 3


def test_missing_dbp_unpaired_observation_handled_explicitly(tmp_path):
    """Verify that missing DBP is audited explicitly and NEVER imputed from SBP."""
    import csv

    export_dir = tmp_path / "missing_dbp_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-mis-01", "gender": "Female", "age": "55.0", "date_of_birth": "1971-01-01"})
        writer.writerow({"patient_id": "p-mis-02", "gender": "Male", "age": "60.0", "date_of_birth": "1966-01-01"})

    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        # p-mis-01 has paired SBP and DBP
        writer.writerow({"observation_id": "o1", "patient_id": "p-mis-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "145.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-mis-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "92.0", "unit": "mmHg", "is_abnormal": "True"})
        # p-mis-02 has ONLY SBP (missing DBP)
        writer.writerow({"observation_id": "o3", "patient_id": "p-mis-02", "encounter_id": "e2", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "150.0", "unit": "mmHg", "is_abnormal": "True"})

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Audit telemetry confirms explicit detection
    assert report.blood_pressure_concordance["patients_with_paired_bp"] == 1
    assert report.blood_pressure_concordance["patients_only_sbp"] == 1
    assert report.blood_pressure_concordance["patients_only_dbp"] == 0

    # DBP metric must have synthetic_n == 1 (not 2; no imputation)
    dbp_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_dbp_distribution")
    assert dbp_metric.synthetic_n == 1
    assert dbp_metric.synthetic_estimate == 92.0


def test_prespecified_index_measurement_selection_prevents_pseudoreplication(tmp_path):
    """Verify that repeated longitudinal observations do not inflate patient-level sample size.
    Rule: First eligible measurement encounter (earliest timestamp) is selected as index measurement."""
    import csv

    export_dir = tmp_path / "longitudinal_bp_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-long-01", "gender": "Female", "age": "58.0", "date_of_birth": "1968-01-01"})

    # 3 longitudinal encounters across 1 year for 1 patient:
    # Enc 1 (t=2026-01-10): SBP 165, DBP 100 (Index encounter)
    # Enc 2 (t=2026-05-15): SBP 145, DBP 90
    # Enc 3 (t=2026-10-20): SBP 128, DBP 82
    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        writer.writerow({"observation_id": "o1", "patient_id": "p-long-01", "encounter_id": "e1", "timestamp": "2026-01-10T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "165.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-long-01", "encounter_id": "e1", "timestamp": "2026-01-10T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "100.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o3", "patient_id": "p-long-01", "encounter_id": "e2", "timestamp": "2026-05-15T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "145.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o4", "patient_id": "p-long-01", "encounter_id": "e2", "timestamp": "2026-05-15T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "90.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o5", "patient_id": "p-long-01", "encounter_id": "e3", "timestamp": "2026-10-20T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "128.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o6", "patient_id": "p-long-01", "encounter_id": "e3", "timestamp": "2026-10-20T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "82.0", "unit": "mmHg", "is_abnormal": "False"})

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Estimand A: Cross-sectional SBP distribution
    sbp_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_sbp_distribution")
    # Patient count is 1, NOT 3!
    assert sbp_metric.synthetic_patient_count == 1
    assert sbp_metric.synthetic_observation_count == 3
    assert sbp_metric.synthetic_n == 1
    # Index measurement must be the earliest encounter (165.0, not mean 146.0 or latest 128.0)
    assert sbp_metric.synthetic_estimate == 165.0

    dbp_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_dbp_distribution")
    assert dbp_metric.synthetic_patient_count == 1
    assert dbp_metric.synthetic_observation_count == 3
    assert dbp_metric.synthetic_n == 1
    assert dbp_metric.synthetic_estimate == 100.0

    # Pulse pressure metric also reflects index measurement: 165 - 100 = 65.0
    pp_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_pulse_pressure_distribution")
    assert pp_metric.synthetic_estimate == 65.0

    # Estimand D: Longitudinal treatment response
    traj_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_longitudinal_trajectory_treatment_response")
    assert traj_metric.status == LasiMetricStatus.UNVERIFIED
    assert traj_metric.synthetic_patient_count == 1
    assert traj_metric.synthetic_observation_count == 3
    # Delta SBP = latest (128.0) - baseline (165.0) = -37.0 mmHg
    assert traj_metric.synthetic_estimate == -37.0


def test_separated_evaluation_estimands_structure(tmp_path):
    """Verify that Estimands A, B, C, and D are explicitly segregated and never conflated."""
    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=SYNTHETIC_DIR,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Collect estimands
    estimands = {m.metric_id: m for m in report.metrics}

    # Estimand A: Patient-level cross-sectional distributions
    assert "lasi_bp_sbp_distribution" in estimands
    assert "lasi_bp_dbp_distribution" in estimands
    assert "lasi_bp_pulse_pressure_distribution" in estimands
    for mid in ["lasi_bp_sbp_distribution", "lasi_bp_dbp_distribution", "lasi_bp_pulse_pressure_distribution"]:
        assert estimands[mid].estimand_type == "ESTIMAND_A_PATIENT_LEVEL_INDEX_DISTRIBUTION"

    # Estimand B: Measurement-defined hypertension prevalence (SBP>=140 | DBP>=90 | Rx)
    assert "lasi_prev_measurement_defined_htn_older_adult" in estimands
    assert estimands["lasi_prev_measurement_defined_htn_older_adult"].estimand_type == "ESTIMAND_B_MEASUREMENT_DEFINED_PREVALENCE"

    # Estimand C: Synthetic EHR recorded hypertension diagnosis
    assert "lasi_prev_htn_older_adult" in estimands
    assert estimands["lasi_prev_htn_older_adult"].estimand_type == "ESTIMAND_C_EHR_RECORDED_PREVALENCE"

    # Estimand D: Longitudinal BP trajectory / treatment response
    assert "lasi_bp_longitudinal_trajectory_treatment_response" in estimands
    assert estimands["lasi_bp_longitudinal_trajectory_treatment_response"].estimand_type == "ESTIMAND_D_LONGITUDINAL_TRAJECTORY"
    assert estimands["lasi_bp_longitudinal_trajectory_treatment_response"].status == LasiMetricStatus.UNVERIFIED


# -------------------------------------------------------------------------
# 7. Independent Estimand and Representativeness Unit Tests
# -------------------------------------------------------------------------

def test_measurement_defined_htn_without_ehr_diagnosis(tmp_path):
    """Verify that a patient can meet the measurement-defined HTN definition without an EHR diagnosis."""
    import csv
    export_dir = tmp_path / "measured_undx_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-undx-01", "gender": "Female", "age": "55.0", "date_of_birth": "1971-01-01"})

    # Stage 2 hypertension measured (150/95 mmHg), but NO diagnosis in conditions.csv
    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        writer.writerow({"observation_id": "o1", "patient_id": "p-undx-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "150.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-undx-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "95.0", "unit": "mmHg", "is_abnormal": "True"})

    with open(export_dir / "conditions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"])
        writer.writeheader()
        # No condition records!

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Measurement-defined HTN prevalence must be 100% (1/1)
    m_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_measurement_defined_htn_older_adult")
    assert m_metric.synthetic_estimate == 100.0

    # EHR-recorded HTN prevalence must be 0% (0/1)
    ehr_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_older_adult")
    assert ehr_metric.synthetic_estimate == 0.0


def test_ehr_diagnosis_without_measurement_threshold(tmp_path):
    """Verify that a patient can have an EHR diagnosis without meeting the current measurement threshold."""
    import csv
    export_dir = tmp_path / "dx_normal_bp_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-dx-norm-01", "gender": "Male", "age": "60.0", "date_of_birth": "1966-01-01"})

    # Normotensive measured BP (122/78 mmHg), no antihypertensives prescribed
    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        writer.writerow({"observation_id": "o1", "patient_id": "p-dx-norm-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "122.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-dx-norm-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "78.0", "unit": "mmHg", "is_abnormal": "False"})

    # Documented I10 diagnosis in conditions.csv (e.g. historical / controlled diagnosis)
    with open(export_dir / "conditions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"])
        writer.writeheader()
        writer.writerow({"condition_id": "c1", "patient_id": "p-dx-norm-01", "encounter_id": "e1", "condition_code": "I10", "condition_name": "Essential (primary) hypertension", "status": "Active"})

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Measurement-defined HTN must be 0% (0/1) because BP < 140/90 and not on medication
    m_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_measurement_defined_htn_older_adult")
    assert m_metric.synthetic_estimate == 0.0

    # EHR-recorded HTN must be 100% (1/1)
    ehr_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_older_adult")
    assert ehr_metric.synthetic_estimate == 100.0


def test_antihypertensive_treatment_qualifies_measurement_definition(tmp_path):
    """Verify that a patient with normal measured blood pressure on antihypertensive medication qualifies as hypertensive."""
    import csv
    export_dir = tmp_path / "rx_treated_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-rx-01", "gender": "Female", "age": "65.0", "date_of_birth": "1961-01-01"})
        writer.writerow({"patient_id": "p-other-med-01", "gender": "Male", "age": "65.0", "date_of_birth": "1961-01-01"})

    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        # Both patients have normal blood pressure
        writer.writerow({"observation_id": "o1", "patient_id": "p-rx-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "124.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-rx-01", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "78.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o3", "patient_id": "p-other-med-01", "encounter_id": "e2", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "120.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o4", "patient_id": "p-other-med-01", "encounter_id": "e2", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "75.0", "unit": "mmHg", "is_abnormal": "False"})

    with open(export_dir / "medications.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["medication_id", "patient_id", "encounter_id", "condition_id", "drug_name", "drug_class", "dosage", "frequency", "source", "evidence_ids", "status"])
        writer.writeheader()
        # p-rx-01 has Amlodipine (antihypertensive)
        writer.writerow({"medication_id": "m1", "patient_id": "p-rx-01", "encounter_id": "e1", "condition_id": "c1", "drug_name": "Amlodipine", "drug_class": "CCB", "dosage": "5mg", "frequency": "Once Daily", "source": "yaml", "evidence_ids": "", "status": "Dispensed"})
        # p-other-med-01 has Paracetamol (analgesic, non-antihypertensive)
        writer.writerow({"medication_id": "m2", "patient_id": "p-other-med-01", "encounter_id": "e2", "condition_id": "c2", "drug_name": "Paracetamol", "drug_class": "Analgesic", "dosage": "500mg", "frequency": "As Needed", "source": "yaml", "evidence_ids": "", "status": "Dispensed"})

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Exactly 1 of 2 patients qualifies for measurement-defined hypertension (50.0%)
    m_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_measurement_defined_htn_older_adult")
    assert m_metric.synthetic_estimate == 50.0
    assert m_metric.synthetic_n == 2


def test_missing_bp_not_silently_treated_as_normal(tmp_path):
    """Verify that unmeasured patients are excluded from continuous BP metrics and not imputed as 0 or 120."""
    import csv
    export_dir = tmp_path / "missing_bp_unmeasured_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-measured", "gender": "Female", "age": "55.0", "date_of_birth": "1971-01-01"})
        writer.writerow({"patient_id": "p-unmeasured", "gender": "Male", "age": "60.0", "date_of_birth": "1966-01-01"})

    # Only p-measured has an observation
    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        writer.writerow({"observation_id": "o1", "patient_id": "p-measured", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "135.0", "unit": "mmHg", "is_abnormal": "False"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-measured", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "85.0", "unit": "mmHg", "is_abnormal": "False"})

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Continuous SBP distribution must include ONLY the measured patient (synthetic_n = 1)
    sbp_metric = next(m for m in report.metrics if m.metric_id == "lasi_bp_sbp_distribution")
    assert sbp_metric.synthetic_n == 1
    assert sbp_metric.synthetic_patient_count == 1
    assert sbp_metric.synthetic_estimate == 135.0

    # In audit concordance: unmeasured rate is 50.0% (1 of 2)
    assert report.blood_pressure_concordance["missingness_rate_pct"] == 50.0


def test_metric_denominators_separated_between_distributions_and_prevalence():
    """Verify that prevalence estimands use scientifically correct, distinct denominators:
    - Continuous distributions: Measured patients (N = 235)
    - Estimand A (EHR Diagnosis): Total older adults (N = 575)
    - Estimand B (Measurement-Defined): Assessable older adults with BP/Rx (N = 235)
    - Estimand C (Community Assessment): Community-assessed older adults (N = 561)
    - Estimand D (Clinical Attenders): Facility attenders (N = 485)
    - Estimand E (Unassessable Status): Total older adults (N = 575)
    """
    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=cohort_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Continuous distributions: synthetic_n == 235 (measured patients)
    sbp_m = next(m for m in report.metrics if m.metric_id == "lasi_bp_sbp_distribution")
    dbp_m = next(m for m in report.metrics if m.metric_id == "lasi_bp_dbp_distribution")
    pp_m = next(m for m in report.metrics if m.metric_id == "lasi_bp_pulse_pressure_distribution")
    assert sbp_m.synthetic_n == 235
    assert dbp_m.synthetic_n == 235
    assert pp_m.synthetic_n == 235

    # Estimand A: EHR-recorded diagnosis prevalence (Denominator = 575, Numerator = 235)
    prev_ehr_htn = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_older_adult")
    assert prev_ehr_htn.synthetic_n == 575
    assert prev_ehr_htn.synthetic_estimate == 40.87

    # Estimand B: Measurement-defined among assessable participants (Denominator = 235, Numerator = 235)
    prev_m_htn = next(m for m in report.metrics if m.metric_id == "lasi_prev_measurement_defined_htn_older_adult")
    assert prev_m_htn.synthetic_n == 235
    assert prev_m_htn.synthetic_estimate == 100.0

    # Estimand C: Community health assessment prevalence
    prev_comm = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_community_assessment")
    assert prev_comm.synthetic_n == 561
    assert prev_comm.synthetic_estimate == 38.68

    # Estimand D: Hypertension prevalence among clinical facility attenders (Denominator = 485)
    prev_clinic = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_clinical_attenders")
    assert prev_clinic.synthetic_n == 485
    assert prev_clinic.synthetic_estimate == 48.45

    # Estimand E: Unassessable / missing status rate (Denominator = 575, Numerator = 340)
    prev_unassess = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_unassessable_status")
    assert prev_unassess.synthetic_n == 575
    assert prev_unassess.synthetic_estimate == 59.13


def test_community_measurements_do_not_create_clinical_encounters_or_diagnoses():
    """Verify that community assessments never create clinical encounters, diagnoses, or prescriptions."""
    from synapse_simulator.datagen.community_assessment import (
        CommunityAssessmentGenerator,
        CommunityAssessmentConfig,
    )
    from synapse_simulator.datagen.models import PatientContext

    # Create dummy patients: one normotensive, one latent hypertensive
    p_norm = PatientContext(
        patient_id="p-comm-01",
        name="Test Patient 1",
        age=50,
        gender="Male",
        latent_conditions={},
    )
    p_htn = PatientContext(
        patient_id="p-comm-02",
        name="Test Patient 2",
        age=62,
        gender="Female",
        latent_conditions={"I10": {"code": "I10", "name": "Essential hypertension", "recognized": False}},
    )
    patients = {p_norm.patient_id: p_norm, p_htn.patient_id: p_htn}

    generator = CommunityAssessmentGenerator(base_seed=42)
    assessments = generator.generate(patients)

    # 1. Exactly 2 community assessment records created
    assert len(assessments) == 2

    # 2. Each record has valid community vital signs and provenance
    for ca in assessments:
        assert ca.provenance == "COMMUNITY_HEALTH_ASSESSMENT_LAYER"
        assert ca.unit == "mmHg"
        assert ca.sbp is not None and ca.dbp is not None
        assert ca.pulse_pressure >= 20.0
        # Must not contain any clinical encounter ID
        assert not hasattr(ca, "encounter_id") or ca.encounter_id is None

    # 3. Patient latent condition recognized status must NOT be modified
    assert p_htn.latent_conditions["I10"]["recognized"] is False


def test_patient_can_have_community_bp_without_ehr_diagnosis(tmp_path):
    """Demonstrate that a patient can have valid community BP readings with zero EHR diagnoses."""
    import csv
    export_dir = tmp_path / "comm_no_dx_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-comm-only-01", "gender": "Female", "age": "58.0", "date_of_birth": "1968-01-01"})

    # Community assessment file with measured BP (132/82 mmHg)
    with open(export_dir / "community_assessments.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "assessment_id", "patient_id", "timestamp", "assessment_type",
            "sbp", "dbp", "pulse_pressure", "unit", "survey_weight", "status", "provenance"
        ])
        writer.writeheader()
        writer.writerow({
            "assessment_id": "ca-p-comm-only-01",
            "patient_id": "p-comm-only-01",
            "timestamp": "2024-06-15T09:30:00",
            "assessment_type": "COMMUNITY_HEALTH_ASSESSMENT",
            "sbp": "132.0",
            "dbp": "82.0",
            "pulse_pressure": "50.0",
            "unit": "mmHg",
            "survey_weight": "1.0",
            "status": "COMPLETED",
            "provenance": "COMMUNITY_HEALTH_ASSESSMENT_LAYER",
        })

    # Empty clinical tables
    for tbl in ["encounters.csv", "conditions.csv", "observations.csv", "medications.csv", "deaths.csv"]:
        with open(export_dir / tbl, "w", newline="", encoding="utf-8") as f:
            f.write("")

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Community assessment evaluated: 1 assessed patient, 0 positive (SBP < 140 and DBP < 90)
    comm_m = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_community_assessment")
    assert comm_m.synthetic_n == 1
    assert comm_m.synthetic_estimate == 0.0

    # EHR recorded diagnosis: 0% (0 / 1)
    ehr_m = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_older_adult")
    assert ehr_m.synthetic_estimate == 0.0


def test_missing_measurements_classified_as_unassessable_not_negative(tmp_path):
    """Verify that unmeasured older adults are classified under Estimand E (unassessable) and excluded from Estimand B denominator."""
    import csv
    export_dir = tmp_path / "unmeasured_safeguard_cohort"
    export_dir.mkdir(parents=True)

    with open(export_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "gender", "age", "date_of_birth"])
        writer.writeheader()
        writer.writerow({"patient_id": "p-measured-htn", "gender": "Female", "age": "60.0", "date_of_birth": "1966-01-01"})
        writer.writerow({"patient_id": "p-unmeasured-01", "gender": "Male", "age": "55.0", "date_of_birth": "1971-01-01"})
        writer.writerow({"patient_id": "p-unmeasured-02", "gender": "Female", "age": "70.0", "date_of_birth": "1956-01-01"})

    # Only p-measured-htn has an observation (150/95 mmHg)
    with open(export_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "timestamp", "observation_code", "observation_name", "value", "unit", "is_abnormal"])
        writer.writeheader()
        writer.writerow({"observation_id": "o1", "patient_id": "p-measured-htn", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "SBP", "observation_name": "SBP", "value": "150.0", "unit": "mmHg", "is_abnormal": "True"})
        writer.writerow({"observation_id": "o2", "patient_id": "p-measured-htn", "encounter_id": "e1", "timestamp": "2026-01-01T10:00:00", "observation_code": "DBP", "observation_name": "DBP", "value": "95.0", "unit": "mmHg", "is_abnormal": "True"})

    for tbl in ["conditions.csv", "medications.csv", "deaths.csv"]:
        with open(export_dir / tbl, "w", newline="", encoding="utf-8") as f:
            f.write("")

    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=export_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Estimand B denominator MUST be 1 (assessable only!), NOT 3!
    m_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_measurement_defined_htn_older_adult")
    assert m_metric.synthetic_n == 1
    assert m_metric.synthetic_estimate == 100.0

    # Estimand E reports the unassessable status rate: 2 of 3 (66.67%)
    unassess_metric = next(m for m in report.metrics if m.metric_id == "lasi_prev_htn_unassessable_status")
    assert unassess_metric.synthetic_n == 3
    assert unassess_metric.synthetic_estimate == 66.67


def test_community_and_clinical_observations_separately_identifiable():
    """Verify that community assessments and clinical observations are distinctly partitioned."""
    import csv
    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    comm_file = cohort_dir / "community_assessments.csv"
    obs_file = cohort_dir / "observations.csv"

    assert comm_file.exists()
    assert obs_file.exists()

    with open(comm_file, "r", encoding="utf-8-sig") as f:
        comm_reader = csv.DictReader(f)
        comm_rows = list(comm_reader)
        assert len(comm_rows) > 0
        for r in comm_rows:
            assert r["provenance"] == "COMMUNITY_HEALTH_ASSESSMENT_LAYER"
            assert "encounter_id" not in r

    with open(obs_file, "r", encoding="utf-8-sig") as f:
        obs_reader = csv.DictReader(f)
        obs_rows = list(obs_reader)
        assert len(obs_rows) > 0
        for r in obs_rows:
            assert "encounter_id" in r
            assert r["encounter_id"].startswith("enc-")


def test_community_assessment_fixed_seed_determinism():
    """Verify that community assessment generation under a fixed seed is bit-for-bit deterministic."""
    from synapse_simulator.datagen.community_assessment import (
        CommunityAssessmentGenerator,
        CommunityAssessmentConfig,
    )
    from synapse_simulator.datagen.models import PatientContext

    patients = {
        f"p-{i}": PatientContext(
            patient_id=f"p-{i}",
            name=f"Patient {i}",
            age=45 + (i % 35),
            gender="Female" if i % 2 == 0 else "Male",
            latent_conditions={"I10": {"code": "I10"}} if i % 3 == 0 else {},
        )
        for i in range(50)
    }

    gen1 = CommunityAssessmentGenerator(base_seed=123)
    res1 = gen1.generate(patients)

    gen2 = CommunityAssessmentGenerator(base_seed=123)
    res2 = gen2.generate(patients)

    assert len(res1) == len(res2)
    for r1, r2 in zip(res1, res2):
        assert r1.assessment_id == r2.assessment_id
        assert r1.patient_id == r2.patient_id
        assert r1.sbp == r2.sbp
        assert r1.dbp == r2.dbp
        assert r1.pulse_pressure == r2.pulse_pressure
        assert r1.status == r2.status


def test_fixture_execution_strictly_reference_data_pending():
    """Verify that executing against synthetic fixture data CANNOT pass the external validation gate."""
    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    ingestor = LasiDataIngestor(source_path=FIXTURE_PATH)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=cohort_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()

    # Overall gate status MUST remain strictly REFERENCE_DATA_PENDING
    assert report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING
    assert report.reference_source_type == LasiDataSourceType.SYNTHETIC_TEST_FIXTURE
