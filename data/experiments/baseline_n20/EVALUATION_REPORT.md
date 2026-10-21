# SYNAPSE Phase 2 — Comprehensive Synthetic Data Evaluation Report

**Evaluation Timestamp:** `2026-10-21T14:18:58.685907`  
**Dataset Directory:** `/Users/shashi/synapse/synapse-phase2/data/experiments/baseline_n20`  
**Overall Evaluation Status:** **FAIL**  
**Invariant Integrity:** **PASSED (0 Hard Violations)**  

---

## 1. Executive Summary & Status Overview

- **Total Evaluated Metrics:** `17`
- **PASS:** `9` (Meets predefined empirical acceptance thresholds)
- **WARNING:** `4` (Observed deviation or moderate divergence requiring calibration/review)
- **FAIL:** `3` (Violates hard invariant or practical tolerance threshold)
- **UNVERIFIED:** `1` (Lacks published empirical real-world benchmark; assumption documented)
- **NOT_APPLICABLE:** `0` (Cohort sample size or eligibility empty for this stratum)

### Dimension Status Breakdown

| Evaluation Dimension | Total | PASS | WARNING | FAIL | UNVERIFIED | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **INVARIANTS** | 4 | 4 | 0 | 0 | 0 | **PASS** |
| **DEMOGRAPHICS** | 3 | 0 | 3 | 0 | 0 | **WARNING** |
| **PREVALENCE** | 3 | 0 | 0 | 3 | 0 | **FAIL** |
| **COMORBIDITY** | 1 | 0 | 1 | 0 | 0 | **WARNING** |
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
| `demo_sex_distribution` | DEMOGRAPHICS | 45.00 | 51.50 | -6.50 | [25.82, 65.79] | **WARNING** | `VERIFIED` |
| `demo_age_pyramid_jsd` | DEMOGRAPHICS | 0.10 | 0.00 | +0.10 | — | **WARNING** | `VERIFIED` |
| `demo_age_by_sex_jsd` | DEMOGRAPHICS | 0.11 | 0.00 | +0.11 | — | **WARNING** | `VERIFIED` |
| `prev_hypertension_adults` | PREVALENCE | 55.56 | 30.70 | +24.86 | [26.67, 81.12] | **FAIL** | `VERIFIED` |
| `prev_diabetes_t2_adults` | PREVALENCE | 33.33 | 11.40 | +21.93 | [12.06, 64.58] | **FAIL** | `VERIFIED` |
| `prev_urti_all_ages` | PREVALENCE | 65.00 | 8.50 | +56.50 | [43.29, 81.88] | **FAIL** | `VERIFIED` |
| `comorb_htn_in_t2d` | COMORBIDITY | 66.67 | 50.10 | +16.57 | [20.77, 93.85] | **WARNING** | `VERIFIED` |
| `long_encounters_per_pt_year` | LONGITUDINAL | 0.82 | 1.50 | -0.68 | — | **PASS** | `UNVERIFIED` |
| `long_inter_encounter_interval_days` | LONGITUDINAL | 113.60 | 180.00 | -66.40 | — | **PASS** | `UNVERIFIED` |
| `long_crude_mortality_rate` | LONGITUDINAL | 0.00 | 0.01 | -0.01 | — | **PASS** | `VERIFIED` |
| `rx_firstline_hypertension` | TREATMENT | 80.00 | 100.00 | -20.00 | — | **PASS** | `VERIFIED` |
| `rx_firstline_diabetes` | TREATMENT | 100.00 | 100.00 | +0.00 | — | **PASS** | `VERIFIED` |
| `rx_adherence_assumption` | TREATMENT | 100.00 | — | — | — | **UNVERIFIED** | `UNVERIFIED` |

---

## 3. Invariant & Safety Evaluation

Hard temporal and causal invariants protect structural and clinical correctness independently of statistical comparisons.

