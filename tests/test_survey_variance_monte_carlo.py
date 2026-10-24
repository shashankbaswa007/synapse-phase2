"""
Reproducible Synthetic Monte Carlo Experiments and Regression Tests for Survey Variance Verification.

Implements Milestone 4 Phase 2D.11 Verification:
1. Monte Carlo simulation against known finite population truth (Totals, Ratio Means, Proportions).
2. Verification of Horvitz-Thompson unbiasedness under SRSWOR cluster partitioning.
3. Verification of Taylor series linearization variance estimator unbiasedness and Monte Carlo error.
4. Design-based confidence interval coverage (Wald and Logit CIs) meeting nominal 95% levels.
5. Mathematical disproof and regression tests for failure modes of the 1 / p_k variance scaling claim:
   - Counterexample A: Finite Population Correction (FPC) inflation.
   - Counterexample B: Integer rounding and unequal stratum sizes (n_h in {4, 5, 6}).
   - Counterexample C: Student's t critical multiplier expansion under small degrees of freedom.
   - Counterexample D: Cluster size dispersion inflating totals vs ratio cancellation dampening means.
"""

import math
from typing import Dict, List, Tuple
import numpy as np
import pytest

import itertools
from synapse_simulator.evaluation.lasi.models import LasiCleanedRecord
from synapse_simulator.evaluation.lasi.partitioner import (
    LasiPsuPartitioner,
    LasiPartitionConfig,
    PartitionLabel,
)
from synapse_simulator.evaluation.lasi.variance import (
    LasiSurveyVarianceEngine,
    SingletonHandlingStrategy,
    student_t_critical_value,
)


def _generate_synthetic_population(
    H: int = 6,
    N_h_pop: int = 40,
    sigma_cluster: float = 5.0,
    sigma_unit: float = 12.0,
    seed: int = 2026,
) -> Tuple[List[dict], Dict[str, float]]:
    """Generate a finite superpopulation with known universe truth."""
    rng = np.random.default_rng(seed)
    pop_units = []

    for h in range(H):
        stratum_mu = 118.0 + 3.0 * h
        p_logit_base = -0.9 + 0.15 * h

        for i in range(N_h_pop):
            # Cluster size M_hi between 40 and 200 (CV ~ 0.50)
            M_hi = int(np.clip(np.round(rng.lognormal(mean=4.6, sigma=0.45)), 35, 220))
            alpha_i = float(rng.normal(0, sigma_cluster))
            p_cluster = float(1.0 / (1.0 + np.exp(-(p_logit_base + rng.normal(0, 0.35)))))

            sbp_vals = stratum_mu + alpha_i + rng.normal(0, sigma_unit, size=M_hi)
            htn_vals = (rng.random(size=M_hi) < p_cluster).astype(float)

            for j in range(M_hi):
                pop_units.append({
                    "stratum": f"S{h}",
                    "psu": f"S{h}_P{i}",
                    "sbp": float(sbp_vals[j]),
                    "htn": float(htn_vals[j]),
                    "M_hi": M_hi,
                })

    N_true = float(len(pop_units))
    Y_true_sbp = float(sum(u["sbp"] for u in pop_units))
    Mean_true_sbp = Y_true_sbp / N_true
    Prop_true_htn = float(sum(u["htn"] for u in pop_units)) / N_true

    truth = {
        "N_true": N_true,
        "total_sbp": Y_true_sbp,
        "mean_sbp": Mean_true_sbp,
        "prop_htn": Prop_true_htn,
    }
    return pop_units, truth


