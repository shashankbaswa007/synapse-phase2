# Scientific Audit: Latent Blood Pressure Generation, Circularity, and Clinical Realism

**Document ID:** `SYNAPSE-AUDIT-2026-LATENT-BP-REALISM-01`  
**Classification:** Scientific Audit, Causal Trace, and Construct Validity Review  
**Target Repository:** `synapse-phase2`  
**Primary Modules:**  
- [`synapse_simulator/datagen/bp_measurement.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/bp_measurement.py)  
- [`synapse_simulator/datagen/community_assessment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/community_assessment.py)  
- [`synapse_simulator/evaluation/experiment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/experiment.py)  
- [`synapse_simulator/evaluation/medication_status.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/medication_status.py)  
- [`synapse_simulator/datagen/patient_generator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/patient_generator.py)  
- [`synapse_simulator/population/loader.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/population/loader.py)  
- [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml)  

**Evaluation Reference Date:** `2024-06-29T00:00:00` (Simulation Day 180 of 720)  
**External Validation Gate Status:** `REFERENCE_DATA_PENDING`  
**Reproducibility Seed:** `42` ($N = 2,200$; 561 assessed community older adults)  
**Test Suite Verification:** 273 passed, 0 failed in 8.64s (`.venv/bin/pytest`)  

---

## 1. Executive Summary

Following the remediation of temporal look-ahead leakage in the Day 180 community assessment pipeline, this audit examines the foundational physiological and statistical assumptions governing latent blood pressure (BP) generation. Specifically, it audits whether the latent resting systolic blood pressure (SBP) and diastolic blood pressure (DBP) sampling distributions produce clinically defensible representations of human hemodynamics, or whether they mechanically enforce hypertension status and treatment response by construction.

### Key Audit Findings:

1. **Inverted Causal Architecture (Construct Circularity):**  
   In clinical medicine and epidemiology, hypertension is a diagnostic construct derived from observed blood pressure measurements ($\text{SBP} \ge 140\text{ mmHg}$ or $\text{DBP} \ge 90\text{ mmHg}$) and current medication use. In SYNAPSE Phase 2, the causal order is reversed:
   $$\text{Disease Assignment (I10)} \longrightarrow \text{Treatment (Rx)} \longrightarrow \text{Conditional Latent BP Draw} \longrightarrow \text{Observed Readings} \longrightarrow \text{Community Classification}$$
   Because latent blood pressure is drawn conditionally from compartmentalized uniform ranges selected by pre-existing disease and treatment labels, agreement between measured BP and latent hypertension does not reflect real-world diagnostic performance; it is a mechanical mathematical consequence of the sampling bounds.

2. **Physiological Gaps and Hard Discontinuities in Untreated States:**  
   Untreated normotensive individuals draw SBP uniformly from $[110.0, 135.0]\text{ mmHg}$ and DBP from $[70.0, 84.0]\text{ mmHg}$. Untreated hypertensive individuals draw SBP from $[145.0, 168.0]\text{ mmHg}$ and DBP from $[90.0, 104.0]\text{ mmHg}$. This introduces an unnatural **$10\text{ mmHg}$ void** ($135.1$ to $144.9\text{ mmHg}$) and a **$6\text{ mmHg}$ void** ($84.1$ to $89.9\text{ mmHg}$) where no untreated individual can ever exist. Consequently, untreated specificity is mechanically $100\%$ ($FP = 0$) and untreated sensitivity is mechanically $100\%$ ($FN = 0$) by design.

3. **Absence of Demographic Gradients in Latent BP:**  
   Across four older-adult age bands (45–54, 55–64, 65–74, 75+), mean SBP ($126.2$ to $129.0\text{ mmHg}$) and hypertension prevalence ($35.8\%$ to $45.0\%$) remain structurally flat. This occurs because:
   - `patient_generator.py` assigns baseline hypertension using a flat rate ($50.1\%$ if diabetes, $28.2\%$ otherwise) to all adults $\ge 20$ without age-dependent scaling.
   - `hypertension.yaml` applies a constant annual transition rate of $0.0344$ to all adults $\ge 20$.
   - `community_assessment.py` applies identical sampling ranges across all ages and sexes, omitting vascular stiffening and isolated systolic hypertension.

4. **Measurement Error Realism:**  
   The primary measurement error mode, `SYMMETRICAL_UNBIASED`, forces exact error cancellation ($\Delta_2 = +\epsilon, \Delta_3 = -\epsilon$), such that the protocol analysis mean of readings 2 and 3 equals the latent draw exactly ($\operatorname{Var}_{\text{error}} \equiv 0$). The realistic stochastic alternatives `INDEPENDENT_GAUSSIAN` ($\operatorname{Var} = 1.62\text{ mmHg}^2$) and `AUTOREGRESSIVE_AR1` ($\operatorname{Var} = 2.7540\text{ mmHg}^2$) are fully supported but currently non-default.

