# Multi-Seed Monte Carlo Evaluation Summary (N=500, 10 Seeds)

**Seeds Evaluated:** `[42, 101, 202, 303, 404, 505, 606, 707, 808, 909]`  
**Timestamp:** `2026-10-21T15:38:03.871912`  

This analysis distinguishes random stochastic sampling variability from systematic structural model bias.

| Metric ID | Metric Name | Reference | Mean Synthetic | Std Dev (σ) | Monte Carlo SE | Min | Max | Systematic Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | Temporal Invariant: No Clinical Activity Prior to Birth | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_no_event_post_mortem` | Temporal Invariant: Zero Post-Mortem Clinical Events | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_diagnosis_encounter_linkage` | Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_allergy_safety_veto` | Clinical Safety Invariant: Zero Contraindicated Prescriptions | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `demo_sex_distribution` | Demographic Fidelity: Male Sex Proportion | 51.50 | **51.40** | 1.75 | 0.55 | 49.20 | 54.00 | -0.10 |
| `demo_age_pyramid_jsd` | Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `demo_age_by_sex_jsd` | Demographic Fidelity: Age-by-Sex Joint Distribution JSD | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.01 | +0.00 |
| `prev_hypertension_adults` | Disease Prevalence: Essential Hypertension (Adults >= 20) | 30.70 | **35.90** | 1.74 | 0.55 | 32.94 | 39.30 | +5.20 |
| `prev_diabetes_t2_adults` | Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) | 11.40 | **13.62** | 2.26 | 0.72 | 9.09 | 15.93 | +2.22 |
| `prev_urti_14day_point` | Disease Prevalence: Acute URTI 14-Day Point Prevalence (All Ages) | 8.50 | **4.60** | 0.67 | 0.21 | 3.60 | 5.60 | -3.90 |
| `prev_urti_cumulative_attack_rate` | Disease Attack Rate: Acute URTI 2-Year Cumulative Attack Rate (All Ages) | 70.00 | **72.74** | 2.12 | 0.67 | 69.60 | 75.20 | +2.74 |
| `comorb_htn_in_t2d` | Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes | 50.10 | **50.17** | 5.91 | 1.87 | 40.74 | 58.70 | +0.07 |
| `long_encounters_per_pt_year` | Longitudinal: Encounters Per Patient-Year | 1.50 | **0.92** | 0.03 | 0.01 | 0.88 | 0.96 | -0.58 |
| `long_inter_encounter_interval_days` | Longitudinal: Mean Days Between Clinical Encounters | 180.00 | **144.37** | 2.28 | 0.72 | 141.70 | 147.70 | -35.63 |
| `long_crude_mortality_rate` | Longitudinal: Annualized Crude Mortality Rate | 0.01 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | -0.00 |
| `rx_firstline_hypertension` | Treatment Guideline Alignment: First-Line Antihypertensive Therapy | 100.00 | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | +0.00 |
| `rx_firstline_diabetes` | Treatment Guideline Alignment: First-Line Oral Hypoglycemic Therapy | 100.00 | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | +0.00 |
| `rx_adherence_assumption` | Treatment Pattern: Perfect Adherence Assumption Disclosure | — | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | — |