# Scientific and Statistical Audit: Independent Community Health Assessment Pathway

**Project:** SYNAPSE Phase 2 Synthetic Healthcare Simulation  
**Audit Target:** Independent Community Health Assessment Pathway (`community_assessment.py`, `evaluator.py`, `experiment.py`)  
**Evaluation Cohort:** $N = 2,200$ total synthetic patients, $575$ older adults ($\ge 45$ years), Random Seed $42$  
**Evaluation Gate Status:** `REFERENCE_DATA_PENDING` (Preserved strictly)  
**Date of Audit:** October 2026  

---

## 1. Executive Summary & Verdict

### 1.1 Executive Verdict: **CONDITIONALLY READY FOR EXTERNAL COMPARISON**

The Independent Community Health Assessment Pathway in SYNAPSE Phase 2 has successfully decoupled population-level epidemiological health observation from clinical hospital encounters. 

The pathway generates **scientifically interpretable and reproducible** population blood pressure data that avoids false-negative misclassification of unmeasured patients while providing a direct counterpart to household health surveys such as LASI (Longitudinal Ageing Study in India) Wave 1.

However, the pathway is **conditionally ready** subject to clear recognition of its structural properties and physiological limitations:
1. **Clinical Pathway Confounding:** The clinical EHR pathway exhibits 100% selection on disease ($235/235 = 100.0\%$ hypertension prevalence) because blood pressure is only recorded during hypertension-module encounters. The clinical pathway cannot be used for general population prevalence evaluation.
2. **Community Pathway Unbiased Coverage:** The community pathway surveyed 561 out of 575 older adults (97.57% coverage), with the remaining 14 individuals having died prior to the survey date ($t = 180$ days). Among surviving older adults, community survey coverage is 100.0% across all demographic and clinical subgroups.
3. **Physiological Distribution Simplicity:** Community blood pressure is currently generated via stratified uniform distributions anchored to clinical and baseline knowledge intervals. It lacks continuous age-dependent arterial stiffening (pulse pressure widening across older age deciles), which must be addressed in future calibration without arbitrary parameter tweaking.
4. **Governance Invariant:** The external evaluation status remains strictly **`REFERENCE_DATA_PENDING`**. No claims of external validity against genuine Indian population data can be made until authorized microdata are ingested.

---

## 2. Regenerated and Verified Cohort Statistics (Seed 42)

Independent replication of the simulation and evaluation pipeline confirmed the reported metrics to the exact integer:

| Metric | Numerator / Denominator | Proportion (%) | 95% Wilson Score CI | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Total Synthetic Population** | 2,200 / 2,200 | 100.0% | — | Verified |
| **Older Adults (Age $\ge 45$)** | 575 / 2,200 | 26.14% | [24.34%, 28.02%] | Verified |
| **EHR-Recorded I10 Diagnosis** | 235 / 575 | 40.87% | [36.90%, 44.97%] | Verified |
| **Clinically Assessable HTN (Estimand B)** | 235 / 235 | **100.00%** | [98.40%, 100.00%] | Verified |
| **Community Health Assessment HTN (Estimand C2)** | 234 / 561 | **41.71%** | [37.69%, 45.86%] | Verified |
| **Clinical Facility Attenders HTN (Estimand D1)** | 235 / 485 | **48.45%** | [44.02%, 52.92%] | Verified |
| **Unassessable Clinical HTN Status (Estimand E)** | 340 / 575 | **59.13%** | [55.08%, 63.07%] | Verified |
| **Prior Deaths Before Survey ($t \le 180\text{ d}$)** | 14 / 575 | 2.43% | [1.44%, 4.07%] | Verified |
| **Test Suite Execution** | 223 passing tests | 100% pass | — | Verified |
| **External Validation Gate** | — | — | — | `REFERENCE_DATA_PENDING` |

---

## 3. End-to-End Trace of the Data-Generation Pathway

### 3.1 Component Architecture & Responsibilities

```
                                [Population Profile: india_default_v1.yaml]
                                                   │
                                                   ▼
                                       [PatientProfileGenerator]
                                       (Demographics, Baselines)
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
             [ClinicalModuleRunner]                            [CommunityAssessmentGenerator]
            (Discrete-Event Simulator)                          (Independent Household Survey)
                         │                                                   │
       ┌─────────────────┴─────────────────┐                                 │
       ▼                                   ▼                                 │
[hypertension.yaml]               [diabetes_t2.yaml]                         │
 (Onset -> BP Encounters)          (HbA1c Encounters)                        │
       │                                   │                                 │
       ▼                                   ▼                                 │
 [encounters.csv]                   [encounters.csv]                         │
 [conditions.csv]                   [conditions.csv]                         │
 [observations.csv] (SBP/DBP)       [observations.csv] (HbA1c)               │
 [medications.csv]                  [medications.csv]                        │
       │                                   │                                 │
       └─────────────────┬─────────────────┘                                 │
                         ▼                                                   ▼
               [Clinical EHR Tables]                           [community_assessments.csv]
                         │                                                   │
                         └─────────────────────────┬─────────────────────────┘
                                                   ▼
                                        [LasiExternalEvaluator]
                                        (Estimands A, B, C, D, E)
```

