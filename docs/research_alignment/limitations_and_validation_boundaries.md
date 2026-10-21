# Limitations Report: Validated Findings vs. Unverified Simulation Assumptions

**Document ID:** `SYNAPSE-AUDIT-DELIV-08`  
**Date:** October 2026  
**Auditor:** SYNAPSE Model Credibility & Clinical Trajectory Audit Team  
**Focus Area:** Scientific Demarcation, Validation Boundaries, and Research Governance  

---

## 1. Governance Principles for Model Credibility

The ultimate objective of SYNAPSE Phase 2 is to produce synthetic healthcare data whose clinical utility and credibility are grounded in transparent, reproducible scientific evidence. 

Passing unit tests, satisfying automated acceptance gates, and generating plausible aggregate statistics **do not** prove that the synthetic data perfectly mirrors real-world clinical behavior.

To prevent over-claiming, this document explicitly delineates what has been **empirically validated** from what remains an **unverified simulation assumption**.

---

## 2. Rigorous Demarcation Matrix

| Clinical / Statistical Dimension | What is Empirically Validated | What Remains an Unverified Simulation Assumption | Risk of Misuse / Research Boundaries |
| :--- | :--- | :--- | :--- |
| **Demographic Pyramid** | Census SRS 2021 national age-sex distribution weights; JSD divergence $< 0.08$. | Uniform integer age sampling within the wide 65–100 age band over-represents individuals aged 85+. | Do not use for actuarial studies of extreme longevity (centenarians). |
| **Baseline Disease Prevalence** | ICMR-INDIAB 2023 baseline marginal targets ($30.7\%$ HTN, $11.4\%$ T2D); conditional comorbidity mathematically exact. | Latent asymptomatic duration is modeled as a uniform 90–180 day delay before opportunistic detection. | Do not interpret latent onset dates as clinically recorded electronic health record timestamps. |
| **Longitudinal Disease Incidence** | Annual incidence hazards ($\lambda_{\text{HTN}}=0.0344$, $\lambda_{\text{T2D}}=0.0149$) derived from prospective Indian cohorts (CURES, CARRS). | Incidence hazard is modeled as constant over time without individual lifestyle/BMI covariates. | Does not simulate individual behavioral intervention effects (e.g. smoking cessation, weight loss). |
| **Pharmacotherapy & Prescribing** | Algorithmic guideline rule conformance: first-line drugs (Amlodipine, Metformin) and stepped-up dual therapy (Telmisartan, Glimepiride) match ICMR/IHCI guidelines. | Prescribing is deterministic (100% adherence to guideline rules); physician hesitation, therapeutic inertia, and stockouts are omitted. | **Do NOT claim that synthetic prescribing represents real-world physician behavior.** In real-world clinics, first-line adherence is 45–65%. |
| **Patient Treatment Adherence** | Software execution: prescriptions are dispensed at scheduled encounter boundaries without error. | Full-adherence assumption: patients never miss doses, abandon therapy, or face financial barriers. | Do not use this baseline to evaluate drug effectiveness or real-world compliance outcomes. |
| **All-Cause Mortality** | Actuarial life-table stepping reproduces SRS 2016–2020 age-specific mortality; right-censored person-time correctly evaluated; zero post-mortem events. | Mortality rates within 65–100 are elevated due to uniform age sampling; cardiovascular excess deaths are additive to all-cause tables. | Calibrated to national life tables, but small cohorts exhibit expected Poisson sampling variance. |
| **Upper Respiratory Infections (URTI)** | Acute episodic presentation with 10-day symptom duration and 2-year cumulative attack rate ($74.2\%$). | The module models a non-recurrent terminal pathway; does not model multiple recurrent seasonal infections per year. | Do not compare 14-day point prevalence against community symptom recall surveys without noting the non-recurrent model structure. |
| **Chronic Complications** | Longitudinal emergence of target-organ damage (`I12.9` CKD, `E11.2` Nephropathy) at ~6% over 2 years matches epidemiological cohorts. | Complication transitions use discrete annual probabilities without continuous laboratory eGFR/albuminuria staging. | Suitable for cohort comorbidity simulation, but not for detailed chronic kidney disease staging. |

---

## 3. Methodological Conclusions and Recommendations

1. **Permissible Research Claims:**
   - SYNAPSE Phase 2 accurately reproduces Indian demographic age-sex proportions and baseline chronic disease prevalences.
   - The platform strictly enforces temporal and causal invariants (no pre-birth or post-mortem actions, zero contraindicated prescriptions).
   - Generated patient trajectories exhibit realistic multi-encounter longitudinal timelines with guideline-concordant treatment step-up and target-organ complications.
2. **Prohibited Research Claims:**
   - Do **not** claim that synthetic datasets validate real-world physician prescribing patterns or therapeutic inertia.
   - Do **not** claim that synthetic patient compliance mirrors real-world patient adherence.
   - Do **not** cite 100% rule conformance as proof of clinical prescribing fidelity.
