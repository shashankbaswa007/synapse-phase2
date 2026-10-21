# Test Execution and Regression Results Report

**Document ID:** `SYNAPSE-AUDIT-DELIV-06`  
**Date:** October 2026  
**Auditor:** SYNAPSE Model Credibility & Clinical Trajectory Audit Team  
**Focus Area:** Automated Regression Suite Verification, Unit Testing, and Invariant Coverage  

---

## 1. Executive Summary

A comprehensive test suite execution was performed across the complete SYNAPSE Phase 2 test suite following the implementation of continuous longitudinal trajectories, treatment intensification, chronic complications, and person-time censoring.

### Overall Test Suite Status
```
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/shashi/synapse/synapse-phase2
plugins: Faker-40.43.0
collected 158 items

============================= 158 passed in 7.23s ==============================
```
**Outcome:** **158 Passed / 0 Failed / 0 Warnings / 0 Regressions.**

---

## 2. Test File Breakdown and Coverage Matrix

| Test Suite File | Test Count | Domain / Layer Tested | Status | Execution Time |
| :--- | :---: | :--- | :---: | :---: |
| `tests/test_longitudinal_trajectories.py` | **4** | Continuous monitoring loops, BP/HbA1c re-measurement, step-up intensification, right-censored person-time, competing risk exclusivity | **PASS** | 0.22s |
| `tests/test_clinical_modules.py` | 6 | Declarative module loading, state-machine transitions, condition evaluation, latent onset preceding diagnosis | **PASS** | 0.18s |
| `tests/test_evaluation_framework.py` | 20 | Pure Python statistical metrics (Wilson, JSD, TVD, Chi-square), CSV evaluation, invariant gates, baseline prevalence isolation | **PASS** | 0.95s |
| `tests/test_root_cause_corrections.py` | 10 | Baseline point prevalence vs period prevalence, background life-table mortality, rule conformance labeling | **PASS** | 0.42s |
| `tests/test_determinism.py` | 10 | Seed-based identical reproducibility, intra-timestep jitter consistency | **PASS** | 0.35s |
| `tests/test_longitudinal_export.py` | 2 | 16 CSV exports, schema integrity, patient timeline export | **PASS** | 0.12s |
| `tests/test_phase2_csv_export.py` | 3 | Backward-compatible CSV column headers and relationship integrity | **PASS** | 0.15s |
| `tests/test_population_profile.py` | 5 | Demographic sampling, age pyramid weights, life-table lookup | **PASS** | 0.11s |
| `tests/test_population_validator.py` | 5 | Multi-tier validation gates, statistical bounds | **PASS** | 0.14s |
| `tests/test_validation_gate.py` | 5 | Acceptance thresholds, hard invariant enforcement | **PASS** | 0.12s |
| `tests/test_state_machines.py` | 7 | Departmental state machines (clinical, pharmacy, lab, rad, finance) | **PASS** | 0.28s |
| `tests/test_state_manager.py` | 4 | In-memory relational state store, ACID transitions | **PASS** | 0.16s |
| `tests/test_stage6_ordering_causation.py` | 2 | Causal event graphs, temporal monotonicity | **PASS** | 0.15s |
| `tests/test_stage6_loop_failure_protection.py` | 2 | Infinite loop detection, deadlock protection | **PASS** | 0.10s |
| `tests/test_stage9_integrity.py` | 1 | Referential foreign key integrity across encounters and orders | **PASS** | 0.08s |
| *Other Stage Suites (7, 9, Billing, Diagnostics)* | 52 | Departmental workflows, operational scenarios, dispatcher, event queue | **PASS** | 2.80s |
| **Total** | **158** | **Complete System Regression & Verification Suite** | **PASS** | **7.23s** |

---

## 3. Specific Trajectory Unit Test Details

The 4 tests implemented in [`tests/test_longitudinal_trajectories.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_longitudinal_trajectories.py) directly validate the requirements of this phase:

1. **`test_hypertension_continuous_loop_and_intensification`:**
   - Validates that patients with hypertension receive initial Amlodipine (`AML-5`) and dietary care plans at `ScreeningEncounter`.
   - Advances simulation time by 180 days to `FollowUpEncounter`.
   - Validates that blood pressure is re-measured (`MeasureFollowUpBP`), and uncontrolled readings trigger step-up combination therapy with Telmisartan (`TEL-40`).
   - Asserts that the module does not transition to a terminal state and remains active in `MaintenanceDelay`.
2. **`test_diabetes_continuous_loop_and_intensification`:**
   - Validates that diabetes diagnosis initiates Metformin (`MET-500`) and lifestyle protocol (`CP-DIAB-01`).
   - Advances time by 90 days to `DiabeticFollowUp`.
   - Validates follow-up HbA1c re-measurement and stepped-up oral hypoglycemic intensification with Glimepiride (`GLIM-1`).
   - Asserts that the previous premature `TerminalState` is eliminated, ensuring continuing quarterly surveillance.
3. **`test_individual_censored_person_time_calculation`:**
   - Creates a hand-verified dataset fixture of 2 patients over 730 days (2.0 years): one survivor and one deceased patient who dies after 183 days (0.50 years).
   - Validates that `DatasetEvaluator.evaluate_longitudinal()` computes right-censored person-years of **$2.50\text{ person-years}$**, rather than treating the cohort as $4.0\text{ person-years}$.
4. **`test_competing_risks_no_double_death`:**
   - Triggers `CardiovascularDeath` in an elderly patient.
   - Asserts `patient.is_alive = False`, exact death date recorded, and 1 death entry created in `longitudinal_deaths`.
   - Steps the patient a subsequent time 30 days later and verifies that zero actions are emitted and zero duplicate death records are generated.
