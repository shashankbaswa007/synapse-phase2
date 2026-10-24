# Scientific Audit: Multi-Reading Blood Pressure Measurement Model

**Document ID:** `SYNAPSE-AUDIT-2026-BP-MEASUREMENT-02`  
**Classification:** Focused Scientific Audit & Evidential Review  
**Target Repository:** `synapse-phase2`  
**Target Module:** `synapse_simulator/datagen/bp_measurement.py`  
**Evaluation Reference Date:** `2024-06-29T00:00:00` (Simulation Day 180 of 720)  
**External Validation Gate Status:** `REFERENCE_DATA_PENDING`  
**Reproducibility Seed:** `42` ($N = 2,200$; 561 assessed community older adults)  

---

## 1. Executive Summary & Objective

This document reports a focused scientific audit of the multi-reading blood pressure (BP) measurement error model implemented in `synapse_simulator/datagen/bp_measurement.py`. The simulation models the independent community health assessment pathway for older adults ($\text{Age} \ge 45$) representative of household epidemiological surveys (specifically the Longitudinal Ageing Study in India, LASI Wave 1).

The audit addresses eight structural dimensions:
1. **Mathematical Tracing of Current Measurement Equations:** Complete formal specification of latent BP sampling, first-reading situational alerting reactivity, within-person resting variability, derived final analysis values, and pulse pressure boundary checks.
2. **Evidential Assessment of Model Parameters:** Classification of empirical support for alerting increments, resting variance, inter-reading correlation, and device characteristics using a rigorous 4-tier evidentiary schema.
3. **Statistical Analysis of the Exact-Cancellation Assumption:** Investigation of the baseline `SYMMETRICAL_UNBIASED` model ($\epsilon_3 = -\epsilon_2$), proving that it achieves zero residual measurement uncertainty in final analysis values, shields population prevalence from noise-induced distortion, but suppresses biological between-reading non-zero covariance.
4. **Empirical Cohort Quantification:** Exact reproduction of the seed-42 cohort ($N=2,200$, 561 assessed older adults), comparing latent state, individual readings (1, 2, 3), and final derived values, including threshold crossings and demographic/treatment stratifications.
5. **Protocol Fidelity Review:** Auditing simulated procedures against official LASI Wave 1 documentation, distinguishing verified protocol invariants from provisional assumptions.
6. **Alternative Measurement Model Formulation:** Implementation and evaluation of a stationary first-order autoregressive model (`AUTOREGRESSIVE_AR1`, $\rho = 0.70$) behind explicit configuration, preserving the baseline reproducibility without ungrounded parameter tuning.
7. **Targeted Verification Tests:** Implementation of 4 new targeted regression tests (tests 19–22 in `tests/test_bp_measurement_protocol.py`), confirming baseline preservation, mathematical cancellation, AR(1) error properties, and gate preservation across all 261 repository tests.
8. **Remaining Scientific Blockers & Governance Constraints:** Documentation of unresolved data-access dependencies requiring `REFERENCE_DATA_PENDING` gate enforcement.

---

## 2. Trace of Current Measurement Equations

The community assessment generator (`synapse_simulator/datagen/community_assessment.py`) and protocol simulator (`synapse_simulator/datagen/bp_measurement.py`) decouple latent resting physiological state from observed sequential readings.

### 2.1 Latent Resting Blood Pressure Generation
For each assessed older adult $i$, the latent resting blood pressure pair $(\text{SBP}_{i, \text{latent}}, \text{DBP}_{i, \text{latent}})$ is sampled based on point-in-time clinical state and treatment status:

$$\text{SBP}_{i, \text{latent}} \sim \begin{cases} 
\mathcal{U}(120.0, 150.0), & \text{if } \text{HTN}_i = 1 \text{ and } \text{Treated}_i = 1 \\
\mathcal{U}(145.0, 168.0), & \text{if } \text{HTN}_i = 1 \text{ and } \text{Treated}_i = 0 \\
\mathcal{U}(110.0, 135.0), & \text{if } \text{HTN}_i = 0
\end{cases}$$

$$\text{DBP}_{i, \text{latent}} \sim \begin{cases} 
\mathcal{U}(75.0, 92.0), & \text{if } \text{HTN}_i = 1 \text{ and } \text{Treated}_i = 1 \\
\mathcal{U}(90.0, 104.0), & \text{if } \text{HTN}_i = 1 \text{ and } \text{Treated}_i = 0 \\
\mathcal{U}(70.0, 84.0), & \text{if } \text{HTN}_i = 0
\end{cases}$$