def test_monte_carlo_survey_variance_and_ci_coverage():
    """Verify Taylor linearization and CI coverage against known population truth over B=400 draws.

    Validates:
    - Relative bias of point estimators (|Bias| < 1.0%)
    - Variance estimator relative bias (|RelBias(Var)| < 15.0%, within MCSE ~ 7%)
    - 95% Confidence Interval empirical coverage in [92.0%, 98.0%]
    """
    H = 4
    N_h_pop = 30
    n_h = 5  # 5 PSUs per stratum: Partition A gets 3, Partition C gets 2
    m_sample = 20
    B = 400
    seed = 2026

    pop_units, truth = _generate_synthetic_population(
        H=H, N_h_pop=N_h_pop, seed=seed
    )

    # Group population by (stratum, psu)
    psu_lookup = {}
    for u in pop_units:
        key = (u["stratum"], u["psu"])
        if key not in psu_lookup:
            psu_lookup[key] = []
        psu_lookup[key].append(u)

    engine = LasiSurveyVarianceEngine()
    rng = np.random.default_rng(seed)

    pts_full_mean, vars_full_mean, cov_full_mean = [], [], []
    pts_A_mean, vars_A_mean, cov_A_mean = [], [], []
    pts_C_mean, vars_C_mean, cov_C_mean = [], [], []

    cov_C_logit_prop = []

    for b in range(B):
        # Sample n_h PSUs per stratum
        full_records = []
        for h in range(H):
            s_name = f"S{h}"
            psu_indices = rng.choice(N_h_pop, size=n_h, replace=False)
            for p_idx in psu_indices:
                p_name = f"{s_name}_P{p_idx}"
                units_in_psu = psu_lookup[(s_name, p_name)]
                M_hi = len(units_in_psu)
                act_m = min(m_sample, M_hi)
                sampled_u_idx = rng.choice(M_hi, size=act_m, replace=False)

                # Base Horvitz-Thompson weight: (N_h_pop / n_h) * (M_hi / act_m)
                w = (float(N_h_pop) / float(n_h)) * (float(M_hi) / float(act_m))
                for uj in sampled_u_idx:
                    u = units_in_psu[uj]
                    rec = LasiCleanedRecord(
                        participant_id=f"b{b}_{u['psu']}_{uj}",
                        household_id=f"hh_{u['psu']}",
                        state="TestState",
                        urban_rural="Rural",
                        survey_weight=w,
                        strata=s_name,
                        psu=p_name,
                        age=65.0,
                        gender="Female",
                        sbp_mean=u["sbp"],
                        dbp_mean=80.0,
                        biomarker_participated=True,
                        bp_participated=True,
                        hba1c_participated=True,
                        has_valid_survey_weight=True,
                    )
                    full_records.append(rec)

        # Partition 60/40: n_A = 3, n_C = 2
        A_records, C_records = [], []
        for h in range(H):
            s_name = f"S{h}"
            psus_in_h = list(set(r.psu for r in full_records if r.strata == s_name))
            perm = rng.permutation(psus_in_h)
            set_A = set(perm[:3])
            set_C = set(perm[3:])

            for r in full_records:
                if r.strata == s_name:
                    if r.psu in set_A:
                        r_copy = r.model_copy()
                        r_copy.survey_weight = r.survey_weight * (5.0 / 3.0)
                        A_records.append(r_copy)
                    elif r.psu in set_C:
                        r_copy = r.model_copy()
                        r_copy.survey_weight = r.survey_weight * (5.0 / 2.0)
                        C_records.append(r_copy)

        # Evaluate Full Sample Mean
        m_f, se_f, tel_f = engine.calculate_taylor_linearized_mean_and_se(
            records=full_records, value_getter=lambda r: r.sbp_mean
        )
        pts_full_mean.append(m_f)
        vars_full_mean.append(tel_f["survey_variance"])
        cov_full_mean.append(tel_f["ci_lower"] <= truth["mean_sbp"] <= tel_f["ci_upper"])

        # Evaluate Partition A Mean
        m_A, se_A, tel_A = engine.calculate_taylor_linearized_mean_and_se(
            records=A_records, value_getter=lambda r: r.sbp_mean
        )
        pts_A_mean.append(m_A)
        vars_A_mean.append(tel_A["survey_variance"])
        cov_A_mean.append(tel_A["ci_lower"] <= truth["mean_sbp"] <= tel_A["ci_upper"])

        # Evaluate Partition C Mean
        m_C, se_C, tel_C = engine.calculate_taylor_linearized_mean_and_se(
            records=C_records, value_getter=lambda r: r.sbp_mean
        )
        pts_C_mean.append(m_C)
        vars_C_mean.append(tel_C["survey_variance"])
        cov_C_mean.append(tel_C["ci_lower"] <= truth["mean_sbp"] <= tel_C["ci_upper"])

        # Evaluate Partition C Proportion Logit CI
        p_C, se_pC, tel_pC = engine.calculate_taylor_linearized_proportion_and_se(
            records=C_records, indicator_getter=lambda r: 1.0 if r.sbp_mean > 130.0 else 0.0
        )
        logit_low, logit_high = tel_pC["logit_ci"]
        prop_true = sum(1.0 for u in pop_units if u["sbp"] > 130.0) / len(pop_units)
        cov_C_logit_prop.append(logit_low <= prop_true <= logit_high)

    # 1. Point Estimator Unbiasedness with Exact MCSE
    var_mc_A = float(np.var(pts_A_mean, ddof=1))
    mcse_pt_A = math.sqrt(var_mc_A / B)
    bias_A = float(np.mean(pts_A_mean)) - truth["mean_sbp"]
    rel_bias_A_pct = (bias_A / truth["mean_sbp"]) * 100.0
    mcse_rel_bias_A_pct = (mcse_pt_A / truth["mean_sbp"]) * 100.0

    var_mc_C = float(np.var(pts_C_mean, ddof=1))
    mcse_pt_C = math.sqrt(var_mc_C / B)
    bias_C = float(np.mean(pts_C_mean)) - truth["mean_sbp"]
    rel_bias_C_pct = (bias_C / truth["mean_sbp"]) * 100.0
    mcse_rel_bias_C_pct = (mcse_pt_C / truth["mean_sbp"]) * 100.0

    # Point estimates must be within 2.58 * MCSE of zero bias (p > 0.01)
    assert abs(bias_A) <= 2.58 * mcse_pt_A, (
        f"Partition A point bias {bias_A:.4f} exceeds 2.58*MCSE ({2.58*mcse_pt_A:.4f})"
    )
    assert abs(bias_C) <= 2.58 * mcse_pt_C, (
        f"Partition C point bias {bias_C:.4f} exceeds 2.58*MCSE ({2.58*mcse_pt_C:.4f})"
    )

    # 2. Variance Estimator Relative Bias with Exact Delta-Method MCSE
    # Under SRSWOR at stage 1 without FPC factor passed to variance engine,
    # the engine estimates the with-replacement variance V_0 = V_WOR / (1 - f_h).
    # Since f_{h, A} = n_{h, A} / N_h_pop = 3 / 30 = 0.10, the expected overestimation
    # of the finite population variance is 1 / (1 - 0.10) - 1 = +11.11%.
    # Adjusting for this known theoretical factor recovers unbiasedness:
    mean_var_A = float(np.mean(vars_A_mean))
    fpc_factor_A = 1.0 - (3.0 / float(N_h_pop))  # 0.90
    mean_var_A_fpc_adjusted = mean_var_A * fpc_factor_A

    # Delta-method MCSE for variance difference: d_b = v_b * fpc - (theta_b - theta_bar)^2
    d_b = np.array(vars_A_mean) * fpc_factor_A - (np.array(pts_A_mean) - np.mean(pts_A_mean))**2
    s_d = float(np.std(d_b, ddof=1))
    mcse_rel_var_bias = (s_d / (math.sqrt(B) * var_mc_A)) * 100.0
    rel_bias_var_fpc = ((mean_var_A_fpc_adjusted - var_mc_A) / var_mc_A) * 100.0

    # The FPC-adjusted variance estimate must be statistically consistent with 0 bias
    assert abs(rel_bias_var_fpc) <= 2.58 * mcse_rel_var_bias, (
        f"FPC-adjusted variance relative bias {rel_bias_var_fpc:+.2f}% exceeds 2.58*MCSE ({2.58*mcse_rel_var_bias:.2f}%)"
    )

    # 3. 95% Confidence Interval Coverage with Exact Binomial MCSE
    cov_rate_full = float(np.mean(cov_full_mean)) * 100.0
    cov_rate_A = float(np.mean(cov_A_mean)) * 100.0
    cov_rate_C = float(np.mean(cov_C_mean)) * 100.0
    cov_rate_C_logit = float(np.mean(cov_C_logit_prop)) * 100.0

    # Binomial standard error for nominal 95% over B draws
    nominal_cov = 95.0
    mcse_cov_nominal = math.sqrt(nominal_cov * (100.0 - nominal_cov) / B)  # ~1.09% for B=400
    ci_margin = 2.58 * mcse_cov_nominal  # 2.81% for 99% MC confidence

    assert (nominal_cov - ci_margin) <= cov_rate_full <= (nominal_cov + ci_margin), (
        f"Full sample coverage {cov_rate_full:.1f}% outside 99% MC interval [{nominal_cov - ci_margin:.1f}, {nominal_cov + ci_margin:.1f}]"
    )
    assert (nominal_cov - ci_margin) <= cov_rate_A <= (nominal_cov + ci_margin), (
        f"Partition A coverage {cov_rate_A:.1f}% outside 99% MC interval [{nominal_cov - ci_margin:.1f}, {nominal_cov + ci_margin:.1f}]"
    )
    assert (nominal_cov - ci_margin) <= cov_rate_C <= (nominal_cov + ci_margin), (
        f"Partition C coverage {cov_rate_C:.1f}% outside 99% MC interval [{nominal_cov - ci_margin:.1f}, {nominal_cov + ci_margin:.1f}]"
    )
    # For small degrees of freedom (df = 4 in Partition C), empirical coverage is nominally ~93-95% (Table 3)
    assert 90.0 <= cov_rate_C_logit <= 98.0, (
        f"Partition C logit coverage {cov_rate_C_logit:.1f}% outside acceptable range [90.0%, 98.0%]"
    )