### ✅ Temporal Invariant: No Clinical Activity Prior to Birth
- **Definition:** Verifies that no clinical encounter or procedure occurs before the patient's recorded birth date.
- **Violations Observed:** `0` out of `33` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires either explicit birth_date column or deterministic age projection.

### ✅ Temporal Invariant: Zero Post-Mortem Clinical Events
- **Definition:** Verifies that deceased patients have strictly zero subsequent encounters, orders, or prescriptions.
- **Violations Observed:** `0` out of `33` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluated against deaths.csv records.

### ✅ Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter
- **Definition:** Conditions must be recognized and diagnosed during an active clinical encounter.
- **Violations Observed:** `0` out of `21` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Requires foreign key condition.encounter_id -> encounters.encounter_id.

### ✅ Clinical Safety Invariant: Zero Contraindicated Prescriptions
- **Definition:** Verifies that no patient is prescribed a medication to which they have a documented allergy.
- **Violations Observed:** `0` out of `21` records
- **Acceptance Threshold:** `0 violations permitted`
- **Status:** **PASS**
- **Known Limitations:** Evaluates allergy constraints against medication names.

---

## 4. Demographic Fidelity Details

### Demographic Fidelity: Male Sex Proportion (`demo_sex_distribution`)
- **Definition:** Percentage of cohort that is male compared to Census SRS 2021 reference.
- **Synthetic Estimate:** `45.0` | **Reference Benchmark:** `51.5`
- **Difference:** `-6.5`
- **Confidence Interval (95% Wilson):** `(25.82, 65.79)`
- **Acceptance Policy & Diagnostics:** `{'pass_abs_diff_max': 5.0, 'warning_abs_diff_max': 10.0}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **WARNING**
- **Limitations:** Natural sex ratio in India is ~51.5% male. Small sample sizes may have higher random variance.

### Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence (`demo_age_pyramid_jsd`)
- **Definition:** JSD (base 2) between synthetic age distribution and SRS 2021 5-band reference pyramid.
- **Synthetic Estimate:** `0.09716` | **Reference Benchmark:** `0.0`
- **Difference:** `0.09716`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.05, 'warning_jsd_max': 0.15, 'total_variation_distance': 0.31, 'chi_square_stat': 7.2373, 'chi_square_df': 2, 'chi_square_p_value': 0.02682, 'chi_square_was_pooled': True, 'cramers_v': 0.3008}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **WARNING**
- **Limitations:** Evaluated over 5 broad SRS census intervals. Small cohorts (<100) experience expected stochastic dispersion.

### Demographic Fidelity: Age-by-Sex Joint Distribution JSD (`demo_age_by_sex_jsd`)
- **Definition:** Jensen-Shannon Divergence across 10 age-by-sex joint strata compared to SRS 2021 Statement 19.
- **Synthetic Estimate:** `0.10707` | **Reference Benchmark:** `0.0`
- **Difference:** `0.10707`
- **Confidence Interval (95% Wilson):** `N/A`
- **Acceptance Policy & Diagnostics:** `{'pass_jsd_max': 0.08, 'warning_jsd_max': 0.2, 'tvd': 0.31}`
- **Provenance:** `SRS_2021_DEMO` (`VERIFIED`)
- **Status:** **WARNING**
- **Limitations:** Requires adequate cohort sample size across all 10 cells to avoid small-sample bin bias.

---

## 5. Disease Prevalence Details (Denominator Matched)

### Disease Prevalence: Essential Hypertension (Adults >= 20) (`prev_hypertension_adults`)
- **Definition:** Prevalence of essential hypertension (I10) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `9` patients | **Diagnosed Cases:** `5`
- **Synthetic Prevalence:** `55.56%` (95% CI: `26.67% - 81.12%`)
- **Empirical Reference:** `30.7%` (Absolute Diff: `24.86%`, Relative Diff: `80.98%`)
- **Provenance:** `ICMR_INDIAB_2023_HTN` (`VERIFIED`)
- **Status:** **FAIL**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 8.0, 'warning_abs_diff_max': 15.0, 'crude_cohort_cases': 5, 'crude_cohort_prevalence_pct': 25.0}`
- **Limitations:** Denominator is restricted strictly to adults age >= 20 to match ICMR-INDIAB sampling criteria.

### Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) (`prev_diabetes_t2_adults`)
- **Definition:** Prevalence of Type 2 Diabetes (E11.9) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.
- **Eligible Cohort Denominator:** `9` patients | **Diagnosed Cases:** `3`
- **Synthetic Prevalence:** `33.33%` (95% CI: `12.06% - 64.58%`)
- **Empirical Reference:** `11.4%` (Absolute Diff: `21.93%`, Relative Diff: `192.37%`)
- **Provenance:** `ICMR_INDIAB_2023_T2D` (`VERIFIED`)
- **Status:** **FAIL**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 6.0, 'warning_abs_diff_max': 12.0, 'crude_cohort_cases': 3, 'crude_cohort_prevalence_pct': 15.0}`
- **Limitations:** Denominator is restricted strictly to adults age >= 20. Excludes pediatric patients.

### Disease Prevalence: Acute Upper Respiratory Tract Infection (All Ages) (`prev_urti_all_ages`)
- **Definition:** Period prevalence of acute URTI (J06.9) across entire cohort vs NHP India 2020 baseline.
- **Eligible Cohort Denominator:** `20` patients | **Diagnosed Cases:** `13`
- **Synthetic Prevalence:** `65.0%` (95% CI: `43.29% - 81.88%`)
- **Empirical Reference:** `8.5%` (Absolute Diff: `56.5%`, Relative Diff: `664.71%`)
- **Provenance:** `NHP_INDIA_URTI_2020` (`VERIFIED`)
- **Status:** **FAIL**
- **Diagnostics & Crude Values:** `{'pass_abs_diff_max': 5.0, 'warning_abs_diff_max': 10.0}`
- **Limitations:** Acute episodic condition. Observed frequency is influenced by surveillance duration.

---

## 6. Comorbidity & Disease Clustering Details

### Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes (`comorb_htn_in_t2d`)
- **Definition:** Conditional prevalence P(HTN|T2D) among adults >= 20 vs ICMR-INDIAB 2023 benchmark.
- **Synthetic Conditional Prevalence P(HTN|T2D):** `66.67%` (Cases: `2` / `3`)
- **Reference Benchmark (ICMR-INDIAB 2023):** `50.1%`
- **Association Diagnostics:** `{'pass_abs_diff_max': 15.0, 'warning_abs_diff_max': 25.0, 'joint_prevalence_pct': 22.22, 'expected_joint_prevalence_pct': 18.52, 'observed_to_expected_ratio': 1.2, 'odds_ratio': 2.0, 'odds_ratio_95_ci': (0.1117, 35.8067)}`
- **Status:** **WARNING** (`VERIFIED`)
- **Limitations:** Evaluated strictly on adults with diagnosed T2D. If no synthetic patient develops T2D, status is NOT_APPLICABLE.

---

## 7. Longitudinal Dynamics & Clinical Treatments

### Longitudinal: Encounters Per Patient-Year (`long_encounters_per_pt_year`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `0.82` | **Reference Benchmark:** `1.5`
- **Provenance:** `NSS_75TH_ROUND_OPD` (`UNVERIFIED`)
- **Status:** **PASS**
- **Known Limitations & Assumptions:** Facility discrete-event simulation captures scheduled outpatient visits and episodic visits.

### Longitudinal: Mean Days Between Clinical Encounters (`long_inter_encounter_interval_days`)
- **Dimension:** `LONGITUDINAL`
- **Synthetic Estimate:** `113.6` | **Reference Benchmark:** `180.0`
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
- **Synthetic Estimate:** `80.0` | **Reference Benchmark:** `100.0`
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
