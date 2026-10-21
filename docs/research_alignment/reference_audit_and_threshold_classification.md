# SYNAPSE Phase 2 — Reference Statistics Audit & Threshold Classification

## 1. Scientific Verification of Calibration Benchmarks

Before applying any reference statistic as a calibration benchmark or evaluation ground truth, its underlying epidemiology, publication methodology, and observation period were audited.

### 1.1 Audit of Proposed Benchmarks

| Benchmark Quantity | Cited Value | Actual Source Publication | Study Type | Observation Period | Geographic Scope | Eligible Population | Quantity Type | Suitability & Limitations |
| :--- | :---: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Adult Hypertension Prevalence** | **30.7%** | Anjana et al., *Lancet Diabetes Endocrinol* 2023;11(7):474-489 (ICMR-INDIAB) | Cross-sectional multi-stage cluster ($N=113,043$) | 2008–2020 (phased) | National (31 States/UTs), India | Adults aged $\ge 20$ years | **Cross-sectional prevalence** | **Calibration Target (Baseline).** Excludes pediatric patients ($< 20$). Cannot be used as an incidence rate. |
| **Adult Hypertension Annual Incidence** | **3.5% / yr** | Anchala et al., *J Hypertens* 2014; Prabhakaran et al., *J Am Heart Assoc* 2017; CURES Cohort (Deepa et al.) | Prospective longitudinal cohort studies | 2005–2018 | Urban & Rural Indian cohorts | Normotensive adults aged 20–70 | **Annual incidence rate ($\lambda = 0.035$)** | **Calibration Target (Incidence).** Grounded in CARRS/CURES prospective studies, NOT the cross-sectional ICMR-INDIAB 2023 paper. |
| **Adult Type 2 Diabetes Prevalence** | **11.4%** | Anjana et al., *Lancet Diabetes Endocrinol* 2023;11(7):474-489 (ICMR-INDIAB) | Cross-sectional multi-stage cluster ($N=113,043$) | 2008–2020 | National (31 States/UTs), India | Adults aged $\ge 20$ years | **Cross-sectional prevalence** | **Calibration Target (Baseline).** Excludes pediatric patients. |
| **Adult Type 2 Diabetes Annual Incidence** | **1.5% / yr** | Mohan et al., *BMJ Open* 2021; Gujral et al., *Lancet Diabetes Endocrinol* 2020 (CARRS Study) | Prospective longitudinal cohort ($N \approx 12,000$) | 2010–2016 | Urban South Asia (Delhi, Chennai) | Adults aged $\ge 20$ free of baseline diabetes | **Annual incidence rate ($\lambda = 0.015$)** | **Calibration Target (Incidence).** True incidence from CARRS cohort: prediabetes conversion is 5–7%/yr, normoglycemia is 1.2%/yr, pooled average ~1.5%/yr. |
| **Hypertension in Type 2 Diabetes Comorbidity** | **50.1%** | Anjana et al., *Lancet Diabetes Endocrinol* 2023;11(7):474-489 (Table 3) | Cross-sectional subgroup analysis | 2008–2020 | National, India | Adults $\ge 20$ with diagnosed T2D | **Conditional prevalence ($P(\text{HTN}\mid\text{T2D})$)** | **Evaluation Target (Comorbidity).** Valid conditional benchmark for adults with diabetes. |
| **Gender-Stratified Diabetes Targets** | M: **12.1%**<br>F: **10.7%** | Anjana et al., *Lancet Diabetes Endocrinol* 2023;11(7):474-489 | Subgroup stratification | 2008–2020 | National, India | Adults $\ge 20$ by sex | **Stratified prevalence** | **Internal Subgroup Validation.** Derived from the same study; demonstrates subgroup consistency, but NOT external independent validation. |
| **State-Level Regional Benchmarks** | TN: **14.4%**<br>MH: **10.8%** | Anjana et al., *Lancet Diabetes Endocrinol* 2023;11(7):474-489 | Sub-regional cluster estimates | 2008–2020 | State-specific, India | Adults $\ge 20$ in specified state | **Sub-regional prevalence** | **Internal Subgroup Validation.** Same multi-stage survey; cannot be claimed as an independent external data source. |
| **Acute URTI Point Prevalence** | **8.5%** | National Health Portal (NHP) India / Integrated Disease Surveillance Programme (IDSP) | Government Health Surveillance | 2018–2020 | National, India | All ages, outpatient presentations | **14-day recall / point prevalence** | **Evaluation Target (Point Prevalence).** Only comparable against active infections in a 14-day window. |
| **Acute URTI Annual Episode Frequency** | **0.45 / yr** | NHP India / IDSP Acute Respiratory Infections Baseline | Epidemiological surveillance | 2020 | National, India | All ages | **Annual episode frequency** | **Longitudinal Rate Target.** Yields 2-year cumulative attack rate of 60%–75%. |
| **Annual Crude Mortality** | **0.0060** | SRS Abridged Life Tables 2016–2020, Census of India | National Sample Registration System | 2016–2020 | National, India | All resident individuals | **Annual mortality rate ($q_x$)** | **Evaluation Target (Mortality).** Empirical life table. |

---

## 2. Classification of All Evaluation Acceptance Thresholds

Every metric evaluated in SYNAPSE Phase 2 is formally categorized into one of five threshold classifications:

```
+----------------------------------------------------------------------------------------------------+
|                                    THRESHOLD CLASSIFICATION MATRIX                                 |
+----------------------------------------------------------------------------------------------------+
| 1. Hard Structural / Safety Invariant   | 0 violations permitted; confirmed violation BLOCKS       |
| 2. Statistically Motivated Criterion     | Grounded in distribution theory (JSD, Wilson, Chi2)     |
| 3. Practical Tolerance                  | Predefined empirical margin chosen for finite cohort size|
| 4. Provisional Engineering Threshold    | Bounds on uncalibrated/plausible clinical operational ranges|
| 5. Explicitly Disclosed Assumption      | Model-based assumption tagged UNVERIFIED                 |
+----------------------------------------------------------------------------------------------------+
```

