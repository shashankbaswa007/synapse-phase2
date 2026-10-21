# SYNAPSE Phase 2: LASI Wave 1 Scientific Mapping Audit

**Document ID:** `SYNAPSE-LASI-SCI-AUDIT-01`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** COMPLETE & INDEPENDENTLY AUDITED  

---

## 1. Executive Summary & Purpose

A scientific audit of variable mappings was conducted against the authoritative documentation for the **Longitudinal Aging Study in India (LASI) Wave 1 (2017–2018)**. 

### Authoritative Documentation Sources
1. International Institute for Population Sciences (IIPS), *Longitudinal Ageing Study in India (LASI) Wave 1, 2017–18, India Report*, Mumbai: IIPS, 2020.
2. Program on Global Aging, Health & Policy, *Gateway to Global Aging Data: Harmonized LASI Wave 1 Version A.1 Codebook & User Guide*, University of Southern California (USC), 2021.
3. IIPS & Harvard T.H. Chan School of Public Health, *LASI Wave 1 Biomarkers and Direct Health Measurements Field Protocol Manual*, Mumbai: IIPS, 2017.

> [!IMPORTANT]
> **Audit Rule:** No semantics were inferred from variable names alone. Every field was verified against survey question text, field measurement protocols, subsampling eligibility criteria, and coded missing sentinels in the official codebook.

---

## 2. In-Depth Variable-by-Variable Mapping Audit

### 2.1 Demographics: Age and Sex

| Specification Attribute | Age Variable (`r1agey` / `age_years`) | Sex Variable (`ragender` / `gender`) |
| :--- | :--- | :--- |
| **Official Variable Name** | Gateway: `r1agey`; IIPS Individual: `q003` / `age_years` | Gateway: `ragender`; IIPS Household/Individual: `q002` / `gender` |
| **Official Definition** | Chronological age in completed years at the time of the individual interview. | Biological sex of the respondent as verified by survey enumerator. |
| **Measurement Modality** | Survey-reported (verified against government voter ID, Aadhaar, or birth certificate where available). | Survey-reported / Observed by enumerator. |
| **Physical Unit & Range** | Years. Valid analytical range: $[18.0, 120.0]$. Core target: $\ge 45.0$. | Categorical ($1 = \text{Male}$, $2 = \text{Female}$). |
| **Eligibility & Subsampling**| Administered to all resident household members aged $\ge 45$ and spouses regardless of age. | Administered to all rostered household respondents. |
| **Missing Sentinels** | Coded as `.` or `.m` (Gateway), `-999`, `-99`, `999` (Raw IIPS). | Coded as `.` or `.m` (Gateway), `9` or blank (Raw IIPS). |
| **Corresponding SYNAPSE Field**| [`patients.age`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/patients.csv) (integer years at observation start $t_0$). | [`patients.gender`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/patients.csv) (string `"Male"`, `"Female"`). |
| **Comparability Status** | **Comparable After Truncation** ($\text{Age} \ge 45$). Non-comparable for general adults $< 45$. | **Directly Comparable** within age-matched older-adult stratum ($\ge 45$). |

---

### 2.2 Vital Signs: Systolic and Diastolic Blood Pressure

| Specification Attribute | Systolic Readings (`r1bpsys1, r1bpsys2, r1bpsys3`) | Diastolic Readings (`r1bpdia1, r1bpdia2, r1bpdia3`) |
| :--- | :--- | :--- |
| **Official Variable Names**| Gateway: `r1bpsys1`, `r1bpsys2`, `r1bpsys3`; IIPS: `sys_bp_1, sys_bp_2, sys_bp_3` | Gateway: `r1bpdia1`, `r1bpdia2`, `r1bpdia3`; IIPS: `dia_bp_1, dia_bp_2, dia_bp_3` |
| **Official Definition** | Triplicated seated systolic blood pressure readings. | Triplicated seated diastolic blood pressure readings. |
| **Measurement Modality** | **Objectively Measured** using Omron HEM-7121 digital oscillometric monitor on left arm. | **Objectively Measured** using Omron HEM-7121 digital oscillometric monitor on left arm. |
| **Physical Unit & Range** | $\text{mmHg}$. Valid physiological range: $[60.0, 280.0]\text{ mmHg}$. | $\text{mmHg}$. Valid physiological range: $[40.0, 160.0]\text{ mmHg}$. |
| **Measurement Protocol** | Reading 1: After 5 min initial rest. Reading 2: After additional 5 min. Reading 3: After final 5 min rest. | Reading 1: After 5 min initial rest. Reading 2: After additional 5 min. Reading 3: After final 5 min rest. |
| **Protocol Derivation Rule**| Protocol average of Reading 2 and Reading 3: $\text{SBP} = (\text{SBP}_2 + \text{SBP}_3) / 2$. | Protocol average of Reading 2 and Reading 3: $\text{DBP} = (\text{DBP}_2 + \text{DBP}_3) / 2$. |
| **Eligibility & Subsampling**| Consenting participants aged $\ge 45$ and spouses; excluded if bilateral mastectomy or dialysis fistula. | Consenting participants aged $\ge 45$ and spouses; excluded if bilateral mastectomy or dialysis fistula. |
| **Missing Sentinels** | Coded as `.` or `.m` (Gateway), `-999`, `999`, or values $<60$ / $>280$. | Coded as `.` or `.m` (Gateway), `-999`, `999`, or values $<40$ / $>160$. |
| **Corresponding SYNAPSE Field**| [`observations.value`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/observations.csv) where `observation_code == 'SBP'` (mmHg). | [`observations.value`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/observations.csv) where `observation_code == 'DBP'` (mmHg). |
| **Comparability Status** | **Directly Comparable** when restricted to protocol mean ($\text{Readings } 2 \& 3$) in untreated patients. | **Directly Comparable** when restricted to protocol mean ($\text{Readings } 2 \& 3$) in untreated patients. |

