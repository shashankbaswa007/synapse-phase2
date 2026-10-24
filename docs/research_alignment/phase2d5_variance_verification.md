# SYNAPSE Phase 2D.5 — Complex Survey Variance Verification & Uncertainty Audit

**Document ID:** `SYNAPSE-AUDIT-2026-PHASE2D5-VARIANCE-VERIFICATION`  
**Classification:** Statistical Methodology, Survey Inference, Taylor Linearization, Degrees of Freedom, and Monte Carlo Uncertainty  
**Target Repository:** `synapse-phase2` (`/Users/shashi/synapse/synapse-phase2`)  
**Implementation Milestone:** Milestone 4 Pre-Flight Verification (Variance Engine Audit & Independent Mathematical Benchmarks)  
**Date:** October 2026  
**External Validation Gate Status:** **`REFERENCE_DATA_PENDING`** (Strictly Preserved)  

---

## 1. Executive Summary & Verification Scope

Before entering Milestone 4 (Empirical Partitioning and Calibration), this audit conducts an independent mathematical and statistical verification of the complex survey variance engine ([`synapse_simulator/evaluation/lasi/variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py)) and the survey design documentation ([`docs/research_alignment/phase2d4_survey_design_missingness.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d4_survey_design_missingness.md)).

### 1.1 Key Verification Outcomes
1. **Taylor Series Linearization (TSL):** Mathematically derived and verified the linearized observation score $z_{hij} = \frac{w_{hij}}{\widehat{N}} (y_{hij} - \bar{y}_w)$ and PSU-level aggregation $z_{hi} = \sum_j z_{hij}$ for weighted means and proportions. Added a dedicated proportion variance estimator ([`calculate_taylor_linearized_proportion_and_se`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L317)) with logit-transformed confidence intervals guaranteeing coverage within $[0, 1]$.
2. **Singleton PSU Protocols:** Audited `CERTAINTY`, `GRAND_MEAN_CENTERING`, and `COLLAPSE_STRATA` against established survey literature (Stata `svyset`, R `survey`). Proved that `CERTAINTY` causes anti-conservative variance underestimation without proof of self-representing sampling, and added safety telemetry. Corrected a boundary condition in stratum collapsing that previously bypassed singletons at the end of the design order.
3. **Design Degrees of Freedom & Student's $t$ Multipliers:** Established exact design degrees of freedom $df = \sum_{h=1}^H n_h - H = K - H$. Replaced fixed standard normal $z = 1.96$ multipliers with exact Student's $t$ critical values ($t_{df, 1-\alpha/2}$), preventing catastrophic under-coverage when $df < 12$. Implemented exact NIST lookup for $df \in [1, 30]$ and Hill's Cornish-Fisher expansion for $df \in [31, 120]$.
4. **Independent Hand-Calculated Reference Benchmarks:** Formulated an independent, non-trivial 2-stratum, 4-PSU, 7-observation dataset with unequal weights and verified rational arithmetic against the engine, confirming exact matches to 5 decimal places.
5. **Finite Population Correction (FPC):** Added stratum-level sampling fraction support $(1 - f_h)$, documenting the baseline conservative assumption of $f_h = 0.0$ (sampling with replacement / negligible sampling fraction).
6. **Separation of Uncertainties & Independence Assumptions:** Formalized the additive variance formula $\text{Var}(\Delta) = \text{Var}_{\text{survey}} + \frac{\text{Var}_{\text{sim}}}{M}$. Explicitly proved that the required independence assumption $\text{Cov}(\bar{\theta}_{\text{sim}}, \widehat{\theta}_{\text{ref}}) = 0$ holds strictly for uncalibrated baseline evaluation and holdout validation (Partition C), but is violated if model parameters are calibrated directly on the same reference data.
7. **External Validation Gate Lockdown:** The validation gate remains strictly at **`REFERENCE_DATA_PENDING`**. Zero parameter tuning, data partitioning, or clinical default alterations were performed.

---

## 2. Mathematical Derivation of Taylor Series Linearization

### 2.1 Multi-Stage Complex Survey Estimands