def test_disproof_counterexample_fpc_violates_scaling():
    """Mathematically demonstrate that FPC causes true variance scaling to depart from 1/p_k.

    When sampling fraction f_h = n_h / N_h > 0:
        Var(Partition k) / Var(Full) = (1 - p_k * f_h) / [p_k * (1 - f_h)] > 1 / p_k
    For f_h = 0.50, p_C = 0.40:
        Nominal 1 / p_C = 2.50x
        Actual True Ratio = (1 - 0.20) / [0.40 * 0.50] = 0.80 / 0.20 = 4.00x (60% higher!)
    """
    f_h = 0.50
    p_A = 0.60
    p_C = 0.40

    nominal_ratio_A = 1.0 / p_A  # 1.6667
    nominal_ratio_C = 1.0 / p_C  # 2.5000

    actual_fpc_ratio_A = (1.0 - p_A * f_h) / (p_A * (1.0 - f_h))
    actual_fpc_ratio_C = (1.0 - p_C * f_h) / (p_C * (1.0 - f_h))

    assert math.isclose(actual_fpc_ratio_A, 2.333333, abs_tol=1e-4)
    assert math.isclose(actual_fpc_ratio_C, 4.000000, abs_tol=1e-4)

    # Percentage by which nominal 1/p_k underestimates true variance
    underestimate_pct_A = (actual_fpc_ratio_A - nominal_ratio_A) / actual_fpc_ratio_A * 100.0
    underestimate_pct_C = (actual_fpc_ratio_C - nominal_ratio_C) / actual_fpc_ratio_C * 100.0

    assert math.isclose(underestimate_pct_A, 28.5714, abs_tol=1e-2)
    assert math.isclose(underestimate_pct_C, 37.5000, abs_tol=1e-2)


