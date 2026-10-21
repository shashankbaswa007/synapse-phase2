# SYNAPSE Phase 2: LASI Pipeline Final Pre-Ingestion Verification Report

**Document ID:** `SYNAPSE-LASI-FINAL-VERIF-08`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Evaluation Authority  
**Overall Pipeline Pre-Release Gate Verdict:** **`CONDITIONALLY_READY`**  
**External Validation Regulatory Status:** **`REFERENCE_DATA_PENDING`** (Evaluated on Synthetic Test Fixture; Genuine Microdata Awaiting DUA Approval)  
**Full Regression Test Suite:** **196 / 196 tests passed (0 failures, 0 warnings; execution time: 7.71s)**  

---

## 1. Executive Summary & Verification Mandate

This document provides the final, independent source-level verification of the **Longitudinal Ageing Study in India (LASI) Wave 1** external-evaluation pipeline within SYNAPSE Phase 2 prior to processing genuine, restricted reference microdata.

The audit was executed under strict pre-release governance rules:
1. **Zero Clinical Alterations:** Clinical transition probabilities, disease modules, treatment rules, synthetic demographic distributions, and calibration parameters were untouched.
2. **No Data Fabrication:** Genuine LASI microdata was not fabricated or claimed to have been accessed. The external validation gate remains formally locked to **`REFERENCE_DATA_PENDING`** until authentic licensed microdata is ingested.
3. **Defensive Mathematical Gating:** Software tests, statistical calculations, sample-size boundaries, survey design limitations, and biomarker assay crosswalks were inspected against official primary documentation and verified via hand-calculated proofs.

---

## 2. Verification of Variable Definitions and Estimands

### 2.1 Complete Variable Mapping Specification

The pipeline's variable ingestion mappings in [`synapse_simulator/evaluation/lasi/ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py) were audited against the *IIPS LASI Wave 1 India Report (2020)* and the *USC Gateway to Global Aging Data Harmonized Codebook (Version A.1, 2021)*:

