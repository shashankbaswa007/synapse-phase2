# SYNAPSE Phase 2: Comprehensive Clinical Evaluation & Metric Scorecard

## 1. Evaluation Architecture & Scorecard Overview

This evaluation report presents the quantitative and qualitative validation results of the **SYNAPSE Phase 2** canonical synthetic cohort ($N=10,000$, seed 42, 720 days, timestep 7 days).

Evaluation was executed by `synapse_simulator.evaluation.runner.EvaluationRunner` against preregistered clinical safety invariants, demographic targets, and published epidemiological calibration benchmarks.

### Executive Evaluation Scorecard
* **Overall Invariant Status**: **PASS** (Zero fatal clinical safety or temporal violations).
* **Total Evaluated Metrics**: **21**
* **Metrics Meeting Acceptance Criteria (PASS)**: **16**
* **Metrics with Warnings (WARN)**: **0**
* **Failing Metrics (FAIL)**: **0**
* **Metrics Requiring Microdata Calibration (UNVERIFIED)**: **5**
* **Validation Gate Status**: **REFERENCE_DATA_PENDING**

---

## 2. Quantitative Metric Results

### 2.1 Clinical Safety & Temporal Invariants (5/5 PASS)

These metrics represent absolute physical, temporal, and clinical invariants. Any single violation results in immediate cohort rejection.

| Metric ID | Invariant Name | Evaluated Records | Violations | Acceptance Bound | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | Zero Clinical Events Prior to Birth | 21,730 encounters | **0** | Allowed $= 0$ | **PASS** |
| `inv_no_event_post_mortem` | Zero Clinical Events Post-Mortem | 21,730 encounters | **0** | Allowed $= 0$ | **PASS** |
| `inv_diagnosis_encounter_linkage`| Condition-to-Encounter Linkage | 10,463 conditions | **0** | Allowed $= 0$ | **PASS** |
| `inv_allergy_safety_veto` | Allergy Contraindication Veto (`RULE-CLIN-ALLERGY-001`) | 12,943 prescriptions | **0** | Allowed $= 0$ | **PASS** |
| `inv_person_time_upper_bound` | Person-Time Timestamp Bounds | 94,595 records | **0** | Allowed $= 0$ | **PASS** |

---

### 2.2 Demographic Calibration Metrics (3/3 PASS)

Demographics are calibrated against the **Sample Registration System (SRS) 2021 India Census**.

| Metric ID | Demographic Metric | Synthetic Estimate | Reference Target | Metric Type / Distance | Acceptance Threshold | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `demo_sex_distribution` | Male Sex Proportion | **51.50%** | 51.50% | Absolute Diff: $0.00\%$ | $[50.0\%, 53.0\%]$ | **PASS** |
| `demo_age_pyramid_jsd` | 5-Band Age Pyramid | Distr. aligned | SRS 2021 | Jensen-Shannon: $\mathbf{0.00005}$ | $\text{JSD} \le 0.050$ | **PASS** |
| `demo_age_by_sex_jsd` | Age-by-Sex Joint Distr. | Distr. aligned | SRS 2021 | Jensen-Shannon: $\mathbf{0.00013}$ | $\text{JSD} \le 0.050$ | **PASS** |

---

### 2.3 Epidemiological Prevalence & Comorbidity (5/5 PASS)

Calibrated against large-scale Indian epidemiological surveys: **ICMR-INDIAB 2023** (Hypertension & Diabetes) and the **National Health Profile (NHP) India 2020** (Acute Respiratory Infections).

| Metric ID | Disease Metric | Synthetic Estimate | Reference Benchmark | Acceptance Range | Calibration Benchmark | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `prev_hypertension_adults` | Adult Hypertension (Period) | **34.82%** ($2,324 / 6,675$) | 30.70% | $[27.0\%, 35.0\%]$ | ICMR-INDIAB 2023 | **PASS** |
| `prev_diabetes_t2_adults` | Adult Type 2 Diabetes (Period) | **13.96%** ($932 / 6,675$) | 11.40% | $[9.0\%, 15.0\%]$ | ICMR-INDIAB 2023 | **PASS** |
| `comorb_htn_in_t2d` | Comorbid HTN in T2D Adults | **47.10%** ($439 / 932$) | 50.10% | $[40.0\%, 60.0\%]$ | ICMR-INDIAB 2023 | **PASS** |
| `prev_urti_cumulative_attack_rate`| Acute URTI Cumulative Attack Rate | **71.65%** ($7,165 / 10,000$) | 70.00% | $[60.0\%, 80.0\%]$ | NHP India 2020 | **PASS** |
| `prev_urti_14day_point` | Acute URTI 14-Day Point Prev. | **4.82%** ($482 / 10,000$) | 8.50% | $[3.0\%, 12.0\%]$ | NHP India 2020 | **PASS** |

> **Denominators**:
> * Adult Denominator: Age $\ge 20$ ($N=6,675$ patients, ICMR-INDIAB standard).
> * Total Cohort Denominator: All ages ($N=10,000$ patients).
> * Diabetic Subpopulation Denominator: Adults with diagnosed T2D ($N=932$ patients).