Consider a finite population partitioned into $H$ mutually exclusive strata. In stratum $h \in \{1, \dots, H\}$, $n_h$ Primary Sampling Units (PSUs) are selected. Within PSU $i \in \{1, \dots, n_h\}$, $m_{hi}$ ultimate observation units (individuals) are sampled.

Each observation $(h, i, j)$ has:
- Observed value: $y_{hij} \in \mathbb{R}$ (continuous for means, $y_{hij} \in \{0, 1\}$ for proportions).
- Sampling design weight: $w_{hij} > 0$.
- Primary sampling fraction: $f_h = \frac{n_h}{N_h}$ (where $N_h$ is the total population of PSUs in stratum $h$).

The total estimated population size is:
$$\widehat{N} = \sum_{h=1}^H \sum_{i=1}^{n_h} \sum_{j=1}^{m_{hi}} w_{hij}$$

The survey-weighted mean estimand is the ratio of two Horvitz-Thompson / Hansen-Hurwitz totals:
$$\bar{y}_w = \frac{\widehat{Y}}{\widehat{N}} = \frac{\sum_{h=1}^H \sum_{i=1}^{n_h} \sum_{j=1}^{m_{hi}} w_{hij} y_{hij}}{\sum_{h=1}^H \sum_{i=1}^{n_h} \sum_{j=1}^{m_{hi}} w_{hij}}$$

### 2.2 First-Order Taylor Linearization Residuals

Because $\bar{y}_w = g(\widehat{Y}, \widehat{N}) = \frac{\widehat{Y}}{\widehat{N}}$ is a non-linear ratio estimator, its variance cannot be computed as a simple sum of variances. We expand $g(\widehat{Y}, \widehat{N})$ in a first-order Taylor series about the true population totals $(Y, N)$:

$$g(\widehat{Y}, \widehat{N}) \approx g(Y, N) + \left.\frac{\partial g}{\partial \widehat{Y}}\right|_{(Y, N)} (\widehat{Y} - Y) + \left.\frac{\partial g}{\partial \widehat{N}}\right|_{(Y, N)} (\widehat{N} - N)$$

The partial derivatives are:
$$\frac{\partial g}{\partial \widehat{Y}} = \frac{1}{N}, \quad \frac{\partial g}{\partial \widehat{N}} = -\frac{Y}{N^2} = -\frac{\bar{Y}}{N}$$

Substituting sample estimates $(\widehat{Y}, \widehat{N}, \bar{y}_w)$ yields the linearized observation residual score for respondent $j$ in PSU $i$ of stratum $h$:
$$z_{hij} = \frac{1}{\widehat{N}} \left( w_{hij} y_{hij} - w_{hij} \bar{y}_w \right) = \frac{w_{hij}}{\widehat{N}} (y_{hij} - \bar{y}_w)$$

Notice the critical identity:
$$\sum_{h=1}^H \sum_{i=1}^{n_h} \sum_{j=1}^{m_{hi}} z_{hij} = \frac{1}{\widehat{N}} \sum_{h,i,j} w_{hij} (y_{hij} - \bar{y}_w) = \bar{y}_w - \bar{y}_w \equiv 0$$

The sum of linearized residuals across the entire sample is identically zero.

### 2.3 PSU Aggregation & Stratum Variance

In multi-stage cluster sampling, within-PSU sampling variation is absorbed into the primary-stage cluster variance (ultimate cluster principle, Hansen, Hurwitz & Madow 1953). We aggregate observation residuals to the PSU level:

$$z_{hi} = \sum_{j=1}^{m_{hi}} z_{hij} = \frac{1}{\widehat{N}} \left( y_{hi} - \bar{y}_w w_{hi} \right)$$
where $y_{hi} = \sum_{j=1}^{m_{hi}} w_{hij} y_{hij}$ and $w_{hi} = \sum_{j=1}^{m_{hi}} w_{hij}$.

The stratum mean of linearized PSU totals is:
$$\bar{z}_h = \frac{1}{n_h} \sum_{i=1}^{n_h} z_{hi}$$