def test_disproof_counterexample_integer_rounding_heterogeneity():
    """Demonstrate that integer rounding causes true partition scaling to depart from nominal 60/40.

    When strata have varying PSU counts (e.g. n_h in {4, 5, 6}):
    - For n_h = 4: n_A = 2, n_C = 2 -> p_A = 0.50 (Ratio A = 2.00x != 1.67x)
    - For n_h = 5: n_A = 3, n_C = 2 -> p_A = 0.60, p_C = 0.40 (Ratio A = 1.67x, C = 2.50x)
    - For n_h = 6: n_A = 4, n_C = 2 -> p_C = 0.333 (Ratio C = 3.00x != 2.50x)
    """
    strata_configs = [
        {"n_h": 4, "n_A": 2, "n_C": 2, "exp_ratio_A": 2.000, "exp_ratio_C": 2.000},
        {"n_h": 5, "n_A": 3, "n_C": 2, "exp_ratio_A": 1.667, "exp_ratio_C": 2.500},
        {"n_h": 6, "n_A": 4, "n_C": 2, "exp_ratio_A": 1.500, "exp_ratio_C": 3.000},
    ]

    for cfg in strata_configs:
        p_A = cfg["n_A"] / cfg["n_h"]
        p_C = cfg["n_C"] / cfg["n_h"]
        ratio_A = 1.0 / p_A
        ratio_C = 1.0 / p_C

        assert math.isclose(ratio_A, cfg["exp_ratio_A"], abs_tol=1e-3)
        assert math.isclose(ratio_C, cfg["exp_ratio_C"], abs_tol=1e-3)

    # In a survey with two 4-PSU strata, two 5-PSU strata, and two 6-PSU strata:
    # Total nominal ratio for Partition C in 6-PSU strata is 3.0x, NOT 2.50x.
    assert (1.0 / (2.0 / 6.0)) == 3.0


def test_disproof_counterexample_degrees_of_freedom_ci_expansion():
    """Demonstrate that confidence interval half-width expands by more than sqrt(1/p_k) due to t_df.

    When degrees of freedom are small:
        HalfWidth_ratio = (t_{df_k} / t_{df_full}) * sqrt(1 / p_k)
    For df_full = 4, df_C = 2, and nominal 1/p_C = 2.50 (sqrt = 1.581):
        t_{df=4} = 2.7764
        t_{df=2} = 4.3027
        t multiplier expansion = 4.3027 / 2.7764 = 1.5497
        Total CI width expansion = 1.5497 * 1.5811 = 2.45x (NOT 1.58x!)
    """
    t_df4 = student_t_critical_value(df=4, confidence=0.95)
    t_df2 = student_t_critical_value(df=2, confidence=0.95)

    assert math.isclose(t_df4, 2.776445, abs_tol=1e-5)
    assert math.isclose(t_df2, 4.302653, abs_tol=1e-5)

    sqrt_var_ratio = math.sqrt(2.50)  # 1.5811
    ci_expansion_factor = (t_df2 / t_df4) * sqrt_var_ratio

    # The CI widens by 2.45x, which is 55% wider than the naive sqrt(1/p_k) expectation
    assert math.isclose(ci_expansion_factor, 2.4504, abs_tol=1e-3)
    excess_expansion_pct = (ci_expansion_factor - sqrt_var_ratio) / sqrt_var_ratio * 100.0
    assert math.isclose(excess_expansion_pct, 54.97, abs_tol=1e-1)


