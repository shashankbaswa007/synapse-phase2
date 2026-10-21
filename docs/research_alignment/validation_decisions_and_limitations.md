# Validation Decisions, Statistical Governance, and Model Limitations

**Document ID:** `SYNAPSE-AUDIT-DELIV-06`  
**Date:** October 2026  
**Auditor:** SYNAPSE Longitudinal Credibility & Statistical Validation Team  
**Focus Area:** Formal Metric Validation Decisions, Justified Tolerances, Separation of Calibration and Evaluation, and Governance Boundaries  

---

## 1. Executive Summary

This document establishes the definitive validation decisions for all 20 metrics evaluated in SYNAPSE Phase 2. 

### Core Audit Principles
1. **No Cosmetic Passing:** A metric is not classified as `PASS` merely because its synthetic estimate happens to land near a reference number. Each `PASS` status requires a formally verified reference data source, matched denominators, identical observation windows, and empirical plausibility.
2. **Explicit Uncertainty:** Wilson score intervals, Poisson-Binomial predictive distributions, and Monte Carlo standard errors are reported for all metrics.
3. **Equivalence vs. Non-Significance:** A non-significant $p$-value ($p > 0.05$) is never claimed as proof of identity. Where equivalence is established, it is bounded by a documented equivalence margin ($\Delta_{\text{equiv}}$).
4. **Separation of Calibration and Evaluation:** Internal subgroup comparisons derived from calibration samples are not claimed as external validation.

---

## 2. Definitive Validation Decision Matrix

| Dimension | Metric Identifier | Synthetic Estimate (5-Seed Mean, N=500) | Reference Value | Equivalence / Tolerance Margin | Statistical Uncertainty (95% CI / PI) | Validation Decision | Methodological Justification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Invariants** | `inv_no_event_pre_birth` | $0.0$ violations | $0$ violations | Zero tolerance | $[0, 0]$ | 🛡️ **`SOFTWARE_INVARIANT_PASS`** | Hard temporal gate. Zero violations across 15 runs. |
| **Invariants** | `inv_no_event_post_mortem` | $0.0$ violations | $0$ violations | Zero tolerance | $[0, 0]$ | 🛡️ **`SOFTWARE_INVARIANT_PASS`** | Hard temporal gate. Deceased patients strictly skipped. |
| **Invariants** | `inv_diagnosis_encounter_linkage` | $0.0$ violations | $0$ violations | Zero tolerance | $[0, 0]$ | 🛡️ **`SOFTWARE_INVARIANT_PASS`** | Hard causal gate. Foreign key referential integrity intact. |
| **Invariants** | `inv_allergy_safety_veto` | $0.0$ violations | $0$ violations | Zero tolerance | $[0, 0]$ | 🛡️ **`SOFTWARE_INVARIANT_PASS`** | Safety hold blocks contraindicated prescriptions. |
| **Invariants** | `inv_person_time_upper_bound` | $0.0$ violations | $0$ violations | Zero tolerance | $[0, 0]$ | 🛡️ **`SOFTWARE_INVARIANT_PASS`** | Hard temporal bound. Person-time strictly $\le 985.63\text{ pt-yrs}$ across all runs. |
| **Demographics** | `demo_sex_distribution` | $51.78\%$ Male | $51.50\%$ | $\pm 5.0\%$ | Wilson: $[47.4\%, 56.1\%]$ | ✅ **`PASS`** | Census SRS 2021 sex ratio faithfully replicated. |
| **Demographics** | `demo_age_pyramid_jsd` | $0.0035$ | $0.0000$ | $\text{JSD} \le 0.05$ | $\chi^2 = 8.12, p = 0.087$ | ✅ **`PASS`** | SRS 5-band age pyramid divergence is negligible. |
| **Demographics** | `demo_age_by_sex_jsd` | $0.0052$ | $0.0000$ | $\text{JSD} \le 0.08$ | $\text{TVD} = 0.056$ | ✅ **`PASS`** | 10-strata joint distribution closely aligns with Census. |
| **Prevalence** | `prev_hypertension_adults` (Period) | $36.16\%$ | $30.70\%$ | $\pm 8.0\%$ | Wilson: $[30.8\%, 41.4\%]$ | ✅ **`PASS`** | Period prevalence includes $3.6\%$ incident cases. Baseline point is $32.53\%$. |
| **Prevalence** | `prev_diabetes_t2_adults` (Period) | $12.92\%$ | $11.40\%$ | $\pm 6.0\%$ | Wilson: $[9.5\%, 16.9\%]$ | ✅ **`PASS`** | Closely matches ICMR-INDIAB 2023 adult prevalence. |
| **Prevalence** | `prev_urti_14day_point` | $8.20\%$ | $8.50\%$ | $\pm 6.0\%$ | Wilson: $[6.1\%, 10.9\%]$ | ✅ **`PASS`** | 14-day recall point prevalence matches NHP India 2020. |
| **Prevalence** | `prev_urti_cumulative_attack_rate`| $71.40\%$ | $70.00\%$ | $\pm 12.0\%$ | Wilson: $[67.3\%, 75.2\%]$ | ✅ **`PASS`** | 2-year cumulative attack rate matches surveillance data. |
| **Comorbidity** | `comorb_htn_in_t2d` | $48.60\%$ | $50.10\%$ | $\pm 15.0\%$ | Wilson: $[35.2\%, 62.2\%]$ | ✅ **`PASS`** | Conditional prevalence $P(\text{HTN}\mid\text{T2D})$ matches INDIAB. |
| **Longitudinal** | `long_encounters_per_pt_year` | $1.11\text{ yr}^{-1}$ | $1.80\text{ yr}^{-1}$ | $[0.2, 5.0]$ | $\text{SE} = 0.04$ | 🔶 **`UNVERIFIED`** | Facility scheduling differs from community NSS survey. |
| **Longitudinal** | `long_inter_encounter_interval` | $123.4\text{ days}$ | $180.0\text{ days}$ | $[30, 365\text{d}]$ | $\text{SD} = 6.6\text{d}$ | 🔶 **`UNVERIFIED`** | Captures module delays (90d, 180d) rather than patient adherence. |
| **Longitudinal** | `long_crude_mortality_rate` | $0.0144\text{ yr}^{-1}$ | $0.0060\text{ yr}^{-1}$ | $[0.005, 0.025]$ | $95\% \text{ PI}: [5.7, 17.7]\text{ deaths}$ | ⚠️ **`WARNING`** | Reconstructed cohort expectation matches actuarial table ($E[D]=11.68$). Elderly skew caveat. |
| **Longitudinal** | `long_treatment_intensification` | $78.97\%$ | None (`None`) | Descript. | $\text{SD} = 3.41\%$ | 🔶 **`UNVERIFIED`** | Reflects algorithmic guideline rules; real-world cross-sectional 35% target is `NOT_COMPARABLE`. |
| **Longitudinal** | `long_chronic_complication_rate`| $2.88\%$ | $4.00\%$ | Descript. | $\text{SD} = 1.44\%$ | 🔶 **`UNVERIFIED`** | Discrete Markov transition weights in closed facility are an architectural modeling choice. |
| **Treatment** | `rx_firstline_hypertension` | $99.30\%$ | $100.00\%$ | $\pm 5.0\%$ | Wilson: $[97.2\%, 99.8\%]$ | ✅ **`PASS`** | Guideline algorithmic conformance for Amlodipine initiation. |
| **Treatment** | `rx_firstline_diabetes` | $100.00\%$ | $100.00\%$ | Zero tolerance | $[100.0\%, 100.0\%]$ | ✅ **`PASS`** | Guideline algorithmic conformance for Metformin initiation. |
| **Treatment** | `rx_urti_antibiotic_avoidance` | $100.00\%$ | $100.00\%$ | Zero tolerance | $[100.0\%, 100.0\%]$ | ✅ **`PASS`** | Guideline stewardship compliance for viral respiratory care. |
| **Treatment** | `rx_adherence_assumption` | $100.00\%$ | None | Assumption | Constant | 🔶 **`UNVERIFIED`** | Simulation assumes perfect adherence. Documented assumption. |

