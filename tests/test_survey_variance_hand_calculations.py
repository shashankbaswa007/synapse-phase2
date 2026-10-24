"""
Synthetic Mathematical Verification Tests for Complex Survey Variance Estimation.

Milestone 4 Verification:
1. Exact hand-calculated benchmark for Taylor series linearized weighted mean.
2. Exact hand-calculated benchmark for Taylor series linearized proportion with Wald and logit CIs.
3. Verification of singleton PSU strategies (CERTAINTY, GRAND_MEAN_CENTERING, COLLAPSE_STRATA).
4. Edge condition: singleton PSU at the end of the stratum list.
5. Finite Population Correction (FPC) factor validation.
6. Degrees of freedom and Student's t multiplier vs fixed normal approximation.
7. Insufficient degrees of freedom (df <= 0) handling.
8. Additive survey sampling variance and simulation Monte Carlo variance with Welch-Satterthwaite df.
9. Handling of missing design fields and non-positive survey weights.
"""

import math
import pytest
from typing import List

from synapse_simulator.evaluation.lasi.models import LasiCleanedRecord
from synapse_simulator.evaluation.lasi.variance import (
    LasiSurveyVarianceEngine,
    SingletonHandlingStrategy,
    student_t_critical_value,
    _norm_ppf,
)


def _build_test_record(
    pid: str,
    val: float,
    weight: float,
    strata: str,
    psu: str,
) -> LasiCleanedRecord:
    """Helper to construct synthetic LasiCleanedRecord for mathematical benchmarking."""
    return LasiCleanedRecord(
        participant_id=pid,
        household_id=f"hh_{psu}",
        state="State_X",
        urban_rural="Rural",
        survey_weight=weight,
        strata=strata,
        psu=psu,
        age=65.0,
        gender="Female",
        sbp_mean=val,
        dbp_mean=80.0,
        biomarker_participated=True,
        bp_participated=True,
        hba1c_participated=True,
        has_valid_survey_weight=(weight is not None and weight > 0.0),
    )


# =============================================================================
# 1. Exact Hand-Calculated Weighted Mean Benchmark
# =============================================================================

def test_hand_calculated_weighted_mean_benchmark():
    """Verify Taylor series linearized mean against exact rational arithmetic hand calculations.

    Design:
        - Stratum 1:
            - PSU 11: Obs 1 (y=120, w=2), Obs 2 (y=140, w=3) -> y_11=660, w_11=5
            - PSU 12: Obs 3 (y=130, w=4), Obs 4 (y=150, w=1) -> y_12=670, w_12=5
        - Stratum 2:
            - PSU 21: Obs 5 (y=110, w=5), Obs 6 (y=160, w=5) -> y_21=1350, w_21=10
            - PSU 22: Obs 7 (y=136, w=10)                     -> y_22=1360, w_22=10

    Exact Quantities:
        Total weight N = 30
        Weighted sum Y = 4040
        Weighted mean = 4040 / 30 = 404 / 3 = 134.6667
        Linearized PSU residuals:
            z_11 = (660 - 5 * (404/3)) / 30 = -4/9
            z_12 = (670 - 5 * (404/3)) / 30 = -1/9
            z_21 = (1350 - 10 * (404/3)) / 30 = 1/9
            z_22 = (1360 - 10 * (404/3)) / 30 = 4/9
            Sum of all z = 0
        Stratum 1:
            z_bar_1 = -5/18
            Var_1 = 2 * [(-1/6)^2 + (1/6)^2] = 2 * (1/18) = 1/9
        Stratum 2:
            z_bar_2 = 5/18
            Var_2 = 2 * [(-1/6)^2 + (1/6)^2] = 2 * (1/18) = 1/9
        Total Taylor Variance = 1/9 + 1/9 = 2/9 approx 0.222222
        Standard Error = sqrt(2/9) = sqrt(2)/3 approx 0.471405
        Degrees of Freedom = K - H = 4 - 2 = 2
        Student's t(df=2, 0.975) = 4.302653
        95% CI Half Width = 4.302653 * (sqrt(2)/3) = 2.0283
    """
    records = [
        # Stratum 1, PSU 1
        _build_test_record("p1", val=120.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=140.0, weight=3.0, strata="S1", psu="P11"),
        # Stratum 1, PSU 2
        _build_test_record("p3", val=130.0, weight=4.0, strata="S1", psu="P12"),
        _build_test_record("p4", val=150.0, weight=1.0, strata="S1", psu="P12"),
        # Stratum 2, PSU 3
        _build_test_record("p5", val=110.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=160.0, weight=5.0, strata="S2", psu="P21"),
        # Stratum 2, PSU 4
        _build_test_record("p7", val=136.0, weight=10.0, strata="S2", psu="P22"),
    ]

    engine = LasiSurveyVarianceEngine()
    mean_val, se, tel = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
        confidence=0.95,
    )

    # 1. Verify weighted mean
    expected_mean = 404.0 / 3.0
    assert math.isclose(mean_val, round(expected_mean, 4), abs_tol=1e-4)

    # 2. Verify total Taylor linearized variance and standard error
    expected_var = 2.0 / 9.0
    expected_se = math.sqrt(expected_var)
    assert math.isclose(tel["survey_variance"], expected_var, abs_tol=1e-5)
    assert math.isclose(se, round(expected_se, 4), abs_tol=1e-4)

    # 3. Verify degrees of freedom (df = 4 PSUs - 2 Strata = 2)
    assert tel["df"] == 2
    assert tel["total_strata"] == 2
    assert tel["total_psus"] == 4

    # 4. Verify Student's t multiplier for df=2 (4.3027 vs normal 1.960)
    assert math.isclose(tel["t_multiplier"], 4.3027, abs_tol=1e-4)
    expected_half_width = 4.302653 * expected_se
    assert math.isclose(tel["ci_half_width"], round(expected_half_width, 4), abs_tol=1e-4)

    # 5. Verify confidence interval bounds
    assert math.isclose(tel["ci_lower"], round(expected_mean - expected_half_width, 4), abs_tol=1e-4)
    assert math.isclose(tel["ci_upper"], round(expected_mean + expected_half_width, 4), abs_tol=1e-4)

    # 6. Verify warning about low df < 12
    assert any("Sparse design degrees of freedom (df = 2 < 12)" in w for w in tel["diagnostic_warnings"])


