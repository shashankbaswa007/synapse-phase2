# Limitations, Unverified Assumptions, and Scientific Governance Report

**Audit Purpose:** Establish rigorous boundaries on the scientific validity and credibility of SYNAPSE Phase 2 synthetic healthcare data.  
**Core Governance Mandate:** Distinguish verified empirical findings from unverified engineering assumptions. Prohibit unsubstantiated claims of clinical realism.  

---

## 1. Executive Summary: What This Platform Does and Does Not Claim

The SYNAPSE Phase 2 platform generates discrete-event longitudinal synthetic healthcare electronic records. Following this model credibility audit:

- **WHAT IS SCIENTIFICALLY VERIFIED:**
  1. The platform generates causal, temporal, and relational data with **100% invariant integrity** (zero pre-birth events, zero post-mortem encounters, zero dangling foreign keys, zero contraindicated prescriptions).
  2. The demographic marginal and joint distributions conform to the **Census of India SRS 2021** ($\text{JSD} < 0.01$).
  3. Baseline chronic disease prevalence and comorbidity clustering conform to **ICMR-INDIAB 2023** ($P(\text{HTN}) = 30.70\%$, $P(\text{T2D}) = 11.40\%$, $P(\text{HTN}\mid\text{T2D}) = 50.10\%$, $\text{OR} = 2.52$).
  4. Prospective incident transitions conform to documented Indian cohort studies (CARRS for diabetes, CURES for hypertension).
  5. Actuarial mortality plausibly reflects the **Census SRS 2016–2020 Life Tables** ($\sim 15$ deaths per 500 patients over 24 months).

- **WHAT IS AN UNVERIFIED ASSUMPTION (DO NOT CLAIM AS REALISTIC):**
  1. **100% Medication Adherence:** Simulated patients have perfect compliance; real-world adherence is $40\%–60\%$.
  2. **Deterministic Monotherapy Prescription:** 100% of diagnosed patients receive a single guideline drug; real-world practice includes combination therapies, clinical inertia, and financial dropouts ($45\%–65\%$).
  3. **Non-Recurrent Acute Illness:** The URTI pathway terminates after one episode, depleting the susceptible pool over multi-year horizons.
  4. **Closed Healthcare Setting:** The simulation assumes all medical events occur within a single integrated hospital system, ignoring provider switching and private unrecorded care.

---

## 2. Comprehensive Inventory of Modeling Dimensions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. EMPIRICALLY VERIFIED (EXTERNAL DATA SOURCES)                             │
│    • Male sex proportion (Census SRS 2021)                                  │
│    • 5-band age pyramid distribution (Census SRS 2021)                      │
│    • 10-strata age-by-sex joint distribution (SRS 2021 Statement 19)        │
│    • Adult hypertension baseline point prevalence (ICMR-INDIAB 2023)        │
│    • Adult Type 2 diabetes baseline point prevalence (ICMR-INDIAB 2023)      │
│    • Metabolic comorbidity coupling P(HTN|T2D) (ICMR-INDIAB 2023)           │
│    • Annual hypertension prospective hazard (CURES Cohort / JAHA 2017)      │
│    • Annual diabetes prospective hazard (CARRS Cohort / BMJ Open 2021)      │
│    • All-cause life-table age-stratified qx (Census SRS 2016-2020)          │
│    • URTI 2-year cumulative attack rate (IDSP Community Surveillance)       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. ALGORITHMIC RULE CONFORMANCE (STATE MACHINE EXECUTION)                   │
│    • Zero clinical activity before birth date                               │
│    • Zero clinical encounters, orders, or prescriptions after death         │
│    • 100% diagnosis linkage to valid active encounters                      │
│    • 100% allergy contraindication veto enforcement                         │
│    • 100% first-line guideline rule execution (Amlodipine / Metformin)      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. UNVERIFIED ENGINEERING ASSUMPTIONS (FLAGGED IN METADATA)                 │
│    • 100% medication adherence (rx_adherence_assumption)                    │
│    • Non-recurrent acute infection pathway (J06.9 terminal state)           │
│    • Facility consultation rate (0.91 encounters/pt-yr vs community NSSO)   │
│    • Inter-encounter follow-up intervals (fixed 90d/180d delays)            │
│    • Absence of renal contraindications or adverse drug reactions           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Limitations by Clinical Domain

### 3.1 Chronic Disease Prevalence & Period Accumulation
- **Limitation:** In a 2-year longitudinal cohort with irreversible chronic conditions, diagnosed prevalence naturally accumulates from $30.70\%$ to $35.90\%$.
- **Guidance for Downstream Researchers:** Researchers training machine learning models on synthetic cohorts must distinguish between **cross-sectional baseline point prevalence** (present at admission/intake) and **longitudinal cumulative period prevalence** (accumulated across the health system timeline).

### 3.2 Acute Illness and Infection Recurrence
- **Limitation:** The URTI module treats acute viral infection as non-recurrent.
- **Guidance for Downstream Researchers:** Synthetic URTI data accurately reflects **multi-year cumulative attack rates** ($74.20\%$), but should not be used to study seasonal reinfection cycles or intra-year transmission dynamics until a recurrent pathway is introduced.

### 3.3 Pharmacotherapy and Health Outcomes
- **Limitation:** The assumption of 100% adherence creates an artificially healthy cohort with suppressed secondary complication rates (stroke, ESRD, diabetic retinopathy).
- **Guidance for Downstream Researchers:** Do not use this data to benchmark real-world health economic burden or cost-effectiveness of adherence-support interventions without introducing an explicit adherence drop-off model.

---

## 4. Scientific Governance & Peer-Review Publication Guardrails

1. **Mandatory Disclaimer in Published Research:**  
   Any academic paper or whitepaper utilizing datasets generated by SYNAPSE Phase 2 must include the following formal disclosure:
   > *"Synthetic patient records were generated using SYNAPSE Phase 2, calibrated to Census SRS 2021 and ICMR-INDIAB 2023 epidemiological benchmarks. Pharmacotherapy represents guideline rule conformance under a 100% adherence assumption. Comorbidity and longitudinal progression reflect modeled hazard transitions and should not be interpreted as empirical clinical practice observations."*
2. **Prohibited Marketing & Research Claims:**  
   - DO NOT claim that synthetic prescribing distributions validate real-world physician behavior in India.
   - DO NOT claim that 0 contraindication violations proves real-world clinical safety; it only proves that the synthetic generator obeys hardcoded safety rules.
   - DO NOT claim that multi-seed Monte Carlo replication constitutes independent real-world cohort validation.