1. **Patient Generation (`synapse_simulator/datagen/patient_generator.py`):**
   - Instantiates `PatientContext` objects with demographic attributes (age, sex) and baseline conditions.
   - For Seed 42, 575 patients reach age 45 or older.
2. **Clinical Simulation Execution (`synapse_simulator/modules/engine.py`):**
   - Discrete-event simulation steps active modules (`hypertension.yaml`, `diabetes_t2.yaml`, `urti.yaml`) over a 720-day horizon with a 7-day timestep.
   - Evaluates background life-table mortality (Census SRS 2016–2020) at each timestep.
3. **Hypertension Clinical Module (`config/modules/hypertension.yaml`):**
   - Older adults transition through `AgeCheck` into `HypertensionOnset` (weight 0.0344/yr) or `NormotensiveDelay` (weight 0.9656/yr).
   - Only patients in `HypertensionOnset` reach `ScreeningEncounter`, which emits SBP (145–168 mmHg) and DBP (90–104 mmHg), records diagnosis `I10`, and prescribes Amlodipine 5mg.
   - Patients in `NormotensiveDelay` delay 365 days and loop back without generating encounters, observations, or prescriptions.
4. **Community Health Assessment Sweep (`synapse_simulator/datagen/community_assessment.py`):**
   - Runs as an independent survey sweep at reference timestamp $t = 180\text{ days}$ (`2024-06-29T00:00:00`).
   - Gating criteria: Age $\ge 45.0$ and alive at survey date (`death_date is None or death_date > survey_date`).
   - Reads latent disease state (`has_htn`) and active medication registry (`active_antihypertensive_pids`).
   - Generates independent community vital signs without emitting encounters, diagnoses, or prescriptions.
5. **CSV Exporter (`synapse_simulator/exporter/csv_exporter.py`):**
   - Strictly isolates community survey records into `community_assessments.csv`.
   - Never writes community observations into `observations.csv` or `encounters.csv`.
6. **LASI Evaluator (`synapse_simulator/evaluation/lasi/evaluator.py`):**
   - Consumes both clinical EHR tables and `community_assessments.csv`.
   - Maps inputs to distinct, non-overlapping estimands (A, B, C1, C2, D1, D2, E).

---

## 4. Investigation of the 100% Clinical Hypertension Result

### 4.1 Root Cause Analysis

In the clinical EHR pathway, **all 235 clinically assessable older adults are hypertensive ($235/235 = 100\%$)**. 

The root cause was traced to a structural feature in the clinical module generator:
1. **Clinical Observation Depends Strictly on Latent Disease:** Blood pressure observations (`observation_code: "SBP"` and `"DBP"`) are defined exclusively within `config/modules/hypertension.yaml` (states `RecordBloodPressure` and `MeasureFollowUpBP`).
2. **Absence of Routine Screening for Non-Hypertensive Patients:** Non-hypertensive older adults loop within `NormotensiveDelay` (365 days) and never trigger a general health checkup or routine vital signs assessment in the clinical EHR.
3. **No Cross-Module Routine Vitals:** 250 older adults visited outpatient clinics for other conditions (e.g. Type 2 Diabetes in `diabetes_t2.yaml`), but outpatient encounters in those modules only record disease-specific biomarkers (e.g. HbA1c), not routine blood pressure.
4. **Deterministic Prescription Concurrence:** Every patient who undergoes `RecordBloodPressure` immediately transitions to `PrescribeAntihypertensive` (Amlodipine 5mg). Hence, all 235 measured patients are simultaneously medicated.

### 4.2 Patient-Level Mutually Interpretable Indicator Audit

The 575 synthetic older adults partition cleanly into three mutually disjoint clinical categories:

```
Total Older Adults (N = 575)
│
├── Clinically Assessable (N = 235, 40.87%)
│   └── 100% Latent HTN, 100% EHR I10, 100% Clinical BP, 100% Active Rx -> 100% Clinically Hypertensive
│
└── Clinically Unassessable (N = 340, 59.13%)
    ├── Attended Clinic for Other Conditions (N = 250, 43.48%)
    │   └── 0% Latent HTN, 0% EHR I10, 0% Clinical BP, 0% Active Rx, HbA1c recorded
    │
    └── Never Attended Clinical Facility (N = 90, 15.65%)
        ├── Normotensive Non-Attenders (N = 89)
        └── Undiagnosed Hypertensive Non-Attender (N = 1, pat-c2683807)
```