# =============================================================================
# 2. Exact Hand-Calculated Weighted Proportion Benchmark & Logit CI
# =============================================================================

def test_hand_calculated_weighted_proportion_and_logit_ci():
    """Verify Taylor series linearized proportion with Wald and logit-transformed intervals.

    Design: Same 4 PSUs in 2 Strata, binary indicator y in {0, 1}.
        - Stratum 1:
            - PSU 11: Obs 1 (y=1, w=2), Obs 2 (y=0, w=3) -> y_11=2, w_11=5
            - PSU 12: Obs 3 (y=1, w=4), Obs 4 (y=0, w=1) -> y_12=4, w_12=5
        - Stratum 2:
            - PSU 21: Obs 5 (y=0, w=5), Obs 6 (y=1, w=5) -> y_21=5, w_21=10
            - PSU 22: Obs 7 (y=0, w=10)                    -> y_22=0, w_22=10

    Exact Quantities:
        N = 30, Y = 11 positive cases
        Weighted proportion p_w = 11 / 30 = 0.3667
        Stratum 1 variance = 1 / 225 = 0.004444
        Stratum 2 variance = 1 / 36 = 0.027778
        Total Taylor variance = 29 / 900 = 0.032222
        Standard error = sqrt(29)/30 approx 0.179505
        df = 2, t_crit = 4.302653
        Wald CI = 0.3667 +/- 4.302653 * 0.179505 = [-0.4057, 1.1390] (VIOLATES [0, 1] BOUNDS!)
        Logit CI:
            eta = ln(11 / 19) = -0.54654
            SE(eta) = (sqrt(29)/30) / [(11/30)(19/30)] = 0.77300
            Half width on logit scale = 4.302653 * 0.77300 = 3.3260
            eta_bounds = [-3.8725, 2.7795]
            p_L = 1 / (1 + exp(3.8725)) approx 0.0204
            p_U = 1 / (1 + exp(-2.7795)) approx 0.9416 (STRICTLY WITHIN [0, 1]!)
    """
    records = [
        _build_test_record("p1", val=1.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=0.0, weight=3.0, strata="S1", psu="P11"),
        _build_test_record("p3", val=1.0, weight=4.0, strata="S1", psu="P12"),
        _build_test_record("p4", val=0.0, weight=1.0, strata="S1", psu="P12"),
        _build_test_record("p5", val=0.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=1.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p7", val=0.0, weight=10.0, strata="S2", psu="P22"),
    ]

    engine = LasiSurveyVarianceEngine()
    p_w, se, tel = engine.calculate_taylor_linearized_proportion_and_se(
        records=records,
        indicator_getter=lambda r: (r.sbp_mean == 1.0),
        confidence=0.95,
    )

    # 1. Verify weighted proportion
    expected_p = 11.0 / 30.0
    assert math.isclose(p_w, round(expected_p, 4), abs_tol=1e-4)

    # 2. Verify total Taylor linearized variance and SE
    expected_var = 29.0 / 900.0
    expected_se = math.sqrt(expected_var)
    assert math.isclose(tel["survey_variance"], expected_var, abs_tol=1e-5)
    assert math.isclose(se, round(expected_se, 4), abs_tol=1e-4)

    # 3. Verify Wald interval violates probability bounds due to small df
    wald_low, wald_high = tel["wald_ci"]
    assert wald_low < 0.0, "Wald lower bound should be negative with small df and large SE"
    assert wald_high > 1.0, "Wald upper bound should exceed 1.0"
    assert math.isclose(wald_low, -0.4057, abs_tol=1e-3)
    assert math.isclose(wald_high, 1.1390, abs_tol=1e-3)

    # 4. Verify Logit-transformed interval strictly respects [0, 1] bounds
    logit_low, logit_high = tel["logit_ci"]
    assert 0.0 < logit_low < p_w < logit_high < 1.0
    assert math.isclose(logit_low, 0.0204, abs_tol=1e-3)
    assert math.isclose(logit_high, 0.9416, abs_tol=1e-3)


# =============================================================================
# 3. Singleton PSU Strategy Verification & Comparative Audit
# =============================================================================

def test_singleton_psu_strategies_and_certainty_warning():
    """Verify CERTAINTY, GRAND_MEAN_CENTERING, and COLLAPSE_STRATA behavior."""
    # Base dataset (2 strata, 4 PSUs) plus a 3rd singleton stratum (Stratum S3, 1 PSU)
    records = [
        _build_test_record("p1", val=120.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=140.0, weight=3.0, strata="S1", psu="P11"),
        _build_test_record("p3", val=130.0, weight=4.0, strata="S1", psu="P12"),
        _build_test_record("p4", val=150.0, weight=1.0, strata="S1", psu="P12"),
        _build_test_record("p5", val=110.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=160.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p7", val=136.0, weight=10.0, strata="S2", psu="P22"),
        # Singleton Stratum S3: 1 observation
        _build_test_record("p8", val=170.0, weight=10.0, strata="S3", psu="P31"),
    ]

    # 1. CERTAINTY Strategy
    engine_cert = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.CERTAINTY)
    mean_cert, se_cert, tel_cert = engine_cert.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    assert tel_cert["singleton_strata_count"] == 1
    # Verify safety warning emitted for certainty default
    assert any("CERTAINTY strategy assumes singleton PSUs were sampled with certainty" in w for w in tel_cert["diagnostic_warnings"])

    # 2. GRAND_MEAN_CENTERING Strategy
    engine_center = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.GRAND_MEAN_CENTERING)
    mean_center, se_center, tel_center = engine_center.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    assert tel_center["singleton_strata_count"] == 1
    # Centering singleton around sample grand mean (0) must contribute strictly positive variance
    assert tel_center["survey_variance"] > tel_cert["survey_variance"]
    assert se_center > se_cert

    # 3. COLLAPSE_STRATA Strategy
    engine_col = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.COLLAPSE_STRATA)
    mean_col, se_col, tel_col = engine_col.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    # After collapsing, no singleton strata remain
    assert tel_col["singleton_strata_count"] == 0
    assert tel_col["total_strata"] == 2  # S1, and merged S2+S3
    assert tel_col["df"] == 3            # 5 effective PSUs - 2 Strata = 3 df


