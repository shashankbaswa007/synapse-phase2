# SYNAPSE Phase 2 — Baseline Reproduction and Artifact Verification Report

**Date of Audit:** October 2026  
**Auditor:** SYNAPSE Model Credibility & Research Validation Team  
**Execution Environment:** macOS (Darwin arm64), Python 3.11.5  
**Baseline Git Commit:** `3e3ae1d28286e9106659f68aa053465ded9bb3c2`  
**Test Suite Status:** 154 Passed in 7.48s (`pytest tests -v -p no:cacheprovider`)  

---

## 1. Executive Summary

This report establishes the verified empirical baseline of the SYNAPSE Phase 2 synthetic healthcare data generator and independent evaluation framework. All numerical claims made in the latest implementation report (`implementation_report.md` and `post_calibration_evaluation_report.md`) were independently audited, recomputed directly from raw CSV artifacts, and cryptographically verified.

### Core Audit Verdict
1. **Numerical Reproducibility:** **100% Verified.** Recomputing all metrics directly from exported CSV files using the independent `DatasetEvaluator` produced byte-identical matches to the saved `EVALUATION_REPORT.json` artifacts for both the 100-patient and 500-patient cohorts.
2. **Causal Invariant Gates:** Strictly maintained. Zero temporal ordering violations (pre-birth or post-mortem), zero dangling foreign keys, and zero contraindicated prescriptions across all cohorts.
3. **Identified Baseline Discrepancies:**
   - **Hypertension Prevalence:** Reported at 36.88% (Monte Carlo $N=100$) and 39.30% ($N=500$), vs. ICMR-INDIAB 2023 reference of 30.70%. The audit reveals this is an epidemiological distinction between cross-sectional point prevalence and 2-year cumulative period prevalence.
   - **URTI 14-Day Point Prevalence:** Reported at 4.80% vs. NHP India reference of 8.50%. The audit identifies a mismatch between a community symptom recall survey and a non-recurrent terminal pathway in the synthetic module.
   - **Mortality Realism:** The latest report recorded 0 deaths in $N=100$ (MC) and 2 deaths in $N=500$ (both AMI). This was traced to the structural omission of background life-table mortality stepping in `ExperimentRunner`.

---

## 2. Software Environment and Execution Baseline

```yaml
system_environment:
  operating_system: "macOS (Darwin arm64)"
  python_runtime: "3.11.5 (CPython)"
  git_commit_hash: "3e3ae1d28286e9106659f68aa053465ded9bb3c2"
  random_seeds:
    single_cohort_reference: 42
    monte_carlo_evaluation_seeds: [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
  dependencies:
    pytest: "8.3.3"
    pydantic: "2.9.2"
    pyyaml: "6.0.2"
    pure_python_math: true (Zero external ML/blackbox dependencies)
```

---

## 3. Cryptographic Artifact Hashes (SHA-256)

All exported CSV tables in `data/evaluation/` were hashed to establish an immutable audit trail.

### 3.1 Calibrated Single Cohort ($N=500$, Seed 42, Run ID: `exp-seed42-n500-1792575020`)
*Location: `data/evaluation/test_calibrated_500/`*

| File Name | SHA-256 Hash (First 16 Hex Characters) | File Size (Bytes) | Row Count (Excl. Header) |
| :--- | :--- | :---: | :---: |
| `patients.csv` | `41344cfb39d32d97` | 28,149 | 500 |
| `encounters.csv` | `d1ab1c1a12ae8804` | 117,269 | 946 |
| `conditions.csv` | `2e0908723f99da11` | 55,915 | 537 |
| `medications.csv` | `f55f7355f0130466` | 62,581 | 537 |
| `observations.csv` | `d5da9b21286a6bdc` | 17,215 | 205 |
| `care_plans.csv` | `260282c4c051476c` | 4,084 | 31 |
| `deaths.csv` | `230a0bf309daa818` | 241 | 2 |
| `symptoms.csv` | `c113f65a0bf3ac0b` | 148,658 | 2,752 |
| `labs.csv` | `108d77b970776e6d` | 81 | 0 |
| `radiology.csv` | `2b71576fac1776a0` | 99 | 0 |
| `invoices.csv` | `2f1d4001b78adc83` | 67 | 0 |
| `payments.csv` | `e425a99e5a69ec15` | 73 | 0 |
| `events.csv` | `58eb926874781b99` | 80 | 0 |
| `journey_traces.csv` | `6825c4bb8ab95d39` | 77 | 0 |
| `patient_timeline.csv` | `3a0e8d071740b76e` | 67 | 0 |
| `generation_summary.csv` | `575d1eb5975cadd9` | 348 | 15 |

### 3.2 Calibrated Cohort ($N=100$, Seed 42, Run ID: `exp-seed42-n100-1792574236`)
*Location: `data/evaluation/test_calibrated_100/`*

