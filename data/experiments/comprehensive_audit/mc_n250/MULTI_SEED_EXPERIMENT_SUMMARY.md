# Multi-Seed Monte Carlo Evaluation Summary (N=250, 10 Seeds)

**Seeds Evaluated:** `[42, 101, 202, 303, 404, 505, 606, 707, 808, 909]`  
**Timestamp:** `2026-10-21T15:37:54.241104`  

This analysis distinguishes random stochastic sampling variability from systematic structural model bias.

| Metric ID | Metric Name | Reference | Mean Synthetic | Std Dev (σ) | Monte Carlo SE | Min | Max | Systematic Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | Temporal Invariant: No Clinical Activity Prior to Birth | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_no_event_post_mortem` | Temporal Invariant: Zero Post-Mortem Clinical Events | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_diagnosis_encounter_linkage` | Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_allergy_safety_veto` | Clinical Safety Invariant: Zero Contraindicated Prescriptions | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `demo_sex_distribution` | Demographic Fidelity: Male Sex Proportion | 51.50 | **50.56** | 3.83 | 1.21 | 45.20 | 56.80 | -0.94 |
| `demo_age_pyramid_jsd` | Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `demo_age_by_sex_jsd` | Demographic Fidelity: Age-by-Sex Joint Distribution JSD | 0.00 | **0.01** | 0.00 | 0.00 | 0.01 | 0.01 | +0.01 |
| `prev_hypertension_adults` | Disease Prevalence: Essential Hypertension (Adults >= 20) | 30.70 | **36.82** | 3.22 | 1.02 | 31.33 | 41.21 | +6.12 |
| `prev_diabetes_t2_adults` | Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) | 11.40 | **13.36** | 3.58 | 1.13 | 6.94 | 18.67 | +1.96 |
| `prev_urti_14day_point` | Disease Prevalence: Acute URTI 14-Day Point Prevalence (All Ages) | 8.50 | **4.68** | 0.84 | 0.27 | 3.20 | 6.00 | -3.82 |
| `prev_urti_cumulative_attack_rate` | Disease Attack Rate: Acute URTI 2-Year Cumulative Attack Rate (All Ages) | 70.00 | **72.04** | 2.91 | 0.92 | 66.80 | 75.60 | +2.04 |
| `comorb_htn_in_t2d` | Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes | 50.10 | **51.19** | 8.22 | 2.60 | 37.50 | 63.64 | +1.09 |
| `long_encounters_per_pt_year` | Longitudinal: Encounters Per Patient-Year | 1.50 | **0.93** | 0.06 | 0.02 | 0.85 | 1.00 | -0.57 |
| `long_inter_encounter_interval_days` | Longitudinal: Mean Days Between Clinical Encounters | 180.00 | **145.23** | 4.08 | 1.29 | 140.10 | 152.20 | -34.77 |
| `long_crude_mortality_rate` | Longitudinal: Annualized Crude Mortality Rate | 0.01 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | -0.00 |
| `rx_firstline_hypertension` | Treatment Guideline Alignment: First-Line Antihypertensive Therapy | 100.00 | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | +0.00 |
| `rx_firstline_diabetes` | Treatment Guideline Alignment: First-Line Oral Hypoglycemic Therapy | 100.00 | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | +0.00 |
| `rx_adherence_assumption` | Treatment Pattern: Perfect Adherence Assumption Disclosure | — | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | — |