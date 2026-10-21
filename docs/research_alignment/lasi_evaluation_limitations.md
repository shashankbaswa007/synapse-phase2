# SYNAPSE Phase 2: LASI Wave 1 External Evaluation Limitations & Assumptions

**Document ID:** `SYNAPSE-LASI-LIMIT-05`  
**Date:** October 2026  
**Auditor / Engineer:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** COMPLETE & PRESPECIFIED  

---

## 1. Executive Summary & Purpose

External evaluation of synthetic health data against real-world cohorts requires transparent disclosure of methodological boundaries. Conflating statistical compatibility with clinical identity, or extrapolating cross-sectional survey findings to longitudinal disease progression, undermines research validity.

This document systematically catalogs the **methodological limitations, survey design constraints, measurement discrepancies, and epidemiological boundaries** of evaluating SYNAPSE Phase 2 against LASI Wave 1.

---

## 2. Inventory of Methodological & Epidemiological Limitations

### 2.1 Cross-Sectional Design vs. Longitudinal Clinical Trajectories
- **The Constraint:** LASI Wave 1 (2017–2018) is fundamentally a single-contact cross-sectional survey (Wave 2 follow-up microdata is not yet publicly released).
- **Impact on Evaluation:**
  - *Incident Disease Emergence:* LASI captures retrospective self-reported age of diagnosis (`r1diabage`, `r1hyperage`), which is prone to severe recall telescoping and digit rounding. Wave 1 **cannot** validate prospective annual attack rates (e.g. $1.5\%\text{ per year}$ for diabetes) or survival time to diagnosis.
  - *Biomarker Trajectory Slopes:* A single laboratory HbA1c reading per participant **cannot** validate within-patient rates of glycemic deterioration ($\Delta\text{HbA1c}/\text{year}$) or blood pressure reductions following medication initiation.
  - *Prespecified Rule:* No claim of longitudinal trajectory validation may be made based on LASI Wave 1 cross-sectional distributions.

### 2.2 Population Age Eligibility Truncation ($\text{Age} \ge 45$)
- **The Constraint:** LASI Wave 1 recruited resident adults aged $\ge 45\text{ years}$ and their resident spouses (regardless of age). Resident spouses aged $< 45$ comprise $< 2\%$ of participants and reflect non-random household selection.
- **Impact on Evaluation:**
  - LASI is strictly valid only for Population B (Older Adults, $\ge 45\text{ years}$).
  - LASI provides **no empirical benchmark** for general adults aged $20\text{--}44\text{ years}$ (Population A).
  - *Prespecified Rule:* Synthetic patients aged $< 45$ must be excluded when comparing to LASI. Extrapolating older-adult LASI findings to younger adult populations is scientifically invalid.

### 2.3 Dried Blood Spot (DBS) vs. Venous HPLC Assay Divergence
- **The Constraint:** In LASI, HbA1c was measured from capillary blood collected on Whatman 903 filter paper (Dried Blood Spots, DBS) in field settings, rather than standard clinical venipuncture.
- **Laboratory Calibration Shift:**
  - DBS samples undergo drying, temperature fluctuations during transport, and elution, resulting in a documented linear calibration shift relative to centralized venous whole-blood HPLC:
    $$\text{HbA1c}_{\text{venous}} \approx 0.94 \times \text{HbA1c}_{\text{DBS}} + 0.45$$
  - DBS assays have higher coefficients of variation ($\text{CV} \approx 4\%\text{--}7\%$) compared to centralized clinical laboratory auto-analyzers ($\text{CV} \le 2\%$).
  - *Handling Rule:* When evaluating synthetic HbA1c observations (which model venous laboratory tests), the empirical transformation must be applied and disclosed.

### 2.4 Household Survey Setting vs. Outpatient Clinical Environment
- **The Constraint:** LASI blood pressure readings were obtained in the respondent's home by trained non-physician enumerators using automated Omron digital monitors after structured 5-minute rest intervals. In contrast, SYNAPSE observations model facility-based consultations.
- **Clinical Differences:**
  - *White-Coat Effect:* Facility-based clinical blood pressures typically exhibit an elevation of $5\text{--}12\text{ mmHg}$ relative to relaxed household measurements.
  - *Averaging Protocols:* LASI measures three readings and averages the 2nd and 3rd readings. Clinical practice in India frequently records a single reading.
  - *Handling Rule:* Synthetic observations must be compared against the protocolized average of the 2nd and 3rd readings, with explicit disclosure of potential white-coat divergence.

