# SYNAPSE Phase 2: LASI Wave 1 Variable Mapping Dictionary

**Document ID:** `SYNAPSE-LASI-MAP-02`  
**Date:** October 2026  
**Auditor / Engineer:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** COMPLETE & VERIFIED  

---

## 1. Overview and Mapping Principles

External evaluation requires mapping real-world survey variables to the standardized internal electronic health record schema exported by SYNAPSE Phase 2 (`patients.csv`, `encounters.csv`, `conditions.csv`, `medications.csv`, `observations.csv`, `deaths.csv`).

This dictionary audits all relevant variables in the **Longitudinal Aging Study in India (LASI) Wave 1**, detailing:
1. Harmonized Gateway to Global Aging Data (G2Aging) variable names.
2. Raw IIPS survey module variable names.
3. Target SYNAPSE Phase 2 internal fields.
4. Units, measurement protocols, and missingness handling.
5. Availability status and analytical suitability.

---

## 2. Comprehensive Variable Mapping Matrix

| Domain | G2Aging Harmonized Field | Raw IIPS Field | Target SYNAPSE Field & Code | Unit | Measurement Protocol & Definition | Missing Value Sentinels | Availability Status | Analytical Suitability |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **Demographics** | `r1agey` | `age_years` / `q003` | `patients.age` | Years | Chronological age at interview | `-999`, `-99`, `.` | **AVAILABLE** ($N=72,250$) | Directly comparable for age $\ge 45$. |
| **Demographics** | `ragender` | `gender` / `q002` | `patients.gender` | Text | Respondent sex ($1=\text{Male}$, $2=\text{Female}$) | Missing string, `.` | **AVAILABLE** ($N=72,250$) | Directly comparable. |
| **Survey Design**| `r1wtresp` | `ind_weight` | Internal `survey_weight` | Weight | Individual sampling weight adjusted for non-response | Missing, $\le 0.0$ | **AVAILABLE** | Essential for representative estimates. |
| **Survey Design**| `r1strata` | `strata` | Internal `strata` | Code | Sampling stratum (State $\times$ Urban/Rural) | Blank, `.` | **AVAILABLE** | Complex survey clustering. |
| **Survey Design**| `r1psu` | `psu` | Internal `psu` | Code | Primary sampling unit / Census Enumeration Block | Blank, `.` | **AVAILABLE** | Complex survey variance. |
| **Vitals (BP)** | `r1bpsys1` | `sys_bp_1` | `observations.value` (`SBP`) | mmHg | First seated SBP reading (Omron HEM-7121) | `-999`, $999$, $<60$, $>280$ | **AVAILABLE** | Used only for fallback if 2 & 3 missing. |
| **Vitals (BP)** | `r1bpsys2` | `sys_bp_2` | `observations.value` (`SBP`) | mmHg | Second seated SBP reading (after 5-min rest) | `-999`, $999$, $<60$, $>280$ | **AVAILABLE** | Primary component of protocol mean. |
| **Vitals (BP)** | `r1bpsys3` | `sys_bp_3` | `observations.value` (`SBP`) | mmHg | Third seated SBP reading (after additional rest) | `-999`, $999$, $<60$, $>280$ | **AVAILABLE** | Primary component of protocol mean. |
| **Vitals (BP)** | `r1bpdia1` | `dia_bp_1` | `observations.value` (`DBP`) | mmHg | First seated DBP reading | `-999`, $999$, $<40$, $>160$ | **AVAILABLE** | Used only for fallback if 2 & 3 missing. |
| **Vitals (BP)** | `r1bpdia2` | `dia_bp_2` | `observations.value` (`DBP`) | mmHg | Second seated DBP reading | `-999`, $999$, $<40$, $>160$ | **AVAILABLE** | Primary component of protocol mean. |
| **Vitals (BP)** | `r1bpdia3` | `dia_bp_3` | `observations.value` (`DBP`) | mmHg | Third seated DBP reading | `-999`, $999$, $<40$, $>160$ | **AVAILABLE** | Primary component of protocol mean. |
| **Biomarker** | `r1hba1c` | `dbs_hba1c` | `observations.value` (`HbA1c`) | % | Dried Blood Spot (DBS) centralized laboratory assay | `-999`, $<3.5$, $>20.0$ | **AVAILABLE** ($n \approx 25,000$ subsample) | Comparable after venous adjustment ($0.94 \times \text{DBS} + 0.45$). |
| **Disease: HTN** | `r1hypere` | `htn_diagnosed` | `conditions.condition_code == 'I10'` | Binary | Self-reported doctor-diagnosed hypertension | `-999`, `-99`, `.` | **AVAILABLE** | Comparable for baseline point prevalence. |
| **Disease: T2D** | `r1diabe` | `diab_diagnosed` | `conditions.condition_code == 'E11.9'` | Binary | Self-reported doctor-diagnosed type 2 diabetes | `-999`, `-99`, `.` | **AVAILABLE** | Comparable for baseline point prevalence. |
| **Disease: CKD** | `r1kidneye`| `ckd_diagnosed` | `conditions.condition_code in ('I12.9', 'E11.2')`| Binary | Self-reported doctor-diagnosed chronic kidney disease | `-999`, `-99`, `.` | **AVAILABLE** | Self-report lacks eGFR/uACR clinical precision. |
| **Medication** | `r1med_bp` | `rx_htn` | `medications.drug_name` in antihypertensives | Binary | Current daily consumption of BP-lowering drugs | `-999`, `.` | **AVAILABLE** | Cross-sectional treatment rate. |
| **Medication** | `r1med_diab`| `rx_t2d` | `medications.drug_name` in hypoglycemics | Binary | Current daily consumption of diabetes medications | `-999`, `.` | **AVAILABLE** | Cross-sectional treatment rate. |
| **Incidence** | `r1diabage`| `age_diab_onset` | New onset $t > 31\text{d}$ among disease-free | Years | Retrospective self-reported age of onset | `-999`, `.` | **UNAVAILABLE / METHODOLOGICALLY INVALID** | Retrospective recall bias; prospective incidence requires Wave 2. |
| **Encounters** | `r1opd_vis` | `opd_visits_12m` | `encounters` rate per person-year | Count | Self-reported outpatient visits in past 12 months | `-999`, `.` | **LIMITED COMPARABILITY** | Survey recall frequency vs discrete consultation schedule. |

