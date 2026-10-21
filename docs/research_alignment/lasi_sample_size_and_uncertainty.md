# SYNAPSE Phase 2: LASI Sample-Size, Effective-Sample-Size, and Survey Uncertainty Gates

**Document ID:** `SYNAPSE-LASI-SAMPLE-AUDIT-04`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** IMPLEMENTED, GATED & INDEPENDENTLY VERIFIED  

---

## 1. Executive Summary & Problem Identification

In prior testing, a distribution comparison for $\text{HbA1c}$ evaluated $N=1$ synthetic patient against $N=49$ reference observations, producing an empirical distance metric that passed or generated a generic warning. 

In statistical inference, comparing an empirical distribution with $N=1$ or $N<30$ against a continuous population distribution is mathematically degenerate. A single point has zero empirical variance, cannot populate quantile bands, and produces arbitrary Kolmogorov–Smirnov ($D_{\text{KS}}$) and Wasserstein distances that reflect sample starvation rather than model validity.

Furthermore, in complex multistage surveys like LASI, unweighted record counts dramatically overestimate true statistical power due to sample clustering and unequal selection probabilities.

This document establishes the minimum sample-size gates, Kish's effective-sample-size formulas, survey design-effect adjustments, and dedicated validation statuses implemented in [`synapse_simulator/evaluation/lasi/evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py).

---

## 2. Minimum Sample-Size Requirements and Statistical Justification

Before processing genuine microdata, the pipeline enforces strict pre-release sample-size thresholds based on standard power calculations and asymptotic distribution theory:

| Metric Type | Estimand | Minimum Synthetic $N$ | Minimum Reference $N$ | Minimum Reference $n_{\text{eff}}$ | Scientific & Statistical Justification |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Continuous Distribution** | SBP, DBP, HbA1c (KS test, Wasserstein) | **30** | **30** | **25.0** | Central Limit Theorem and asymptotic convergence of empirical cumulative distribution functions (ECDF). With $N < 30$, two-sample Kolmogorov–Smirnov tests lack power to reject even massive distributional shifts ($\Delta > 15\text{ mmHg}$). |
| **Binary Prevalence** | HTN, T2DM, CKD (Wilson Score / Weighted CI) | **20** | **20** | **15.0** | Normal approximation to binomial / multinomial proportions requires $N \cdot p \ge 5$ and $N(1-p) \ge 5$. In older adults, chronic condition prevalences range from $5\%$ to $35\%$; $N < 20$ yields undefined or degenerate confidence bounds. |
| **Direct Age-Sex Stratum** | Cell-specific mean or proportion | **5** | **5** | **4.0** | Required to compute non-degenerate intra-stratum sample variances $\sigma_k^2$. Strata with $N < 5$ trigger empty/insufficient stratum flags. |

---

## 3. Complex Survey Weighting and Effective Sample Size Formulation

### 3.1 Kish's Effective Sample Size Formula
In LASI, participants are sampled with unequal probabilities across states, urban/rural strata, and oversampled older cohorts. Unequal sampling weights increase the variance of sample estimators.