> [!NOTE]
> While $\sum_{h=1}^H \sum_{i=1}^{n_h} z_{hi} \equiv 0$, the stratum-specific mean $\bar{z}_h$ is **not** generally zero unless the stratum weighted mean $\bar{y}_{wh} = \bar{y}_w$.

For strata with $n_h \ge 2$, the stratum variance contribution accounting for finite population correction $f_h$ is:
$$\widehat{\text{Var}}_h = (1 - f_h) \frac{n_h}{n_h - 1} \sum_{i=1}^{n_h} (z_{hi} - \bar{z}_h)^2$$

Total Taylor Series Linearized Variance:
$$\widehat{\text{Var}}(\bar{y}_w) = \sum_{h=1}^H \widehat{\text{Var}}_h, \quad \widehat{\text{SE}}(\bar{y}_w) = \sqrt{\widehat{\text{Var}}(\bar{y}_w)}$$

### 2.4 Proportions and Logit-Transformed Intervals

A survey proportion $p_w = \frac{\sum w_{hij} y_{hij}}{\sum w_{hij}}$ is mathematically identical to a weighted mean where $y_{hij} \in \{0, 1\}$. Its Taylor linearized variance $\widehat{\text{Var}}(p_w)$ follows the exact same formula.

However, constructing a standard Wald confidence interval:
$$\text{CI}_{\text{Wald}} = p_w \pm t_{df, 1-\alpha/2} \widehat{\text{SE}}(p_w)$$
frequently results in severe failure: when $p_w$ is near $0$ or $1$, or when design degrees of freedom are small, the Wald interval can produce lower bounds $< 0$ or upper bounds $> 1$.

To resolve this, [`calculate_taylor_linearized_proportion_and_se`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L317) implements the **logit-transformed confidence interval** (Korn & Graubard 1998):

1. Transform proportion to log-odds:
   $$\eta = \text{logit}(p_w) = \ln\left(\frac{p_w}{1 - p_w}\right)$$
2. Delta-method standard error on logit scale:
   $$\widehat{\text{SE}}(\eta) = \frac{\widehat{\text{SE}}(p_w)}{p_w (1 - p_w)}$$
3. Compute confidence bounds on logit scale:
   $$[\eta_L, \eta_U] = \eta \pm t_{df, 1-\alpha/2} \widehat{\text{SE}}(\eta)$$
4. Transform back via inverse logit ($\text{expit}$):
   $$p_L = \frac{1}{1 + e^{-\eta_L}}, \quad p_U = \frac{1}{1 + e^{-\eta_U}}$$

Because $\text{expit}(x) \in (0, 1)$ for all $x \in \mathbb{R}$, $[p_L, p_U]$ is mathematically guaranteed to lie strictly within the valid probability space $[0, 1]$.

---

## 3. Singleton PSU Protocols & Methodological Audit

When a stratum contains only one PSU ($n_h = 1$), the stratum degrees of freedom $n_h - 1 = 0$, causing division by zero in $\frac{n_h}{n_h - 1}$.

### 3.1 Comparative Audit of Recognized Protocols

| Strategy | Mathematical Formula | Statistical Interpretation | Literature Standard | Suitability in SYNAPSE |
| :--- | :--- | :--- | :--- | :--- |
| **`CERTAINTY`** | $\widehat{\text{Var}}_h = 0.0$ | Treats stratum as sampled with certainty (self-representing). All variance attributed to sub-stages. | Stata `singleunit(certainty)` | **UNSAFE as default.** Requires empirical proof of certainty sampling. Causes anti-conservative SE underestimation. |
| **`GRAND_MEAN_CENTERING`** | $\widehat{\text{Var}}_h = (1 - f_h) (z_{h1} - 0)^2 = z_{h1}^2$ | Centers singleton PSU around the theoretical sample grand mean (which is identically 0). | Stata `singleunit(centered)`, R `survey.lonely.psu = "adjust"` | **RECOMMENDED DEFAULT.** Conservative; bounds variance without modifying strata boundaries. |
| **`COLLAPSE_STRATA`** | Merges stratum $h$ ($n_h=1$) with adjacent stratum $h'$ in design order. | Treats adjacent strata as a single stratum with $n_{h+h'} \ge 2$. | Wolter (2007), Kish (1965) | **VALID ALTERNATIVE.** Strictly preserves design degrees of freedom without arbitrary geographic heuristics. |

