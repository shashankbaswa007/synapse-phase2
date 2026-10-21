# Evidence and Assumptions Catalog: Longitudinal Clinical Transitions

**Document ID:** `SYNAPSE-AUDIT-DELIV-03`  
**Date:** October 2026  
**Auditor:** SYNAPSE Model Credibility & Clinical Trajectory Audit Team  
**Focus Area:** 5-Tier Provenance Classification of Longitudinal Transition Parameters  

---

## 1. Classification Hierarchy (5-Tier Parameter Provenance)

To ensure scientific integrity and eliminate ungrounded clinical claims, every transition probability, delay, observation range, and therapy rule in the SYNAPSE Phase 2 longitudinal clinical modules is categorized into one of five rigorous evidence tiers:

1. **Tier 1: Prospective Epidemiological Evidence (PEE):** Empirically estimated from prospective longitudinal cohort studies with well-characterized incident event rates and observation windows.
2. **Tier 2: Clinical Guideline (CG):** Mandated by national or international clinical practice guidelines (ICMR, IHCI, RSSDI, WHO) as recommended standard of care.
3. **Tier 3: Estimated from Longitudinal Datasets (ELD):** Statistically estimated from longitudinal electronic health records, public registries, or real-world evidence studies.
4. **Tier 4: Modeling Assumption (MA):** Structural or operational assumption introduced to enable simulation execution where empirical data is sparse or uncharacterized.
5. **Tier 5: Calibrated against Aggregate Statistics (CAS):** Tuned to match cross-sectional census or national survey target statistics.

---

## 2. Hypertension Module (`mod-htn-01`) Parameter Catalog

| State / Transition | Parameter Name | Value / Distribution | Provenance Tier | Evidence Source / Benchmark | Uncertainty / Boundaries |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `AgeCheck -> HypertensionOnset` | Annual Adult Incidence Hazard | $\lambda = 0.0344\text{ yr}^{-1}$ ($3.44\%$) | **Tier 1 (PEE)** | Prospective urban/rural Indian cohorts: CURES (Chennai Urban Rural Epidemiology Study) & CCDC. | $95\%\text{ CI: } [0.028, 0.041]$. Age-dependent ($25\text{--}65+$). |
| `HypertensionOnset -> AsymptomaticDelay` | Latent Asymptomatic Duration | $90\text{ days}$ ($3\text{ months}$) | **Tier 4 (MA)** | Simulation heuristic for delayed detection in opportunistic screening settings. | Real-world latency is unmeasured; range $30\text{--}365\text{ days}$. |
| `RecordBloodPressure` | Initial Systolic BP Range | Uniform($145.0, 168.0$) mmHg | **Tier 2 (CG)** | Stage 1 / Stage 2 Essential Hypertension definition (Indian Guidelines on Hypertension IV). | Minimum $140\text{ mmHg}$; severe crisis $>180\text{ mmHg}$ excluded. |
| `PrescribeFirstLineAntihypertensive` | First-Line Monotherapy Drug | Amlodipine 5mg QD (`AML-5`) | **Tier 2 (CG)** | IHCI Protocol & Indian Guidelines on Hypertension IV (First-line CCB). | Monotherapy rule; $100\%$ compliance is an assumption. |
| `MaintenanceDelay` | Routine Follow-up Surveillance Interval | $180\text{ days}$ ($6\text{ months}$) | **Tier 2 (CG)** | Standard chronic monitoring guidelines for stable controlled hypertension. | Real-world follow-up exhibits high variance ($30\text{--}365\text{d}$). |
| `MeasureFollowUpBP -> BPControlled` | Blood Pressure Control Rate | $p = 0.60$ ($60.0\%$) | **Tier 3 (ELD)** | India Hypertension Control Initiative (IHCI) real-world program evaluations. | Reported clinic control rates vary from $45\%\text{ to }70\%$. |
| `BPControlled` | Controlled SBP Range | Uniform($120.0, 135.0$) mmHg | **Tier 2 (CG)** | Target SBP for treated adult hypertension (ICMR/IHCI). | Target $< 130\text{ mmHg}$ in high-risk patients. |
| `BPUncontrolled` | Uncontrolled SBP Range | Uniform($145.0, 165.0$) mmHg | **Tier 2 (CG)** | Suboptimal control range under monotherapy. | Extreme uncontrolled ($>170\text{ mmHg}$) not modeled. |
| `PrescribeStepUpAntihypertensive` | Step-Up Dual Combination Therapy | Add Telmisartan 40mg QD (`TEL-40`) | **Tier 2 (CG)** | IHCI Stepped Care Protocol (Add ARB to CCB for uncontrolled BP). | Dual therapy assumption; fixed-dose combinations not modeled. |
| `ComplicationEvaluation -> HypertensiveCKD` | Chronic Kidney Disease Annual Incidence | $p = 0.03\text{ yr}^{-1}$ ($3.0\%$) | **Tier 1 (PEE)** | Longitudinal renal impairment rates in uncontrolled hypertensive cohorts. | Highly dependent on BP severity and duration of disease. |
| `ComplicationEvaluation -> CardiovascularDeath` | Fatal Acute Myocardial Infarction | $p = 0.05\text{ yr}^{-1}$ (Age $\ge 75$) | **Tier 5 (CAS)** | Calibrated to approximate cardiovascular mortality in elderly hypertensives. | Real-world hazard depends on smoking, lipids, and diabetes. |

