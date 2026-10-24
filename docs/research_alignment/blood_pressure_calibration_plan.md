# Blood Pressure Calibration Plan: Establishing a Rigorous Baseline

**Project:** SYNAPSE Phase 2 Synthetic Healthcare Simulation  
**Document Purpose:** Baseline Characterization and Scientific Calibration Plan for Population Blood Pressure Dynamics  
**Current Gate Status:** `REFERENCE_DATA_PENDING` (Preserved strictly)  
**Date of Execution:** October 2026  

---

## 1. Executive Summary

This document establishes the scientific baseline and future empirical calibration methodology for blood pressure generation in SYNAPSE Phase 2.

### Critical Premise & Governance Boundary:
In strict compliance with project governance:
- **No unsupported age coefficients, arbitrary SBP/DBP ratios, or heuristic formulas have been introduced.**
- **No disease-transition probabilities in `hypertension.yaml` have been modified.**
- An uncalibrated, evidence-anchored baseline is formally documented so that subsequent calibration against genuine reference data can be rigorously quantified without historical confounding.

---

## 2. Characterization of the Uncalibrated Baseline Generator

### 2.1 Current Stationary Modeling Assumptions

In the current implementation ([synapse_simulator/datagen/community_assessment.py](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/community_assessment.py#L127-L147)), community vital signs are generated as follows:

```python
if has_htn:
    if is_treated:
        sbp = round(pat_rng.uniform(120.0, 150.0), 1)
        dbp = round(pat_rng.uniform(75.0, 92.0), 1)
    else:
        sbp = round(pat_rng.uniform(145.0, 168.0), 1)
        dbp = round(pat_rng.uniform(90.0, 104.0), 1)
else:
    sbp = round(pat_rng.uniform(110.0, 135.0), 1)
    dbp = round(pat_rng.uniform(70.0, 84.0), 1)

if sbp - dbp < 20.0:
    sbp = round(dbp + 25.0, 1)
```

### 2.2 Core Structural Assumptions:
1. **Stationary Uniform Intervals:** Blood pressure is drawn uniformly within three fixed intervals:
   - Normotensive: $\text{SBP} \in [110, 135]$, $\text{DBP} \in [70, 84]$ mmHg.
   - Treated Hypertensive: $\text{SBP} \in [120, 150]$, $\text{DBP} \in [75, 92]$ mmHg.
   - Untreated Hypertensive: $\text{SBP} \in [145, 168]$, $\text{DBP} \in [90, 104]$ mmHg.
2. **Physiological Guard:** A hard lower bound ensures pulse pressure $PP = SBP - DBP \ge 20.0$ mmHg.
3. **Decoupling from Biological Age:** Conditional on disease status (`has_htn`) and treatment (`is_treated`), the generated distribution is identically distributed across chronological age $a \in [45, 100+]$.

---

## 3. Observed Age-Stratified Empirical Distributions (Baseline Cohort, Seed 42)

The baseline simulation of 561 assessed older adults reveals an essentially flat trajectory across chronological age:

| Age Decile / Group | Assessed $N$ | Mean SBP (SD) | Median SBP | Mean DBP (SD) | Median DBP | Mean Pulse Pressure (SD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **45–54 years** | 203 | 127.78 (10.06) | 127.20 | 79.63 (5.35) | 79.30 | 48.15 (9.81) |
| **55–64 years** | 209 | 127.42 (9.60) | 126.70 | 79.87 (5.39) | 79.60 | 47.55 (9.69) |
| **65–74 years** | 40 | 129.60 (9.83) | 129.10 | 80.51 (5.65) | 79.60 | 49.09 (10.62) |
| **75+ years** | 109 | 126.86 (9.85) | 124.40 | 79.79 (5.54) | 79.50 | 47.07 (9.57) |
| **All Older Adults (45+)** | **561** | **127.60 (9.83)** | **126.90** | **79.81 (5.42)** | **79.50** | **47.78 (9.77)** |

```
Observed Mean SBP by Age Decile (Flat Baseline):
135 ┼
    │
130 ┼      127.8        127.4        129.6        126.9
    │   ───●────────────●────────────●────────────●────
125 ┼
    └──────┬────────────┬────────────┬────────────┬─────
         45-54        55-64        65-74         75+
```

---

## 4. Scientific Diagnosis: Plausibility vs. Distributional Fidelity

It is critical to distinguish between two levels of modeling success:

### 4.1 Physiological Plausibility (Achieved at Baseline)
- Every generated pair $(SBP_i, DBP_i)$ is hemodynamically valid ($SBP > DBP$).
- Zero individuals have implausible pulse pressure ($< 20$ mmHg or $> 110$ mmHg).
- The overall population mean ($127.60$ / $79.81$ mmHg) falls within accepted epidemiological norms for South Asian adults.
- Treated individuals reflect expected pharmacological suppression ($58.80\%$ controlled, $41.20\%$ uncontrolled).

### 4.2 Population-Level Distributional Fidelity (Uncalibrated Baseline Limitation)
- **Absence of Age-Related Systolic Drift:** In real human populations (LASI Wave 1, Framingham, NHANES), systolic pressure rises steadily from age 40 to 80+ by $15$–$25$ mmHg due to aortic stiffening and loss of vascular compliance.
- **Absence of Diastolic Mid-Life Plateau:** In genuine epidemiological data, diastolic pressure increases up to age 50–55, plateaus, and then declines in older age, resulting in dramatic pulse pressure widening in the eighth and ninth decades of life.
- **Isolated Systolic Hypertension (ISH) Mechanism:** In the baseline model, ISH ($11.94\%$) occurs purely through the random overlap of uniform bounds, not through biological arterial stiffening.

---

## 5. Evidence Requirements for Calibration

Before modifying blood pressure generation parameters, the following empirical evidence must be extracted from genuine reference data:

1. **Joint Conditional Quantiles by Age Decile:**
   - Empirical quantiles ($10\text{th}, 25\text{th}, 50\text{th}, 75\text{th}, 90\text{th}$) of SBP, DBP, and PP stratified across 5-year age bands ($45\text{--}49, 50\text{--}54, \dots, 80+$).
2. **Sex-Specific Divergence:**
   - Quantification of post-menopausal systolic acceleration in females relative to males.
3. **Treatment Effect Distributions:**
   - Empirical difference in SBP and DBP among individuals on active monotherapy vs dual therapy in the target population.
4. **Intra-Individual Measurement Variance:**
   - Repeated measurement variability (difference between 1st, 2nd, and 3rd survey readings in LASI protocol).

---

## 6. Mathematical Framework for Future Calibration

When genuine reference microdata are ingested, the stationary uniform formulation will be replaced with a physiologically grounded, parameterizable distribution:

### 6.1 Biological Vascular Compliance Formulation
$$\text{SBP}_i = \mu_{\text{sbp}}(a_i, s_i, L_i, \text{Rx}_i) + \epsilon_{i, \text{sbp}}$$
$$\text{DBP}_i = \mu_{\text{dbp}}(a_i, s_i, L_i, \text{Rx}_i) + \epsilon_{i, \text{dbp}}$$

where:
- $a_i$ is chronological age.
- $s_i$ is biological sex.
- $L_i \in \{0, 1\}$ is latent hypertension status.
- $\text{Rx}_i \in \{0, 1\}$ is active pharmacotherapy.

The mean functions incorporate arterial elastance:
$$\mu_{\text{sbp}}(a, s, L, \text{Rx}) = \beta_0 + \beta_L \cdot L + \beta_{\text{age}} \cdot (a - 45) + \beta_{\text{stiff}} \cdot \max(0, a - 55)^2 - \delta_{\text{Rx}} \cdot \text{Rx}$$
$$\mu_{\text{dbp}}(a, s, L, \text{Rx}) = \alpha_0 + \alpha_L \cdot L + \alpha_{\text{age1}} \cdot \min(a - 45, 15) - \alpha_{\text{age2}} \cdot \max(0, a - 60) - \gamma_{\text{Rx}} \cdot \text{Rx}$$

Residuals $(\epsilon_{\text{sbp}}, \epsilon_{\text{dbp}})$ are drawn from a bivariate Gaussian or Frank copula with correlation $\rho \in [0.55, 0.75]$, truncated at the physiological invariant boundary $PP \ge 20$ mmHg.

### 6.2 Minimum-Distance Parameter Estimation Protocol
Parameters $\mathbf{\Theta} = \{\beta_0, \beta_L, \beta_{\text{age}}, \beta_{\text{stiff}}, \delta_{\text{Rx}}, \alpha_0, \alpha_L, \dots\}$ must be estimated via **Minimum-Distance Estimation (MDE)** against the calibration partition of the reference data:
$$\widehat{\mathbf{\Theta}} = \arg\min_{\mathbf{\Theta}} \sum_{k} \left[ \frac{\hat{q}_k^{\text{syn}}(\mathbf{\Theta}) - \hat{q}_k^{\text{ref}}}{\hat{\sigma}_k^{\text{ref}}} \right]^2$$

where $\hat{q}_k$ represents the joint age-stratified marginal quantiles and $\hat{\sigma}_k^{\text{ref}}$ is the complex-survey standard error of the reference quantile.

---

## 7. Preservation of the Baseline and Anti-Regression Invariant

1. **Baseline Invariant:** The current stationary implementation must remain archived and documented as the *SYNAPSE Phase 2 Uncalibrated Structural Baseline*.
2. **Ablation Comparison:** When future calibrated models are developed, evaluation reports must present side-by-side comparisons:
   - Baseline Uncalibrated vs Genuine Reference Data.
   - Calibrated Model vs Genuine Reference Data (on untouched holdout validation set).
3. **No Retrospective Fitting:** The current gate `REFERENCE_DATA_PENDING` ensures that the simulation does not overfit to synthetic fixtures or provisional hypotheses prior to genuine data availability.