Values are rounded to one decimal place.

### 2.2 First-Reading Situational Alerting Effect
To model acute sympathetic activation during the initial cuff inflation, the first reading ($k=1$) adds an alerting shift:

$$\delta_{\text{alert}, \text{SBP}, i} \sim \mathcal{N}(\mu_{\text{alert}, \text{SBP}}, \sigma_{\text{alert}, \text{SBP}}^2), \quad \mu_{\text{alert}, \text{SBP}} = 3.5\text{ mmHg}, \; \sigma_{\text{alert}, \text{SBP}} = 0.5\text{ mmHg}$$

$$\delta_{\text{alert}, \text{DBP}, i} \sim \mathcal{N}(\mu_{\text{alert}, \text{DBP}}, \sigma_{\text{alert}, \text{DBP}}^2), \quad \mu_{\text{alert}, \text{DBP}} = 1.5\text{ mmHg}, \; \sigma_{\text{alert}, \text{DBP}} = 0.3\text{ mmHg}$$

$$\text{Reading } 1: \begin{cases}
\text{SBP}_{i, 1} = \text{SBP}_{i, \text{latent}} + \delta_{\text{alert}, \text{SBP}, i} + \eta_{i, \text{SBP}} \\
\text{DBP}_{i, 1} = \text{DBP}_{i, \text{latent}} + \delta_{\text{alert}, \text{DBP}, i} + \eta_{i, \text{DBP}}
\end{cases}$$

where $\eta_{i, \text{SBP}} \sim \mathcal{N}(0, 0.4^2)$ and $\eta_{i, \text{DBP}} \sim \mathcal{N}(0, 0.2^2)$ represent residual micro-fluctuation during reading 1.

### 2.3 Within-Person Reading Variability (Baseline `SYMMETRICAL_UNBIASED`)
For sequential readings $k=2$ and $k=3$, the baseline model samples a single resting fluctuation vector:

$$\epsilon_{i, \text{SBP}} \sim \mathcal{N}(0, \sigma_{\text{within}}^2), \quad \sigma_{\text{within}} = 1.8\text{ mmHg}$$

$$\epsilon_{i, \text{DBP}} \sim \mathcal{N}\left(0, \left(\frac{\sigma_{\text{within}}}{2}\right)^2\right) = \mathcal{N}(0, 0.9^2)$$

The errors are assigned symmetrically:

$$\text{Reading } 2: \begin{cases}
\text{SBP}_{i, 2} = \text{SBP}_{i, \text{latent}} + \epsilon_{i, \text{SBP}} \\
\text{DBP}_{i, 2} = \text{DBP}_{i, \text{latent}} + \epsilon_{i, \text{DBP}}
\end{cases}$$

$$\text{Reading } 3: \begin{cases}
\text{SBP}_{i, 3} = \text{SBP}_{i, \text{latent}} - \epsilon_{i, \text{SBP}} \\
\text{DBP}_{i, 3} = \text{DBP}_{i, \text{latent}} - \epsilon_{i, \text{DBP}}
\end{cases}$$

### 2.4 Final Analysis Blood Pressure Calculation
Under the reference protocol (readings 2 and 3 selected), the derived final analysis blood pressure is calculated by arithmetic averaging:

$$\text{SBP}_{i, \text{final}} = \frac{\text{SBP}_{i, 2} + \text{SBP}_{i, 3}}{2}$$

$$\text{DBP}_{i, \text{final}} = \frac{\text{DBP}_{i, 2} + \text{DBP}_{i, 3}}{2}$$

$$\text{PP}_{i, \text{final}} = \text{SBP}_{i, \text{final}} - \text{DBP}_{i, \text{final}}$$

### 2.5 Verification of Exact Error Cancellation and Residual Uncertainty
Substituting the equations from Section 2.3 into Section 2.4:

$$\text{SBP}_{i, \text{final}} = \frac{(\text{SBP}_{i, \text{latent}} + \epsilon_{i, \text{SBP}}) + (\text{SBP}_{i, \text{latent}} - \epsilon_{i, \text{SBP}})}{2} = \frac{2 \cdot \text{SBP}_{i, \text{latent}}}{2} = \text{SBP}_{i, \text{latent}}$$

$$\text{DBP}_{i, \text{final}} = \frac{(\text{DBP}_{i, \text{latent}} + \epsilon_{i, \text{DBP}}) + (\text{DBP}_{i, \text{latent}} - \epsilon_{i, \text{DBP}})}{2} = \frac{2 \cdot \text{DBP}_{i, \text{latent}}}{2} = \text{DBP}_{i, \text{latent}}$$

