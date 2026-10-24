# Hypertension Status Semantics and Denominator Audit

## 1. Executive Summary

This audit establishes the formal semantics of hypertension disease status and evaluates the denominators used for population-level prevalence metrics in SYNAPSE Phase 2.

In epidemiological and clinical informatics evaluation, a critical distinction must be maintained between:
1. **The underlying biological state of the individual** (latent truth).
2. **The objective physical measurements observed** (vital signs).
3. **The formal diagnostic recognition recorded in the health system** (EHR chart).
4. **The pharmacological interventions initiated** (prescriptions).
5. **The unobserved or missing disease status** (unassessable).

Prior audits identified that previous implementations conflated missing blood pressure measurements with normal blood pressure by evaluating measurement-defined hypertension over the total older adult population ($N = 575$) instead of the assessable subset ($N = 235$), which falsely treated $340$ unmeasured individuals as normotensive. This document corrects that defect, defines the five distinct prevalence estimands, and documents the statistical safeguards that prevent false-negative misclassification.

---

## 2. Disease-Status Semantics Matrix

The table below delineates the five distinct representations of hypertension in SYNAPSE Phase 2:

| Dimension | System Representation | Data Source | Clinical & Epidemiological Meaning | Mutability & Visibility |
| :--- | :--- | :--- | :--- | :--- |
| **1. Modeled Latent Disease State** | `PatientContext.latent_conditions["I10"]` | Simulation State | True biological presence of elevated vascular resistance and arterial hypertension in the simulated individual. | Ground truth in simulation engine. Not visible to health system until clinical recognition. |
| **2. EHR-Recorded Diagnosis** | `conditions.condition_code == 'I10'` | [`conditions.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/conditions.csv) | Formal ICD-10 medical diagnosis entered into the outpatient electronic medical record by an attending physician during an encounter. | Observable in EHR. Requires clinical presentation and diagnostic evaluation (`recognized = True`). |
| **3. Measurement-Defined Hypertension** | $\text{SBP} \ge 140\text{ mmHg} \lor \text{DBP} \ge 90\text{ mmHg} \lor \text{Rx}$ | [`observations.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/observations.csv) or [`community_assessments.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/community_assessments.csv) | Objective fulfillment of the clinical consensus case definition (JNC-7 / Indian Guidelines on Hypertension IV) from physical measurements. | Empirical observation. Requires assessable vital signs or known prescription history. |
| **4. Medication / Treatment Status** | `medications.drug_name` in antihypertensive class | [`medications.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/medications.csv) | Active prescription of antihypertensive agent (Amlodipine, Telmisartan, Enalapril, Losartan, Atenolol). | Observable in pharmacy dispense logs. Indicates treated status. |
| **5. Unassessable / Missing Status** | Absence of BP observations and absence of antihypertensive Rx | Null in observations / medications | Individual has no recorded vital signs or treatment history in the evaluation window. | **Cannot be classified as negative.** Formally coded as `UNKNOWN` / `UNASSESSABLE`. |

---

## 3. Audit of the Five Distinct Prevalence Estimands

To provide scientifically rigorous population health evaluation, SYNAPSE Phase 2 audits five distinct prevalence metrics:

```
+-----------------------------------------------------------------------------------------------------------------+
|                               TOTAL OLDER ADULT POPULATION (Age >= 45): N = 575                                 |
+-------------------------------------------------------+---------------------------------------------------------+
|        CLINICALLY ASSESSABLE SUBSET: N = 235          |            CLINICALLY UNASSESSABLE: N = 340             |
|          (Has valid clinical BP or Rx)                |            (No BP readings, No prescriptions)           |
+-------------------------------------------------------+---------------------------------------------------------+
| - Hypertensive by Measurement / Rx: N = 235 (100.0%)  | - Disease status cannot be ruled out.                   |
| - Diagnosed with ICD-10 I10 in EHR: N = 235 (100.0%)  | - Formally classified as UNASSESSABLE under Estimand E. |
+-------------------------------------------------------+---------------------------------------------------------+
|            FACILITY ATTENDERS (>= 1 Encounter): N = 485  |  Zero Encounters (Never visited clinic): N = 90      |
|               Hypertension Diagnosis: N = 235 (48.45%)   |     Zero Diagnoses, Zero Vital Signs                 |
+----------------------------------------------------------+------------------------------------------------------+
|            INDEPENDENT COMMUNITY ASSESSMENT SWEEP: N = 561 (Alive at survey sweep)                              |
|                 Survey-Measured Hypertension (SBP >= 140 | DBP >= 90 | Rx): N = 234 (41.71%)                    |
+-----------------------------------------------------------------------------------------------------------------+
```