| LASI Source Variable | Official Survey Definition & Coding | Applicable Population | Measurement Modality | Missing Sentinels & Ranges | Corresponding SYNAPSE Variable | Direct Comparability Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `r1agey` / `q003` | Chronological age in completed years at interview ($18\text{--}120$). | Rostered resident adults aged $\ge 45$ and resident spouses. | Survey-reported (verified against Voter ID / Aadhaar). | Missing: `.`, `.m`, `-999`, `999`. Range: $[18, 120]$. | [`patients.age`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/patients.csv) (integer years at $t_0$). | **Comparable for Age $\ge 45$**; Non-comparable for general adults $< 45$. |
| `ragender` / `q002` | Biological sex ($1=\text{Male}$, $2=\text{Female}$). | All rostered respondents. | Enumerator observed / Survey-reported. | Missing: `.`, `.m`, `9`. Values: $1, 2$. | [`patients.gender`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/patients.csv) (`"Male"`, `"Female"`). | **Directly Comparable** within age-matched stratum ($\ge 45$). |
| `r1bpsys1`, `r1bpsys2`, `r1bpsys3` | Triplicated seated systolic blood pressure readings (mmHg). | Consenting respondents aged $\ge 45$ & spouses (left arm). | **Objectively Measured** (Omron HEM-7121 digital monitor). | Missing: `.`, `.m`, `-999`, `999`. Range: $[60.0, 280.0]\text{ mmHg}$. | [`observations.value`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/observations.csv) (`code == 'SBP'`). | **Directly Comparable** using protocol average $(\text{SBP}_2 + \text{SBP}_3)/2$. |
| `r1bpdia1`, `r1bpdia2`, `r1bpdia3` | Triplicated seated diastolic blood pressure readings (mmHg). | Consenting respondents aged $\ge 45$ & spouses (left arm). | **Objectively Measured** (Omron HEM-7121 digital monitor). | Missing: `.`, `.m`, `-999`, `999`. Range: $[40.0, 160.0]\text{ mmHg}$. | [`observations.value`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/observations.csv) (`code == 'DBP'`). | **Directly Comparable** using protocol average $(\text{DBP}_2 + \text{DBP}_3)/2$. |
| `r1hba1c` / `dbs_hba1c` | Glycated hemoglobin percentage from dried blood spot ($3.5\%\text{--}20.0\%$). | Consenting biomarker subsample ($n \approx 25,000$). | **Objectively Measured Laboratory Biomarker** (Capillary DBS). | Missing: `.`, `.m`, `-999`, `999.0`. Range: $[3.5, 20.0]\%$. | [`observations.value`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/observations.csv) (`code == 'HbA1c'`). | **UNVERIFIED / NOT_COMPARABLE** by default (Capillary DBS vs Venous HPLC). |
| `r1hypere` | Self-report: "Has any doctor diagnosed you with high blood pressure?" ($1=\text{Yes}, 0=\text{No}$). | Core survey respondents aged $\ge 45$ & spouses. | Survey-reported physician diagnosis. | Missing: `.`, `.m`, `-999`, `9`. Values: $1, 0, 2 \to 0$. | [`conditions.condition_code == 'I10'`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) | **Comparable with Disclosure:** Self-report under-detects asymptomatic HTN by $30\%\text{--}40\%$. |
| `r1diabe` | Self-report: "Has any doctor diagnosed you with diabetes or high blood sugar?" ($1=\text{Yes}, 0=\text{No}$). | Core survey respondents aged $\ge 45$ & spouses. | Survey-reported physician diagnosis. | Missing: `.`, `.m`, `-999`, `9`. Values: $1, 0, 2 \to 0$. | [`conditions.condition_code == 'E11.9'`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) | **Directly Comparable** against synthetic primary diabetes diagnostic records. |
| `r1kidneye` | Self-report: "Has any doctor diagnosed you with chronic renal failure or kidney disease?" ($1=\text{Yes}, 0=\text{No}$). | Core survey respondents aged $\ge 45$ & spouses. | Survey-reported physician diagnosis. | Missing: `.`, `.m`, `-999`, `9`. Values: $1, 0, 2 \to 0$. | [`conditions.condition_code in ('I12.9', 'E11.2')`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) | **Exploratory Only:** Extreme under-diagnosis in community survey without routine eGFR. |
| `r1wtresp` | Individual sampling weight with non-response and post-stratification adjustment. | All individual respondents. | Derived survey design weight. | Missing/Invalid: $\le 0$ mapped to $1.0$ and flagged. | Synthetic unweighted ($w = 1.0$). | **Directly Applicable** for computing reference point estimates and Kish $n_{\text{eff}}$. |
| `r1strata` | Sampling stratum (State / UT $\times$ Urban / Rural residence). | All respondents. | Administrative sampling frame. | Missing: Preserved as `None`. | N/A (Simulation has no geographic strata). | **Survey Design Metadata:** Ingested for complex variance estimation audit. |
| `r1psu` | Primary Sampling Unit (Census Enumeration Block / Village). | All respondents. | Administrative sampling frame. | Missing: Preserved as `None`. | N/A (Synthetic individuals are i.i.d.). | **Survey Design Metadata:** Ingested for clustering telemetry. |

---

### 2.2 Strict Segregation of Disease Estimands

The audit confirmed that the pipeline enforces strict non-interchangeability across **three distinct disease constructs**:
1. **Objective Measured Disease:** Calculated solely from vital sign observations ($\text{Protocol Mean SBP} \ge 140\text{ mmHg}$ or $\text{Protocol Mean DBP} \ge 90\text{ mmHg}$).
2. **Self-Reported Survey Diagnosis:** Affirmative responses to survey questionnaire items (`r1hypere`, `r1diabe`, `r1kidneye`).
3. **Synthetic Recorded Clinical Diagnosis:** Diagnostic condition records in [`conditions.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/calibrated_mc_500/seed_42/conditions.csv) (`I10`, `E11.9`).

> [!CAUTION]
> **Scientific Finding:**
> In community surveys of older adults in India, up to **$40\%$ of hypertensive individuals are unaware of their condition** and answer "No" to `r1hypere` despite having measured SBP $> 160\text{ mmHg}$. Conversely, treated hypertensive patients on medication may have measured SBP $< 140\text{ mmHg}$ while answering "Yes" to `r1hypere`.
> 
> The pipeline strictly segregates measured blood pressure from self-reported diagnosis in [`LasiCleanedRecord`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py) and forbids collapsing them into a single variable.

---

## 3. Blood-Pressure Processing Verification

### 3.1 Measurement Protocol and Code Trace
The code path in [`synapse_simulator/evaluation/lasi/ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py) (`_calculate_average_bp` and lines 235–286) was verified against the official LASI Biomarker Protocol:
1. **Device:** Omron HEM-7121 digital oscillometric monitor.
2. **Rest Period:** 5 minutes quiet seated rest prior to Reading 1; 5 minutes quiet interval between Reading 1 and Reading 2; 5 minutes quiet interval between Reading 2 and Reading 3.
3. **Protocol Averaging Rule:** In accordance with standard cardiovascular epidemiology, Reading 1 exhibits situational white-coat reactivity. The protocol average is the arithmetic mean of Reading 2 and Reading 3:
   $$\text{SBP}_{\text{protocol}} = \frac{\text{SBP}_2 + \text{SBP}_3}{2}, \quad \text{DBP}_{\text{protocol}} = \frac{\text{DBP}_2 + \text{DBP}_3}{2}$$