**Audit Finding:**
* **Exact Cancellation:** Yes. Readings 2 and 3 utilize equal-and-opposite errors ($\epsilon$ and $-\epsilon$) by mathematical design.
* **Residual Measurement Uncertainty in Final Analysis Value:** Exactly **zero** ($\text{Var}(\text{SBP}_{\text{final}} - \text{SBP}_{\text{latent}}) = 0.00\text{ mmHg}^2$). The final analysis value is an exact algebraic identity with the latent resting physiological state.

### 2.6 Pulse Pressure and Physiological Validity Constraints
Validation checks occur at two distinct stages:
1. **Per-Reading Validity:**
   - $\text{SBP}_k \in [60.0, 280.0]\text{ mmHg}$
   - $\text{DBP}_k \in [40.0, 160.0]\text{ mmHg}$
   - $\text{PP}_k = (\text{SBP}_k - \text{DBP}_k) \ge 20.0\text{ mmHg}$
   - If violated, the reading is marked invalid (`OUT_OF_RANGE_SBP`, `OUT_OF_RANGE_DBP`, or `PHYSIOLOGICALLY_IMPLAUSIBLE_PP`).
2. **Final Analysis Derivation Validity:**
   - Evaluated after averaging.
   - If derived $\text{PP}_{\text{final}} < 20.0\text{ mmHg}$, $\text{SBP}_{\text{final}}$ is coerced to $\text{DBP}_{\text{final}} + 20.0\text{ mmHg}$.

---

## 3. Evidential Status and Parameter Provenance

Every parameter governing blood pressure measurement was audited against project research documentation and external biomedical literature. Parameters are classified into four evidential categories.

| Parameter | Implemented Value | Evidential Status | Source / Evidence Basis | Justification & Cautions |
| :--- | :--- | :--- | :--- | :--- |
| **Measurement Device** | Digital oscillometric monitor (Omron HEM-7121) | **Supported by a directly applicable source** | LASI Wave 1 Fieldwork Manual (IIPS 2017); LASI Biomarker Protocol | Official reference survey specification mandates Omron HEM-7121 with standardized arm cuffs. |
| **Reading Schedule** | 3 seated readings, 5-minute quiet intervals | **Supported by a directly applicable source** | LASI Wave 1 Fieldwork Manual; WHO SAGE Biomarker Protocol | Official protocol requires 3 readings separated by 5 minutes, discarding reading 1. |
| **First-Reading SBP Alerting Increment** | $\mu = 3.5\text{ mmHg}$, $\sigma = 0.5\text{ mmHg}$ | **Supported by a source requiring cautious extrapolation** | NHANES/Framingham white-coat response studies (Stergiou et al., *J Hypertens* 2018; Myers et al., *Hypertension* 2010) | Well-established epidemiological phenomenon; magnitude in Indian older adults must be empirically verified against LASI microdata. |
| **First-Reading DBP Alerting Increment** | $\mu = 1.5\text{ mmHg}$, $\sigma = 0.3\text{ mmHg}$ | **Supported by a source requiring cautious extrapolation** | White-coat literature; DBP typically exhibits roughly half the alerting reactivity of SBP | Extrapolated from general population studies; requires empirical tuning on genuine reference microdata. |
| **Within-Visit Resting SBP Variance** | $\sigma_{\text{within}} = 1.8\text{ mmHg}$ | **Provisional assumption** | Internal conservative heuristic | Chosen to introduce realistic reading variation ($\pm 3.6\text{ mmHg}$ 95% CI) without destabilizing baseline calibration. |
| **Within-Visit Resting DBP Variance** | $\sigma_{\text{within}} = 0.9\text{ mmHg}$ | **Provisional assumption** | Internal conservative heuristic | Assumes DBP resting variation is approximately $0.5 \times \sigma_{\text{SBP}}$. |
| **Baseline Inter-Reading Error Correlation** | $\rho = -1.0$ (equal & opposite: $\epsilon_3 = -\epsilon_2$) | **Provisional assumption** | Mathematical convenience artifact in `SYMMETRICAL_UNBIASED` | Enforces exact cancellation; does not reflect physiological error correlation. |
| **Alternative Inter-Reading Correlation** | $\rho = 0.70$ (in `AUTOREGRESSIVE_AR1`) | **Awaiting empirical estimation from authorized reference data** | Short-interval repeat measurement literature (e.g., Stergiou 2018 reports $\rho \approx 0.65\text{--}0.80$) | Plausible physiological range, but specific correlation matrix awaits estimation from LASI Wave 1 microdata. |
| **Missing Reading Fallback Rule** | Disabled by default (`allow_fallback=False`) | **Awaiting empirical estimation from authorized reference data** | LASI Wave 1 methodological reports (IIPS) | Strict protocol mandates $\ge 2$ valid readings; official handling of single-reading respondents requires microdata inspection. |

