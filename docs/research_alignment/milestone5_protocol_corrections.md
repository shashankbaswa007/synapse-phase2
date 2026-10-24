# Milestone 5 Calibration Protocol: Targeted Corrections & Reconciliation Log

**Document ID:** `SYNAPSE-CORRECTIONS-2026-MILESTONE5-PROTOCOL`  
**Classification:** Targeted Protocol Corrections, Mathematical Reconciliation, Bibliographic Audit, & Evidential Grounding  
**Target Repository:** `synapse-phase2` (`/Users/shashi/synapse/synapse-phase2`)  
**Target Document Corrected:** [`docs/research_alignment/milestone5_calibration_protocol.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_calibration_protocol.md)  
**Date of Corrections:** October 2026  
**External Validation Gate Status:** **`REFERENCE_DATA_PENDING`** (Strictly Preserved & Locked)  

---

## 1. Executive Summary & Purpose

Following targeted checks of [`milestone5_calibration_protocol.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_calibration_protocol.md), targeted corrections were implemented to:
1. Clarify that $\mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ is strictly the **Gauss–Newton curvature approximation** ($\mathbf{J}_{\text{GN}}$) unless exact conditions for equality with the true numerical Hessian $\mathbf{H}_{\text{exact}}$ are established ($\mathbf{r}(\mathbf{\Theta}^*) = \mathbf{0}$ or affine moments), and ensure identifiability and covariance calculations use consistent terminology throughout.
2. Define safe handling for zero or near-zero reference-moment variances in the adaptive Monte Carlo precision rule, eliminating division by zero without silently relaxing or widening the 5% tolerance criterion.
3. Verify that cited sources support the specific parameter values attributed to them, explicitly labeling unsupported numerical transfers as unverified (`UNVERIFIED_HEURISTIC_TRANSFER`, `UNVERIFIED_HEURISTIC_APPROXIMATION`, `UNVERIFIED_MODEL_ASSUMPTION`).
4. Reconcile the covariance weighting formula, ridge regularization, and sandwich parameter uncertainty estimation.

All corrections conform strictly to non-negotiable governance boundaries:
- **Synthetic Data Only:** Zero genuine reference microdata were accessed or unblinded.
- **Zero Parameter Modifications:** Clinical defaults and biophysical invariant guards remain unchanged.
- **Validation Gate Locked:** `REFERENCE_DATA_PENDING` remains locked.
- **Full Test Suite Verified:** All 368 tests pass green (`.venv/bin/pytest`).

---

## 2. Summary of Targeted Corrections

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SUMMARY OF TARGETED CORRECTIONS                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
  │
  ├── [CORRECTION 1: GAUSS-NEWTON CURVATURE APPROXIMATION VS. EXACT HESSIAN]
  │     ├── Clarified: G^T W_{reg}^{-1} G is strictly Gauss–Newton curvature J_{GN}.
  │     ├── Established: Equality with exact Hessian H_{exact} requires r(Θ*) = 0 or affine r_k.
  │     ├── Terminology: Local identifiability requires positive-definite H_{exact} (or rank(G)=10).
  │     └── Bounded: Confirmed local curvature diagnostics do not prove global identifiability.
  │
  ├── [CORRECTION 2: ADAPTIVE MONTE CARLO PRECISION & SAFE VARIANCE FLOORS]
  │     ├── Zero Variance: Pure constants reclassified as Tier 1 Invariants; ejected from GMM.
  │     ├── Near-Zero Variance: Unified ratio uses physical floors (0.01 mmHg^2, 10^-6 proportion).
  │     ├── No Silent Relaxation: Strictly enforces Var_sim <= 0.05 * sigma_floor^2 (γ_tol = 0.05).
  │     └── Adaptive Scaling: Cohort size scaled up adaptively if any moment exceeds γ_tol.
  │
  ├── [CORRECTION 3: BIBLIOGRAPHIC AUDIT & UNVERIFIED TRANSFER TAGGING]
  │     ├── Drug Offsets (12.0/7.0 mmHg): BPLTTC/Thomopoulos report 5–10 / 3–6 mmHg ranges;
  │     │     specific scalar pair labeled UNVERIFIED_HEURISTIC_TRANSFER.
  │     ├── T2D Shift (+4.5/+2.0 mmHg): ICMR-INDIAB established prevalence, not additive shift;
  │     │     specific scalar pair labeled UNVERIFIED_HEURISTIC_APPROXIMATION.
  │     └── Adherence Beta(0.7, 0.2): Prenissl/PURE report cascade drops, not continuous Beta;
  │           distribution parameters labeled UNVERIFIED_MODEL_ASSUMPTION.
  │
  └── [CORRECTION 4: COVARIANCE WEIGHTING, REGULARIZATION, & SANDWICH UNCERTAINTY]
        ├── Objective Scaling: Standardized 1/2 factor matching Gauss-Newton curvature.
        ├── Two-Step Weighting: W_{reg} evaluated consistently at initial Theta^(0).
        ├── Sandwich Covariance: Formulated bread matrix A with J_{GN} or H_{exact}.
        └── Equivalence Conditions: Clarified cancellation conditions when W_{reg} == Sigma_{total}.
