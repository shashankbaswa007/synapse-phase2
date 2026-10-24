"""
Design-Aware Survey Variance Estimation and Uncertainty Accounting Engine.

Implements Milestone 3 Requirement 5 and Milestone 4 Verification:
1. Taylor Series Linearization (TSL) for complex-survey weighted means and proportions,
   properly accounting for multi-stage cluster sampling (PSUs nested in Strata).
2. Explicit handling of singleton PSUs (nh == 1) via CERTAINTY, GRAND_MEAN_CENTERING,
   or COLLAPSE_STRATA policies, rejecting arbitrary geographic merges.
3. Proper design degrees of freedom (df = sum(n_h) - H) and Student's t critical
   multipliers (tdf) rather than anti-conservative fixed normal approximations.
4. Logit-transformed confidence intervals for proportions ensuring bounds in (0, 1).
5. Support for Finite Population Correction (FPC) factors at primary sampling stage.
6. Separation of Survey Sampling Uncertainty from Simulation Monte Carlo Uncertainty
   with explicit documentation of independence assumptions (Cov = 0).
"""

from enum import Enum
import math
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict

from synapse_simulator.evaluation.lasi.models import LasiCleanedRecord


class SingletonHandlingStrategy(str, Enum):
    """Protocol for estimating variance in survey strata containing only 1 PSU (nh == 1)."""
    CERTAINTY = "CERTAINTY"                      # Treat stratum as sampled with certainty (variance contribution = 0)
    GRAND_MEAN_CENTERING = "GRAND_MEAN_CENTERING" # Center singleton PSU around theoretical sample grand mean (0)
    COLLAPSE_STRATA = "COLLAPSE_STRATA"           # Collapse singleton with adjacent stratum in design order


# =============================================================================
# Exact NIST Student's t Distribution Lookup Table (two-tailed, df 1-30)
# =============================================================================
_T_TABLE_95 = {
    1: 12.706205, 2: 4.302653, 3: 3.182446, 4: 2.776445, 5: 2.570582,
    6: 2.446912, 7: 2.364624, 8: 2.306004, 9: 2.262157, 10: 2.228139,
    11: 2.200985, 12: 2.178813, 13: 2.160369, 14: 2.144787, 15: 2.131450,
    16: 2.119905, 17: 2.109816, 18: 2.100922, 19: 2.093024, 20: 2.085963,
    21: 2.079614, 22: 2.073873, 23: 2.068658, 24: 2.063899, 25: 2.059539,
    26: 2.055529, 27: 2.051831, 28: 2.048407, 29: 2.045230, 30: 2.042272,
}

_T_TABLE_90 = {
    1: 6.313752, 2: 2.919986, 3: 2.353363, 4: 2.131847, 5: 2.015048,
    6: 1.943180, 7: 1.894579, 8: 1.859548, 9: 1.833113, 10: 1.812461,
    11: 1.795885, 12: 1.782288, 13: 1.770933, 14: 1.761310, 15: 1.753050,
    16: 1.745884, 17: 1.739607, 18: 1.734064, 19: 1.729133, 20: 1.724718,
    21: 1.720743, 22: 1.717144, 23: 1.713872, 24: 1.710882, 25: 1.708141,
    26: 1.705618, 27: 1.703288, 28: 1.701130, 29: 1.699127, 30: 1.697261,
}

_T_TABLE_99 = {
    1: 63.65674, 2: 9.92484, 3: 5.84091, 4: 4.60409, 5: 4.03214,
    6: 3.70743, 7: 3.49948, 8: 3.35539, 9: 3.24984, 10: 3.16927,
    11: 3.10581, 12: 3.05454, 13: 3.01228, 14: 2.97684, 15: 2.94671,
    16: 2.92078, 17: 2.89823, 18: 2.87844, 19: 2.86093, 20: 2.84534,
    21: 2.83136, 22: 2.81876, 23: 2.80734, 24: 2.79694, 25: 2.78744,
    26: 2.77871, 27: 2.77068, 28: 2.76326, 29: 2.75639, 30: 2.75000,
}