### 3.2 Audit Findings on Implementation Deficiencies

#### Defect 1: Centering Around Sample Grand Mean of Scores
- **Previous Code:** Computed `grand_z_bar = sum(all_z_bars) / len(all_z_bars)` where `all_z_bars` was the unweighted list of stratum means. Because strata have unequal PSU counts, this produced a non-zero artifact (e.g. $0.002$).
- **Correction:** Under Taylor linearization, the sample grand total of observation scores $\sum_{h,i,j} z_{hij} \equiv 0$. The theoretical center for singleton residuals is identically $0.0$, yielding $\widehat{\text{Var}}_h = z_{h1}^2$. This precisely aligns with Stata's `singleunit(centered)`.

#### Defect 2: Loop Boundary Bug in Strata Collapsing
- **Previous Code:**
  ```python
  if len(psus) == 1 and (i + 1) < len(sorted_strata):
      # collapse with i + 1
  else:
      new_strata_psu[current_s] = psus
  ```
  If the singleton stratum happened to be the **last** stratum in `sorted_strata` (e.g. `Stratum_Z`), `(i + 1) < len` evaluated to `False`. The last stratum was dropped into the `else` block, remaining an uncollapsed singleton. In the variance pass, it silently defaulted to $0.0$ variance.
- **Correction:** Implemented bidirectional collapsing: if the singleton is at index $i < \text{len} - 1$, merge with $i + 1$; if the singleton is at the end of the list ($i = \text{len} - 1$), merge into the preceding stratum $i - 1$.

#### Defect 3: Permissive Certainty Default
- **Previous Code:** Permitted `CERTAINTY` without telemetry warnings.
- **Correction:** Added an explicit telemetry warning whenever `CERTAINTY` is selected:
  `"CERTAINTY strategy assumes singleton PSUs were sampled with certainty (self-representing). Without empirical verification, this causes anti-conservative variance underestimation."`

---

## 4. Design Degrees of Freedom & Student's $t$ Distribution

### 4.1 Design Degrees of Freedom Formulation

For a stratified multi-stage cluster design with $H$ strata and $K = \sum_{h=1}^H n_h$ total PSUs:
$$df = \sum_{h=1}^H (n_h - 1) = K - H$$

In survey statistics, degrees of freedom depend on the number of primary sampling clusters ($K$) and strata ($H$), **not** on the number of individual respondents ($N$).

### 4.2 Failure of the Fixed Normal Approximation ($z = 1.96$)

In naive implementations, confidence intervals are constructed using $z = 1.96$ regardless of sample design. When degrees of freedom are small (e.g. in subpopulation analyses, regional domains, or sparse disease strata), this produces catastrophic under-coverage:

| Design $df$ | Student's $t_{df, 0.975}$ | Fixed Normal $z_{0.975}$ | Understatement of Margin of Error |
| :---: | :---: | :---: | :---: |
| **$df = 1$** | $12.706$ | $1.960$ | **$84.6\%$ too narrow** |
| **$df = 2$** | $4.303$ | $1.960$ | **$54.5\%$ too narrow** |
| **$df = 3$** | $3.182$ | $1.960$ | **$38.4\%$ too narrow** |
| **$df = 5$** | $2.571$ | $1.960$ | **$23.8\%$ too narrow** |
| **$df = 10$** | $2.228$ | $1.960$ | **$12.0\%$ too narrow** |
| **$df = 30$** | $2.042$ | $1.960$ | **$4.0\%$ too narrow** |
| **$df \ge 120$** | $1.980 \to 1.960$ | $1.960$ | Asymptotic convergence ($< 1.0\%$) |

### 4.3 Implemented Critical Multiplier Algorithm ([`student_t_critical_value`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L86))