def test_totals_vs_ratio_means_cluster_size_dispersion():
    """Demonstrate that cluster size dispersion directly inflates totals while ratio means cancel it.

    Under unequal cluster sizes M_hi:
        Var(Total) = sum n_h^2 (1/n_hk - 1/nh) S^2_Y,h (strongly dependent on M_hi variance)
        Var(Mean)  = sum (1/N^2) [S^2_Y + Y^2 S^2_N - 2Y S_YN] (covariance cancellation)
    """
    # 2 strata, each with 2 PSUs:
    # S1: PSU 1 has M=50, PSU 2 has M=150 (Mean SBP=120 everywhere, zero outcome variance)
    records_zero_outcome_var = [
        # S1, P1 (M=50)
        LasiCleanedRecord(
            participant_id="p1", household_id="h1", state="S", urban_rural="R",
            survey_weight=50.0, strata="S1", psu="P1", age=65.0, gender="F",
            sbp_mean=120.0, dbp_mean=80.0, biomarker_participated=True,
            bp_participated=True, hba1c_participated=True, has_valid_survey_weight=True,
        ),
        # S1, P2 (M=150)
        LasiCleanedRecord(
            participant_id="p2", household_id="h2", state="S", urban_rural="R",
            survey_weight=150.0, strata="S1", psu="P2", age=65.0, gender="F",
            sbp_mean=120.0, dbp_mean=80.0, biomarker_participated=True,
            bp_participated=True, hba1c_participated=True, has_valid_survey_weight=True,
        ),
        # S2, P3 (M=50)
        LasiCleanedRecord(
            participant_id="p3", household_id="h3", state="S", urban_rural="R",
            survey_weight=50.0, strata="S2", psu="P3", age=65.0, gender="F",
            sbp_mean=120.0, dbp_mean=80.0, biomarker_participated=True,
            bp_participated=True, hba1c_participated=True, has_valid_survey_weight=True,
        ),
        # S2, P4 (M=150)
        LasiCleanedRecord(
            participant_id="p4", household_id="h4", state="S", urban_rural="R",
            survey_weight=150.0, strata="S2", psu="P4", age=65.0, gender="F",
            sbp_mean=120.0, dbp_mean=80.0, biomarker_participated=True,
            bp_participated=True, hba1c_participated=True, has_valid_survey_weight=True,
        ),
    ]

    engine = LasiSurveyVarianceEngine()

    # Mean estimator: every individual has sbp = 120.0 -> variance of ratio mean is EXACTLY 0.0
    mean_val, se_mean, tel_mean = engine.calculate_taylor_linearized_mean_and_se(
        records=records_zero_outcome_var, value_getter=lambda r: r.sbp_mean
    )
    assert mean_val == 120.0
    assert math.isclose(tel_mean["survey_variance"], 0.0, abs_tol=1e-9)

    # Total estimator: PSU totals are Y_1 = 50*120 = 6000, Y_2 = 150*120 = 18000
    # Mean PSU total in S1 = 12000. Diff = 6000.
    # Var_1 = (2 / 1) * [(-6000)^2 + (6000)^2] = 2 * (36M + 36M) = 144,000,000!
    # Total variance = 288,000,000!
    tot_val, se_tot, tel_tot = engine.calculate_taylor_linearized_total_and_se(
        records=records_zero_outcome_var, value_getter=lambda r: r.sbp_mean
    )
    assert tot_val == 48000.0
    assert math.isclose(tel_tot["survey_variance"], 288000000.0, abs_tol=1e-3)
    assert math.isclose(se_tot, math.sqrt(288000000.0), abs_tol=1e-3)


