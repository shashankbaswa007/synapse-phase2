# LASI Patient-Level Comparison Method and Estimand Framework

**Project:** SYNAPSE Phase 2 — Synthea-Inspired Synthetic Healthcare Generation  
**Document ID:** `DOC-RES-LASI-009`  
**Focus Area:** Longitudinal-to-Cross-Sectional Comparability, Prespecified Index Selection, and Estimand Segregation  
**Date:** 2026-10-21  
**Git Revision:** `c71a39d`  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Methodological Rationale: Longitudinal vs. Cross-Sectional Data

The Longitudinal Ageing Study in India (LASI) Wave 1 (2017–2018) is a **nationally representative, cross-sectional population survey** (with respect to Wave 1 measurements). In contrast, SYNAPSE Phase 2 is an **agent-based discrete-event longitudinal simulation** producing repeated outpatient visits, medication adjustments, and follow-up vitals over time.

In the 2,200-patient synthetic cohort, 235 older adults ($\ge 45$ years) undergo repeated clinical encounters, generating **852 paired blood pressure observations** (an average of $3.6$ encounters per patient).

### The Danger of Pseudoreplication
Directly pooling all 852 synthetic measurements and comparing them against the cross-sectional LASI survey records creates **severe pseudoreplication**:
1. **Violation of Independence:** Multiple blood pressure observations from the same synthetic individual share latent physiological traits, underlying vascular stiffening, and common treatment paths. Treating them as 852 independent individuals artificially shrinks standard errors, distorts Kolmogorov-Smirnov statistics, and biases empirical cumulative distribution functions (eCDFs).
2. **Survival and Treatment Confounding:** Follow-up visits capture patients after lifestyle interventions and antihypertensive medications (Amlodipine, Telmisartan) have been initiated, shifting distributions toward normal ranges in a manner uncharacteristic of an unselected community survey.
3. **Over-Representation of Frequent Attenders:** Patients with severe or uncontrolled hypertension return more frequently for step-up therapy evaluation, overweighting uncontrolled blood pressures if all encounters are pooled indiscriminately.

---

## 2. Prespecified Patient-Level Index Measurement Pathway

To eliminate pseudoreplication while maintaining methodological integrity, SYNAPSE implements a **prespecified patient-level index measurement rule**:

```
[All Synthetic Encounters for Patient i]
   ├── Encounter 1 (t = t_0): SBP 158 mmHg, DBP 96 mmHg   <-- SELECTED AS INDEX MEASUREMENT
   ├── Encounter 2 (t = t_1): SBP 142 mmHg, DBP 88 mmHg   [Longitudinal Follow-up - Retained for Estimand D]
   └── Encounter 3 (t = t_2): SBP 132 mmHg, DBP 82 mmHg   [Longitudinal Follow-up - Retained for Estimand D]
```

### 2.1 Prespecified Selection Rule
For each eligible synthetic patient (age $\ge 45$ years):
$$\text{Index Encounter}_i = \arg\min_{e \in \mathcal{E}_i} \text{timestamp}(e)$$
where $\mathcal{E}_i$ is the set of clinical encounters for patient $i$ containing valid blood pressure measurements.

### 2.2 Methodological Justification
1. **Clinical Representativeness:** The earliest eligible measurement captures the patient's baseline or presenting clinical state before longitudinal treatment titration and simulation attrition occur.
2. **Pre-specified and Outcome-Blind:** The selection rule operates strictly on temporal ordering (`timestamp`). Measurements are **never selected based on proximity to the reference distribution**.
3. **Deterministic & Reproducible:** Given a fixed simulation seed, the patient's trajectory and earliest encounter are strictly deterministic.
4. **Explicit Handling of Unmeasured Patients:** Synthetic individuals who do not experience a hypertensive outpatient encounter during the simulation window ($N=340$ older adults) are audited explicitly as unmeasured ($59.13\%$) rather than imputed.

---

## 3. Four Segregated Evaluation Estimands

Under scientific validation governance, distinct clinical and epidemiological questions cannot be collapsed into a single metric. SYNAPSE evaluates four explicitly separated estimands:

### Estimand A: Patient-Level Cross-Sectional Continuous Blood Pressure Distributions
* **Target Population:** Older adults aged $\ge 45$ with at least one measured blood pressure.
* **Synthetic Unit:** One index measurement per patient ($N=235$).
* **Reference Unit:** Protocolized average blood pressure from LASI Wave 1 survey ($N=50$, $n_{\text{eff}}=48.9$).
* **Metrics:**
  1. `lasi_bp_sbp_distribution`: Index SBP continuous distribution (mean, quantiles, KS statistic, 1-Wasserstein distance).
  2. `lasi_bp_sbp_standardized_mean`: Directly standardized mean index SBP across 8 Census SRS older-adult strata.
  3. `lasi_bp_dbp_distribution`: Index DBP continuous distribution.
  4. `lasi_bp_dbp_standardized_mean`: Directly standardized mean index DBP across 8 Census SRS strata.
  5. `lasi_bp_pulse_pressure_distribution`: Index Pulse Pressure ($\text{PP} = \text{SBP} - \text{DBP}$) distribution.

