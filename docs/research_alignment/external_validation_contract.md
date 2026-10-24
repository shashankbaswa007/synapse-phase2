# External Validation Contract: LASI Wave 1 Benchmark for SYNAPSE Phase 2

**Document Version:** 1.0.0  
**Status:** BINDING GOVERNANCE SPECIFICATION  
**Primary Target:** Longitudinal Ageing Study in India (LASI) Wave 1 External Comparison  
**Current Gate Status:** `REFERENCE_DATA_PENDING` (Preserved strictly)  
**Date of Execution:** October 2026  

---

## 1. Executive Summary & Purpose

This document establishes the binding formal contract for validating the SYNAPSE Phase 2 synthetic healthcare simulation against authorized Longitudinal Ageing Study in India (LASI) Wave 1 reference data.

It specifies:
- The multidimensional validation objectives that must be independently satisfied.
- The authorization, provenance, and data security requirements for genuine reference microdata.
- The precise variable mapping and semantic comparability boundaries.
- The survey-design-aware statistical methods required for unbiased inference.
- The absolute separation between empirical parameter calibration and independent external validation.
- Predeclared acceptance criteria and the governance protocol governing the `REFERENCE_DATA_PENDING` gate.

---

## 2. Validation Objectives (Multidimensional Separation)

To prevent conflation of distinct validation dimensions, validation is partitioned into six non-substitutable axes:

```
                                  VALIDATION OBJECTIVES
                                             │
      ┌──────────────┬──────────────┬────────┼──────────────┬──────────────┐
      ▼              ▼              ▼        ▼              ▼              ▼
  [Software]   [Statistical]   [Clinical] [Population]  [Longitudinal] [Downstream]
 Correctness      Fidelity       Fidelity  Represent.      Fidelity      Utility
```

1. **Software Correctness:**
   - Deterministic execution across seeds and operating environments.
   - Elimination of process hash-randomization sensitivity (`PYTHONHASHSEED`).
   - Structural schema integrity and relational referential consistency.
   - *Rule:* Software test suite pass (e.g., 227 passing tests) verifies software correctness ONLY; it does NOT constitute epidemiological validity.
2. **Statistical Distributional Fidelity:**
   - Equivalence of univariate and joint continuous distributions for biological biomarkers (SBP, DBP, pulse pressure, HbA1c).
   - Evaluated via two-sample Kolmogorov-Smirnov statistics, 1-D Wasserstein distances, and quantile concordance ($Q_{0.10}, Q_{0.25}, Q_{0.50}, Q_{0.75}, Q_{0.90}$).
3. **Clinical & Physiological Fidelity:**
   - Adherence to hemodynamics and biological invariants (e.g., $SBP > DBP$, $PP \ge 20$ mmHg, non-negative survival time).
   - Clinical consistency between diagnostic thresholds, active pharmacotherapy, and measured blood pressure control rates.