def test_first_principles_eves_law_variance_decomposition():
    """Verify Eve's Law decomposition: Var(Y_C) = Var_S(Y_full) + E_S[Var(Y_C | S)].

    Proves that total unconditional partition variance decomposes exactly into:
    1. Original survey sampling variance: Var_S(Y_full)
    2. Expected additional partitioning variance: E_S[Var(Y_C | S)]
    """
    rng = np.random.default_rng(123)
    H = 3
    N_h_pop = 25
    n_h = 5
    n_C = 2
    m_sample = 15
    B_survey = 300

    # Synthetic population
    psus = {}
    for h in range(H):
        for i in range(N_h_pop):
            M = int(rng.integers(40, 120))
            sbp = 120.0 + 4.0 * h + rng.normal(0, 4.0) + rng.normal(0, 8.0, size=M)
            psus[(h, i)] = {"M": M, "sbp": sbp}

    p_C = n_C / n_h  # 0.40
    cond_factor = (1.0 - p_C) / p_C  # 1.50

    y_full_draws = []
    cond_var_C_analytical = []
    unconditional_y_C = []

    for b in range(B_survey):
        psu_Y = {}
        for h in range(H):
            sampled_psu = rng.choice(N_h_pop, size=n_h, replace=False)
            for idx in sampled_psu:
                M_hi = psus[(h, idx)]["M"]
                act_m = min(m_sample, M_hi)
                sampled_u = rng.choice(M_hi, size=act_m, replace=False)
                w = (N_h_pop / n_h) * (M_hi / act_m)
                y_cluster = sum(w * psus[(h, idx)]["sbp"][uj] for uj in sampled_u)
                psu_Y[(h, idx)] = y_cluster

        y_full = sum(psu_Y.values())
        y_full_draws.append(y_full)

        # Analytical conditional partitioning variance for Partition C given this S:
        cond_v_C = 0.0
        for h in range(H):
            y_his = [psu_Y[k] for k in psu_Y if k[0] == h]
            y_bar_h = sum(y_his) / n_h
            s2_h = sum((yi - y_bar_h)**2 for yi in y_his) / (n_h - 1)
            cond_v_C += n_h * cond_factor * s2_h
        cond_var_C_analytical.append(cond_v_C)

        # Realized partition C draw
        y_C_draw = 0.0
        for h in range(H):
            h_psus = [k for k in psu_Y if k[0] == h]
            perm = rng.permutation(len(h_psus))
            c_psus = [h_psus[i] for i in perm[:n_C]]
            y_C_draw += (n_h / n_C) * sum(psu_Y[k] for k in c_psus)
        unconditional_y_C.append(y_C_draw)

    var_survey_emp = float(np.var(y_full_draws, ddof=1))
    mean_cond_var_C = float(np.mean(cond_var_C_analytical))
    var_total_predicted = var_survey_emp + mean_cond_var_C
    var_uncond_emp = float(np.var(unconditional_y_C, ddof=1))

    # Compute exact paired bootstrap SE for the difference Delta = Var_uncond - Var_total_predicted.
    # Because Y_full and Y_C are evaluated on the same survey draw S_b, they covary strongly.
    # Evaluating SE(Delta) directly provides the exact uncertainty of the difference.
    B_boot = 500
    boot_rng = np.random.default_rng(2026)
    indices = boot_rng.choice(B_survey, size=(B_boot, B_survey), replace=True)
    yf_arr = np.array(y_full_draws)
    yc_arr = np.array(unconditional_y_C)
    vc_arr = np.array(cond_var_C_analytical)

    diff_boot = np.var(yc_arr[indices], axis=1, ddof=1) - (
        np.var(yf_arr[indices], axis=1, ddof=1) + np.mean(vc_arr[indices], axis=1)
    )
    se_diff = float(np.std(diff_boot, ddof=1))

    # The predicted sum must match empirical variance within 2.58 * SE(diff)
    discrepancy = abs(var_total_predicted - var_uncond_emp)
    assert discrepancy <= 2.58 * se_diff, (
        f"Eve's Law discrepancy {discrepancy:,.0f} exceeds 2.58*SE(diff) ({2.58*se_diff:,.0f})"
    )


def test_pps_stage1_self_weighting_vs_srswor():
    """Verify design-based properties of PPS sampling at Stage 1 vs SRSWOR.

    Under PPS:
        pi_hi = n_h * M_hi / M_h, pi_j|hi = m / M_hi -> pi_hij = n_h * m / M_h (constant)
        w_hij = M_h / (n_h * m) is self-weighting (CV of weights = 0 within stratum).
    Under SRSWOR:
        pi_hi = n_h / N_h, pi_j|hi = m / M_hi -> w_hij = (N_h M_hi) / (n_h m) proportional to M_hi.
    """
    rng = np.random.default_rng(456)
    H = 2
    N_h_pop = 20
    n_h = 4
    m = 10

    # Build population with unequal cluster sizes
    psus = {}
    strata_M = {}
    for h in range(H):
        M_h = 0
        for i in range(N_h_pop):
            M_hi = int(rng.integers(30, 150))
            M_h += M_hi
            psus[(h, i)] = {
                "M": M_hi,
                "sbp": 125.0 + rng.normal(0, 5.0) + rng.normal(0, 10.0, size=M_hi),
            }
        strata_M[h] = M_h

    # 1. PPS sampling: verify self-weighting
    pps_probs_0 = np.array([psus[(0, i)]["M"] for i in range(N_h_pop)], dtype=float)
    pps_probs_0 /= pps_probs_0.sum()

    sampled_pps = rng.choice(N_h_pop, size=n_h, replace=False, p=pps_probs_0)
    pps_weights = []
    for idx in sampled_pps:
        M_hi = psus[(0, idx)]["M"]
        w = strata_M[0] / (n_h * m)
        for _ in range(m):
            pps_weights.append(w)

    # PPS weights are perfectly uniform: CV = 0.0
    assert math.isclose(float(np.std(pps_weights)), 0.0, abs_tol=1e-9)

    # 2. SRSWOR sampling: verify unequal weights proportional to M_hi
    sampled_srs = rng.choice(N_h_pop, size=n_h, replace=False)
    srs_weights = []
    for idx in sampled_srs:
        M_hi = psus[(0, idx)]["M"]
        w = (N_h_pop / n_h) * (M_hi / m)
        for _ in range(m):
            srs_weights.append(w)

    cv_srs = float(np.std(srs_weights) / np.mean(srs_weights))
    assert cv_srs > 0.20, f"SRSWOR weights should exhibit dispersion, got CV={cv_srs:.3f}"


