# SYNAPSE Phase 2: Calibration vs. Evaluation Leakage Assessment

**Document ID:** `SYNAPSE-LEAKAGE-AUDIT-03`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Readiness Assessment Authority  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary & Audit Rationale

A foundational principle of scientific simulation modeling is the **strict separation between calibration data and evaluation data**:
- **Calibration Data:** Real-world empirical data used to fit, tune, or select model parameters (e.g., initial condition prevalence, demographic pyramids, disease incidence hazards, and state transition probabilities).
- **Internal Validation Holdout:** Stratified subsets or holdout splits derived from the *same* underlying survey or study sample (e.g. sex-specific prevalence from the same national survey). While valuable for testing internal consistency, internal holdouts share identical sampling frames, instruments, biases, and historical contexts. They **cannot** establish external generalizability.
- **Independent External Evaluation Data:** Truly independent datasets collected by separate investigators, on distinct patient cohorts, using independent sampling frames and measurement protocols. Only independent external datasets can evaluate real-world generalizability and predictive fidelity.

This audit examines the complete parameter inventory of SYNAPSE Phase 2, maps every parameter to its underlying evidence source, identifies historical data leakage, and establishes a clean governance boundary.

---

## 2. Complete Model Parameter Provenance Inventory

The table below catalogs every empirical parameter currently utilized in [config/population/india_default_v1.yaml](file:///Users/shashi/synapse/synapse-phase2/config/population/india_default_v1.yaml), [config/modules/](file:///Users/shashi/synapse/synapse-phase2/config/modules/), and [synapse_simulator/evaluation/reference_data.py](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/reference_data.py):

| Component | Parameter Identifier | Model Value | Source Citation | Provenance ID | Scientific Role & Leakage Status |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Demographics** | `male_ratio` | $0.515$ ($51.5\%$) | Census SRS Statistical Report 2021 | `SRS_2021_DEMO` | **LEAKED / CALIBRATION.** Primary generative weight. Cannot be reused as independent evaluation. |
| **Demographics** | `age_pyramid_bands` | 5 Census Bands | Census SRS Statistical Report 2021 | `SRS_2021_DEMO` | **LEAKED / CALIBRATION.** Primary generative weights. |
| **Demographics** | `age_by_sex_matrix` | 10 Strata Weights | Census SRS 2021 Statement 19 | `SRS_2021_DEMO` | **INTERNAL HOLDOUT.** Joint distribution from same census. |
| **Mortality** | `mortality.bands (qx)` | 10 Age Bands | Census SRS Abridged Life Tables 2016–2020 | `SRS_2016_2020_LIFE_TABLE` | **LEAKED / CALIBRATION.** Directly parameterizes weekly Bernoulli hazard stepping. |
| **Epidemiology** | `I10.prevalence_percent` | $30.7\%$ (Age $\ge 20$) | ICMR-INDIAB Study (*Lancet Diabetes Endocrinol* 2023) | `ICMR_INDIAB_2023_HTN` | **LEAKED / CALIBRATION.** Baseline condition assignment target. Disqualified from external evaluation. |
| **Epidemiology** | `I10.annual_incidence_rate` | $0.035\text{ yr}^{-1}$ | CURES / CCDC Cohort Studies (Prabhakaran et al. 2017) | `CURES_CCDC_HYPERTENSION_INCIDENCE_2014` | **LEAKED / CALIBRATION.** Informs annual background disease progression hazard. |
| **Epidemiology** | `E11.9.prevalence_percent` | $11.4\%$ (Age $\ge 20$) | ICMR-INDIAB Study (*Lancet Diabetes Endocrinol* 2023) | `ICMR_INDIAB_2023_T2D` | **LEAKED / CALIBRATION.** Baseline condition assignment target. Disqualified from external evaluation. |
| **Epidemiology** | `E11.9.annual_incidence_rate`| $0.015\text{ yr}^{-1}$ | CARRS Cohort Study (Prabhakaran et al. *BMJ Open* 2021) | `CARRS_DIABETES_INCIDENCE_2021` | **LEAKED / CALIBRATION.** Informs background incident diabetes hazard. |
| **Epidemiology** | `E11.9.male_prevalence` | $12.1\%$ | ICMR-INDIAB Study (*Lancet Diabetes Endocrinol* 2023) | `ICMR_INDIAB_2023_T2D` | **INTERNAL HOLDOUT.** Sub-stratum from same study. Proves internal consistency, not external validity. |
| **Epidemiology** | `E11.9.female_prevalence` | $10.7\%$ | ICMR-INDIAB Study (*Lancet Diabetes Endocrinol* 2023) | `ICMR_INDIAB_2023_T2D` | **INTERNAL HOLDOUT.** Sub-stratum from same study. Proves internal consistency, not external validity. |
| **Epidemiology** | `J06.9.prevalence_percent` | $8.5\%$ | National Health Portal India 2020 (Acute ARI) | `NHP_INDIA_URTI_2020` | **LEAKED / CALIBRATION.** Generative parameter for baseline acute URTI. |
| **Epidemiology** | `J06.9.annual_incidence_rate`| $0.45\text{ yr}^{-1}$ | NHP India / IDSP Surveillance Baseline 2020 | `NHP_INDIA_URTI_2020` | **LEAKED / CALIBRATION.** Informs periodic acute attack rate. |
| **Clinical Module**| `HTN.first_line_drug` | Amlodipine 5mg | ICMR Standard Treatment Guidelines 2022 | `ICMR_STG_HYPERTENSION_2022` | **LEAKED / RULE SPECIFICATION.** Encoded directly into state machine transition rules. |
| **Clinical Module**| `HTN.step_up_drug` | Telmisartan 40mg | ICMR Standard Treatment Guidelines 2022 | `ICMR_STG_HYPERTENSION_2022` | **LEAKED / RULE SPECIFICATION.** Encoded directly into state machine transition rules. |
| **Clinical Module**| `T2D.first_line_drug` | Metformin 500mg | ICMR Standard Treatment Guidelines 2022 | `ICMR_STG_DIABETES_2022` | **LEAKED / RULE SPECIFICATION.** Encoded directly into state machine transition rules. |
| **Clinical Module**| `T2D.step_up_drug` | Glimepiride 1mg | ICMR Standard Treatment Guidelines 2022 | `ICMR_STG_DIABETES_2022` | **LEAKED / RULE SPECIFICATION.** Encoded directly into state machine transition rules. |
| **Clinical Module**| `HTN.ckd_transition_weight` | $0.015$ / 180d | CURES-45 / CCDC Prospective Cohort Studies | `CURES_CCDC_PROSPECTIVE_HTN` | **CALIBRATED.** Manually selected to yield $\sim 3\text{--}4\%$ 2-year cumulative target-organ damage. |
| **Clinical Module**| `T2D.nephropathy_weight` | $0.010$ / 90d | CURES-45 / CCDC Prospective Cohort Studies | `CURES_CCDC_PROSPECTIVE_T2D` | **CALIBRATED.** Manually selected to yield $\sim 3\text{--}4\%$ 2-year cumulative target-organ damage. |

---

## 3. Analysis of Historical Data Leakage and Circular Evaluation

### 3.1 The Circular Evaluation Trap
Prior evaluation iterations evaluated synthetic disease prevalence against ICMR-INDIAB and claimed a **`PASS`** with zero difference:
- In `config/population/india_default_v1.yaml`, the generator is explicitly instructed to assign hypertension to $30.7\%$ of adults aged $\ge 20$.
- In `DatasetEvaluator.evaluate_disease_prevalences()`, the metric `prev_hypertension_adults` compares the synthetic adult prevalence ($32.53\%$) against $30.7\%$ from ICMR-INDIAB.
- **The Methodological Fallacy:** Comparing a synthetic output to the exact number used to seed the synthetic generator is **circular**. It verifies that the generator's pseudo-random sampler functions correctly; it does **not** validate that the synthetic data mirrors the real world.
- **Remediation:** In [reference_data.py](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/reference_data.py#L165), `prev_htn_adults` and `prev_t2d_adults` are formally classified as `BenchmarkRole.CALIBRATION`. They must never be presented as external validation evidence.

### 3.2 The Subgroup Holdout Fallacy
A secondary methodological flaw identified in the baseline report was claiming external validity from sex-stratified holdout comparisons (`prev_t2d_male_subgroup = 12.1%` and `prev_t2d_female_subgroup = 10.7%`).
- Both male and female prevalence statistics originate from the **exact same ICMR-INDIAB survey sample** ($n=113,043$).
- Evaluating male and female sub-strata proves that the conditional sampling logic preserves subgroup proportions. It does **not** prove external validity.
- **Remediation:** In [reference_data.py](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/reference_data.py#L262), subgroup statistics are formally classified as `BenchmarkRole.INTERNAL_VALIDATION_HOLDOUT`.

### 3.3 The Actuarial Mortality Equivalence Fallacy
SYNAPSE generates patient deaths by querying age-specific hazard rates $q_x(\text{age})$ from the Census SRS 2016–2020 Life Table at each weekly timestep:
- Demonstrating that the synthetic cohort's deaths match the actuarial expectation ($\mu_D = 11.68, D_{\text{obs}} = 14.0$) verifies software adherence to the mathematical life table.
- It does **not** prove national crude mortality fidelity, because the synthetic population's elderly age distribution reflects an assumption (uniform draw in 65–100) rather than empirical census survival.
- **Remediation:** In [validation_decisions_and_limitations.md](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/validation_decisions_and_limitations.md), crude mortality is classified as `WARNING`, with explicit disclosure of the elderly sampling skew.

---

## 4. Recommended Clean Data Separation Framework

To ensure that future external validation studies are scientifically defensible, data sources are partitioned into three strictly segregated tiers:

```
Three-Tier Data Governance Architecture:
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: CALIBRATION BENCHMARKS (Model Fitting & Parameterization)                      │
│ - Census SRS 2021 (Sex ratio: 51.5%, 5-band age pyramid)                              │
│ - Census SRS Life Tables 2016–2020 (qx age-specific mortality rates)                  │
│ - ICMR-INDIAB 2023 (Baseline adult HTN: 30.7%, T2D: 11.4%, comorbidity: 50.1%)       │
│ - ICMR Standard Treatment Guidelines 2022 (First-line & step-up drug protocols)       │
│ - NHP India 2020 (URTI point prevalence: 8.5%, annual incidence: 0.45/yr)             │
│                                                                                        │
│ TIER 2: INTERNAL VALIDATION HOLDOUTS (Consistency & Architecture Checks)               │
│ - ICMR-INDIAB Sex-Stratified Prevalences (Male T2D: 12.1%, Female T2D: 10.7%)         │
│ - Census SRS Statement 19 Age-by-Sex Joint Distribution (10 strata JSD)               │
│ - Poisson-Binomial Cohort Actuarial Expected Deaths (Expected vs. Observed)           │
│                                                                                        │
│ TIER 3: INDEPENDENT EXTERNAL EVALUATION DATASETS (Unbiased Generalization Audit)       │
│ - LASI Wave 1 Individual-Level Microdata (National older-adult cohort, 45+)           │
│ - NFHS-5 Survey Microdata (National cross-sectional BP & blood glucose, 15–54)        │
│ - CARRS Prospective Longitudinal Cohort (Independent 6-year urban incidence & CKD)   │
│ - IHCI Routine Primary Healthcare Registry (Real-world clinical prescribing inertia)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Transparent Interim Evaluation Plan

Because acquiring full longitudinal microdata from prospective clinical cohorts (such as CARRS) or administrative registries (such as IHCI) requires formal data-access committee reviews and ministerial data-use agreements taking 3 to 6 months, an interim evaluation plan is established:

### Interim Protocol Execution Steps:
1. **Tier 3A: Immediate Microdata Validation using LASI Wave 1:**
   - Download de-identified LASI Wave 1 individual microdata via Gateway to Global Aging Data ([g2aging.org](https://g2aging.org)).
   - Truncate the SYNAPSE synthetic population to match LASI eligibility ($age \ge 45\text{ years}$).
   - Execute continuous distributional comparisons on Omron blood pressure measurements (SBP and DBP) and dried blood spot $\text{HbA1c}$ distributions using Kolmogorov-Smirnov and Wasserstein distance tests.
   - Evaluate multi-drug medication rosters (monotherapy vs. dual therapy) among older adults.
2. **Tier 3B: Cross-Sectional Multi-State Prevalence using NFHS-5:**
   - Ingest NFHS-5 de-identified microdata via DHS Program.
   - Compare age-stratified blood pressure distributions and untreated vs. treated SBP levels across synthetic and empirical cohorts.
3. **Explicit Boundary Disclosure:**
   - The interim evaluation plan must explicitly disclose that cross-sectional survey comparisons (LASI Wave 1 and NFHS-5) **cannot** validate prospective longitudinal incidence, inter-encounter follow-up intervals, or prospective target-organ complication hazards.
   - A complete longitudinal validation verdict remains conditional upon prospective cohort data access (CARRS or IHCI).