4. **Population Representativeness:**
   - Unbiased sampling coverage across demographic strata (age, sex, urban/rural residence, state-level geography).
   - Separation of general community population prevalence from outpatient hospital attendance (Berkson's bias).
5. **Longitudinal Fidelity:**
   - Within-individual disease progression, treatment response dynamics, and multi-year trajectory realism.
   - *Constraint:* Cross-sectional reference data (such as LASI Wave 1) CANNOT validate longitudinal trajectories; multi-wave data (e.g. LASI Wave 2) are mandatory for this dimension.
6. **Downstream Utility:**
   - Performance preservation when synthetic data are used for health economics, policy simulation, and machine learning model training without inductive bias leakage.

---

## 3. Reference Data Authorization, Provenance, and Blocker Status

### 3.1 Provenance and Authorization Requirements
Genuine LASI Wave 1 reference data must satisfy strict provenance criteria:
1. **Official Custodian:** International Institute for Population Sciences (IIPS), Mumbai, in collaboration with Harvard T.H. Chan School of Public Health and the University of Southern California (USC).
2. **Access License:** Formally authorized Data Use Agreement (DUA) or authorized research data distribution under IIPS/MoHFW data governance protocols.
3. **Integrity Manifest:** SHA-256 cryptographic verification of raw data files upon ingestion.
4. **De-identification & Ethics:** Full adherence to participant confidentiality protocols.

### 3.2 Current Blocker Status: Lack of Genuine Reference Microdata
- **Status:** **CRITICAL ACTIVE BLOCKER**.
- **Current State:** The repository currently contains only an uncalibrated synthetic test fixture (`data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`, $N = 29$).
- **Binding Rule:** **Synthetic structural fixtures must NEVER be used as external validation data.** Running against fixture data produces a gate verdict of `REFERENCE_DATA_PENDING`. Under no circumstances may this gate advance to `PASSED` using synthetic fixtures.

---

## 4. Variable Comparability Matrix

For every intended comparison between SYNAPSE Phase 2 and LASI Wave 1, the official reference variable and its synthetic mapping are specified below:

| Dimension | LASI Wave 1 Reference Variable | Reference Definition & Protocol | Corresponding SYNAPSE Variable | Eligibility & Protocol | Units & Valid Ranges | Known Comparability Limitations |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Demographics: Age** | `age` / `w1_age` | Chronological age in completed years at survey interview. | `patients.csv:age` | Age $\ge 45.0$ at baseline. | Completed years: $[45, 110]$ | Age rounding in surveys vs continuous exact simulation age. |
| **Demographics: Sex** | `gender` / `ragender` | Respondent biological sex (1 = Male, 2 = Female). | `patients.csv:gender` | All respondents. | `Male`, `Female` | Synthetic profile currently binary; does not model third gender. |
| **Systolic BP (Community)** | `sbp_mean` / `w1_sbp_mean` | Arithmetic mean of 2nd and 3rd Omron HEM-7121 digital monitor readings taken in sitting position. | `community_assessments.csv:sbp` | Living respondents at survey reference date (`2024-06-29`). | mmHg: $[70.0, 260.0]$ | SYNAPSE generates single survey reading; LASI uses tri-measurement protocol (mean of 2nd/3rd). |
| **Diastolic BP (Community)** | `dbp_mean` / `w1_dbp_mean` | Arithmetic mean of 2nd and 3rd Omron digital monitor readings taken in sitting position. | `community_assessments.csv:dbp` | Living respondents at survey reference date (`2024-06-29`). | mmHg: $[40.0, 160.0]$ | White-coat and observer variation in survey vs parametric uniform synthetic generation. |
| **Pulse Pressure** | `pp` ($SBP - DBP$) | Calculated pulse pressure: $\text{sbp\_mean} - \text{dbp\_mean}$. | `community_assessments.csv:pulse_pressure` | Living respondents with valid SBP and DBP. | mmHg: $[20.0, 110.0]$ | Invariant safeguard enforced in simulation ($PP \ge 20$). |
| **Diagnosed HTN** | `diagnosed_hypertension` / `w1_bp_diag` | Self-report: "Has any doctor or healthcare provider ever told you that you have high blood pressure or hypertension?" | `conditions.csv:condition_code == "I10"` | All synthetic older adults ($N = 575$). | Boolean: `True`, `False` | Self-report in LASI subject to recall bias; EHR diagnosis in SYNAPSE reflects outpatient consultation coding. |
| **Antihypertensive Rx** | `taking_bp_medication` / `w1_bp_meds` | Self-report: "Are you currently taking any medication for high blood pressure?" | `medications.csv:drug_name` (linked via `encounter_id`) | Active prescription at survey date (`2024-06-29`). | Binary: 1 / 0 | Compliance/adherence in survey vs active prescription issuance in simulation. |
| **Community HTN Prevalence** | Composite Metric | $\text{sbp\_mean} \ge 140 \lor \text{dbp\_mean} \ge 90 \lor \text{taking\_bp\_medication} = 1$. | Composite Estimand C2 (`community_assessments.csv` + active Rx) | Living surveyed older adults ($N = 561$). | Proportion: $[0.0, 1.0]$ | Excludes individuals deceased prior to survey date. |
| **Clinical Index BP** | None directly comparable | LASI does not sample outpatient clinical encounters. | `observations.csv:value` (Earliest SBP/DBP) | Facility attenders with measured BP ($N = 235$). | mmHg | Severe Berkson's selection bias; cannot be validated against LASI community survey. |

---

## 5. Survey-Design-Aware Statistical Methods

### 5.1 Mandatory Accounting for Complex Survey Design
LASI Wave 1 utilizes a multi-stage stratified cluster sampling design:
1. **Primary Sampling Units (PSUs):** Rural villages and urban Census Enumeration Blocks (CEBs).
2. **Stratification:** Geopolitical states/UTs, subdivided into urban and rural substrata.
3. **Sampling Weights:** Individual sampling weights normalized to account for unequal selection probabilities and household non-response.

### 5.2 Methodological Boundary: Kish Effective Sample Size
> [!IMPORTANT]
> **Kish's effective sample size is an unequal-weighting heuristic ($\text{DEFF}_w$), NOT a substitute for complex-survey variance estimation.**

- **Unequal Weighting Effect:**
  $$\text{DEFF}_w = \frac{n}{n_{\text{eff}}} = 1 + \text{CV}(w)^2$$
- **Clustering Variance Inflation:**
  $$\text{DEFF}_c = 1 + (\bar{m} - 1)\rho$$
  where $\bar{m}$ is average cluster size and $\rho$ is the intracluster correlation coefficient.
- **Contractual Mandate:** Reference variance estimation must employ **Taylor Series Linearization** or **Balanced Repeated Replication (BRR)** incorporating PSU and strata identifiers:
  $$\widehat{\text{Var}}(\hat{\theta}) = \sum_{h=1}^H \frac{n_h}{n_h - 1} \sum_{i=1}^{n_h} (z_{hi} - \bar{z}_h)^2$$
  Kish effective sample size alone is insufficient for formal hypothesis testing.

---

## 6. Calibration versus Independent Validation (Anti-Leakage Protocol)

To maintain scientific integrity, reference data must be partitioned strictly into calibration and validation domains:

```
                          GENUINE REFERENCE MICRODATA
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
       [Calibration Set (50%)]                       [Validation Set (50%)]
       (Parameter Estimation)                        (Independent Gating)
                │                                             │
                ▼                                             ▼
  Biological Stiffening Tuning                   Zero Parameter Modification
  Joint Quantile Alignment                       Final Acceptance Testing
```

1. **Anti-Leakage Invariant:** Parameters tuned or fitted against a reference dataset CANNOT be evaluated against the same observations to claim independent validity.
2. **Holdout Partitioning:** If only a single cross-sectional wave (LASI Wave 1) is available, a prespecified **50/50 cluster-level split** (split by PSU, not individual patients) must be executed before analysis:
   - *Split A (Calibration Sample):* Used to estimate biological age-stiffening parameters and baseline prevalences.
   - *Split B (Holdout Evaluation Sample):* Held strictly in escrow until calibration is frozen.
3. **Holdout Limitations:** Holdout cross-validation on a single cross-sectional survey validates in-distribution generalization, but CANNOT establish longitudinal fidelity or temporal transportability.

---

## 7. Predeclared Acceptance Criteria

Validation criteria are predeclared below. Where empirical thresholds cannot be scientifically defended prior to data inspection, they are designated `TO_BE_PREDECLARED_BEFORE_REFERENCE_DATA_ANALYSIS`:

| Dimension / Metric | Estimand | Test Statistic | Preliminary Acceptance Threshold |
| :--- | :--- | :--- | :---: |
| **Demographics: Age Distribution** | Older Adults (45+) | 2-sample Kolmogorov-Smirnov ($D$) | $D \le 0.08$ |
| **Demographics: Sex Ratio** | Female Proportion | Absolute Difference in % | $|\Delta_{\text{female}}| \le 3.0\%$ |
| **Community SBP Distribution** | Estimand A (Survey) | 2-sample KS ($D$) & 1-D Wasserstein ($W_1$) | $D \le \text{TO\_BE\_PREDECLARED}$; $W_1 \le 5.0\text{ mmHg}$ |
| **Community DBP Distribution** | Estimand A (Survey) | 2-sample KS ($D$) & 1-D Wasserstein ($W_1$) | $D \le \text{TO\_BE\_PREDECLARED}$; $W_1 \le 3.5\text{ mmHg}$ |
| **Community HTN Prevalence** | Estimand C2 | Absolute Difference in Survey-Weighted % | $|\hat{p}_{\text{syn}} - \hat{p}_{\text{ref}}| \le 5.0\%$ |
| **EHR Diagnosis Prevalence** | Estimand C1 | Comparison against Self-Reported Diagnosis | Directional: $\hat{p}_{\text{EHR}} \le \hat{p}_{\text{comm}}$ (Awareness gap) |
| **Treated BP Control Rate** | Subgroup Control | Treated % with SBP $<140$ & DBP $<90$ | $|\Delta_{\text{control}}| \le \text{TO\_BE\_PREDECLARED}$ |
| **Physiological Invariants** | Hemodynamics | $SBP \le DBP$ or $PP < 20\text{ mmHg}$ | **Strictly 0 violations (0.0%)** |
| **Longitudinal Trajectory** | Estimand D2 | Multi-year Delta SBP | **STRICTLY UNVERIFIED** (Requires Wave 2) |

---

## 8. Governance Protocol for External Validation Gate

The gate status `REFERENCE_DATA_PENDING` is protected by non-negotiable governance constraints:

```
[REFERENCE_DATA_PENDING] ────(Authorized Microdata Ingested)────> [CALIBRATION_FROZEN]
                                                                        │
                                                       (Independent Validation Pass)
                                                                        │
                                                                        ▼
                                                                     [PASSED]
```

1. **Conditions Under Which Gate MUST NOT Advance:**
   - The gate MUST NOT advance solely because unit or integration tests pass.
   - The gate MUST NOT advance solely because synthetic distributions appear visually plausible.
   - The gate MUST NOT advance against synthetic fixtures or self-generated test files.
   - The gate MUST NOT advance if parameters were calibrated on the same sample used for evaluation.
2. **Mandatory Conditions for Gate Advancement to `PASSED`:**
   - Genuine LASI Wave 1 microdata ingested under authorized DUA with SHA-256 manifest.
   - Complex survey design (weights, strata, PSUs) formally accounted for in standard errors.
   - Predeclared acceptance criteria satisfied on an independent, untouched holdout partition.
   - Comprehensive external validation report signed and archived in `docs/research_alignment/`.