To ensure complete platform portability without requiring heavy third-party dependencies (like SciPy), the engine implements a hybrid two-tier algorithm:
1. **Exact NIST Lookup Tables ($df \in [1, 30]$):** Pre-compiled NIST double-precision critical values for two-sided $\alpha \in \{0.10, 0.05, 0.01\}$.
2. **Hill (1970) Cornish-Fisher Expansion ($df \in [31, 120]$):**
   $$t_{df} \approx z + \frac{z^3 + z}{4 df} + \frac{5z^5 + 16z^3 + 3z}{96 df^2} + \frac{3z^7 + 19z^5 + 17z^3 - 15z}{384 df^3}$$
   where $z = \Phi^{-1}(1 - \alpha/2)$ is computed via Acklam's rational approximation. Maximum absolute error vs. full numerical integration is $< 2 \times 10^{-6}$.
3. **Sparse Degrees of Freedom Rules:**
   - If $df < 12$: Telemetry emits a `low_df_warning` and applies $t_{df}$ penalization, aligning with National Center for Health Statistics (NCHS) guidelines.
   - If $df \le 0$: Telemetry marks `insufficient_df: True` and returns `NaN` for confidence bounds, preventing spurious inference.

---

## 5. Independent Hand-Calculated Reference Benchmarks

