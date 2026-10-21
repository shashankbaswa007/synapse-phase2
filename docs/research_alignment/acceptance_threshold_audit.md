# Comprehensive Acceptance-Threshold Audit and Five-Tier Governance Policy

**Evaluation Framework:** SYNAPSE Phase 2 Independent Evaluator  
**Audit Purpose:** Reassess every quantitative acceptance threshold to eliminate arbitrary scorecard "curve-fitting".  
**Classification Mandate:** Every threshold must be explicitly categorized into one of five rigorous tiers.  

---

## 1. Five-Tier Acceptance Threshold Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: HARD INVARIANTS                                                     │
│ Causal, temporal, referential, and safety invariants.                       │
│ Tolerance: Strictly 0 allowed violations.                                   │
│ Failure Mode: HARD PUBLICATION GATE BLOCK (FAIL).                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: EVIDENCE-BASED CRITERIA                                             │
│ Derived from formal statistical hypothesis testing or published survey CIs. │
│ Tolerance: Wilson 95% Confidence Intervals / SRS Life Tables / Chi-Square.  │
│ Failure Mode: Statistical Rejection (WARNING or FAIL based on sample size). │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: RESEARCH-TEAM PRACTICAL TOLERANCES                                  │
│ Heuristic tolerances selected to accommodate sample size constraints.       │
│ Tolerance: Pre-configured percentage margins (e.g., ±5.0% on baseline prev).│
│ Failure Mode: Documented Review (PASS / WARNING).                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 4: PROVISIONAL ENGINEERING THRESHOLDS                                  │
│ Operational benchmarks established during initial platform development.     │
│ Tolerance: Broad plausibility bounds (e.g., 0.2 to 5.0 encounters/pt-year). │
│ Failure Mode: Engineering Inspection (WARNING).                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 5: UNVERIFIED MODEL ASSUMPTIONS                                        │
│ Non-empirical modeling choices (e.g. 100% adherence, static transitions).   │
│ Tolerance: Disclosure and Sensitivity Mandate.                              │
│ Failure Mode: Permanent UNVERIFIED tag. NEVER labeled as empirical PASS.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete Metric-by-Metric Classification Audit

### 2.1 Invariant Metrics (Layer 1)

| Metric ID | Metric Name | Acceptance Threshold | Classification Tier | Scientific Rationale & Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| `inv_no_event_pre_birth` | Zero Clinical Events Prior to Birth | Violations $= 0$ | **Tier 1: Hard Invariant** | Strict causal and chronological prerequisite: no human can attend an encounter or receive a prescription prior to their birth date. Hard publication blocker. |
| `inv_no_event_post_mortem` | Zero Post-Mortem Clinical Events | Violations $= 0$ | **Tier 1: Hard Invariant** | Strict biological invariant: deceased patients must not generate vital signs, laboratory orders, or prescriptions. Hard publication blocker. |
| `inv_diagnosis_encounter_linkage`| Encounter Diagnosis Linkage | Violations $= 0$ | **Tier 1: Hard Invariant** | Relational and causal requirement: medical diagnoses only occur during formal clinical encounters. No dangling foreign keys allowed. |
| `inv_allergy_safety_veto` | Zero Contraindicated Prescriptions | Violations $= 0$ | **Tier 1: Hard Invariant** | Clinical safety mandate: RuleEngine must execute allergy safety vetoes (e.g. blocking Amoxicillin in Penicillin allergy). Zero tolerance for medical harm. |

---

### 2.2 Demographic Fidelity Metrics (Layer 2)

| Metric ID | Metric Name | Acceptance Threshold | Classification Tier | Scientific Rationale & Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| `demo_sex_distribution` | Male Sex Proportion | Pass: $\le 5.0\%$, Warn: $\le 10.0\%$ | **Tier 2: Evidence-Based Criterion** | Derived from Census of India SRS 2021 sex ratio (51.5% male, 95% CI: `[51.2%, 51.8%]`). Tolerance accounts for expected binomial sampling variance in cohorts of $N \ge 100$. |
| `demo_age_pyramid_jsd` | Age Pyramid Jensen-Shannon Divergence | Pass: $< 0.05$, Warn: $< 0.15$ | **Tier 2: Evidence-Based Criterion** | Evaluates similarity between synthetic age bands and SRS 2021 5-band national age distribution. JSD $< 0.05$ represents statistical indistinguishability. |
| `demo_age_by_sex_jsd` | Age-by-Sex Joint Distribution JSD | Pass: $< 0.08$, Warn: $< 0.20$ | **Tier 3: Practical Tolerance** | Compares 10-cell joint age-gender matrix against SRS 2021 Statement 19. Threshold widened to 0.08 to prevent false rejection from small-sample cell sparsity. |

---

### 2.3 Disease Prevalence and Incidence Metrics (Layer 2)