def _norm_ppf(p: float) -> float:
    """Standard normal quantile function using Acklam's algorithm (error < 1.15e-9)."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError(f"p must be strictly in (0, 1), got {p}")
    a = [
        -3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
        1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00
    ]
    b = [
        -5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
        6.680131188771972e01, -1.328068155288572e01
    ]
    c = [
        -7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
        -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00
    ]
    d = [
        7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
        3.754408661907416e00
    ]
    p_low = 0.02425
    p_high = 1.0 - p_low
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)


def student_t_critical_value(df: int, confidence: float = 0.95) -> float:
    """Return two-tailed critical value t_{df, 1 - alpha/2} for given degrees of freedom.

    Args:
        df: Design degrees of freedom (must be >= 1).
        confidence: Two-sided confidence level (e.g. 0.95, 0.90, 0.99).

    Returns:
        Critical multiplier t_{df}.
    """
    if df < 1:
        raise ValueError(f"Degrees of freedom must be >= 1, got {df}")
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError(f"Confidence must be strictly between 0 and 1, got {confidence}")

    alpha = 1.0 - confidence
    p = 1.0 - (alpha / 2.0)

    # Use exact lookup tables for standard confidence levels when df <= 30
    if df <= 30:
        if math.isclose(confidence, 0.95, abs_tol=1e-4) and df in _T_TABLE_95:
            return _T_TABLE_95[df]
        if math.isclose(confidence, 0.90, abs_tol=1e-4) and df in _T_TABLE_90:
            return _T_TABLE_90[df]
        if math.isclose(confidence, 0.99, abs_tol=1e-4) and df in _T_TABLE_99:
            return _T_TABLE_99[df]

    # For df > 30 (or non-standard confidence), use Hill's Cornish-Fisher expansion
    z = _norm_ppf(p)
    if df >= 120:
        return z

    # Hill (1970) Cornish-Fisher expansion for Student's t quantile
    t_val = (
        z
        + (z**3 + z) / (4.0 * df)
        + (5.0 * z**5 + 16.0 * z**3 + 3.0 * z) / (96.0 * (df**2))
        + (3.0 * z**7 + 19.0 * z**5 + 17.0 * z**3 - 15.0 * z) / (384.0 * (df**3))
    )
    return t_val


class LasiSurveyVarianceEngine:
    """Design-based variance estimation for complex survey microdata."""

    def __init__(
        self,
        singleton_strategy: SingletonHandlingStrategy = SingletonHandlingStrategy.GRAND_MEAN_CENTERING,
    ):
        self.singleton_strategy = singleton_strategy

    def calculate_taylor_linearized_mean_and_se(
        self,
        records: List[LasiCleanedRecord],
        value_getter,
        strata_getter = lambda r: r.strata or "UNKNOWN_STRATUM",
        psu_getter = lambda r: r.psu or "UNKNOWN_PSU",
        weight_getter = lambda r: r.survey_weight if (r.survey_weight is not None and r.survey_weight > 0.0) else 0.0,
        fpc_by_stratum: Optional[Dict[str, float]] = None,
        fpc_is_partition_adjusted: bool = False,
        full_stratum_psu_counts: Optional[Dict[str, int]] = None,
        confidence: float = 0.95,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Calculate survey-weighted mean and Taylor Series Linearized standard error.

        Formula:
            y_bar_w = sum(w_hij * y_hij) / sum(w_hij)
            z_hij = (w_hij / sum(w)) * (y_hij - y_bar_w)
            z_hi = sum_{j in PSU_hi} z_hij
            z_bar_h = mean_{i=1..n_h}(z_hi)
            Var_h = (1 - f_h) * (n_h / (n_h - 1)) * sum_{i=1}^{n_h} (z_hi - z_bar_h)^2
            Var(y_bar_w) = sum_h Var_h
            SE(y_bar_w) = sqrt(Var(y_bar_w))
            df = sum(n_h) - H

        Returns:
            (weighted_mean, standard_error, diagnostic_telemetry)
        """
        # Filter valid records
        valid_items = []
        for r in records:
            val = value_getter(r)
            if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                w = float(weight_getter(r))
                if w > 0.0 and not (math.isnan(w) or math.isinf(w)):
                    s_id = str(strata_getter(r)).strip()
                    p_id = str(psu_getter(r)).strip()
                    valid_items.append((val, w, s_id, p_id))

        if not valid_items:
            return 0.0, 0.0, {"error": "NO_VALID_RECORDS"}

        n_total = len(valid_items)
        sum_w = sum(w for _, w, _, _ in valid_items)
        if sum_w <= 0.0:
            return 0.0, 0.0, {"error": "ZERO_WEIGHT_SUM"}

        weighted_mean = sum(v * w for v, w, _, _ in valid_items) / sum_w

        # If only 1 total record, variance is 0
        if n_total == 1:
            return round(weighted_mean, 4), 0.0, {
                "n_valid_observations": 1,
                "weighted_sum": round(sum_w, 2),
                "total_strata": 1,
                "total_psus": 1,
                "df": 0,
                "survey_variance": 0.0,
                "survey_se": 0.0,
                "insufficient_df": True,
            }

        # Aggregate linearized residuals to PSU level: z_hi
        psu_z_map: Dict[Tuple[str, str], float] = defaultdict(float)
        strata_psu_keys: Dict[str, Set[str]] = defaultdict(set)

        for val, w, s_id, p_id in valid_items:
            z_hij = (w / sum_w) * (val - weighted_mean)
            psu_z_map[(s_id, p_id)] += z_hij
            strata_psu_keys[s_id].add(p_id)

        # Handle collapsing if requested
        if self.singleton_strategy == SingletonHandlingStrategy.COLLAPSE_STRATA:
            strata_psu_keys, psu_z_map = self._collapse_singleton_strata(strata_psu_keys, psu_z_map)

        # Compute stratum-level variances
        total_variance = 0.0
        strata_summaries = {}
        singleton_strata = []
        total_effective_psus = 0

        # Sample grand mean of linearized score across all observations is exactly 0.0
        grand_z_center = 0.0

        # Partition FPC safety check:
        # Detect if records originate from a partitioned dataset
        is_partitioned = any(getattr(r, "partition_label", None) is not None for r in records)
        if is_partitioned and fpc_by_stratum is not None:
            if not fpc_is_partition_adjusted and not full_stratum_psu_counts:
                raise ValueError(
                    "Detected partitioned survey records analyzed with FPC. You must not pass the "
                    "unadjusted full-sample FPC fraction, as this deflates variance anti-conservatively. "
                    "Derive the partition fraction via LasiPartitionResult.get_partition_fpc(...) "
                    "and pass fpc_is_partition_adjusted=True, or supply full_stratum_psu_counts."
                )

        for s_id, psus in strata_psu_keys.items():
            n_h = len(psus)
            total_effective_psus += n_h
            z_his = [psu_z_map[(s_id, p_id)] for p_id in psus]
            z_bar_h = sum(z_his) / n_h if n_h > 0 else 0.0

            # Finite population correction factor f_h
            f_h = 0.0
            if fpc_by_stratum and s_id in fpc_by_stratum:
                f_h_raw = max(0.0, min(1.0, float(fpc_by_stratum[s_id])))
                if full_stratum_psu_counts and s_id in full_stratum_psu_counts and not fpc_is_partition_adjusted:
                    full_n_h = full_stratum_psu_counts[s_id]
                    if full_n_h > 0 and n_h < full_n_h:
                        f_h = f_h_raw * (float(n_h) / float(full_n_h))
                    else:
                        f_h = f_h_raw
                else:
                    f_h = f_h_raw
            fpc_multiplier = 1.0 - f_h

            if n_h > 1:
                # Standard Taylor Series Linearization stratum variance
                sum_sq_diff = sum((z_i - z_bar_h) ** 2 for z_i in z_his)
                var_h = fpc_multiplier * (n_h / (n_h - 1)) * sum_sq_diff
            elif n_h == 1:
                singleton_strata.append(s_id)
                if self.singleton_strategy == SingletonHandlingStrategy.CERTAINTY:
                    var_h = 0.0
                elif self.singleton_strategy == SingletonHandlingStrategy.GRAND_MEAN_CENTERING:
                    # Stata singleunit(centered) & R survey: centered around theoretical grand mean 0.0
                    var_h = fpc_multiplier * ((z_his[0] - grand_z_center) ** 2)
                else:
                    var_h = 0.0
            else:
                var_h = 0.0

            total_variance += var_h
            strata_summaries[s_id] = {
                "n_psu": n_h,
                "var_contribution": var_h,
                "is_singleton": (n_h == 1),
                "fpc": f_h,
            }

        se = math.sqrt(max(0.0, total_variance))

        # Design degrees of freedom: df = sum(n_h) - H
        total_strata_count = len(strata_psu_keys)
        df = max(0, total_effective_psus - total_strata_count)

        # Critical multiplier and confidence interval
        warnings = []
        if self.singleton_strategy == SingletonHandlingStrategy.CERTAINTY and singleton_strata:
            warnings.append(
                "CERTAINTY strategy assumes singleton PSUs were sampled with certainty (self-representing). "
                "Without empirical verification, this causes anti-conservative variance underestimation."
            )

        if df < 1:
            t_multiplier = math.nan
            ci_half_width = math.nan
            ci_lower = math.nan
            ci_upper = math.nan
            insufficient_df = True
            warnings.append("Insufficient degrees of freedom (df <= 0) to construct design-based confidence intervals.")
        else:
            insufficient_df = False
            if df < 12:
                warnings.append(
                    f"Sparse design degrees of freedom (df = {df} < 12). "
                    "Variance estimates may be unstable; Student's t multiplier applied."
                )
            t_multiplier = student_t_critical_value(df, confidence=confidence)
            ci_half_width = t_multiplier * se
            ci_lower = weighted_mean - ci_half_width
            ci_upper = weighted_mean + ci_half_width

        telemetry = {
            "n_valid_observations": n_total,
            "weighted_sum": round(sum_w, 2),
            "total_strata": total_strata_count,
            "singleton_strata_count": len(singleton_strata),
            "singleton_strategy": self.singleton_strategy.value,
            "total_psus": total_effective_psus,
            "df": df,
            "t_multiplier": round(t_multiplier, 4) if not math.isnan(t_multiplier) else None,
            "confidence_level": confidence,
            "ci_half_width": round(ci_half_width, 4) if not math.isnan(ci_half_width) else None,
            "ci_lower": round(ci_lower, 4) if not math.isnan(ci_lower) else None,
            "ci_upper": round(ci_upper, 4) if not math.isnan(ci_upper) else None,
            "survey_variance": total_variance,
            "survey_se": se,
            "insufficient_df": insufficient_df,
            "diagnostic_warnings": warnings,
        }

        return round(weighted_mean, 4), round(se, 4), telemetry

    def calculate_taylor_linearized_total_and_se(
        self,
        records: List[LasiCleanedRecord],
        value_getter,
        strata_getter = lambda r: r.strata or "UNKNOWN_STRATUM",
        psu_getter = lambda r: r.psu or "UNKNOWN_PSU",
        weight_getter = lambda r: r.survey_weight if (r.survey_weight is not None and r.survey_weight > 0.0) else 0.0,
        fpc_by_stratum: Optional[Dict[str, float]] = None,
        fpc_is_partition_adjusted: bool = False,
        full_stratum_psu_counts: Optional[Dict[str, int]] = None,
        confidence: float = 0.95,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Calculate survey-weighted population total and Taylor linearized standard error.

        Formula:
            Y_hat = sum_{hij} w_hij * y_hij
            Y_hi = sum_{j in PSU_hi} w_hij * y_hij
            Y_bar_h = mean_{i=1..n_h}(Y_hi)
            Var_h = (1 - f_h) * (n_h / (n_h - 1)) * sum_{i=1}^{n_h} (Y_hi - Y_bar_h)^2
            Var(Y_hat) = sum_h Var_h
            SE(Y_hat) = sqrt(Var(Y_hat))
            df = sum(n_h) - H

        Returns:
            (weighted_total, standard_error, diagnostic_telemetry)
        """
        valid_items = []
        for r in records:
            val = value_getter(r)
            if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                w = float(weight_getter(r))
                if w > 0.0 and not (math.isnan(w) or math.isinf(w)):
                    s_id = str(strata_getter(r)).strip()
                    p_id = str(psu_getter(r)).strip()
                    valid_items.append((val, w, s_id, p_id))

        if not valid_items:
            return 0.0, 0.0, {"error": "NO_VALID_RECORDS"}

        n_total = len(valid_items)
        sum_w = sum(w for _, w, _, _ in valid_items)
        if sum_w <= 0.0:
            return 0.0, 0.0, {"error": "ZERO_WEIGHT_SUM"}

        weighted_total = sum(v * w for v, w, _, _ in valid_items)

        if n_total == 1:
            return round(weighted_total, 4), 0.0, {
                "n_valid_observations": 1,
                "weighted_sum": round(sum_w, 2),
                "total_strata": 1,
                "total_psus": 1,
                "df": 0,
                "survey_variance": 0.0,
                "survey_se": 0.0,
                "insufficient_df": True,
            }

        # Aggregate weighted values to PSU level: Y_hi
        psu_y_map: Dict[Tuple[str, str], float] = defaultdict(float)
        strata_psu_keys: Dict[str, Set[str]] = defaultdict(set)

        for val, w, s_id, p_id in valid_items:
            psu_y_map[(s_id, p_id)] += w * val
            strata_psu_keys[s_id].add(p_id)

        # Handle collapsing if requested
        if self.singleton_strategy == SingletonHandlingStrategy.COLLAPSE_STRATA:
            strata_psu_keys, psu_y_map = self._collapse_singleton_strata(strata_psu_keys, psu_y_map)

        total_variance = 0.0
        strata_summaries = {}
        singleton_strata = []
        total_effective_psus = sum(len(psus) for psus in strata_psu_keys.values())

        # For singleunit(centered) on totals: center around overall mean PSU total
        grand_y_center = (
            sum(psu_y_map.values()) / max(1, total_effective_psus)
            if total_effective_psus > 0
            else 0.0
        )

        # Partition FPC safety check:
        is_partitioned = any(getattr(r, "partition_label", None) is not None for r in records)
        if is_partitioned and fpc_by_stratum is not None:
            if not fpc_is_partition_adjusted and not full_stratum_psu_counts:
                raise ValueError(
                    "Detected partitioned survey records analyzed with FPC. You must not pass the "
                    "unadjusted full-sample FPC fraction, as this deflates variance anti-conservatively. "
                    "Derive the partition fraction via LasiPartitionResult.get_partition_fpc(...) "
                    "and pass fpc_is_partition_adjusted=True, or supply full_stratum_psu_counts."
                )

        for s_id, psus in strata_psu_keys.items():
            n_h = len(psus)
            y_his = [psu_y_map[(s_id, p_id)] for p_id in psus]
            y_bar_h = sum(y_his) / n_h if n_h > 0 else 0.0

            f_h = 0.0
            if fpc_by_stratum and s_id in fpc_by_stratum:
                f_h_raw = max(0.0, min(1.0, float(fpc_by_stratum[s_id])))
                if full_stratum_psu_counts and s_id in full_stratum_psu_counts and not fpc_is_partition_adjusted:
                    full_n_h = full_stratum_psu_counts[s_id]
                    if full_n_h > 0 and n_h < full_n_h:
                        f_h = f_h_raw * (float(n_h) / float(full_n_h))
                    else:
                        f_h = f_h_raw
                else:
                    f_h = f_h_raw
            fpc_multiplier = 1.0 - f_h

            if n_h > 1:
                sum_sq_diff = sum((y_i - y_bar_h) ** 2 for y_i in y_his)
                var_h = fpc_multiplier * (n_h / (n_h - 1)) * sum_sq_diff
            elif n_h == 1:
                singleton_strata.append(s_id)
                if self.singleton_strategy == SingletonHandlingStrategy.CERTAINTY:
                    var_h = 0.0
                elif self.singleton_strategy == SingletonHandlingStrategy.GRAND_MEAN_CENTERING:
                    var_h = fpc_multiplier * ((y_his[0] - grand_y_center) ** 2)
                else:
                    var_h = 0.0
            else:
                var_h = 0.0

            total_variance += var_h
            strata_summaries[s_id] = {
                "n_psu": n_h,
                "var_contribution": var_h,
                "is_singleton": (n_h == 1),
                "fpc": f_h,
            }

        se = math.sqrt(max(0.0, total_variance))
        total_strata_count = len(strata_psu_keys)
        df = max(0, total_effective_psus - total_strata_count)

        warnings = []
        if self.singleton_strategy == SingletonHandlingStrategy.CERTAINTY and singleton_strata:
            warnings.append(
                "CERTAINTY strategy assumes singleton PSUs were sampled with certainty (self-representing). "
                "Without empirical verification, this causes anti-conservative variance underestimation."
            )

        if df < 1:
            t_multiplier = math.nan
            ci_half_width = math.nan
            ci_lower = math.nan
            ci_upper = math.nan
            insufficient_df = True
            warnings.append("Insufficient degrees of freedom (df <= 0) to construct design-based confidence intervals.")
        else:
            insufficient_df = False
            if df < 12:
                warnings.append(
                    f"Sparse design degrees of freedom (df = {df} < 12). "
                    "Variance estimates may be unstable; Student's t multiplier applied."
                )
            t_multiplier = student_t_critical_value(df, confidence=confidence)
            ci_half_width = t_multiplier * se
            ci_lower = weighted_total - ci_half_width
            ci_upper = weighted_total + ci_half_width

        telemetry = {
            "n_valid_observations": n_total,
            "weighted_sum": round(sum_w, 2),
            "total_strata": total_strata_count,
            "singleton_strata_count": len(singleton_strata),
            "singleton_strategy": self.singleton_strategy.value,
            "total_psus": total_effective_psus,
            "df": df,
            "t_multiplier": round(t_multiplier, 4) if not math.isnan(t_multiplier) else None,
            "confidence_level": confidence,
            "ci_half_width": round(ci_half_width, 4) if not math.isnan(ci_half_width) else None,
            "ci_lower": round(ci_lower, 4) if not math.isnan(ci_lower) else None,
            "ci_upper": round(ci_upper, 4) if not math.isnan(ci_upper) else None,
            "survey_variance": total_variance,
            "survey_se": se,
            "insufficient_df": insufficient_df,
            "diagnostic_warnings": warnings,
        }

        return round(weighted_total, 4), round(se, 4), telemetry

    def calculate_taylor_linearized_proportion_and_se(
        self,
        records: List[LasiCleanedRecord],
        indicator_getter,
        strata_getter = lambda r: r.strata or "UNKNOWN_STRATUM",
        psu_getter = lambda r: r.psu or "UNKNOWN_PSU",
        weight_getter = lambda r: r.survey_weight if (r.survey_weight is not None and r.survey_weight > 0.0) else 0.0,
        fpc_by_stratum: Optional[Dict[str, float]] = None,
        fpc_is_partition_adjusted: bool = False,
        full_stratum_psu_counts: Optional[Dict[str, int]] = None,
        confidence: float = 0.95,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Calculate survey-weighted proportion, Taylor linearized SE, Wald and logit CIs.

        A proportion is a weighted mean of a binary indicator variable y in {0, 1}.
        The logit-transformed interval maps eta = logit(p) +/- t * SE(logit(p))
        back through expit to guarantee bounds strictly within [0, 1].

        Returns:
            (weighted_proportion, standard_error, diagnostic_telemetry)
        """
        # Binary indicator adapter
        def binary_val_getter(r):
            raw = indicator_getter(r)
            if raw is None:
                return None
            if isinstance(raw, bool):
                return 1.0 if raw else 0.0
            if isinstance(raw, (int, float)):
                if math.isnan(raw) or math.isinf(raw):
                    return None
                if raw in (1, 1.0):
                    return 1.0
                if raw in (0, 0.0):
                    return 0.0
                raise ValueError(f"Indicator value must be binary (0 or 1), got {raw}")
            raise ValueError(f"Unsupported indicator type {type(raw)} for value {raw}")

        p_w, se, mean_tel = self.calculate_taylor_linearized_mean_and_se(
            records=records,
            value_getter=binary_val_getter,
            strata_getter=strata_getter,
            psu_getter=psu_getter,
            weight_getter=weight_getter,
            fpc_by_stratum=fpc_by_stratum,
            fpc_is_partition_adjusted=fpc_is_partition_adjusted,
            full_stratum_psu_counts=full_stratum_psu_counts,
            confidence=confidence,
        )

        df = mean_tel.get("df", 0)
        t_mult = mean_tel.get("t_multiplier")

        # Wald interval
        wald_lower = mean_tel.get("ci_lower")
        wald_upper = mean_tel.get("ci_upper")

        # Logit-transformed confidence interval (Korn & Graubard 1998)
        # eta = log(p / (1 - p))
        # SE(eta) = SE(p) / (p * (1 - p))
        logit_lower = None
        logit_upper = None
        logit_se = None

        if (
            not mean_tel.get("insufficient_df", False)
            and t_mult is not None
            and 0.0 < p_w < 1.0
            and se > 0.0
        ):
            try:
                eta = math.log(p_w / (1.0 - p_w))
                se_eta = se / (p_w * (1.0 - p_w))
                logit_se = round(se_eta, 6)
                half_eta = t_mult * se_eta
                eta_low = eta - half_eta
                eta_high = eta + half_eta

                # Expit transform
                logit_lower = round(1.0 / (1.0 + math.exp(-eta_low)), 4)
                logit_upper = round(1.0 / (1.0 + math.exp(-eta_high)), 4)
            except (OverflowError, ZeroDivisionError):
                logit_lower = round(max(0.0, wald_lower) if wald_lower is not None else 0.0, 4)
                logit_upper = round(min(1.0, wald_upper) if wald_upper is not None else 1.0, 4)
        elif p_w == 0.0:
            logit_lower = 0.0
            logit_upper = 0.0
        elif p_w == 1.0:
            logit_lower = 1.0
            logit_upper = 1.0

        telemetry = dict(mean_tel)
        telemetry.update({
            "proportion": p_w,
            "wald_ci": (wald_lower, wald_upper) if wald_lower is not None else None,
            "logit_ci": (logit_lower, logit_upper) if logit_lower is not None else None,
            "logit_se": logit_se,
        })

        return p_w, se, telemetry

    def _collapse_singleton_strata(
        self,
        strata_psu_keys: Dict[str, Set[str]],
        psu_z_map: Dict[Tuple[str, str], float],
    ) -> Tuple[Dict[str, Set[str]], Dict[Tuple[str, str], float]]:
        """Collapse singleton strata with an adjacent stratum in the design order.

        Ensures singletons at the start, middle, or end of the stratum list are
        properly merged, leaving zero singleton strata whenever total strata >= 2.
        """
        sorted_strata = sorted(strata_psu_keys.keys())
        if len(sorted_strata) <= 1:
            return dict(strata_psu_keys), dict(psu_z_map)

        strata_list: List[List[Any]] = [[s, set(strata_psu_keys[s])] for s in sorted_strata]
        new_psu_z: Dict[Tuple[str, str], float] = dict(psu_z_map)

        i = 0
        while i < len(strata_list):
            s_name, psus = strata_list[i]
            if len(psus) == 1:
                if i + 1 < len(strata_list):
                    # Collapse with next stratum
                    next_name, next_psus = strata_list[i + 1]
                    merged_name = f"{s_name}+{next_name}"
                    merged_psus = set()

                    for p in psus:
                        new_p = f"{s_name}_{p}"
                        merged_psus.add(new_p)
                        new_psu_z[(merged_name, new_p)] = psu_z_map.get((s_name, p), new_psu_z.get((s_name, p), 0.0))

                    for p in next_psus:
                        new_p = f"{next_name}_{p}"
                        merged_psus.add(new_p)
                        new_psu_z[(merged_name, new_p)] = psu_z_map.get((next_name, p), new_psu_z.get((next_name, p), 0.0))

                    strata_list[i : i + 2] = [[merged_name, merged_psus]]
                    # Do not advance i; re-check merged stratum
                elif i > 0:
                    # Last stratum is a singleton: collapse into previous stratum
                    prev_name, prev_psus = strata_list[i - 1]
                    merged_name = f"{prev_name}+{s_name}"
                    merged_psus = set()

                    for p in prev_psus:
                        new_p = p if "_" in p else f"{prev_name}_{p}"
                        merged_psus.add(new_p)
                        new_psu_z[(merged_name, new_p)] = new_psu_z.get((prev_name, p), psu_z_map.get((prev_name, p), 0.0))

                    for p in psus:
                        new_p = f"{s_name}_{p}"
                        merged_psus.add(new_p)
                        new_psu_z[(merged_name, new_p)] = psu_z_map.get((s_name, p), new_psu_z.get((s_name, p), 0.0))

                    strata_list[i - 1 : i + 1] = [[merged_name, merged_psus]]
                    break
                else:
                    i += 1
            else:
                i += 1

        res_strata = {name: psus for name, psus in strata_list}
        return res_strata, new_psu_z

    @staticmethod
    def combine_survey_and_monte_carlo_variance(
        survey_var: float,
        sim_variance: float,
        sim_replications_m: int,
        df_survey: Optional[int] = None,
        confidence: float = 0.95,
    ) -> Dict[str, Any]:
        """Combine reference survey sampling uncertainty with simulation Monte Carlo uncertainty.

        Total discrepancy variance:
            Var(Delta) = Var(theta_sim - theta_ref) = Var_survey + (Var_sim / M)
            SE(Delta) = sqrt(Var(Delta))

        Independence Assumption:
            Requires Cov(theta_sim, theta_ref) == 0.
            - Holds strictly for baseline (pre-calibration) evaluation and holdout validation
              against uncalibrated reference data (Partition C).
            - VIOLATED if simulation model parameters were fitted/calibrated directly on the
              exact same reference data, inducing positive covariance.

        Degrees of Freedom:
            If df_survey is supplied, Welch-Satterthwaite effective degrees of freedom is computed:
                df_eff = (Var_survey + Var_MC)^2 / [ (Var_survey^2 / df_survey) + (Var_MC^2 / (M - 1)) ]
            and Student's t multiplier is used. Otherwise, standard normal z multiplier is used.
        """
        mc_var = sim_variance / max(1, sim_replications_m)
        total_var = survey_var + mc_var
        total_se = math.sqrt(max(0.0, total_var))

        # Degrees of freedom calculation
        effective_df = None
        multiplier = None

        if df_survey is not None and df_survey > 0 and total_var > 0.0:
            df_mc = max(1, sim_replications_m - 1)
            denom = (survey_var**2 / df_survey) + (mc_var**2 / df_mc)
            if denom > 0.0:
                effective_df = int(round((total_var**2) / denom))
                effective_df = max(1, effective_df)
                multiplier = student_t_critical_value(effective_df, confidence=confidence)

        if multiplier is None:
            z_map = {0.90: 1.644853, 0.95: 1.959964, 0.99: 2.575829}
            multiplier = z_map.get(confidence, _norm_ppf(1.0 - (1.0 - confidence) / 2.0))

        half_width = multiplier * total_se

        pct_survey = round((survey_var / max(1e-9, total_var)) * 100.0, 1)
        pct_mc = round((mc_var / max(1e-9, total_var)) * 100.0, 1)

        return {
            "survey_variance": round(survey_var, 6),
            "monte_carlo_variance": round(mc_var, 6),
            "total_variance": round(total_var, 6),
            "combined_se": round(total_se, 4),
            "z_multiplier": multiplier,
            "multiplier": multiplier,
            "effective_df": effective_df,
            "confidence_level": confidence,
            "ci_half_width": round(half_width, 4),
            "survey_uncertainty_share_pct": pct_survey,
            "monte_carlo_uncertainty_share_pct": pct_mc,
            "independence_assumption": (
                "Assumes Cov(theta_sim, theta_ref) == 0. Valid for uncalibrated baseline and "
                "out-of-sample holdout validation. Violated if simulator is calibrated directly "
                "against the reference dataset."
            ),
        }
