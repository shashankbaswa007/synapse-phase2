# SYNAPSE Phase 2: LASI Wave 1 External Evaluation Report

**Evaluation Timestamp:** `2026-10-21T19:31:27.642578`  
**Synthetic Cohort Directory:** `/Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_101`  
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

## 3. Quantitative Evaluation Metrics Table

| Metric ID | Metric Name | Category | Pop | Syn N | Ref N (Eff N) | Syn Est | Ref Est | Diff | KS Stat | W1 Dist | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `lasi_demo_age_older_adult` | Older Adult Age Distribution (Age >= 45) | DEMOGRAPHICS | B (>=45) | 553 | 50 (48.9) | 61.93 | 64.30 | -2.38 | 0.193 | 4.83 | **PASS** |
| `lasi_demo_sex_female_pct` | Proportion Female Among Older Adults (Age >= 45) | DEMOGRAPHICS | B (>=45) | 553 | 50 (48.9) | 47.38 | 54.00 | -6.62 | — | — | **PASS** |
| `lasi_demo_pop_a_non_comparable` | Population A General Adults (< 45) Comparability Check | DEMOGRAPHICS | A (>=20) | 1451 | 50 | 43.10 | N/A | N/A | — | — | **NOT_COMPARABLE** |
| `lasi_bp_sbp_distribution` | Systolic Blood Pressure Continuous Distribution | BLOOD_PRESSURE | B (>=45) | 751 | 50 (48.9) | 146.15 | 148.51 | -2.36 | 0.063 | 0.95 | **PASS** |
| `lasi_bp_sbp_standardized_mean` | Directly Standardized Mean SBP (Census SRS Standard) | BLOOD_PRESSURE | B (>=45) | 751 | 50 (48.9) | 146.04 | 141.49 | +4.55 | — | — | **PASS** |
| `lasi_bp_dbp_distribution` | Diastolic Blood Pressure Continuous Distribution | BLOOD_PRESSURE | B (>=45) | 0 | 50 (48.9) | 0.00 | 86.60 | N/A | — | — | **INSUFFICIENT_SAMPLE_SIZE** |
| `lasi_lab_hba1c_distribution` | HbA1c Distribution Among Older Adults | HBA1C | B (>=45) | 478 | 49 | 7.91 | 7.14 | +0.78 | 0.290 | 0.78 | **UNVERIFIED** |
| `lasi_lab_hba1c_clinical_categories` | HbA1c Clinical Control Categories (<7%, 7-8%, >8%) | HBA1C | B (>=45) | 478 | 49 | 0.26 | 0.00 | +0.26 | — | — | **UNVERIFIED** |
| `lasi_prev_htn_older_adult` | Hypertension Prevalence Among Older Adults (Age >= 45) | PREVALENCE | B (>=45) | 553 | 50 (48.9) | 36.53 | 79.73 | -43.20 | — | — | **WARNING** |
| `lasi_prev_t2d_older_adult` | Type 2 Diabetes Prevalence Among Older Adults (Age >= 45) | PREVALENCE | B (>=45) | 553 | 50 (48.9) | 14.47 | 56.00 | -41.53 | — | — | **WARNING** |

---

## 4. Population Comparability & Standardization Analysis

### Population A (General Adults >= 20) vs Population B (Older Adults >= 45)
- **Population A Finding:** LASI Wave 1 is fundamentally an older-adult cohort (>= 45 years). Younger spouses represent < 2% of respondents and are not nationally representative.
  Direct comparison of SYNAPSE general adult population (< 45) to LASI is clinically and methodologically **NOT COMPARABLE**.
- **Population B Alignment:** When truncated to age >= 45, SYNAPSE synthetic records can be matched directly against LASI survey observations.
- **Direct Age-Sex Standardization:** Census SRS 2021 older adult population distribution weights (8 strata) were applied to control for differential survival and sampling pyramids between synthetic discrete-event simulations and real-world surveys.

---

## 5. Methodological Limitations & Explicit Disclosures

- EVALUATION EXECUTED AGAINST STRUCTURAL TEST FIXTURE (NOT REAL LASI MICRODATA). Genuine external evaluation remains pending receipt of credentialed microdata via IIPS / Gateway to Global Aging Data.
- LASI Wave 1 reference cohort is restricted to adults aged >= 45 and resident spouses.
- Comparisons of general adult synthetic populations (age < 45) to LASI are methodologically non-comparable.
- Thresholds of KS <= 0.08 and Wasserstein <= 4.0 mmHg are provisional pending formal epidemiological consensus.
- Agreement on cross-sectional disease prevalence does NOT establish correct disease incidence, duration, or progression.
- Dried Blood Spot (DBS) HbA1c conversion to venous HPLC is disabled by default due to lack of validated Indian LASI calibration.

---

**Report Integrity Signature:** Generated deterministically by `LasiExternalEvaluator` in SYNAPSE Phase 2.