> [!IMPORTANT]
> No parameters have been empirically fitted to LASI Wave 1 microdata, as genuine participant microdata remain inaccessible pending institutional data authorization.

---

## 4. Statistical Consequences of the Exact-Cancellation Assumption

### 4.1 Algebraic and Distributional Properties of the Baseline
In the baseline `SYMMETRICAL_UNBIASED` mode:
$$\text{Reading } 2 = \theta_i + \epsilon_i$$
$$\text{Reading } 3 = \theta_i - \epsilon_i$$
where $\theta_i$ is latent resting blood pressure and $\epsilon_i \sim \mathcal{N}(0, \sigma^2)$.

This structure entails four mathematical consequences:
1. **Sample Average Recovers Latent Truth Exactly:**
   $$\bar{Y}_i = \frac{Y_{i, 2} + Y_{i, 3}}{2} = \theta_i \quad \forall i$$
2. **Zero Residual Variance:**
   $$\text{Var}(\bar{Y}_i - \theta_i) = 0$$
3. **No Threshold Crossing for Final Values:**
   $$\mathbb{I}(\bar{Y}_i \ge 140) = \mathbb{I}(\theta_i \ge 140)$$
   Under this model, the measurement procedure can **never** cause a normotensive person to be classified as having elevated BP, nor can it cause a hypertensive person to be classified as normotensive.
4. **Implied Negative Correlation:**
   $$\text{Cov}(\epsilon_{i, 2}, \epsilon_{i, 3}) = \text{Cov}(\epsilon_i, -\epsilon_i) = -\sigma^2 \implies \rho(\epsilon_2, \epsilon_3) = -1.0$$
   In genuine human physiology, short-term blood pressure measurements taken 5 minutes apart exhibit **positive** autocorrelation ($\rho \in [0.60, 0.85]$), not perfect negative correlation.

### 4.2 Comparison with a General Correlated Measurement Model
In real-world epidemiological measurements, sequential readings follow an error structure:
$$Y_{i, k} = \theta_i + \delta_k + e_{i, k}, \quad k \in \{1, 2, 3\}$$
where $\delta_k$ is reading-specific bias ($\delta_1 > 0, \delta_2 \approx \delta_3 \approx 0$) and $\mathbf{e}_i = (e_{i, 1}, e_{i, 2}, e_{i, 3})^T \sim \mathcal{N}(\mathbf{0}, \boldsymbol{\Sigma})$.

For readings 2 and 3:
$$\boldsymbol{\Sigma}_{2, 3} = \begin{pmatrix} \sigma_2^2 & \rho \sigma_2 \sigma_3 \\ \rho \sigma_2 \sigma_3 & \sigma_3^2 \end{pmatrix}$$

Assuming homoscedastic resting error ($\sigma_2 = \sigma_3 = \sigma$):
$$\bar{Y}_i = \frac{Y_{i, 2} + Y_{i, 3}}{2} = \theta_i + \frac{e_{i, 2} + e_{i, 3}}{2}$$
The residual variance is:
$$\text{Var}(\bar{Y}_i - \theta_i) = \frac{\sigma^2 + \sigma^2 + 2\rho\sigma^2}{4} = \frac{\sigma^2(1 + \rho)}{2}$$

* **If $\rho = -1.0$ (Baseline):** $\text{Var} = \frac{\sigma^2(1 - 1)}{2} = 0.00$.
* **If $\rho = 0.00$ (Independent Gaussian):** $\text{Var} = \frac{\sigma^2}{2} = 1.62\text{ mmHg}^2$ (for $\sigma = 1.8$).
* **If $\rho = 0.70$ (Realistic Autoregressive):** $\text{Var} = \frac{1.8^2 (1 + 0.70)}{2} = 2.754\text{ mmHg}^2$.

### 4.3 Why the Baseline Model is Retained
1. **Preservation of Pre-Trained Calibration:** The baseline disease modules and latent ranges in `synapse-phase2` were calibrated to match target population prevalence ($40.11\%$). Injecting uncalibrated residual noise introduces random threshold crossings near $140/90\text{ mmHg}$, causing artificial prevalence drift.
2. **Defensible Granular Representation:** Individual readings exhibit realistic situational variance (reading 1 has alerting bias, readings 2 and 3 differ from each other), populating `community_bp_readings.csv` with realistic microdata.
3. **Scientific Soundness:** Rather than guessing an empirical covariance matrix without access to reference microdata, the baseline model makes a transparent, mathematically reproducible choice while isolating experimental models behind explicit flags.

