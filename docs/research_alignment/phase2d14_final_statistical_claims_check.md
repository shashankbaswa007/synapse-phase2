# Phase 2D.14: Final Statistical Claims Check and Implementation Hardening

**Document Status:** Final Closed Audit & Architectural Consolidation  
**Prior Documents:**  
- [`phase2d10_design_based_inference_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d10_design_based_inference_audit.md)  
- [`phase2d11_variance_estimator_verification.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d11_variance_estimator_verification.md)  
- [`phase2d12_independent_monte_carlo_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d12_independent_monte_carlo_audit.md)  
- [`phase2d13_final_variance_reconciliation.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d13_final_variance_reconciliation.md)  
**Target Code Modules:**  
- [`synapse_simulator/evaluation/lasi/models.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py)  
- [`synapse_simulator/evaluation/lasi/partitioner.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py)  
- [`synapse_simulator/evaluation/lasi/variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py)  
- [`tests/test_survey_variance_monte_carlo.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_monte_carlo.py)  
**Verification Scope:** Narrowly scoped final review of statistical claims, Eve's Law paired bootstrap uncertainty, ratio estimator consistency vs. Horvitz-Thompson unbiasedness, and automated FPC partition safety guards.  
**Governance Invariant:** Synthetic microdata only; zero genuine LASI access; `REFERENCE_DATA_PENDING` strictly preserved; zero clinical default alterations.

---

## 1. Executive Summary

This review finalizes the statistical and computational verification of complex survey design, partitioning, and variance estimation across the Synapse LASI evaluation pipeline. It addresses three specific statistical questions arising from Phase 2D.13:

1. **Paired Bootstrap Standard Error for Eve's Law:** Verified that testing the Eve's Law discrepancy $\Delta = \widehat{V}_{\text{uncond}} - V_{\text{pred}}$ against marginal $\text{SE}(\widehat{V}_{\text{uncond}})$ is conservative because $\hat{Y}_{\text{full}}$ and $\hat{Y}^{(C)}$ covary strongly across common survey draws $S_b$. Upgraded [`test_first_principles_eves_law_variance_decomposition`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_monte_carlo.py#L412) to compute the exact paired bootstrap $\text{SE}(\Delta)$ and enforce `discrepancy <= 2.58 * se_diff`.
2. **Design-Unbiased Totals vs. Design-Consistent Ratio Means:** Formally corrected the claim that sample weighted means and proportions are "design-unbiased". While Horvitz-Thompson population totals are strictly design-unbiased in finite samples ($E[\hat{Y}] \equiv Y$), ratio estimators $\hat{\bar{Y}} = \hat{Y}/\hat{N}$ are nonlinear ratios of random variables that exhibit finite-sample bias of order $O(1/n)$ (Cochran 1977 Eq 6.13). Added an exact mathematical proof and regression test [`test_ratio_estimator_finite_sample_bias_vs_horvitz_thompson_total_unbiasedness`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_monte_carlo.py#L710) demonstrating exact zero bias for totals ($0.00000000$) alongside non-zero finite-sample ratio bias ($-1.63\%$).
3. **Automated FPC Partition Guard:** Implemented technical safeguards preventing partition callers from passing unadjusted full-sample FPC fractions $f_h = n_h / N_h$, which would deflate partition variance anti-conservatively. Partition records are stamped with `partition_label`, `LasiPartitionResult` exposes `get_partition_fpc(...)`, and [`variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py) raises a strict `ValueError` if unadjusted full-sample FPC is supplied to partitioned records without auto-scaling.
4. **Final Closure:** With these checks implemented and 368 tests passing, all statistical claims are fully grounded, reproducible, and mathematically closed. No material defects remain.

---

## 2. Eve's Law Discrepancy & Paired Bootstrap Uncertainty

### 2.1 Theoretical Variance of the Difference

Under the Law of Total Variance (Eve's Law):
$$\text{Var}(\hat{Y}^{(C)}) = \text{Var}_S(E[\hat{Y}^{(C)} \mid S]) + E_S[\text{Var}(\hat{Y}^{(C)} \mid S)] = \text{Var}_S(\hat{Y}_{\text{full}}) + E_S[\text{Var}(\hat{Y}^{(C)} \mid S)]$$

Let:
$$V_{\text{pred}} = \widehat{\text{Var}}_S(\hat{Y}_{\text{full}}) + \frac{1}{B}\sum_{b=1}^B \text{Var}(\hat{Y}_b^{(C)} \mid S_b)$$
$$\widehat{V}_{\text{uncond}} = \frac{1}{B-1}\sum_{b=1}^B (\hat{Y}_b^{(C)} - \bar{Y}^{(C)})^2$$
$$\Delta = \widehat{V}_{\text{uncond}} - V_{\text{pred}}$$

Because $\hat{Y}_b^{(C)}$ is a subsample of $S_b$, $\hat{Y}_{b, \text{full}}$ and $\hat{Y}_b^{(C)}$ share the same primary sampling realizations. Consequently, their random fluctuations across survey draws are strongly correlated:
$$\text{Cov}\left(\widehat{V}_{\text{uncond}}, V_{\text{pred}}\right) > 0$$

Therefore, the variance of the difference is:
$$\text{Var}(\Delta) = \text{Var}(\widehat{V}_{\text{uncond}}) + \text{Var}(V_{\text{pred}}) - 2\,\text{Cov}(\widehat{V}_{\text{uncond}}, V_{\text{pred}}) \le \text{Var}(\widehat{V}_{\text{uncond}})$$

### 2.2 Numerical Verification & Acceptance Threshold Alignment

In [`test_first_principles_eves_law_variance_decomposition`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_monte_carlo.py#L412) ($B = 300$ survey draws):
- $V_{\text{pred}} = 8,109,092,348.32$
- $\widehat{V}_{\text{uncond}} = 8,119,312,421.02$
- Raw Discrepancy $\Delta = +10,220,072.69$ ($+0.13\%$)
- Marginal Unconditional MCSE: $\text{MCSE}(\widehat{V}_{\text{uncond}}) = 664,046,751.54$
- **Paired Bootstrap Standard Error of Difference:**
  Evaluating $B_{\text{boot}} = 500$ paired resamples over $b \in \{1, \dots, B\}$:
  $$\text{SE}(\Delta) = \mathbf{541,642,427.01}$$
- Standardized $z$-statistic:
  $$z = \frac{\Delta}{\text{SE}(\Delta)} = \frac{10,220,072.69}{541,642,427.01} = \mathbf{0.0189}$$

The test assertion was updated to use the exact uncertainty for the difference:
```python
# Compute exact paired bootstrap SE for the difference Delta = Var_uncond - Var_total_predicted.
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

discrepancy = abs(var_total_predicted - var_uncond_emp)
assert discrepancy <= 2.58 * se_diff
```
Since $\Delta = 10.22\text{M} \ll 2.58 \times 541.64\text{M} = 1.397\text{B}$, the test passes decisively using the exact uncertainty of the difference.

---

## 3. Horvitz–Thompson Totals vs. Finite-Sample Ratio Estimators

### 3.1 Mathematical Distinction

A fundamental tenet of survey sampling is the distinction between linear total estimators and nonlinear ratio estimators:

#### 1. Population Totals ($\hat{Y}$)
The Horvitz-Thompson total estimator is:
$$\hat{Y} = \sum_{i \in S} w_i y_i = \sum_{i \in U} \frac{I_i}{\pi_i} y_i$$
Taking the design expectation:
$$E_D[\hat{Y}] = \sum_{i \in U} \frac{E_D[I_i]}{\pi_i} y_i = \sum_{i \in U} \frac{\pi_i}{\pi_i} y_i = \sum_{i \in U} y_i = Y$$
**Conclusion:** Horvitz-Thompson totals are **strictly design-unbiased in finite samples** for any sample size $n \ge 1$ and any valid probability design.

#### 2. Ratio Means and Proportions ($\hat{\bar{Y}}$)
In complex surveys where cluster sizes $M_{hi}$ vary or the population size $N$ is estimated from sample weights, the weighted mean is a ratio:
$$\hat{\bar{Y}} = \frac{\sum_{i \in S} w_i y_i}{\sum_{i \in S} w_i} = \frac{\hat{Y}}{\hat{N}}$$
Because both numerator $\hat{Y}$ and denominator $\hat{N}$ are random variables, by bivariate Taylor series expansion:
$$E_D\left[\frac{\hat{Y}}{\hat{N}}\right] = \frac{Y}{N} + \frac{1}{N^2}\left[ \bar{Y}\text{Var}_D(\hat{N}) - \text{Cov}_D(\hat{Y}, \hat{N}) \right] + O\left(\frac{1}{n^2}\right)$$
$$\text{Bias}_D(\hat{\bar{Y}}) \approx \frac{1}{N^2}\left[ \bar{Y}\text{Var}_D(\hat{N}) - \text{Cov}_D(\hat{Y}, \hat{N}) \right] = O\left(\frac{1}{n}\right)$$
(Cochran 1977 Eq 6.13; Särndal, Swensson, & Wretman 1992 Section 5.6).

**Conclusion:** Weighted means and proportions are **NOT strictly design-unbiased in finite samples**. They are **design-consistent** and **asymptotically design-unbiased** as $n \to \infty$. In our large-sample simulations ($n = 20$ PSUs, $N = 31,866$ individuals), the $O(1/n)$ ratio bias is numerically negligible ($< 0.10\%$), but conflating consistency with exact finite-sample unbiasedness is statistically erroneous.

### 3.2 Exact Complete Enumeration Benchmark

In [`test_ratio_estimator_finite_sample_bias_vs_horvitz_thompson_total_unbiasedness`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_monte_carlo.py#L710), a finite population of $N = 4$ PSUs with unequal sizes $M_i \in \{10, 20, 40, 80\}$ and SBP totals $Y_i \in \{1200, 2600, 4800, 11200\}$ was evaluated under all $\binom{4}{2} = 6$ possible SRSWOR samples ($n=2$):

| Estimator | Population Truth | Design Expectation Across All $\binom{4}{2}$ Samples | Design Bias | Relative Bias | Theoretical Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Total ($\hat{Y}$)** | $19,800.0000$ | $19,800.0000$ | **$0.00000000$** | **$0.00\%$** | **Strictly Design-Unbiased** |
| **Ratio Mean ($\hat{\bar{Y}}$)** | $132.0000$ | $129.8519$ | **$-2.1481$** | **$-1.63\%$** | **Design-Consistent ($O(1/n)$)** |

This benchmark proves that while Horvitz-Thompson totals have exact zero finite-sample bias, ratio means have a distinct $O(1/n)$ bias that vanishes only as sample size grows.

---

## 4. FPC Guidance & Technical Partition Safety Guard

### 4.1 The Partition FPC Deflation Hazard

Let $N_h$ be the frame population of PSUs in stratum $h$, $n_h$ be the full sample count, and $n_{h, k}$ be the partition $k$ count.
- Full sample frame fraction: $f_h = n_h / N_h$. Multiplier: $1 - f_h$.
- Partition frame fraction: $f_{h, k} = n_{h, k} / N_h = p_{h, k} f_h$. Multiplier: $1 - p_{h, k} f_h$.

If a caller passes $f_h$ (the full-sample fraction) to analyze partition records, the variance estimator erroneously uses $(1 - f_h)$ instead of $(1 - p_{h, k} f_h)$.
Because $p_{h, k} < 1$, we have $(1 - f_h) < (1 - p_{h, k} f_h)$. The resulting variance is deflated by:
$$\text{Deflation Factor} = \frac{1 - f_h}{1 - p_{h, k} f_h} < 1$$
For example, if $f_h = 0.50$ and $p_k = 0.40$, variance is deflated by $\frac{0.50}{0.80} = 0.625$ (a $-37.5\%$ artificial underestimate of variance!).

### 4.2 Implementation of Technical Safeguards

To make it impossible for callers to accidentally trigger this deflation:

1. **Partition Stamping on Cleaned Records:**
   In [`synapse_simulator/evaluation/lasi/models.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py#L149), `LasiCleanedRecord` includes `partition_label: Optional[str] = None`.
   In [`synapse_simulator/evaluation/lasi/partitioner.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L711), partitioned records are stamped with `"PARTITION_A"` or `"PARTITION_C"`.
2. **Deterministic Partition FPC Derivation:**
   In [`synapse_simulator/evaluation/lasi/partitioner.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L147), `LasiPartitionResult` provides:
   ```python
   def get_partition_fpc(
       self,
       partition: PartitionLabel,
       full_fpc_by_stratum: Dict[str, float],
   ) -> Dict[str, float]:
       # Computes f_{h,k} = (n_{h,k} / n_h) * f_h
   ```
3. **Strict Exception Guard in Variance Engine:**
   In [`synapse_simulator/evaluation/lasi/variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L231), `calculate_taylor_linearized_mean_and_se` and `calculate_taylor_linearized_total_and_se` inspect incoming records:
   ```python
   is_partitioned = any(getattr(r, "partition_label", None) is not None for r in records)
   if is_partitioned and fpc_by_stratum is not None:
       if not fpc_is_partition_adjusted and not full_stratum_psu_counts:
           raise ValueError(
               "Detected partitioned survey records analyzed with FPC. You must not pass the "
               "unadjusted full-sample FPC fraction, as this deflates variance anti-conservatively. "
               "Derive the partition fraction via LasiPartitionResult.get_partition_fpc(...) "
               "and pass fpc_is_partition_adjusted=True, or supply full_stratum_psu_counts."
           )
   ```
4. **Auto-Scaling Fallback:**
   If `full_stratum_psu_counts` is supplied, `variance.py` automatically scales $f_h$ by $n_{h, k} / n_{h, \text{full}}$, ensuring correct variance scaling without error.

Validated in regression test [`test_fpc_partition_guard_blocks_unadjusted_full_sample_fraction`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_monte_carlo.py#L644).

---

## 5. Consolidated Statistical Architecture Matrix

| Property | Statistical Classification | Governing Theorem / Formula | Verified Status |
| :--- | :--- | :--- | :---: |
| **Population Totals ($\hat{Y}$)** | **Strictly Design-Unbiased** | Horvitz-Thompson: $E_D[\hat{Y}] = \sum_{U} \frac{\pi_i}{\pi_i} y_i \equiv Y$ | **VERIFIED** |
| **Ratio Means & Proportions ($\hat{\bar{Y}}$)** | **Design-Consistent** | Cochran Eq 6.13: $\text{Bias}(\hat{\bar{Y}}) = O(1/n) \to 0$ as $n \to \infty$ | **VERIFIED** |
| **Eve's Law Additivity** | **Additive Partition Variance** | $Var(Y) = Var_S(E[Y\mid S]) + E_S[Var(Y\mid S)]$; $\Delta \le 2.58\,\text{SE}_{\text{diff}}$ | **VERIFIED** |
| **FPC Application** | **Single-Stage Hypergeometric** | Stratum multiplier $1 - f_h$; zero double application | **VERIFIED** |
| **Partition FPC Protection** | **Technical Guard** | Enforces $f_{h, k} = p_{h, k} f_h$; blocks full $f_h$ on partitions | **VERIFIED** |
| **$1/p_k$ Variance Scaling** | **Disproved in General** | Violations: $f > 0$, integer rounding, ratio cancellation, $df$ shift | **DISPROVED** |
| **Singleton Handling** | **Grand Mean Centering** | Centering around theoretical mean 0 avoids variance collapse | **VERIFIED** |
| **Degrees of Freedom** | **$t$-Distributed** | $df = n_{\text{PSU}} - H$; uses exact Student's $t$ lookup | **VERIFIED** |

---

## 6. Verification and Governance Commitments

1. **Synthetic Data Exclusivity:** All experiments, benchmarks, and regression tests were conducted exclusively using synthetic microdata. Zero genuine LASI records were accessed or inspected.
2. **Clinical Default Invariance:** Zero clinical parameters, blood pressure cutoffs, disease prevalences, or biological mechanisms were modified or calibrated.
3. **Reference Data Invariant:** The external empirical reference gate in [`models.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/modules/models.py) remains strictly locked at:
   ```python
   REFERENCE_DATA_PENDING = "PENDING_EXTERNAL_REFERENCE_UNBLINDING"
   ```
4. **Final Suite Status:**
   ```bash
   .venv/bin/pytest
   ============================= 368 passed in 12.15s =============================
   ```
   No further audit phases required; documentation consolidated and implementation fully hardened.