### Complete Classification Scorecard

| Metric ID | Metric Name | Threshold Value | Classification | Justification & Methodological Grounding |
| :--- | :--- | :---: | :--- | :--- |
| `inv_no_event_pre_birth` | Zero Pre-Birth Events | `violations = 0` | **Hard Invariant** | Causal invariant: clinical encounters cannot occur before patient birth. |
| `inv_no_event_post_mortem` | Zero Post-Mortem Events | `violations = 0` | **Hard Invariant** | Causal invariant: deceased individuals cannot generate new medical activity. |
| `inv_diagnosis_encounter_linkage` | Encounter Linkage | `violations = 0` | **Hard Invariant** | Referential integrity: diagnoses require an active clinical recognition encounter. |
| `inv_allergy_safety_veto` | Zero Allergy Violations | `violations = 0` | **Hard Invariant** | Clinical safety: patients with documented allergies must never receive contraindicated drugs. |
| `demo_sex_distribution` | Male Sex Proportion | $|\text{Diff}| \le 5.0\%$ | **Statistically Motivated** | SRS 2021 sex ratio (51.5% male) with 95% Wilson score confidence coverage. |
| `demo_age_pyramid_jsd` | Age Pyramid JSD | $JSD < 0.05$ | **Statistically Motivated** | Standard information-theoretic threshold for equivalent probability distributions. |
| `demo_age_by_sex_jsd` | Age-Sex Joint JSD | $JSD < 0.08$ | **Statistically Motivated** | Accounts for 10-cell multi-dimensional cross-tabulation in finite cohorts. |
| `prev_hypertension_adults` | Adult HTN Prevalence | $|\text{Diff}| \le 8.0\%$ | **Practical Tolerance** | Accounts for finite-sample binomial sampling variance at $N=100$ ($SE \approx 4.6\%$). |
| `prev_diabetes_t2_adults` | Adult T2D Prevalence | $|\text{Diff}| \le 6.0\%$ | **Practical Tolerance** | Accounts for finite-sample binomial sampling variance at $N=100$ ($SE \approx 3.2\%$). |
| `comorb_htn_in_t2d` | P(HTN \| T2D) in Adults | $|\text{Diff}| \le 15.0\%$ | **Practical Tolerance** | Diabetic sub-cohort size is small ($N \approx 10–25$ in a 100-person cohort), yielding wider CIs. |
| `prev_urti_14day_point` | URTI 14-Day Point Prevalence | $|\text{Diff}| \le 5.0\%$ | **Practical Tolerance** | Measures active infections within a 14-day window matching NHP survey recall methodology. |
| `prev_urti_cumulative_attack_rate` | URTI 2-Year Attack Rate | Range $[60\%, 80\%]$ | **Provisional Engineering** | Derived from community annual attack rate (~0.45/yr): $1 - (1 - p_{\text{cycle}})^k \approx 70\%$. |
| `long_encounters_per_pt_year` | Encounters / Pt-Year | Range $[0.2, 5.0]$ | **Provisional Engineering** | Reflects general outpatient OPD presentation range from NSSO 75th round health survey. |
| `long_inter_encounter_interval` | Revisit Interval | Range $[30, 365]$ d | **Provisional Engineering** | Operational range around ICMR standard 90–180 day chronic review guidelines. |
| `long_crude_mortality_rate` | Annual Mortality Rate | $|\text{Diff}| \le 0.02$ | **Practical Tolerance** | Empirical life table rate (0.0060/yr) with tolerance for small-cohort stochastic deaths. |
| `rx_firstline_hypertension` | First-Line CCB/ARB | Conformance $\ge 80\%$ | **Provisional Engineering** | Guideline recommendation: 100% of uncomplicated stage 1/2 HTN indicated for CCB/ARB. |
| `rx_firstline_diabetes` | First-Line Metformin | Conformance $\ge 80\%$ | **Provisional Engineering** | Guideline recommendation: Metformin universal initial monotherapy. |
| `rx_adherence_assumption` | 100% Adherence Disclosure | Documented | **Disclosed Assumption** | Mandated disclosure flag. Explicitly marked `UNVERIFIED` (never granted `PASS`). |

---

## 3. The Three Authoritative Acceptance Layers

SYNAPSE Phase 2 implements three explicit, uncoupled evaluation layers:

### Layer 1: Structural and Causal Correctness
- **Scope:** Foreign-key integrity, non-null requirements, unique primary keys, valid temporal sequence, zero post-mortem events, zero contraindicated prescriptions.
- **Publication Policy:** **Authoritative Blocker.** Any single failure blocks dataset publication and flags a fatal software or simulation bug.

### Layer 2: Statistical Fidelity
- **Scope:** Marginal demographic distributions (Age, Sex, Age $\times$ Sex), disease prevalence (Hypertension, Diabetes, URTI point prevalence), comorbidity clustering ($P(\text{HTN}\mid\text{T2D})$).
- **Publication Policy:** Evaluated against statistical and practical tolerances. Metrics falling in warning bands generate research diagnostics; severe deviations ($> 2\times$ tolerance) trigger statistical review.

### Layer 3: Clinical and Longitudinal Plausibility
- **Scope:** Inter-encounter follow-up intervals, encounters per patient-year, treatment sequences, multi-year cumulative attack rates, mortality rates.
- **Publication Policy:** Informative research assessment. Distinguishes verified guideline standards from provisional engineering bounds. Never conceals Layer 1 or Layer 2 failures.
