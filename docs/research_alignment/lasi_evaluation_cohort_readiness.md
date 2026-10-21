# LASI Evaluation Cohort Readiness Report

**Project:** SYNAPSE Phase 2 — Synthetic Healthcare Data Generation and Evaluation  
**Document ID:** `DOC-RES-LASI-006`  
**Evaluation Scope:** Purpose-Built Older-Adult Synthetic Cohort Readiness for LASI Wave 1 Benchmark  
**Date:** 2026-10-21  
**Git Revision:** `3e3ae1d28286e9106659f68aa053465ded9bb3c2` (with DBP regression test & evaluator hardening)  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary & Objective

The objective of this phase is to prepare and verify a reproducible, statistically defensible synthetic cohort for the upcoming genuine LASI Wave 1 external evaluation, resolving the sample-size starvation identified in the preliminary test fixture run without violating core scientific constraints:
1. **No Artificial Parameter Changes:** Clinical transition probabilities, disease incidence rates, treatment escalation algorithms, and baseline demographic distributions must **not** be tuned merely to force metric validation gates to pass.
2. **No Data Fabrication or Formulaic Synthesis:** Missing clinical measurements (such as diastolic blood pressure) must not be generated via arbitrary scalar mathematical formulas (e.g., $0.65 \times \text{SBP}$).
3. **No Patient Duplication:** Cohort sample size must not be artificially inflated by replicating existing patient trajectories.
4. **Strict Isolation:** The purpose-built evaluation cohort is maintained in a dedicated path ([`data/evaluation/lasi_cohort_500/seed_42`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42)) separate from default production synthetic data ([`data/synthetic/`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/)).

---

## 2. Investigation of Baseline Fixture Deficiencies

The initial verification run against the test fixture ([`data/evaluation/lasi/LASI_EVALUATION_REPORT.md`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi/LASI_EVALUATION_REPORT.md)) reported severe sample starvation:
* **Older Adults ($\ge 45$ years):** Only 29 synthetic patients.
* **Systolic Blood Pressure (SBP):** Only 11 observations in older adults.
* **Diastolic Blood Pressure (DBP):** 0 exported observations.
* **HbA1c Biomarker:** Only 1 observation in older adults.
* **Validation Metric Status:** All continuous distributions gated out under `INSUFFICIENT_SAMPLE_SIZE` ($N < 30$).