---

## 5. Empirical Quantification of Measurement Effects

### 5.1 Experimental Setup
The entire synthetic cohort was regenerated using fixed master seed `42` ($N = 2,200$). Among these, 575 were older adults ($\text{Age} \ge 45$ at baseline), and **561** were alive and eligible at the community health survey reference date (`2024-06-29T00:00:00`, simulation day 180 of 720).

### 5.2 Blood Pressure Distributions Across Measurement Tiers
All 561 participants underwent 3 sequential readings. Distributions are presented below.

| Measurement Tier | SBP Mean ± SD (mmHg) | SBP Min – Max | DBP Mean ± SD (mmHg) | DBP Min – Max |
| :--- | :--- | :--- | :--- | :--- |
| **Latent Resting State** | $127.60 \pm 9.83$ | $110.0\text{ -- }149.5$ | $79.81 \pm 5.42$ | $70.1\text{ -- }92.8$ |
| **Reading 1 (Alerting)** | $131.09 \pm 9.84$ | $112.9\text{ -- }153.9$ | $81.33 \pm 5.44$ | $70.9\text{ -- }94.9$ |
| **Reading 2** | $127.54 \pm 9.96$ | $107.9\text{ -- }152.5$ | $79.74 \pm 5.51$ | $68.5\text{ -- }92.6$ |
| **Reading 3** | $127.66 \pm 10.04$ | $107.7\text{ -- }153.7$ | $79.88 \pm 5.54$ | $67.4\text{ -- }95.3$ |
| **Final Analysis Mean** | **$127.60 \pm 9.83$** | **$110.0\text{ -- }149.5$** | **$79.81 \pm 5.42$** | **$70.1\text{ -- }92.8$** |

### 5.3 Distributional Percentiles (SBP / DBP in mmHg)
| Percentile | Latent BP | Reading 1 | Reading 2 | Reading 3 | Final Analysis Mean |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Min** | 110.0 / 70.1 | 112.9 / 70.9 | 107.9 / 68.5 | 107.7 / 67.4 | 110.0 / 70.1 |
| **25th** | 120.5 / 75.9 | 123.8 / 77.4 | 120.4 / 75.6 | 119.7 / 76.0 | 120.5 / 75.9 |
| **Median** | 126.9 / 79.5 | 130.3 / 80.8 | 126.6 / 79.4 | 126.9 / 79.5 | 126.9 / 79.5 |
| **75th** | 133.3 / 83.4 | 136.9 / 84.8 | 133.3 / 83.2 | 133.8 / 83.4 | 133.3 / 83.4 |
| **Max** | 149.5 / 92.8 | 153.9 / 94.9 | 152.5 / 92.6 | 153.7 / 95.3 | 149.5 / 92.8 |

### 5.4 Within-Person Differences Between Readings
| Pairwise Comparison | SBP Difference (Mean ± SD) | SBP Min / Median / Max | DBP Difference (Mean ± SD) | DBP Min / Median / Max |
| :--- | :--- | :--- | :--- | :--- |
| **Reading 1 − Reading 2** | $+3.55 \pm 2.04\text{ mmHg}$ | $-2.3 / +3.5 / +8.9$ | $+1.59 \pm 1.15\text{ mmHg}$ | $-1.8 / +1.6 / +5.1$ |
| **Reading 1 − Reading 3** | $+3.43 \pm 1.98\text{ mmHg}$ | $-2.5 / +3.6 / +9.4$ | $+1.45 \pm 1.17\text{ mmHg}$ | $-2.4 / +1.5 / +4.6$ |
| **Reading 2 − Reading 3** | $-0.12 \pm 3.69\text{ mmHg}$ | $-10.0 / 0.0 / +10.0$ | $-0.14 \pm 2.20\text{ mmHg}$ | $-6.0 / 0.0 / +6.0$ |
| **Final − Latent State** | **$0.00 \pm 0.00\text{ mmHg}$** | **$0.0 / 0.0 / 0.0$** | **$0.00 \pm 0.00\text{ mmHg}$** | **$0.0 / 0.0 / 0.0$** |

### 5.5 Threshold Crossings and Prevalence Distortion
The standard clinical threshold for measured elevated blood pressure is $\text{SBP} \ge 140\text{ mmHg}$ or $\text{DBP} \ge 90\text{ mmHg}$.

| Metric | Latent Resting | Reading 1 (Alerting) | Reading 2 | Reading 3 | Final Protocol Mean |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Measured Elevated BP Count** | 97 | 124 | 90 | 102 | 97 |
| **False-Positive Crossers (vs Latent)** | 0 | 27 | 6 | 13 | **0** |
| **False-Negative Crossers (vs Latent)**| 0 | 0 | 13 | 8 | **0** |
| **Net Crossers (vs Latent)** | 0 | +27 | -7 | +5 | **0** |
| **Active Point-in-Time Medication ($Rx$)**| 217 | 217 | 217 | 217 | 217 |
| **Community HTN Prevalence ($N=561$)** | 40.11% (225) | 41.00% (230) | 39.75% (223) | 40.46% (227) | **40.11% (225)** |

#### Dissecting First-Reading Alerting vs. Averaging Effects:
1. **Alerting Effect Distortion:** If survey fieldworkers utilized only Reading 1, **27 additional individuals** would be classified as having elevated blood pressure due to acute white-coat reactivity. Among these 27, 5 were untreated, causing an artificial **+0.89 percentage point increase** in overall community hypertension prevalence ($41.00\%$ vs $40.11\%$).
2. **Averaging Protocol Protection:** By discarding Reading 1 and averaging Readings 2 and 3, all 27 white-coat crossers are correctly returned to their resting physiological classification.
3. **Symmetrical Averaging Cancellation:** Because $\epsilon_2 + \epsilon_3 = 0$, exactly zero participants cross the diagnostic threshold in the final derived value relative to their latent state.

### 5.6 Demographic and Clinical Stratifications
All statistics below are calculated on the reproduced seed-42 cohort ($N=561$).