def test_singleton_psu_at_end_of_stratum_list_collapsing():
    """Verify bug fix: singleton stratum at the end of the sorted stratum list collapses into previous stratum."""
    records = [
        # Stratum A: 2 PSUs
        _build_test_record("p1", val=120.0, weight=1.0, strata="Stratum_A", psu="P_A1"),
        _build_test_record("p2", val=130.0, weight=1.0, strata="Stratum_A", psu="P_A2"),
        # Stratum B: 2 PSUs
        _build_test_record("p3", val=140.0, weight=1.0, strata="Stratum_B", psu="P_B1"),
        _build_test_record("p4", val=150.0, weight=1.0, strata="Stratum_B", psu="P_B2"),
        # Stratum Z (last alphabetically): 1 PSU (Singleton!)
        _build_test_record("p5", val=160.0, weight=1.0, strata="Stratum_Z", psu="P_Z1"),
    ]

    engine = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.COLLAPSE_STRATA)
    _, _, tel = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )

    # Crucial test: Stratum_Z must have been collapsed with Stratum_B!
    assert tel["singleton_strata_count"] == 0, "Last stratum singleton was not collapsed!"
    assert tel["total_strata"] == 2
    assert tel["total_psus"] == 5
    assert tel["df"] == 3


# =============================================================================
# 4. Finite Population Correction (FPC) Factor Validation
# =============================================================================

