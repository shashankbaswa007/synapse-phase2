# SYNAPSE Phase 2 — Comprehensive Synthetic Data Evaluation Report

**Evaluation Timestamp:** `2026-10-21T18:03:41.363233`  
**Dataset Directory:** `/Users/shashi/synapse/synapse-phase2/data/experiments/longitudinal_trajectories/n100_s42`  
**Overall Evaluation Status:** **WARNING**  
**Invariant Integrity:** **PASSED (0 Hard Violations)**  

---

## 1. Executive Summary & Status Overview

- **Total Evaluated Metrics:** `21`
- **PASS:** `13` (Meets predefined empirical acceptance thresholds)
- **WARNING:** `3` (Observed deviation or moderate divergence requiring calibration/review)
- **FAIL:** `0` (Violates hard invariant or practical tolerance threshold)
- **UNVERIFIED:** `5` (Lacks published empirical real-world benchmark; assumption documented)
- **NOT_APPLICABLE:** `0` (Cohort sample size or eligibility empty for this stratum)

### Dimension Status Breakdown

| Evaluation Dimension | Total | PASS | WARNING | FAIL | UNVERIFIED | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **INVARIANTS** | 5 | 5 | 0 | 0 | 0 | **PASS** |
| **DEMOGRAPHICS** | 3 | 3 | 0 | 0 | 0 | **PASS** |
| **PREVALENCE** | 4 | 2 | 2 | 0 | 0 | **WARNING** |
| **COMORBIDITY** | 1 | 0 | 1 | 0 | 0 | **WARNING** |
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
| `demo_sex_distribution` | DEMOGRAPHICS | 53.00 | 51.50 | +1.50 | [43.29, 62.49] | **PASS** | `VERIFIED` |
| `demo_age_pyramid_jsd` | DEMOGRAPHICS | 0.01 | 0.00 | +0.01 | — | **PASS** | `VERIFIED` |
| `demo_age_by_sex_jsd` | DEMOGRAPHICS | 0.02 | 0.00 | +0.02 | — | **PASS** | `VERIFIED` |
| `prev_hypertension_adults` | PREVALENCE | 45.31 | 30.70 | +14.61 | [33.73, 57.43] | **WARNING** | `VERIFIED` |
| `prev_diabetes_t2_adults` | PREVALENCE | 9.38 | 11.40 | -2.02 | [4.37, 18.98] | **PASS** | `VERIFIED` |
| `prev_urti_14day_point` | PREVALENCE | 1.00 | 8.50 | -7.50 | [0.18, 5.45] | **WARNING** | `VERIFIED` |
| `prev_urti_cumulative_attack_rate` | PREVALENCE | 72.00 | 70.00 | +2.00 | [62.51, 79.86] | **PASS** | `VERIFIED` |
| `comorb_htn_in_t2d` | COMORBIDITY | 33.33 | 50.10 | -16.77 | [9.68, 70.00] | **WARNING** | `VERIFIED` |
| `long_encounters_per_pt_year` | LONGITUDINAL | 1.11 | 1.50 | -0.39 | — | **UNVERIFIED** | `UNVERIFIED` |
| `long_inter_encounter_interval_days` | LONGITUDINAL | 141.00 | 180.00 | -39.00 | — | **UNVERIFIED** | `UNVERIFIED` |
| `long_crude_mortality_rate` | LONGITUDINAL | 0.02 | 0.01 | +0.01 | — | **PASS** | `VERIFIED` |
| `long_treatment_intensification_rate` | LONGITUDINAL | 0.79 | — | — | — | **UNVERIFIED** | `UNVERIFIED` |
| `long_chronic_complication_rate` | LONGITUDINAL | 0.03 | 0.04 | -0.01 | — | **UNVERIFIED** | `UNVERIFIED` |
| `rx_firstline_hypertension` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_firstline_diabetes` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_adherence_assumption` | TREATMENT | 100.00 | — | — | — | **UNVERIFIED** | `UNVERIFIED` |

---

## 3. Invariant & Safety Evaluation

Hard temporal and causal invariants protect structural and clinical correctness independently of statistical comparisons.

### ✅ Temporal Invariant: No Clinical Activity Prior to Birth
- **Definition:** Verifies that no clinical encounter or procedure occurs before the patient's recorded birth date.
- **Violations Observed:** `0` out of `213` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires either explicit birth_date column or deterministic age projection.