### Estimand B: Measurement-Defined Hypertension Prevalence
* **Target Population:** Entire older adult cohort ($N=575$).
* **Case Definition (Standard Epidemiological Criteria):**
  $$\text{Index SBP} \ge 140 \text{ mmHg} \lor \text{Index DBP} \ge 90 \text{ mmHg} \lor \text{currently on antihypertensive medication}$$
* **Metric:** `lasi_prev_measurement_defined_htn_older_adult`.
* **Methodological Distinction:** Captures both diagnosed and undiagnosed hypertensive individuals based on objective vital signs and medication orders, mirroring population bio-marker surveys.

### Estimand C: Synthetic EHR-Recorded Hypertension Prevalence
* **Target Population:** Entire older adult cohort ($N=575$).
* **Case Definition:** Presence of documented ICD-10 diagnosis code `I10` (Essential Hypertension) in the patient's medical record.
* **Metric:** `lasi_prev_htn_older_adult`.
* **Methodological Distinction:** Reflects institutional EHR capture rates. In real-world health systems, EHR-recorded diagnosis prevalence is consistently lower than survey measurement-defined prevalence due to under-diagnosis and asymptomatic latency.

### Estimand D: Longitudinal BP Trajectory and Treatment Response
* **Target Population:** Multi-visit synthetic patients with $\ge 2$ clinical encounters ($N=229$).
* **Estimand Definition:** Intra-individual trajectory response:
  $$\Delta \text{SBP}_i = \text{SBP}_{i, \text{latest}} - \text{SBP}_{i, \text{baseline}}$$
* **Metric:** `lasi_bp_longitudinal_trajectory_treatment_response`.
* **Validation Status:** Strictly assigned **`UNVERIFIED`**.
* **Methodological Justification:** LASI Wave 1 is a single cross-sectional wave. Longitudinal treatment response cannot be validated against single-point survey data; verifying trajectory fidelity requires multi-wave longitudinal panel data (such as LASI Wave 2, when authorized).

---

## 4. Quantitative Results and Estimand Separation

In the generated cohort ($N=2,200$, 575 older adults, seed 42):

| Estimand | Metric Name | Synthetic N (Pts) | Synthetic Est | Reference Est | Difference | Gate Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Estimand A** | Index SBP Distribution | 235 pts (852 obs) | 156.44 mmHg | 148.51 mmHg | +7.93 mmHg | **WARNING** |
| **Estimand A** | Standardized Mean SBP | 235 pts (852 obs) | 156.45 mmHg | 141.49 mmHg | +14.96 mmHg | **WARNING** |
| **Estimand A** | Index DBP Distribution | 235 pts (852 obs) | 96.89 mmHg | 87.36 mmHg | +9.53 mmHg | **WARNING** |
| **Estimand A** | Standardized Mean DBP | 235 pts (852 obs) | 96.88 mmHg | 84.26 mmHg | +12.62 mmHg | **WARNING** |
| **Estimand A** | Index Pulse Pressure | 235 pts (852 obs) | 59.55 mmHg | 60.18 mmHg | -0.63 mmHg | **WARNING** |
| **Estimand B** | Measurement-Defined HTN | 575 older adults | 40.87% | 79.73% | -38.86% | **WARNING** |
| **Estimand C** | EHR Diagnosis HTN | 575 older adults | 40.87% | 79.73% | -38.86% | **WARNING** |
| **Estimand D** | Longitudinal Delta SBP | 229 multi-visit pts | -14.47 mmHg | N/A | N/A | **UNVERIFIED** |

*Note: The reference fixture is a 50-row structural test fixture. The overall evaluation status remains formally **`REFERENCE_DATA_PENDING`**.*

---

## 5. Statistical Independence Safeguards

1. **Disaggregated Denominators:** The evaluation report explicitly displays both the number of distinct patients ($N=235$) and the total number of longitudinal observations ($N=852$).
2. **Kish Effective Sample Size:** Complex survey weights in the reference dataset are incorporated using Kish's formula ($n_{\text{eff}} = 48.9$), preventing variance underestimation.
3. **Census SRS Direct Standardization:** Differences in age and sex pyramids between the synthetic cohort and the reference population are standardized across 8 Census SRS strata.

---

## 6. Summary

By establishing a prespecified index measurement selection rule and segregating Estimands A, B, C, and D, the SYNAPSE external evaluation framework eliminates pseudoreplication while rigorously respecting the boundary between cross-sectional population distributions and longitudinal clinical trajectories.