The effective sample size ($n_{\text{eff}}$) quantifies the equivalent number of independent and identically distributed (i.i.d.) observations that would yield the same precision as the weighted sample. In [`synapse_simulator/evaluation/metrics.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/metrics.py), $n_{\text{eff}}$ is computed via Kish's classic design-effect formulation:

$$n_{\text{eff}} = \frac{\left( \sum_{i=1}^n w_i \right)^2}{\sum_{i=1}^n w_i^2}$$

where $w_i$ is the sampling weight (`r1wtresp`) for respondent $i$.

### 3.2 Weighting Design Effect ($\text{DEFF}_w$)
The inflation in sampling variance attributable solely to unequal weighting is:

$$\text{DEFF}_w = \frac{n}{n_{\text{eff}}} = 1 + \text{CV}(w)^2$$

where $\text{CV}(w) = \frac{s_w}{\bar{w}}$ is the coefficient of variation of the sampling weights.

### 3.3 Design-Adjusted Standard Error and Confidence Intervals
For a weighted prevalence $\hat{p} = \frac{\sum w_i y_i}{\sum w_i}$, the naive unweighted binomial variance severely underestimates true parameter uncertainty. The pipeline implements the design-adjusted standard error:

$$\text{SE}_{\text{design}}(\hat{p}) = \sqrt{\frac{\hat{p}(1 - \hat{p})}{n_{\text{eff}}}} = \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} \cdot \text{DEFF}_w}$$

The $(1 - \alpha)$ confidence interval is calculated as:

$$\hat{p} \pm z_{1 - \alpha/2} \cdot \text{SE}_{\text{design}}(\hat{p})$$

---

## 4. Dedicated Gate Status Classifications

To prevent false-positive validation claims and avoid collapsing distinct statistical failures into ambiguous warnings, the pipeline emits dedicated gate statuses in `LasiMetricStatus`:

```python
class LasiMetricStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNVERIFIED = "UNVERIFIED"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    INSUFFICIENT_SAMPLE_SIZE = "INSUFFICIENT_SAMPLE_SIZE"
    INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE = "INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE"
    REFERENCE_DATA_PENDING = "REFERENCE_DATA_PENDING"
```

### Gate Decision Logic
1. **Raw Sample Size Gate:**
   - If synthetic $N < N_{\text{min}}$ or reference $N < N_{\text{min}}$:
     $$\text{Status} \leftarrow \text{INSUFFICIENT\_SAMPLE\_SIZE}$$
   - *Example:* In test fixtures with $N=11$ synthetic SBP measurements, status is explicitly `INSUFFICIENT_SAMPLE_SIZE` (preventing silent PASS).
2. **Effective Sample Size Gate:**
   - If reference $n_{\text{eff}} < n_{\text{eff, min}}$:
     $$\text{Status} \leftarrow \text{INSUFFICIENT\_EFFECTIVE\_SAMPLE\_SIZE}$$
3. **Assay Incompatibility Gate:**
   - If outcome definitions or assay modalities diverge without verified calibration (e.g., DBS vs venous HbA1c):
     $$\text{Status} \leftarrow \text{UNVERIFIED}$$
4. **Authentic Microdata Gate:**
   - If evaluated against test fixtures rather than genuine licensed microdata:
     $$\text{Overall Gate Status} \leftarrow \text{REFERENCE\_DATA\_PENDING}$$

---

## 5. Independent Analytical Verification of Survey Metrics

In [`tests/test_lasi_pipeline.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_lasi_pipeline.py), the statistical functions were verified against independent hand-calculated benchmarks:

### Case 1: Unequal Survey Weights
- **Sample Weights:** $W = [1.0, 2.0, 3.0, 4.0]$ ($n = 4$).
- **Calculations:**
  $$\sum w_i = 1 + 2 + 3 + 4 = 10.0$$
  $$\sum w_i^2 = 1^2 + 2^2 + 3^2 + 4^2 = 1 + 4 + 9 + 16 = 30.0$$
  $$n_{\text{eff}} = \frac{10.0^2}{30.0} = \frac{100.0}{30.0} = 3.333333$$
  $$\text{DEFF}_w = \frac{4}{3.333333} = 1.200000$$
- **Unit Test Output:** Matches to 6 decimal places (`3.333333`).

### Case 2: Survey-Weighted Prevalence & Design-Adjusted CI
- **Values:** $Y = [1, 1, 0, 0]$
- **Weights:** $W = [2.0, 2.0, 1.0, 1.0]$ ($n = 4$)
- **Weighted Prevalence:**
  $$\hat{p} = \frac{2(1) + 2(1) + 1(0) + 1(0)}{2 + 2 + 1 + 1} = \frac{4.0}{6.0} = 0.666667$$
- **Effective Sample Size:**
  $$\sum w_i = 6.0, \quad \sum w_i^2 = 4 + 4 + 1 + 1 = 10.0$$
  $$n_{\text{eff}} = \frac{6.0^2}{10.0} = \frac{36.0}{10.0} = 3.600000$$
- **Standard Error:**
  $$\text{SE} = \sqrt{\frac{0.666667 \times (1 - 0.666667)}{3.600000}} = \sqrt{\frac{0.222222}{3.600000}} = \sqrt{0.061728} \approx 0.248452$$
- **95% Confidence Interval ($z = 1.96$):**
  $$\text{Margin} = 1.959964 \times 0.248452 = 0.486957$$
  $$\text{Lower Bound} = \max(0.0, 0.666667 - 0.486957) = 0.179710$$
  $$\text{Upper Bound} = \min(1.0, 0.666667 + 0.486957) = 1.000000$$
- **Unit Test Output:** Matches exact hand-calculated boundaries.

---

## 6. Audit Verdict

Sample-size and effective-sample-size gates are **fully active and verified**. The pipeline cleanly blocks underpowered comparisons, distinguishes between sample starvation and model divergence, and prevents false validation passes.