def test_fpc_exact_calibration_recovers_unbiased_finite_variance():
    """Verify that supplying partition-specific FPC f_{h,k} recovers unbiased finite variance."""
    rng = np.random.default_rng(789)
    H = 3
    N_h_pop = 20
    n_h = 6
    n_A = 4
    n_C = 2
    m = 15
    B = 300

    # Population
    psus = {}
    pop_units = []
    for h in range(H):
        for i in range(N_h_pop):
            M = int(rng.integers(50, 100))
            sbp = 120.0 + 3.0*h + rng.normal(0, 4.0) + rng.normal(0, 8.0, size=M)
            psus[(h, i)] = {"M": M, "sbp": sbp}
            for j in range(M):
                pop_units.append(sbp[j])

    pop_mean = float(np.mean(pop_units))
    engine = LasiSurveyVarianceEngine()

    # Pass exact partition sampling fraction to FPC: f_{h, A} = 4 / 20 = 0.20
    fpc_A_dict = {f"S{h}": n_A / float(N_h_pop) for h in range(H)}

    pts_A = []
    vars_A = []

    for b in range(B):
        recs_A = []
        for h in range(H):
            s_name = f"S{h}"
            sampled_i = rng.choice(N_h_pop, size=n_h, replace=False)
            perm = rng.permutation(sampled_i)
            set_A = perm[:n_A]
            for idx in set_A:
                p_info = psus[(h, idx)]
                M_hi = p_info["M"]
                act_m = min(m, M_hi)
                sampled_u = rng.choice(M_hi, size=act_m, replace=False)
                # HT weight: (N_h / n_h) * (n_h / n_A) * (M_hi / act_m) = (N_h / n_A) * (M_hi / act_m)
                w = (float(N_h_pop) / float(n_A)) * (float(M_hi) / float(act_m))
                for uj in sampled_u:
                    recs_A.append(
                        LasiCleanedRecord(
                            participant_id=f"{b}_{h}_{idx}_{uj}", household_id=f"h_{idx}",
                            state="S", urban_rural="R", survey_weight=w, strata=s_name,
                            psu=f"P_{idx}", age=65.0, gender="F", sbp_mean=float(p_info["sbp"][uj]),
                            dbp_mean=80.0, biomarker_participated=True, bp_participated=True,
                            hba1c_participated=True, has_valid_survey_weight=True,
                        )
                    )

        m_val, se_val, tel_val = engine.calculate_taylor_linearized_mean_and_se(
            records=recs_A,
            value_getter=lambda r: r.sbp_mean,
            fpc_by_stratum=fpc_A_dict,
        )
        pts_A.append(m_val)
        vars_A.append(tel_val["survey_variance"])

    var_mc = float(np.var(pts_A, ddof=1))
    mean_var_est = float(np.mean(vars_A))

    # Delta-method MCSE
    d_b = np.array(vars_A) - (np.array(pts_A) - np.mean(pts_A))**2
    s_d = float(np.std(d_b, ddof=1))
    mcse_rel_bias = (s_d / (math.sqrt(B) * var_mc)) * 100.0
    rel_bias_pct = ((mean_var_est - var_mc) / var_mc) * 100.0

    # With exact FPC calibration, relative variance bias is statistically indistinguishable from 0
    assert abs(rel_bias_pct) <= 2.58 * mcse_rel_bias, (
        f"FPC-calibrated variance relative bias {rel_bias_pct:+.2f}% exceeds 2.58*MCSE ({2.58*mcse_rel_bias:.2f}%)"
    )


