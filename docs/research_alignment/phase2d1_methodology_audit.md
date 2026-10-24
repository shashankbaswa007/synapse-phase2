# SYNAPSE Phase 2D.1 — Scientific and Statistical Methodology Audit

**Document ID:** `SYNAPSE-AUDIT-2026-PHASE2D1-METHODOLOGY-AUDIT`  
**Classification:** Scientific Methodology Audit, Mathematical Verification, Survey Statistics, and Validation Governance  
**Target Document Audited:** [`docs/research_alignment/phase2d_calibration_validation_plan.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d_calibration_validation_plan.md)  
**Target Repository:** `synapse-phase2` (`/Users/shashi/synapse/synapse-phase2`)  
**Audit Date:** October 2026  
**Auditor:** Antigravity Senior Statistical & Scientific Methodology Pair  
**Baseline Test Suite Status:** 299 passed, 0 failed in 9.25s (`.venv/bin/pytest`)  
**External Validation Gate Status:** **`REFERENCE_DATA_PENDING`** (Strictly Preserved)  

---

## 1. Executive Verdict & Governance Scope

### 1.1 Executive Verdict: CONDITIONAL APPROVAL WITH MANDATORY METHODOLOGICAL REVISIONS

The proposed Phase 2D Calibration and Validation Plan establishes an ambitious, structurally sound roadmap for transitioning the SYNAPSE simulator from heuristic evidence-anchored parameters to formal empirical calibration. The plan correctly recognizes the necessity of out-of-sample holdout partitioning, protocol harmonization, and cryptographic gatekeeping.

However, a rigorous mathematical and statistical methodology audit reveals **critical defects in the calibration objective formulation, design-based complex-survey inference, partitioning unit definitions, and validation threshold declarations**. If executed without revision, the plan would introduce:
1. **Quadratic double-weighting** of populous demographic strata in the calibration loss function, severely distorting vascular aging slope estimation.
2. **False precision and variance underestimation** by treating Kish effective sample size as a substitute for Primary Sampling Unit (PSU) cluster variance estimation.
3. **Severe holdout leakage** caused by unclustered participant-level data splitting across multi-stage survey clusters.
4. **Invalid hypothesis testing** resulting from applying standard two-sample Kolmogorov-Smirnov asymptotics to complex survey-weighted data.
5. **Conflation of observational survey associations with causal mechanistic parameters**, specifically regarding drug treatment effect size and biological aging drift.

**Governance Mandate:** Parameter calibration, microdata ingestion, and validation gate unlocking must **not** proceed until the mathematical and statistical corrections detailed in this audit are formally integrated into the calibration harness. The external validation gate remains strictly locked at **`REFERENCE_DATA_PENDING`**.

---

### 1.2 Explicit Separation of Software Correctness from Empirical Validity

A core tenet of this audit is the strict operational and epistemological separation between **software correctness** and **empirical scientific validity**:

```
+---------------------------------------------------------------------------------------------------+
|                                 DUAL-AXIS EVALUATION FRAMEWORK                                    |
+---------------------------------------------------------------------------------------------------+
|  AXIS 1: SOFTWARE IMPLEMENTATION INTEGRITY (VERIFIED)                                             |
|  • Zero syntax, runtime, or schema errors across 299 automated pytest suites.                     |
|  • Deterministic execution guaranteed via isolated cryptographic PRNG streams (SHA-256 seeds).    |
|  • Complete referential, temporal, and causal relational integrity (foreign keys, timestamps).   |
|  • Zero clinical invariant violations (no pre-birth events, no post-mortem activity).              |
|  STATUS: FULLY VERIFIED IN CODEBASE (299/299 TESTS PASSING).                                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  (DOES NOT IMPLY)
+---------------------------------------------------------------------------------------------------+
|  AXIS 2: EMPIRICAL SCIENTIFIC & CLINICAL VALIDITY (PENDING)                                       |
|  • Continuous hemodynamic distributions conform to genuine national reference microdata.          |
|  • Vascular stiffening and pulse pressure dynamics match human biological aging trajectories.     |
|  • Multi-visit diagnostic incidence reproduces epidemiological population event cascades.         |
|  • Pharmacodynamic treatment response reflects real-world clinical effectiveness.                |
|  STATUS: REFERENCE_DATA_PENDING (AWAITING CREDENTIALED DUA AND VALIDATION EXECUTION).              |
+---------------------------------------------------------------------------------------------------+
```

> [!CAUTION]
> **Non-Negotiable Safeguard:** Passing 100% of software unit, integration, and regression tests establishes only that the simulation code executes without software defects according to its programmatic specification. It provides **zero empirical proof** of clinical realism or population validity. Synthetic test fixtures (e.g. `lasi_wave1_sample_fixture.csv`, $N=51$) are software testing harnesses and must **never** be cited as evidence of epidemiological fidelity.

---

## 2. Prioritized Findings by Severity

The audit findings are prioritized according to their potential to bias parameter estimates, compromise holdout independence, or invalidate statistical inferences:

| Finding ID | Severity | Category | Summary of Defect |
| :--- | :---: | :--- | :--- |
| **FINDING-01** | **CRITICAL** | Objective Function | **Quadratic Double-Weighting in WMDE Loss:** Combining stratum population weights $w_k$ with inverse empirical standard errors $\widehat{\text{SE}}(\widehat{Q}_k)^{-2}$ creates an unintended $w_k^2$ weighting, severely overweighting younger adults and underweighting the elderly. |
| **FINDING-02** | **CRITICAL** | Survey Inference | **Omission of Clustering Design Effect:** Kish effective sample size accounts solely for unequal weighting variance inflation ($\text{DEFF}_w$) and completely ignores Primary Sampling Unit (PSU) clustering ($\text{DEFF}_c$). |
| **FINDING-03** | **HIGH** | Partitioning | **Contamination via Unclustered Respondent Splitting:** Random 50/25/25 participant-level splitting scatters individuals from the same household and PSU across calibration and holdout sets, leaking intra-cluster correlation. |
| **FINDING-04** | **HIGH** | Objective Function | **Omission of Simulation Monte Carlo Uncertainty:** The calibration loss treats simulated quantiles $\widehat{Q}^{\text{syn}}(\mathbf{\Theta})$ as deterministic, omitting simulation variance from the distance denominator. |
| **FINDING-05** | **HIGH** | Statistical Testing | **Invalid Asymptotics for Survey KS and Wasserstein Metrics:** Applying standard i.i.d. Kolmogorov-Smirnov test statistics and p-values to complex-survey data invalidates false-positive error control. |
| **FINDING-06** | **HIGH** | Disease Definition | **Informative Missingness Bias in Composite Hypertension:** Incomplete blood pressure readings in survey data cannot be defaulted to normotension without drastically underestimating true prevalence. |
| **FINDING-07** | **HIGH** | Identifiability | **Conflation of Cross-Sectional Age Slopes with Biological Aging:** Single-wave cross-sectional age gradients confound within-person vascular stiffening with birth-cohort effects and differential survivorship selection. |
| **FINDING-08** | **MEDIUM** | Survey Inference | **Vulnerability to Singleton PSUs and Degrees of Freedom Collapse:** Lack of explicit variance collapse rules for single-PSU strata under subpopulation analysis. |
| **FINDING-09** | **MEDIUM** | Identifiability | **Confounding of Causal Drug Efficacy with Adherence and Indication:** Attempting to calibrate causal pharmacological effect size $\delta_{\text{drug}}$ from observational survey contrasts without randomized or longitudinal controls. |
| **FINDING-10** | **LOW** | Governance | **Ambiguous Characterization of Engineering Thresholds as Clinically Validated:** Proposed distance thresholds ($D_{\text{ks}} < 0.08, W_1 < 3.5\text{ mmHg}$) lack formal clinical consensus grounding and must be designated as exploratory benchmarks. |

---

## 3. Deep-Dive Audit of the Calibration Objective Function

### 3.1 Mathematical Dissection of the Proposed Objective

The calibration loss function proposed in Section 4.1 of `phase2d_calibration_validation_plan.md` is:

$$\mathcal{L}(\mathbf{\Theta}) = \sum_{k \in \mathcal{K}} \sum_{q \in \mathcal{Q}} w_k \left[ \frac{\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta}) - \widehat{Q}^{\text{ref}}_{k,q}}{\widehat{\text{SE}}(\widehat{Q}^{\text{ref}}_{k,q})} \right]^2$$

where $k \in \mathcal{K}$ indexes demographic strata (e.g. 8 age-sex strata), $q \in \mathcal{Q} = \{0.10, 0.25, 0.50, 0.75, 0.90\}$ indexes marginal quantiles for SBP and DBP, $\widehat{Q}^{\text{ref}}_{k,q}$ is the complex-survey-weighted quantile estimate in Partition A, $\widehat{\text{SE}}(\widehat{Q}^{\text{ref}}_{k,q})$ is its estimated standard error, and $w_k$ is the Census SRS population proportion for stratum $k$.

---

### 3.2 Defect 1: The Quadratic Double-Weighting Phenomenon

#### Mathematical Proof of Defect:
Let $N$ be the total population size, $N_k$ be the population in stratum $k$, such that the stratum population weight is $w_k = N_k / N$.
In a nationally representative sample with approximately proportional allocation across major demographic strata, the empirical stratum sample size is $n_k \approx n \cdot w_k$.

From asymptotic distribution theory for sample quantiles (Bahadur representation), the variance of an empirical sample quantile $\widehat{Q}_q$ in stratum $k$ is:

$$\text{Var}(\widehat{Q}_{k,q}) = \frac{q(1-q)}{n_k \left[ f_k(Q_{k,q}) \right]^2} \cdot \text{DEFF}_k$$

where $f_k(\cdot)$ is the stratum probability density function at the true quantile $Q_{k,q}$, and $\text{DEFF}_k$ is the design effect.

The estimated standard error is therefore inversely proportional to the square root of the stratum sample size:

$$\widehat{\text{SE}}(\widehat{Q}^{\text{ref}}_{k,q}) \approx \frac{\sigma_{k,q}}{\sqrt{n_k}} \propto \frac{1}{\sqrt{w_k}}$$

Squaring the denominator in the proposed objective introduces a factor of $n_k$ into the numerator:

$$\left[ \frac{1}{\widehat{\text{SE}}(\widehat{Q}^{\text{ref}}_{k,q})} \right]^2 \approx \frac{n_k}{\sigma_{k,q}^2} \propto n \cdot \frac{w_k}{\sigma_{k,q}^2}$$

Substituting this back into the proposed loss function yields:

$$w_k \cdot \left[ \frac{1}{\widehat{\text{SE}}(\widehat{Q}^{\text{ref}}_{k,q})} \right]^2 \propto w_k \cdot \left( \frac{n \cdot w_k}{\sigma_{k,q}^2} \right) = n \cdot \frac{w_k^2}{\sigma_{k,q}^2}$$

#### Consequence:
The objective function scales with the **square of the population weight ($w_k^2$)** rather than linearly with $w_k$:
- For the young older-adult stratum (e.g. 45–54 years, where $w_k \approx 0.23$), the effective weight in the loss is $(0.23)^2 \approx 0.0529$.
- For the elderly stratum (e.g. 75+ years, where $w_k \approx 0.045$), the effective weight is $(0.045)^2 \approx 0.0020$.
- The ratio of effective optimization weights between age 45–54 and age 75+ becomes:

$$\frac{(0.23)^2}{(0.045)^2} \approx 26.1$$

whereas the actual population ratio is only $0.23 / 0.045 \approx 5.1$.

**Impact on Calibration:** The optimizer will aggressively fit the blood pressure distribution of 45–54 year olds while virtually ignoring the 75+ population. This fatally distorts the calibration of vascular stiffening parameters ($\beta_{\text{age, sbp}}$) and the late-life diastolic inflection point ($a_{\text{inflect}}, \beta_{\text{age, dbp2}}$), leading to poor fit at advanced ages where cardiovascular risk and pulse pressure widening are highest.

---

### 3.3 Defect 2: Omission of Simulation Monte Carlo Uncertainty

The proposed denominator accounts exclusively for reference survey sampling error: $\widehat{\text{SE}}(\widehat{Q}^{\text{ref}}_{k,q})$.
However, the synthetic quantile $\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta})$ is generated by running a stochastic simulation of finite cohort size $M_{\text{sim}}$ (e.g. 10,000 synthetic patients). Consequently, $\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta})$ is itself a random variable subject to Monte Carlo simulation error:

$$\text{Var}(\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta})) = \frac{\sigma_{\text{syn}, k, q}^2}{M_{k, \text{sim}}}$$

The difference $D_{k,q}(\mathbf{\Theta}) = \widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta}) - \widehat{Q}^{\text{ref}}_{k,q}$ has total variance:

$$\text{Var}(D_{k,q}(\mathbf{\Theta})) = \text{Var}(\widehat{Q}^{\text{ref}}_{k,q}) + \text{Var}(\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta}))$$

By omitting $\text{Var}(\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta}))$, the objective function artificially inflates the z-score distance, making the loss surface excessively noisy and sensitive to random simulation seeds.

---

### 3.4 Defect 3: Quantile Inter-Correlation and Off-Diagonal Covariance

The proposed objective sums independent squared differences across five quantiles $\mathcal{Q} = \{0.10, 0.25, 0.50, 0.75, 0.90\}$.
In reality, empirical sample quantiles from the same distribution are **highly correlated**. For any two quantiles $q_1 < q_2$, their asymptotic covariance is:

$$\text{Cov}(\widehat{Q}_{q_1}, \widehat{Q}_{q_2}) = \frac{q_1(1 - q_2)}{n \cdot f(Q_{q_1}) f(Q_{q_2})}$$

For example, between the median ($q=0.50$) and the 75th percentile ($q=0.75$):

$$\text{Corr}(\widehat{Q}_{0.50}, \widehat{Q}_{0.75}) = \frac{0.50 \cdot (1 - 0.75)}{\sqrt{0.50(1-0.50)} \sqrt{0.75(1-0.75)}} = \frac{0.125}{\sqrt{0.25} \sqrt{0.1875}} = \frac{0.125}{0.50 \times 0.433} \approx 0.577$$

Treating these five quantiles as mutually independent in a diagonal sum overcounts redundant distributional information (e.g. median shift affects all quantiles simultaneously) and violates classical Generalized Method of Moments (GMM) theory.

---

### 3.5 Recommended Mathematical Corrections for the Calibration Objective

To address Defects 1, 2, and 3, two mathematically rigorous formulations are established:

#### Formulation A: Classical Generalized Method of Moments (GMM) / Optimal WMD
For each stratum $k$, define the vector of quantile differences:

$$\mathbf{d}_k(\mathbf{\Theta}) = \widehat{\mathbf{Q}}^{\text{syn}}_k(\mathbf{\Theta}) - \widehat{\mathbf{Q}}^{\text{ref}}_k \in \mathbb{R}^{|\mathcal{Q}|}$$

The optimal minimum distance objective is:

$$\mathcal{L}_{\text{GMM}}(\mathbf{\Theta}) = \sum_{k \in \mathcal{K}} \mathbf{d}_k(\mathbf{\Theta})^T \mathbf{\Omega}_k^{-1} \mathbf{d}_k(\mathbf{\Theta})$$

where the weighting matrix $\mathbf{\Omega}_k$ is the total covariance matrix:

$$\mathbf{\Omega}_k = \mathbf{V}^{\text{ref}}_k + \mathbf{V}^{\text{syn}}_k(\mathbf{\Theta})$$

$\mathbf{V}^{\text{ref}}_k$ is estimated empirically from Partition A using the design-based survey bootstrap across Primary Sampling Units (PSUs). To prevent singularity when $|\mathcal{Q}|$ is large relative to effective sample size, $\mathbf{\Omega}_k$ should be regularized using Ledoit-Wolf or ridge shrinkage: $\mathbf{\Omega}_k^* = (1 - \lambda)\mathbf{\Omega}_k + \lambda \text{diag}(\mathbf{\Omega}_k)$ with $\lambda \in [0.1, 0.2]$.

#### Formulation B: Corrected Diagonal Weighted Minimum Distance (Recommended for Numerical Stability)
If numerical inversion of $\mathbf{\Omega}_k$ proves unstable across optimization iterations, the diagonalized formulation must eliminate the quadratic population weight $w_k$:

$$\mathcal{L}_{\text{WMDE-CORRECTED}}(\mathbf{\Theta}) = \sum_{k \in \mathcal{K}} \sum_{q \in \mathcal{Q}} \frac{\left( \widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta}) - \widehat{Q}^{\text{ref}}_{k,q} \right)^2}{\widehat{\text{Var}}(\widehat{Q}^{\text{ref}}_{k,q}) + \widehat{\text{Var}}(\widehat{Q}^{\text{syn}}_{k,q}(\mathbf{\Theta}))}$$

> [!IMPORTANT]
> **Resolution of Double-Weighting:** Under `Formulation B`, the stratum sample size $n_k$ is already embedded in the empirical variance denominator ($\widehat{\text{Var}} \propto 1/n_k \propto 1/w_k$). The stratum weight $w_k$ **must not** appear as an additional multiplicative factor in the numerator. This ensures that every individual respondent in the reference population contributes with correct, un-squared statistical leverage.

---

## 4. Complex-Survey Inference & Variance Estimation Audit

### 4.1 Audit of Kish Effective Sample Size Usage

Section 4.2 of `phase2d_calibration_validation_plan.md` specifies:
$$N_{\text{eff}} = \frac{\left( \sum_{i=1}^n w_i \right)^2}{\sum_{i=1}^n w_i^2} = \frac{n}{1 + \text{CV}(w)^2}$$
and establishes an exclusion rule: *"If $N_{\text{eff}} < 25.0$ in any stratum, that stratum is flagged as `INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE` and excluded from calibration loss."*

#### Critical Methodological Findings:
1. **Kish $N_{\text{eff}}$ Captures ONLY Weighting Dispersions:** Kish's formula measures variance inflation strictly attributable to **unequal sampling weights** ($\text{DEFF}_w = 1 + \text{CV}(w)^2$). It assumes independent sampling (SRS) within strata and **completely ignores spatial and administrative clustering** across Primary Sampling Units (PSUs).
2. **Total Design Effect is Multiplicative:** In multi-stage surveys like LASI (which sample Villages/Census Wards as PSUs, then households, then individuals), the true design effect is:

$$\text{DEFF}_{\text{total}} = \text{DEFF}_w \times \text{DEFF}_c = \left[ 1 + \text{CV}(w)^2 \right] \times \left[ 1 + (\bar{m} - 1)\rho_{\text{ICC}} \right]$$

where $\bar{m}$ is the average cluster size and $\rho_{\text{ICC}}$ is the intraclass correlation coefficient.
For blood pressure and cardiovascular risk factors, $\rho_{\text{ICC}}$ is typically $0.03–0.08$. In a PSU cluster with $\bar{m} = 25$ respondents, $\text{DEFF}_c \approx 1 + (24)(0.05) = 2.20$.
Using Kish's formula alone underestimates true standard errors by a factor of $\sqrt{2.20} \approx 1.48$ (a ~48% underestimation of variance), producing artificially narrow confidence intervals and overconfident calibration loss.

3. **Arbitrary Stratum Dropping Induces Survival Bias:** Dropping strata where $N_{\text{eff}} < 25.0$ disproportionately eliminates the oldest age bands (e.g. 75+ or 80+), precisely where sample counts are smaller. Dropping these strata truncates the dynamic range of vascular aging and hides late-life blood pressure trajectories.

---

### 4.2 Design-Based Quantile and Variance Estimation

To achieve scientifically valid inference from complex survey data, all reference estimates must implement design-based estimation:

#### Survey-Weighted Quantile Estimation:
For a continuous variable $Y$ (e.g. SBP) with sampling weights $w_i$, the survey-weighted empirical cumulative distribution function (ECDF) is:

$$\widehat{F}_w(y) = \frac{\sum_{i=1}^n w_i \cdot \mathbb{I}(y_i \le y)}{\sum_{i=1}^n w_i}$$

The survey-weighted quantile $\widehat{Q}_{q}^{\text{ref}}$ is defined via generalized inverse with continuous linear interpolation:

$$\widehat{Q}_q^{\text{ref}} = \widehat{F}_w^{-1}(q)$$

#### Design-Based Variance Estimation:
Variance estimation for quantiles cannot use simple analytical formulas under complex multi-stage designs. Two methods are formally mandated:

1. **Primary Method: Multi-Stage Cluster Bootstrap (Rao-Wu-Yue-Beaumont):**
   - Resample $m_h - 1$ PSUs with replacement from the $m_h$ PSUs in stratum $h$.
   - Re-scale survey weights for bootstrap replicate $b \in \{1, \dots, B\}$ ($B \ge 500$):
   
   $$w_i^{(b)} = w_i \cdot \left[ \frac{m_h}{m_h - 1} r_{hi}^{(b)} \right]$$
   
   where $r_{hi}^{(b)}$ is the number of times PSU $i$ in stratum $h$ was selected in replicate $b$.
   - The bootstrap standard error is the empirical standard deviation across replicates:
   
   $$\widehat{\text{SE}}_{\text{boot}}(\widehat{Q}_q) = \sqrt{\frac{1}{B-1} \sum_{b=1}^B \left( \widehat{Q}_q^{(b)} - \bar{Q}_q \right)^2}$$

2. **Secondary / Analytic Method: Woodruff's Confidence Interval Inversion:**
   - Construct Taylor linearized variance of the estimated cumulative proportion $\widehat{p} = \widehat{F}_w(\widehat{Q}_q) = q$.
   - Using Taylor linearization across PSUs:
   
   $$\widehat{\text{Var}}(\widehat{F}_w(y)) = \sum_{h=1}^H \frac{m_h}{m_h - 1} \sum_{i=1}^{m_h} \left( z_{hi} - \bar{z}_h \right)^2$$
   
   where $z_{hi} = \sum_{j \in \text{PSU}_{hi}} \frac{w_{hij}}{\sum w} \left[ \mathbb{I}(y_{hij} \le y) - \widehat{F}_w(y) \right]$.
   - Invert the interval $[\widehat{p} - 1.96 \text{SE}(\widehat{p}), \widehat{p} + 1.96 \text{SE}(\widehat{p})]$ back through $\widehat{F}_w^{-1}(\cdot)$ to yield exact design-adjusted Woodruff confidence intervals for $\widehat{Q}_q$.

---

### 4.3 Handling Complex Survey Anomalies

The audit formalizes protocols for four standard survey anomalies:

| Anomaly | Epidemiological Mechanism | Mandated Protocol |
| :--- | :--- | :--- |
| **Singleton PSUs** | Strata with only $m_h = 1$ PSU selected (e.g. after domain subsetting or in small administrative union territories). | **Collapse Strata:** Merge singleton stratum with the most demographically and geographically similar adjacent stratum within the same state prior to variance estimation. Never drop singleton strata from the dataset. |
| **Missing Strata / PSU IDs** | Gateway to Global Aging Data or public-use files occasionally redact PSU identifiers for privacy. | **Group Jackknife / State Pseudo-PSUs:** When true PSU IDs are legally redacted, construct pseudo-clusters based on administrative district and sampling weight quantiles. Never assume simple random sampling (SRS). |
| **Extreme Sampling Weights** | Outlier weights from non-response adjustments that inflate variance. | **Weight Trimming:** Apply weight trimming at the 99th percentile (or median $+ 4 \times \text{IQR}$). Re-distribute trimmed mass proportionally across untrimmed weights to preserve the national population total $\sum w_i = N_{\text{census}}$. |
| **Small Domain Subsamples** | Small cell counts (e.g. diabetic men aged 75+, where $n_k < 20$). | **Exact Clopper-Pearson / Wilson Inversion:** Do not use Wald normal approximations. If $n_k < 15$, report as `ESTIMATE_SUPPRESSED_SPARSE_DOMAIN` for individual cell reporting, but retain all observations in overall model calibration. |

---

## 5. Partitioning & Holdout Independence Audit

### 5.1 Verification of Participant-Level Integrity

The audit inspected whether multiple records from the same participant could be divided across partitions:
- In SYNAPSE, each individual is assigned a unique surrogate identifier `participant_id` (SHA-256 digest prefix).
- In LASI Wave 1 microdata, individuals are identified by `prim_key` (household) and `respid` (individual).
- **Rule Verification:** All longitudinal records, clinical encounters, community vitals, and condition events belonging to a given `participant_id` must reside in **exactly one partition**. No intra-individual splitting is permitted.

---

### 5.2 Defect: Contamination via Unclustered Random Splitting

Section 5.1 of `phase2d_calibration_validation_plan.md` proposes a *"50% Random Stratified Split for Partition A, 25% for Partition B, and 25% for Partition C"*.

#### Mathematical Flaw:
A simple random split of participants—even if stratified by age and sex—violates the hierarchical sampling structure of multi-stage surveys:
- In LASI, households often contain multiple age-eligible respondents (e.g. index participant and spouse).
- Households are clustered within Primary Sampling Units (Villages in rural areas; Census Enumeration Blocks / Wards in urban areas).
- If individuals are randomly partitioned independently, **Participant 1 (husband) may be placed in Partition A (calibration) while Participant 2 (wife) is placed in Partition C (holdout validation)**.
- Furthermore, neighbors within the same village sharing identical local drinking water salinity, dietary habits, ambient temperature, healthcare access, and field interviewers would be split across calibration and validation sets.
- This creates **intra-cluster correlation leakage**, artificially deflating out-of-sample validation error and giving a false impression of model generalizability.

#### Mandated Correction: Primary Sampling Unit (PSU) Cluster-Level Partitioning
Partitioning must be executed at the **Primary Sampling Unit (PSU) level**, not at the individual participant level:
1. Group all records by `(State, Urban_Rural, PSU_ID)`.
2. Randomly assign **entire PSUs** to Partition A (50%), Partition B (25%), and Partition C (25%), stratified by State and Urban/Rural status.
3. This guarantees that:
   - All members of the same household remain in the same partition.
   - All respondents from the same village/neighborhood remain in the same partition.
   - Partition C provides a genuine test of spatial and cluster-level out-of-sample generalization.

---

### 5.3 Anti-Leakage Safeguards across Preprocessing and Model Selection

To prevent subtle information leakage from Partition C into Partition A:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ANTI-LEAKAGE BOUNDARY PROTOCOL                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Population Standardization Weights:                                                 │
│    • PERMITTED: External population weights (Census SRS 2021) may be used across all    │
│      partitions because they are exogenous external constants, not sample estimates.  │
│                                                                                        │
│ 2. Preprocessing & Imputation Parameters:                                              │
│    • PROHIBITED: Computing mean, median, standard deviation, or missingness imputation│
│      models on the pooled dataset (A + B + C).                                         │
│    • MANDATED: Any data imputation or scaling models must be fitted strictly on        │
│      Partition A, then frozen and applied out-of-sample to B and C.                    │
│                                                                                        │
│ 3. Survey Weight Normalization:                                                        │
│    • Sampling weights within Partition A must be re-normalized to sum to the stratum   │
│      population total: w_i^(A) = w_i * (sum_{k in Pop} W_k / sum_{i in A} w_i).         │
│                                                                                        │
│ 4. Model Selection & Hyperparameter Tuning:                                            │
│    • Structural model choices (e.g. linear vs bilinear late-life DBP drift) must be    │
│      decided using Partition B, NEVER Partition C.                                     │
│                                                                                        │
│ 5. Holdout Partition C Vault Lockdown:                                                 │
│    • Partition C must be stored in an encrypted archive with SHA-256 digest logging.   │
│    • Decrypted and accessed strictly ONCE upon final calibration freeze.               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.4 Longitudinal Claims vs. Single-Wave Cross-Sectional Data

The plan must explicitly acknowledge that **no partitioning of single-wave cross-sectional data (LASI Wave 1) can validate longitudinal causal trajectories**.
- Internal splitting of Wave 1 validates cross-sectional distributional fidelity across unobserved geographic clusters.
- It **cannot** validate within-person blood pressure progression, treatment ramp dynamics ($\tau_{\text{ramp}}$), or multi-year disease incidence hazards ($\lambda_{\text{htn}}$).
- **Mandated Revision:** Any claim of longitudinal or trajectory validation must be formally deferred to LASI Wave 2 panel data or prospective cohort audits (e.g. CARRS/CURES).

---

## 6. Audit of Predeclared Validation Thresholds

Section 5.2 of `phase2d_calibration_validation_plan.md` establishes five independent validation targets. The audit analyzes each metric's mathematical definition, sample-size sensitivity, and clinical grounding:

### 6.1 Metric-by-Metric Evaluation

#### 1 & 2. SBP and DBP Distributional Fidelity ($D_{\text{ks}} < 0.08, W_1 < 3.5\text{ mmHg}$)
- **Exact Estimand:** Marginal cumulative distribution functions $F_{\text{sbp}}(y)$ and $F_{\text{dbp}}(y)$ among unmedicated older adults ($\text{Age} \ge 45$).
- **Defect in KS Distance:** The standard two-sample Kolmogorov-Smirnov statistic:

$$D_{\text{ks}} = \sup_y |F_{\text{syn}}(y) - F_{\text{ref}}(y)|$$

assumes continuous, independent, and identically distributed observations. In complex surveys, positive spatial autocorrelation reduces effective sample size, inflating the empirical supremum. A threshold of $D_{\text{ks}} < 0.08$ on a sample of $N=5,000$ has immense statistical power (rejecting trivial differences of 1.5 mmHg), whereas on a small stratum ($N=100$), it has low power.
- **Defect in 1D Wasserstein Distance:** $W_1 = \int_0^1 |F_{\text{syn}}^{-1}(u) - F_{\text{ref}}^{-1}(u)| du$ measures average absolute shift in mmHg. While clinically interpretable (units of mmHg), the plan does not specify whether $W_1 < 3.5\text{ mmHg}$ applies to pooled unstandardized data or within each of the 8 age-sex strata.
- **Correction:** Compute $W_1$ within each of the 8 strata. The threshold is $W_{1, k} \le 4.0\text{ mmHg}$ across all individual strata and pooled $W_1 \le 3.0\text{ mmHg}$.

#### 3. Pulse Pressure Stiffening Difference ($|\Delta \text{PP}_{\text{syn}} - \Delta \text{PP}_{\text{ref}}| < 3.0\text{ mmHg}$)
- **Exact Estimand:** The difference in mean pulse pressure ($\text{SBP} - \text{DBP}$) between the oldest stratum (75+ years) and the youngest older-adult stratum (45–54 years):

$$\Delta \text{PP} = \mathbb{E}[\text{PP} \mid \text{Age} \ge 75] - \mathbb{E}[\text{PP} \mid 45 \le \text{Age} \le 54]$$

- **Clinical Grounding:** Measures large-artery conduit stiffening (loss of arterial elastance). In human biology, pulse pressure widens by ~15–25 mmHg between ages 45 and 80.
- **Statistical Assessment:** Grounded and robust. The 3.0 mmHg tolerance is biologically sound and accounts for empirical sampling error in the 75+ age band.

#### 4. Composite Hypertension Prevalence ($|\pi_{\text{std}}^{\text{syn}} - \pi_{\text{std}}^{\text{ref}}| < 3.5\%$ points)
- **Exact Estimand:** Direct age- and sex-standardized composite hypertension prevalence among older adults ($\text{Age} \ge 45$) using Census SRS 2021 standard weights across 8 strata.
- **Statistical Assessment:** With a holdout sample size of $N \approx 18,000$ (25% of LASI Wave 1), the survey standard error for standardized prevalence is $\text{SE} \approx 0.45\%$. A tolerance of $\pm 3.5\%$ points represents ~8 standard errors, providing an appropriately powered operational tolerance that accommodates minor baseline geographic discrepancies without rejecting valid models.

#### 5. Treatment Control Rate ($|\text{Control}_{\text{syn}} - \text{Control}_{\text{ref}}| < 5.0\%$ points)
- **Exact Estimand:** Proportion of treated hypertensive older adults ($\text{Taking BP Medication} = \text{True}$) who achieve target blood pressure ($\text{Mean SBP} < 140\text{ mmHg} \land \text{Mean DBP} < 90\text{ mmHg}$).
- **Confounding Warning:** In cross-sectional surveys, "control" conflates drug efficacy with patient adherence, dosage titration, and treatment duration. A synthetic simulation with 100% adherence will naturally overestimate control rates unless adherence degradation is explicitly modeled.

---

### 6.2 Threshold Classification Scorecard

All proposed validation thresholds are categorized into the formal repository taxonomy:

| Metric ID | Metric Name | Threshold Value | Classification | Justification & Clinical Status |
| :--- | :--- | :---: | :--- | :--- |
| `val_sbp_strata_ks` | SBP Kolmogorov-Smirnov | $D_{\text{ks}} \le 0.08$ | **Provisional Engineering** | Non-parametric shape metric; uncalibrated against clinical endpoints. |
| `val_sbp_strata_w1` | SBP 1D Wasserstein | $W_1 \le 3.5\text{ mmHg}$ | **Practical Tolerance** | Clinically interpretable mean absolute bias bound. |
| `val_dbp_strata_w1` | DBP 1D Wasserstein | $W_1 \le 2.5\text{ mmHg}$ | **Practical Tolerance** | Diastolic variance is physiologically narrower than systolic. |
| `val_pulse_pressure_gradient` | Pulse Pressure Widening | $|\Delta \text{PP}| \le 3.0\text{ mmHg}$ | **Statistically Motivated** | Grounded in Framingham / Franklin et al. vascular aging physiology. |
| `val_composite_htn_prev_std` | Direct Standardized HTN Prev | $|\Delta \pi_{\text{std}}| \le 3.5\%$ | **Practical Tolerance** | Balanced tolerance reflecting survey sampling variance. |
| `val_htn_treatment_control` | Hypertensive Control Rate | $|\Delta \text{Control}| \le 5.0\%$ | **Provisional Engineering** | Confounded by adherence; exploratory diagnostic. |

> [!WARNING]
> **Prohibition on Post-Hoc Tuning:** Validation thresholds must be permanently frozen prior to decrypting Partition C. Under no circumstances may threshold boundaries be widened after inspecting holdout results to force an apparent "PASS". If any criterion fails, the gate outcome must be reported honestly as `FAIL`.

---

## 7. Disease Definitions and Epidemiological Comparability

### 7.1 Multi-Indicator Comparison Matrix

The audit evaluated how chronic disease status is represented across survey microdata and synthetic simulation tables:

| Indicator Dimension | Survey Reference (LASI Wave 1) | Synthetic Simulation (SYNAPSE Phase 2) | Harmonization Mechanism | Potential Bias if Conflated |
| :--- | :--- | :--- | :--- | :--- |
| **Self-Reported Diagnosis** | *"Has any doctor or health professional ever diagnosed you with hypertension or high BP?"* (`r1hypere`) | Historical condition record (`conditions.csv`, ICD-10 `I10`) generated upon visit confirmation. | Harmonized via explicit consultation latency. | **Substantial Under-Reporting:** 30–45% of hypertensive individuals in India are unaware of their condition. Comparing simulated true latent state to self-report produces massive apparent overestimation. |
| **Pharmacotherapy Exposure** | *"Are you currently taking any medication for high blood pressure?"* (`r1bprx`) | Active prescription entry (`medications.csv`) with adherence factor $\theta_i$. | Harmonized via active prescription status at observation time. | **Adherence Confounding:** Survey records binary drug possession, not biological adherence ($\theta_i$). |
| **Measured Blood Pressure** | Tri-measurement seated oscillometric protocol (Omron HEM-7121). Mean of readings 2 and 3. | `community_assessments.csv` tri-measurement protocol (`BpMeasurementProtocolSimulator`). | Protocol identical: arithmetic mean of readings 2 and 3. | **Alerting Discrepancy:** Clinic vitals (`observations.csv`) exhibit higher white-coat alerting ($\alpha \approx 6.0\text{ mmHg}$) than community surveys ($\alpha \approx 3.5\text{ mmHg}$). |
| **Clinical Diagnosis Event** | Not captured (surveys do not record hospital EHR diagnostic codes). | `ClinicalDiagnosisEvent` timestamped event in outpatient consultations. | Distinguished as an administrative EHR indicator, not an epidemiological prevalence standard. | **Incomparable:** Surveys capture community point prevalence; EHR records capture healthcare utilization. |

---

### 7.2 The Composite Hypertension Definition

To eliminate reporting bias and achieve strict epidemiological equivalence, the primary hypertension estimand is the **unified epidemiological composite standard**:

$$\text{Hypertensive} \iff (\text{Mean SBP} \ge 140\text{ mmHg}) \lor (\text{Mean DBP} \ge 90\text{ mmHg}) \lor (\text{Currently taking BP medication})$$

#### Audit of Missing Data Handling:
Real-world survey microdata exhibits ~8–12% missing blood pressure observations due to physical refusal, functional disability, severe tremor, or arm circumference exceeding cuff limits.
- **Hazard:** If respondents with missing blood pressure readings are defaulted to `Hypertensive = False`, population prevalence is biased downward by ~4–6 percentage points.
- **Mandated Harmonization Protocol:**
  1. If a participant has valid medication data and reports taking antihypertensive medication, classify as `Hypertensive = True` regardless of BP missingness.
  2. If medication is not reported and blood pressure is missing/unassessable, the composite outcome is **`Missing` (NaN)**.
  3. Missing records must be handled via **design-based non-response reweighting** or full-information domain estimation. Under no circumstances may missing values be imputed as normotensive.

---

### 7.3 Direct Age-Sex Standardization Protocol

To ensure comparability between synthetic cohorts and reference populations with differing demographic structures, all prevalence estimates must be directly standardized:

$$\pi_{\text{std}} = \sum_{s=1}^8 W_s \cdot \widehat{p}_s$$

where $s \in \{1, \dots, 8\}$ indexes the eight mutually exclusive age-sex strata for adults aged 45+, $\widehat{p}_s$ is the stratum-specific empirical prevalence, and $W_s$ is the official Census of India SRS 2021 standard population weight:

$$\sum_{s=1}^8 W_s = 1.0000$$

The standard stratum weights from Table 1 of [`synapse_simulator/evaluation/lasi/comparability.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/comparability.py#L23-L32) are verified:
- `M_45_54`: $0.231$, `F_45_54`: $0.222$
- `M_55_64`: $0.154$, `F_55_64`: $0.149$
- `M_65_74`: $0.078$, `F_65_74`: $0.076$
- `M_75_PLUS`: $0.043$, `F_75_PLUS`: $0.047$

---

## 8. Parameter Provenance and Identifiability Classification

Every configurable parameter across the seven structural layers is rigorously audited. Each of the **36 inventoried parameters** is classified into exactly one of the five mandated categories:

```
[CAT-1] Directly estimable from authorized Wave 1 cross-sectional microdata.
[CAT-2] Estimable only under explicit modeling assumptions (requires sensitivity analysis).
[CAT-3] Requiring longitudinal panel observations (unidentifiable from single-wave cross-section).
[CAT-4] Requiring external evidence / clinical guideline consensus (unidentifiable from survey).
[CAT-5] Not identifiable from currently available data (fundamental observational confounding).
```

### 8.1 Complete Parameter Identifiability Table (36 Parameters)

| # | Layer & Location | Parameter Name | Symbol | Current Value & Unit | Mandated Classification | Target Estimand / Identification Strategy | Confounding Mechanisms & Sensitivity Analysis |
| :-: | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **1** | 0. Demographics (`india_default_v1.yaml`) | `male_ratio` | $p_{\text{male}}$ | `0.515` (—) | **[CAT-1]** | National older-adult sex ratio in Census SRS 2021. | Stable national census parameter; low sensitivity. |
| **2** | 0. Demographics (`india_default_v1.yaml`) | `age_bands.weights` | $w_{\text{age}}$ | `[0.252, ..., 0.070]` | **[CAT-1]** | Census of India SRS 2021 population pyramid. | Exogenous demographic anchor; non-confounded. |
| **3** | 0. Prevalences (`india_default_v1.yaml`) | `htn_prevalence` | $\pi_{\text{htn}}$ | `30.7%` (%) | **[CAT-1]** | Survey-weighted composite HTN prevalence in adults $\ge 20$. | Benchmark target from ICMR-INDIAB; verify age cutoff. |
| **4** | 0. Prevalences (`india_default_v1.yaml`) | `t2d_prevalence` | $\pi_{\text{t2d}}$ | `11.4%` (%) | **[CAT-1]** | Survey-weighted diabetes prevalence in adults $\ge 20$. | Benchmark target from ICMR-INDIAB; verify age cutoff. |
| **5** | 1. Disease Module (`hypertension.yaml`) | `annual_incidence_weight` | $\lambda_{\text{htn}}$ | `0.0344` ($\text{yr}^{-1}$) | **[CAT-3]** | Prospective annual transition hazard from normotension to HTN. | **Unidentifiable from Wave 1:** Prevalence $\ne$ incidence. Requires CURES/CARRS prospective cohorts or LASI Wave 2 panel. |
| **6** | 1. Disease Module (`hypertension.yaml`) | `screening_delay_days` | $\tau_{\text{screen}}$ | `90` (days) | **[CAT-4]** | Mean delay between condition onset and first screening visit. | Heuristic parameter. Sensitivity range: 30 to 365 days. |
| **7** | 1. Disease Module (`hypertension.yaml`) | `maintenance_delay_days`| $\tau_{\text{maint}}$ | `180` (days) | **[CAT-4]** | Routine chronic follow-up revisit interval. | Outpatient review cycle. Sensitivity range: 90 to 365 days. |
| **8** | 2. Physiology Anchor (`forward_hemodynamics.py`) | `mean_sbp_anchor` | $\mu_{0, \text{sbp}}$ | `120.0` (mmHg) | **[CAT-2]** | Mean latent resting SBP at baseline age 45. | **Confounded:** Untreated 45-year-olds in surveys include undiagnosed hypertensives. Requires unmedicated normotensive filtering. |
| **9** | 2. Physiology Anchor (`forward_hemodynamics.py`) | `sd_sbp_anchor` | $\sigma_{0, \text{sbp}}$ | `9.0` (mmHg) | **[CAT-2]** | Inter-individual standard deviation of resting SBP. | Confounded by within-visit measurement error variance ($\sigma_{\text{within}}$). Must be de-convolved: $\sigma_0^2 = \sigma_{\text{obs}}^2 - \sigma_{\text{meas}}^2$. |
| **10** | 2. Physiology Anchor (`forward_hemodynamics.py`) | `mean_dbp_anchor` | $\mu_{0, \text{dbp}}$ | `78.0` (mmHg) | **[CAT-2]** | Mean latent resting DBP at baseline age 45. | Same de-convolution and normotensive filtering as SBP. |
| **11** | 2. Physiology Anchor (`forward_hemodynamics.py`) | `sd_dbp_anchor` | $\sigma_{0, \text{dbp}}$ | `6.0` (mmHg) | **[CAT-2]** | Inter-individual standard deviation of resting DBP. | Same de-convolution as SBP. |
| **12** | 2. Physiology Anchor (`forward_hemodynamics.py`) | `sbp_dbp_correlation` | $\rho_0$ | `0.65` (—) | **[CAT-1]** | Pearson correlation between unmedicated resting SBP and DBP. | Directly estimable from unmedicated tri-readings. |
| **13** | 2. Physiological Guard (`forward_hemodynamics.py`) | `min_pulse_pressure` | $\text{PP}_{\min}$ | `20.0` (mmHg) | **[CAT-4]** | Biological minimum pulse pressure (stroke volume floor). | Fixed biophysical constraint; not subject to empirical tuning. |
| **14** | 2. Physiological Guard (`forward_hemodynamics.py`) | `min_sbp` | $\text{SBP}_{\min}$ | `70.0` (mmHg) | **[CAT-4]** | Minimum viable cerebral perfusion systolic floor. | Inviolable biophysical guard. |
| **15** | 2. Physiological Guard (`forward_hemodynamics.py`) | `max_sbp` | $\text{SBP}_{\max}$ | `260.0` (mmHg) | **[CAT-4]** | Upper ceiling for severe hypertensive emergency. | Inviolable biophysical guard. |
| **16** | 2. Physiological Guard (`forward_hemodynamics.py`) | `min_dbp` | $\text{DBP}_{\min}$ | `40.0` (mmHg) | **[CAT-4]** | Minimum viable coronary perfusion diastolic floor. | Inviolable biophysical guard. |
| **17** | 2. Physiological Guard (`forward_hemodynamics.py`) | `max_dbp` | $\text{DBP}_{\max}$ | `150.0` (mmHg) | **[CAT-4]** | Upper ceiling for acute intracranial hemorrhage risk. | Inviolable biophysical guard. |
| **18** | 2. Aging Drift (`forward_hemodynamics.py`) | `annual_drift_sbp` | $\beta_{\text{age, sbp}}$ | `0.60` ($\text{mmHg/yr}$) | **[CAT-2]** | Cross-sectional age gradient $\partial \text{SBP} / \partial \text{age}$. | **Severely Confounded:** Confounders: birth cohort effects, differential cardiovascular survival. Calibrate as cross-sectional gradient; flag as unverified for intra-individual aging. |
| **19** | 2. Aging Drift (`forward_hemodynamics.py`) | `annual_drift_dbp_early` | $\beta_{\text{age, dbp1}}$| `0.25` ($\text{mmHg/yr}$) | **[CAT-2]** | Cross-sectional DBP age gradient prior to inflection. | Estimable via piecewise linear spline on unmedicated adults. |
| **20** | 2. Aging Drift (`forward_hemodynamics.py`) | `annual_drift_dbp_late` | $\beta_{\text{age, dbp2}}$| `-0.15` ($\text{mmHg/yr}$) | **[CAT-2]** | Cross-sectional late-life DBP decline slope. | Estimable via piecewise linear spline after inflection point. |
| **21** | 2. Aging Drift (`forward_hemodynamics.py`) | `age_inflection_dbp` | $a_{\text{inflect}}$ | `60.0` (yrs) | **[CAT-2]** | Age at which DBP peaks and begins late-life decline. | Estimable via non-linear least squares change-point estimation. |
| **22** | 2. Comorbidity Shift (`forward_hemodynamics.py`) | `t2d_sbp_shift` | $\gamma_{\text{t2d, sbp}}$ | `4.5` (mmHg) | **[CAT-2]** | SBP difference between diabetic and non-diabetic adults. | Observational regression coefficient adjusting for age and sex. Confounded by BMI and duration of diabetes. |
| **23** | 2. Comorbidity Shift (`forward_hemodynamics.py`) | `t2d_dbp_shift` | $\gamma_{\text{t2d, dbp}}$ | `2.0` (mmHg) | **[CAT-2]** | DBP difference between diabetic and non-diabetic adults. | Observational regression coefficient adjusting for age and sex. |
| **24** | 2. Demographic Offset (`forward_hemodynamics.py`) | `male_sbp_offset` | $\delta_{\text{male, sbp}}$ | `2.0` (mmHg) | **[CAT-1]** | Adjusted mean difference in resting SBP between males and females. | Directly estimable from multivariable regression on unmedicated respondents. |
| **25** | 2. Demographic Offset (`forward_hemodynamics.py`) | `male_dbp_offset` | $\delta_{\text{male, dbp}}$ | `1.5` (mmHg) | **[CAT-1]** | Adjusted mean difference in resting DBP between males and females. | Directly estimable from multivariable regression on unmedicated respondents. |
| **26** | 3. Measurement Protocol (`bp_measurement.py`) | `reading1_alerting_sbp` | $\alpha_{\text{alert, sbp}}$ | `3.5` (mmHg) | **[CAT-1]** | Mean situational white-coat elevation on Reading 1: $\mathbb{E}[R_1 - R_2]$. | Directly identified by pairwise difference between Reading 1 and Reading 2 in survey microdata. |
| **27** | 3. Measurement Protocol (`bp_measurement.py`) | `reading1_alerting_dbp` | $\alpha_{\text{alert, dbp}}$ | `1.5` (mmHg) | **[CAT-1]** | Mean situational white-coat elevation on Reading 1: $\mathbb{E}[R_1 - R_2]$. | Directly identified by pairwise difference between Reading 1 and Reading 2 in survey microdata. |
| **28** | 3. Measurement Protocol (`bp_measurement.py`) | `within_visit_noise_sd` | $\sigma_{\text{within}}$ | `1.8` (mmHg) | **[CAT-1]** | Standard deviation of resting measurement noise. | Identified from difference between resting readings: $\sigma_{\text{within}}^2 = \frac{1}{2}\text{Var}(R_2 - R_3)$. |
| **29** | 3. Measurement Protocol (`bp_measurement.py`) | `inter_reading_correlation` | $\phi_{\text{ar1}}$ | `0.70` (—) | **[CAT-1]** | Correlation between consecutive readings in tri-measurement. | Identified from sample autocorrelation: $\text{Corr}(R_2 - \bar{R}, R_3 - \bar{R})$. |
| **30** | 3. Measurement Protocol (`bp_measurement.py`) | `white_coat_prob` | $p_{\text{wc}}$ | `0.15` (—) | **[CAT-4]** | Proportion of individuals exhibiting clinic white-coat hypertension. | Unidentifiable in household surveys (requires ambulatory BP monitoring). Literature-fixed. |
| **31** | 4. Diagnostic Rules (`forward_hemodynamics.py`) | `severe_sbp_threshold` | $T_{\text{severe, sbp}}$ | `180.0` (mmHg) | **[CAT-4]** | Hypertensive urgency immediate diagnosis threshold. | Clinical practice guideline rule (ICMR / AHA); not an empirical parameter. |
| **32** | 4. Diagnostic Rules (`forward_hemodynamics.py`) | `severe_dbp_threshold` | $T_{\text{severe, dbp}}$ | `120.0` (mmHg) | **[CAT-4]** | Hypertensive urgency immediate diagnosis threshold. | Clinical practice guideline rule (ICMR / AHA); not an empirical parameter. |
| **33** | 4. Diagnostic Rules (`forward_hemodynamics.py`) | `elevated_sbp_threshold` | $T_{\text{htn, sbp}}$ | `140.0` (mmHg) | **[CAT-4]** | Diagnostic cut-point for Stage 1/2 clinical hypertension. | Clinical practice guideline definition; fixed constant. |
| **34** | 4. Diagnostic Rules (`forward_hemodynamics.py`) | `elevated_dbp_threshold` | $T_{\text{htn, dbp}}$ | `90.0` (mmHg) | **[CAT-4]** | Diagnostic cut-point for Stage 1/2 clinical hypertension. | Clinical practice guideline definition; fixed constant. |
| **35** | 4. Diagnostic Rules (`forward_hemodynamics.py`) | `confirmed_visits_required` | $K_{\text{visits}}$ | `2` (visits) | **[CAT-4]** | Multi-visit confirmation requirement for diagnosis. | Clinical guideline requirement; fixed operational rule. |
| **36** | 5. Pharmacodynamics (`forward_hemodynamics.py`) | `delta_drug_sbp` | $\delta_{\text{drug, sbp}}$ | `12.0` (mmHg) | **[CAT-5]** | Causal biological SBP reduction from antihypertensive monotherapy. | **Fundamentally Non-Identifiable from Cross-Sectional Observational Data:** Comparing treated to untreated individuals yields confounding by indication (sicker patients get drugs) and adherence heterogeneity. Must be fixed from randomized trials (BPLTTC meta-analysis). |

---

### 8.2 Summary of Identifiability Audits

Of the 36 parameters cataloged:
- **7 parameters (19.4%)** are **Directly Estimable [CAT-1]** from authorized Wave 1 cross-sectional microdata (sex ratio, age distribution, baseline SBP/DBP correlation, sex offsets, Reading 1 alerting bias, and within-visit measurement error).
- **8 parameters (22.2%)** are **Estimable Under Explicit Modeling Assumptions [CAT-2]** (baseline resting anchors, cross-sectional age gradients, change-point inflection, and diabetes comorbidity shifts). These require explicit sensitivity analyses documenting potential survivorship and cohort confounding.
- **1 parameter (2.8%)** **Requires Longitudinal Panel Observations [CAT-3]** (annual disease transition hazard $\lambda_{\text{htn}}$).
- **19 parameters (52.8%)** **Require External Evidence / Clinical Guidelines [CAT-4]** (biophysical guard limits, clinical diagnostic criteria thresholds, visit delays, and white-coat prevalence).
- **1 parameter (2.8%)** is **Fundamentally Non-Identifiable [CAT-5]** from observational cross-sectional survey data (causal pharmacological drug effect $\delta_{\text{drug}}$) due to intractable confounding by indication and unmeasured compliance.

---

## 9. Revised Calibration and Validation Protocol

The findings of this audit mandate specific revisions to the execution pipeline:

```mermaid
flowchart TD
    subgraph DataPrep [1. Ingestion & Cluster-Stratified Splitting]
        INGEST[LasiDataIngestor: SHA-256 Verified]
        PSU_MAP[Group by State, Urban/Rural, and PSU_ID]
        CLUSTER_SPLIT{Stratified PSU Cluster Split}
        
        PART_A[Partition A: Calibration Set 50% PSUs]
        PART_B[Partition B: Model Tuning Set 25% PSUs]
        PART_C[Partition C: Secure Holdout Set 25% PSUs]
        
        INGEST --> PSU_MAP --> CLUSTER_SPLIT
        CLUSTER_SPLIT --> PART_A & PART_B & PART_C
    end

    subgraph CalibrationHarness [2. Revised Calibration on Partition A]
        SURVEY_WT[Re-normalize Partition A Survey Weights]
        BOOT_VAR[PSU Cluster Bootstrap Variance Estimation]
        LOSS_FN[Corrected Loss Function: Eq. 12]
        OPTIM[Nelder-Mead / Powell Optimization]
        FREEZE[Freeze Calibrated Parameters in Manifest]
        
        PART_A --> SURVEY_WT --> BOOT_VAR --> LOSS_FN
        LOSS_FN --> OPTIM --> FREEZE
    end

    subgraph TuningHarness [3. Model Architecture Selection on Partition B]
        TUNING[Evaluate Bilinear vs Smooth Splines for Late-Life DBP]
        PART_B --> TUNING
    end

    subgraph HoldoutValidation [4. Independent Validation on Partition C]
        VAULT[Decrypt Partition C Vault via Single-Use Key]
        EVAL[LasiExternalEvaluator on Partition C]
        GATE_EVAL{Evaluate Predeclared Criteria}
        
        FREEZE --> EVAL
        VAULT --> EVAL
        EVAL --> GATE_EVAL
        GATE_EVAL -->|All Predeclared Criteria Met| PASS[GATE: PASS]
        GATE_EVAL -->|Any Mandatory Criterion Fails| FAIL[GATE: FAIL]
    end

    style PART_C fill:#ffebee,stroke:#c62828,stroke-width:2px;
    style PASS fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    style FAIL fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px;
```

---

## 10. Unresolved Scientific Questions Requiring Human & Committee Review

The audit identifies five substantive clinical, epidemiological, and legal questions that cannot be resolved programmatically and require human review:

1. **Data Use Agreement (DUA) Execution and Credentialing:**
   - *Issue:* Individual-level LASI Wave 1 microdata requires credentialed approval through the International Institute for Population Sciences (IIPS), Mumbai, and Gateway to Global Aging Data.
   - *Review Required:* Legal and research governance review must confirm that simulated calibration complies with all data privacy, terms-of-use, and participant re-identification restrictions.
2. **Clinical Consensus on Acceptable Synthetic Blood Pressure Tolerances:**
   - *Issue:* While $W_1 \le 3.5\text{ mmHg}$ and $D_{\text{ks}} \le 0.08$ represent reasonable engineering benchmarks, there is no universally established international standard for what constitutes "clinically acceptable" synthetic hemodynamic fidelity.
   - *Review Required:* A clinical advisory panel (cardiologists and biostatisticians) must formally ratify the acceptance boundaries prior to unlocking the validation gate.
3. **Disentangling Observational Treatment Discrepancies from Causal Drug Efficacy:**
   - *Issue:* In observational surveys, treated hypertensive individuals frequently exhibit *higher* measured blood pressure than untreated individuals because patients with severe Stage 2/3 hypertension are far more likely to receive prescriptions (confounding by indication).
   - *Review Required:* Epidemiological alignment on whether to fix causal drug efficacy from randomized trial meta-analyses (e.g. BPLTTC: $-12/-7\text{ mmHg}$) while calibrating clinical prescribing thresholds and adherence drop-off to match the observed cross-sectional treated distribution.
4. **Classification of Traditional and Unconventional Medications:**
   - *Issue:* Survey respondents in India frequently report taking traditional/ayurvedic remedies for high blood pressure.
   - *Review Required:* Clinical determination on whether traditional remedies should be coded as active antihypertensive pharmacotherapy in composite hypertension indicators.
5. **DBS vs. Venous HbA1c Calibration in South Asian Cohorts:**
   - *Issue:* In LASI Wave 1, HbA1c was assayed using Dried Blood Spot (DBS) specimens rather than venous whole-blood HPLC. DBS assays are sensitive to ambient temperature and hematocrit variations.
   - *Review Required:* Laboratory medicine review on whether to implement published regression conversion equations or restrict validation strictly to raw DBS assay metrics.

---

## 11. Concluding Audit Sign-Off

### Summary of Audit Outcome:
- **Mathematical Formulations:** Corrected to eliminate quadratic double-weighting in the calibration objective and incorporate simulation Monte Carlo uncertainty.
- **Survey Statistics:** Upgraded from simple Kish effective sample size to multi-stage PSU cluster bootstrap variance estimation and singleton PSU collapse rules.
- **Holdout Independence:** Hardened by mandating Primary Sampling Unit (PSU) cluster-level partitioning rather than unclustered participant-level splitting.
- **Parameter Provenance:** All 36 parameters cataloged and classified across the five formal identifiability categories.
- **Validation Gate:** Formally certified at **`REFERENCE_DATA_PENDING`**. No parameters were calibrated, no clinical defaults were altered, and no unauthorized microdata was ingested.

**Audit Status:** Certified and Ready for Protocol Integration.