### 2.5 Diagnostic Case Definitions: Self-Report vs. Clinical Diagnostic Coding
- **The Constraint:** In LASI, chronic disease status is determined primarily by participant recall of prior physician diagnosis ("Has a doctor ever told you...").
- **Real-World Under-Diagnosis Bias:**
  - In community-based epidemiological surveys in India, $30\%\text{--}50\%$ of individuals with objectively measured hypertension (SBP $\ge 140$ or DBP $\ge 90$) or diabetes (HbA1c $\ge 6.5\%$) are unaware of their condition and report "No" to the diagnosis question.
  - In SYNAPSE Phase 2, disease status is governed by explicit diagnostic codes (`I10`, `E11.9`) assigned upon clinical detection.
  - *Handling Rule:* Baseline prevalence comparisons must harmonize self-reported diagnosis with objective biomarker thresholds (SBP $\ge 140$, DBP $\ge 90$, or $\text{HbA1c} \ge 6.5\%$).

### 2.6 Complex Survey Design & Variance Estimation
- **The Constraint:** LASI employed a multistage stratified cluster design with unequal selection probabilities.
- **Analytical Impact:**
  - Unweighted sample means do not reflect the national population distribution of India.
  - Failing to account for primary sampling units (PSUs) and strata leads to underestimation of standard errors and overly narrow confidence intervals (design effects typically range from $1.5$ to $3.0$).
  - *Handling Rule:* All reference point estimates must incorporate survey sampling weights (`r1wtresp`). When survey metadata is missing or incomplete, unweighted confidence intervals must not be presented as fully representative.

### 2.7 Cross-Sectional Medication Roster vs. Longitudinal Escalation Trajectory
- **The Constraint:** LASI records current daily medications at the time of the survey interview.
- **Clinical Distinction:**
  - Cross-sectional rosters indicate the static proportion of treated patients taking monotherapy vs. dual therapy.
  - They **cannot** measure the dynamic rate of clinical step-up, median days to escalation, or physician therapeutic inertia.
  - *Prespecified Rule:* Static medication proportions must not be cited as evidence of correct longitudinal treatment intensification timing.

---

## 3. Strict Boundary Matrix Summary

| Validation Dimension | Methodological Status Against LASI Wave 1 | Prespecified Boundary / Action |
| :--- | :--- | :--- |
| **Demographics ($\ge 45$)** | **VALID (Directly Comparable)** | Truncate synthetic cohort to $\text{Age} \ge 45$; apply SRS direct standardization. |
| **Demographics ($< 45$)** | **INVALID (Non-Comparable)** | Mark metric `NOT_COMPARABLE`. Do not extrapolate older-adult findings. |
| **Blood Pressure (Continuous)** | **VALID (Directly Comparable)** | Compare against mean of 2nd & 3rd readings using KS test and Wasserstein distance. |
| **HbA1c (Continuous)** | **VALID (With Assay Adjustment)**| Apply DBS-to-venous conversion equation ($0.94 \times \text{DBS} + 0.45$). |
| **Baseline Prevalence ($\ge 45$)**| **VALID (Directly Comparable)** | Combine self-report with objective biomarker thresholds. |
| **Prospective Incidence** | **INVALID (Data Unavailable)** | Cross-sectional Wave 1 cannot validate incidence. Defer to CARRS or LASI Wave 2. |
| **Trajectory Slopes** | **INVALID (Data Unavailable)** | Single-contact survey cannot validate longitudinal within-patient rates of change. |
| **Treatment Escalation Timing**| **INVALID (Data Unavailable)** | Cross-sectional regimens cannot validate Kaplan-Meier escalation curves. |
| **All-Cause Survival** | **INVALID (Data Unavailable)** | Wave 1 lacks prospective follow-up time. Benchmark survival against Census SRS life tables. |
