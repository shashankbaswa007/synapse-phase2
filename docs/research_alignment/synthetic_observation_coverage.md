# Synthetic Observation Availability and Coverage Audit

**Project:** SYNAPSE Phase 2 — Synthetic Healthcare Data Generation and Evaluation  
**Document ID:** `DOC-RES-LASI-008`  
**Evaluation Scope:** Metric-by-Metric Audit of Patient Denominators, Observation Counts, Exclusions, and Pseudoreplication  
**Date:** 2026-10-21  
**Target Cohort:** [`data/evaluation/lasi_cohort_500/seed_42`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42) ($N = 2,200$ simulated individuals)  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary

This audit establishes transparent accounting for all synthetic patient denominators, observation yields, missingness rates, exclusion criteria, and stratum coverage across the 10 LASI-relevant evaluation metrics. Crucially, it resolves the distinction between **patient-level sample size** and **longitudinal observation counts**, establishing guidelines to prevent accidental pseudoreplication when comparing synthetic EHR-style time series against cross-sectional survey microdata.

---

## 2. Metric-by-Metric Observation Coverage Table

The table below documents patient-level denominators, observation counts, exclusions, missingness rates, stratum coverage, and gate satisfaction for [`data/evaluation/lasi_cohort_500/seed_42`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42):

| Metric ID | Metric Name | Category | Total Syn Patients | Eligible Patients | Usable Observations | Usable Patients | Excluded Patients (Reason) | Missingness Rate | Populated Strata (of 8) | Gate Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| `lasi_demo_age_older_adult` | Older Adult Age Distribution | DEMO | 2,200 | 575 | 575 | 575 | 1,625 (Age < 45) | 0.0% | 8 / 8 | **PASS** |
| `lasi_demo_sex_female_pct` | Proportion Female (Age $\ge 45$) | DEMO | 2,200 | 575 | 575 | 575 | 1,625 (Age < 45) | 0.0% | 8 / 8 | **PASS** |
| `lasi_demo_pop_a_non_comparable` | Population A Check (< 45) | DEMO | 2,200 | 1,432 | 1,432 | 1,432 | 768 (Age < 20 or $\ge 45$) | 0.0% | N/A | **NOT_COMPARABLE** |
| `lasi_bp_sbp_distribution` | Continuous SBP Distribution | BP | 2,200 | 575 | 863 | 235 | 340 (No HTN visits); 1,625 (< 45) | 59.1% (General $\ge 45$) | 8 / 8 | **PASS** |
| `lasi_bp_sbp_standardized_mean` | Directly Standardized Mean SBP | BP | 2,200 | 575 | 863 | 235 | 340 (No HTN visits); 1,625 (< 45) | 59.1% (General $\ge 45$) | 8 / 8 | **PASS** |
| `lasi_bp_dbp_distribution` | Continuous DBP Distribution | BP | 2,200 | 575 | 0 | 0 | 575 (DBP state not in module) | 100.0% | 0 / 8 | **INSUFFICIENT_SAMPLE_SIZE** |
| `lasi_lab_hba1c_distribution` | Continuous HbA1c Distribution | LAB | 2,200 | 575 | 506 | 78 | 497 (No T2D visits); 1,625 (< 45) | 86.4% (General $\ge 45$) | 8 / 8 | **UNVERIFIED** (Assay Mismatch) |
| `lasi_lab_hba1c_clinical_categories` | HbA1c Control Categories | LAB | 2,200 | 575 | 506 | 78 | 497 (No T2D visits); 1,625 (< 45) | 86.4% (General $\ge 45$) | 8 / 8 | **UNVERIFIED** (Assay Mismatch) |
| `lasi_prev_htn_older_adult` | Hypertension Prevalence ($\ge 45$) | PREV | 2,200 | 575 | 575 | 575 (235 Pos) | 1,625 (Age < 45) | 0.0% | 8 / 8 | **WARNING** (Prevalence vs Fixture) |
| `lasi_prev_t2d_older_adult` | Type 2 Diabetes Prevalence ($\ge 45$) | PREV | 2,200 | 575 | 575 | 575 (79 Pos) | 1,625 (Age < 45) | 0.0% | 8 / 8 | **WARNING** (Prevalence vs Fixture) |

---

## 3. Stratum-Level Population Breakdown

The Census SRS 2021 older adult standardization scheme defines 8 distinct demographic strata ($2 \times 4$: Sex $\times$ 10-year age groups). The table below verifies that all 8 strata are robustly populated in [`data/evaluation/lasi_cohort_500/seed_42`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42):