### Estimand A: EHR-Recorded Hypertension Diagnosis Prevalence
- **Metric ID:** `lasi_prev_htn_older_adult`
- **Case Definition:** Patient has diagnostic code `I10` in [`conditions.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/conditions.csv).
- **Target Population:** All community-dwelling older adults aged $\ge 45$.
- **Denominator:** Total eligible older adults ($N_{\text{older}} = 575$).
- **Numerator:** Patients with documented `I10` diagnosis ($N = 235$).
- **Synthetic Estimate:** **$40.87\%$** ($95\%\text{ Wilson CI}: [36.89\%, 44.98\%]$).
- **Reference Fixture:** $79.73\%$ ($95\%\text{ CI}: [66.86\%, 88.52\%]$).
- **Difference:** $-38.86\%$.
- **Clinical Interpretation:** Measures the formal diagnostic capture of the healthcare system. An individual without an EHR diagnosis is considered undiagnosed in the clinical chart, but not necessarily free of latent biological disease.

### Estimand B: Measurement-Defined Hypertension Prevalence Among Assessable Participants
- **Metric ID:** `lasi_prev_measurement_defined_htn_older_adult`
- **Approved Case Definition:**
  $$\text{Index SBP} \ge 140\text{ mmHg} \lor \text{Index DBP} \ge 90\text{ mmHg} \lor \text{Currently prescribed antihypertensive medication}$$
- **Target Population:** Older adults with assessable clinical blood pressure or medication status.
- **Denominator:** Strictly assessable older adults ($N_{\text{assessable}} = 235$).
- **Numerator:** Assessable older adults meeting the case definition ($N = 235$).
- **Synthetic Estimate:** **$100.00\%$** ($95\%\text{ Wilson CI}: [98.40\%, 100.00\%]$).
- **Reference Fixture:** $79.73\%$.
- **Difference:** $+20.27\%$.
- **Methodological Rule:** The $340$ older adults lacking clinical measurements are **excluded from this denominator**. They are NOT classified as negative.

### Estimand C: Community-Assessment Hypertension Prevalence
- **Metric ID:** `lasi_prev_htn_community_assessment`
- **Approved Case Definition:**
  $$\text{Community SBP} \ge 140\text{ mmHg} \lor \text{Community DBP} \ge 90\text{ mmHg} \lor \text{Taking antihypertensive medication}$$
- **Target Population:** Community older adults surveyed in the independent assessment sweep.
- **Denominator:** Older adults assessed in community survey ($N_{\text{comm assessable}} = 561$ alive at survey window).
- **Numerator:** Community-assessed older adults meeting the case definition ($N = 234$).
- **Synthetic Estimate:** **$41.71\%$** ($95\%\text{ Wilson CI}: [37.68\%, 45.86\%]$).
- **Reference Fixture:** $79.73\%$.
- **Difference:** $-38.02\%$.
- **Clinical Interpretation:** Reflects true population-level disease burden in the community, capturing both normotensive and hypertensive individuals without facility-based healthcare-seeking bias.

### Estimand D: Hypertension Prevalence Among Clinical Facility Attenders
- **Metric ID:** `lasi_prev_htn_clinical_attenders`
- **Case Definition:** Documented diagnosis of `I10` in patients who attended healthcare facilities.
- **Target Population:** Older adults who attended at least one clinical encounter in [`encounters.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/encounters.csv).
- **Denominator:** Older adult facility attenders ($N_{\text{attenders}} = 485$).
- **Numerator:** Facility attenders diagnosed with hypertension ($N = 235$).
- **Synthetic Estimate:** **$48.45\%$** ($95\%\text{ Wilson CI}: [44.02\%, 52.92\%]$).
- **Difference:** N/A (Facility diagnostic benchmark).
- **Clinical Interpretation:** Quantifies healthcare-seeking selection bias: individuals presenting to outpatient facilities exhibit higher hypertension prevalence ($48.45\%$) than the general population ($40.87\%$).