| Patient Group | $N$ | Latent HTN | EHR I10 | Clinical BP | Active Rx | Comm BP | Comm HTN Status | Clinical Assessability Reason |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Diagnosed Hypertensive Attenders** | 233 | Yes | Yes | Yes | Yes | Yes | 96 Uncontrolled, 137 Controlled | `ASSESSABLE` |
| **Diagnosed Hypertensives Deceased $<180$d** | 2 | Yes | Yes | Yes | Yes | No | Unassessed (Died prior) | `ASSESSABLE` |
| **Undiagnosed Hypertensive Non-Attender** | 1 | Yes | No | No | No | Yes | Measured Elevated (145.9/92.8) | `NO_CLINICAL_VISITS` |
| **Normotensive Diabetic Attenders** | 250 | No | No | No | No | Yes | Measured Normal (110–135) | `VISITED_CLINIC_NO_BP_ORDERED` |
| **Normotensive Non-Attenders** | 77 | No | No | No | No | Yes | Measured Normal (110–135) | `NO_CLINICAL_VISITS` |
| **Normotensives Deceased $<180$d** | 12 | No | No | No | No | No | Unassessed (Died prior) | `NO_CLINICAL_VISITS` |
| **Total Older Adults** | **575** | **236** | **235** | **235** | **235** | **561** | **234 HTN / 327 Normal** | — |

*Key Scientific Insight:* Patient `pat-c2683807` represents an undiagnosed hypertensive individual in the community who developed latent hypertension but never visited a clinical facility. Their blood pressure was accurately detected as elevated (145.9 / 92.8 mmHg) during the community survey despite zero clinical records.

---

## 5. Audit Findings Ranked by Severity

### Finding 1 (Critical): Clinical Pathway exhibits Total Berkson's / Selection Bias
- **Severity:** CRITICAL
- **Component:** `config/modules/hypertension.yaml`, `evaluator.py:800-860`
- **Description:** Clinical BP observations are 100% confounded by latent disease onset. Estimand B ($100.0\%$) measures the positive rate among clinic-screened hypertensive patients, not population prevalence.
- **Remediation Completed:** Implemented independent community assessment pathway (`community_assessments.csv`) and formal Estimand E ($59.13\%$ unassessable rate) to prevent false-negative misclassification.

### Finding 2 (High): Community BP Generator Lacks Age-Dependent Arterial Stiffening
- **Severity:** HIGH
- **Component:** `synapse_simulator/datagen/community_assessment.py:127-147`
- **Description:** Community SBP and DBP are drawn from stationary uniform distributions stratified only by `has_htn` and `is_treated`. Mean SBP is virtually flat across age groups (127.78 mmHg at 45–54 vs 126.86 mmHg at 75+). Real human populations exhibit monotonic SBP increases and pulse pressure widening with advancing age.
- **Action Required:** Future empirical calibration against authorized reference data using a biological arterial compliance model, without arbitrary parameter adjustments.

### Finding 3 (Medium): Estimand Labeling Collision in Evaluator
- **Severity:** MEDIUM
- **Component:** `synapse_simulator/evaluation/lasi/evaluator.py:1108, 1188`
- **Description:** Both EHR-recorded prevalence and community assessment prevalence are tagged with `estimand_type` containing "ESTIMAND_C". Similarly, both facility attenders prevalence and longitudinal trajectory contain "ESTIMAND_D".
- **Remediation Completed:** Formally disambiguated the estimands into C1 (EHR Diagnosis), C2 (Community Survey), D1 (Facility Attenders), and D2 (Longitudinal Trajectory).

### Finding 4 (Low): Uniform Survey Weights in Synthetic Export
- **Severity:** LOW
- **Component:** `synapse_simulator/datagen/community_assessment.py:111, 148`
- **Description:** The community survey exports uniform survey weights ($w = 1.0$) because the sampling rate is 100%. Complex survey design elements (strata, primary sampling units) are not yet emitted in the synthetic schema.

---

## 6. Verification of Determinism and Reproducibility

1. **Hash Independence:** Verified that `CommunityAssessmentGenerator` derives its per-patient PRNG using isolated seeds (`f"{self.base_seed}_comm_eval_{pid}"`). Because Python 3 hashes strings using `sha512` internally during `random.seed()`, results are bit-for-bit identical across processes with differing `PYTHONHASHSEED`.
2. **Order Independence:** Verified that adding, removing, or re-ordering unrelated patients in the patient dictionary has zero effect on any existing patient's assessment values.
3. **Seed Sensitivity:** Verified that varying `base_seed` alters stochastic blood pressure draws while strictly preserving physiological invariants ($PP \ge 20$ mmHg, $SBP > DBP$).

---

## 7. Audit Conclusion & Future Calibration Roadmap

The Independent Community Health Assessment Pathway is **ready for comparative evaluation against genuine authorized epidemiological reference data**. 

| Milestone | Status | Governance Constraint |
| :--- | :---: | :--- |
| **Architectural Separation** | COMPLETED | Community survey and clinical EHR tables remain strictly decoupled. |
| **Estimand Disambiguation** | COMPLETED | Five distinct estimands formally defined and audited. |
| **Reproducibility Testing** | COMPLETED | 10 dedicated audit unit tests added; full 223-test suite passing. |
| **External Validation Gate** | PENDING | Retain `REFERENCE_DATA_PENDING` until authorized microdata are ingested. |
| **Age-Trend Calibration** | FUTURE | Calibrate vascular stiffening against genuine LASI Wave 1 reference data. |