### ✅ Temporal Invariant: Zero Post-Mortem Clinical Events
- **Definition:** Verifies that deceased patients have strictly zero subsequent encounters, orders, or prescriptions.
- **Violations Observed:** `0` out of `213` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluated against deaths.csv records.

### ✅ Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter
- **Definition:** Conditions must be recognized and diagnosed during an active clinical encounter.
- **Violations Observed:** `0` out of `108` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires foreign key condition.encounter_id -> encounters.encounter_id.

### ✅ Clinical Safety Invariant: Zero Contraindicated Prescriptions
- **Definition:** Verifies that no patient is prescribed a medication to which they have a documented allergy.
- **Violations Observed:** `0` out of `134` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluates allergy constraints against medication names.

### ✅ Temporal Invariant: Person-Time Bounded by Eligible Observation Duration
- **Definition:** Verifies that total cohort person-time does not exceed the sum of maximum eligible observation durations across all patients.
- **Violations Observed:** `0` out of `100` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluates individual and aggregated right-censored follow-up duration.

---

## 4. Demographic Fidelity Details

### Demographic Fidelity: Male Sex Proportion (`demo_sex_distribution`)
- **Definition:** Percentage of cohort that is male compared to Census SRS 2021 reference.
- **Synthetic Estimate:** `53.0` | **Reference Benchmark:** `51.5`
- **Difference:** `1.5`
- **Confidence Interval (95% Wilson):** `(43.29, 62.49)`
- **Acceptance Policy & Diagnostics:** `{'pass_abs_diff_max': 5.0, 'warning_abs_diff_max': 10.0}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Natural sex ratio in India is ~51.5% male. Small sample sizes may have higher random variance.

### Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence (`demo_age_pyramid_jsd`)
- **Definition:** JSD (base 2) between synthetic age distribution and SRS 2021 5-band reference pyramid.
- **Synthetic Estimate:** `0.01217` | **Reference Benchmark:** `0.0`
- **Difference:** `0.01217`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.05, 'warning_jsd_max': 0.15, 'total_variation_distance': 0.09, 'chi_square_stat': 6.0869, 'chi_square_df': 4, 'chi_square_p_value': 0.19275, 'chi_square_was_pooled': False, 'cramers_v': 0.1234}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Evaluated over 5 broad SRS census intervals. Small cohorts (<100) experience expected stochastic dispersion.

### Demographic Fidelity: Age-by-Sex Joint Distribution JSD (`demo_age_by_sex_jsd`)
- **Definition:** Jensen-Shannon Divergence across 10 age-by-sex joint strata compared to SRS 2021 Statement 19.
- **Synthetic Estimate:** `0.01785` | **Reference Benchmark:** `0.0`
- **Difference:** `0.01785`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.08, 'warning_jsd_max': 0.2, 'tvd': 0.1188}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Requires adequate cohort sample size across all 10 cells to avoid small-sample bin bias.

---

## 5. Disease Prevalence Details (Denominator Matched)

### Disease Prevalence: Essential Hypertension (Adults >= 20) (`prev_hypertension_adults`)
- **Definition:** Prevalence of essential hypertension (I10) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `64` patients | **Diagnosed Cases:** `29`
- **Synthetic Prevalence:** `45.31%` (95% CI: `33.73% - 57.43%`)
- **Empirical Reference:** `30.7%` (Absolute Diff: `14.61%`, Relative Diff: `47.59%`)
- **Provenance:** `ICMR_INDIAB_2023_HTN` (`VERIFIED`)
- **Status:** **WARNING**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 8.0, 'warning_abs_diff_max': 15.0, 'crude_cohort_cases': 29, 'crude_cohort_prevalence_pct': 29.0, 'baseline_point_cases': 25, 'baseline_point_prevalence_pct': 39.06, 'incident_cases': 4, 'incident_attack_rate_pct': 6.25}`
- **Limitations:** Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold.

### Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) (`prev_diabetes_t2_adults`)
- **Definition:** Prevalence of Type 2 Diabetes (E11.9) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `64` patients | **Diagnosed Cases:** `6`
- **Synthetic Prevalence:** `9.38%` (95% CI: `4.37% - 18.98%`)
- **Empirical Reference:** `11.4%` (Absolute Diff: `-2.02%`, Relative Diff: `17.72%`)
- **Provenance:** `ICMR_INDIAB_2023_T2D` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 12.0, 'crude_cohort_cases': 6, 'crude_cohort_prevalence_pct': 6.0, 'baseline_point_cases': 2, 'baseline_point_prevalence_pct': 3.12, 'incident_cases': 4, 'incident_attack_rate_pct': 6.25}`
- **Limitations:** Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold.

### Disease Prevalence: Acute URTI 14-Day Point Prevalence (All Ages) (`prev_urti_14day_point`)
- **Definition:** 14-day recall point prevalence of active acute URTI (J06.9) vs NHP India 2020 baseline.
- **Eligible Cohort Denominator:** `100` patients | **Diagnosed Cases:** `1`
- **Synthetic Prevalence:** `1.0%` (95% CI: `0.18% - 5.45%`)
- **Empirical Reference:** `8.5%` (Absolute Diff: `-7.5%`, Relative Diff: `88.24%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **WARNING**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 10.0}`
- **Limitations:** Requires filtering for active, non-resolved infection episodes within a 14-day evaluation window.

### Disease Attack Rate: Acute URTI 2-Year Cumulative Attack Rate (All Ages) (`prev_urti_cumulative_attack_rate`)
- **Definition:** 2-year cumulative attack rate of acute URTI (J06.9) across entire cohort vs NHP/IDSP surveillance baseline.
- **Eligible Cohort Denominator:** `100` patients | **Diagnosed Cases:** `72`
- **Synthetic Prevalence:** `72.0%` (95% CI: `62.51% - 79.86%`)
- **Empirical Reference:** `70.0%` (Absolute Diff: `2.0%`, Relative Diff: `2.86%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 12.0, 'warning_abs_diff_max': 20.0}`
- **Limitations:** Cumulative attack rate over 24-month horizon. Derived from quarterly infection hazards.

---

## 6. Comorbidity & Disease Clustering Details

### Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes (`comorb_htn_in_t2d`)
- **Definition:** Conditional prevalence P(HTN|T2D) among adults >= 20 vs ICMR-INDIAB 2023 benchmark.
- **Synthetic Conditional Prevalence P(HTN|T2D):** `33.33%` (Cases: `2` / `6`)
- **Reference Benchmark (ICMR-INDIAB 2023):** `50.1%`
- **Association Diagnostics:** `{'pass_abs_diff_max': 15.0, 'warning_abs_diff_max': 25.0, 'joint_prevalence_pct': 3.12, 'expected_joint_prevalence_pct': 4.25, 'observed_to_expected_ratio': 0.7356, 'odds_ratio': 0.5741, 'odds_ratio_95_ci': (0.0974, 3.384)}`
- **Status:** **WARNING** (`VERIFIED`)
- **Limitations:** Evaluated strictly on adults with diagnosed T2D. If no synthetic patient develops T2D, status is NOT_APPLICABLE.

---

## 7. Longitudinal Dynamics & Clinical Treatments

### Longitudinal: Encounters Per Patient-Year (`long_encounters_per_pt_year`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `1.11` | **Reference Benchmark:** `1.5`
- **Provenance:** `NSS_75TH_ROUND_OPD` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** Facility discrete-event simulation captures scheduled outpatient visits and episodic visits.

### Longitudinal: Mean Days Between Clinical Encounters (`long_inter_encounter_interval_days`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `141.0` | **Reference Benchmark:** `180.0`
- **Provenance:** `ICMR_TREATMENT_GUIDELINES` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** Clinical modules use configured surveillance delays (e.g., 90d, 180d, 365d).

### Longitudinal: Annualized Crude Mortality Rate (`long_crude_mortality_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.0208` | **Reference Benchmark:** `0.006`
- **Provenance:** `SRS_2016_2020_LIFE_TABLE` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Short simulation windows (e.g. 2 years) in small cohorts exhibit expected binomial variance.

### Longitudinal: Treatment Intensification Rate (`long_treatment_intensification_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.7879` | **Reference Benchmark:** `Unspecified`
- **Provenance:** `ICMR_TREATMENT_GUIDELINES` (`UNVERIFIED`)
- **Status:** **UNVERIFIED**
- **Known Limitations & Assumptions:** High cumulative intensification (75-85%) reflects zero therapeutic inertia across repeated visits.

### Longitudinal: Chronic Complication Rate (`long_chronic_complication_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.0303` | **Reference Benchmark:** `0.04`
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