### 3.2 Fallback Hierarchy and Strict Protocol Mode
The pipeline prevents silent substitution by logging an exact derivation category for every record:
- `PROTOCOL_MEAN_READINGS_2_AND_3`: Both Reading 2 and Reading 3 valid.
- `FALLBACK_READING_2_ONLY`: Reading 2 valid; Reading 3 missing.
- `FALLBACK_READING_3_ONLY`: Reading 3 valid; Reading 2 missing.
- `FALLBACK_READING_1_ONLY`: Readings 2 and 3 missing; Reading 1 substituted.
- `NO_VALID_READING`: No readings valid within physiological range.

When `strict_protocol_bp=True` is enabled, records utilizing `FALLBACK_READING_1_ONLY`, `FALLBACK_READING_2_ONLY`, or `FALLBACK_READING_3_ONLY` have `is_valid_for_bp` set to `False` and are excluded from blood pressure metrics.

### 3.3 Physiological Plausibility Boundaries and Denominators
- Permitted ranges: $\text{SBP} \in [60.0, 280.0]\text{ mmHg}$, $\text{DBP} \in [40.0, 160.0]\text{ mmHg}$.
- Readings outside these ranges are set to `None` and counted in `LasiDataQualityReport.out_of_range_counts`.
- If an individual reading is out-of-range, remaining valid readings are evaluated via the protocol rule. If no readings are valid, the record is flagged `NO_VALID_READING` and excluded from BP metrics without altering survey weights of other participants.

---

## 4. HbA1c Assay Comparability Verification

### 4.1 Assay Divergence Disclosure
- **SYNAPSE Simulator:** Emits longitudinal laboratory values modeling clinical venous whole-blood high-performance liquid chromatography (HPLC) aligned with National Glycohemoglobin Standardization Program (NGSP) standards.
- **LASI Reference Survey:** Collected capillary finger-prick blood on Whatman 903 protein saver cards (Dried Blood Spots, DBS) in non-air-conditioned field conditions across India.

### 4.2 Status of the Linear Harmonization Crosswalk
The previously utilized equation:
$$\text{HbA1c}_{\text{venous}} = 0.94 \times \text{HbA1c}_{\text{DBS}} + 0.45$$
was audited and confirmed to originate from the US Health and Retirement Study (HRS 2006/2008) in North American adults. It lacks empirical calibration against Indian DBS samples, where tropical ambient degradation and regional hemoglobin variants ($\text{HbE}, \beta\text{-thalassemia}$) introduce unquantified bias.

### 4.3 Code Verification
In [`synapse_simulator/evaluation/lasi/comparability.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/comparability.py):
```python
adjust_dbs_hba1c_to_venous(..., enabled=False) -> returns None
```
In [`synapse_simulator/evaluation/lasi/evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py):
When `enable_venous_hba1c=False` (default), direct comparison of synthetic venous HbA1c against reference DBS HbA1c is assigned:
$$\text{status} = \text{LasiMetricStatus.UNVERIFIED}$$
**Verification Proof:** Even if synthetic and reference values have zero distance ($D_{\text{KS}} = 0.0, W_1 = 0.0$), the metric CANNOT pass. It is permanently gated as `UNVERIFIED`.