def test_finite_population_correction_reduces_variance():
    """Verify that finite population correction factors (1 - f_h) scale stratum variance appropriately."""
    records = [
        _build_test_record("p1", val=120.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=140.0, weight=3.0, strata="S1", psu="P11"),
        _build_test_record("p3", val=130.0, weight=4.0, strata="S1", psu="P12"),
        _build_test_record("p4", val=150.0, weight=1.0, strata="S1", psu="P12"),
        _build_test_record("p5", val=110.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=160.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p7", val=136.0, weight=10.0, strata="S2", psu="P22"),
    ]

    engine = LasiSurveyVarianceEngine()

    # Without FPC: f_h = 0.0 -> total variance = 2/9 approx 0.222222
    _, se_no_fpc, tel_no_fpc = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )

    # With FPC: f_1 = 0.5 (50% sampled in S1), f_2 = 0.5 (50% sampled in S2)
    # Variance should be exactly scaled by 0.5: 0.222222 * 0.5 = 0.111111
    fpc_dict = {"S1": 0.5, "S2": 0.5}
    _, se_with_fpc, tel_with_fpc = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
        fpc_by_stratum=fpc_dict,
    )

    expected_fpc_var = tel_no_fpc["survey_variance"] * 0.5
    assert math.isclose(tel_with_fpc["survey_variance"], expected_fpc_var, abs_tol=1e-5)
    assert math.isclose(se_with_fpc, math.sqrt(expected_fpc_var), abs_tol=1e-4)
    assert se_with_fpc < se_no_fpc


# =============================================================================
# 5. Degrees of Freedom & Student's t Distribution Accuracy
# =============================================================================

def test_student_t_critical_multipliers():
    """Verify Student's t critical multipliers across various degrees of freedom against NIST benchmarks."""
    # df=1: extreme t=12.706
    assert math.isclose(student_t_critical_value(1, 0.95), 12.706205, abs_tol=1e-4)
    # df=2: t=4.303
    assert math.isclose(student_t_critical_value(2, 0.95), 4.302653, abs_tol=1e-4)
    # df=10: t=2.228
    assert math.isclose(student_t_critical_value(10, 0.95), 2.228139, abs_tol=1e-4)
    # df=30: t=2.042
    assert math.isclose(student_t_critical_value(30, 0.95), 2.042272, abs_tol=1e-4)
    # df=60 (Hill's expansion): approx 2.0003
    assert math.isclose(student_t_critical_value(60, 0.95), 2.000298, abs_tol=1e-4)
    # df=120: approaches normal 1.960
    assert math.isclose(student_t_critical_value(120, 0.95), 1.959964, abs_tol=1e-3)

    # Invalid df <= 0 raises ValueError
    with pytest.raises(ValueError):
        student_t_critical_value(0, 0.95)
    with pytest.raises(ValueError):
        student_t_critical_value(-5, 0.95)


def test_insufficient_degrees_of_freedom_handling():
    """Verify behavior when sample provides insufficient degrees of freedom (df <= 0)."""
    # 1 Stratum with only 1 PSU: df = 1 - 1 = 0
    records = [
        _build_test_record("p1", val=120.0, weight=1.0, strata="S1", psu="P1"),
        _build_test_record("p2", val=130.0, weight=1.0, strata="S1", psu="P1"),
    ]

    engine = LasiSurveyVarianceEngine()
    mean_val, se, tel = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )

    assert mean_val == 125.0
    assert tel["df"] == 0
    assert tel["insufficient_df"] is True
    assert tel["t_multiplier"] is None
    assert tel["ci_lower"] is None
    assert tel["ci_upper"] is None
    assert any("Insufficient degrees of freedom (df <= 0)" in w for w in tel["diagnostic_warnings"])


