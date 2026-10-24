# Scientific Audit: Latent Blood Pressure, Measurement Error, and Hypertension Classification

**Document ID:** `SYNAPSE-AUDIT-2026-LATENT-BP-PREVALENCE-03`  
**Classification:** Read-Only-First Scientific Audit & Causal Trace  
**Target Repository:** `synapse-phase2`  
**Primary Module:** [`synapse_simulator/datagen/bp_measurement.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/bp_measurement.py)  
**Related Modules:**  
- [`synapse_simulator/datagen/community_assessment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/community_assessment.py)  
- [`synapse_simulator/evaluation/experiment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/experiment.py)  
- [`synapse_simulator/evaluation/medication_status.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/medication_status.py)  
- [`synapse_simulator/evaluation/lasi/evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py)  
- [`synapse_simulator/datagen/patient_generator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/patient_generator.py)  
- [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml)  

**Evaluation Reference Date:** `2024-06-29T00:00:00` (Simulation Day 180 of 720)  
**External Validation Gate Status:** `REFERENCE_DATA_PENDING`  
**Reproducibility Seed:** `42` ($N = 2,200$; 561 assessed community older adults)  

---

## 1. Executive Summary

This read-only-first scientific audit investigates the end-to-end causal and computational pipeline connecting latent disease assignment, point-in-time treatment status, physiological blood pressure sampling, multi-reading measurement error, and composite community hypertension classification in SYNAPSE Phase 2.

### Key Audit Findings:
1. **Resolution of the AR(1) Variance Discrepancy:** The reported value of $3.24\text{ mmHg}^2$ in the previous audit's summary table is the **marginal error variance of a single reading** ($\sigma^2 = 1.8^2 = 3.24\text{ mmHg}^2$), not the residual variance of the mean of two readings. The theoretical variance of the mean under $\sigma = 1.8\text{ mmHg}$ and $\rho = 0.70$ is identically $\frac{\sigma^2(1 + \rho)}{2} = \mathbf{2.7540\text{ mmHg}^2}$. Across the 561 simulated cohort patients, the empirical sample variance is $\mathbf{2.7641\text{ mmHg}^2}$ (differing from theory by $< 0.37\%$, attributable to finite sampling and 1-decimal rounding).
2. **DBP Parameter Discrepancy (Code vs. Documentation):** In previous documentation, within-person DBP standard deviation was described as $0.9\text{ mmHg}$ (factor $0.5 \times \sigma_{\text{SBP}}$). However, the actual code in `bp_measurement.py` implements `within_visit_noise_sd * 0.6 = 1.08 mmHg` (factor $0.6$). This yields a theoretical single-reading variance of $1.1664\text{ mmHg}^2$ and an AR(1) mean residual variance of $0.9914\text{ mmHg}^2$ (empirical sample: $1.1515\text{ mmHg}^2$), compared to $0.6885\text{ mmHg}^2$ under the documented $0.9\text{ mmHg}$ factor.
3. **Causal Circularity in Latent BP Sampling:** Latent blood pressure is not an independent biological reference standard; it is sampled conditionally on assigned disease and treatment states ($[110, 135]$ for normotensives, $[120, 150]$ for treated hypertensives, $[145, 168]$ for untreated hypertensives). Thus, latent disease status mechanically forces blood pressure above or below diagnostic thresholds by construction.
4. **Post-Simulation Generation Look-Ahead:** `CommunityAssessmentGenerator.generate()` is executed after the full 720-day simulation terminates. It evaluates `has_htn = ("I10" in p.latent_conditions)` without filtering on `onset_time <= survey_date`. In the seed-42 cohort, 17 patients experienced incident hypertension in Year 2 (between days 181 and 720). Because their latent state at Day 720 contained `I10`, they were flagged as hypertensive at Day 180. Furthermore, 16 of them received treatment in Year 2 and were passed into the generator via `active_antihypertensive_pids` from the full run, causing their Day 180 BP to be drawn from the treated range $[120, 150]$. Eight of these patients sampled $< 140/90\text{ mmHg}$ and were subsequently classified normotensive at Day 180 because their prescription was not active at Day 180.
5. **Stratification Drivers:** The relatively flat hypertension prevalence across age bands (~37–48%) is caused by `patient_generator.py` applying a fixed conditional baseline rate ($50.1\%$ if diabetes, $28.2\%$ otherwise) to all adults $\ge 20$ without an age gradient. Small group sample variance is evident in the 65–74 age band ($n=40$).
6. **Test Suite Integrity:** Added 2 new deterministic regression tests (tests 23–24 in `tests/test_bp_measurement_protocol.py`), bringing the test suite to **263 passing tests** (100% pass rate).
7. **External Validation Gate:** Remains strictly **`REFERENCE_DATA_PENDING`**.

---

## 2. Complete Causal and Computational Trace

```mermaid
flowchart TD
    subgraph S1 [1. Population Initialization]
        PG[PatientProfileGenerator] -->|Demographics & SRS Mortality| P[PatientContext]
        PG -->|Baseline Sampling P HTN|T2D = 50.1%, no T2D = 28.2%| BC[baseline_conditions: I10]
    end

    subgraph S2 [2. Longitudinal Discrete-Event Simulation 720 Days]
        CMR[ClinicalModuleRunner: hypertension.yaml]
        P & BC --> CMR
        CMR -->|Annual AgeCheck rate 0.0344| IO[Incident Onset: latent_conditions I10]
        CMR -->|Delay 90d| SE[Screening Encounter]
        SE -->|Record BP & Care Plan| Rx[Prescribe Amlodipine 5mg: pharmacy.prescriptions]
        Rx -->|Delay 180d| FU[Follow-Up Encounter]
    end

    subgraph S3 [3. Survey Execution: Day 180 Sweep]
        CAG[CommunityAssessmentGenerator]
        P & CMR --> CAG
        CAG -->|Evaluate has_htn at Day 720 post-sim| DH[Latent HTN Status]
        CAG -->|Treated: 120-150 / Untreated: 145-168 / Normo: 110-135| LBP[Latent Resting BP SBP/DBP]
        LBP --> BMS[BpMeasurementProtocolSimulator]
        BMS -->|Reading 1: + Alerting Shift| R1[Reading 1]
        BMS -->|Readings 2 & 3: Within-visit Noise| R23[Readings 2 and 3]
        R23 -->|Arithmetic Average| FBP[Final Analysis Value]
    end

    subgraph S4 [4. Downstream External Evaluation: Day 180]
        FBP --> EVAL[LasiExternalEvaluator]
        Rx -->|is_prescription_active_at <= Day 180| PIT[Point-in-Time Rx Status]
        FBP & PIT -->|Elevated BP >= 140/90 OR Active Rx| CHTN[Composite Community HTN Prevalence: 40.11%]
    end
```

### 2.1 Detailed Computational Steps
1. **Latent Hypertension Assignment:**
   - *Baseline:* In `synapse_simulator/datagen/patient_generator.py` (lines 117–136), each patient aged $\ge 20$ is evaluated. If diabetes is present, $P(\text{HTN}\mid\text{T2D}) = 50.1\%$; otherwise $P(\text{HTN}\mid\text{no T2D}) = 28.2\%$. Baseline-positive patients receive `"I10"` in `patient.baseline_conditions`.
   - *Incident:* Patients without baseline hypertension transition from `Initial` to `AgeCheck` in `config/modules/hypertension.yaml`. At each 365-day interval, patients transition to `HypertensionOnset` with fixed probability $0.0344$, populating `patient.latent_conditions["I10"]`.
2. **Point-in-Time Antihypertensive Treatment Determination:**
   - Evaluated by `is_prescription_active_at()` in `synapse_simulator/evaluation/medication_status.py`.
   - Requires prescription drug name to contain target keywords (`amlodipine`, `telmisartan`, etc.), `start_time <= reference_time` (`2024-06-29T00:00:00`), and no discontinuation prior to the reference timestamp.
3. **Latent Blood Pressure Sampling:**
   - In `synapse_simulator/datagen/community_assessment.py` (lines 165–174):
     $$\text{SBP}_{\text{latent}} \sim \begin{cases} \mathcal{U}(120.0, 150.0), & \text{if } \text{has\_htn} \wedge \text{is\_treated} \\ \mathcal{U}(145.0, 168.0), & \text{if } \text{has\_htn} \wedge \neg\text{is\_treated} \\ \mathcal{U}(110.0, 135.0), & \text{if } \neg\text{has\_htn} \end{cases}$$
     $$\text{DBP}_{\text{latent}} \sim \begin{cases} \mathcal{U}(75.0, 92.0), & \text{if } \text{has\_htn} \wedge \text{is\_treated} \\ \mathcal{U}(90.0, 104.0), & \text{if } \text{has\_htn} \wedge \neg\text{is\_treated} \\ \mathcal{U}(70.0, 84.0), & \text{if } \neg\text{has\_htn} \end{cases}$$
   - Bounded by physiological safeguard $\text{PP} = \text{SBP} - \text{DBP} \ge 20.0\text{ mmHg}$.
4. **Sequential Reading Generation:**
   - In `synapse_simulator/datagen/bp_measurement.py`: Reading 1 adds alerting response $\mathcal{N}(3.5, 0.4^2)$ / $\mathcal{N}(1.5, 0.4^2)$. Readings 2 and 3 add within-visit error according to the configured `noise_mode`.
5. **Final Analysis BP Estimation:**
   - Calculated as the independent arithmetic average of readings 2 and 3: $\text{SBP}_{\text{final}} = (\text{SBP}_2 + \text{SBP}_3)/2$ and $\text{DBP}_{\text{final}} = (\text{DBP}_2 + \text{DBP}_3)/2$.
6. **Elevated Measured BP Classification:**
   - Binary indicator: $\mathbb{I}(\text{SBP}_{\text{final}} \ge 140.0 \vee \text{DBP}_{\text{final}} \ge 90.0)$.
7. **Composite Community Hypertension Classification:**
   - Evaluated in `evaluator.py` (lines 1154–1174):
     $$\text{Community HTN Positive} \iff (\text{SBP}_{\text{final}} \ge 140.0) \vee (\text{DBP}_{\text{final}} \ge 90.0) \vee (\text{Active Rx at Day 180})$$
8. **Prevalence Denominators & Confidence Intervals:**
   - Denominator: Assessed older adults ($\text{Age} \ge 45$, alive at Day 180, survey completed).
   - Confidence Interval: Wilson score binomial interval without continuity correction.

### 2.2 Circularity and Independence Analysis
* **Generative Circularity:** The measurement generator samples blood pressure from ranges that are *partitioned by the disease classification*. Normotensive latent SBP cannot exceed 135 mmHg; untreated hypertensive latent SBP cannot fall below 145 mmHg. Consequently, measured BP in the simulation does not function as an independent biomarker; it is an algebraic consequence of the latent disease state.
* **Prescription vs. Adherence:** The model assumes 100% medication possession and adherence. Every patient reaching `PrescribeAntihypertensive` has active medication in perpetuity until follow-up (no non-compliance or loss to follow-up).

---

## 3. Reconciliation of the AR(1) Variance Discrepancy

### 3.1 Mathematical Derivation
Let $Y_{i, 2} = \theta_i + e_{i, 2}$ and $Y_{i, 3} = \theta_i + e_{i, 3}$ be sequential seated blood pressure readings taken on patient $i$, where $\theta_i$ is latent resting blood pressure and $\mathbf{e}_i = (e_{i, 2}, e_{i, 3})^T$ is a bivariate normal error vector with marginal variance $\text{Var}(e_{i, 2}) = \text{Var}(e_{i, 3}) = \sigma^2$ and Pearson correlation $\text{Corr}(e_{i, 2}, e_{i, 3}) = \rho$.

The final analysis measurement is:
$$\bar{Y}_i = \frac{Y_{i, 2} + Y_{i, 3}}{2} = \theta_i + \bar{e}_i, \quad \text{where } \bar{e}_i = \frac{e_{i, 2} + e_{i, 3}}{2}$$

The residual measurement variance relative to the latent state is:
$$\text{Var}(\bar{Y}_i - \theta_i) = \text{Var}(\bar{e}_i) = \text{Var}\left(\frac{e_{i, 2} + e_{i, 3}}{2}\right) = \frac{\text{Var}(e_{i, 2}) + \text{Var}(e_{i, 3}) + 2\text{Cov}(e_{i, 2}, e_{i, 3})}{4}$$
$$\text{Var}(\bar{e}_i) = \frac{\sigma^2 + \sigma^2 + 2\rho\sigma^2}{4} = \frac{2\sigma^2(1 + \rho)}{4} = \frac{\sigma^2(1 + \rho)}{2}$$

### 3.2 SBP Parameter Reconciliation
For SBP with within-visit standard deviation $\sigma = 1.8\text{ mmHg}$ and $\rho = 0.70$:
1. **Marginal Variance of a Single Reading:**
   $$\sigma^2 = 1.8^2 = \mathbf{3.24\text{ mmHg}^2}$$
2. **Theoretical Variance of the Mean of Two Correlated Readings:**
   $$\text{Var}(\bar{e}_{\text{SBP}}) = \frac{3.24 \times (1 + 0.70)}{2} = \frac{3.24 \times 1.70}{2} = \mathbf{2.7540\text{ mmHg}^2}$$
3. **Empirical Variance in Seed-42 Cohort ($N = 561$):**
   $$\widehat{\text{Var}}(\bar{e}_{\text{SBP}}) = \mathbf{2.7641\text{ mmHg}^2}$$

**Root Cause of the Previous Discrepancy:**
The value $3.24\text{ mmHg}^2$ reported in Table 7.2 of `docs/research_alignment/bp_measurement_error_model_audit.md` was a transcription of the single-reading marginal error variance $\sigma^2 = 1.8^2 = 3.24$, mistakenly inserted into the summary table column labeled $\text{Var}(\bar{Y} - \theta)$, despite the correct formula ($2.754$) having been derived in Section 4.2 of that same document.

### 3.3 DBP Parameter Reconciliation
For DBP, the audit revealed a divergence between documentation and codebase implementation:
* **Implemented Code:** In `bp_measurement.py` (lines 465, 479, 495), the code implements:
  $$\sigma_{\text{DBP}} = \sigma_{\text{SBP}} \times 0.6 = 1.8 \times 0.6 = 1.08\text{ mmHg}$$
  $$\sigma_{\text{DBP}}^2 = 1.08^2 = 1.1664\text{ mmHg}^2$$
  $$\text{Theoretical } \text{Var}(\bar{e}_{\text{DBP}}) = \frac{1.1664 \times 1.70}{2} = \mathbf{0.9914\text{ mmHg}^2}$$
  $$\text{Empirical Cohort } \widehat{\text{Var}}(\bar{e}_{\text{DBP}}) = \mathbf{1.1515\text{ mmHg}^2}$$
* **Documentation Prior:** Earlier documentation stated $\sigma_{\text{DBP}} = 0.9\text{ mmHg}$ (factor $0.5$):
  $$\text{Theoretical } \text{Var}(\bar{e}_{\text{DBP, text}}) = \frac{0.9^2 \times 1.70}{2} = \frac{0.81 \times 1.70}{2} = \mathbf{0.6885\text{ mmHg}^2}$$

---

## 4. Outcome Definitions and Denominator Reconciliation

All metrics evaluated on Seed 42 ($N = 2,200$, 561 assessed older adults aged $\ge 45$ alive at Day 180).

### 4.1 Cross-Sectional Outcome Classifications

| Classification Concept | Operational Definition | Numerator ($n$) | Denominator ($N$) | Prevalence (%) | 95% Wilson CI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Point-in-Time Latent HTN** | Baseline HTN or incident onset $\le$ 2024-06-29 | 217 | 561 | 38.68% | [34.74%, 42.77%] |
| **Full-Run Ever-Hypertensive**| Baseline HTN or incident onset $\le$ 720 days | 234 | 561 | 41.71% | [37.69%, 45.85%] |
| **Historical EHR Diagnosis** | `I10` in consultations with encounter $\le$ 2024-06-29 | 217 | 561 | 38.68% | [34.74%, 42.77%] |
| **Full-Run EHR Diagnosis** | `I10` in consultations at any point in 720 days | 233 | 561 | 41.53% | [37.52%, 45.67%] |
| **Point-in-Time Active Rx** | Valid antihypertensive prescription active on 2024-06-29 | 217 | 561 | 38.68% | [34.74%, 42.77%] |
| **Elevated Measured BP (Baseline)**| Derived final SBP $\ge 140$ or DBP $\ge 90$ (`SYMMETRICAL`) | 97 | 561 | 17.29% | [14.36%, 20.66%] |
| **Composite Community HTN** | Elevated Measured BP $\ge 140/90 \vee$ Active Rx at Day 180 | 225 | 561 | 40.11% | [36.12%, 44.24%] |