---

## 5. Survey-Weighted Estimation and Methodological Boundaries

### 5.1 Formulation of Survey Statistics
In [`synapse_simulator/evaluation/metrics.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/metrics.py):
1. **Survey-Weighted Mean:** $\bar{y}_w = \frac{\sum w_i y_i}{\sum w_i}$
2. **Unbiased Bessel-Corrected Weighted Variance:**
   $$\sigma_w^2 = \frac{\sum w_i (y_i - \bar{y}_w)^2}{\sum w_i - \frac{\sum w_i^2}{\sum w_i}}$$
3. **Kish's Effective Sample Size:**
   $$n_{\text{eff}} = \frac{\left(\sum w_i\right)^2}{\sum w_i^2}$$
4. **Weighting Design Effect:** $\text{DEFF}_w = \frac{n}{n_{\text{eff}}} = 1 + \text{CV}(w)^2$
5. **Design-Adjusted Prevalence Confidence Interval:**
   $$\hat{p} \pm z_{1 - \alpha/2} \sqrt{\frac{\hat{p}(1 - \hat{p})}{n_{\text{eff}}}}$$

### 5.2 Critical Survey Design Limitation Disclosure

> [!IMPORTANT]
> **Methodological Boundary:**
> Kish's effective sample size ($n_{\text{eff}}$) and weighting design effect ($\text{DEFF}_w$) implemented in SYNAPSE account **strictly for the variance inflation caused by unequal sampling weights**.
> 
> They **DO NOT** account for the complete complex survey design:
> 1. They do not compute cluster-level primary sampling unit (PSU) variance inflation ($\text{DEFF}_{\text{cluster}} = 1 + (m-1)\rho$).
> 2. They do not apply Taylor-series linearization across state strata.
> 
> Full design-aware variance estimation requires specialized complex survey software (e.g. R `survey` package, Python `samplics`, or Stata `svy`). The current implementation is a **design-effect weighting approximation**, not a complete multistage survey linearization.

---

## 6. Age-Sex Standardization Audit & Census SRS Distribution

### 6.1 Complete 8-Strata Census SRS Standard Population
In [`synapse_simulator/evaluation/lasi/comparability.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/comparability.py), the standard population distribution represents older adults ($\ge 45$) from the Census of India Sample Registration System (SRS):

| Stratum Label | Age Band | Sex | Standard Weight ($W_k$) | Cumulative Proportion |
| :--- | :---: | :---: | :---: | :---: |
| `45-54_Male` | 45–54 | Male | **0.231** | 0.231 |
| `45-54_Female` | 45–54 | Female | **0.222** | 0.453 |
| `55-64_Male` | 55–64 | Male | **0.154** | 0.607 |
| `55-64_Female` | 55–64 | Female | **0.149** | 0.756 |
| `65-74_Male` | 65–74 | Male | **0.078** | 0.834 |
| `65-74_Female` | 65–74 | Female | **0.076** | 0.910 |
| `75+_Male` | 75+ | Male | **0.043** | 0.953 |
| `75+_Female` | 75+ | Female | **0.047** | **1.000** |

$$\sum_{k=1}^8 W_k = 1.000000$$

### 6.2 Treatment of Empty Strata and Target Population Integrity
- When strata are unobserved ($n_k = 0$), standard weights of observed strata are re-normalized:
  $$W_k' = \frac{W_k}{\sum_{j \in \text{obs}} W_j}$$
- The report explicitly documents `used_weight_mass` and `missing_weight_mass`.
- If fewer than 4 of 8 strata are populated, standardization **safely aborts** (`std == None`), preventing an unrepresentative minority from masquerading as a standardized national estimate.

---

## 7. Sample-Size and Effective-Sample-Size Gates

The pipeline enforces strict operational sample-size gates before statistical inference can proceed:

| Metric Category | Minimum Synthetic $N$ | Minimum Reference $N$ | Minimum Reference $n_{\text{eff}}$ | Gate Failure Status |
| :--- | :---: | :---: | :---: | :--- |
| **Continuous Distributions** (SBP, DBP, HbA1c) | **30** | **30** | **25.0** | `INSUFFICIENT_SAMPLE_SIZE` / `INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE` |
| **Binary Prevalences** (HTN, T2DM, CKD) | **20** | **20** | **15.0** | `INSUFFICIENT_SAMPLE_SIZE` / `INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE` |
| **Direct Strata** | **5** | **5** | **4.0** | Strata excluded / empty warning |

> [!NOTE]
> These thresholds represent **minimum operational safeguards** against degenerate asymptotic calculations (e.g. KS test power collapse when $N < 30$). They do not guarantee statistical power for subtle subgroup hypotheses.

---

## 8. Population Comparability Boundaries

The pipeline formally partitions evaluation cohorts into two distinct populations:
- **Population A: General Adults (Age $\ge 20$):** Synthetic adults aged 20–44 cannot be compared to LASI Wave 1 because LASI's core sampling frame excluded adults $< 45$ (spouses $< 45$ represent $< 2\%$ and are not nationally representative). Evaluated as **`NOT_COMPARABLE`**.
- **Population B: Older Adults (Age $\ge 45$):** Synthetic patients truncated to age $\ge 45$ are directly comparable to LASI respondents.

Findings from older adults **cannot be extrapolated to younger adult cohorts** without independent external data sources (e.g., NFHS-5 or ICMR-INDIAB).

---

## 9. Report Semantics, Data Provenance, and Privacy Safeguards

1. **Distinction of Execution Modes:**
   - Test fixtures are explicitly marked `reference_source_type: SYNTHETIC_TEST_FIXTURE` and locked to `overall_gate_status: REFERENCE_DATA_PENDING`.
   - Authentic reference runs are marked `GENUINE_LASI_MICRODATA`.
2. **Pseudonymization Safeguards:**
   - Raw survey identifiers (`r1hhid`, `r1pn`) are replaced with truncated SHA-256 digests (`lasi_p_{sha256[:12]}`).
   - The documentation explicitly notes that surrogate hashing provides **pseudonymization**, not irreversible anonymization or differential privacy.
3. **Version Control Governance:**
   - Raw microdata and derived individual CSVs are ignored via `.gitignore`.
   - Manifests and summary reports expose only aggregated statistics and cryptographic file hashes.

---

## 10. Failure Mode Testing Verification Matrix