5. **Scientific Posture and Gate Preservation:**  
   No clinical parameters have been altered to force alignment with external prevalence targets. The external validation gate remains strictly **`REFERENCE_DATA_PENDING`**.

---

## 2. Exact Code Paths and Parameter Values

### 2.1 Latent BP Sampling Implementation
In [`synapse_simulator/datagen/community_assessment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/community_assessment.py) (lines 240–262):

```python
# 4. Underlying latent physiological health status at assessment date
has_htn = is_condition_active_at(p, "I10", self.config.assessment_date)
is_treated = pid in active_rx

# 5. Measure vital signs based on established medical knowledge ranges
if has_htn:
    if is_treated:
        underlying_sbp = round(pat_rng.uniform(120.0, 150.0), 1)
        underlying_dbp = round(pat_rng.uniform(75.0, 92.0), 1)
    else:
        underlying_sbp = round(pat_rng.uniform(145.0, 168.0), 1)
        underlying_dbp = round(pat_rng.uniform(90.0, 104.0), 1)
else:
    underlying_sbp = round(pat_rng.uniform(110.0, 135.0), 1)
    underlying_dbp = round(pat_rng.uniform(70.0, 84.0), 1)

# Physiological safeguard: pulse pressure (PP = SBP - DBP) must be >= 20 mmHg
if underlying_sbp - underlying_dbp < 20.0:
    underlying_sbp = round(underlying_dbp + 25.0, 1)
```

### 2.2 Verified Parameter Values vs. Documentation

| Health State Category | Implemented SBP Range | Implemented DBP Range | Theoretical Mean (SBP / DBP) | Theoretical $\sigma$ (SBP / DBP) | Provenance in Code Comments |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normotensive** | $[110.0, 135.0]\text{ mmHg}$ | $[70.0, 84.0]\text{ mmHg}$ | $122.5\text{ mmHg}$ / $77.0\text{ mmHg}$ | $7.22\text{ mmHg}$ / $4.04\text{ mmHg}$ | "Adult/elderly knowledge base" |
| **Treated Hypertensive** | $[120.0, 150.0]\text{ mmHg}$ | $[75.0, 92.0]\text{ mmHg}$ | $135.0\text{ mmHg}$ / $83.5\text{ mmHg}$ | $8.66\text{ mmHg}$ / $4.91\text{ mmHg}$ | "Follow-up module range" |
| **Untreated Hypertensive** | $[145.0, 168.0]\text{ mmHg}$ | $[90.0, 104.0]\text{ mmHg}$ | $156.5\text{ mmHg}$ / $97.0\text{ mmHg}$ | $6.64\text{ mmHg}$ / $4.04\text{ mmHg}$ | "Screening module range" |
| **Pulse Pressure Safeguard** | $\text{PP} < 20.0\text{ mmHg}$ | $\text{SBP} \gets \text{DBP} + 25.0$ | $\text{PP} \ge 20.0\text{ mmHg}$ | — | Physiological hemodynamics guard |

### 2.3 Verification of the Eight Specification Points

1. **Hypertension Status Assignment:** Assigned via `is_condition_active_at(p, "I10", self.config.assessment_date)` in `community_assessment.py`. Checks baseline conditions, chronic conditions, and latent condition `onset_time <= assessment_date` and `resolved_time > assessment_date`.
2. **Treatment Status Assignment:** Assigned via `is_prescription_active_at(rx, assessment_date, encounter=enc)` in `medication_status.py`. Evaluates drug keyword matching, prescription/encounter start time $\le \text{assessment\_date}$, and no prior discontinuation or expiration.
3. **Distribution Selection:** Selected conditionally using **both** disease status (`has_htn`) and treatment status (`is_treated`).
4. **Temporal Reference of Treatment:** Correctly evaluated at the exact assessment timestamp (`2024-06-29T00:00:00` for Day 180).
5. **Direction of Influence:** Generated community BP influences composite community hypertension classification ($\text{SBP} \ge 140$ or $\text{DBP} \ge 90$). It **never** influences clinical EHR encounters, hospital diagnoses, or prescriptions (strict separation of layers).
6. **Latent State Persistence:** Inside a single assessment sweep, a single `underlying_sbp` and `underlying_dbp` pair is sampled per patient and used across all three sequential readings. Across longitudinal simulation time, latent BP is **not** stored as a persistent continuous trajectory on `PatientContext`.
7. **Demographic Differentiation:** Latent BP sampling ranges do **not** differ by age, sex, diabetes, BMI, or comorbidity.
8. **Truncation and Clipping:** Uniform random variables are rounded to 1 decimal place. Pulse pressure is safeguarded to $\text{PP} \ge 20\text{ mmHg}$. Protocol readings are clipped to $[60, 280]$ SBP and $[40, 160]$ DBP.

---

## 3. Dependency Diagram and Causal Architecture

The following diagram illustrates the causal pathway and reveals the inverted dependency structure:

```mermaid
flowchart TD
    subgraph S1 [1. Synthetic Population Generation]
        PG[PatientProfileGenerator] -->|Demographic Sampling SRS| P[PatientContext: age, gender, birth_date]
        PG -->|Comorbidity Sampling: P HTN|T2D = 50.1%, no T2D = 28.2%| BC[baseline_conditions: I10]
    end

    subgraph S2 [2. Longitudinal Discrete-Event Simulation Days 0-720]
        CMR[ClinicalModuleRunner: hypertension.yaml]
        P & BC --> CMR
        CMR -->|Annual AgeCheck rate 0.0344| IO[Incident Onset: latent_conditions I10]
        CMR -->|90d Delay| SE[Screening Encounter]
        SE -->|Prescribe Amlodipine 5mg| RX[pharmacy.prescriptions]
    end

    subgraph S3 [3. Inverted Latent BP Generation at Day 180 Sweep]
        P & IO -->|Point-in-Time Check: onset <= Day 180| DH[has_htn: Boolean]
        RX -->|Point-in-Time Check: start <= Day 180| TRT[is_treated: Boolean]
        
        DH & TRT -->|Branch Selection| DIST{Conditional Distribution}
        DIST -->|has_htn=F| N_RANGE[Uniform 110-135 / 70-84]
        DIST -->|has_htn=T, treated=T| T_RANGE[Uniform 120-150 / 75-92]
        DIST -->|has_htn=T, treated=F| U_RANGE[Uniform 145-168 / 90-104]
        
        N_RANGE & T_RANGE & U_RANGE --> LBP[Latent Resting BP SBP/DBP]
    end

    subgraph S4 [4. Measurement Protocol & Classification]
        LBP --> BMS[BpMeasurementProtocolSimulator]
        BMS -->|R1 Alerting + R2/R3 Repeated Readings| PROTO[Protocol Mean of Readings 2 & 3]
        PROTO --> EVAL[LasiExternalEvaluator / Community Assessment]
        PROTO & TRT -->|SBP >= 140 OR DBP >= 90 OR Active Rx| CHTN[Composite Community HTN]
    end
```

---

## 4. Circularity and Construct Validity Findings

### 4.1 Internal Consistency vs. Real-World Diagnostic Accuracy
In real-world clinical practice, a patient's true underlying blood pressure is an unobserved physiological state. Clinicians measure blood pressure with error and apply diagnostic cut-points ($\ge 140/90\text{ mmHg}$) to diagnose hypertension. In this real-world paradigm:
- True normotensive patients may occasionally have elevated readings due to situational stress, caffeine, or measurement noise (false positives).
- Hypertensive patients may occasionally measure below $140/90\text{ mmHg}$ due to biological diurnal variability or random variation (false negatives).
- Diagnostic accuracy metrics (sensitivity, specificity, ROC curves) evaluate how effectively an imperfect measurement process identifies a latent clinical state.

In SYNAPSE Phase 2, the simulator assigns the disease label first, and then samples blood pressure strictly within bounds determined by that label.

### 4.2 Seed 42 Empirical 2x2 Matrix
Evaluating the 561 assessed older adults (age $\ge 45$) alive at Day 180 under Seed 42:

| Metric | Count | Proportion of Denominator ($N = 561$) |
| :--- | :--- | :--- |
| **Point-in-Time Latent Hypertension** | 217 | 38.68% |
| **Active Antihypertensive Prescription** | 217 | 38.68% |
| **Elevated Measured BP ($\ge 140/90\text{ mmHg}$)** | 89 | 15.86% |
| **Composite Community Hypertension** | 217 | 38.68% |

#### 2x2 Matrix: Latent Disease Label vs. Measured Elevated BP ($\ge 140/90\text{ mmHg}$)

| | Latent Hypertensive ($N = 217$) | Latent Normotensive ($N = 344$) | Total |
| :--- | :---: | :---: | :---: |
| **Measured Elevated BP ($\ge 140/90$)** | **89** (True Positive) | **0** (False Positive) | **89** |
| **Measured Normal BP ($< 140/90$)** | **128** (False Negative) | **344** (True Negative) | **472** |
| **Total** | **217** | **344** | **561** |

#### Internal Consistency Metrics (Not Clinical Validity):
- **Sensitivity:** $89 / 217 = \mathbf{41.01\%}$
- **Specificity:** $344 / (344 + 0) = \mathbf{100.00\%}$
- **Positive Predictive Value (PPV):** $89 / (89 + 0) = \mathbf{100.00\%}$
- **Negative Predictive Value (NPV):** $344 / (344 + 128) = \mathbf{72.88\%}$

> [!IMPORTANT]
> **Scientific Interpretation:**  
> The $100\%$ specificity and $100\%$ PPV are **mathematical artifacts** of the upper bound of the normotensive distribution ($135.0\text{ mmHg} < 140.0\text{ mmHg}$). They do not establish that the simulation exhibits realistic diagnostic fidelity. The sensitivity of $41.01\%$ reflects that all 217 hypertensives are treated, and the treated range $[120, 150]$ samples $\ge 140/90$ with probability $\approx 41\%$. When untreated, sensitivity is structurally $100\%$.

---

## 5. Distribution Overlap, Gaps, and Threshold Analysis

### 5.1 Empirical Sample Moments vs. Theoretical Parameters

Across the Seed 42 older adult cohort:

| Cohort Subset | Metric | Sample Mean | Sample SD | Sample Min | Sample Max | Theoretical Expected Value | Theoretical SD |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normotensive ($N = 344$)** | SBP | $123.04\text{ mmHg}$ | $7.12\text{ mmHg}$ | $110.0\text{ mmHg}$ | $134.8\text{ mmHg}$ | $122.50\text{ mmHg}$ | $7.22\text{ mmHg}$ |
| | DBP | $77.19\text{ mmHg}$ | $3.98\text{ mmHg}$ | $70.1\text{ mmHg}$ | $84.0\text{ mmHg}$ | $77.00\text{ mmHg}$ | $4.04\text{ mmHg}$ |
| | PP | $45.85\text{ mmHg}$ | $8.07\text{ mmHg}$ | $27.0\text{ mmHg}$ | $63.3\text{ mmHg}$ | $45.50\text{ mmHg}$ | $8.27\text{ mmHg}$ |
| **Treated Hypertensive ($N = 217$)** | SBP | $133.73\text{ mmHg}$ | $9.56\text{ mmHg}$ | $120.0\text{ mmHg}$ | $149.5\text{ mmHg}$ | $135.00\text{ mmHg}$ | $8.66\text{ mmHg}$ |
| | DBP | $83.40\text{ mmHg}$ | $4.97\text{ mmHg}$ | $75.3\text{ mmHg}$ | $92.0\text{ mmHg}$ | $83.50\text{ mmHg}$ | $4.91\text{ mmHg}$ |
| | PP | $50.34\text{ mmHg}$ | $10.66\text{ mmHg}$ | $28.0\text{ mmHg}$ | $73.3\text{ mmHg}$ | $51.50\text{ mmHg}$ | $9.95\text{ mmHg}$ |

### 5.2 Hard Boundaries and Discontinuities

```
Systolic Blood Pressure (mmHg)
100      110           120           130   135   140   145           150           160         170
 |--------|-------------|-------------|-----|-----|-----|-------------|-------------|-----------|
 Normotensive:  [===========================] (Max 135)
 Treated HTN:                 [=======================================] (120 to 150)
 Untreated HTN:                                               [=========================] (145 to 168)
                                            ^     ^     ^
                                            |     |     |
                                  135.1 to 144.9 GAP (Untreated Void)
                                  No untreated individual can exist here!
```

1. **The Untreated SBP Gap ($135.1$ to $144.9\text{ mmHg}$):**  
   In the real world, SBP is continuously distributed. Stage 1 hypertension begins at $140\text{ mmHg}$. Many untreated individuals have marginal elevations ($136, 138, 141, 143\text{ mmHg}$). In SYNAPSE Phase 2, the untreated normotensive ceiling is $135.0\text{ mmHg}$ and the untreated hypertensive floor is $145.0\text{ mmHg}$. There is an absolute **$10\text{ mmHg}$ empty gap** across the diagnostic threshold where no untreated patient can ever sample.
2. **The Untreated DBP Gap ($84.1$ to $89.9\text{ mmHg}$):**  
   Similarly, untreated normotensive DBP tops out at $84.0\text{ mmHg}$, and untreated hypertensive DBP starts at $90.0\text{ mmHg}$. A **$6\text{ mmHg}$ gap** prevents any continuous transition across the $90\text{ mmHg}$ diagnostic boundary.
3. **Controlled vs. Uncontrolled Treatment Partitioning:**  
   In treated patients ($[120, 150]\text{ mmHg}$ SBP, $[75, 92]\text{ mmHg}$ DBP), values $\ge 140/90$ occur uniformly above $140\text{ mmHg}$ for SBP and above $90\text{ mmHg}$ for DBP. This yields an empirical control rate of $128 / 217 = \mathbf{58.99\%}$ and an uncontrolled rate of $89 / 217 = \mathbf{41.01\%}$. This control rate is entirely dictated by the ratio $\frac{140 - 120}{150 - 120} = \frac{20}{30} \approx 66.7\%$ adjusted for DBP elevation.

---

## 6. Demographic Structure and Stratification Audit

### 6.1 Age Band Stratification (Denominator = 561)

| Age Band | Eligible $N$ | Latent HTN $n$ (%) | Elevated BP $n$ (%) | Active Rx $n$ (%) | Composite HTN $n$ (%) | Mean SBP (mmHg) | Mean DBP (mmHg) | Sensitivity | Specificity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **45–54** | 203 | 84 (41.4%) | 31 (15.3%) | 84 (41.4%) | 84 (41.4%) | 127.6 | 79.5 | 36.90% | 100.0% |
| **55–64** | 209 | 76 (36.4%) | 33 (15.8%) | 76 (36.4%) | 76 (36.4%) | 126.9 | 79.6 | 43.42% | 100.0% |
| **65–74** | **40** *(flagged)* | 18 (45.0%) | 10 (25.0%) | 18 (45.0%) | 18 (45.0%) | 129.0 | 80.1 | 55.56% | 100.0% |
| **75+** | 109 | 39 (35.8%) | 15 (13.8%) | 39 (35.8%) | 39 (35.8%) | 126.2 | 79.4 | 38.46% | 100.0% |
| **All Older Adults** | **561** | **217 (38.68%)** | **89 (15.86%)** | **217 (38.68%)** | **217 (38.68%)** | **127.2** | **79.6** | **41.01%** | **100.0%** |

*Note on small strata:* The 65–74 stratum contains only $N = 40$ participants ($7.1\%$ of the older adult sample), reflecting mortality attrition and demographic sampling weights.

### 6.2 Sex Stratification (Denominator = 561)

| Sex | Eligible $N$ | Latent HTN $n$ (%) | Elevated BP $n$ (%) | Active Rx $n$ (%) | Composite HTN $n$ (%) | Mean SBP (mmHg) | Mean DBP (mmHg) | Sensitivity | Specificity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Male** | 295 | 114 (38.6%) | 43 (14.6%) | 114 (38.6%) | 114 (38.6%) | 126.9 | 79.8 | 37.72% | 100.0% |
| **Female** | 266 | 103 (38.7%) | 46 (17.3%) | 103 (38.7%) | 103 (38.7%) | 127.5 | 79.4 | 44.66% | 100.0% |

### 6.3 Scientific Separation of Observations, Assumptions, and Evidence

1. **Observed Synthetic Results:**  
   Across all four age bands, mean SBP hovers within a $2.8\text{ mmHg}$ band ($126.2$ to $129.0\text{ mmHg}$), mean DBP hovers within a $0.7\text{ mmHg}$ band ($79.4$ to $80.1\text{ mmHg}$), and hypertension prevalence remains in a narrow band ($35.8\%$ to $45.0\%$).
2. **Structural Consequences of Model Assumptions:**  
   - In `synapse_simulator/datagen/patient_generator.py` line 121, baseline hypertension is assigned with flat probabilities: $50.1\%$ if diabetes is present, $28.2\%$ otherwise, for all individuals aged $\ge 20$.
   - In `synapse_simulator/population/loader.py` line 62, passing `conditional_rate` completely bypasses age-band and sex-specific prevalence tables in `india_default_v1.yaml`.
   - In `config/modules/hypertension.yaml` line 25, annual incident onset is a constant $0.0344$ for all adults $\ge 20$.
   - In `synapse_simulator/datagen/community_assessment.py`, the uniform sampling ranges do not adjust for chronological age.
3. **Empirically Supported Population Claims (Real-World Evidence):**  
   In genuine population data (such as LASI Wave 1 and ICMR-INDIAB), blood pressure and hypertension exhibit a steep age gradient:
   - SBP rises progressively with age (e.g. from $\sim 120\text{ mmHg}$ at age 45 to $> 140\text{ mmHg}$ at age 75+) due to vascular stiffening and loss of arterial compliance.
   - DBP tends to rise until age 55–60 and then plateau or decline, causing marked pulse pressure widening.
   - Hypertension prevalence rises from $\sim 25\%$ at age 45–54 to $> 55\%$ at age 75+.
4. **Unresolved Hypotheses:**  
   Whether Indian older adults experience a distinct SBP trajectory compared to Western populations due to earlier arterial stiffening or malnutrition-related low BMI cannot be determined from synthetic simulation alone without authorized access to LASI Wave 1 microdata.

---

## 7. Measurement Error Equations and Variance Checks

The protocol simulator supports three measurement-error modes applied to individual sequential readings:

```
Reading 1: SBP_1 = SBP_underlying + AlertingShift_SBP
Readings 2 & 3: Repeated resting measurements with within-visit variation
Final Analysis Value: Mean of Readings 2 and 3
```

### 7.1 Equations and Error Variance Derivations

#### 1. SYMMETRICAL_UNBIASED (Current Default)
- **Equation:**
  $$\Delta_{\text{SBP}, 1} = \max(0.5, \mathcal{N}(3.5, 0.8^2))$$
  $$\epsilon \sim \text{clip}(\mathcal{N}(0, 1.8^2), -5.0, 5.0)$$
  $$\text{Reading 2: } SBP_2 = SBP_{\text{underlying}} + \epsilon$$
  $$\text{Reading 3: } SBP_3 = SBP_{\text{underlying}} - \epsilon$$
- **Protocol Analysis Mean (Readings 2 & 3):**
  $$SBP_{\text{final}} = \frac{SBP_2 + SBP_3}{2} = \frac{(SBP_{\text{underlying}} + \epsilon) + (SBP_{\text{underlying}} - \epsilon)}{2} \equiv SBP_{\text{underlying}}$$
- **Variance Behavior:**  
  Residual measurement error variance is **identically 0**. The protocol mean equals the latent physiological draw exactly. Single readings capture variation ($\sigma^2 = 3.24\text{ mmHg}^2$), but the analysis mean has zero variance.

#### 2. INDEPENDENT_GAUSSIAN
- **Equation:**
  $$\epsilon_2 \sim \mathcal{N}(0, \sigma^2), \quad \epsilon_3 \sim \mathcal{N}(0, \sigma^2), \quad \epsilon_2 \perp \epsilon_3, \quad \sigma = 1.8\text{ mmHg}$$
- **Protocol Analysis Mean:**
  $$SBP_{\text{final}} = SBP_{\text{underlying}} + \frac{\epsilon_2 + \epsilon_3}{2}$$
- **Variance Behavior:**
  $$\operatorname{Var}\left(\frac{\epsilon_2 + \epsilon_3}{2}\right) = \frac{\sigma^2 + \sigma^2}{4} = \frac{\sigma^2}{2} = \frac{1.8^2}{2} = \mathbf{1.6200\text{ mmHg}^2}$$
  For DBP ($\sigma_{\text{DBP}} = 1.8 \times 0.6 = 1.08\text{ mmHg}$):
  $$\operatorname{Var}\left(\frac{\epsilon_{2, \text{DBP}} + \epsilon_{3, \text{DBP}}}{2}\right) = \frac{1.08^2}{2} = \mathbf{0.5832\text{ mmHg}^2}$$

#### 3. AUTOREGRESSIVE_AR1
- **Equation:**
  $$u_2 \sim \mathcal{N}(0, \sigma^2), \quad u_3 \sim \mathcal{N}(0, \sigma^2), \quad \sigma = 1.8\text{ mmHg}, \quad \rho = 0.70$$
  $$\epsilon_2 = u_2, \quad \epsilon_3 = \rho u_2 + \sqrt{1 - \rho^2} u_3$$
- **Protocol Analysis Mean:**
  $$SBP_{\text{final}} = SBP_{\text{underlying}} + \frac{\epsilon_2 + \epsilon_3}{2}$$
- **Variance Behavior:**
  $$\operatorname{Var}(\epsilon_2) = \sigma^2, \quad \operatorname{Var}(\epsilon_3) = \sigma^2, \quad \operatorname{Cov}(\epsilon_2, \epsilon_3) = \rho \sigma^2$$
  $$\operatorname{Var}\left(\frac{\epsilon_2 + \epsilon_3}{2}\right) = \frac{\sigma^2 + \sigma^2 + 2\rho\sigma^2}{4} = \frac{\sigma^2(1 + \rho)}{2} = \frac{3.24 \times 1.70}{2} = \mathbf{2.7540\text{ mmHg}^2}$$
  For DBP ($\sigma_{\text{DBP}} = 1.08\text{ mmHg}$):
  $$\operatorname{Var}_{\text{DBP}} = \frac{1.08^2 \times 1.70}{2} = \mathbf{0.9914\text{ mmHg}^2}$$

### 7.2 Measurement Error Comparison Table

| Error Mode | Reading 1 Shift | Single Reading SD ($\sigma$) | Theoretical Variance of Mean | Empirical Sample Variance | Practical Implication |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **SYMMETRICAL_UNBIASED** | $+3.5\text{ mmHg}$ | $1.80\text{ mmHg}$ | $\mathbf{0.0000\text{ mmHg}^2}$ | $0.0000\text{ mmHg}^2$ | Exact calibration preservation; zero residual noise in analysis value. |
| **INDEPENDENT_GAUSSIAN** | $+3.5\text{ mmHg}$ | $1.80\text{ mmHg}$ | $\mathbf{1.6200\text{ mmHg}^2}$ | $1.6184\text{ mmHg}^2$ | Independent random error; dampens variance by factor of 2. |
| **AUTOREGRESSIVE_AR1** | $+3.5\text{ mmHg}$ | $1.80\text{ mmHg}$ | $\mathbf{2.7540\text{ mmHg}^2}$ | $2.7641\text{ mmHg}^2$ | Realistic serial autocorrelation ($\rho = 0.70$); preserves residual noise. |

---

## 8. Evidential Status Catalog of Major Parameters

| Parameter | Location in Code | Value | Evidential Status | Scientific Justification & Boundaries |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline HTN Rate (with T2D)** | `patient_generator.py:121` | $50.1\%$ | **Empirical Literature** | ICMR-INDIAB 2023 reported $P(\text{HTN}\mid\text{T2D}) = 50.1\%$. |
| **Baseline HTN Rate (no T2D)** | `patient_generator.py:121` | $28.2\%$ | **Empirical Literature** | ICMR-INDIAB 2023 reported $P(\text{HTN}\mid\text{no T2D}) = 28.2\%$. |
| **Annual HTN Incident Rate** | `hypertension.yaml:25` | $0.0344$ | **Empirical Literature** | CURES / CCDC prospective cohort incidence rate. |
| **Normotensive SBP Range** | `community_assessment.py:256` | $[110.0, 135.0]$ | **Stylized Knowledge Default** | Expert knowledge bounds; lacks smooth continuous tails. |
| **Normotensive DBP Range** | `community_assessment.py:257` | $[70.0, 84.0]$ | **Stylized Knowledge Default** | Expert knowledge bounds; lacks smooth continuous tails. |
| **Treated HTN SBP Range** | `community_assessment.py:250` | $[120.0, 150.0]$ | **Stylized Knowledge Default** | Derived from clinical follow-up range; forces $33\%$ uncontrolled SBP. |
| **Treated HTN DBP Range** | `community_assessment.py:251` | $[75.0, 92.0]$ | **Stylized Knowledge Default** | Clinical follow-up range. |
| **Untreated HTN SBP Range** | `community_assessment.py:253` | $[145.0, 168.0]$ | **Stylized Knowledge Default** | Derived from screening observation range; introduces $10\text{ mmHg}$ gap. |
| **Untreated HTN DBP Range** | `community_assessment.py:254` | $[90.0, 104.0]$ | **Stylized Knowledge Default** | Screening observation range; introduces $6\text{ mmHg}$ gap. |
| **Pulse Pressure Minimum** | `community_assessment.py:260` | $20.0\text{ mmHg}$ | **Physiological Guard** | Ensures SBP strictly exceeds DBP by physiological minimum. |
| **Alerting SBP Shift (R1)** | `bp_measurement.py:153` | $+3.5\text{ mmHg}$ | **Provisional Literature Default** | White-coat situational alerting effect from clinical trials. |
| **Within-Visit Noise SD** | `bp_measurement.py:161` | $1.8\text{ mmHg}$ | **Provisional Literature Default** | Within-visit repeated measurement noise from clinical trials. |
| **AR(1) Autocorrelation $\rho$** | `bp_measurement.py:149` | $0.70$ | **Provisional Literature Default** | Short-interval correlation between repeated readings. |

---

## 9. Remaining Scientific Limitations

1. **Inverted Disease-to-Measurement Causal Direction:**  
   The simulator cannot model realistic continuous blood pressure development (e.g. tracking pre-hypertension, gradual arterial stiffening, or fluctuating borderline status) because blood pressure is a downstream child of the discrete `"I10"` categorical state.
2. **Artificial $10\text{ mmHg}$ Void in Untreated Populations:**  
   The non-overlapping ranges $[110, 135]$ and $[145, 168]$ guarantee that no untreated individual can ever have blood pressure in the borderline zone ($136–144\text{ mmHg}$).
3. **Absence of Age-Related SBP Trajectory:**  
   Because both baseline risk and latent BP ranges are flat across age, the simulator fails to reflect the classic physiological rise of systolic blood pressure and pulse pressure widening with advancing age.
4. **Uniform Distribution Shape:**  
   Biological variables in populations follow continuous unimodal distributions (e.g., Gaussian, log-normal, or skew-normal). Using uniform distributions introduces rectangular density functions with hard cutoffs rather than bell-shaped population densities.
5. **Validation Gate Status:**  
   The external validation gate remains strictly **`REFERENCE_DATA_PENDING`**. All evaluations are verified against synthetic test fixtures.

---

## 10. Recommended Next Steps (Future Architecture Roadmap)

When external reference microdata becomes available, the following architectural enhancements are scientifically justified:

1. **Continuous Latent BP Evolution Model:**  
   Replace discrete conditional uniform sampling with a continuous latent biological trajectory:
   $$SBP_i(t) = \beta_0 + \beta_{\text{age}} \cdot \text{Age}_i(t) + \beta_{\text{sex}} \cdot \text{Sex}_i + \beta_{\text{T2D}} \cdot \text{T2D}_i(t) + u_i + \epsilon_{it}$$
   where $u_i \sim \mathcal{N}(0, \sigma_u^2)$ is individual random intercept.
2. **Forward Diagnostic Assignment:**  
   Assign the clinical hypertension diagnosis when observed blood pressure persistently exceeds $140/90\text{ mmHg}$ at healthcare encounters, restoring correct physiological causality.
3. **Continuous Treatment Effect:**  
   Model antihypertensive treatment as a continuous downward shift in latent blood pressure ($\Delta_{\text{treatment}} \approx -10\text{ to } -15\text{ mmHg}$ SBP) with adherence variation, rather than switching to an arbitrary $[120, 150]$ uniform compartment.

---

## 11. Verification and Test Suite Execution

The entire test suite was executed to confirm that no regressions were introduced and that all temporal boundary tests continue to pass:

```bash
$ .venv/bin/pytest
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/shashi/synapse/synapse-phase2
plugins: Faker-40.43.0
collected 273 items

tests/test_bp_measurement_protocol.py .........................          [  9%]
tests/test_clinical_modules.py ......                                    [ 11%]
tests/test_community_assessment_audit.py ............................... [ 22%]
....                                                                     [ 24%]
tests/test_data_integrity_temporal_consistency.py ...............        [ 29%]
tests/test_datagen.py ...                                                [ 30%]
tests/test_determinism.py ..........                                     [ 34%]
tests/test_dispatcher.py .                                               [ 34%]
tests/test_end_to_end_acceptance.py .                                    [ 35%]
tests/test_evaluation_framework.py ....................                  [ 42%]
tests/test_evaluation_mutations.py ......                                [ 44%]
tests/test_event_queue.py ...                                            [ 45%]
tests/test_full_simulation.py .                                          [ 46%]
tests/test_lab_rad_finance_rules.py ...                                  [ 47%]
tests/test_lasi_pipeline.py ..........................................   [ 62%]
tests/test_longitudinal_export.py ..                                     [ 63%]
tests/test_longitudinal_trajectories.py ....                             [ 64%]
tests/test_orchestrator.py ..                                            [ 65%]
tests/test_person_time_and_censoring.py .......                          [ 68%]
tests/test_phase2_csv_export.py ...                                      [ 69%]
tests/test_population_profile.py .....                                   [ 71%]
tests/test_population_validator.py .....                                 [ 72%]
tests/test_pubmed_datagen_integration.py ........                        [ 75%]
tests/test_pubmed_treatment_architecture.py ........                     [ 78%]
tests/test_root_cause_corrections.py ..........                          [ 82%]
tests/test_rule_engine.py ....                                           [ 83%]
tests/test_solid_principles.py .....                                     [ 85%]
tests/test_stage6_clock_scheduler.py ...                                 [ 86%]
tests/test_stage6_domain_events.py ..                                    [ 87%]
tests/test_stage6_loop_failure_protection.py ..                          [ 88%]
tests/test_stage6_ordering_causation.py ..                               [ 89%]
tests/test_stage6_reproducibility.py .                                   [ 89%]
tests/test_stage6_small_simulation.py .                                  [ 89%]
tests/test_stage7_cross_department.py .                                  [ 90%]
tests/test_stage7_patient_journeys.py .                                  [ 90%]
tests/test_stage7_scale.py .                                             [ 90%]
tests/test_stage7_workflows.py ..                                        [ 91%]
tests/test_stage9_billing.py .                                           [ 91%]
tests/test_stage9_diagnostics.py .                                       [ 92%]
tests/test_stage9_discharge.py .                                         [ 92%]
tests/test_stage9_integrity.py .                                         [ 93%]
tests/test_stage9_persistence.py ..                                      [ 93%]
tests/test_stage9_prescription.py .                                      [ 94%]
tests/test_state_machines.py .......                                     [ 96%]
tests/test_state_manager.py ....                                         [ 98%]
tests/test_validation_gate.py .....                                      [100%]

============================= 273 passed in 8.64s ==============================
```