---

## 3. Detailed Endpoint Compatibility Analyses

### 3.1 Blood Pressure (SBP and DBP)
- **Reference Measurement Protocol:** Three seated readings taken at 5-minute intervals using Omron HEM-7121 digital oscillometric monitors.
- **SYNAPSE Estimand:** Simulated clinical outpatient vital sign observations generated during initial screening consultations ($t \le 31\text{d}$) and routine follow-up encounters ($t > 180\text{d}$).
- **Mapping Transformation:**
  $$\text{SBP}_{\text{ref}} = \frac{\text{r1bpsys2} + \text{r1bpsys3}}{2}, \quad \text{DBP}_{\text{ref}} = \frac{\text{r1bpdia2} + \text{r1bpdia3}}{2}$$
- **Comparability Classification:** **`Directly Comparable`** among untreated older adults ($Age \ge 45$). Continuous distributions evaluated via Two-sample Kolmogorov-Smirnov test ($D_{\text{KS}}$) and 1-Wasserstein distance ($W_1$).

### 3.2 Glycated Hemoglobin ($\text{HbA1c}$)
- **Reference Measurement Protocol:** Capillary blood collected on Whatman 903 filter paper (Dried Blood Spots, DBS), shipped to centralized reference laboratories, and assayed via immunoturbidimetry or HPLC.
- **SYNAPSE Estimand:** Simulated diagnostic laboratory encounters in diabetic patients representing standard centralized venous blood HPLC.
- **Mapping Transformation:**
  $$\text{HbA1c}_{\text{venous\_equiv}} = 0.94 \times \text{r1hba1c} + 0.45$$
- **Comparability Classification:** **`Comparable After Documented Transformation`**. Evaluated on continuous deciles and clinical categories ($<7.0\%$, $7.0\text{--}8.0\%$, $>8.0\%$).
- **Caveat:** Cross-sectional DBS measurements **cannot** validate longitudinal biomarker deterioration or within-patient trajectory slopes.

### 3.3 Hypertension & Type 2 Diabetes Prevalence
- **Reference Measurement Protocol:** Self-reported affirmative response to "Has any doctor or healthcare professional ever diagnosed you with hypertension / diabetes?" supplemented by biomarker module confirmation.
- **SYNAPSE Estimand:** Baseline disease status at study inception ($t \le 31\text{d}$) based on active diagnostic condition codes (`I10` for hypertension, `E11.9` for type 2 diabetes).
- **Mapping Transformation:** Age-truncated to patients aged $\ge 45\text{ years}$ to match LASI eligibility.
- **Comparability Classification:** **`Comparable After Documented Transformation`** (Age-truncation and Census SRS age-sex standardization).
