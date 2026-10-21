# SYNAPSE Phase 2: LASI Wave 1 External Evaluation Report

**Evaluation Timestamp:** `2026-10-21T20:00:42.909308`  
**Synthetic Cohort Directory:** `/Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42`  
**Reference Source File:** `data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`  
**Reference File SHA-256:** `f3e3b7a440cd743fb7b02c091bb4fe6ddefb96f907da0ce7a6875c6cd759d5a2`  
**Reference Source Type:** `SYNTHETIC_TEST_FIXTURE`  
**Overall Gate Verdict:** **REFERENCE_DATA_PENDING**  
**Calibration Leakage Veto:** **PASSED (No Calibration Leakage)**  

---

## 1. Regulatory Status and Data Access Disclosure

> [!IMPORTANT]
> **NOTICE OF PENDING EXTERNAL VALIDATION**
> This evaluation was executed against a small, clearly labeled **structural verification test fixture** (`SYNTHETIC_TEST_FIXTURE`).
> Genuine LASI Wave 1 reference microdata is governed by the International Institute for Population Sciences (IIPS) and
> Gateway to Global Aging Data (g2aging.org), requiring formal registration and an executed Data Use Agreement (DUA).
> In compliance with research governance rules, no real data was fabricated or substituted.
> **External evaluation against real-world LASI observations remains formally REFERENCE_DATA_PENDING.**

## 2. Ingestion & Data Quality Audit

- **Total Records Ingested:** `50`
- **Duplicate Records Detected/Removed:** `0`
- **Valid Analysis Records:** `50`
- **Excluded Records (Missing/Out of Range):** `0`
- **Survey Weights Coverage:** `100.0%` (Weights Present)
- **Kish Effective Sample Size (n_eff):** `48.94` (Weighting DEFF: `1.022`)
- **Sampling Strata & PSU Captured:** `Strata: True, PSU: True`
- **Blood Pressure Derivation Breakdown:** `{'PROTOCOL_MEAN_READINGS_2_AND_3': 50, 'FALLBACK_READING_2_ONLY': 0, 'FALLBACK_READING_3_ONLY': 0, 'FALLBACK_READING_1_ONLY': 0, 'NO_VALID_READING': 0}`

### Biological & Vital Sign Ranges in Reference Dataset

- **Age (Years):** Mean `62.9`, Range `[45.0, 83.0]`
- **Systolic Blood Pressure (mmHg):** Mean `146.8`, Range `[121.0, 169.0]` (Valid: `50.0`)
- **Diastolic Blood Pressure (mmHg):** Mean `86.6`, Range `[74.0, 97.0]` (Valid: `50.0`)
- **HbA1c (%):** Mean `7.14`, Range `[5.3, 8.9]` (Valid: `49.0`)

---

## 3. Blood Pressure Paired Pathway & Estimand Audit

- **Index Selection Rule:** `First eligible blood pressure measurement encounter (earliest timestamp)`
- **Total Synthetic Population:** `2200`
- **Eligible Older Adults (Age >= 45):** `575`
- **Patients with >= 1 Valid Paired Measurement:** `235`
- **Total Clinical BP Encounters:** `852`
- **Total Longitudinal SBP Observations:** `852`
- **Total Longitudinal DBP Observations:** `852`
- **Total Paired Observations (Same Encounter & Timestamp):** `852`
- **Patients with Only SBP or Only DBP:** `SBP Only: 0, DBP Only: 0`
- **Implausible Pulse Pressure Count (PP < 20 or PP > 110 or SBP <= DBP):** `0`
- **Unmeasured Rate Across Older Adults:** `59.13%`

### Evaluation Estimands Breakdown
- **Estimand A (Cross-Sectional Distribution):** Patient-level index BP (1 per patient) evaluated against LASI survey readings.
- **Estimand B (Measurement-Defined Prevalence):** Criteria: Index SBP >= 140 OR Index DBP >= 90 OR on antihypertensive Rx.
- **Estimand C (EHR-Recorded Diagnosis):** Diagnostic ICD-10 `I10` condition records in synthetic EHR.
- **Estimand D (Longitudinal Trajectory):** Multi-visit trajectory response over time (marked UNVERIFIED for single-wave LASI).

---

## 4. Quantitative Evaluation Metrics Table