To establish an unassailable mathematical baseline, a reference dataset was hand-calculated using exact rational arithmetic and verified against [`tests/test_survey_variance_hand_calculations.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_survey_variance_hand_calculations.py).

### 5.1 Reference Survey Design Specification

- **Total Sample:** $N = 7$ observations.
- **Strata:** $H = 2$ (`S1`, `S2`).
- **Primary Sampling Units:** $K = 4$ (`P11`, `P12`, `P21`, `P22`).
- **Unequal Sampling Weights:** $w \in \{1, 2, 3, 4, 5, 10\}$.

```mermaid
graph TD
    POP[Sample Population: N=7, Total W=30] --> S1[Stratum S1: W=10]
    POP --> S2[Stratum S2: W=20]
    
    S1 --> P11[PSU P11: W=5]
    S1 --> P12[PSU P12: W=5]
    
    S2 --> P21[PSU P21: W=10]
    S2 --> P22[PSU P22: W=10]
    
    P11 --> O1["Obs 1: y=120 (bin=1), w=2"]
    P11 --> O2["Obs 2: y=140 (bin=0), w=3"]
    
    P12 --> O3["Obs 3: y=130 (bin=1), w=4"]
    P12 --> O4["Obs 4: y=150 (bin=0), w=1"]
    
    P21 --> O5["Obs 5: y=110 (bin=0), w=5"]
    P21 --> O6["Obs 6: y=160 (bin=1), w=5"]
    
    P22 --> O7["Obs 7: y=136 (bin=0), w=10"]
```

### 5.2 Hand Calculation: Continuous Weighted Mean

1. **Total Weight & Weighted Sum:**
   $$\widehat{N} = 2 + 3 + 4 + 1 + 5 + 5 + 10 = 30$$
   $$\widehat{Y} = 2(120) + 3(140) + 4(130) + 1(150) + 5(110) + 5(160) + 10(136) = 240 + 420 + 520 + 150 + 550 + 800 + 1360 = 4040$$
   $$\bar{y}_w = \frac{4040}{30} = \frac{404}{3} \approx 134.6667\text{ mmHg}$$

2. **PSU Linearized Residual Totals ($z_{hi} = \frac{y_{hi} - \bar{y}_w w_{hi}}{\widehat{N}}$):**
   - **PSU 11:** $y_{11} = 660, w_{11} = 5 \implies z_{11} = \frac{660 - 5(404/3)}{30} = \frac{1980 - 2020}{90} = -\frac{40}{90} = -\frac{4}{9}$
   - **PSU 12:** $y_{12} = 670, w_{12} = 5 \implies z_{12} = \frac{670 - 5(404/3)}{30} = \frac{2010 - 2020}{90} = -\frac{10}{90} = -\frac{1}{9}$
   - **PSU 21:** $y_{21} = 1350, w_{21} = 10 \implies z_{21} = \frac{1350 - 10(404/3)}{30} = \frac{4050 - 4040}{90} = \frac{10}{90} = \frac{1}{9}$
   - **PSU 22:** $y_{22} = 1360, w_{22} = 10 \implies z_{22} = \frac{1360 - 10(404/3)}{30} = \frac{4080 - 4040}{90} = \frac{40}{90} = \frac{4}{9}$
   $$\sum_{h,i} z_{hi} = -\frac{4}{9} - \frac{1}{9} + \frac{1}{9} + \frac{4}{9} \equiv 0$$

3. **Stratum Variance Contributions:**
   - **Stratum 1 ($n_1 = 2$):** $\bar{z}_1 = \frac{-4/9 + (-1/9)}{2} = -\frac{5}{18}$
     $$(z_{11} - \bar{z}_1) = -\frac{8}{18} - (-\frac{5}{18}) = -\frac{3}{18} = -\frac{1}{6}, \quad (z_{12} - \bar{z}_1) = \frac{1}{6}$$
     $$\widehat{\text{Var}}_1 = \frac{2}{2 - 1} \left[ \left(-\frac{1}{6}\right)^2 + \left(\frac{1}{6}\right)^2 \right] = 2 \left( \frac{2}{36} \right) = \frac{1}{9} \approx 0.111111$$
   - **Stratum 2 ($n_2 = 2$):** $\bar{z}_2 = \frac{1/9 + 4/9}{2} = \frac{5}{18}$
     $$(z_{21} - \bar{z}_2) = -\frac{1}{6}, \quad (z_{22} - \bar{z}_2) = \frac{1}{6} \implies \widehat{\text{Var}}_2 = \frac{1}{9} \approx 0.111111$$

4. **Total Variance & Confidence Interval ($df = 4 - 2 = 2$):**
   $$\widehat{\text{Var}}(\bar{y}_w) = \frac{1}{9} + \frac{1}{9} = \frac{2}{9} \approx 0.222222$$
   $$\widehat{\text{SE}}(\bar{y}_w) = \sqrt{\frac{2}{9}} = \frac{\sqrt{2}}{3} \approx 0.471405$$
   $$t_{2, 0.975} = 4.302653$$
   $$\text{Margin of Error} = 4.302653 \times 0.471405 = 2.0283$$
   $$95\%\text{ CI} = [134.6667 - 2.0283, 134.6667 + 2.0283] = [132.6384, 136.6950]$$

### 5.3 Hand Calculation: Binary Proportion & Logit Interval

Using the binary indicators from the same dataset ($y \in \{0, 1\}$):
- Positive cases: $\widehat{Y} = 2(1) + 4(1) + 5(1) = 11$. Total $N = 30$.
- Weighted proportion: $p_w = \frac{11}{30} \approx 0.366667$.
- PSU residuals:
  $z_{11} = \frac{2 - 5(11/30)}{30} = \frac{1}{180}$, $z_{12} = \frac{13}{180}$, $z_{21} = \frac{4}{90} = \frac{8}{180}$, $z_{22} = -\frac{11}{90} = -\frac{22}{180}$.
- Stratum variances:
  $\widehat{\text{Var}}_1 = \frac{1}{225} \approx 0.004444$, $\widehat{\text{Var}}_2 = \frac{1}{36} \approx 0.027778$.
- Total Variance & SE:
  $$\widehat{\text{Var}}(p_w) = \frac{1}{225} + \frac{1}{36} = \frac{29}{900} \approx 0.032222 \implies \widehat{\text{SE}}(p_w) = \frac{\sqrt{29}}{30} \approx 0.179505$$
- **Wald 95% Interval ($df = 2, t = 4.302653$):**
  $$0.3667 \pm 4.302653(0.179505) = 0.3667 \pm 0.7723 = \mathbf{[-0.4057, 1.1390]} \quad \text{(VIOLATES [0, 1] BOUNDS)}$$
- **Logit-Transformed 95% Interval:**
  $$\eta = \ln\left(\frac{11/30}{19/30}\right) = \ln\left(\frac{11}{19}\right) \approx -0.54654$$
  $$\widehat{\text{SE}}(\eta) = \frac{\sqrt{29}/30}{(11/30)(19/30)} = \frac{30\sqrt{29}}{209} \approx 0.77300$$
  $$\text{Half-width} = 4.302653 \times 0.77300 = 3.3260$$
  $$[\eta_L, \eta_U] = [-0.54654 - 3.3260, -0.54654 + 3.3260] = [-3.8725, 2.7795]$$
  $$p_L = \frac{1}{1 + e^{3.8725}} \approx \mathbf{0.0204}, \quad p_U = \frac{1}{1 + e^{-2.7795}} \approx \mathbf{0.9416} \quad \text{(STRICTLY IN [0, 1])}$$

### 5.4 Verification Results Summary

The implementation in [`variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py) reproduces these hand-calculated values to exact numerical precision:
- Weighted mean: $134.6667$ (Exact match).
- Weighted mean SE: $0.4714$ (Exact match).
- Degrees of freedom: $2$ (Exact match).
- $t$-multiplier: $4.3027$ (Exact match).
- Mean 95% CI: $[132.6384, 136.6950]$ (Exact match).
- Proportion: $0.3667$ (Exact match).
- Proportion SE: $0.1795$ (Exact match).
- Wald CI: $[-0.4057, 1.1390]$ (Exact match).
- Logit CI: $[0.0204, 0.9416]$ (Exact match).
- FPC halving test ($f_h = 0.5$): $\text{Var}_{\text{FPC}} = 0.111111$ (Exact match).