# =============================================================================
# 6. Combined Survey Sampling & Simulation Monte Carlo Variance
# =============================================================================

def test_combined_variance_and_welch_satterthwaite_df():
    """Verify combined variance formula and Welch-Satterthwaite effective degrees of freedom."""
    survey_var = 0.50
    sim_var = 1.00
    m_reps = 100
    df_survey = 10

    res = LasiSurveyVarianceEngine.combine_survey_and_monte_carlo_variance(
        survey_var=survey_var,
        sim_variance=sim_var,
        sim_replications_m=m_reps,
        df_survey=df_survey,
        confidence=0.95,
    )

    # Var(diff) = 0.50 + 1.00 / 100 = 0.51
    assert res["total_variance"] == 0.51
    assert res["monte_carlo_variance"] == 0.01
    assert res["survey_variance"] == 0.50

    # Welch-Satterthwaite effective df
    # df_eff = (0.51)^2 / [ (0.50)^2 / 10 + (0.01)^2 / 99 ]
    # denom = 0.25 / 10 + 0.0001 / 99 = 0.025001
    # df_eff = 0.2601 / 0.025001 approx 10.4 -> 10
    assert res["effective_df"] == 10
    # Multiplier uses t_{10, 0.975} = 2.2281
    assert math.isclose(res["multiplier"], 2.2281, abs_tol=1e-4)
    # Check documented independence assumption
    assert "Cov(theta_sim, theta_ref) == 0" in res["independence_assumption"]


# =============================================================================
# 7. Robustness to Missing Fields & Non-Positive Weights
# =============================================================================

def test_missing_design_fields_and_invalid_weights_filtering():
    """Verify non-positive weights and missing values are safely filtered without crashing."""
    records = [
        # Valid records
        _build_test_record("p1", val=120.0, weight=1.0, strata="S1", psu="P1"),
        _build_test_record("p2", val=130.0, weight=1.0, strata="S1", psu="P2"),
        # Zero weight: excluded
        _build_test_record("p3", val=140.0, weight=0.0, strata="S1", psu="P1"),
        # None weight: excluded
        _build_test_record("p4", val=150.0, weight=None, strata="S1", psu="P2"),
        # NaN value: excluded
        _build_test_record("p5", val=float("nan"), weight=1.0, strata="S1", psu="P1"),
        # None value: excluded
        _build_test_record("p6", val=None, weight=1.0, strata="S1", psu="P2"),
    ]

    engine = LasiSurveyVarianceEngine()
    mean_val, se, tel = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )

    # Only p1 and p2 should be included
    assert tel["n_valid_observations"] == 2
    assert mean_val == 125.0
    assert tel["weighted_sum"] == 2.0


# =============================================================================
# 8. Additional Boundary Regression Tests
# =============================================================================

def test_consecutive_singletons_multi_strata_collapsing():
    """Verify collapsing when 3 consecutive strata are singletons, collapsing into 1 stratum with df=2."""
    records = [
        _build_test_record("p1", val=120.0, weight=1.0, strata="S1", psu="P1"),
        _build_test_record("p2", val=140.0, weight=1.0, strata="S2", psu="P2"),
        _build_test_record("p3", val=160.0, weight=1.0, strata="S3", psu="P3"),
    ]

    engine = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.COLLAPSE_STRATA)
    mean_val, se, tel = engine.calculate_taylor_linearized_mean_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )

    assert mean_val == 140.0
    assert tel["singleton_strata_count"] == 0
    assert tel["total_strata"] == 1
    assert tel["total_psus"] == 3
    assert tel["df"] == 2
    # Exact rational variance: 400 / 3 = 133.33333333333331
    expected_var = 400.0 / 3.0
    assert math.isclose(tel["survey_variance"], expected_var, abs_tol=1e-5)
    assert math.isclose(se, math.sqrt(expected_var), abs_tol=1e-4)


def test_student_t_confidence_input_validation():
    """Verify student_t_critical_value rejects invalid confidence levels outside (0, 1)."""
    with pytest.raises(ValueError, match="Confidence must be strictly between 0 and 1"):
        student_t_critical_value(10, confidence=0.0)
    with pytest.raises(ValueError, match="Confidence must be strictly between 0 and 1"):
        student_t_critical_value(10, confidence=1.0)
    with pytest.raises(ValueError, match="Confidence must be strictly between 0 and 1"):
        student_t_critical_value(10, confidence=1.5)
    with pytest.raises(ValueError, match="Confidence must be strictly between 0 and 1"):
        student_t_critical_value(10, confidence=-0.05)