---

## 3. Type 2 Diabetes Module (`mod-t2d-01`) Parameter Catalog

| State / Transition | Parameter Name | Value / Distribution | Provenance Tier | Evidence Source / Benchmark | Uncertainty / Boundaries |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `T2DAgeCheck -> PrediabetesOnset` | Annual Adult Incidence Hazard | $\lambda = 0.0149\text{ yr}^{-1}$ ($1.49\%$) | **Tier 1 (PEE)** | CARRS (Center for cArdiometabolic Risk Reduction in South Asia) longitudinal study. | $95\%\text{ CI: } [0.012, 0.019]$. Elevated with obesity/family history. |
| `PrediabetesProgressionDelay` | Latent Prediabetes Duration | $180\text{ days}$ ($6\text{ months}$) | **Tier 4 (MA)** | Simulation approximation of transition from impaired glucose to clinical diabetes. | Prospective conversion rates typically span $1\text{--}3\text{ years}$. |
| `RecordHbA1c` | Diagnostic HbA1c Range | Uniform($7.4, 9.6$) % | **Tier 2 (CG)** | Diagnostic criteria for overt Type 2 Diabetes (ICMR Guidelines / ADA). | Diagnostic threshold is $\ge 6.5\%$; modeled as symptomatic at visit. |
| `InitiateDiabeticCarePlan` | Structured Lifestyle Management | `CP-DIAB-01` Diet/Exercise | **Tier 2 (CG)** | ICMR Guidelines for Management of Type 2 Diabetes (Standard Care Plan). | Patient adherence assumed $100\%$ in baseline. |
| `PrescribeMetformin` | First-Line Hypoglycemic Drug | Metformin 500mg BID (`MET-500`) | **Tier 2 (CG)** | First-line oral hypoglycemic monotherapy across all Indian & international guidelines. | GFR contraindications ($<30\text{ mL/min}$) checked by safety rules. |
| `QuarterlySurveillanceDelay` | Routine Glycemic Surveillance Interval | $90\text{ days}$ ($3\text{ months}$) | **Tier 2 (CG)** | Standard quarterly HbA1c monitoring recommendation (ICMR/RSSDI). | Real-world adherence to quarterly monitoring is $<35\%$. |
| `MeasureFollowUpHbA1c -> Controlled` | Glycemic Control Rate under Monotherapy | $p = 0.45$ ($45.0\%$) | **Tier 1 (PEE)** | CARRS Cohort & ICMR-INDIAB Real-World Glycemic Control Studies. | Control rates vary from $35\%\text{ to }52\%$ depending on socioeconomics. |
| `GlycemicControlled` | Controlled HbA1c Range | Uniform($6.4, 6.9$) % | **Tier 2 (CG)** | Target glycemic control range for non-elderly adults (ICMR). | Target $< 7.0\%$; elderly targets relaxed to $< 8.0\%$. |
| `GlycemicUncontrolled` | Uncontrolled HbA1c Range | Uniform($7.5, 9.2$) % | **Tier 2 (CG)** | Suboptimal glycemic control range triggering therapy intensification. | Severe hyperglycemia ($>10.0\%$) not modeled. |
| `PrescribeStepUpHypoglycemic` | Step-Up Dual Oral Hypoglycemic | Add Glimepiride 1mg QD (`GLIM-1`) | **Tier 2 (CG)** | ICMR Step-up Guideline: Add Sulfonylurea to Metformin if HbA1c $> 7.0\%$. | Alternative DPP-4i (Teneligliptin) used in practice; SU selected as benchmark. |
| `DiabeticComplication -> Nephropathy` | Diabetic Microvascular Nephropathy | $p = 0.04\text{ yr}^{-1}$ ($4.0\%$) | **Tier 1 (PEE)** | Mohan et al., CURES-45 longitudinal microalbuminuria incidence in Asian Indians. | Risk escalates with uncontrolled HbA1c and concurrent hypertension. |

---

## 4. Preservation of Safety Hierarchy

Probabilistic module transitions operate strictly beneath the simulation platform's **mandatory clinical safety rules**:
1. **Contraindication Invariant:** Even if a module dictates `PrescribeMetformin`, the pharmacy rule engine checks renal function (`eGFR < 30`) and active acute kidney injury. If contraindicated, the order is blocked by an allergy/contraindication safety veto.
2. **Post-Mortem Event Invariant:** If background mortality triggers (`patient.is_alive = False`), all pending appointments, consultations, and prescriptions are immediately canceled in the discrete-event scheduler.
3. **Temporal Invariant:** Biological onset timestamps are stored as latent state and cannot generate clinical billing records, diagnostic invoices, or medication orders prior to an encounter timestamp.