---

## 6. Separation of Uncertainties & Monte Carlo Independence

### 6.1 Total Discrepancy Decomposition

When assessing whether the SYNAPSE simulator accurately reproduces reference epidemiological targets, we evaluate the calibration discrepancy $\Delta$:

$$\Delta = \bar{\theta}_{\text{sim}} - \widehat{\theta}_{\text{ref}}$$

where:
- $\widehat{\theta}_{\text{ref}}$ is the complex survey estimator from the reference dataset.
- $\bar{\theta}_{\text{sim}} = \frac{1}{M} \sum_{m=1}^M \theta_{\text{sim}}^{(m)}$ is the empirical mean across $M$ simulation replications (or simulated cohort of size $M$).

The sampling variance of the discrepancy is:
$$\text{Var}(\Delta) = \text{Var}\left(\bar{\theta}_{\text{sim}} - \widehat{\theta}_{\text{ref}}\right) = \text{Var}(\bar{\theta}_{\text{sim}}) + \text{Var}\left(\widehat{\theta}_{\text{ref}}\right) - 2\text{Cov}\left(\bar{\theta}_{\text{sim}}, \widehat{\theta}_{\text{ref}}\right)$$

### 6.2 The Independence Assumption: When Does $\text{Cov} = 0$ Hold?

The engine's additive variance formula:
$$\text{Var}(\Delta) = \text{Var}_{\text{survey}}\left(\widehat{\theta}_{\text{ref}}\right) + \frac{\text{Var}_{\text{sim}}(\theta)}{M}$$
holds **strictly if and only if**:
$$\text{Cov}\left(\bar{\theta}_{\text{sim}}, \widehat{\theta}_{\text{ref}}\right) = 0$$

#### Conditions Under Which Independence Holds ($\text{Cov} = 0$):
1. **Pre-Calibration Baseline Evaluation:** When the simulator runs with clinical defaults derived from published literature before any empirical reference calibration occurs.
2. **Holdout Validation on Partition C:** When the simulator has been calibrated solely on Partition B, and is evaluated against the independent, unobserved Partition C. Because Partition C was never used to estimate simulation parameters, $\bar{\theta}_{\text{sim}}$ and $\widehat{\theta}_{\text{ref}, C}$ are statistically independent.

#### Condition Under Which Independence is VIOLATED ($\text{Cov} > 0$):
- **In-Sample Evaluation on Calibration Data (Partition B):** If the simulator's parameters $\psi$ are optimized to minimize $\bar{\theta}_{\text{sim}}(\psi) - \widehat{\theta}_{\text{ref}, B}$, the simulated values become explicit mathematical functions of the observed sample realization $\widehat{\theta}_{\text{ref}, B}$.
- Consequently, $\text{Cov}(\bar{\theta}_{\text{sim}}, \widehat{\theta}_{\text{ref}, B}) > 0$. Adding variances directly without accounting for covariance produces invalid confidence intervals for in-sample calibration fit.

