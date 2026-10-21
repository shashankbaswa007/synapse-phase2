"""
Mathematical and Statistical Metrics for SYNAPSE Phase 2 Evaluation.
All statistical functions are implemented in pure Python (using math module)
without external C/SciPy dependencies, supporting high portability and auditability.
"""

import math
from typing import List, Tuple, Optional, Dict, Any, Union


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate the Wilson Score confidence interval for a binomial proportion.
    
    Wilson interval provides superior coverage probability compared to the Wald
    (normal approximation) interval, especially for small sample sizes or extreme proportions.

    Args:
        k: Observed successes / positive cases.
        n: Total sample size / denominator.
        confidence: Confidence level in (0, 1), default 0.95.

    Returns:
        (lower_bound, upper_bound) bounded in [0.0, 1.0].
    """
    if n <= 0:
        return (0.0, 0.0)

    k = max(0, min(k, n))
    
    # Quantiles of standard normal distribution
    z_map = {0.90: 1.644853, 0.95: 1.959964, 0.99: 2.575829}
    z = z_map.get(confidence, 1.959964)

    p = k / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    spread = (z * math.sqrt((p * (1.0 - p)) / n + z2 / (4.0 * n * n))) / denominator

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (round(lower, 4), round(upper, 4))


def jensen_shannon_divergence(p: List[float], q: List[float], base: float = 2.0) -> float:
    """Calculate the Jensen-Shannon Divergence (JSD) between two probability distributions.
    
    JSD is symmetric, bounded in [0.0, 1.0] when using logarithm base 2, and always finite.

    Args:
        p: First probability distribution (unnormalized or normalized).
        q: Second probability distribution.
        base: Logarithm base (default 2.0).

    Returns:
        JSD value in [0.0, 1.0].
    """
    if len(p) != len(q) or len(p) == 0:
        raise ValueError("Distributions must have identical non-zero length")

    sum_p = sum(p) or 1.0
    sum_q = sum(q) or 1.0
    p_norm = [x / sum_p for x in p]
    q_norm = [y / sum_q for y in q]

    # Midpoint distribution M = 0.5 * (P + Q)
    m = [0.5 * (p_norm[i] + q_norm[i]) for i in range(len(p))]

    log_fn = math.log2 if base == 2.0 else math.log

    def kl_divergence(a: List[float], b: List[float]) -> float:
        kl = 0.0
        for ai, bi in zip(a, b):
            if ai > 0.0 and bi > 0.0:
                kl += ai * (log_fn(ai) - log_fn(bi))
        return kl

    jsd = 0.5 * kl_divergence(p_norm, m) + 0.5 * kl_divergence(q_norm, m)
    return max(0.0, min(1.0, round(jsd, 5)))


def total_variation_distance(p: List[float], q: List[float]) -> float:
    """Calculate Total Variation Distance (TVD) between two probability distributions.
    TVD = 0.5 * sum(|p_i - q_i|), bounded in [0.0, 1.0].
    """
    if len(p) != len(q) or len(p) == 0:
        raise ValueError("Distributions must have identical non-zero length")

    sum_p = sum(p) or 1.0
    sum_q = sum(q) or 1.0
    p_norm = [x / sum_p for x in p]
    q_norm = [y / sum_q for y in q]

    tvd = 0.5 * sum(abs(pi - qi) for pi, qi in zip(p_norm, q_norm))
    return round(tvd, 5)


def regularized_lower_gamma(s: float, x: float, max_iter: int = 200, eps: float = 1e-12) -> float:
    """Compute regularized lower incomplete gamma function P(s, x) = gamma(s, x) / Gamma(s).
    Used for exact Chi-Square cumulative distribution function calculation.
    """
    if x <= 0.0 or s <= 0.0:
        return 0.0

    if x < s + 1.0:
        # Series expansion
        term = 1.0 / s
        total = term
        for n in range(1, max_iter):
            term *= x / (s + n)
            total += term
            if abs(term) < eps * abs(total):
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    else:
        # Continued fraction approximation for upper gamma Q(s, x) = 1 - P(s, x)
        b = x + 1.0 - s
        c = 1.0 / 1e-30
        d = 1.0 / b
        h = d
        for i in range(1, max_iter):
            an = -i * (i - s)
            b += 2.0
            d = an * d + b
            if abs(d) < 1e-30:
                d = 1e-30
            c = b + an / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < eps:
                break
        q = math.exp(-x + s * math.log(x) - math.lgamma(s)) * h
        return 1.0 - q


def chi_square_p_value(stat: float, df: int) -> float:
    """Compute p-value for chi-square statistic: P(X^2 >= stat) with df degrees of freedom."""
    if df <= 0 or stat <= 0.0:
        return 1.0
    cdf = regularized_lower_gamma(df / 2.0, stat / 2.0)
    return max(0.0, min(1.0, round(1.0 - cdf, 5)))


def chi_square_goodness_of_fit(
    observed: List[float],
    expected: List[float],
    min_expected: float = 5.0,
) -> Dict[str, Any]:
    """Calculate Chi-Square goodness-of-fit with automated sparse bin pooling.
    
    Cochran's rule for Chi-square tests requires expected counts to be at least 5.0.
    When sparse expected bins (E_i < min_expected) exist, adjacent categories
    are automatically pooled together until Cochran's rule is satisfied.

    Args:
        observed: Observed frequency counts in each bin.
        expected: Expected frequency counts in each bin (same sum as observed).
        min_expected: Minimum expected count per bin (default 5.0).

    Returns:
        Dict containing:
            chi2_stat: Chi-square test statistic.
            df: Degrees of freedom (k_pooled - 1).
            p_value: Probability under null hypothesis.
            pooled_observed: Array of observed counts after pooling.
            pooled_expected: Array of expected counts after pooling.
            was_pooled: Boolean flag indicating if pooling occurred.
            is_valid: Boolean flag indicating if df >= 1 after pooling.
    """
    if len(observed) != len(expected) or len(observed) == 0:
        raise ValueError("Observed and expected arrays must have identical non-zero length")

    obs = [float(x) for x in observed]
    exp = [float(y) for y in expected]

    # Automated pooling for sparse expected bins
    pooled_obs: List[float] = []
    pooled_exp: List[float] = []
    
    cur_o = 0.0
    cur_e = 0.0
    was_pooled = False

    for o, e in zip(obs, exp):
        cur_o += o
        cur_e += e
        if cur_e >= min_expected:
            pooled_obs.append(cur_o)
            pooled_exp.append(cur_e)
            cur_o = 0.0
            cur_e = 0.0
        else:
            was_pooled = True

    # If residual left over, merge into last pooled bin
    if cur_e > 0.0:
        if pooled_exp:
            pooled_obs[-1] += cur_o
            pooled_exp[-1] += cur_e
            was_pooled = True
        else:
            # All bins combined were less than min_expected
            pooled_obs.append(cur_o)
            pooled_exp.append(cur_e)

    k_pooled = len(pooled_exp)
    df = k_pooled - 1

    if df < 1:
        # Sample size too small for chi-square test
        return {
            "chi2_stat": 0.0,
            "df": 0,
            "p_value": 1.0,
            "pooled_observed": pooled_obs,
            "pooled_expected": pooled_exp,
            "was_pooled": was_pooled,
            "is_valid": False,
            "note": "Sample size insufficient for chi-square test after pooling",
        }

    chi2 = 0.0
    for o, e in zip(pooled_obs, pooled_exp):
        if e > 0.0:
            chi2 += ((o - e) ** 2) / e

    p_val = chi_square_p_value(chi2, df)

    return {
        "chi2_stat": round(chi2, 4),
        "df": df,
        "p_value": p_val,
        "pooled_observed": [round(x, 2) for x in pooled_obs],
        "pooled_expected": [round(y, 2) for y in pooled_exp],
        "was_pooled": was_pooled,
        "is_valid": True,
        "note": f"Pooled to {k_pooled} bins (min expected {min_expected})" if was_pooled else "Valid without pooling",
    }


def cramers_v(chi2_stat: float, n: int, k: int) -> float:
    """Calculate Cramér's V effect size for goodness-of-fit test.
    V = sqrt(chi2 / (n * (k - 1))).
    """
    if n <= 0 or k <= 1 or chi2_stat <= 0:
        return 0.0
    val = math.sqrt(chi2_stat / (n * (k - 1)))
    return round(min(1.0, val), 4)


def odds_ratio_and_ci(
    a: int, b: int, c: int, d: int, confidence: float = 0.95
) -> Tuple[float, float, float]:
    """Calculate Odds Ratio and 95% confidence interval for a 2x2 contingency table.
    
    Table layout:
               Condition B (+)  Condition B (-)
    Cond A (+)       a                b
    Cond A (-)       c                d

    Uses Haldane-Anscombe correction (+0.5 to all cells) if any cell is zero.

    Returns:
        (odds_ratio, lower_ci, upper_ci).
    """
    # Haldane-Anscombe correction if any cell is zero
    if a == 0 or b == 0 or c == 0 or d == 0:
        a_adj = a + 0.5
        b_adj = b + 0.5
        c_adj = c + 0.5
        d_adj = d + 0.5
    else:
        a_adj, b_adj, c_adj, d_adj = float(a), float(b), float(c), float(d)

    odds_ratio = (a_adj * d_adj) / (b_adj * c_adj)

    # Standard error of log odds ratio
    se_log_or = math.sqrt(1.0 / a_adj + 1.0 / b_adj + 1.0 / c_adj + 1.0 / d_adj)

    z_map = {0.90: 1.644853, 0.95: 1.959964, 0.99: 2.575829}
    z = z_map.get(confidence, 1.959964)

    log_or = math.log(odds_ratio)
    lower = math.exp(log_or - z * se_log_or)
    upper = math.exp(log_or + z * se_log_or)

    return (round(odds_ratio, 4), round(lower, 4), round(upper, 4))


def comorbidity_oe_ratio(p_joint: float, p_a: float, p_b: float) -> Optional[float]:
    """Calculate Observed-to-Expected (O/E) ratio under independence.
    O/E = P(A and B) / (P(A) * P(B)).
    O/E > 1.0 implies positive comorbidity clustering.
    O/E = 1.0 implies statistical independence.
    O/E < 1.0 implies mutual exclusivity / negative association.
    """
    expected = p_a * p_b
    if expected <= 0.0:
        return None
    return round(p_joint / expected, 4)


def distribution_quantiles(
    data: List[float],
    quantiles: Optional[List[float]] = None,
) -> Dict[float, float]:
    """Calculate empirical quantiles for a continuous sample with linear interpolation.

    Args:
        data: Numeric values.
        quantiles: List of quantile points in [0.0, 1.0] (default: 0.10, 0.25, 0.50, 0.75, 0.90).

    Returns:
        Dict mapping quantile point to interpolated value.
    """
    if not data:
        return {}

    qs = quantiles if quantiles is not None else [0.10, 0.25, 0.50, 0.75, 0.90]
    sorted_data = sorted(float(x) for x in data)
    n = len(sorted_data)

    results: Dict[float, float] = {}
    for q in qs:
        if q <= 0.0:
            results[q] = round(sorted_data[0], 4)
        elif q >= 1.0:
            results[q] = round(sorted_data[-1], 4)
        else:
            idx = q * (n - 1)
            low = int(idx)
            frac = idx - low
            if low + 1 < n:
                val = sorted_data[low] + frac * (sorted_data[low + 1] - sorted_data[low])
            else:
                val = sorted_data[low]
            results[q] = round(val, 4)

    return results


def two_sample_ks_statistic(
    sample1: List[float],
    sample2: List[float],
) -> Tuple[float, float]:
    """Compute Two-Sample Kolmogorov-Smirnov statistic and asymptotic p-value.
    
    Tests H0: sample1 and sample2 are drawn from the same continuous distribution.
    D = sup_x |F1(x) - F2(x)|.

    Args:
        sample1: First continuous sample.
        sample2: Second continuous sample.

    Returns:
        (ks_statistic, p_value).
    """
    if not sample1 or not sample2:
        return (0.0, 1.0)

    n1 = len(sample1)
    n2 = len(sample2)

    s1 = sorted(float(x) for x in sample1)
    s2 = sorted(float(y) for y in sample2)

    all_vals = sorted(set(s1 + s2))

    max_diff = 0.0
    idx1 = 0
    idx2 = 0

    for val in all_vals:
        while idx1 < n1 and s1[idx1] <= val:
            idx1 += 1
        while idx2 < n2 and s2[idx2] <= val:
            idx2 += 1

        cdf1 = idx1 / n1
        cdf2 = idx2 / n2
        diff = abs(cdf1 - cdf2)
        if diff > max_diff:
            max_diff = diff

    # Asymptotic p-value approximation via Kolmogorov limiting distribution
    neff = (n1 * n2) / (n1 + n2)
    lam = (math.sqrt(neff) + 0.12 + 0.11 / math.sqrt(neff)) * max_diff

    if lam <= 0.0:
        p_val = 1.0
    else:
        # Sum first 50 terms of Kolmogorov expansion
        p_sum = 0.0
        for k in range(1, 51):
            term = 2.0 * ((-1) ** (k - 1)) * math.exp(-2.0 * (k ** 2) * (lam ** 2))
            p_sum += term
            if abs(term) < 1e-10:
                break
        p_val = max(0.0, min(1.0, round(p_sum, 5)))

    return (round(max_diff, 5), p_val)


def wasserstein_distance_1d(
    sample1: List[float],
    sample2: List[float],
) -> float:
    """Compute 1-Wasserstein (earth-mover's) distance between two 1D empirical samples.
    
    W1(P, Q) = integral_0^1 |F1^-1(u) - F2^-1(u)| du = sum delta_x * |F1(x) - F2(x)|.

    Args:
        sample1: First sample values.
        sample2: Second sample values.

    Returns:
        W1 distance in original measurement units.
    """
    if not sample1 or not sample2:
        return 0.0

    n1 = len(sample1)
    n2 = len(sample2)

    s1 = sorted(float(x) for x in sample1)
    s2 = sorted(float(y) for y in sample2)

    # Collect all unique points
    unique_vals = sorted(set(s1 + s2))
    if len(unique_vals) <= 1:
        return 0.0

    total_dist = 0.0
    idx1 = 0
    idx2 = 0

    for i in range(len(unique_vals) - 1):
        v_cur = unique_vals[i]
        v_next = unique_vals[i + 1]
        delta_x = v_next - v_cur

        while idx1 < n1 and s1[idx1] <= v_cur:
            idx1 += 1
        while idx2 < n2 and s2[idx2] <= v_cur:
            idx2 += 1

        cdf1 = idx1 / n1
        cdf2 = idx2 / n2
        total_dist += delta_x * abs(cdf1 - cdf2)

    return round(total_dist, 4)


def weighted_mean_and_variance(
    values: List[float],
    weights: Optional[List[float]] = None,
) -> Tuple[float, float]:
    """Calculate survey-weighted mean and sample variance.

    Args:
        values: Observed numeric values.
        weights: Optional survey sampling weights (must be non-negative).

    Returns:
        (weighted_mean, weighted_variance).
    """
    if not values:
        return (0.0, 0.0)

    n = len(values)
    if weights is None or len(weights) != n:
        # Unweighted
        mean_v = sum(values) / n
        if n > 1:
            var_v = sum((x - mean_v) ** 2 for x in values) / (n - 1)
        else:
            var_v = 0.0
        return (round(mean_v, 4), round(var_v, 4))

    sum_w = sum(weights)
    if sum_w <= 0.0:
        return (0.0, 0.0)

    w_mean = sum(w * x for w, x in zip(weights, values)) / sum_w

    sum_w2 = sum(w * w for w in weights)
    # Unbiased weighted variance (Bessel-corrected for survey weights)
    denom = sum_w - (sum_w2 / sum_w)
    if denom > 0.0:
        w_var = sum(w * ((x - w_mean) ** 2) for w, x in zip(weights, values)) / denom
    else:
        w_var = 0.0

    return (round(w_mean, 4), round(w_var, 4))


def effective_sample_size(weights: List[float]) -> float:
    """Calculate Kish's effective sample size (n_eff) for unequal sampling weights.
    
    Formula:
        n_eff = (sum w_i)^2 / sum (w_i^2)
    
    When weights are uniform, n_eff == n.
    When weights vary, n_eff < n, reflecting variance inflation due to weighting.

    Args:
        weights: List of positive survey weights.

    Returns:
        Effective sample size as float. Returns 0.0 if empty or sum <= 0.
    """
    if not weights:
        return 0.0
    valid_w = [w for w in weights if w is not None and w > 0.0 and not math.isnan(w)]
    if not valid_w:
        return 0.0

    sum_w = sum(valid_w)
    sum_w2 = sum(w * w for w in valid_w)
    if sum_w2 <= 0.0:
        return 0.0
    return round((sum_w * sum_w) / sum_w2, 2)


def survey_design_effect_weighting(weights: List[float]) -> float:
    """Calculate Kish's design effect due to unequal weighting (DEFF_w).
    
    Formula:
        DEFF_w = n / n_eff = 1 + CV(w)^2
    
    Args:
        weights: Survey weights.

    Returns:
        DEFF_w (>= 1.0). Returns 1.0 if empty or uniform.
    """
    if not weights:
        return 1.0
    n = len(weights)
    n_eff = effective_sample_size(weights)
    if n_eff <= 0.0:
        return 1.0
    return round(max(1.0, n / n_eff), 3)


def survey_weighted_proportion_and_ci(
    values: List[Union[int, bool, float]],
    weights: Optional[List[float]] = None,
    confidence: float = 0.95,
) -> Tuple[float, Tuple[float, float], float]:
    """Calculate survey-weighted proportion and design-adjusted confidence interval.
    
    Uses effective sample size (n_eff) to adjust standard error for unequal weighting:
        SE = sqrt(p * (1 - p) / n_eff)

    Args:
        values: Binary outcomes (1/0, True/False).
        weights: Optional sampling weights.
        confidence: Confidence level (default 0.95).

    Returns:
        (weighted_prop, (ci_lower, ci_upper), n_eff).
    """
    if not values:
        return (0.0, (0.0, 0.0), 0.0)

    n = len(values)
    num_vals = [1.0 if v in {1, 1.0, True} else 0.0 for v in values]

    if weights is None or len(weights) != n:
        # Unweighted Wilson interval
        k = int(sum(num_vals))
        p = k / n
        ci = wilson_score_interval(k, n, confidence=confidence)
        return (round(p, 4), ci, float(n))

    # Survey weighted
    valid_pairs = [(v, w) for v, w in zip(num_vals, weights) if w is not None and w > 0.0]
    if not valid_pairs:
        return (0.0, (0.0, 0.0), 0.0)

    sum_w = sum(w for _, w in valid_pairs)
    if sum_w <= 0.0:
        return (0.0, (0.0, 0.0), 0.0)

    w_prop = sum(v * w for v, w in valid_pairs) / sum_w
    n_eff = effective_sample_size([w for _, w in valid_pairs])

    # Z-multiplier
    z_map = {0.90: 1.644853, 0.95: 1.959964, 0.99: 2.575829}
    z = z_map.get(confidence, 1.959964)

    # Design-adjusted Wald interval using n_eff
    if n_eff > 1.0 and 0.0 < w_prop < 1.0:
        se = math.sqrt((w_prop * (1.0 - w_prop)) / n_eff)
        lower = max(0.0, w_prop - z * se)
        upper = min(1.0, w_prop + z * se)
    else:
        lower, upper = w_prop, w_prop

    return (round(w_prop, 4), (round(lower, 4), round(upper, 4)), n_eff)