| Stratum | Subgroup | Sample Size ($n$) | Active Rx | Elev BP Count | Final SBP (mmHg) | Final DBP (mmHg) | R1 SBP (mmHg) | HTN Prev (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Age Group** | 45–54 | 203 | 84 | 33 | $127.8 \pm 9.9$ | $79.6 \pm 5.5$ | $131.3 \pm 9.8$ | 42.36% (86) |
| | 55–64 | 209 | 76 | 35 | $127.4 \pm 9.9$ | $79.9 \pm 5.3$ | $130.9 \pm 10.0$ | 37.32% (78) |
| | 65–74 | 40 | 18 | 11 | $129.6 \pm 8.9$ | $80.5 \pm 5.2$ | $133.0 \pm 8.9$ | 47.50% (19) |
| | 75+ | 109 | 39 | 18 | $126.9 \pm 9.9$ | $79.8 \pm 5.4$ | $130.4 \pm 9.8$ | 38.53% (42) |
| **Sex** | Male | 295 | 114 | 50 | $127.5 \pm 9.8$ | $80.1 \pm 5.4$ | $131.0 \pm 9.9$ | 41.02% (121) |
| | Female | 266 | 103 | 47 | $127.7 \pm 9.9$ | $79.5 \pm 5.4$ | $131.2 \pm 9.8$ | 39.10% (104) |
| **Treatment** | Treated | 217 | 217 | 89 | $133.7 \pm 8.9$ | $83.4 \pm 5.0$ | $137.2 \pm 9.0$ | 100.0% (217) |
| | Untreated | 344 | 0 | 8 | $123.7 \pm 8.2$ | $77.6 \pm 4.3$ | $127.2 \pm 8.1$ | 2.33% (8) |

---

## 6. Review of Protocol Fidelity (LASI Wave 1)

The simulated measurement protocol was compared with official LASI documentation (IIPS 2017 Biomarker Manual).

### 6.1 Verified Protocol Dimensions
1. **Device:** Omron HEM-7121 digital automatic oscillometric blood pressure monitor.
2. **Readings Count:** Exactly 3 sequential readings per participant.
3. **Participant Rest:** Participant seated quietly with feet flat for $\ge 5$ minutes prior to the first reading.
4. **Reading Interval:** Approximately 5-minute pause between consecutive readings.
5. **Selection Rule:** Final analysis blood pressure is calculated as the arithmetic mean of Reading 2 and Reading 3.
6. **Exclusion of Reading 1:** Reading 1 is systematically omitted from primary survey analysis due to alerting reactivity.

### 6.2 Remaining Uncertainties and Provisional Rules
The following elements cannot be definitively verified without access to official IIPS analysis scripts and are explicitly designated **Provisional**:
* **Participant Refusal / Break-off:** The baseline model assumes 100% completion among eligible participants who are alive. Real-world survey break-off rates (~2–5%) require empirical estimation.
* **Incomplete Readings Handling:** If a participant has only 1 valid reading, standard LASI practice in certain research publications utilizes the single available reading, whereas strict clinical trial protocols exclude the participant. SYNAPSE defaults to strict exclusion (`allow_fallback=False`), but supports configurable fallback (`ALLOW_SINGLE_READING_FALLBACK`).
* **Cuff Size Adjustments:** LASI Wave 1 provided regular (22–32 cm) and large (32–42 cm) cuffs. Oscillometric mis-cuffing bias (under-cuffing elevating BP by 2–5 mmHg) is currently not modeled.

---

## 7. Alternative Measurement Model Assessment

To evaluate measurement error without exact cancellation, an experimental autoregressive model was formulated and implemented behind explicit configuration.

### 7.1 Mathematical Formulation of `AUTOREGRESSIVE_AR1`
Under `noise_mode = "AUTOREGRESSIVE_AR1"`:
1. **Reading 1 Error:**
   $$\epsilon_{i, 1} = \delta_{\text{alert}, i} + w_{i, 1}, \quad w_{i, 1} \sim \mathcal{N}(0, \sigma^2)$$
2. **Readings 2 and 3 Error (Stationary AR(1) Process):**
   $$\epsilon_{i, 2} \sim \mathcal{N}(0, \sigma^2)$$
   $$\epsilon_{i, 3} = \rho \cdot \epsilon_{i, 2} + \sqrt{1 - \rho^2} \cdot w_{i, 3}, \quad w_{i, 3} \sim \mathcal{N}(0, \sigma^2)$$
   where $\rho \in [0.0, 1.0)$ is the inter-reading correlation coefficient (default $\rho = 0.70$) and $\sigma = 1.8\text{ mmHg}$.

### 7.2 Empirical Comparison of Measurement Models (Seed 42, $N=561$)

| Model Configuration | Residual Variance $\text{Var}(\bar{Y} - \theta)$ | Threshold Crossers (Final vs Latent) | Community HTN Positives | Community HTN Prevalence |
| :--- | :--- | :--- | :--- | :--- |
| **`SYMMETRICAL_UNBIASED` (Baseline)** | **$0.00\text{ mmHg}^2$** | **0** | **225** | **40.11%** |
| **`INDEPENDENT_GAUSSIAN` ($\rho = 0$)** | $1.82\text{ mmHg}^2$ | 10 | 224 | 39.93% |
| **`AUTOREGRESSIVE_AR1` ($\rho = 0.70$)** | $3.24\text{ mmHg}^2$ | 14 | 224 | 39.93% |

### 7.3 Implementation vs. Deferral Decisions
* **Implemented:**
  - Added `AUTOREGRESSIVE_AR1` mode to `BpMeasurementProtocolSimulator`.
  - Added `inter_reading_correlation: float = 0.70` to `BpMeasurementProtocolConfig`.
  - Preserved `SYMMETRICAL_UNBIASED` as the default baseline.
* **Deferred:**
  - Replacing the default baseline model with `AUTOREGRESSIVE_AR1` is **deferred** until genuine LASI Wave 1 reference microdata are ingested. Calibrating $\rho$ or $\sigma$ without empirical reference data would violate scientific governance constraints against artificial parameter tuning.

---

## 8. Test Execution and Verification Results

The test suite was executed to verify protocol integrity, exact cancellation properties, autoregressive simulation, and gate preservation.

### 8.1 Targeted Tests Added (`tests/test_bp_measurement_protocol.py`)
1. **`test_symmetrical_unbiased_exact_cancellation_and_zero_residual_variance` (Test 19):** Validates that under `SYMMETRICAL_UNBIASED`, $\text{Var}(\text{SBP}_{\text{final}} - \text{SBP}_{\text{latent}}) == 0.0$ and $\text{Var}(\text{DBP}_{\text{final}} - \text{DBP}_{\text{latent}}) == 0.0$ across 500 patients.
2. **`test_autoregressive_ar1_correlation_and_residual_variance` (Test 20):** Validates that `AUTOREGRESSIVE_AR1` produces positive correlation ($\rho \approx 0.70$) between readings 2 and 3, and non-zero residual variance in the derived mean.
3. **`test_threshold_crossing_consistency_across_models` (Test 21):** Validates that baseline produces zero threshold crossers, while AR(1) produces non-zero crossers due to residual noise.
4. **`test_run_manifest_metadata_and_gate_preservation` (Test 22):** Validates that protocol configuration is recorded in the run manifest and the validation gate remains `REFERENCE_DATA_PENDING`.

### 8.2 Full Test Suite Results
```
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/shashi/synapse/synapse-phase2
plugins: Faker-40.43.0
collected 261 items

tests/test_bp_measurement_protocol.py .......................            [  8%]
tests/test_clinical_modules.py ......                                    [ 11%]
tests/test_community_assessment_audit.py .........................       [ 20%]
tests/test_data_integrity_temporal_consistency.py ...............        [ 26%]
tests/test_datagen.py ...                                                [ 27%]
tests/test_determinism.py ..........                                     [ 31%]
tests/test_dispatcher.py .                                               [ 31%]
tests/test_end_to_end_acceptance.py .                                    [ 32%]
tests/test_evaluation_framework.py ....................                  [ 39%]
tests/test_evaluation_mutations.py ......                                [ 42%]
tests/test_event_queue.py ...                                            [ 43%]
tests/test_full_simulation.py .                                          [ 43%]
tests/test_lab_rad_finance_rules.py ...                                  [ 44%]
tests/test_lasi_pipeline.py ..........................................   [ 60%]
tests/test_longitudinal_export.py ..                                     [ 61%]
tests/test_longitudinal_trajectories.py ....                             [ 63%]
tests/test_orchestrator.py ..                                            [ 63%]
tests/test_person_time_and_censoring.py .......                          [ 66%]
tests/test_phase2_csv_export.py ...                                      [ 67%]
tests/test_population_profile.py .....                                   [ 69%]
tests/test_population_validator.py .....                                 [ 71%]
tests/test_pubmed_datagen_integration.py ........                        [ 74%]
tests/test_pubmed_treatment_architecture.py ........                     [ 77%]
tests/test_root_cause_corrections.py ..........                          [ 81%]
tests/test_rule_engine.py ....                                           [ 83%]
tests/test_solid_principles.py .....                                     [ 85%]
tests/test_stage6_clock_scheduler.py ...                                 [ 86%]
tests/test_stage6_domain_events.py ..                                    [ 86%]
tests/test_stage6_loop_failure_protection.py ..                          [ 87%]
tests/test_stage6_ordering_causation.py ..                               [ 88%]
tests/test_stage6_reproducibility.py .                                   [ 88%]
tests/test_stage6_small_simulation.py .                                  [ 89%]
tests/test_stage7_cross_department.py .                                  [ 89%]
tests/test_stage7_patient_journeys.py .                                  [ 90%]
tests/test_stage7_scale.py .                                             [ 90%]
tests/test_stage7_workflows.py ..                                        [ 91%]
tests/test_stage9_billing.py .                                           [ 91%]
tests/test_stage9_diagnostics.py .                                       [ 91%]
tests/test_stage9_discharge.py .                                         [ 92%]
tests/test_stage9_integrity.py .                                         [ 92%]
tests/test_stage9_persistence.py ..                                      [ 93%]
tests/test_stage9_prescription.py .                                      [ 93%]
tests/test_state_machines.py .......                                     [ 96%]
tests/test_state_manager.py ....                                         [ 98%]
tests/test_validation_gate.py .....                                      [100%]

============================= 261 passed in 8.52s ==============================
```

---

## 9. Remaining Scientific Blockers and Gate Verdict

### 9.1 Remaining Blockers
1. **Institutional Access to LASI Wave 1 Microdata:** Acquisition and authorized ingestion of participant-level blood pressure microdata from IIPS/Gateway to Global Aging Data.
2. **Empirical Covariance Matrix Estimation:** Direct empirical estimation of $\text{Var}(\text{Reading}_1)$, $\text{Var}(\text{Reading}_2)$, $\text{Var}(\text{Reading}_3)$, and $\text{Corr}(\text{Reading}_j, \text{Reading}_k)$ in Indian older adults.
3. **Missingness Mechanism Calibration:** Official verification of survey non-response and single-reading fallback patterns in Wave 1.

### 9.2 External Validation Gate Verdict

```
================================================================================
EXTERNAL VALIDATION GATE STATUS: REFERENCE_DATA_PENDING
================================================================================
- Multi-reading BP measurement error model successfully audited and verified.
- Baseline exact cancellation model preserved with zero residual variance.
- Alternative AR(1) error model implemented behind explicit configuration.
- Operational community hypertension prevalence preserved at 40.11% (225 / 561).
- 261 / 261 tests passing.
- Gate remains strictly REFERENCE_DATA_PENDING until authorized microdata are ingested.
================================================================================
```
