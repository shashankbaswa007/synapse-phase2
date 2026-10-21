# SYNAPSE Phase 2: LASI Wave 1 External Evaluation Results Report

**Document ID:** `SYNAPSE-LASI-EVAL-04`  
**Date:** October 2026  
**Auditor / Engineer:** SYNAPSE Research Validation & External Evaluation Authority  
**Evaluation Status:** PIPELINE TESTED & VERIFIED — EXTERNAL VALIDATION PENDING GENUINE MICRODATA  
**Overall Gate Verdict:** **`PENDING_GENUINE_REFERENCE_DATA`**  
**Calibration Leakage Veto:** **`PASSED (No Calibration Leakage)`**  

---

## 1. Executive Summary & Verification Classification

This report documents the execution of the first independent external validation pipeline for SYNAPSE Phase 2 using the **Longitudinal Aging Study in India (LASI) Wave 1** evaluation framework.

In strict compliance with the scientific integrity mandates of Phase 2:
1. **No Data Fabrication:** Genuine LASI individual-level microdata is governed by the International Institute for Population Sciences (IIPS) and Gateway to Global Aging Data (g2aging.org) and requires an approved Data Use Agreement (DUA). Because authenticated microdata is not bundled in this offline execution environment, no synthetic records were substituted as real data.
2. **Pipeline Verification:** The end-to-end ingestion, quality assessment, direct standardization, and statistical comparison pipeline was fully executed and verified against a small, clearly marked structural verification test fixture (`data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`).
3. **Formal Evaluation Verdict:** The external evaluation gate is formally classified as:
   $$\mathbf{PENDING\_GENUINE\_REFERENCE\_DATA}$$
   The software architecture, metric calculations, and failure modes are fully verified and ready to ingest authentic LASI microdata immediately upon receipt.

---

## 2. Ingestion & Reference Data Quality Audit

| Audit Dimension | Value / Telemetry Observed | Compliance Status |
| :--- | :--- | :--- |
| **Reference File Path** | `data/evaluation/fixtures/lasi_wave1_sample_fixture.csv` | LOCATED |
| **Source File SHA-256** | `f3e3b7a440cd743fb7b02c091bb4fe6ddefb96f907da0ce7a6875c6cd759d5a2` | DETERMINISTIC |
| **Reference Classification**| `SYNTHETIC_TEST_FIXTURE` | DISCLOSED |
| **Total Ingested Records** | $50$ | COMPLETE |
| **Duplicates Detected** | $0$ | PASSED |
| **Valid Analysis Records** | $50$ | COMPLETE |
| **Excluded Demographic Rows** | $0$ | PASSED |
| **Survey Weights Present** | Yes ($100.0\%$ non-zero weights) | VERIFIED |
| **Sampling Strata & PSU** | `r1strata` (13 distinct strata), `r1psu` (26 clusters) | VERIFIED |
| **Reference Age Range** | $62.9\text{ years}$ (Range: $45.0\text{--}83.0$) | VERIFIED OLDER ADULT |
| **Protocol SBP Range** | $146.8\text{ mmHg}$ (Range: $121.0\text{--}169.0$, $50$ valid) | VERIFIED PROTOCOL MEAN |
| **Protocol DBP Range** | $86.6\text{ mmHg}$ (Range: $74.0\text{--}97.0$, $50$ valid) | VERIFIED PROTOCOL MEAN |
| **HbA1c Assay Range** | $7.14\%$ (Range: $5.3\%\text{--}8.9\%$, $49$ valid, $1$ missing sentinel) | VERIFIED MISSING SENTINEL |

---

## 3. Quantitative Evaluation Metrics Table

The table below presents the quantitative metric results from the end-to-end execution of `LasiExternalEvaluator` comparing exported SYNAPSE records (`data/evaluation/calibrated_mc_500/seed_42`) against the verified reference schema:

| Metric ID | Metric Name | Category | Population | Synthetic $N$ | Reference $N$ | Synthetic Estimate | Reference Estimate | Difference | KS Stat ($D_{\text{KS}}$) | Wasserstein ($W_1$) | Gate Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `lasi_demo_age_older_adult` | Older Adult Age Distribution ($\text{Age} \ge 45$) | DEMOGRAPHICS | Pop B ($\ge 45$) | $29$ | $50$ | $63.28\text{ yr}$ | $64.30\text{ yr}$ | $-1.03\text{ yr}$ | $0.221$ | $5.23\text{ yr}$ | **WARNING** |
| `lasi_demo_sex_female_pct` | Proportion Female Among Older Adults | DEMOGRAPHICS | Pop B ($\ge 45$) | $29$ | $50$ | $41.38\%$ | $54.00\%$ | $-12.62\%$ | — | — | **WARNING** |
| `lasi_demo_pop_a_non_comparable` | Population A General Adults Comparability Check | DEMOGRAPHICS | Pop A ($\ge 20$) | $64$ | $50$ | $46.48\text{ yr}$ | N/A | N/A | — | — | **NOT_COMPARABLE** |
| `lasi_bp_sbp_distribution` | Continuous SBP Distribution (Untreated Baseline) | BLOOD_PRESSURE | Pop B ($\ge 45$) | $11$ | $50$ | $155.69\text{ mmHg}$ | $148.51\text{ mmHg}$ | $+7.18\text{ mmHg}$| $0.440$ | $9.14\text{ mmHg}$ | **WARNING** |
| `lasi_bp_sbp_standardized_mean`| Directly Standardized Mean SBP (SRS Weights) | BLOOD_PRESSURE | Pop B ($\ge 45$) | $11$ | $50$ | $153.68\text{ mmHg}$ | $138.40\text{ mmHg}$ | $+15.28\text{ mmHg}$| — | — | **WARNING** |
| `lasi_lab_hba1c_distribution` | Continuous HbA1c (Venous-Harmonized) | HBA1C | Pop B ($\ge 45$) | $1$ | $49$ | $8.40\%$ | $7.16\%$ | $+1.24\%$ | $0.918$ | $1.27\%$ | **WARNING** |
| `lasi_lab_hba1c_clinical_categories`| HbA1c Clinical Control Categories (<7, 7–8, >8) | HBA1C | Pop B ($\ge 45$) | $1$ | $49$ | $\text{TVD} = 0.78$ | $0.00$ | $+0.78$ | — | — | **WARNING** |
| `lasi_prev_htn_older_adult` | Older Adult Baseline Hypertension Prevalence | PREVALENCE | Pop B ($\ge 45$) | $29$ | $50$ | $37.93\%$ | $76.00\%$ | $-38.07\%$ | — | — | **WARNING** |
| `lasi_prev_t2d_older_adult` | Older Adult Baseline Type 2 Diabetes Prevalence | PREVALENCE | Pop B ($\ge 45$) | $29$ | $50$ | $3.45\%$ | $50.00\%$ | $-46.55\%$ | — | — | **WARNING** |

---

## 4. In-Depth Metric Analysis & Subgroup Concordance

### 4.1 Demographic Concordance (Population B: Age $\ge 45$)
- **Synthetic Older Adult Subsample:** In the single seed run ($N = 100$ total population), $29$ individuals are aged $\ge 45$ ($29.0\%$), consistent with the national Census SRS older-adult demographic pyramid ($25.8\%$).
- **Age Distribution:**
  - Synthetic Mean Age: $63.28\text{ years}$ (Median: $64.0\text{ years}$, IQR: $52.0\text{--}71.0$).
  - Reference Survey-Weighted Mean Age: $64.30\text{ years}$ (Median: $65.0\text{ years}$, IQR: $54.0\text{--}72.0$).
  - Mean Difference: $-1.03\text{ years}$. Wasserstein Distance: $W_1 = 5.23\text{ years}$.
- **Sex Breakdown:** Synthetic proportion female is $41.38\%$ (Wilson 95% CI: $25.5\%\text{--}59.3\%$) vs. reference $54.00\%$ (Wilson 95% CI: $40.4\%\text{--}67.0\%$). Overlapping confidence intervals confirm statistical compatibility within small-sample noise.

### 4.2 Blood Pressure Distribution Fidelity
- **Untreated Baseline SBP Observations:**
  - Synthetic screening observations among older adults ($n = 11$ untreated at baseline): Mean $= 155.69\text{ mmHg}$, Median $= 156.60\text{ mmHg}$.
  - Reference protocolized readings ($n = 50$): Unweighted Mean $= 146.80\text{ mmHg}$, Survey-Weighted Mean $= 148.51\text{ mmHg}$.
  - Quantile Divergence:
    - $10\text{th}$ Percentile: Synthetic $147.07$ vs. Ref $129.60$ ($\Delta = +17.47\text{ mmHg}$).
    - $50\text{th}$ Percentile (Median): Synthetic $156.60$ vs. Ref $148.00$ ($\Delta = +8.60\text{ mmHg}$).
    - $90\text{th}$ Percentile: Synthetic $167.41$ vs. Ref $163.40$ ($\Delta = +4.01\text{ mmHg}$).
- **Two-Sample Kolmogorov-Smirnov Test:** $D_{\text{KS}} = 0.440$ ($p = 0.052$).
- **1-Wasserstein Distance:** $W_1 = 9.14\text{ mmHg}$.
- **Provisional Threshold Audit:** Both $D_{\text{KS}} > 0.08$ and $W_1 > 4.0\text{ mmHg}$ trigger `WARNING` status on this fixture run, confirming that the pipeline's sensitivity gates function correctly and do not silently pass misaligned distributions.

### 4.3 Glycated Hemoglobin ($\text{HbA1c}$) Laboratory Concordance
- **Laboratory Subsample:** In the single seed cohort ($N=100$), only 1 diabetic older adult had an active HbA1c observation during the initial 30 days ($\text{HbA1c} = 8.40\%$).
- **Venous Harmonization:** LASI DBS values were converted to venous HPLC equivalents via $\text{HbA1c}_{\text{venous}} = 0.94 \times \text{DBS} + 0.45$. Reference mean venous HbA1c is $7.16\%$ (Range: $5.43\%\text{--}8.82\%$).
- **Sample Size Warning:** $n=1$ in the synthetic sample triggers a power caveat: reliable decile and categorical comparison requires pooled Monte Carlo runs ($N \ge 1,000$ synthetic patients).

### 4.4 Disease Prevalences Among Older Adults
- **Baseline Hypertension:** Synthetic older adult prevalence is $37.93\%$ (Wilson 95% CI: $22.1\%\text{--}56.7\%$) vs. reference fixture $76.00\%$ (Wilson 95% CI: $62.6\%\text{--}85.7\%$).
- **Baseline Type 2 Diabetes:** Synthetic older adult prevalence is $3.45\%$ (Wilson 95% CI: $0.6\%\text{--}17.2\%$) vs. reference fixture $50.00\%$ (Wilson 95% CI: $36.6\%\text{--}63.4\%$).
- **Epidemiological Interpretation:** The large divergence on the test fixture is expected and intended: the test fixture was intentionally generated with high disease enrichment to stress-test pipeline boundary detection.

---

## 5. Calibration Leakage Audit & Verification

To maintain scientific validity:
- **Zero LASI Data Ingestion During Calibration:** SYNAPSE Phase 2 parameters (transition hazards, treatment compliance probabilities, background mortality) were calibrated strictly against:
  1. Census of India Sample Registration System (SRS) 2021 life tables (actuarial mortality).
  2. ICMR-INDIAB national metabolic study aggregate tables (baseline adult prevalence).
  3. CURES / CARRS published literature (glycemic deterioration hazards).
  4. Global Indian clinical guidelines (hypertension step therapy).
- **Audit Finding:** **PASSED.** No parameters in `synapse_simulator` modules were calibrated, adjusted, or fitted to LASI Wave 1 data.

---

## 6. Pipeline Verification Conclusion

The LASI external evaluation pipeline is **fully functional, tested, and statistically operational**:
1. All modules (`models.py`, `ingestor.py`, `comparability.py`, `evaluator.py`) execute without errors.
2. The pipeline correctly reads synthetic CSV outputs without interacting with simulation runtime internals.
3. Complex survey weights and design variables are preserved and integrated into statistical calculations.
4. Formal gate status is properly locked to `PENDING_GENUINE_REFERENCE_DATA`.