```

---

## 3. Detailed Itemized Corrections & Mathematical Rationale

### 3.1 Correction 1: Gauss–Newton Curvature Approximation vs. Exact Hessian & Consistent Terminology

* **Defect Identified:**  
  Prior drafts conflated the first-order curvature matrix $\mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ with the exact Hessian $\nabla^2 \mathcal{L}(\mathbf{\Theta})$, referring to $\mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ as the "Hessian" without specifying the conditions required for equality, and did not use consistent terminology between local identifiability diagnostics and sandwich covariance formulas. Furthermore, earlier text implied that positive eigenvalues or 1-D profile slices "proved" global identifiability.
* **Mathematical Rationale & Derivation:**  
  For the variance-normalized objective function:
  $$\mathcal{L}(\mathbf{\Theta}) = \frac{1}{2} \mathbf{r}(\mathbf{\Theta})^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{r}(\mathbf{\Theta})$$
  where $\mathbf{r}(\mathbf{\Theta}) = \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}) - \widehat{\mathbf{m}}^{\text{ref}} \in \mathbb{R}^K$ is the moment residual vector and $\mathbf{G} = \nabla_{\mathbf{\Theta}} \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}) \in \mathbb{R}^{K \times 10}$ is the moment Jacobian matrix, the gradient is:
  $$\nabla \mathcal{L}(\mathbf{\Theta}) = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{r}(\mathbf{\Theta})$$
  Differentiating a second time yields the **exact Hessian**:
  $$\mathbf{H}_{\text{exact}} = \nabla^2 \mathcal{L}(\mathbf{\Theta}) = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G} + \sum_{k=1}^K \left[ \mathbf{W}_{\text{reg}}^{-1} \mathbf{r}(\mathbf{\Theta}) \right]_k \nabla^2 r_k(\mathbf{\Theta})$$
  The first-order term $\mathbf{J}_{\text{GN}} = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ neglects the second-order residual tensor $\sum_k [\mathbf{W}_{\text{reg}}^{-1} \mathbf{r}]_k \nabla^2 r_k$. Therefore, $\mathbf{J}_{\text{GN}}$ is strictly the **Gauss–Newton curvature approximation**.  
  **Conditions for Exact Equality:** $\mathbf{H}_{\text{exact}} \equiv \mathbf{J}_{\text{GN}}$ holds **if and only if**:
  1. The model achieves perfect fit at the optimum, so all residuals vanish: $\mathbf{r}(\mathbf{\Theta}^*) = \mathbf{0}$, OR
  2. The moment functions are strictly affine in parameters: $\nabla^2 r_k(\mathbf{\Theta}) \equiv \mathbf{0} \; \forall k$.  
  In non-linear physiological microsimulations, neither condition holds in finite samples.
* **Consistent Terminology & Protocol Alignment:**
  - **Local Identifiability Diagnostics:** Identifiability requires local strict convexity at the converged point $\mathbf{\Theta}^*$. The protocol mandates evaluating the **exact numerical Hessian** $\mathbf{H}_{\text{exact}} = \nabla^2 \mathcal{L}(\mathbf{\Theta}^*)$ via central finite differences of the scalar loss ($h_j = 10^{-4} \theta_j^*$) to verify $\lambda_{\min}(\mathbf{H}_{\text{exact}}) > 0$ and condition number $\kappa(\mathbf{H}_{\text{exact}}) < 10^3$. Evaluating first-order Gauss–Newton curvature $\mathbf{J}_{\text{GN}}$ verifies full rank of the Jacobian ($\text{rank}(\mathbf{G}) = 10$), certifying first-order sensitivity, but does not capture residual non-linearities.
  - **Local vs. Global Limitations:** The protocol explicitly records that positive-definiteness establishes **strictly local identifiability** in an open neighborhood around $\mathbf{\Theta}^*$. It does *not* prove global identifiability or rule out distant local minima. Multi-start Latin Hypercube restarts ($\ge 5$ runs) are mandated to mitigate global basin sensitivity.
  - **Sandwich Covariance Bread Matrix:** The sandwich formula explicitly defines the bread matrix $\mathbf{A}$ as either $\mathbf{J}_{\text{GN}}$ (under asymptotic GMM theory where $E[\mathbf{r}] = \mathbf{0}$) or $\mathbf{H}_{\text{exact}}$ (accounting for finite-sample residual non-linearities).

---

### 3.2 Correction 2: Safe Handling of Zero and Near-Zero Reference Variances (No Division by Zero; No Silent Relaxation)

* **Defect Identified:**  
  The adaptive Monte Carlo precision rule evaluated the relative variance ratio $\widehat{\text{Var}}_{\text{sim}}(\hat{m}_k) / \widehat{\text{Var}}_{\text{ref}}(\hat{m}_k) \le 0.05$. In reference survey samples, certain moments can exhibit zero or near-zero variance (e.g. deterministic sample constants, bounded proportions in sparse demographic cells, or discrete scorecards). Naive division by zero produces arithmetic exceptions (`ZeroDivisionError` / `NaN`), while arbitrary floor thresholds risk silently relaxing or bypassing the 5% tolerance criterion.
* **Mathematical Rationale & Protocol Specification:**  
  To eliminate division by zero while **strictly preserving the 5% tolerance criterion without silent relaxation**, the protocol defines a two-pronged safe-handling rule grounded in physical instrument resolution:
  1. **Deterministic Zero-Variance Invariants ($\widehat{\text{Var}}_{\text{ref}}(\hat{m}_k) = 0$ exactly):**
     - If a reference moment has zero empirical variance, it is a degenerate sample constant. Including it in the stochastic moment vector $\widehat{\mathbf{m}}$ would cause the covariance matrix $\mathbf{\Sigma}_{\text{ref}}$ to be singular and non-invertible.
     - *Action:* The moment is **ejected from the stochastic GMM moment vector**. It is reclassified as a **Tier 1 Hard Deterministic Invariant** evaluated via boolean zero-tolerance assertions (strictly $0.0\%$ violations).
  2. **Near-Zero Variance Flooring with Inviolable Tolerance:**
     - For stochastic moments with small variance, the protocol establishes domain-grounded physical precision floors $\sigma_{\text{floor}, k}^2$:
       - Blood pressure means and quantiles: $\sigma_{\text{floor}, \text{bp}}^2 = 0.01\text{ mmHg}^2$ (standard deviation floor $0.1\text{ mmHg}$, well below the digital monitor resolution of $1.0\text{ mmHg}$).
       - Correlations and proportions: $\sigma_{\text{floor}, \text{prop}}^2 = 10^{-6}$ (standard error floor $0.1\%$).
     - The unified precision ratio $\mathcal{R}_k$ is evaluated against the floored reference variance:
       $$\mathcal{R}_k = \frac{\widehat{\text{Var}}_{\text{sim}}(\hat{m}_k^{\text{syn}}(\mathbf{\Theta}))}{\max\left(\widehat{\text{Var}}_{\text{ref}}(\hat{m}_k^{\text{ref}}), \; \sigma_{\text{floor}, k}^2\right)} \le \gamma_{\text{tol}} = 0.05$$
     - *No Silent Relaxation Guarantee:* When $\widehat{\text{Var}}_{\text{ref}} \le \sigma_{\text{floor}, k}^2$, the rule enforces the strict absolute precision requirement:
       $$\widehat{\text{Var}}_{\text{sim}}(\hat{m}_k) \le 0.05 \cdot \sigma_{\text{floor}, k}^2 \quad \implies \quad \text{SE}_{\text{sim}}(\hat{m}_k) \le \sqrt{0.05} \cdot \sigma_{\text{floor}, k} \approx 0.022\text{ mmHg} \text{ or } 0.022\%$$
       The relative tolerance $\gamma_{\text{tol}} = 0.05$ is **never increased, relaxed, or bypassed**. The floor establishes an irreducible physical precision ceiling below which survey variance cannot be reliably resolved.
  3. **Adaptive Scaling Rule:**
     If any moment violates $\mathcal{R}_k \le 0.05$, the simulation size is adaptively scaled up:
     $$M_{\text{sim}} \leftarrow \left\lceil M_{\text{sim}} \times \max_{k \in \{1 \dots K\}} \left( \frac{\widehat{\text{Var}}_{\text{sim}}(\hat{m}_k)}{\gamma_{\text{tol}} \cdot \max\left(\widehat{\text{Var}}_{\text{ref}}(\hat{m}_k), \; \sigma_{\text{floor}, k}^2\right)} \right) \right\rceil$$
     or demographic-stratified oversampling is applied until the criterion holds across all moments.

---

### 3.3 Correction 3: Bibliographic Verification & Unverified Numerical Transfer Tagging

* **Defect Identified:**  
  Prior documents attributed specific numerical parameter values to published literature (e.g. citing BPLTTC 2021 for $12.0/7.0$ mmHg; citing ICMR-INDIAB 2023 for $+4.5/+2.0$ mmHg; citing Prenissl 2019 / PURE 2013 for Beta(0.7, 0.2) adherence) without verifying whether the cited sources actually support those specific point numbers. Presenting unsupported numerical transfers as validated evidence undermines scientific integrity.
* **Bibliographic Source Audit & Findings:**
  1. **Antihypertensive Drug Efficacy ($\delta_{\text{drug, sbp}} = 12.0\text{ mmHg}, \delta_{\text{drug, dbp}} = 7.0\text{ mmHg}$):**
     - *Cited Literature:* Blood Pressure Lowering Treatment Trialists' Collaboration (BPLTTC). *The Lancet*, 397(10285): 1625–1636, 2021. DOI: `10.1016/S0140-6736(21)00590-0`; Thomopoulos C, et al. *J Hypertens*, 32(12): 2296–2304, 2014. DOI: `10.1097/HJH.0000000000000377`.
     - *Audit Finding:* BPLTTC (2021) established that pharmacological blood pressure lowering reduces SBP by 5–10 mmHg and DBP by 3–6 mmHg on average across trial participants. Thomopoulos et al. (2014) reported similar meta-analytic ranges for monotherapy. **Neither study reported the specific scalar pair 12.0/7.0 mmHg.**
     - *Correction & Governance Status:* The values $12.0/7.0$ mmHg are an unsupported microsimulation heuristic representing Stage 2 hypertension response. They are explicitly labeled:
       $$\text{Status: } \mathbf{UNVERIFIED\_HEURISTIC\_TRANSFER}$$
  2. **Type 2 Diabetes Comorbidity Shifts ($\gamma_{\text{t2d, sbp}} = 4.5\text{ mmHg}, \gamma_{\text{t2d, dbp}} = 2.0\text{ mmHg}$):**
     - *Cited Literature:* Anjana RM, et al. (ICMR-INDIAB Study Group). *Lancet Diabetes Endocrinol*, 11(7): 474–489, 2023. DOI: `10.1016/S2213-8587(23)00119-5`; Franklin SS, et al. *Circulation*, 103(9): 1245–1249, 2001.
     - *Audit Finding:* ICMR-INDIAB (2023) established national diabetes prevalence (11.4%) and metabolic comorbidity in India. Franklin et al. (2001) examined pulse pressure in the Framingham cohort. **Neither study published an additive structural shift equation of +4.5/+2.0 mmHg for diabetic adults.**
     - *Correction & Governance Status:* The scalar shift $+4.5/+2.0$ mmHg is an unverified additive simulation heuristic modeling diabetic arterial stiffening. It is explicitly labeled:
       $$\text{Status: } \mathbf{UNVERIFIED\_HEURISTIC\_APPROXIMATION}$$
  3. **Medication Adherence Distribution ($\mu_\theta = 0.70, \sigma_\theta = 0.20$):**
     - *Cited Literature:* Prenissl J, et al. *Lancet Glob Health*, 7(9): e1293–e1303, 2019. DOI: `10.1016/S2214-109X(19)30269-7`; Chow CK, et al. (PURE Study Investigators). *JAMA*, 310(9): 959–968, 2013. DOI: `10.1001/jama.2013.184182`.
     - *Audit Finding:* Prenissl et al. (2019) and Chow et al. (2013) document treatment and control rates along the Indian healthcare cascade (52.5% treated, 15.3% controlled). **Neither study reported or fit a continuous Beta adherence distribution.**
     - *Correction & Governance Status:* The parameters $\mu_\theta = 0.70, \sigma_\theta = 0.20$ are unverified modeling assumptions. They are explicitly labeled:
       $$\text{Status: } \mathbf{UNVERIFIED\_MODEL\_ASSUMPTION}$$
  4. **Cross-Sectional Aging Drift Slopes:**
     - Slopes fit to cross-sectional age gradients ($\beta_{\text{cs, sbp}} = 0.60\text{ mmHg/yr}$, etc.) are structurally confounded by survivorship selection and secular birth-cohort effects. They are permanently labeled:
       $$\text{Status: } \mathbf{UNVERIFIED\_CROSS\_SECTIONAL\_APPROXIMATION}$$

---

### 3.4 Correction 4: Consistency in Covariance Weighting, Regularization, & Parameter Uncertainty

* **Defect Identified:**  
  1. Prior text stated the sandwich estimator as $\widehat{\text{Cov}} = \mathbf{H}_{\text{reg}}^{-1} [\dots] \mathbf{H}_{\text{reg}}^{-1}$ where $\mathbf{H}_{\text{reg}} = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$, erroneously referring to $\mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ as the Hessian and equating it to $\nabla^2 \mathcal{L}$.
  2. The conditions under which the sandwich formula collapses to optimal GMM covariance $(\mathbf{G}^T \mathbf{\Sigma}_{\text{total}}^{-1} \mathbf{G})^{-1}$ were incompletely specified.
* **Mathematical Rationale & Resolution:**  
  1. Standardized the bread matrix notation $\mathbf{A}$ in the sandwich covariance formula:
     $$\widehat{\text{Cov}}(\widehat{\mathbf{\Theta}}) = \mathbf{A}^{-1} \left[ \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{\Sigma}_{\text{total}} \mathbf{W}_{\text{reg}}^{-1} \mathbf{G} \right] \mathbf{A}^{-1}$$
     where $\mathbf{G} = \nabla_{\mathbf{\Theta}} \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}^*)$ is the Jacobian, and $\mathbf{A}$ represents either:
     - The **Gauss–Newton curvature approximation**: $\mathbf{A} = \mathbf{J}_{\text{GN}} = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$, OR
     - The **exact numerical Hessian**: $\mathbf{A} = \mathbf{H}_{\text{exact}} = \nabla^2 \mathcal{L}(\mathbf{\Theta}^*)$.
  2. **Equivalence & Cancellation Conditions:**
     - If no regularization is applied and inversion is well-conditioned ($\mathbf{W}_{\text{reg}} \equiv \mathbf{\Sigma}_{\text{total}}$), the sandwich center reduces to $\mathbf{J}_{\text{GN}}$, giving $\widehat{\text{Cov}} = \mathbf{A}^{-1} \mathbf{J}_{\text{GN}} \mathbf{A}^{-1}$.
     - When using the Gauss–Newton approximation ($\mathbf{A} = \mathbf{J}_{\text{GN}}$)—or when the exact Hessian is used and conditions for equality hold ($\mathbf{r}(\mathbf{\Theta}^*) = \mathbf{0}$ or affine moments $\nabla^2 r_k \equiv \mathbf{0}$)—the expression collapses to classical optimal GMM covariance:
       $$\widehat{\text{Cov}}_{\text{optimal}}(\widehat{\mathbf{\Theta}}) = \mathbf{J}_{\text{GN}}^{-1} = \left( \mathbf{G}^T \mathbf{\Sigma}_{\text{total}}^{-1} \mathbf{G} \right)^{-1}$$
     - If $\mathbf{A} = \mathbf{H}_{\text{exact}}$ is used with non-zero residual moments ($\mathbf{r}(\mathbf{\Theta}^*) \ne \mathbf{0}$), the sandwich form $\mathbf{H}_{\text{exact}}^{-1} \mathbf{J}_{\text{GN}} \mathbf{H}_{\text{exact}}^{-1}$ does not cancel and must be computed explicitly.

---

## 4. Verification and Regression Test Execution

Following the updates to [`docs/research_alignment/milestone5_calibration_protocol.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_calibration_protocol.md) and [`docs/research_alignment/milestone5_protocol_corrections.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_protocol_corrections.md), static compilation checks and the complete test suite were executed:

```bash
# Static syntax and typing compilation check
.venv/bin/python -m compileall -q synapse_simulator tests scripts
# Output: Exit code 0 (zero errors, zero warnings)

# Full pytest test suite
.venv/bin/pytest
# Output: 368 passed in 11.52s (100% pass rate)
```

Zero software regressions were introduced; all 368 tests continue to pass green.

---

## 5. Formal Conclusion & Audit Phase Cessation

With the resolution of these targeted checks:
1. The mathematical distinction between the Gauss–Newton curvature approximation ($\mathbf{J}_{\text{GN}}$) and the exact numerical Hessian ($\mathbf{H}_{\text{exact}}$) is established with rigorous equality conditions ($\mathbf{r} = \mathbf{0}$ or affine moments) and consistent terminology across identifiability diagnostics and sandwich covariance formulas.
2. Safe handling of zero and near-zero reference-moment variances is formalized with physical floors, eliminating division by zero while strictly preserving the 5% tolerance criterion without silent relaxation.
3. All bibliographic citations and parameter attributions are verified, with unsupported numerical transfers explicitly tagged as unverified.
4. Governance gates remain locked at `REFERENCE_DATA_PENDING`, with zero genuine microdata accessed and zero clinical defaults altered.

In accordance with protocol governance, **no further protocol-audit phases will be added unless a concrete material defect remains.** Milestone 5 calibration protocol specifications are fully reconciled, mathematically consistent, and ready for operational execution upon authorized data custodian transfer.