---

### 2.4 Longitudinal Healthcare Utilization & Mortality (1 PASS, 2 UNVERIFIED)

| Metric ID | Metric Name | Synthetic Estimate | Reference Target | Acceptance Criteria | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `long_crude_mortality_rate` | Crude All-Cause Mortality | **0.01311** /pt-yr | 0.00600 /pt-yr | Rate $\le 0.02000$ | **PASS** |
| `long_encounters_per_pt_year` | Annual OPD Visits per Pt-Year | **1.12** /pt-yr | 1.50 /pt-yr | Requires survey microdata | **UNVERIFIED** |
| `long_inter_encounter_interval_days` | Mean Inter-Encounter Days | **120.4** days | 180.0 days | Requires survey microdata | **UNVERIFIED** |

* **Mortality Interpretation**: The observed crude rate of $0.01311$ deaths per patient-year corresponds to 255 deaths across 19,446.7 patient-years of exposure. This rate reflects background age-sex hazards from SRS 2016–2020 combined with chronic comorbidity elevation.

---

### 2.5 Clinical Guidelines Adherence & Stepped Care (2 PASS, 3 UNVERIFIED)

Evaluated against the **ICMR Standard Treatment Guidelines (STG) 2022**.

| Metric ID | Guideline / Clinical Metric | Synthetic Value | Reference Target | Status |
| :--- | :--- | :---: | :---: | :---: |
| `rx_firstline_hypertension` | First-Line Monotherapy Adherence (Amlodipine) | **99.87%** | 100.00% | **PASS** |
| `rx_firstline_diabetes` | First-Line Monotherapy Adherence (Metformin) | **99.57%** | 100.00% | **PASS** |
| `long_treatment_intensification_rate`| Stepped-Care Escalation (Telmisartan / Glimepiride)| **0.7937** | Reference Pending | **UNVERIFIED** |
| `long_chronic_complication_rate` | Microvascular Progression (Nephropathy / CKD) | **0.0149** | 0.0400 | **UNVERIFIED** |
| `rx_adherence_assumption` | Medication Adherence Parameter | **100.00%** | Simulation Assumption | **UNVERIFIED** |

---

## 3. Blood Pressure Protocol Evaluation (`LASI_WAVE1_TRI_MEASUREMENT` v1.0.0)

Conducted on Day 360 for surviving older adults (Age 45+, $N=2,638$).

### Summary Statistics Across Triplicate Measurements

| Measurement Step | Systolic BP Mean $\pm$ SD | Diastolic BP Mean $\pm$ SD | Pulse Pressure Mean $\pm$ SD | Habituation Drop ($\Delta$ SBP) |
| :--- | :---: | :---: | :---: | :---: |
| **Reading 1 (Initial Seated)** | $130.14 \pm 9.41$ mmHg | $80.62 \pm 5.25$ mmHg | $49.52 \pm 8.95$ mmHg | Reference baseline |
| **Reading 2 (Post-Rest 1)** | $126.69 \pm 9.59$ mmHg | $79.11 \pm 5.36$ mmHg | $47.58 \pm 9.28$ mmHg | **$-3.45$ mmHg** |
| **Reading 3 (Post-Rest 2)** | $126.61 \pm 9.56$ mmHg | $79.14 \pm 5.32$ mmHg | $47.47 \pm 9.38$ mmHg | **$-0.08$ mmHg** |
| **Protocol Average (R2+R3)**| $126.65 \pm 9.54$ mmHg | $79.13 \pm 5.31$ mmHg | $47.52 \pm 9.30$ mmHg | **$-3.49$ mmHg** |

### Protocol Integrity Checks
1. **Triplicate Count**: 2,638 assessments $\times$ 3 readings $= 7,914$ readings (**100% complete, 0 missing**).
2. **Physiological Bound**: $\text{SBP} > \text{DBP}$ across all 7,914 readings (**0 violations**).
3. **Pulse Pressure Bound**: $\text{Pulse Pressure} \ge 20$ mmHg across all 7,914 readings (Minimum observed: **$22.60$ mmHg**).

---

## 4. Methodological Distinction: Engineering Tests vs. Calibration vs. External Validation

To maintain strict scientific and regulatory integrity:

1. **Synthetic-Data Engineering Tests**:
   - Referential integrity audits, foreign-key resolution, primary-key uniqueness, and chronological bounding.
   - Verified 100% passed across all 18 tables.
2. **Statistical Calibration Benchmarks**:
   - Tuning disease onset hazard ratios, state machine transitions, and age-pyramid distributions to match published aggregate national health tables (SRS 2021, ICMR-INDIAB 2023, NHP 2020).
   - 16 metrics verified within target tolerance ranges.
3. **Empirical Clinical External Validation**:
   - Evaluating patient-level trajectory concordance and predictive discrimination against genuine patient microdata.
   - **Current Status**: **REFERENCE_DATA_PENDING**.
   - No genuine LASI individual participant data (IPD) or restricted microdata files were accessed or utilized.
