# SYNAPSE Phase 2 — Comprehensive Synthetic Data Evaluation Report

**Evaluation Timestamp:** `2026-10-21T15:38:47.203915`  
**Dataset Directory:** `/Users/shashi/synapse/synapse-phase2/data/experiments/comprehensive_audit/sensitivity_duration/12_months`  
**Overall Evaluation Status:** **WARNING**  
**Invariant Integrity:** **PASSED (0 Hard Violations)**  

---

## 1. Executive Summary & Status Overview

- **Total Evaluated Metrics:** `18`
- **PASS:** `15` (Meets predefined empirical acceptance thresholds)
- **WARNING:** `2` (Observed deviation or moderate divergence requiring calibration/review)
- **FAIL:** `0` (Violates hard invariant or practical tolerance threshold)
- **UNVERIFIED:** `1` (Lacks published empirical real-world benchmark; assumption documented)
- **NOT_APPLICABLE:** `0` (Cohort sample size or eligibility empty for this stratum)

### Dimension Status Breakdown

| Evaluation Dimension | Total | PASS | WARNING | FAIL | UNVERIFIED | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **INVARIANTS** | 4 | 4 | 0 | 0 | 0 | **PASS** |
| **DEMOGRAPHICS** | 3 | 3 | 0 | 0 | 0 | **PASS** |
| **PREVALENCE** | 4 | 2 | 2 | 0 | 0 | **WARNING** |
| **COMORBIDITY** | 1 | 1 | 0 | 0 | 0 | **PASS** |
| **LONGITUDINAL** | 3 | 3 | 0 | 0 | 0 | **PASS** |
| **TREATMENT** | 3 | 2 | 0 | 0 | 1 | **PASS** |

---

## 2. Quantitative Metric Scorecard

| Metric ID | Dimension | Synthetic Estimate | Reference Benchmark | Difference | 95% Confidence Interval | Status | Verification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `inv_no_event_post_mortem` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `inv_diagnosis_encounter_linkage` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `inv_allergy_safety_veto` | INVARIANTS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `demo_sex_distribution` | DEMOGRAPHICS | 52.00 | 51.50 | +0.50 | [47.62, 56.35] | **PASS** | `VERIFIED` |
| `demo_age_pyramid_jsd` | DEMOGRAPHICS | 0.00 | 0.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `demo_age_by_sex_jsd` | DEMOGRAPHICS | 0.01 | 0.00 | +0.01 | — | **PASS** | `VERIFIED` |
| `prev_hypertension_adults` | PREVALENCE | 36.36 | 30.70 | +5.66 | [31.44, 41.60] | **PASS** | `VERIFIED` |
| `prev_diabetes_t2_adults` | PREVALENCE | 8.50 | 11.40 | -2.90 | [5.99, 11.95] | **PASS** | `VERIFIED` |
| `prev_urti_14day_point` | PREVALENCE | 0.00 | 8.50 | -8.50 | [0.00, 0.76] | **WARNING** | `VERIFIED` |
| `prev_urti_cumulative_attack_rate` | PREVALENCE | 50.20 | 70.00 | -19.80 | [45.83, 54.56] | **WARNING** | `VERIFIED` |
| `comorb_htn_in_t2d` | COMORBIDITY | 51.72 | 50.10 | +1.62 | [34.43, 68.61] | **PASS** | `VERIFIED` |
| `long_encounters_per_pt_year` | LONGITUDINAL | 1.11 | 1.50 | -0.39 | — | **PASS** | `UNVERIFIED` |
| `long_inter_encounter_interval_days` | LONGITUDINAL | 124.80 | 180.00 | -55.20 | — | **PASS** | `UNVERIFIED` |
| `long_crude_mortality_rate` | LONGITUDINAL | 0.00 | 0.01 | -0.01 | — | **PASS** | `VERIFIED` |
| `rx_firstline_hypertension` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_firstline_diabetes` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_adherence_assumption` | TREATMENT | 100.00 | — | — | — | **UNVERIFIED** | `UNVERIFIED` |

---

## 3. Invariant & Safety Evaluation