### 4.2 Overlap and Concordance Breakdown
* **Elevated BP AND Active Rx:** 89 patients (treated uncontrolled hypertension).
* **Active Rx ONLY (Controlled):** 128 patients (treated controlled hypertension, final SBP $< 140$ and DBP $< 90$).
* **Elevated BP ONLY (Untreated):** 8 patients (7 future incident cases whose treatment begins in Year 2 + 1 future incident case who died before treatment).
* **Composite Community HTN Numerator:** $128 \text{ (controlled Rx)} + 89 \text{ (uncontrolled Rx)} + 8 \text{ (untreated elevated)} = \mathbf{225}$.
* **Discordance with Point-in-Time Latent HTN:**
  - Latent HTN at Day 180: 217.
  - Composite Community HTN: 225.
  - Net difference: **+8 patients**. All 8 discordant patients are individuals who were normotensive at Day 180, but because the community generator was executed post-simulation, their BP was drawn from the hypertensive range, causing false-positive elevation on Day 180.

### 4.3 Sensitivity Across Measurement Error Models

| Metric | `SYMMETRICAL_UNBIASED` (Baseline) | `INDEPENDENT_GAUSSIAN` ($\rho = 0.0$) | `AUTOREGRESSIVE_AR1` ($\rho = 0.70$) |
| :--- | :--- | :--- | :--- |
| **Residual Error Variance $\text{Var}(\bar{Y} - \theta)$** | $0.0000\text{ mmHg}^2$ | $1.6851\text{ mmHg}^2$ | $2.7641\text{ mmHg}^2$ |
| **Final Elevated BP Count ($\ge 140/90$)** | 97 (17.29%) | 100 (17.83%) | 101 (18.00%) |
| **Threshold Crossers (Final vs. Latent)** | **0** | 17 (10 false +, 7 false -) | 18 (11 false +, 7 false -) |
| **Composite Community HTN Numerator** | **225 (40.11%)** | **227 (40.46%)** | **227 (40.46%)** |
| **Difference from Baseline Prevalence** | 0.00 pp | +0.35 pp (+2 patients) | +0.35 pp (+2 patients) |

---

## 5. Age and Sex Stratified Findings

All statistics calculated on the 561 assessed older adults in the seed-42 cohort.

### 5.1 Stratification Summary Table

| Stratum | Group | Denominator ($n$) | Small Group Flag ($n < 50$) | Point-in-Time Active Rx | Measured Elev BP | Composite HTN Pos | Prevalence (%) [95% CI] | Mean Final SBP (mmHg) | Mean Final DBP (mmHg) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Age** | 45–54 | 203 | False | 84 | 33 | 86 | 42.36% [35.75%, 49.26%] | $127.8 \pm 9.9$ | $79.6 \pm 5.5$ |
| | 55–64 | 209 | False | 76 | 35 | 78 | 37.32% [31.00%, 44.09%] | $127.4 \pm 9.9$ | $79.9 \pm 5.3$ |
| | 65–74 | 40 | **True ($n=40$)** | 18 | 11 | 19 | 47.50% [32.88%, 62.58%] | $129.6 \pm 8.9$ | $80.5 \pm 5.2$ |
| | 75+ | 109 | False | 39 | 18 | 42 | 38.53% [29.83%, 48.04%] | $126.9 \pm 9.9$ | $79.8 \pm 5.4$ |
| **Sex** | Male | 295 | False | 114 | 50 | 121 | 41.02% [35.53%, 46.74%] | $127.5 \pm 9.8$ | $80.1 \pm 5.4$ |
| | Female | 266 | False | 103 | 47 | 104 | 39.10% [33.40%, 45.12%] | $127.7 \pm 9.9$ | $79.5 \pm 5.4$ |

### 5.2 Analysis of Stratification Drivers
1. **Absence of Real-World Age Gradient:** In real-world Indian surveys (LASI Wave 1), hypertension prevalence increases monotonically from ~35% at age 45–54 to $>60\%$ at age 75+. In the synthetic cohort, prevalence remains flat between 37% and 48%. This is directly driven by `patient_generator.py`:
   - It assigns baseline hypertension using fixed rates ($50.1\%$ if diabetes, $28.2\%$ if not) for all ages $\ge 20$.
   - The disease module transitions from `AgeCheck` with a constant hazard ($0.0344$/year) regardless of age band.