All 8 failure modes mandated by the pre-release audit were verified with automated tests in [`tests/test_lasi_pipeline.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_lasi_pipeline.py):

| Failure Mode Tested | Test Implementation Function | Verified Result |
| :--- | :--- | :---: |
| **1. Fixture Cannot Produce PASS Gate** | `test_failure_mode_fixture_cannot_pass_overall_gate` | **PASSED:** Overall gate is `REFERENCE_DATA_PENDING`. |
| **2. Small Synthetic Sample Cannot Pass Distribution** | `test_lasi_evaluator_sample_size_gating` | **PASSED:** Synthetic $N=11 < 30$ emits `INSUFFICIENT_SAMPLE_SIZE`. |
| **3. Low Effective Reference Sample Size Gated** | `test_failure_mode_low_effective_sample_size_gated` | **PASSED:** Reference $n_{\text{eff}} = 1.2 < 25.0$ emits `INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE`. |
| **4. Unsupported HbA1c Crosswalk Cannot Pass** | `test_failure_mode_unsupported_hba1c_cannot_pass` | **PASSED:** `enable_venous_hba1c=False` emits `UNVERIFIED`. |
| **5. Empty Strata Target Population Integrity** | `test_direct_standardization_empty_strata_handling` & `abort` | **PASSED:** Weight mass tracked; $<4$ strata aborts with `std=None`. |
| **6. Segregation of Incompatible Case Definitions** | `test_failure_mode_case_definitions_strictly_segregated` | **PASSED:** Measured BP and self-report maintained as separate variables. |
| **7. Missing Reference Data Cannot Pass** | `test_lasi_evaluator_empty_reference` | **PASSED:** Raises `ValueError`; cannot produce passing verdict. |
| **8. Required Metric Failure Prevents Overall PASS** | `test_failure_mode_metric_failure_prevents_overall_pass` | **PASSED:** Metric `FAIL` or `INSUFFICIENT` forces overall gate away from `PASS`. |

---

## 11. Comprehensive Audit Check Table

| Audit Check Domain | Evaluation Result | Primary Evidence / Source Document | Unresolved Limitation / Residual Risk |
| :--- | :---: | :--- | :--- |
| **Variable Mapping Semantics** | **VERIFIED** | *IIPS LASI Report 2020*, *Gateway Codebook 2021*. | Self-reported CKD (`r1kidneye`) has high false-negative rate in community surveys. |
| **Case Definition Separation** | **VERIFIED** | [`models.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py) (`LasiCleanedRecord`), `test_failure_mode_case_definitions_strictly_segregated`. | Self-report under-detects asymptomatic disease; comparison is descriptive. |
| **BP Protocol Averaging** | **VERIFIED** | *LASI Field Protocol Manual 2017*, [`ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py) (`_calculate_average_bp`). | Single-reading fallbacks introduce mild positive bias if `strict_protocol_bp=False`. |
| **BP Range Exclusions** | **VERIFIED** | SBP $[60, 280]$, DBP $[40, 160]\text{ mmHg}$ tracked in data quality reports. | Extreme physiological outliers ($<60$ or $>280$) excluded from reference denominator. |
| **HbA1c Assay Harmonization** | **VERIFIED** | Crimmins et al. (2014) US HRS; disabled by default in [`comparability.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/comparability.py). | Venous HPLC vs Capillary DBS cannot be directly compared without Indian calibration study. |
| **Unequal Weighting Adjustment** | **VERIFIED** | Kish (1965); [`metrics.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/metrics.py) (`effective_sample_size`, `survey_design_effect_weighting`). | Does not model PSU clustering or state strata Taylor-series linearization. |
| **Age-Sex Standardization** | **VERIFIED** | Census of India SRS 2021 (8 strata summing to 1.000); hand-calculated tests. | Standardizes age-sex only; does not adjust for geography, SES, or urbanicity. |
| **Sample Size Gating** | **VERIFIED** | $N_{\text{min, dist}} = 30$, $N_{\text{min, prev}} = 20$, $n_{\text{eff, min}} = 25.0$ in [`evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py). | Small synthetic cohorts ($N=100$) lack power to populate older-adult clinical subsamples. |
| **Data De-identification** | **VERIFIED** | SHA-256 surrogate prefix in [`ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py); `.gitignore` blocks raw CSVs. | Truncated hashing is pseudonymization, not differential privacy. |
| **Validation Gate Semantics** | **VERIFIED** | 8 distinct statuses in [`models.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py); fixture cannot pass overall gate. | Test fixtures cannot certify real-world validity. |

---

## 12. Code Defects Identified and Corrected During Audit

1. **Missing 75+ Age Stratum in Standardization:**
   - *Defect:* `CENSUS_SRS_OLDER_ADULT_WEIGHTS` previously omitted participants aged $\ge 75$ (6 strata), while `get_age_band_older_adult` generated `"75+"`.
   - *Correction:* Expanded to all 8 standard Census SRS strata ($45-54, 55-64, 65-74, 75+$ for Male and Female) summing to exactly 1.000.
2. **Uncalibrated US HRS HbA1c Conversion Active by Default:**
   - *Defect:* Converted capillary DBS to venous whole blood HPLC using an unvalidated US HRS regression equation.
   - *Correction:* Disabled by default (`enabled=False`); authentic DBS HbA1c preserved; direct comparisons gated as `UNVERIFIED`.
3. **Underpowered Fixture Comparisons Masked as Warnings:**
   - *Defect:* $N=1$ synthetic vs $N=49$ reference observations emitted generic `WARNING`.
   - *Correction:* Added strict sample-size gates ($N < 30$ continuous, $N < 20$ binary) emitting `INSUFFICIENT_SAMPLE_SIZE`.
4. **Missing DBP Evaluation in Blood Pressure Subsystem:**
   - *Defect:* `_evaluate_blood_pressure` in `evaluator.py` evaluated SBP but omitted DBP.
   - *Correction:* Added `lasi_bp_dbp_distribution` continuous evaluation, correctly reporting `INSUFFICIENT_SAMPLE_SIZE` when synthetic DBP observations are absent.