---

## 3. Methodological Boundaries and Model Limitations

The following boundaries must be maintained in research publications and regulatory filings:

1. **Guideline Conformance vs. Real-World Prescribing Fidelity:**
   - The simulation executes clinical guideline state machines (e.g. 100% first-line Metformin initiation, 100% treatment escalation on uncontrolled readings).
   - In real-world Indian outpatient clinics, initial monotherapy alignment is $\sim 50\%\text{--}65\%$, and clinician therapeutic inertia results in visit-level intensification rates of only $\sim 30\%\text{--}40\%$.
   - **Mandatory Caveat:** Passing `rx_firstline_*` tests proves software rule execution fidelity; it must **never** be cited as evidence of real-world physician prescribing patterns.
2. **Medication Adherence Assumption:**
   - Synthetic patients exhibit $100\%$ medication persistence and adherence unless a specific non-adherence sub-model is configured. Real-world NCD medication adherence in India is approximately $40\%\text{--}60\%$.
   - Results represent an "idealized guideline-adherent clinical trial" cohort.
3. **Elderly Age Distribution Assumption:**
   - As documented in `population_sampling_and_denominators.md`, uniform sampling within age 65–100 creates an over-representation of patients aged 85+.
   - This elevates synthetic crude mortality ($15\text{ per } 1,000$ pt-yrs) relative to the national Census CDR ($6.0\text{ per } 1,000$), but is 100% consistent with the actuarial expectation of the simulated age structure.
4. **Facility Scheduling vs. Community Consultations:**
   - Synthetic visit frequency ($1.08\text{ visits/pt-yr}$) represents primary health centre (PHC) chronic surveillance and episodic care. It does not model private sector shopping, traditional AYUSH consultations, or self-medication.
