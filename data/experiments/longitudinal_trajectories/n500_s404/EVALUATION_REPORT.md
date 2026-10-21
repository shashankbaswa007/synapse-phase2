# SYNAPSE Phase 2 — Comprehensive Synthetic Data Evaluation Report

**Evaluation Timestamp:** `2026-10-21T18:03:50.234487`  
**Dataset Directory:** `/Users/shashi/synapse/synapse-phase2/data/experiments/longitudinal_trajectories/n500_s404`  
**Overall Evaluation Status:** **PASS**  
**Invariant Integrity:** **PASSED (0 Hard Violations)**  

---

## 1. Executive Summary & Status Overview

- **Total Evaluated Metrics:** `21`
- **PASS:** `16` (Meets predefined empirical acceptance thresholds)
- **WARNING:** `0` (Observed deviation or moderate divergence requiring calibration/review)
- **FAIL:** `0` (Violates hard invariant or practical tolerance threshold)
- **UNVERIFIED:** `5` (Lacks published empirical real-world benchmark; assumption documented)
- **NOT_APPLICABLE:** `0` (Cohort sample size or eligibility empty for this stratum)

### Dimension Status Breakdown

| Evaluation Dimension | Total | PASS | WARNING | FAIL | UNVERIFIED | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **INVARIANTS** | 5 | 5 | 0 | 0 | 0 | **PASS** |
| **DEMOGRAPHICS** | 3 | 3 | 0 | 0 | 0 | **PASS** |
| **PREVALENCE** | 4 | 4 | 0 | 0 | 0 | **PASS** |
| **COMORBIDITY** | 1 | 1 | 0 | 0 | 0 | **PASS** |
| **LONGITUDINAL** | 5 | 1 | 0 | 0 | 4 | **PASS** |
| **TREATMENT** | 3 | 2 | 0 | 0 | 1 | **PASS** |

---

## 2. Quantitative Metric Scorecard

| Metric ID | Dimension | Synthetic Estimate | Reference Benchmark | Difference | 95% Confidence Interval | Status | Verification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `inv_no_event_post_mortem` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `inv_diagnosis_encounter_linkage` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `inv_allergy_safety_veto` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `SOFTWARE_INVARIANT_PASS` |
| `inv_person_time_upper_bound` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `SOFTWARE_INVARIANT_PASS` |
| `demo_sex_distribution` | DEMOGRAPHICS | 52.00 | 51.50 | +0.50 | [47.62, 56.35] | **PASS** | `VERIFIED` |
| `demo_age_pyramid_jsd` | DEMOGRAPHICS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `demo_age_by_sex_jsd` | DEMOGRAPHICS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `prev_hypertension_adults` | PREVALENCE | 34.46 | 30.70 | +3.76 | [29.50, 39.78] | **PASS** | `VERIFIED` |
| `prev_diabetes_t2_adults` | PREVALENCE | 13.85 | 11.40 | +2.45 | [10.51, 18.03] | **PASS** | `VERIFIED` |
| `prev_urti_14day_point` | PREVALENCE | 6.00 | 8.50 | -2.50 | [4.23, 8.44] | **PASS** | `VERIFIED` |
| `prev_urti_cumulative_attack_rate` | PREVALENCE | 66.60 | 70.00 | -3.40 | [62.35, 70.59] | **PASS** | `VERIFIED` |
| `comorb_htn_in_t2d` | COMORBIDITY | 55.56 | 50.10 | +5.46 | [41.18, 69.06] | **PASS** | `VERIFIED` |
| `long_encounters_per_pt_year` | LONGITUDINAL | 1.08 | 1.50 | -0.42 | — | **UNVERIFIED** | `UNVERIFIED` |
| `long_inter_encounter_interval_days` | LONGITUDINAL | 115.90 | 180.00 | -64.10 | — | **UNVERIFIED** | `UNVERIFIED` |
| `long_crude_mortality_rate` | LONGITUDINAL | 0.01 | 0.01 | +0.00 | — | **PASS** | `VERIFIED` |
| `long_treatment_intensification_rate` | LONGITUDINAL | 0.83 | — | — | — | **UNVERIFIED** | `UNVERIFIED` |
| `long_chronic_complication_rate` | LONGITUDINAL | 0.04 | 0.04 | -0.00 | — | **UNVERIFIED** | `UNVERIFIED` |
| `rx_firstline_hypertension` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_firstline_diabetes` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_adherence_assumption` | TREATMENT | 100.00 | — | — | — | **UNVERIFIED** | `UNVERIFIED` |