def test_proportion_boundary_conditions_and_type_validation():
    """Verify proportions at p=0 and p=1 return valid bounded CIs, and invalid types raise ValueError."""
    # All 0s
    records_zero = [
        _build_test_record("p1", val=0.0, weight=1.0, strata="S1", psu="P1"),
        _build_test_record("p2", val=0.0, weight=1.0, strata="S1", psu="P2"),
    ]
    engine = LasiSurveyVarianceEngine()
    p_zero, _, tel_zero = engine.calculate_taylor_linearized_proportion_and_se(
        records=records_zero,
        indicator_getter=lambda r: r.sbp_mean,
    )
    assert p_zero == 0.0
    assert tel_zero["logit_ci"] == (0.0, 0.0)

    # All 1s
    records_one = [
        _build_test_record("p1", val=1.0, weight=1.0, strata="S1", psu="P1"),
        _build_test_record("p2", val=1.0, weight=1.0, strata="S1", psu="P2"),
    ]
    p_one, _, tel_one = engine.calculate_taylor_linearized_proportion_and_se(
        records=records_one,
        indicator_getter=lambda r: r.sbp_mean,
    )
    assert p_one == 1.0
    assert tel_one["logit_ci"] == (1.0, 1.0)

    # Non-binary indicator value (e.g. 2.0 or string) raises ValueError
    records_invalid = [
        _build_test_record("p1", val=2.0, weight=1.0, strata="S1", psu="P1"),
    ]
    with pytest.raises(ValueError, match="Indicator value must be binary"):
        engine.calculate_taylor_linearized_proportion_and_se(
            records=records_invalid,
            indicator_getter=lambda r: r.sbp_mean,
        )

    records_string = [
        _build_test_record("p1", val=1.0, weight=1.0, strata="S1", psu="P1"),
    ]
    with pytest.raises(ValueError, match="Unsupported indicator type"):
        engine.calculate_taylor_linearized_proportion_and_se(
            records=records_string,
            indicator_getter=lambda r: "YES",
        )


# =============================================================================
# 11. Exact Hand-Calculated Weighted Total Benchmarks
# =============================================================================

def test_hand_calculated_weighted_total_benchmark():
    """Verify Taylor linearized complex survey total against exact rational arithmetic hand calculations.

    Design:
        - Stratum 1:
            - PSU 11: Obs 1 (y=120, w=2), Obs 2 (y=140, w=3) -> Y_11 = 660
            - PSU 12: Obs 3 (y=130, w=4), Obs 4 (y=150, w=1) -> Y_12 = 670
        - Stratum 2:
            - PSU 21: Obs 5 (y=110, w=5), Obs 6 (y=160, w=5) -> Y_21 = 1350
            - PSU 22: Obs 7 (y=136, w=10)                     -> Y_22 = 1360

    Exact Quantities:
        Total Y = 660 + 670 + 1350 + 1360 = 4040.0
        Stratum 1:
            Y_bar_1 = (660 + 670) / 2 = 665.0
            Var_1 = (2 / 1) * [(660 - 665)^2 + (670 - 665)^2] = 2 * (25 + 25) = 100.0
        Stratum 2:
            Y_bar_2 = (1350 + 1360) / 2 = 1355.0
            Var_2 = (2 / 1) * [(1350 - 1355)^2 + (1360 - 1355)^2] = 2 * (25 + 25) = 100.0
        Total Variance = 100.0 + 100.0 = 200.0
        Standard Error = sqrt(200) = 14.1421356...
        Degrees of Freedom = 4 - 2 = 2
        t_0.95(df=2) = 4.302653
        Half-width = 4.302653 * 14.1421356 = 60.8487
        95% CI = [3979.1513, 4100.8487]
    """
    records = [
        # Stratum 1, PSU 1
        _build_test_record("p1", val=120.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=140.0, weight=3.0, strata="S1", psu="P11"),
        # Stratum 1, PSU 2
        _build_test_record("p3", val=130.0, weight=4.0, strata="S1", psu="P12"),
        _build_test_record("p4", val=150.0, weight=1.0, strata="S1", psu="P12"),
        # Stratum 2, PSU 3
        _build_test_record("p5", val=110.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=160.0, weight=5.0, strata="S2", psu="P21"),
        # Stratum 2, PSU 4
        _build_test_record("p7", val=136.0, weight=10.0, strata="S2", psu="P22"),
    ]

    engine = LasiSurveyVarianceEngine()
    total_y, se, tel = engine.calculate_taylor_linearized_total_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )

    assert total_y == 4040.0
    assert math.isclose(tel["survey_variance"], 200.0, abs_tol=1e-5)
    assert math.isclose(se, math.sqrt(200.0), abs_tol=1e-4)
    assert tel["df"] == 2
    assert math.isclose(tel["t_multiplier"], 4.3027, abs_tol=1e-4)
    assert math.isclose(tel["ci_half_width"], 60.8487, abs_tol=1e-3)
    assert math.isclose(tel["ci_lower"], 3979.1513, abs_tol=1e-3)
    assert math.isclose(tel["ci_upper"], 4100.8487, abs_tol=1e-3)