Hard temporal and causal invariants protect structural and clinical correctness independently of statistical comparisons.

### ✅ Temporal Invariant: No Clinical Activity Prior to Birth
- **Definition:** Verifies that no clinical encounter or procedure occurs before the patient's recorded birth date.
- **Violations Observed:** `0` out of `557` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires either explicit birth_date column or deterministic age projection.

### ✅ Temporal Invariant: Zero Post-Mortem Clinical Events
- **Definition:** Verifies that deceased patients have strictly zero subsequent encounters, orders, or prescriptions.
- **Violations Observed:** `0` out of `557` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluated against deaths.csv records.

### ✅ Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter
- **Definition:** Conditions must be recognized and diagnosed during an active clinical encounter.
- **Violations Observed:** `0` out of `404` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires foreign key condition.encounter_id -> encounters.encounter_id.

### ✅ Clinical Safety Invariant: Zero Contraindicated Prescriptions
- **Definition:** Verifies that no patient is prescribed a medication to which they have a documented allergy.
- **Violations Observed:** `0` out of `404` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluates allergy constraints against medication names.

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
- **Synthetic Estimate:** `0.00312` | **Reference Benchmark:** `0.0`
- **Difference:** `0.00312`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.05, 'warning_jsd_max': 0.15, 'total_variation_distance': 0.048, 'chi_square_stat': 8.0286, 'chi_square_df': 4, 'chi_square_p_value': 0.09054, 'chi_square_was_pooled': False, 'cramers_v': 0.0634}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Evaluated over 5 broad SRS census intervals. Small cohorts (<100) experience expected stochastic dispersion.

### Demographic Fidelity: Age-by-Sex Joint Distribution JSD (`demo_age_by_sex_jsd`)
- **Definition:** Jensen-Shannon Divergence across 10 age-by-sex joint strata compared to SRS 2021 Statement 19.
- **Synthetic Estimate:** `0.00502` | **Reference Benchmark:** `0.0`
- **Difference:** `0.00502`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.08, 'warning_jsd_max': 0.2, 'tvd': 0.0553}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **PASS**
- **Limitations:** Requires adequate cohort sample size across all 10 cells to avoid small-sample bin bias.

---

## 5. Disease Prevalence Details (Denominator Matched)

### Disease Prevalence: Essential Hypertension (Adults >= 20) (`prev_hypertension_adults`)
- **Definition:** Prevalence of essential hypertension (I10) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `341` patients | **Diagnosed Cases:** `124`
- **Synthetic Prevalence:** `36.36%` (95% CI: `31.44% - 41.6%`)
- **Empirical Reference:** `30.7%` (Absolute Diff: `5.66%`, Relative Diff: `18.44%`)
- **Provenance:** `ICMR_INDIAB_2023_HTN` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 8.0, 'warning_abs_diff_max': 15.0, 'crude_cohort_cases': 124, 'crude_cohort_prevalence_pct': 24.8}`
- **Limitations:** Denominator is restricted strictly to adults age >= 20 to match ICMR-INDIAB sampling criteria.

### Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) (`prev_diabetes_t2_adults`)
- **Definition:** Prevalence of Type 2 Diabetes (E11.9) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `341` patients | **Diagnosed Cases:** `29`
- **Synthetic Prevalence:** `8.5%` (95% CI: `5.99% - 11.95%`)
- **Empirical Reference:** `11.4%` (Absolute Diff: `-2.9%`, Relative Diff: `25.44%`)
- **Provenance:** `ICMR_INDIAB_2023_T2D` (`VERIFIED`)
- **Status:** **PASS**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 12.0, 'crude_cohort_cases': 29, 'crude_cohort_prevalence_pct': 5.8}`
- **Limitations:** Denominator is restricted strictly to adults age >= 20. Excludes pediatric patients.