| Metric ID | Metric Name | Category | Pop | Syn N | Ref N (Eff N) | Syn Est | Ref Est | Diff | KS Stat | W1 Dist | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `lasi_demo_age_older_adult` | Older Adult Age Distribution (Age >= 45) | DEMOGRAPHICS | B (>=45) | 575 | 50 (48.9) | 62.49 | 64.30 | -1.81 | 0.165 | 4.96 | **PASS** |
| `lasi_demo_sex_female_pct` | Proportion Female Among Older Adults (Age >= 45) | DEMOGRAPHICS | B (>=45) | 575 | 50 (48.9) | 48.00 | 54.00 | -6.00 | — | — | **PASS** |
| `lasi_demo_pop_a_non_comparable` | Population A General Adults (< 45) Comparability Check | DEMOGRAPHICS | A (>=20) | 1432 | 50 | 44.19 | N/A | N/A | — | — | **NOT_COMPARABLE** |
| `lasi_bp_sbp_distribution` | Patient-Level Index Systolic Blood Pressure Continuous Distribution | BLOOD_PRESSURE | B (>=45) | 235 | 50 (48.9) | 156.44 | 148.51 | +7.93 | 0.431 | 9.71 | **WARNING** |
| `lasi_bp_sbp_standardized_mean` | Directly Standardized Mean Index SBP (Census SRS Standard) | BLOOD_PRESSURE | B (>=45) | 235 | 50 (48.9) | 156.45 | 141.49 | +14.96 | — | — | **WARNING** |
| `lasi_bp_dbp_distribution` | Patient-Level Index Diastolic Blood Pressure Continuous Distribution | BLOOD_PRESSURE | B (>=45) | 235 | 50 (48.9) | 96.89 | 87.36 | +9.53 | 0.752 | 10.29 | **WARNING** |
| `lasi_bp_dbp_standardized_mean` | Directly Standardized Mean Index DBP (Census SRS Standard) | BLOOD_PRESSURE | B (>=45) | 235 | 50 (48.9) | 96.88 | 84.26 | +12.62 | — | — | **WARNING** |
| `lasi_bp_pulse_pressure_distribution` | Index Pulse Pressure Continuous Distribution (PP = SBP - DBP) | BLOOD_PRESSURE | B (>=45) | 235 | 50 | 59.55 | 60.18 | -0.63 | 0.115 | 1.23 | **WARNING** |
| `lasi_prev_measurement_defined_htn_older_adult` | Measurement-Defined Hypertension Prevalence (Index SBP>=140 | DBP>=90 | Rx) | PREVALENCE | B (>=45) | 575 | 50 (48.9) | 40.87 | 79.73 | -38.86 | — | — | **WARNING** |
| `lasi_bp_longitudinal_trajectory_treatment_response` | Longitudinal BP Treatment Response Trajectory (Mean Delta SBP) | BLOOD_PRESSURE | B (>=45) | 229 | 50 | -14.47 | N/A | N/A | — | — | **UNVERIFIED** |
| `lasi_lab_hba1c_distribution` | HbA1c Distribution Among Older Adults | HBA1C | B (>=45) | 506 | 49 | 7.89 | 7.14 | +0.75 | 0.266 | 0.75 | **UNVERIFIED** |
| `lasi_lab_hba1c_clinical_categories` | HbA1c Clinical Control Categories (<7%, 7-8%, >8%) | HBA1C | B (>=45) | 506 | 49 | 0.27 | 0.00 | +0.27 | — | — | **UNVERIFIED** |
| `lasi_prev_htn_older_adult` | Hypertension Prevalence Among Older Adults (Age >= 45) | PREVALENCE | B (>=45) | 575 | 50 (48.9) | 40.87 | 79.73 | -38.86 | — | — | **WARNING** |
| `lasi_prev_t2d_older_adult` | Type 2 Diabetes Prevalence Among Older Adults (Age >= 45) | PREVALENCE | B (>=45) | 575 | 50 (48.9) | 14.43 | 56.00 | -41.57 | — | — | **WARNING** |

---

## 5. Population Comparability & Standardization Analysis

### Population A (General Adults >= 20) vs Population B (Older Adults >= 45)
- **Population A Finding:** LASI Wave 1 is fundamentally an older-adult cohort (>= 45 years). Younger spouses represent < 2% of respondents and are not nationally representative.
  Direct comparison of SYNAPSE general adult population (< 45) to LASI is clinically and methodologically **NOT COMPARABLE**.
- **Population B Alignment:** When truncated to age >= 45, SYNAPSE synthetic records can be matched directly against LASI survey observations.
- **Direct Age-Sex Standardization:** Census SRS 2021 older adult population distribution weights (8 strata) were applied to control for differential survival and sampling pyramids between synthetic discrete-event simulations and real-world surveys.

---

## 6. Methodological Limitations & Explicit Disclosures

- EVALUATION EXECUTED AGAINST STRUCTURAL TEST FIXTURE (NOT REAL LASI MICRODATA). Genuine external evaluation remains pending receipt of credentialed microdata via IIPS / Gateway to Global Aging Data.
- LASI Wave 1 reference cohort is restricted to adults aged >= 45 and resident spouses.
- Comparisons of general adult synthetic populations (age < 45) to LASI are methodologically non-comparable.
- Thresholds of KS <= 0.08 and Wasserstein <= 4.0 mmHg are provisional pending formal epidemiological consensus.
- Agreement on cross-sectional disease prevalence does NOT establish correct disease incidence, duration, or progression.
- Dried Blood Spot (DBS) HbA1c conversion to venous HPLC is disabled by default due to lack of validated Indian LASI calibration.

---

**Report Integrity Signature:** Generated deterministically by `LasiExternalEvaluator` in SYNAPSE Phase 2.