def test_weighted_total_with_fpc():
    """Verify weighted total variance with stratum-specific FPC factors."""
    records = [
        _build_test_record("p1", val=120.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=140.0, weight=3.0, strata="S1", psu="P11"),
        _build_test_record("p3", val=130.0, weight=4.0, strata="S1", psu="P12"),
        _build_test_record("p4", val=150.0, weight=1.0, strata="S1", psu="P12"),
        _build_test_record("p5", val=110.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=160.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p7", val=136.0, weight=10.0, strata="S2", psu="P22"),
    ]

    # f_1 = 0.20 -> (1 - f_1) = 0.80 -> Var_1 = 0.80 * 100.0 = 80.0
    # f_2 = 0.10 -> (1 - f_2) = 0.90 -> Var_2 = 0.90 * 100.0 = 90.0
    # Total Var = 170.0 -> SE = sqrt(170) approx 13.0384
    engine = LasiSurveyVarianceEngine()
    total_y, se, tel = engine.calculate_taylor_linearized_total_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
        fpc_by_stratum={"S1": 0.20, "S2": 0.10},
    )

    assert total_y == 4040.0
    assert math.isclose(tel["survey_variance"], 170.0, abs_tol=1e-5)
    assert math.isclose(se, math.sqrt(170.0), abs_tol=1e-4)


def test_weighted_total_singleton_strategies():
    """Verify singleton PSU handling for totals under CERTAINTY and GRAND_MEAN_CENTERING."""
    # S1 has only 1 PSU: Y_11 = 660.0
    # S2 has 2 PSUs: Y_21 = 1350.0, Y_22 = 1360.0
    records = [
        _build_test_record("p1", val=120.0, weight=2.0, strata="S1", psu="P11"),
        _build_test_record("p2", val=140.0, weight=3.0, strata="S1", psu="P11"),
        _build_test_record("p5", val=110.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p6", val=160.0, weight=5.0, strata="S2", psu="P21"),
        _build_test_record("p7", val=136.0, weight=10.0, strata="S2", psu="P22"),
    ]

    # Under CERTAINTY: Var_1 = 0.0, Var_2 = 100.0 -> Total Var = 100.0
    eng_cert = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.CERTAINTY)
    _, se_cert, tel_cert = eng_cert.calculate_taylor_linearized_total_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    assert math.isclose(tel_cert["survey_variance"], 100.0, abs_tol=1e-5)
    assert tel_cert["singleton_strata_count"] == 1

    # Under GRAND_MEAN_CENTERING:
    # Grand mean center: Y_bar_psu = (660 + 1350 + 1360) / 3 = 3370 / 3 = 1123.333333
    # Var_1 = (660 - 1123.333333)^2 = (-463.333333)^2 = 214677.777778
    # Var_2 = 100.0
    # Total Var = 214677.777778 + 100.0 = 214777.777778
    eng_gmc = LasiSurveyVarianceEngine(singleton_strategy=SingletonHandlingStrategy.GRAND_MEAN_CENTERING)
    _, se_gmc, tel_gmc = eng_gmc.calculate_taylor_linearized_total_and_se(
        records=records,
        value_getter=lambda r: r.sbp_mean,
    )
    expected_var = (660.0 - 3370.0 / 3.0) ** 2 + 100.0
    assert math.isclose(tel_gmc["survey_variance"], expected_var, abs_tol=1e-3)