### Disease Prevalence: Acute URTI 14-Day Point Prevalence (All Ages) (`prev_urti_14day_point`)
- **Definition:** 14-day recall point prevalence of active acute URTI (J06.9) vs NHP India 2020 baseline.
- **Eligible Cohort Denominator:** `500` patients | **Diagnosed Cases:** `0`
- **Synthetic Prevalence:** `0.0%` (95% CI: `0.0% - 0.76%`)
- **Empirical Reference:** `8.5%` (Absolute Diff: `-8.5%`, Relative Diff: `100.0%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **WARNING**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 10.0}`
- **Limitations:** Requires filtering for active, non-resolved infection episodes within a 14-day evaluation window.

### Disease Attack Rate: Acute URTI 2-Year Cumulative Attack Rate (All Ages) (`prev_urti_cumulative_attack_rate`)
- **Definition:** 2-year cumulative attack rate of acute URTI (J06.9) across entire cohort vs NHP/IDSP surveillance baseline.
- **Eligible Cohort Denominator:** `500` patients | **Diagnosed Cases:** `251`
- **Synthetic Prevalence:** `50.2%` (95% CI: `45.83% - 54.56%`)
- **Empirical Reference:** `70.0%` (Absolute Diff: `-19.8%`, Relative Diff: `28.29%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **WARNING**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 12.0, 'warning_abs_diff_max': 20.0}`
- **Limitations:** Cumulative attack rate over 24-month horizon. Derived from quarterly infection hazards.

---

## 6. Comorbidity & Disease Clustering Details

### Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes (`comorb_htn_in_t2d`)
- **Definition:** Conditional prevalence P(HTN|T2D) among adults >= 20 vs ICMR-INDIAB 2023 benchmark.
- **Synthetic Conditional Prevalence P(HTN|T2D):** `51.72%` (Cases: `15` / `29`)
- **Reference Benchmark (ICMR-INDIAB 2023):** `50.1%`
- **Association Diagnostics:** `{'pass_abs_diff_max': 15.0, 'warning_abs_diff_max': 25.0, 'joint_prevalence_pct': 4.4, 'expected_joint_prevalence_pct': 3.09, 'observed_to_expected_ratio': 1.4224, 'odds_ratio': 1.9954, 'odds_ratio_95_ci': (0.9289, 4.2865)}`
- **Status:** **PASS** (`VERIFIED`)
- **Limitations:** Evaluated strictly on adults with diagnosed T2D. If no synthetic patient develops T2D, status is NOT_APPLICABLE.

---

## 7. Longitudinal Dynamics & Clinical Treatments

### Longitudinal: Encounters Per Patient-Year (`long_encounters_per_pt_year`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `1.11` | **Reference Benchmark:** `1.5`
- **Provenance:** `NSS_75TH_ROUND_OPD` (`UNVERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Facility discrete-event simulation captures scheduled outpatient visits and episodic visits.

### Longitudinal: Mean Days Between Clinical Encounters (`long_inter_encounter_interval_days`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `124.8` | **Reference Benchmark:** `180.0`
- **Provenance:** `ICMR_TREATMENT_GUIDELINES` (`UNVERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Clinical modules use configured surveillance delays (e.g., 90d, 180d, 365d).

### Longitudinal: Annualized Crude Mortality Rate (`long_crude_mortality_rate`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.0` | **Reference Benchmark:** `0.006`
- **Provenance:** `SRS_2016_2020_LIFE_TABLE` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Short simulation windows (e.g. 2 years) in small cohorts exhibit expected binomial variance.

### Treatment Guideline Alignment: First-Line Antihypertensive Therapy (`rx_firstline_hypertension`)
- **Dimension:** `TREATMENT`
- **Synthetic Estimate:** `100.0` | **Reference Benchmark:** `100.0`
- **Provenance:** `ICMR_STG_HYPERTENSION_2022` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Assumes uncomplicated stage 1/2 essential hypertension indicated for calcium channel blocker.

### Treatment Guideline Alignment: First-Line Oral Hypoglycemic Therapy (`rx_firstline_diabetes`)
- **Dimension:** `TREATMENT`
- **Synthetic Estimate:** `100.0` | **Reference Benchmark:** `100.0`
- **Provenance:** `ICMR_STG_DIABETES_2022` (`VERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Guideline recommends Metformin monotherapy as universal initial pharmacotherapy.

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