### Estimand E: Unknown or Unassessable Hypertension Status Rate
- **Metric ID:** `lasi_prev_htn_unassessable_status`
- **Definition:** Older adults with neither clinical vital signs nor antihypertensive prescriptions.
- **Target Population:** All community older adults aged $\ge 45$.
- **Denominator:** Total older adults ($N_{\text{older}} = 575$).
- **Numerator:** Unmeasured older adults with zero BP records and zero prescriptions ($N = 340$).
- **Synthetic Estimate:** **$59.13\%$** ($95\%\text{ Wilson CI}: [55.06\%, 63.09\%]$).
- **Status:** **PASS** (Statistical diagnostic safeguard).
- **Clinical Interpretation:** Formally records that $59.13\%$ of older adults cannot be assessed from hospital EHR records alone, guarding against false-negative imputation.

---

## 4. Denominator & Sample Count Audit Table

| Estimand Code | Estimand Label | Target Population | Denominator Description | Denominator ($N$) | Numerator ($n$) | Prevalence (%) | 95% Wilson CI |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **A** | EHR-Recorded Diagnosis | All older adults ($\ge 45$) | All simulated older adults | **575** | **235** | **40.87%** | [36.89%, 44.98%] |
| **B** | Measurement-Defined (Assessable) | Clinical assessable cohort | Older adults with clinical BP or Rx | **235** | **235** | **100.00%** | [98.40%, 100.00%] |
| **C** | Community Health Assessment | General community survey | Assessed community older adults | **561** | **234** | **41.71%** | [37.68%, 45.86%] |
| **D** | Clinical Facility Attenders | Outpatient clinic attenders | Older adults with $\ge 1$ encounter | **485** | **235** | **48.45%** | [44.02%, 52.92%] |
| **E** | Unassessable Missing Status | All older adults ($\ge 45$) | All simulated older adults | **575** | **340** | **59.13%** | [55.06%, 63.09%] |

---

## 5. Statistical Safeguards Against False-Negative Imputation

In real-world epidemiological studies (e.g., NHANES, LASI, ICMR-INDIAB), failure to attend a clinic or missingness in an administrative dataset cannot be taken as evidence that the patient is healthy. The following statistical safeguards are permanently embedded in the codebase:

1. **Explicit Null Representation:** In [`synapse_simulator/evaluation/lasi/evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py), missing vital sign observations remain `None` and are never imputed as $0.0$ or normal values ($120/80\text{ mmHg}$).
2. **Restricted Assessable Denominator:** Estimand B evaluates measurement-defined prevalence exclusively over `n_assessable`, preventing the $340$ unmeasured individuals from falsely inflating the denominator and depressing the prevalence estimate.
3. **Mandatory Missingness Reporting:** Estimand E actively audits and displays the unassessable fraction in the main evaluation report table ([`LASI_EVALUATION_REPORT.md`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/LASI_EVALUATION_REPORT.md)).
4. **Independent Assessment Decoupling:** The community assessment layer provides an unselected denominator ($N = 561$) where normotensive individuals have explicitly measured blood pressure readings ($110 - 135\text{ mmHg}$), completely eliminating the need for imputation.
