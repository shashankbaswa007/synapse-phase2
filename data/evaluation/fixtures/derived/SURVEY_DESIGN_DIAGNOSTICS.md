# LASI Survey Design & Missingness Diagnostics Report

**Source Data Label:** `data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`  
**Audit Timestamp:** `2026-10-24T18:24:02.248323`  
**Total Ingested Participants:** 50  
**Total Survey Strata:** 13  
**Total Primary Sampling Units (PSUs):** 25  
**Singleton Strata ($n_h = 1$):** 1 (7.69%)  

---

## 1. Survey Design Fields & Missingness

| Design Field | Present | Non-Null Count | Missing Count | Missingness % | Audit Note |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`survey_weight`** | Yes | 50 | 0 | 0.0% |  |
| **`strata`** | Yes | 50 | 0 | 0.0% |  |
| **`psu`** | Yes | 50 | 0 | 0.0% |  |
| **`household_id`** | No | 0 | 50 | 100.0% |  |
| **`state`** | No | 0 | 50 | 100.0% |  |
| **`urban_rural`** | No | 0 | 50 | 100.0% |  |

---

## 2. Sampling Weight Diagnostics

- **Weights Range:** [0.8, 1.45]
- **Mean Weight:** 1.1 (Median: 1.1, SD: 0.1632)
- **Coefficient of Variation $\text{CV}(w)$:** 0.148
- **Kish Design Effect $\text{DEFF}_w$:** 1.022
- **Kish Effective Sample Size $n_{\text{eff}}$:** 48.94
- **Max-to-Min Weight Ratio:** 1.81
- **Extreme Weights Count:** 0 (0.0%)
- **Top 1% Weight Share:** 2.64% (Top 5%: 7.73%)
- **Weight Trimming Indicated:** No

---

## 3. Stratum-PSU Topology & Singleton Audit

- **Average PSU Size:** 2.0 participants (Range: [2, 2])
- **Singleton Strata Count:** 1 of 13 strata have $n_h = 1$.
- **Methodological Requirement:** Singleton strata require collapsing with adjacent design strata or grand-mean centering before Taylor series variance estimation.

---

## 4. Module Participation & Biomarker Non-Response

- **Individual Survey Participants:** 50
- **Biomarker Module Participants:** 50
- **Biomarker Non Response Count:** 0
- **Biomarker Non Response Pct:** 0.0
- **Blood Pressure Valid Count:** 50
- **Blood Pressure Missingness Pct:** 0.0
- **Hba1C Valid Count:** 49

---

## 5. Estimand Eligibility Framework

| Estimand ID | Name | Available N | Support Classification | Ineligibility / Methodological Notes |
| :--- | :--- | :---: | :---: | :--- |
| **`sbp_mean_overall`** | Mean Systolic Blood Pressure (Older Adults >= 45) | 50 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |
| **`dbp_mean_overall`** | Mean Diastolic Blood Pressure (Older Adults >= 45) | 50 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |
| **`sbp_quantiles_age_sex`** | SBP Quantiles (25th, 50th, 75th) by Age-Sex Strata | 50 | `UNSUPPORTED` | Severely sparse age-sex domains (n < 15): Male_45_54, Male_55_64, Male_65_74, Male_75_plus, Female_45_54, Female_55_64, Female_65_74, Female_75_plus. |
| **`hypertension_prevalence`** | Hypertension Prevalence (Composite: BP >= 140/90 or Rx or Dx) | 49 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |
| **`hypertension_awareness`** | Hypertension Awareness Rate (Self-reported Dx among Hypertensives) | 49 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |
| **`hypertension_treatment`** | Hypertension Treatment Rate (Medication among Diagnosed/Hypertensives) | 50 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |
| **`hypertension_control`** | Hypertension Control Rate (BP < 140/90 among Treated) | 50 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |
| **`hba1c_mean_overall`** | Mean HbA1c Laboratory Assay (%) | 49 | `DESIGN_WEIGHTED_OBSERVED` | Supported with full complex survey design weights. |

---

## 6. Actionable Diagnostic Warnings

> [!WARNING]
> SINGLETON PSUs: 1 strata contain exactly 1 PSU (e.g. ['ST_13']). Design variance estimation requires explicit singleton handling (certainty, centering, or collapsing).

> [!WARNING]
> SPARSE DOMAINS: Sample size n < 30 or n_eff < 25 in domains: Male_45_54, Male_55_64, Male_65_74, Male_75_plus, Female_45_54, Female_55_64, Female_65_74, Female_75_plus.


---

*CONFIDENTIALITY ASSURANCE: This report contains strictly aggregate statistical summaries. Zero participant-level identifiers, respondent keys, or protected health information are present in this document.*