def test_fpc_partition_guard_blocks_unadjusted_full_sample_fraction():
    """Verify that passing unadjusted full-sample FPC to partitioned records is blocked.

    Ensures callers cannot accidentally pass full-sample FPC fraction to partition records,
    and validates that get_partition_fpc and full_stratum_psu_counts work correctly.
    """
    records = []
    for s in ["S0", "S1"]:
        for p in range(4):
            p_name = f"{s}_P{p}"
            for j in range(10):
                records.append(
                    LasiCleanedRecord(
                        participant_id=f"{s}_{p}_{j}",
                        household_id=f"h_{s}_{p}",
                        strata=s,
                        psu=p_name,
                        survey_weight=10.0,
                        age=60.0,
                        gender="Female",
                        sbp_mean=120.0 + 5.0 * p,
                        dbp_mean=80.0,
                        has_valid_survey_weight=True,
                    )
                )

    partitioner = LasiPsuPartitioner()
    res = partitioner.partition(records)

    full_fpc = {"S0": 0.20, "S1": 0.20}
    engine = LasiSurveyVarianceEngine()

    # 1. Calling on partition A with unadjusted full_fpc directly MUST raise ValueError
    with pytest.raises(ValueError, match="Detected partitioned survey records analyzed with FPC"):
        engine.calculate_taylor_linearized_mean_and_se(
            res.records_a,
            value_getter=lambda r: r.sbp_mean,
            fpc_by_stratum=full_fpc,
        )

    # 2. Derive partition FPC: 4 PSUs total, n_a = 2, so p_k = 0.50 -> part_fpc = 0.10
    part_fpc = res.get_partition_fpc(PartitionLabel.PARTITION_A, full_fpc)
    assert part_fpc["S0"] == 0.10
    assert part_fpc["S1"] == 0.10

    # 3. Passing fpc_is_partition_adjusted=True succeeds
    m_adj, se_adj, tel_adj = engine.calculate_taylor_linearized_mean_and_se(
        res.records_a,
        value_getter=lambda r: r.sbp_mean,
        fpc_by_stratum=part_fpc,
        fpc_is_partition_adjusted=True,
    )
    assert se_adj > 0.0

    # 4. Supplying full_stratum_psu_counts auto-scales and produces identical SE
    m_auto, se_auto, tel_auto = engine.calculate_taylor_linearized_mean_and_se(
        res.records_a,
        value_getter=lambda r: r.sbp_mean,
        fpc_by_stratum=full_fpc,
        full_stratum_psu_counts=res.full_stratum_psu_counts,
    )
    assert math.isclose(se_adj, se_auto, rel_tol=1e-6)

    # 5. Check totals also enforce the guard
    with pytest.raises(ValueError, match="Detected partitioned survey records analyzed with FPC"):
        engine.calculate_taylor_linearized_total_and_se(
            res.records_a,
            value_getter=lambda r: r.sbp_mean,
            fpc_by_stratum=full_fpc,
        )


def test_ratio_estimator_finite_sample_bias_vs_horvitz_thompson_total_unbiasedness():
    """Mathematically demonstrate that totals are strictly design-unbiased while ratio means are only design-consistent.

    Evaluates all C(N, n) possible samples of size n=2 from N=4 PSUs with unequal cluster sizes.
    Demonstrates:
    1. Horvitz-Thompson total has exact zero design bias in finite samples: E[Y_hat] == Y_true.
    2. Ratio estimator has non-zero finite-sample bias O(1/n) due to Jensen's inequality and Cov(Y_hat, N_hat) != 0.
    """
    psus = [
        {"M": 10, "Y": 1200.0},
        {"M": 20, "Y": 2600.0},
        {"M": 40, "Y": 4800.0},
        {"M": 80, "Y": 11200.0},
    ]
    N = len(psus)
    n = 2
    true_total_Y = sum(p["Y"] for p in psus)
    true_total_M = sum(p["M"] for p in psus)
    true_mean = true_total_Y / true_total_M  # 19800 / 150 = 132.0

    samples = list(itertools.combinations(range(N), n))
    n_samples = len(samples)  # 6 equally likely samples under SRSWOR

    ht_totals = []
    ratio_means = []

    for s in samples:
        # Horvitz-Thompson total estimator: sum_{i in s} (N / n) * Y_i
        y_ht = sum((N / n) * psus[i]["Y"] for i in s)
        ht_totals.append(y_ht)

        # Ratio mean estimator: sum(w_i Y_i) / sum(w_i M_i) = sum(Y_i) / sum(M_i)
        r_mean = sum(psus[i]["Y"] for i in s) / sum(psus[i]["M"] for i in s)
        ratio_means.append(r_mean)

    expected_total = sum(ht_totals) / n_samples
    expected_mean = sum(ratio_means) / n_samples

    # 1. Horvitz-Thompson total is EXACTLY design-unbiased
    assert math.isclose(expected_total, true_total_Y, rel_tol=1e-12), (
        f"Horvitz-Thompson total must be strictly design-unbiased: {expected_total} vs {true_total_Y}"
    )

    # 2. Ratio mean has non-zero finite sample bias (Cochran 1977 Eq 6.13)
    finite_sample_bias = expected_mean - true_mean
    assert abs(finite_sample_bias) > 1.0, (
        f"Ratio mean should exhibit non-zero finite-sample bias, got bias={finite_sample_bias:.4f}"
    )
    # The bias here is exactly -2.1481 mmHg (-1.63%)
    assert math.isclose(finite_sample_bias, -2.148148, abs_tol=1e-4)
