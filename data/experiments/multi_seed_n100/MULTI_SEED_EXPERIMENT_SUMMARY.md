# Multi-Seed Monte Carlo Evaluation Summary (N=100, 5 Seeds)

**Seeds Evaluated:** `[42, 101, 202, 303, 404]`  
**Timestamp:** `2026-10-21T14:19:59.923039`  

This analysis distinguishes random stochastic sampling variability from systematic structural model bias.

| Metric ID | Metric Name | Reference | Mean Synthetic | Std Dev (σ) | Monte Carlo SE | Min | Max | Systematic Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | Temporal Invariant: No Clinical Activity Prior to Birth | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_no_event_post_mortem` | Temporal Invariant: Zero Post-Mortem Clinical Events | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_diagnosis_encounter_linkage` | Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `inv_allergy_safety_veto` | Clinical Safety Invariant: Zero Contraindicated Prescriptions | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 | 0.00 | +0.00 |
| `demo_sex_distribution` | Demographic Fidelity: Male Sex Proportion | 51.50 | **53.40** | 3.36 | 1.50 | 48.00 | 57.00 | +1.90 |
| `demo_age_pyramid_jsd` | Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence | 0.00 | **0.01** | 0.00 | 0.00 | 0.00 | 0.01 | +0.01 |
| `demo_age_by_sex_jsd` | Demographic Fidelity: Age-by-Sex Joint Distribution JSD | 0.00 | **0.02** | 0.00 | 0.00 | 0.01 | 0.02 | +0.02 |
| `prev_hypertension_adults` | Disease Prevalence: Essential Hypertension (Adults >= 20) | 30.70 | **42.96** | 3.57 | 1.60 | 39.47 | 47.83 | +12.26 |
| `prev_diabetes_t2_adults` | Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20) | 11.40 | **25.40** | 4.79 | 2.14 | 19.12 | 31.82 | +14.00 |
| `prev_urti_all_ages` | Disease Prevalence: Acute Upper Respiratory Tract Infection (All Ages) | 8.50 | **74.00** | 2.65 | 1.18 | 71.00 | 78.00 | +65.50 |
| `comorb_htn_in_t2d` | Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes | 50.10 | **49.11** | 11.41 | 5.10 | 31.58 | 62.50 | -0.99 |
| `long_encounters_per_pt_year` | Longitudinal: Encounters Per Patient-Year | 1.50 | **0.99** | 0.05 | 0.02 | 0.93 | 1.05 | -0.51 |
| `long_inter_encounter_interval_days` | Longitudinal: Mean Days Between Clinical Encounters | 180.00 | **147.14** | 7.66 | 3.43 | 140.70 | 159.30 | -32.86 |
| `long_crude_mortality_rate` | Longitudinal: Annualized Crude Mortality Rate | 0.01 | **0.00** | 0.00 | 0.00 | 0.00 | 0.01 | -0.00 |
| `rx_firstline_hypertension` | Treatment Guideline Alignment: First-Line Antihypertensive Therapy | 100.00 | **87.38** | 3.87 | 1.73 | 84.00 | 93.94 | -12.62 |
| `rx_firstline_diabetes` | Treatment Guideline Alignment: First-Line Oral Hypoglycemic Therapy | 100.00 | **95.87** | 4.11 | 1.84 | 90.48 | 100.00 | -4.13 |
| `rx_adherence_assumption` | Treatment Pattern: Perfect Adherence Assumption Disclosure | — | **100.00** | 0.00 | 0.00 | 100.00 | 100.00 | — |