2. **Small-Group Variance:** The 65–74 age band contains only **40 patients** ($7.1\%$ of the assessed cohort). In a sample of $n=40$, each individual patient alters prevalence by $2.5$ percentage points. The observed prevalence of $47.50\%$ ($19/40$) is well within the 95% confidence interval $[32.88\%, 62.58\%]$ and reflects small-sample binomial noise rather than a biological peak.
3. **Sex Invariance:** Male and female prevalence are nearly identical ($41.02\%$ vs. $39.10\%$, difference $1.92$ pp). The demographic sampler applies identical conditional baseline probabilities, and the clinical module specifies sex-invariant disease transition rates.

---

## 6. Scientific Assumptions and Parameter Provenance

| Parameter | Implemented Value | Code Location | Evidence Source | Direct Population Support | Status Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Measurement Monitor** | Omron HEM-7121 digital oscillometric | `bp_measurement.py:95` | LASI Wave 1 Fieldwork Manual (IIPS 2017) | Yes (direct reference standard) | **Supported by directly applicable source** |
| **Measurement Schedule** | 3 seated readings, 5-min intervals | `bp_measurement.py:97-101` | LASI Biomarker Protocol | Yes (direct reference standard) | **Supported by directly applicable source** |
| **Reading Selection Rule** | Mean of readings 2 & 3; discard reading 1 | `bp_measurement.py:98` | LASI Analysis Protocol | Yes (direct reference standard) | **Supported by directly applicable source** |
| **First-Reading Alerting Shift (SBP)**| $\mu = 3.5\text{ mmHg}, \sigma = 0.4\text{ mmHg}$ | `bp_measurement.py:109, 459` | White-coat literature (Stergiou 2018) | No (general adult literature prior) | **Extrapolated** |
| **First-Reading Alerting Shift (DBP)**| $\mu = 1.5\text{ mmHg}, \sigma = 0.4\text{ mmHg}$ | `bp_measurement.py:110, 460` | White-coat literature | No (general adult literature prior) | **Extrapolated** |
| **Within-Visit SBP Noise SD** | $\sigma_{\text{within}} = 1.8\text{ mmHg}$ | `bp_measurement.py:111, 464` | Internal conservative heuristic | No (uncalibrated) | **Provisional assumption** |
| **Within-Visit DBP Noise SD** | $\sigma = 1.8 \times 0.6 = 1.08\text{ mmHg}$ | `bp_measurement.py:465, 479` | Internal heuristic (differs from text $0.9$) | No (uncalibrated) | **Provisional assumption** |
| **Baseline Correlation** | $\rho = -1.0$ (equal and opposite) | `bp_measurement.py:470-471` | Mathematical artifact for zero residual error | No (synthetic convenience) | **Provisional computational baseline** |
| **AR(1) Correlation** | $\rho = 0.70$ | `bp_measurement.py:149, 473` | Repeat oscillometric studies (Stergiou 2018)| No (general adult literature prior) | **Awaiting empirical estimation** |
| **Missing Reading Fallback**| Disabled (`allow_fallback=False`) | `bp_measurement.py:100` | Strict protocol | No (IIPS imputation unverified) | **Awaiting empirical estimation** |

---

## 7. Limitations and Unresolved Assumptions

1. **Post-Simulation Sweep Leakage:** As demonstrated in Section 2, generating community assessments after the 720-day simulation terminates allows Year 2 incident cases ($17$ patients) and Year 2 prescriptions ($16$ patients) to influence Day 180 blood pressure sampling.
2. **Deterministic Adherence:** Real-world medication adherence among Indian older adults is approximately $50\text{--}65\%$. In SYNAPSE Phase 2, every diagnosed patient is prescribed medication and maintains 100% adherence.
3. **Flat Baseline Age Profile:** Baseline hypertension prevalence is sampled without age-specific weighting above age 20, preventing the emergence of a realistic steep age gradient.
4. **Uncalibrated Covariance Matrix:** While `AUTOREGRESSIVE_AR1` provides a biologically plausible alternative to exact error cancellation, its parameters ($\rho = 0.70, \sigma = 1.8\text{ mmHg}$) represent literature priors rather than empirical estimates from Indian older adults.

---

## 8. Test Execution and Verification

Two deterministic unit tests were added to [`tests/test_bp_measurement_protocol.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_bp_measurement_protocol.py):
* `test_ar1_theoretical_variance_formula` (Test 23): Verifies the exact theoretical residual variance formula $\text{Var}(\bar{e}) = \sigma^2(1 + \rho)/2 = 2.7540$ and single-reading variance $\sigma^2 = 3.24$, cementing the mathematical resolution of the discrepancy.
* `test_point_in_time_vs_full_run_prevalence_invariants` (Test 24): Verifies the point-in-time medication boundary condition distinguishing Day 180 prescriptions from Year 2 future prescriptions.

### Test Execution Command:
```bash
.venv/bin/pytest
```

### Actual Output:
```
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/shashi/synapse/synapse-phase2
plugins: Faker-40.43.0
collected 263 items

tests/test_bp_measurement_protocol.py .........................          [  9%]
tests/test_clinical_modules.py ......                                    [ 11%]
tests/test_community_assessment_audit.py .........................       [ 21%]
tests/test_data_integrity_temporal_consistency.py ...............        [ 26%]
tests/test_datagen.py ...                                                [ 28%]
tests/test_determinism.py ..........                                     [ 31%]
tests/test_dispatcher.py .                                               [ 32%]
tests/test_end_to_end_acceptance.py .                                    [ 32%]
tests/test_evaluation_framework.py ....................                  [ 40%]
tests/test_evaluation_mutations.py ......                                [ 42%]
tests/test_event_queue.py ...                                            [ 43%]
tests/test_full_simulation.py .                                          [ 44%]
tests/test_lab_rad_finance_rules.py ...                                  [ 45%]
tests/test_lasi_pipeline.py ..........................................   [ 61%]
tests/test_longitudinal_export.py ..                                     [ 61%]
tests/test_longitudinal_trajectories.py ....                             [ 63%]
tests/test_orchestrator.py ..                                            [ 64%]
tests/test_person_time_and_censoring.py .......                          [ 66%]
tests/test_phase2_csv_export.py ...                                      [ 68%]
tests/test_population_profile.py .....                                   [ 69%]
tests/test_population_validator.py .....                                 [ 71%]
tests/test_pubmed_datagen_integration.py ........                        [ 74%]
tests/test_pubmed_treatment_architecture.py ........                     [ 77%]
tests/test_root_cause_corrections.py ..........                          [ 81%]
tests/test_rule_engine.py ....                                           [ 83%]
tests/test_solid_principles.py .....                                     [ 85%]
tests/test_stage6_clock_scheduler.py ...                                 [ 86%]
tests/test_stage6_domain_events.py ..                                    [ 87%]
tests/test_stage6_loop_failure_protection.py ..                          [ 87%]
tests/test_stage6_ordering_causation.py ..                               [ 88%]
tests/test_stage6_reproducibility.py .                                   [ 88%]
tests/test_stage6_small_simulation.py .                                  [ 89%]
tests/test_stage7_cross_department.py .                                  [ 89%]
tests/test_stage7_patient_journeys.py .                                  [ 90%]
tests/test_stage7_scale.py .                                             [ 90%]
tests/test_stage7_workflows.py ..                                        [ 91%]
tests/test_stage9_billing.py .                                           [ 91%]
tests/test_stage9_diagnostics.py .                                       [ 92%]
tests/test_stage9_discharge.py .                                         [ 92%]
tests/test_stage9_integrity.py .                                         [ 92%]
tests/test_stage9_persistence.py ..                                      [ 93%]
tests/test_stage9_prescription.py .                                      [ 93%]
tests/test_state_machines.py .......                                     [ 96%]
tests/test_state_manager.py ....                                         [ 98%]
tests/test_validation_gate.py .....                                      [100%]

============================= 263 passed in 8.97s ==============================
```

---

## 9. External Validation Gate Verdict

```
================================================================================
EXTERNAL VALIDATION GATE STATUS: REFERENCE_DATA_PENDING
================================================================================
- Causal and computational dependency paths fully traced and documented.
- AR(1) variance discrepancy resolved: 3.24 is marginal sigma^2, theoretical
  variance of mean is 2.7540 mmHg^2, empirical cohort variance is 2.7641 mmHg^2.
- Generative circularity and post-simulation look-ahead mechanisms identified.
- Outcome definitions and denominators rigorously separated across 5 concepts.
- 263 / 263 tests passing.
- Gate remains strictly REFERENCE_DATA_PENDING until credentialed LASI Wave 1
  reference microdata are authorized, ingested, and validated.
================================================================================
```