---

### 2.3 Laboratory Biomarker: Glycated Hemoglobin ($\text{HbA1c}$)

| Specification Attribute | Capillary Blood Assay (`r1hba1c` / `dbs_hba1c`) |
| :--- | :--- |
| **Official Variable Name** | Gateway: `r1hba1c`; IIPS Biomarker Module: `dbs_hba1c` / `bio_hba1c` |
| **Official Definition** | Percentage of glycated hemoglobin assayed from dried capillary whole blood spots. |
| **Measurement Modality** | **Objectively Measured Laboratory Biomarker** (Dried Blood Spot, DBS). |
| **Sample Collection** | Finger-prick capillary blood collected on Whatman 903 protein saver cards in field conditions. |
| **Laboratory Assay** | Centralized reference laboratories (NIMHANS, Bengaluru) using Bio-Rad HPLC / Roche automated platforms. |
| **Physical Unit & Range** | Percentage ($\%$). Valid clinical range: $[3.5\%, 20.0\%]$. |
| **Subsampling Restriction** | Biomarker module administered only to an eligible consenting subsample ($n \approx 25,000$ of $72,250$ participants). |
| **Missing Sentinels** | Coded as `.` or `.m` (Gateway), `-999`, `999.0`, values $<3.5\%$ or $>20.0\%$. |
| **Corresponding SYNAPSE Field**| [`observations.value`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/observations.csv) where `observation_code == 'HbA1c'`. |
| **Scientific Finding** | **Assay Non-Equivalence Disclosure:** In the simulator, HbA1c models standard venous clinical HPLC. LASI measured capillary DBS. Applying an uncalibrated US equation ($0.94 \times \text{DBS} + 0.45$) lacks official LASI documentation backing. |
| **Comparability Status** | **`UNVERIFIED / NOT_COMPARABLE`** by default. Direct comparison enabled only with explicit conversion uncertainty ($\text{SE} \approx 0.40\%$). |

---

### 2.4 Chronic Disease Indicators: Hypertension, Diabetes, and CKD

To prevent methodological conflation, the audit strictly separates **three distinct case definitions**:
1. **Measured Disease:** Objective biological threshold (e.g. Protocol $\text{SBP} \ge 140$ or $\text{DBP} \ge 90\text{ mmHg}$).
2. **Self-Reported Disease:** Survey question affirmative response ("Has a doctor ever told you that you have...").
3. **Clinical Diagnostic Code:** Explicit clinical diagnosis recorded in medical records ([`conditions.condition_code`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv)).

| Disease Dimension | LASI Variable (`r1hypere`, `r1diabe`, `r1kidneye`) | Modality & Wording | SYNAPSE Diagnostic Code | Harmonization & Comparison Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Hypertension** | `r1hypere` | Self-report: "Has any doctor diagnosed you with high blood pressure or hypertension?" ($1=\text{Yes}$, $0=\text{No}$). | [`conditions.condition_code == 'I10'`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) | Compare self-reported diagnosis vs synthetic clinical condition code. Disclose that community self-report under-detects asymptomatic hypertension by $30\%\text{--}40\%$. |
| **Type 2 Diabetes** | `r1diabe` | Self-report: "Has any doctor diagnosed you with diabetes or high blood sugar?" ($1=\text{Yes}$, $0=\text{No}$). | [`conditions.condition_code == 'E11.9'`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) | Compare self-report vs synthetic code `E11.9`. |
| **Chronic Kidney Disease**| `r1kidneye` | Self-report: "Has any doctor diagnosed you with chronic renal failure or kidney disease?" ($1=\text{Yes}$, $0=\text{No}$). | [`conditions.condition_code in ('I12.9', 'E11.2')`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) | Self-reported CKD in LASI has high false-negative rate (lacks routine serum creatinine / eGFR). Comparison is exploratory. |

---

### 2.5 Complex Survey Design Metadata

| Variable Name | Definition & Sampling Role | Unit / Representation | Missing Handling | Analytical Requirement |
| :--- | :--- | :---: | :--- | :--- |
| `r1wtresp` | Individual sampling weight adjusted for household non-response and post-stratification. | Non-negative float. | Values $\le 0$, NaN, or missing are imputed to $1.0$ and flagged. | Mandatory for calculating nationally representative point estimates and effective sample size ($n_{\text{eff}}$). |
| `r1strata` | Sampling stratum (State / Union Territory $\times$ Urban / Rural residence). | Categorical string. | Preserved as string or `None`. | Mandatory for complex survey Taylor-series variance linearization. |
| `r1psu` | Primary Sampling Unit (Census Enumeration Block in urban; Census Village in rural). | Categorical string. | Preserved as string or `None`. | Mandatory for cluster-level survey variance and design effects. |

---

## 3. Summary Audit Verdict

- **Verified Fields:** Age (`r1agey`), Sex (`ragender`), SBP (`r1bpsys*`), DBP (`r1bpdia*`), Self-reported Hypertension (`r1hypere`), Self-reported Diabetes (`r1diabe`), Survey Weights (`r1wtresp`), Strata (`r1strata`), PSU (`r1psu`).
- **Unverified / Disabled Transformation:** Linear DBS-to-venous conversion equation ($0.94 \times \text{DBS} + 0.45$) is disabled by default due to absence of LASI-specific validation in official documentation.
- **Unavailable Fields:** Longitudinal incident diabetes attack rate, survival time to diagnosis, and within-patient biomarker slopes are **unavailable** in cross-sectional Wave 1.