### 6.3 Welch-Satterthwaite Effective Degrees of Freedom

When combining reference survey variance with simulation Monte Carlo variance, the degrees of freedom for the discrepancy $\Delta$ are approximated using the Welch-Satterthwaite equation ([`combine_survey_and_monte_carlo_variance`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L484)):

$$df_{\text{eff}} = \frac{\left( \text{Var}_{\text{survey}} + \text{Var}_{\text{MC}} \right)^2}{\frac{\text{Var}_{\text{survey}}^2}{df_{\text{survey}}} + \frac{\text{Var}_{\text{MC}}^2}{M - 1}}$$

When the simulation sample size $M \ge 10,000$, $\text{Var}_{\text{MC}} \to 0$, and $df_{\text{eff}} \approx df_{\text{survey}}$.

---

## 7. Verification Test Suite Execution Results

The mathematical verification test suite was executed via `pytest`:

```bash
.venv/bin/pytest tests/test_survey_variance_hand_calculations.py
```

### 7.1 Test Case Coverage
1. `test_hand_calculated_weighted_mean_benchmark`: Rational arithmetic verification of weighted mean ($134.6667$), variance ($2/9$), SE ($0.4714$), $df=2$, and $t_{2}=4.3027$.
2. `test_hand_calculated_weighted_proportion_and_logit_ci`: Verification of Wald bound violation ($[-0.4057, 1.1390]$) vs. valid logit-transformed interval ($[0.0204, 0.9416]$).
3. `test_singleton_psu_strategies_and_certainty_warning`: Confirms `GRAND_MEAN_CENTERING` variance $> \text{CERTAINTY}$ variance, and verifies certainty warning emission.
4. `test_singleton_psu_at_end_of_stratum_list_collapsing`: Confirms bug fix for end-of-list singletons collapsing into the preceding stratum.
5. `test_finite_population_correction_reduces_variance`: Confirms $(1 - f_h)$ scaling factor reduces variance by exactly $50\%$ when $f_h = 0.5$.
6. `test_student_t_critical_multipliers`: Confirms Student's $t$ lookup tables and Hill's expansion against NIST standards for $df \in [1, 120]$.
7. `test_insufficient_degrees_of_freedom_handling`: Confirms graceful degradation with `NaN` intervals and explicit telemetry when $df \le 0$.
8. `test_combined_variance_and_welch_satterthwaite_df`: Confirms additive variance and Welch-Satterthwaite effective $df$.
9. `test_missing_design_fields_and_invalid_weights_filtering`: Confirms non-positive weights and missing clinical values are excluded without coercion to 1.0.

### 7.2 Full Repository Test Suite Status
All **332 tests** across the SYNAPSE Phase 2 test suite pass with zero errors:
```
============================= 332 passed in 9.48s ==============================
```

---

## 8. Governance & External Validation Gate Lockdown

| Milestone Guardrail | Required Status | Current Implementation Status | Compliance Assessment |
| :--- | :---: | :---: | :---: |
| **Validation Gate Status** | `REFERENCE_DATA_PENDING` | `REFERENCE_DATA_PENDING` | **COMPLIANT (Preserved)** |
| **Parameter Calibration** | Strictly Prohibited | None executed; clinical defaults unchanged | **COMPLIANT** |
| **Empirical Microdata Partitioning** | Strictly Prohibited | No empirical data partitioned or accessed | **COMPLIANT** |
| **Empirical Validity Claims** | Strictly Prohibited | Zero empirical claims; synthetic tests only | **COMPLIANT** |
| **Synthetic Benchmarking** | Required | Exact rational hand calculations verified | **COMPLIANT** |
| **Independence Assumptions** | Explicitly Documented | Proved $\text{Cov}=0$ boundary conditions | **COMPLIANT** |

With the completion of this verification audit, the variance estimation engine is mathematically validated and certified for implementation in Milestone 4.