5. **Silent Single-Reading BP Fallbacks:**
   - *Defect:* Single blood pressure readings were substituted without record-level traceability.
   - *Correction:* Implemented `LasiCleanedRecord.bp_derivation_method` and added `strict_protocol_bp` toggle.

---

## 13. Test Results and Execution Command

```bash
$ .venv/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/shashi/synapse/synapse-phase2
plugins: Faker-40.43.0
collected 196 items

tests/test_clinical_modules.py ......                                    [  3%]
tests/test_data_integrity_temporal_consistency.py ...............        [ 10%]
tests/test_datagen.py ...                                                [ 12%]
tests/test_determinism.py ..........                                     [ 17%]
tests/test_dispatcher.py .                                               [ 17%]
tests/test_end_to_end_acceptance.py .                                    [ 18%]
tests/test_evaluation_framework.py ....................                  [ 28%]
tests/test_evaluation_mutations.py ......                                [ 31%]
tests/test_event_queue.py ...                                            [ 33%]
tests/test_full_simulation.py .                                          [ 33%]
tests/test_lab_rad_finance_rules.py ...                                  [ 35%]
tests/test_lasi_pipeline.py .........................                    [ 47%]
tests/test_longitudinal_export.py ..                                     [ 48%]
tests/test_longitudinal_trajectories.py ....                             [ 51%]
tests/test_orchestrator.py ..                                            [ 52%]
tests/test_person_time_and_censoring.py .......                          [ 55%]
tests/test_phase2_csv_export.py ...                                      [ 57%]
tests/test_population_profile.py .....                                   [ 59%]
tests/test_population_validator.py .....                                 [ 62%]
tests/test_pubmed_datagen_integration.py ........                        [ 66%]
tests/test_pubmed_treatment_architecture.py ........                     [ 70%]
tests/test_root_cause_corrections.py ..........                          [ 75%]
tests/test_rule_engine.py ....                                           [ 77%]
tests/test_solid_principles.py .....                                     [ 80%]
tests/test_stage6_clock_scheduler.py ...                                 [ 81%]
tests/test_stage6_domain_events.py ..                                    [ 82%]
tests/test_stage6_loop_failure_protection.py ..                          [ 83%]
tests/test_stage6_ordering_causation.py ..                               [ 84%]
tests/test_stage6_reproducibility.py .                                   [ 85%]
tests/test_stage6_small_simulation.py .                                  [ 85%]
tests/test_stage7_cross_department.py .                                  [ 86%]
tests/test_stage7_patient_journeys.py .                                  [ 86%]
tests/test_stage7_scale.py .                                             [ 87%]
tests/test_stage7_workflows.py ..                                        [ 88%]
tests/test_stage9_billing.py .                                           [ 88%]
tests/test_stage9_diagnostics.py .                                       [ 89%]
tests/test_stage9_discharge.py .                                         [ 89%]
tests/test_stage9_integrity.py .                                         [ 90%]
tests/test_stage9_persistence.py ..                                      [ 91%]
tests/test_stage9_prescription.py .                                      [ 91%]
tests/test_state_machines.py .......                                     [ 95%]
tests/test_state_manager.py ....                                         [ 97%]
tests/test_validation_gate.py .....                                      [100%]

============================= 196 passed in 7.71s ==============================
```

---

## 14. Final Gate Verdict

### **Verdict:** **`CONDITIONALLY_READY`**

### Verdict Specifications:
1. **Ready for Microdata Ingestion:** The data ingestion, variable mapping, range validation, de-identification, and data quality subsystems are mathematically, epidemiologically, and computationally ready to receive genuine, authorized LASI Wave 1 reference microdata.
2. **Prerequisites for External Validation Certification:**
   - Formal approval and execution of the IIPS / Gateway to Global Aging Data Research Data Use Agreement (DUA).
   - Ingestion of genuine reference microdata (overall gate status transitions from `REFERENCE_DATA_PENDING` to analytical evaluation).
   - Execution against a sufficiently powered synthetic cohort ($N \ge 500$ older adults) to satisfy the $N \ge 30$ continuous and $N \ge 20$ prevalence gates.
   - Separate verification of local Indian HbA1c capillary DBS crosswalk calibration before enabling laboratory glycemic comparisons.