| Metric ID | Metric Name | Acceptance Threshold | Classification Tier | Scientific Rationale & Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| `prev_hypertension_adults` | Essential Hypertension Prevalence | Pass: $\le 8.0\%$, Warn: $\le 15.0\%$ | **Tier 3: Practical Tolerance** | Configured tolerance accommodates both random sampling variance ($\sigma \approx 3.8\%$ at $N=100$) and expected 2-year incident accumulation ($+4.7\%$). Baseline point prevalence is isolated in threshold telemetry. |
| `prev_diabetes_t2_adults` | Type 2 Diabetes Prevalence | Pass: $\le 6.0\%$, Warn: $\le 12.0\%$ | **Tier 2: Evidence-Based Criterion** | Calibrated to ICMR-INDIAB 2023 adult prevalence (11.4%, 95% CI: `[10.2%, 12.5%]`). 6.0% bound corresponds to 2 standard deviations in a 100-patient sample. |
| `prev_urti_14day_point` | Acute URTI 14-Day Point Prevalence | Pass: $\le 6.0\%$, Warn: $\le 10.0\%$ | **Tier 4: Provisional Engineering Threshold** | Provisional benchmark reflecting NHP India 2020 symptom survey. Acknowledged limitation: non-recurrent pathway architecture depresses 24-month point prevalence to ~4.8%. |
| `prev_urti_cumulative_attack_rate`| URTI 2-Year Cumulative Attack Rate | Pass: $\le 12.0\%$, Warn: $\le 20.0\%$ | **Tier 2: Evidence-Based Criterion** | Grounded in community surveillance benchmarks from IDSP/NCDC (~0.45 episodes/pt-year yielding ~70% 2-year cumulative attack rate). |

---

### 2.4 Comorbidity Patterns (Layer 2)

| Metric ID | Metric Name | Acceptance Threshold | Classification Tier | Scientific Rationale & Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| `comorb_htn_in_t2d` | Hypertension Prevalence in Diabetics | Pass: $\le 15.0\%$, Warn: $\le 25.0\%$ | **Tier 2: Evidence-Based Criterion** | Derived from published ICMR-INDIAB 2023 Table 3 ($50.1\%$, 95% CI: `[47.5%, 52.7%]`). Tolerance is wider for small cohorts because diabetic subsample size is small ($N_{\text{t2d}} \approx 11$ at $N=100$). |

---

### 2.5 Longitudinal Dynamics and Outcomes (Layer 3)

| Metric ID | Metric Name | Acceptance Threshold | Classification Tier | Scientific Rationale & Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| `long_encounters_per_pt_year` | Encounters Per Patient-Year | Plausible Range: $0.2 - 5.0$ | **Tier 4: Provisional Engineering Threshold** | Broad operational bounds reflecting outpatient utilization in public/private Indian facilities. Marked as UNVERIFIED due to facility vs community survey differences. |
| `long_inter_encounter_interval_days`| Mean Days Between Encounters | Range: $30 - 365\text{ days}$ | **Tier 4: Provisional Engineering Threshold** | Operational plausibility for routine chronic disease follow-up (ICMR guidelines recommend 90–180 days). Marked as UNVERIFIED. |
| `long_crude_mortality_rate` | Annualized Crude Mortality Rate | Tolerance: $\pm 0.02$ (/pt-year) | **Tier 2: Evidence-Based Criterion** | Calibrated to Census of India SRS Abridged Life Tables 2016–2020 (crude death rate: ~6.0 per 1,000 person-years). |

---

### 2.6 Treatment Conformance and Adherence (Layer 3)

| Metric ID | Metric Name | Acceptance Threshold | Classification Tier | Scientific Rationale & Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| `rx_firstline_hypertension` | First-Line Antihypertensive Conformance | Min Conformance: $80.0\%$ | **Tier 3: Practical Tolerance** | Measures algorithmic state machine rule compliance to ICMR 2022 guidelines (Amlodipine). Relabeled as Rule Conformance, not real-world fidelity. |
| `rx_firstline_diabetes` | First-Line Antidiabetic Conformance | Min Conformance: $80.0\%$ | **Tier 3: Practical Tolerance** | Measures algorithmic state machine rule compliance to ICMR 2022 guidelines (Metformin). Relabeled as Rule Conformance, not real-world fidelity. |
| `rx_adherence_assumption` | Perfect Adherence Disclosure | Full Disclosure: $100.0\%$ | **Tier 5: Unverified Assumption** | Unverified model assumption. Permanently tagged with status UNVERIFIED. Never declared as an empirical PASS. |

---

## 3. Governance Summary: Separation of Publication Gates from Clinical Scores

1. **Hard Blocking Behavior:**  
   If ANY Tier 1 Invariant fails (`inv_no_event_pre_birth`, `inv_no_event_post_mortem`, `inv_diagnosis_encounter_linkage`, `inv_allergy_safety_veto`), `overall_status` is locked to **`FAIL`**, and the dataset is strictly blocked from publication or downstream consumption.
2. **Statistical Warnings vs. Operational Tolerances:**  
   Tier 2 and Tier 3 metric deviations outside tolerance trigger **`WARNING`**, initiating an epidemiological investigation without falsely invalidating the physical and relational integrity of the dataset.
3. **No False PASS for Modeling Assumptions:**  
   Tier 5 assumptions (such as 100% adherence and static transition rates) are explicitly reported under the **`UNVERIFIED`** status, ensuring transparency for peer review and clinical credibility audits.
