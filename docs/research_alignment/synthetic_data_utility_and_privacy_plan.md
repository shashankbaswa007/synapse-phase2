# SYNAPSE Phase 2: Synthetic Data Utility and Privacy Risk Assessment Plan

**Document ID:** `SYNAPSE-UTIL-PRIV-05`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Readiness Assessment Authority  
**Status:** COMPLETE & SEALED  

---

## 1. Executive Summary & Governance Mandate

A common error in synthetic healthcare data generation is assuming that synthetic data is automatically private because no real individual's record was directly copied. Generative models and discrete-event simulators can inadvertently memorize rare patient combinations, leak training/calibration priors, or reproduce unique outlier profiles that enable re-identification.

Simultaneously, clinical fidelity (matching marginal distributions) does not guarantee **downstream analytical utility** (the preservation of multivariable interactions, predictive relationships, and epidemiological associations).

This governance plan establishes independent, formal frameworks for evaluating:
1. **Downstream Analytical Utility:** Whether synthetic data can replace real data for machine learning, epidemiological risk modeling, and clinical trials without degrading performance.
2. **Subgroup and Structural Integrity:** Whether multivariable correlations and minority clinical subpopulations are preserved.
3. **Privacy and Disclosure Risks:** Empirical testing for membership inference, attribute disclosure, nearest-neighbor memorization, and identity leakage.

---

## 2. Downstream Analytical Utility Assessment

Analytical utility evaluates whether statistical models and predictive algorithms trained on synthetic data yield identical conclusions and performance when deployed on real-world clinical populations.

```
Analytical Utility Evaluation Architecture:
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TRAIN ON SYNTHETIC, TEST ON REAL (TSTR) BENCHMARK                                      │
│                                                                                        │
│        Synthetic Data ───► Train Model M_syn ───┐                                      │
│                                                 ▼                                      │
│                                           Evaluate on ──► Performance Metric Diff:     │
│                                           Real Test Set   |AUROC_syn - AUROC_real| < δ │
│                                                 ▲                                      │
│        Real Train Data ──► Train Model M_real ──┘                                      │
│        (TRTR Benchmark)                                                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 The TSTR vs. TRTR Machine Learning Paradigm
To evaluate whether SYNAPSE Phase 2 data can train predictive clinical models:
- **Baseline Model ($\text{TRTR}$):** Train a gradient-boosted decision tree (LightGBM/XGBoost) and a multivariable logistic regression model on $70\%$ of an external empirical cohort (e.g. CARRS or LASI) and evaluate on the remaining $30\%$ real holdout.
- **Synthetic-Trained Model ($\text{TSTR}$):** Train the identical model architecture on SYNAPSE synthetic patient records and evaluate on the same $30\%$ real holdout.
- **Target Predictive Tasks:**
  1. *2-Year Chronic Complication Prediction:* Predicting incident CKD or nephropathy from baseline age, sex, SBP, baseline HbA1c, and medication status.
  2. *Treatment Intensification Prediction:* Predicting progression to dual therapy from follow-up blood pressure trajectories.
- **Utility Acceptance Thresholds:**
  $$\Delta_{\text{AUROC}} = |\text{AUROC}_{\text{TSTR}} - \text{AUROC}_{\text{TRTR}}| \le 0.05$$
  $$\Delta_{\text{AUPRC}} = |\text{AUPRC}_{\text{TSTR}} - \text{AUPRC}_{\text{TRTR}}| \le 0.08$$

### 2.2 Preservation of Multivariable Regression Associations
A critical scientific failure of crude synthetic data is the disruption of multivariable regression coefficients (e.g. an odds ratio reversing direction).

We evaluate multivariable logistic regression coefficients:
$$\text{logit}(P(\text{Complication})) = \beta_0 + \beta_{\text{age}} \cdot \text{Age} + \beta_{\text{male}} \cdot \text{Male} + \beta_{\text{sbp}} \cdot \text{SBP} + \beta_{\text{t2d}} \cdot \text{T2D}$$
- **Evaluation Estimand:** Mean Absolute Relative Parameter Error (MARPE):
  $$\text{MARPE} = \frac{1}{K} \sum_{k=1}^K \left| \frac{\hat{\beta}_k^{\text{syn}} - \hat{\beta}_k^{\text{real}}}{\hat{\beta}_k^{\text{real}}} \right|$$
- **Acceptance Criterion:** $\text{MARPE} \le 0.20$ ($20\%$ maximum average distortion across regression weights). All odds ratios must preserve identical directional sign ($\text{sign}(\beta_k^{\text{syn}}) = \text{sign}(\beta_k^{\text{real}})$).

### 2.3 Correlation and Covariance Matrix Fidelity
- **Metric:** Difference between synthetic correlation matrix $\mathbf{R}_{\text{syn}}$ and real correlation matrix $\mathbf{R}_{\text{real}}$ across continuous variables (Age, SBP, DBP, HbA1c, Inter-visit days):
  - Frobenius Norm of Difference:
    $$\|\mathbf{R}_{\text{syn}} - \mathbf{R}_{\text{real}}\|_F = \sqrt{\sum_{i} \sum_{j} (r_{ij}^{\text{syn}} - r_{ij}^{\text{real}})^2}$$
  - **Acceptance Criterion:** $\|\mathbf{R}_{\text{syn}} - \mathbf{R}_{\text{real}}\|_F \le 0.35$.

---

## 3. Subgroup Structure & Clinical Intersectionality

Synthetic generators often model single-variable marginals correctly while distorting small or complex intersectional subpopulations.

### 3.1 Intersectional Subgroup Preservations
The evaluation assesses representation across 16 intersectional clinical strata:
$$\text{Strata} = \text{AgeGroup}(20\text{--}44, 45\text{--}64, 65+) \times \text{Sex}(\text{M}, \text{F}) \times \text{Hypertension}(0, 1) \times \text{Diabetes}(0, 1)$$
- **Total Variation Distance (TVD) on Intersectional Strata:**
  $$\text{TVD}_{\text{subgroup}} = \frac{1}{2} \sum_{k=1}^{16} |P_{\text{syn}}(\text{stratum}_k) - P_{\text{real}}(\text{stratum}_k)|$$
- **Acceptance Criterion:** $\text{TVD}_{\text{subgroup}} \le 0.08$.

### 3.2 Minority Clinical Subpopulations Protection
- Synthetic generation must not collapse sparse clinical subgroups (e.g., young diabetics aged $< 30$, or non-hypertensive diabetic nephropathy).
- Any subgroup comprising $\ge 0.5\%$ of the empirical population must be present in the synthetic population with an observed prevalence within $50\%\text{--}200\%$ of its expected relative frequency.

---

## 4. Privacy and Empirical Disclosure Risk Assessment

> [!WARNING]
> Synthetic data is **not** inherently anonymous. High-dimensional longitudinal datasets containing repeated encounter dates, specific drug combinations, and exact physiological measurements can uniquely fingerprint individuals.

```
Privacy Risk Assessment Framework:
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PRIVACY ATTACK VECTORS AUDITED                                                         │
│                                                                                        │
│ 1. Membership Inference Attack (MIA)                                                   │
│    - Determines if a specific real patient was in the calibration sample.             │
│    - Metric: Distance to Closest Record (DCR) & Nearest Neighbor Distance Ratio (NNDR)│
│                                                                                        │
│ 2. Attribute Disclosure Inference                                                      │
│    - Determines if a sensitive disease/medication can be predicted from quasi-IDs.     │
│    - Metric: Adversarial Attribute Inference Advantage (Adv_attr <= 0.05)             │
│                                                                                        │
│ 3. Exact Duplicate & Near-Duplicate Memorization                                       │
│    - Verifies zero identical copies of calibration profiles.                          │
│    - Metric: Hard 0 exact match constraint across all 16 CSV tables.                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Distance to Closest Record (DCR) and Nearest-Neighbor Distance Ratio (NNDR)
To prove that SYNAPSE does not memorize individual profiles from calibration reference studies:
1. Normalize all quasi-identifiers (Age, Sex, Baseline SBP, Baseline HbA1c, Encounter Count) to standard normal space $[0, 1]$.
2. For each synthetic patient $s_i$, compute the Euclidean distance to the closest record in the real reference dataset $r_j$:
   $$d_{\min}(s_i, \mathcal{D}_{\text{real}}) = \min_{r_j \in \mathcal{D}_{\text{real}}} \|s_i - r_j\|_2$$
3. Compute the **Nearest Neighbor Distance Ratio (NNDR)**:
   $$\text{NNDR}(s_i) = \frac{d_{\text{1stNN}}(s_i, \mathcal{D}_{\text{real}})}{d_{\text{2ndNN}}(s_i, \mathcal{D}_{\text{real}})}$$
- **Privacy Standard:**
  - If $\text{NNDR} \to 0$, the synthetic record is an exact or near-identical copy of an individual real patient (memorization failure).
  - The $5\text{th}$ percentile of the NNDR distribution across all synthetic patients must be **$\ge 0.40$**, proving that synthetic points reside in continuous probability density space rather than clustering tightly on real training points.

### 4.2 Adversarial Attribute Disclosure Testing
- **Threat Model:** An adversary possesses partial external knowledge of an individual: age, sex, and the dates of two outpatient clinic visits (quasi-identifiers). The adversary attempts to infer whether the patient has chronic kidney disease (`I12.9`) or is taking a specific step-up drug (Telmisartan).
- **Metric:** Adversarial Prediction Advantage:
  $$\text{Adv}_{\text{attr}} = \text{Accuracy}_{\text{adversary}}(\text{with synthetic data}) - \text{Accuracy}_{\text{baseline}}(\text{prior marginal prevalence})$$
- **Acceptance Criterion:** $\text{Adv}_{\text{attr}} \le 0.05$ ($5\%$ maximum advantage gain over random prior guessing).

### 4.3 Exact Duplicate Prevention Invariant
- A software invariant checks that zero synthetic patient records share identical tuples of (`age`, `gender`, `exact birth date`, `first 3 encounter timestamps`, `all condition codes`, `all drug dosages`) with any record in the calibration reference data.
- **Threshold:** Strictly **$0$ exact duplicates allowed**.

---

## 5. Cryptographic Provenance and Reproducibility Architecture

Every synthetic dataset released for research or external evaluation must be cryptographically sealed to ensure verifiable auditability:

1. **Deterministic Pseudorandom Seeds:**
   - Every simulation run must document its exact master seed ($42, 101, \dots$).
   - Patient-level RNGs must be isolated using deterministic hash derivation (`runner.get_patient_rng(patient_id)`).
2. **Git Commit Provenance:**
   - Every run manifest (`RUN_MANIFEST.json`) must record the exact 40-character Git commit hash under which it was generated.
3. **Cryptographic Output Hashes:**
   - SHA-256 hashes must be generated and published for all 16 exported CSV files. Any modification, post-processing, or mutation invalidates the audit certificate.
4. **Environment Specification:**
   - Python version (3.11.5), OS platform (macOS / Linux), and exact dependency versions from `requirements.txt` must accompany every evaluation report.