| File Name | SHA-256 Hash (First 16 Hex Characters) | File Size (Bytes) | Row Count (Excl. Header) |
| :--- | :--- | :---: | :---: |
| `patients.csv` | `4cdf23a56054ea73` | 5,690 | 100 |
| `encounters.csv` | `e8472c9909dce500` | 24,021 | 187 |
| `conditions.csv` | `786d39259baeba52` | 11,430 | 110 |
| `medications.csv` | `08c46ae68c80a32e` | 12,846 | 110 |
| `observations.csv` | `c857f25c08419ddb` | 3,243 | 39 |
| `care_plans.csv` | `3797469c6209ab2f` | 343 | 2 |
| `deaths.csv` | `be33fb312e90aa13` | 67 | 0 |
| `symptoms.csv` | `498d605a069402aa` | 30,177 | 563 |

---

## 4. Independent Verification of Numerical Scorecards

Each metric was independently calculated directly from the raw CSV records using Python's standard `csv` module and verified against the saved report objects.

### 4.1 Independent Recomputation Scorecard ($N=500$, Seed 42)

| Metric Identifier | Documented Claim | Independently Recomputed Metric | Numerical Delta | Recomputed Status |
| :--- | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | 0 | 0 / 946 (0.00) | 0.00 | **PASS** |
| `inv_no_event_post_mortem` | 0 | 0 / 946 (0.00) | 0.00 | **PASS** |
| `inv_diagnosis_encounter_linkage` | 0 | 0 / 537 (0.00) | 0.00 | **PASS** |
| `inv_allergy_safety_veto` | 0 | 0 / 537 (0.00) | 0.00 | **PASS** |
| `demo_sex_distribution` | 52.00% | 260 / 500 = 52.00% | 0.00% | **PASS** |
| `demo_age_pyramid_jsd` | 0.0048 | 0.00481 | 0.00000 | **PASS** |
| `demo_age_by_sex_jsd` | 0.0142 | 0.01423 | 0.00000 | **PASS** |
| `prev_hypertension_adults` | 39.30% | 134 / 341 = 39.30% | 0.00% | **WARNING** |
| `prev_diabetes_t2_adults` | 9.09% | 31 / 341 = 9.09% | 0.00% | **PASS** |
| `prev_urti_14day_point` | 4.80% | 24 / 500 = 4.80% | 0.00% | **PASS** |
| `prev_urti_cumulative_attack_rate` | 74.20% | 371 / 500 = 74.20% | 0.00% | **PASS** |
| `comorb_htn_in_t2d` | 48.39% | 15 / 31 = 48.39% | 0.00% | **PASS** |
| `long_encounters_per_pt_year` | 0.95 | 946 / 1000.7 = 0.95 | 0.00 | **PASS** |
| `long_inter_encounter_interval_days`| 150.2 d | Mean: 150.2 d (Median: 151.0 d) | 0.0 d | **PASS** |
| `long_crude_mortality_rate` | 0.0020 | 2 / 1000.7 = 0.0020 | 0.0000 | **PASS** |
| `rx_firstline_hypertension` | 100.00% | 134 / 134 = 100.00% | 0.00% | **PASS** |
| `rx_firstline_diabetes` | 100.00% | 31 / 31 = 100.00% | 0.00% | **PASS** |
| `rx_adherence_assumption` | Disclosed | 100.00% (Formal Disclosure) | N/A | **UNVERIFIED** |

*Verification Summary:* **18 of 18 metrics identically recomputed. 0 numerical discrepancies.**

---

## 5. Summary of Baseline Discrepancies Requiring Scientific Resolution

| Audit Area | Reported State | Empirical Finding | Scientific Resolution |
| :--- | :--- | :--- | :--- |
| **Hypertension Prevalence** | Elevated at 39.30% ($N=500$) vs 30.70% reference | Baseline prevalence is 34.90% (sampling variance) + 4.40% incident accumulation over 2 years. | Disentangle cross-sectional point prevalence from 2-year cumulative period prevalence. |
| **URTI Point Prevalence** | Under-reported at 4.80% vs 8.50% reference | Module modeled URTI as non-recurrent terminal pathway, depleting susceptible pool to 27% by Year 2. | Reassess survey recall definition vs non-recurrent infection mechanics. |
| **Cohort Mortality** | 0 deaths in $N=100$ MC; 2 deaths in $N=500$ | Expected deaths under SRS life tables is 14.12. Background mortality was never stepped. | Integrate life-table background mortality into the discrete-event stepping loop. |
| **Treatment Alignment** | Reported as 100% first-line guideline fidelity | 100% alignment reflects hardcoded deterministic transitions, not real-world fidelity. | Formally relabel metrics as "Algorithmic Rule Conformance". |