### 2.1 Demographic Root Cause Analysis
In the baseline multi-seed configuration, the simulation cohort size was set to $N = 100$ general-population individuals. Under the Census SRS 2021 Indian age pyramid specified in [`config/population/india_default_v1.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/population/india_default_v1.yaml), older adults represent a minority:

$$\text{Older Adult Fraction} = P(\text{Age} \in [45, 64]) + P(\text{Age} \ge 65) = 0.188 + 0.070 = 0.258 \quad (25.8\%)$$

For $N = 100$, the expected older adult sample size is:
$$\mathbb{E}[N_{\ge 45}] = 100 \times 0.258 = 25.8 \approx 26 \text{ patients}$$

The baseline run produced exactly 29 patients aged $\ge 45$, completely consistent with random binomial sampling ($B(100, 0.258)$). This demonstrated that the generator was operating correctly according to its population profile, but was severely underpowered for older-adult external evaluation.

---

## 3. Dedicated Cohort Scaling & Legitimate Sampling

To achieve an older-adult cohort size $N_{\ge 45} \ge 500$ without modifying demographic parameters, the simulation population size was scaled:

$$N_{\text{total}} \ge \frac{500}{0.258} \approx 1,938 \implies \text{Configured } N_{\text{total}} = 2,200$$

### 3.1 Simulation Configuration Specification
* **Generation Script:** [`scripts/generate_and_evaluate_lasi_cohort.py`](file:///Users/shashi/synapse/synapse-phase2/scripts/generate_and_evaluate_lasi_cohort.py)
* **Total Synthetic Population:** $N = 2,200$
* **Random Seed:** `42` (Fixed, documented)
* **Observation Window:** 720 days (2024-01-01T00:00:00 to 2025-12-22T00:00:00)
* **Discrete-Event Timestep:** 7 days
* **Population Profile:** [`config/population/india_default_v1.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/population/india_default_v1.yaml) (Census SRS 2021)
* **Clinical Modules Loaded:** [`hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml), [`diabetes_t2.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/diabetes_t2.yaml), [`urti.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/urti.yaml)
* **Actuarial Background Mortality:** Enabled ([`synapse_simulator.evaluation.experiment.ExperimentRunner`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/experiment.py#L119-L138)) via Census SRS Life Tables 2016–2020.

---

## 4. Cohort Demographics & Sample Comparison

| Dimension | Baseline Fixture Run (`seed_42`) | Dedicated LASI Cohort (`seed_42`) | Sensitivity Run (`seed_101`) | LASI Wave 1 Target Population |
| :--- | :---: | :---: | :---: | :---: |
| **Total Simulated Individuals** | 100 | **2,200** | 2,200 | Survey Sample |
| **Older Adults (Age $\ge 45$)** | 29 (29.0%) | **575 (26.14%)** | 553 (25.14%) | Target: $\ge 500$ |
| **Female Older Adults** | 12 (41.4%) | **276 (48.00%)** | 262 (47.38%) | ~54.0% in LASI |
| **Male Older Adults** | 17 (58.6%) | **299 (52.00%)** | 291 (52.62%) | ~46.0% in LASI |
| **Age 45–54** | 11 | **205 (35.65%)** | 208 (37.61%) | Populated |
| **Age 55–64** | 12 | **211 (36.70%)** | 205 (37.07%) | Populated |
| **Age 65–74** | 3 | **40 (6.96%)** | 46 (8.32%) | Populated |
| **Age 75+** | 3 | **119 (20.70%)** | 94 (17.00%) | Populated |
| **Total Age-Sex Strata Populated** | 8 / 8 (Sparse) | **8 / 8 (Robust)** | 8 / 8 (Robust) | 8 Strata Required |
| **Minimum Sample Gate Status** | ❌ Gated (< 30) | **✅ Satisfied ($\ge 500$)** | **✅ Satisfied ($\ge 500$)** | Threshold: 500 |

---

## 5. Summary of Observation Yield in Dedicated Cohort

| Clinical Domain | Metric Code | Usable Older-Adult Observations | Usable Older Patients | Mean Measurements / Patient | Sample-Size Gate Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Systolic BP** | `lasi_bp_sbp_distribution` | **863** | **235** | 3.67 | **PASS** ($863 \ge 30$) |
| **Standardized SBP** | `lasi_bp_sbp_standardized_mean` | **863** | **235** | 3.67 | **PASS** ($863 \ge 30$) |
| **Diastolic BP** | `lasi_bp_dbp_distribution` | **0** | **0** | 0.00 | **INSUFFICIENT_SAMPLE_SIZE** ($0 < 30$) |
| **HbA1c Lab** | `lasi_lab_hba1c_distribution` | **506** | **78** | 6.49 | **UNVERIFIED** (Biomarker non-equivalence) |
| **HbA1c Control** | `lasi_lab_hba1c_clinical_categories` | **506** | **78** | 6.49 | **UNVERIFIED** (Biomarker non-equivalence) |
| **Hypertension** | `lasi_prev_htn_older_adult` | **575** | **575** | 1.00 | **WARNING** (Prevalence vs Fixture) |
| **Type 2 Diabetes** | `lasi_prev_t2d_older_adult` | **575** | **575** | 1.00 | **WARNING** (Prevalence vs Fixture) |

---

## 6. Regulatory & Governance Disclosure

> [!IMPORTANT]
> **OVERALL EVALUATION GATE: `REFERENCE_DATA_PENDING`**  
> While the synthetic cohort generation and observation export are verified, reproducible, and sufficiently powered ($N=575 \ge 500$), external validation against genuine LASI Wave 1 reference microdata remains strictly **`REFERENCE_DATA_PENDING`**.
> Structural verification was performed exclusively against [`data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/fixtures/lasi_wave1_sample_fixture.csv). Genuine evaluation will occur only upon formal receipt of authorized microdata under IIPS / Gateway to Global Aging DUA agreements.