| Stratum Code | Gender | Age Range | Synthetic Older Adult Count | Fraction of Cohort | Census SRS 2021 Reference Weight | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Female_45-54` | Female | 45–54 | 103 | 17.91% | 0.2010 (20.10%) | Robustly Populated |
| `Female_55-64` | Female | 55–64 | 99 | 17.22% | 0.1650 (16.50%) | Robustly Populated |
| `Female_65-74` | Female | 65–74 | 18 | 3.13% | 0.0950 (9.50%) | Populated |
| `Female_75+` | Female | $\ge 75$ | 56 | 9.74% | 0.0490 (4.90%) | Robustly Populated |
| `Male_45-54` | Male | 45–54 | 102 | 17.74% | 0.2100 (21.00%) | Robustly Populated |
| `Male_55-64` | Male | 55–64 | 112 | 19.48% | 0.1580 (15.80%) | Robustly Populated |
| `Male_65-74` | Male | 65–74 | 22 | 3.83% | 0.0820 (8.20%) | Populated |
| `Male_75+` | Male | $\ge 75$ | 63 | 10.96% | 0.0400 (4.00%) | Robustly Populated |
| **Total Older Adults** | — | **$\ge 45$** | **575** | **100.00%** | **1.0000 (100.00%)** | **8 / 8 Complete** |

---

## 4. Methodological Distinction: Observation Counts vs. Patient Counts

### 4.1 The Risk of Accidental Pseudoreplication
A critical methodological trap when evaluating synthetic EHR datasets against cross-sectional population health surveys is **pseudoreplication**:
* In **LASI Wave 1 microdata**, each survey respondent represents a single biological individual sampled at one point in time. The recorded vital signs represent a protocolized cross-sectional measurement (mean of 2nd and 3rd readings).
* In **SYNAPSE simulation output**, synthetic patients with chronic diseases (e.g., diagnosed hypertension or type 2 diabetes) undergo longitudinal monitoring, generating multiple clinical encounters over the 720-day observation window:
  - **SBP Observations:** 863 measurements generated across 235 distinct patients (mean $3.67$ observations per patient, min 1, max 4).
  - **HbA1c Observations:** 506 measurements generated across 78 distinct patients (mean $6.49$ observations per patient, min 2, max 7).

### 4.2 Impact on Distributional Statistics
If longitudinal encounters are pooled naively into an empirical continuous distribution:
1. **Artificially Narrowed Standard Errors:** Treating 863 repeated observations as 863 independent individuals underestimates true population sampling variance by a factor of approximately $\sqrt{3.67} \approx 1.92$.
2. **Clinical Severity Weighting:** Patients with severe, uncontrolled disease or high visit frequencies generate more observations than well-controlled or non-adherent patients, skewing the distribution towards sick encounters rather than patient prevalence.

### 4.3 Evaluator Architecture Safeguards
In [`synapse_simulator.evaluation.lasi.evaluator.LasiExternalEvaluator`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py):
1. **Sample Size Gating:** The evaluator explicitly requires $N_{\text{patients}} \ge 30$ and $N_{\text{observations}} \ge 30$.
2. **Explicit Population Scope:** The evaluation report explicitly notes in its metadata whether distributions are computed across longitudinal encounters or patient-level averages.
3. **Survey Weighting & Kish Effective Sample Size:** Reference survey estimates incorporate complex design weights ($n_{\text{eff}} = 48.94$ in test fixture), preventing artificial precision claims.

---

## 5. Summary of Gating and Exclusion Verification

1. **Older-Adult Sample Size Requirement ($N \ge 500$):** Fully satisfied ($N = 575 \ge 500$).
2. **Metric-Level Sample Size Gating ($N \ge 30$):** Satisfied for SBP ($863 \ge 30$), HbA1c ($506 \ge 30$), HTN ($575 \ge 50$), and T2D ($575 \ge 50$).
3. **DBP Gating:** Correctly identified as missing ($N = 0$) and gated out as `INSUFFICIENT_SAMPLE_SIZE`.
4. **HbA1c Assay Non-Equivalence Gating:** Correctly flagged and gated out as `UNVERIFIED`.
5. **Prevalence Gate Status:** Evaluated with design-adjusted Wilson score intervals and assigned `WARNING` against fixture prevalence.
6. **Overall Gate Status:** Preserved at **`REFERENCE_DATA_PENDING`** until authorized genuine microdata is ingested.