---

## 3. Invariant & Safety Evaluation

Hard temporal and causal invariants protect structural and clinical correctness independently of statistical comparisons.

### ✅ Temporal Invariant: No Clinical Activity Prior to Birth
- **Definition:** Verifies that no clinical encounter or procedure occurs before the patient's recorded birth date.
- **Violations Observed:** `0` out of `1053` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires either explicit birth_date column or deterministic age projection.

### ✅ Temporal Invariant: Zero Post-Mortem Clinical Events
- **Definition:** Verifies that deceased patients have strictly zero subsequent encounters, orders, or prescriptions.
- **Violations Observed:** `0` out of `1053` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluated against deaths.csv records.

### ✅ Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter
- **Definition:** Conditions must be recognized and diagnosed during an active clinical encounter.
- **Violations Observed:** `0` out of `495` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires foreign key condition.encounter_id -> encounters.encounter_id.

### ✅ Clinical Safety Invariant: Zero Contraindicated Prescriptions
- **Definition:** Verifies that no patient is prescribed a medication to which they have a documented allergy.
- **Violations Observed:** `0` out of `616` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluates allergy constraints against medication names.

### ✅ Temporal Invariant: Person-Time Bounded by Eligible Observation Duration
- **Definition:** Verifies that total cohort person-time does not exceed the sum of maximum eligible observation durations across all patients.
- **Violations Observed:** `0` out of `500` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluates individual and aggregated right-censored follow-up duration.

---

## 4. Demographic Fidelity Details

### Demographic Fidelity: Male Sex Proportion (`demo_sex_distribution`)
- **Definition:** Percentage of cohort that is male compared to Census SRS 2021 reference.
- **Synthetic Estimate:** `52.0` | **Reference Benchmark:** `51.5`
- **Difference:** `0.5`
- **Confidence Interval (95% Wilson):** `(47.62, 56.35)`
- **Acceptance Policy & Diagnostics:** `{'pass_abs_diff_max': 5.0, 'warning_abs_diff_max': 10.0}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Natural sex ratio in India is ~51.5% male. Small sample sizes may have higher random variance.

### Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence (`demo_age_pyramid_jsd`)
- **Definition:** JSD (base 2) between synthetic age distribution and SRS 2021 5-band reference pyramid.
- **Synthetic Estimate:** `0.00118` | **Reference Benchmark:** `0.0`
- **Difference:** `0.00118`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.05, 'warning_jsd_max': 0.15, 'total_variation_distance': 0.02, 'chi_square_stat': 2.9469, 'chi_square_df': 4, 'chi_square_p_value': 0.56675, 'chi_square_was_pooled': False, 'cramers_v': 0.0384}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Evaluated over 5 broad SRS census intervals. Small cohorts (<100) experience expected stochastic dispersion.

### Demographic Fidelity: Age-by-Sex Joint Distribution JSD (`demo_age_by_sex_jsd`)
- **Definition:** Jensen-Shannon Divergence across 10 age-by-sex joint strata compared to SRS 2021 Statement 19.
- **Synthetic Estimate:** `0.0039` | **Reference Benchmark:** `0.0`
- **Difference:** `0.0039`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.08, 'warning_jsd_max': 0.2, 'tvd': 0.0519}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Requires adequate cohort sample size across all 10 cells to avoid small-sample bin bias.

---

## 5. Disease Prevalence Details (Denominator Matched)

### Disease Prevalence: Essential Hypertension (Adults >= 20) (`prev_hypertension_adults`)
- **Definition:** Prevalence of essential hypertension (I10) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `325` patients | **Diagnosed Cases:** `112`
- **Synthetic Prevalence:** `34.46%` (95% CI: `29.5% - 39.78%`)
- **Empirical Reference:** `30.7%` (Absolute Diff: `3.76%`, Relative Diff: `12.25%`)
- **Provenance:** `ICMR_INDIAB_2023_HTN` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 8.0, 'warning_abs_diff_max': 15.0, 'crude_cohort_cases': 112, 'crude_cohort_prevalence_pct': 22.4, 'baseline_point_cases': 100, 'baseline_point_prevalence_pct': 30.77, 'incident_cases': 12, 'incident_attack_rate_pct': 3.69}`
- **Limitations:** Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold.

### Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) (`prev_diabetes_t2_adults`)
- **Definition:** Prevalence of Type 2 Diabetes (E11.9) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `325` patients | **Diagnosed Cases:** `45`
- **Synthetic Prevalence:** `13.85%` (95% CI: `10.51% - 18.03%`)
- **Empirical Reference:** `11.4%` (Absolute Diff: `2.45%`, Relative Diff: `21.49%`)
- **Provenance:** `ICMR_INDIAB_2023_T2D` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 12.0, 'crude_cohort_cases': 45, 'crude_cohort_prevalence_pct': 9.0, 'baseline_point_cases': 38, 'baseline_point_prevalence_pct': 11.69, 'incident_cases': 7, 'incident_attack_rate_pct': 2.15}`
- **Limitations:** Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold.

### Disease Prevalence: Acute URTI 14-Day Point Prevalence (All Ages) (`prev_urti_14day_point`)
- **Definition:** 14-day recall point prevalence of active acute URTI (J06.9) vs NHP India 2020 baseline.
- **Eligible Cohort Denominator:** `500` patients | **Diagnosed Cases:** `30`
- **Synthetic Prevalence:** `6.0%` (95% CI: `4.23% - 8.44%`)
- **Empirical Reference:** `8.5%` (Absolute Diff: `-2.5%`, Relative Diff: `29.41%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 10.0}`
- **Limitations:** Requires filtering for active, non-resolved infection episodes within a 14-day evaluation window.

### Disease Attack Rate: Acute URTI 2-Year Cumulative Attack Rate (All Ages) (`prev_urti_cumulative_attack_rate`)
- **Definition:** 2-year cumulative attack rate of acute URTI (J06.9) across entire cohort vs NHP/IDSP surveillance baseline.
- **Eligible Cohort Denominator:** `500` patients | **Diagnosed Cases:** `333`
- **Synthetic Prevalence:** `66.6%` (95% CI: `62.35% - 70.59%`)
- **Empirical Reference:** `70.0%` (Absolute Diff: `-3.4%`, Relative Diff: `4.86%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 12.0, 'warning_abs_diff_max': 20.0}`
- **Limitations:** Cumulative attack rate over 24-month horizon. Derived from quarterly infection hazards.

---

## 6. Comorbidity & Disease Clustering Details

### Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes (`comorb_htn_in_t2d`)
- **Definition:** Conditional prevalence P(HTN|T2D) among adults >= 20 vs ICMR-INDIAB 2023 benchmark.
- **Synthetic Conditional Prevalence P(HTN|T2D):** `55.56%` (Cases: `25` / `45`)
- **Reference Benchmark (ICMR-INDIAB 2023):** `50.1%`
- **Association Diagnostics:** `{'pass_abs_diff_max': 15.0, 'warning_abs_diff_max': 25.0, 'joint_prevalence_pct': 7.69, 'expected_joint_prevalence_pct': 4.77, 'observed_to_expected_ratio': 1.6121, 'odds_ratio': 2.773, 'odds_ratio_95_ci': (1.462, 5.2597)}`
- **Status:** **PASS** (`VERIFIED`)
- **Limitations:** Evaluated strictly on adults with diagnosed T2D. If no synthetic patient develops T2D, status is NOT_APPLICABLE.

---

## 7. Longitudinal Dynamics & Clinical Treatments

### Longitudinal: Encounters Per Patient-Year (`long_encounters_per_pt_year`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `1.08` | **Reference Benchmark:** `1.5`
- **Provenance:** `NSS_75TH_ROUND_OPD` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** Facility discrete-event simulation captures scheduled outpatient visits and episodic visits.

### Longitudinal: Mean Days Between Clinical Encounters (`long_inter_encounter_interval_days`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `115.9` | **Reference Benchmark:** `180.0`
- **Provenance:** `ICMR_TREATMENT_GUIDELINES` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** Clinical modules use configured surveillance delays (e.g., 90d, 180d, 365d).

### Longitudinal: Annualized Crude Mortality Rate (`long_crude_mortality_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.00923` | **Reference Benchmark:** `0.006`
- **Provenance:** `SRS_2016_2020_LIFE_TABLE` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Short simulation windows (e.g. 2 years) in small cohorts exhibit expected binomial variance.

### Longitudinal: Treatment Intensification Rate (`long_treatment_intensification_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.8258` | **Reference Benchmark:** `Unspecified`
- **Provenance:** `ICMR_TREATMENT_GUIDELINES` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** High cumulative intensification (75-85%) reflects zero therapeutic inertia across repeated visits.

### Longitudinal: Chronic Complication Rate (`long_chronic_complication_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.0379` | **Reference Benchmark:** `0.04`
- **Provenance:** `CURES_CCDC_PROSPECTIVE_HTN` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** Complications depend on discrete transition weights and surveillance visit frequencies. Classified UNVERIFIED because discrete Markov draws are not externally calibrated clinical trial incidence.

### Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Antihypertensive Therapy) (`rx_firstline_hypertension`)
- **Dimension:** `TREATMENT`
- **Synthetic Estimate:** `100.0` | **Reference Benchmark:** `100.0`
- **Provenance:** `ICMR_STG_HYPERTENSION_2022` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Assumes uncomplicated stage 1/2 essential hypertension indicated for calcium channel blocker. Reflects algorithmic rule compliance rather than verified real-world prescribing fidelity (empirical real-world monotherapy alignment is ~45-65%).

### Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Oral Hypoglycemic Therapy) (`rx_firstline_diabetes`)
- **Dimension:** `TREATMENT`
- **Synthetic Estimate:** `100.0` | **Reference Benchmark:** `100.0`
- **Provenance:** `ICMR_STG_DIABETES_2022` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Guideline recommends Metformin monotherapy as universal initial pharmacotherapy. Reflects algorithmic rule compliance rather than verified real-world prescribing fidelity (empirical real-world monotherapy alignment is ~50-60%).

### Treatment Pattern: Perfect Adherence Assumption Disclosure (`rx_adherence_assumption`)
- **Dimension:** `TREATMENT`
- **Synthetic Estimate:** `100.0` | **Reference Benchmark:** `Unspecified`
- **Provenance:** `SYNAPSE_SIMULATION_ASSUMPTION` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** Real-world non-communicable disease medication adherence in India is ~40-60%. Simulation assumes 100% adherence.

---

## 8. Calibration Guidance & Research Governance

- **Separation of Evaluation from Generation:** Evaluator inspected exported CSV artifacts without relying on simulation memory objects.
- **Denominator Compatibility:** Denominators for adult chronic non-communicable conditions (HTN, T2D) strictly filter for age >= 20, matching ICMR-INDIAB survey methodology.
- **Unverified Benchmarks:** Metrics without formal peer-reviewed or census benchmarks are explicitly labeled `UNVERIFIED` and never marked `PASS`.
- **Adherence Assumption:** Medication adherence is assumed to be 100% in simulation, which represents an idealized clinical trial or guideline-adherent baseline.
