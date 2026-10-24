# Milestone 5 Preregistered Calibration Protocol: Identifiability, Variance-Normalized Objective, & Holdout Escrow

**Document ID:** `SYNAPSE-PROTOCOL-2026-MILESTONE5-CALIBRATION`  
**Classification:** Binding Preregistered Calibration Specification, Identifiability Audit, GMM/WMDE Objective, & Statistical Stopping Protocol  
**Target Repository:** `synapse-phase2` (`/Users/shashi/synapse/synapse-phase2`)  
**Companion Documents:**
- [`docs/research_alignment/milestone5_protocol_corrections.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_protocol_corrections.md)  
- [`docs/research_alignment/milestone5_readiness_assessment.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_readiness_assessment.md)  
- [`docs/research_alignment/milestone5_go_no_go_checklist.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_go_no_go_checklist.md)  
- [`docs/research_alignment/phase2d_calibration_validation_plan.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d_calibration_validation_plan.md)  
- [`docs/research_alignment/acceptance_threshold_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/acceptance_threshold_audit.md)  

**Date of Preregistration:** October 2026  
**External Validation Gate Status:** **`REFERENCE_DATA_PENDING`** (Strictly Preserved & Locked)  
**Governance Invariant:** Synthetic data only during protocol registration; zero genuine microdata accessed; zero clinical defaults altered; zero empirical validation claims.

---

## 1. Executive Summary & Preregistration Declaration

### 1.1 Preregistration Mandate
This document establishes the binding, immutable **Preregistered Calibration Protocol** for Milestone 5 of SYNAPSE Phase 2. To eliminate post-hoc data snooping, p-hacking, retrospective scorecard adjustment, and parameter tuning against evaluation holdouts, this protocol specifies:
1. The exact mathematical separation of parameters that are estimable from cross-sectional survey observables versus those requiring independent trial evidence or structural modeling assumptions.
2. The complete removal of structurally confounded or unidentifiable parameters from the free calibration set.
3. A statistically principled, variance-normalized **Generalized Method of Moments (GMM)** / **Weighted Minimum Distance Estimation (WMDE)** objective function with adaptive Monte Carlo precision controls and safe variance floors, completely replacing arbitrary heuristic weights ($\lambda_i$).
4. Rigorous local identifiability diagnostics (distinguishing the Gauss–Newton curvature approximation from the exact Hessian, and establishing local curvature boundaries), multi-start initialization protocols, asymptotic sandwich covariance uncertainty estimation under regularized weighting, numerical stopping rules, and the schema for a frozen cryptographic run manifest.
5. The formal reclassification of numerical holdout thresholds as **provisional engineering tolerances** until empirical statistical power calculations are executed post-ingestion.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PREREGISTERED CALIBRATION PROTOCOL                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ 1. Parameter Taxonomy & Identifiability      │
               │    - Free Parameters (Category I)            │
               │    - External Trial Evidence (Category II)   │
               │    - Unidentifiable / Assumptions (Cat. III) │
               └──────────────────────┬───────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ 2. Variance-Normalized Objective Function    │
               │    - WMDE / GMM Metric Vector m(Θ)           │
               │    - Design Covariance Σ_ref (TSL / Boots)   │
               │    - Adaptive Precision Check with Floors    │
               │    - Regularized Weighting & Sandwich Covar  │
               └──────────────────────┬───────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ 3. Optimization & Diagnostic Protocol        │
               │    - Nelder-Mead with Multi-Start Restarts   │
               │    - Internal 5-Fold Cluster Cross-Validation│
               │    - Exact Hessian vs Gauss-Newton Defined   │
               │    - Local Condition Bound: κ(H_exact) < 10^3│
               └──────────────────────┬───────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ 4. Calibration Freeze & Cryptographic Signoff│
               │    - Freeze Parameter Vector Θ*              │
               │    - Lock CALIBRATION_FROZEN_MANIFEST.json   │
               │    - Permanent Git Commit of Manifest Digest │
               └──────────────────────┬───────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │ 5. Single-Use Holdout Ticket Authorization   │
               │    (Partition C Decrypted Strictly Once)     │
               └──────────────────────────────────────────────┘
```

---

## 2. Parameter Taxonomy & Three-Way Identifiability Separation

Prior readiness documents proposed an undifferentiated 17-parameter free calibration set. Following the methodological audit in [`milestone5_go_no_go_checklist.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_go_no_go_checklist.md#L150), all simulation parameters across the seven causal layers are separated into three mutually exclusive categories.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THREE-WAY PARAMETER TAXONOMY                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
  │
  ├── [CATEGORY I: FREE ESTIMABLE PARAMETERS (Θ_LASI)] (10 Scalar Parameters)
  │     ├── Resting Hemodynamic Anchors: μ_{0, sbp}, σ_{0, sbp}, μ_{0, dbp}, σ_{0, dbp}
  │     ├── Bivariate Association: ρ_0 (resting SBP-DBP correlation)
  │     ├── Demographic Contrasts: δ_{male, sbp}, δ_{male, dbp}
  │     └── Measurement Protocol: α_{alert, sbp}, α_{alert, dbp}, σ_{within}
  │
  ├── [CATEGORY II: FIXED EXTERNAL CLINICAL EVIDENCE] (8 Scalar Parameters)
  │     ├── Antihypertensive Efficacy: δ_{drug, sbp} = 12.0, δ_{drug, dbp} = 7.0 mmHg
  │     │     (UNVERIFIED_HEURISTIC_TRANSFER; BPLTTC 2021 / Thomopoulos 2014)
  │     ├── Pharmacokinetic Ramp: τ_{ramp} = 14.0 days (UNVERIFIED_PHARMACOLOGY_HEURISTIC)
  │     ├── Comorbidity Shifts: γ_{t2d, sbp} = 4.5, γ_{t2d, dbp} = 2.0 mmHg
  │     │     (UNVERIFIED_HEURISTIC_APPROXIMATION; ICMR-INDIAB 2023)
  │     └── Invariant Guards: PP_min = 20.0 mmHg, SBP in [70, 260], DBP in [40, 150] mmHg
  │
  └── [CATEGORY III: STRUCTURALLY UNIDENTIFIABLE / ASSUMPTIONS] (7 Scalar Parameters)
        ├── Longitudinal Aging Drift: β_{age, sbp}, β_{age, dbp1}, β_{age, dbp2}, a_{inflect}
        │     (UNVERIFIED_CROSS_SECTIONAL_APPROXIMATION; Confounded by survivorship & cohort)
        ├── Medication Adherence: μ_θ = 0.70, σ_θ = 0.20
        │     (UNVERIFIED_MODEL_ASSUMPTION; Prenissl et al. 2019 / PURE 2013)
        └── Healthcare Operations: τ_{screen} = 90 d, τ_{maint} = 180 d, λ_{htn} = 0.0344/yr
```

### 2.1 Category I: Free Parameters Estimable from Cross-Sectional LASI Partition A ($\mathbf{\Theta}_{\text{LASI}}$)

These parameters correspond to physical and physiological observables that are **directly identifiable** from unmedicated respondents in Partition A without confounding by survivorship, treatment indication, or cohort transitions:

| Parameter Symbol | Configuration Path | Baseline Default | Identifiability Subpopulation & Estimator in Partition A | Search Bounds $[\theta_{\min}, \theta_{\max}]$ |
| :--- | :--- | :---: | :--- | :---: |
| $\mu_{0, \text{sbp}}$ | `forward_hemodynamics.mean_sbp_anchor` | `120.0 mmHg` | Weighted mean protocol SBP among unmedicated normotensive respondents aged 45–49. | $[110.0, 130.0]\text{ mmHg}$ |
| $\sigma_{0, \text{sbp}}$ | `forward_hemodynamics.sd_sbp_anchor` | `9.0 mmHg` | Weighted standard deviation of protocol SBP among unmedicated respondents aged 45–49. | $[6.0, 14.0]\text{ mmHg}$ |
| $\mu_{0, \text{dbp}}$ | `forward_hemodynamics.mean_dbp_anchor` | `78.0 mmHg` | Weighted mean protocol DBP among unmedicated normotensive respondents aged 45–49. | $[70.0, 86.0]\text{ mmHg}$ |
| $\sigma_{0, \text{dbp}}$ | `forward_hemodynamics.sd_dbp_anchor` | `6.0 mmHg` | Weighted standard deviation of protocol DBP among unmedicated respondents aged 45–49. | $[4.0, 10.0]\text{ mmHg}$ |
| $\rho_0$ | `forward_hemodynamics.sbp_dbp_correlation` | `0.65` | Survey-weighted Pearson correlation between protocol SBP and DBP in unmedicated adults. | $[0.40, 0.85]$ |
| $\delta_{\text{male, sbp}}$ | `forward_hemodynamics.male_sbp_offset` | `2.0 mmHg` | Weighted mean contrast $\bar{\text{SBP}}_{\text{male}} - \bar{\text{SBP}}_{\text{female}}$ among unmedicated respondents aged 45–49. | $[-2.0, 6.0]\text{ mmHg}$ |
| $\delta_{\text{male, dbp}}$ | `forward_hemodynamics.male_dbp_offset` | `1.5 mmHg` | Weighted mean contrast $\bar{\text{DBP}}_{\text{male}} - \bar{\text{DBP}}_{\text{female}}$ among unmedicated respondents aged 45–49. | $[-2.0, 5.0]\text{ mmHg}$ |
| $\alpha_{\text{alert, sbp}}$ | `bp_measurement.reading1_alerting_sbp` | `3.5 mmHg` | Survey-weighted intra-individual contrast $\text{mean}(R_1 - R_2)$ across all valid pairs. | $[1.0, 8.0]\text{ mmHg}$ |
| $\alpha_{\text{alert, dbp}}$ | `bp_measurement.reading1_alerting_dbp` | `1.5 mmHg` | Survey-weighted intra-individual contrast $\text{mean}(R_1 - R_2)$ across all valid pairs. | $[0.5, 4.0]\text{ mmHg}$ |
| $\sigma_{\text{within}}$ | `bp_measurement.within_visit_noise_sd` | `1.8 mmHg` | Residual within-visit standard deviation derived from $\frac{1}{2}\text{Var}(R_2 - R_3)$. | $[0.8, 3.5]\text{ mmHg}$ |

### 2.2 Category II: Parameters Fixed to External Clinical Evidence & Trial Meta-Analyses

The following parameters are **removed** from empirical calibration against LASI Wave 1 because observational survey data cannot identify them without severe bias. They are strictly fixed to external clinical trial literature, carry explicit applicability notes, and are marked with their true validation status:

| Parameter Symbol | Configuration Path | Fixed Value | Evidential Status Tag | Authoritative Bibliographic Citation & Applicability Notes |
| :--- | :--- | :---: | :---: | :--- |
| $\delta_{\text{drug, sbp}}$ | `forward_hemodynamics.delta_drug_sbp` | `12.0 mmHg` | `UNVERIFIED_HEURISTIC_TRANSFER` | **Source Evidence:** Blood Pressure Lowering Treatment Trialists' Collaboration (BPLTTC). *The Lancet*, 397(10285): 1625–1636, 2021. DOI: [10.1016/S0140-6736(21)00590-0](https://doi.org/10.1016/S0140-6736(21)00590-0); Thomopoulos C, et al. *J Hypertens*, 32(12): 2296–2304, 2014. DOI: [10.1097/HJH.0000000000000377](https://doi.org/10.1097/HJH.0000000000000377).<br>*Applicability Note & Verification Disclosure:* In cross-sectional surveys, treated hypertensives frequently exhibit higher blood pressure than untreated individuals due to **confounding by indication / disease severity**. BPLTTC (2021) established that pharmacological lowering reduces SBP by 5–10 mmHg and DBP by 3–6 mmHg on average across trial participants. **The specific pair 12.0/7.0 mmHg is a round microsimulation heuristic for Stage 2 hypertension, not an exact point estimate reported by BPLTTC.** It is explicitly labeled as an unverified external transfer. |
| $\delta_{\text{drug, dbp}}$ | `forward_hemodynamics.delta_drug_dbp` | `7.0 mmHg` | `UNVERIFIED_HEURISTIC_TRANSFER` | Same as above. Fixed simulation heuristic for DBP reduction under monotherapy. |
| $\tau_{\text{ramp}}$ | `forward_hemodynamics.treatment_ramp_days` | `14.0 days` | `UNVERIFIED_PHARMACOLOGY_HEURISTIC` | **Clinical Pharmacology Prescribing Standards (Amlodipine / Telmisartan Package Inserts).** Cross-sectional surveys collect static point-in-time observations; the initial 14-day steady-state ramp curve contains zero survey observables. Heuristic standard from package insert pharmacokinetics. |
| $\gamma_{\text{t2d, sbp}}$ | `forward_hemodynamics.t2d_sbp_shift` | `4.5 mmHg` | `UNVERIFIED_HEURISTIC_APPROXIMATION` | **Source Evidence:** Anjana RM, et al. (ICMR-INDIAB Study Group). *Lancet Diabetes Endocrinol*, 11(7): 474–489, 2023. DOI: [10.1016/S2213-8587(23)00119-5](https://doi.org/10.1016/S2213-8587(23)00119-5); Franklin SS, et al. *Circulation*, 103(9): 1245–1249, 2001.<br>*Applicability Note & Verification Disclosure:* ICMR-INDIAB (2023) established the high comorbidity between diabetes and hypertension in India ($>50\%$ overlap), but **did not publish a structural additive shift of +4.5/+2.0 mmHg**. The scalar shift $+4.5/+2.0$ mmHg is an unverified additive simulation heuristic modeling diabetic arterial stiffening, not an empirical point estimate from ICMR-INDIAB. |
| $\gamma_{\text{t2d, dbp}}$ | `forward_hemodynamics.t2d_dbp_shift` | `2.0 mmHg` | `UNVERIFIED_HEURISTIC_APPROXIMATION` | Same as above. Fixed additive heuristic for DBP shift in diabetic patients. |
| $\text{PP}_{\min}$ | `forward_hemodynamics.min_pulse_pressure` | `20.0 mmHg` | `PHYSIOLOGICAL_GUARD` | **Cardiovascular Physiology (Starling's Law / Stroke Volume Limits).** Inviolable lower physiological guard. |
| $\text{SBP}_{\text{bounds}}$ | `forward_hemodynamics.min_sbp / max_sbp` | `[70.0, 260.0]` | `PHYSIOLOGICAL_GUARD` | **Human Biophysical Perfusion Limits.** Inviolable physiological guards. |
| $\text{DBP}_{\text{bounds}}$ | `forward_hemodynamics.min_dbp / max_dbp` | `[40.0, 150.0]` | `PHYSIOLOGICAL_GUARD` | **Coronary Perfusion Biophysical Limits.** Inviolable physiological guards. |

### 2.3 Category III: Structurally Unidentifiable Parameters (Assumptions Tagged)

These parameters are **unidentifiable from single-wave cross-sectional data** and are permanently labeled with the governance status `UNVERIFIED_MODEL_ASSUMPTION`:

1. **Longitudinal Biological Aging Drift ($\beta_{\text{age, sbp}}, \beta_{\text{age, dbp1}}, \beta_{\text{age, dbp2}}, a_{\text{inflect}}$):**
   - *Structural Confounding:* Cross-sectional age gradients confound within-person biological vascular stiffening with **survivorship/mortality selection** (unhealthy hypertensives die earlier, flattening the apparent age slope in elderly cohorts) and **secular birth-cohort effects** (differing early-life nutrition and infectious burdens across generations).
   - *Binding Protocol Rule:* In Milestone 5, age gradients in Partition A are fit strictly as *cross-sectional marginal anchors* ($\beta_{\text{cs, sbp}} = 0.60\text{ mmHg/yr}$, $\beta_{\text{cs, dbp1}} = 0.25$, $\beta_{\text{cs, dbp2}} = -0.15$, $a_{\text{inflect}} = 60.0$). **Longitudinal causal claims are permanently disclaimed** until LASI Wave 2 panel re-measurements are ingested. Status: `UNVERIFIED_CROSS_SECTIONAL_APPROXIMATION`.
2. **Continuous Medication Adherence Distribution ($\mu_\theta, \sigma_\theta$):**
   - *Structural Confounding:* LASI Wave 1 records adherence via a single binary/ordinal questionnaire response ("Are you currently taking BP medication regularly?"). A scalar variable cannot identify both the mean ($\mu_\theta$) and dispersion ($\sigma_\theta$) of a continuous Beta distribution.
   - *Bibliographic Citation:* Prenissl J, et al. *Lancet Glob Health*, 7(9): e1293–e1303, 2019. DOI: [10.1016/S2214-109X(19)30269-7](https://doi.org/10.1016/S2214-109X(19)30269-7); Chow CK, et al. (PURE Study Investigators). *JAMA*, 310(9): 959–968, 2013. DOI: [10.1001/jama.2013.184182](https://doi.org/10.1001/jama.2013.184182).
   - *Verification Disclosure:* Prenissl et al. (2019) and Chow et al. (2013) document treatment and control rates along the Indian healthcare cascade (52.5% treated, 15.3% controlled). **Neither study reported a continuous Beta adherence distribution.** The parameters $\mu_\theta = 0.70$ and $\sigma_\theta = 0.20$ are unverified engineering assumptions. Status: `UNVERIFIED_MODEL_ASSUMPTION`.
3. **Annual Disease Incidence ($\lambda_{\text{htn}} = 0.0344\text{ yr}^{-1}$) & Healthcare Delays ($\tau_{\text{screen}} = 90\text{ d}, \tau_{\text{maint}} = 180\text{ d}$):**
   - Cross-sectional surveys observe cumulative prevalence, not incident hazard rates. Fixed to provisional literature defaults with `UNVERIFIED_MODEL_ASSUMPTION` tags.

---

## 3. Variance-Normalized Objective Function (WMDE / GMM)

### 3.1 Rejection of Arbitrary Scalar Loss Formulations
Section 5.2 of the preliminary readiness assessment proposed minimizing an arbitrary linear combination:
$$L(\mathbf{\Theta}) = \lambda_1 W_1(\text{SBP}) + \lambda_2 W_1(\text{DBP}) + \lambda_3 L_{\text{prev}} + \dots$$
**This formulation is formally rejected.** Linear scalarization with subjective coefficients ($\lambda_i$) has no statistical justification:
1. It mixes metrics with different units and scales (millimeters of mercury versus dimensionless normalized squared errors).
2. It fails to account for sampling variance differences across demographic strata (sparse 80+ cells receive identical weight to dense 45–54 cells unless properly normalized).
3. It ignores cross-metric correlations between SBP, DBP, and prevalence.

### 3.2 Formal GMM / WMDE Formulation
The preregistered calibration objective is formulated as a **Generalized Method of Moments (GMM)** / **Weighted Minimum Distance Estimator (WMDE)** over the free parameter vector $\mathbf{\Theta}_{\text{LASI}} \in \mathbb{R}^{10}$:

$$\widehat{\mathbf{\Theta}} = \arg\min_{\mathbf{\Theta}} \mathcal{L}(\mathbf{\Theta}) = \frac{1}{2} \left( \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}) - \widehat{\mathbf{m}}^{\text{ref}} \right)^T \mathbf{W}_{\text{reg}}^{-1} \left( \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}) - \widehat{\mathbf{m}}^{\text{ref}} \right)$$

where:
1. $\widehat{\mathbf{m}}^{\text{ref}} \in \mathbb{R}^K$ is the vector of complex-survey-weighted empirical moments computed from **Partition A**.
2. $\widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}) \in \mathbb{R}^K$ is the corresponding moment vector generated by the forward simulation engine under candidate parameters $\mathbf{\Theta}$.
3. $\mathbf{W}_{\text{reg}} \in \mathbb{R}^{K \times K}$ is the regularized total uncertainty weighting matrix evaluated via consistent two-step estimation (evaluated at initial or step-1 estimates $\mathbf{\Theta}^{(0)}$ to prevent the objective from artificially shrinking the variance matrix during optimization).

### 3.3 Target Moment Vector Specification ($\widehat{\mathbf{m}}$)
The moment vector $\widehat{\mathbf{m}}$ comprises $K = 26$ targeted statistical moments:
- **Baseline Anchors (Unmedicated 45–49 yrs):** $\bar{Y}_{\text{sbp}}, S_{\text{sbp}}, \bar{Y}_{\text{dbp}}, S_{\text{dbp}}, \text{Cov}(Y_{\text{sbp}}, Y_{\text{dbp}})$ (5 moments).
- **Demographic Sex Contrasts (45–49 yrs):** $\bar{Y}_{\text{sbp, male}} - \bar{Y}_{\text{sbp, female}}$, $\bar{Y}_{\text{dbp, male}} - \bar{Y}_{\text{dbp, female}}$ (2 moments).
- **Measurement Protocol Offsets:** $\text{mean}(R_1 - R_2)_{\text{sbp}}$, $\text{mean}(R_1 - R_2)_{\text{dbp}}$, $\text{Var}(R_2 - R_3)_{\text{pooled}}$ (3 moments).
- **Stratified Blood Pressure Quantiles (Marginal Distributions):** Age-stratified protocol SBP and DBP quantiles $Q \in \{0.10, 0.25, 0.50, 0.75, 0.90\}$ across male and female 45–54 age bands (16 moments).

### 3.4 Total Uncertainty Weighting Matrix & Adaptive Monte Carlo Precision

The unregularized total uncertainty covariance matrix is:
$$\mathbf{W}(\mathbf{\Theta}) = \mathbf{\Sigma}_{\text{ref}} + \mathbf{\Sigma}_{\text{sim}}(\mathbf{\Theta})$$

1. **Reference Complex Survey Covariance ($\mathbf{\Sigma}_{\text{ref}}$):**
   - Estimated directly from Partition A using the design-based **Taylor Series Linearization (TSL)** engine ([`variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py)) or $B = 1,000$ multi-stage cluster bootstrap resamples at the PSU level within strata.
   - Accurately incorporates unequal sampling weights, clustering design effects ($\text{DEFF}_c$), and stratum support.
2. **Simulation Monte Carlo Covariance ($\mathbf{\Sigma}_{\text{sim}}$):**
   - Represents the finite-sample variability of the synthetic cohort:
     $$\mathbf{\Sigma}_{\text{sim}}(\mathbf{\Theta}) = \frac{1}{M_{\text{sim}}} \mathbf{\Sigma}_{\text{MC}}(\mathbf{\Theta})$$
3. **Adaptive Moment-Specific Monte Carlo Precision Criterion & Safe Variance Floors:**
   > [!IMPORTANT]
   > **Handling Zero and Near-Zero Reference Moment Variances:**  
   > A fixed global simulation size (e.g. $M_{\text{sim}} \ge 20,000$) cannot guarantee negligible Monte Carlo error across all demographic cells. Conversely, if a reference moment exhibits zero or near-zero variance, naive division by $\widehat{\text{Var}}_{\text{ref}}$ leads to arithmetic singularity or infinite sample size requirements.
   >
   > To prevent division by zero while **strictly preserving the 5% tolerance criterion without silent relaxation**, the protocol establishes domain-grounded physical precision floors $\sigma_{\text{floor}, k}^2$:
   > - Blood pressure mean and quantile moments (mmHg): $\sigma_{\text{floor}, \text{bp}}^2 = 0.01\text{ mmHg}^2$ (standard deviation floor $0.1\text{ mmHg}$, well below the digital monitor resolution of $1.0\text{ mmHg}$).
   > - Correlation and proportion moments: $\sigma_{\text{floor}, \text{prop}}^2 = 10^{-6}$ (standard error floor $0.1\%$).
   >
   > **Protocol Rules for Variance Singularities:**
   > 1. *Deterministic Zero-Variance Invariants:* If $\widehat{\text{Var}}_{\text{ref}}(\hat{m}_k) = 0$ exactly (a degenerate constant in the reference sample), the moment **must be removed** from the stochastic GMM moment vector $\widehat{\mathbf{m}}$ to prevent covariance singularity. It is reclassified as a **Tier 1 Hard Deterministic Invariant** evaluated via boolean zero-tolerance assertions ($0.0\%$ violations).
   > 2. *Near-Zero Variance Flooring:* For all stochastic moments, the unified precision ratio $\mathcal{R}_k$ is evaluated against the floored reference variance:
   >    $$\mathcal{R}_k = \frac{\widehat{\text{Var}}_{\text{sim}}(\hat{m}_k^{\text{syn}}(\mathbf{\Theta}))}{\max\left(\widehat{\text{Var}}_{\text{ref}}(\hat{m}_k^{\text{ref}}), \; \sigma_{\text{floor}, k}^2\right)} \le \gamma_{\text{tol}} = 0.05$$
   >    When $\widehat{\text{Var}}_{\text{ref}} \le \sigma_{\text{floor}, k}^2$, this enforces the strict absolute precision requirement $\widehat{\text{Var}}_{\text{sim}} \le 0.05 \cdot \sigma_{\text{floor}, k}^2$ ($\text{SE}_{\text{sim}} \le 0.022\text{ mmHg}$ or $\le 0.022\%$). This guarantees numerical stability without division by zero and **without silently relaxing or widening the 5% tolerance criterion** ($\gamma_{\text{tol}} = 0.05$ remains strictly inviolable).
   > 3. *Adaptive Scaling Rule:* If any moment violates $\mathcal{R}_k \le 0.05$, the simulation size is adaptively scaled up:
   >    $$M_{\text{sim}} \leftarrow \left\lceil M_{\text{sim}} \times \max_{k \in \{1 \dots K\}} \left( \frac{\widehat{\text{Var}}_{\text{sim}}(\hat{m}_k)}{\gamma_{\text{tol}} \cdot \max\left(\widehat{\text{Var}}_{\text{ref}}(\hat{m}_k), \; \sigma_{\text{floor}, k}^2\right)} \right) \right\rceil$$
   >    or demographic-stratified oversampling is applied until $\mathcal{R}_k \le 0.05$ holds across all target moments.

### 3.5 Regularized / Block-Diagonal Weighting for Ill-Conditioned Covariances
In practice, full $26 \times 26$ empirical covariance matrices can exhibit high condition numbers ($\kappa(\mathbf{\Sigma}_{\text{ref}}) > 10^4$) due to high correlation between adjacent quantiles ($Q_{0.75}$ and $Q_{0.90}$).

**Preregistered Matrix Regularization Protocol:**
1. Compute the condition number $\kappa = \lambda_{\max}(\mathbf{W}) / \lambda_{\min}(\mathbf{W})$.
2. If $\kappa \le 10^3$, invert $\mathbf{W}$ directly via Cholesky decomposition: $\mathbf{W}^{-1} = (\mathbf{L}\mathbf{L}^T)^{-1}$.
3. If $\kappa > 10^3$, apply **Tikhonov / Ridge Regularization**:
   $$\mathbf{W}_{\text{reg}} = \mathbf{W} + \epsilon \cdot \text{diag}(\mathbf{W}), \quad \epsilon = 10^{-3}$$
4. If off-diagonal cross-block covariances between distinct measurement dimensions (e.g. alerting offset vs. baseline quantile) have empirical correlation $r < 0.15$ with overlapping bootstrap $p > 0.05$, apply **Block-Diagonal Precision Weighting**:
   $$\mathbf{W}_{\text{block}} = \text{block\_diag}\left(\mathbf{\Sigma}_{\text{anchors}}, \mathbf{\Sigma}_{\text{sex}}, \mathbf{\Sigma}_{\text{protocol}}, \mathbf{\Sigma}_{\text{quantiles}}\right)$$
   This guarantees positive-definiteness, eliminates numerical inversion instability, and preserves correct relative weighting across all physical dimensions.

---

## 4. Optimization Engine, Diagnostics, Uncertainty, & Frozen Manifest

### 4.1 Numerical Optimization Algorithm
Optimization is executed using the **Nelder-Mead simplex algorithm** with adaptive parameters (Gao & Han 2012) and bounded box projections:
1. **Parameter Transformation:** All bounded parameters $\theta_j \in [\theta_j^{\min}, \theta_j^{\max}]$ are mapped to unconstrained space via the logit-link transformation:
   $$\tilde{\theta}_j = \ln\left( \frac{\theta_j - \theta_j^{\min}}{\theta_j^{\max} - \theta_j} \right)$$
   This prevents the simplex from evaluating unphysiological parameters (e.g. negative standard deviations or correlations $> 1.0$).
2. **Extreme Barrier Penalty:** If any trial point generates physiological invariant violations ($PP < 20$ mmHg or $SBP \le DBP$), the simulator returns a barrier loss value $\mathcal{L} = 10^{12}$, immediately rejecting the trial simplex vertex.

### 4.2 Exact Hessian vs. Gauss–Newton Curvature & Local Identifiability Diagnostics

> [!CAUTION]
> **Mathematical Distinction: Exact Hessian vs. Gauss–Newton Approximation:**  
> For the objective function $\mathcal{L}(\mathbf{\Theta}) = \frac{1}{2} \mathbf{r}(\mathbf{\Theta})^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{r}(\mathbf{\Theta})$, where $\mathbf{r}(\mathbf{\Theta}) = \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}) - \widehat{\mathbf{m}}^{\text{ref}}$ and $\mathbf{G} = \nabla_{\mathbf{\Theta}} \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta})$, the **exact Hessian** is:
> $$\mathbf{H}_{\text{exact}} = \nabla^2 \mathcal{L}(\mathbf{\Theta}) = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G} + \sum_{k=1}^K [\mathbf{W}_{\text{reg}}^{-1} \mathbf{r}(\mathbf{\Theta})]_k \nabla^2 r_k(\mathbf{\Theta})$$
> The first-order matrix $\mathbf{J}_{\text{GN}} = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ is strictly the **Gauss–Newton curvature approximation**.  
> **Conditions for Equality:** $\mathbf{H}_{\text{exact}} \equiv \mathbf{J}_{\text{GN}}$ holds **if and only if**:
> 1. The model fits the moments perfectly at the optimum ($\mathbf{r}(\mathbf{\Theta}^*) = \mathbf{0}$), OR
> 2. The moment functions are strictly affine in parameters ($\nabla^2 r_k(\mathbf{\Theta}) \equiv \mathbf{0}$).  
> Because our non-linear simulation model exhibits non-zero residual moments and non-linear parameter mappings, $\mathbf{J}_{\text{GN}}$ is strictly a first-order curvature approximation.

**Consistent Terminology for Diagnostics and Covariance:**
1. **Local Curvature & Identifiability Diagnostics:**
   At convergence $\mathbf{\Theta}^*$, the **exact numerical Hessian** $\mathbf{H}_{\text{exact}} = \nabla^2 \mathcal{L}(\mathbf{\Theta}^*)$ is computed via central finite differences of the scalar loss with step size $h_j = 10^{-4} \cdot \theta_j^*$.
   - *Positive-Definiteness:* All eigenvalues must be strictly positive: $\lambda_{\min}(\mathbf{H}_{\text{exact}}) > 0$.
     *Scope & Limitations:* Verifies **strictly local identifiability** in an open neighborhood around $\mathbf{\Theta}^*$, confirming that local curvature is strictly convex and non-degenerate. It does **not** prove global identifiability, nor does it rule out distant local minima or disconnected basins of attraction across $\Omega$.
   - *Condition Number Bound:* $\kappa(\mathbf{H}_{\text{exact}}) = \frac{\lambda_{\max}(\mathbf{H}_{\text{exact}})}{\lambda_{\min}(\mathbf{H}_{\text{exact}})} < 10^3$. If $\kappa \ge 10^3$, severe parameter sloppiness or collinearity exists.
2. **1-D Profile Likelihood Slices (Coordinate Cross-Sections):**
   Evaluate 1-D profile likelihood slices for each parameter $\theta_j$ over $[\theta_j^{\min}, \theta_j^{\max}]$ while profiling out other parameters.
   *Diagnostic Scope:* Detects single-coordinate non-identifiability (flat profiles) or local non-convexity. It cannot detect high-dimensional curvilinear valleys or diagonal saddle ridges off the coordinate axes.
3. **Multi-Start Simplex Protocol (Global Basin Sensitivity Mitigation):**
   To mitigate the risk of local non-global traps, the Nelder-Mead optimization must be initialized from at least **5 diverse starting vectors** $\mathbf{\Theta}^{(0)}$ drawn via Latin Hypercube Sampling across the interior of the search space. Convergence to a single consistent parameter basin ($|\theta_{j, \text{run } a}^* - \theta_{j, \text{run } b}^*| / \bar{\theta}_j^* < 0.02$) is required before declaring convergence.

### 4.3 Overfitting Diagnostic: Internal 5-Fold Cluster Cross-Validation
To guarantee that the calibrated parameters do not overfit idiosyncrasies of Partition A:
1. The clusters (PSUs) in Partition A are randomly partitioned into 5 balanced folds.
2. The model is optimized on 4 folds ($\mathcal{D}_{A, -k}$) and evaluated out-of-fold on the held-out 5th fold ($\mathcal{D}_{A, k}$).
3. **Cross-Validation Generalization Invariant:**
   $$\Delta_{\text{CV}} = \frac{\bar{\mathcal{L}}_{\text{OOF}} - \mathcal{L}_{\text{train}}}{\mathcal{L}_{\text{train}}} < 0.20$$
   If the out-of-fold loss exceeds training loss by more than $20\%$, parameter over-parameterization is detected, requiring dimension reduction before proceeding.

### 4.4 Calibrated Parameter Uncertainty Estimation (Asymptotic Sandwich Formula)

When the weighting matrix $\mathbf{W}_{\text{reg}}$ incorporates Tikhonov ridge regularization ($\epsilon > 0$) or block-diagonalization, it does not equal the exact empirical covariance ($\mathbf{W}_{\text{reg}} \ne \mathbf{\Sigma}_{\text{total}}$). Consequently, standard optimal-GMM variance formulas like $(\mathbf{G}^T \mathbf{W}^{-1} \mathbf{G})^{-1}$ are biased and understate uncertainty.

The protocol mandates the **full asymptotic sandwich covariance estimator**:
$$\widehat{\text{Cov}}(\widehat{\mathbf{\Theta}}) = \mathbf{A}^{-1} \left[ \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{\Sigma}_{\text{total}} \mathbf{W}_{\text{reg}}^{-1} \mathbf{G} \right] \mathbf{A}^{-1}$$
where:
1. $\mathbf{G} = \nabla_{\mathbf{\Theta}} \widehat{\mathbf{m}}^{\text{syn}}(\mathbf{\Theta}^*) \in \mathbb{R}^{K \times 10}$ is the numerical Jacobian of simulated moments with respect to parameters.
2. The "bread" matrix $\mathbf{A}$ is evaluated using either:
   - The standard GMM Gauss–Newton curvature matrix: $\mathbf{A} = \mathbf{J}_{\text{GN}} = \mathbf{G}^T \mathbf{W}_{\text{reg}}^{-1} \mathbf{G}$ (valid under asymptotic GMM theory where moment residuals have expectation zero), OR
   - The exact numerical Hessian: $\mathbf{A} = \mathbf{H}_{\text{exact}} = \nabla^2 \mathcal{L}(\mathbf{\Theta}^*)$ (accounting for non-zero finite-sample moment residuals and second-order non-linearities).
3. $\mathbf{\Sigma}_{\text{total}} = \mathbf{\Sigma}_{\text{ref}} + \mathbf{\Sigma}_{\text{sim}}(\mathbf{\Theta}^*)$ is the true unregularized empirical covariance matrix.

*Note on Simplification & Equivalence Conditions:*
- If no regularization is required and full inversion is well-conditioned ($\mathbf{W}_{\text{reg}} \equiv \mathbf{\Sigma}_{\text{total}}$), the sandwich expression simplifies to $\mathbf{A}^{-1} \mathbf{J}_{\text{GN}} \mathbf{A}^{-1}$ where $\mathbf{J}_{\text{GN}} = \mathbf{G}^T \mathbf{\Sigma}_{\text{total}}^{-1} \mathbf{G}$.
- If using the Gauss–Newton curvature approximation ($\mathbf{A} = \mathbf{J}_{\text{GN}}$)—or if the exact Hessian is used and conditions for equality hold ($\mathbf{r}(\mathbf{\Theta}^*) = \mathbf{0}$ or affine moments $\nabla^2 r_k \equiv \mathbf{0}$)—the sandwich expression collapses to the classical optimal GMM covariance:
  $$\widehat{\text{Cov}}_{\text{optimal}}(\widehat{\mathbf{\Theta}}) = \mathbf{J}_{\text{GN}}^{-1} = \left( \mathbf{G}^T \mathbf{\Sigma}_{\text{total}}^{-1} \mathbf{G} \right)^{-1}$$
- If the exact numerical Hessian $\mathbf{A} = \mathbf{H}_{\text{exact}}$ is used and residual moments are non-zero ($\mathbf{r}(\mathbf{\Theta}^*) \ne \mathbf{0}$), the sandwich form $\mathbf{H}_{\text{exact}}^{-1} \mathbf{J}_{\text{GN}} \mathbf{H}_{\text{exact}}^{-1}$ does not cancel and must be computed explicitly to reflect finite-sample misspecification.
Standard errors are extracted as $\text{SE}(\hat{\theta}_j) = \sqrt{\widehat{\text{Cov}}_{jj}}$, and 95% Wald confidence intervals are reported: $\hat{\theta}_j \pm 1.96 \cdot \text{SE}(\hat{\theta}_j)$.

### 4.5 Formal Stopping Criteria
Nelder-Mead optimization terminates if and only if **all** of the following conditions are met:
1. **Function Value Absolute Tolerance:** $|\mathcal{L}^{(t)} - \mathcal{L}^{(t-20)}| < 10^{-5}$ across 20 successive iterations.
2. **Parameter Coordinate Relative Tolerance:** $\max_j |\theta_j^{(t)} - \theta_j^{(t-1)}| / |\theta_j^{(t)}| < 10^{-4}$.
3. **Iteration Cap:** Total function evaluations $\le 1,500$.
4. **Boundary Separation:** Final point $\mathbf{\Theta}^*$ is strictly interior to the search box: $\text{dist}(\theta_j^*, \partial \Omega_j) > 0.05 \cdot (\theta_j^{\max} - \theta_j^{\min})$.

### 4.6 Cryptographic Frozen Run Manifest Schema (`CALIBRATION_FROZEN_MANIFEST.json`)
Upon satisfying all convergence and diagnostic checks, the calibration harness writes a cryptographically signed manifest:

```json
{
  "manifest_version": "1.0.0",
  "run_id": "calib-run-2026-m5-partA-001",
  "pipeline_git_commit": "e8a14b58c...",
  "execution_timestamp": "2026-10-24T12:00:00Z",
  "governance_status": "CALIBRATION_FROZEN",
  "partition_a_digest": {
    "source_file": "data/reference/derived_partition_a/lasi_partition_a.csv",
    "sha256": "3b8c1a9d...",
    "records_count": 43250,
    "psus_count": 1260
  },
  "free_calibrated_parameters": {
    "mean_sbp_anchor": {"estimate": 121.2, "se": 0.42, "ci_95": [120.38, 122.02], "unit": "mmHg"},
    "sd_sbp_anchor": {"estimate": 8.7, "se": 0.31, "ci_95": [8.09, 9.31], "unit": "mmHg"},
    "mean_dbp_anchor": {"estimate": 78.4, "se": 0.28, "ci_95": [77.85, 78.95], "unit": "mmHg"},
    "sd_dbp_anchor": {"estimate": 5.9, "se": 0.22, "ci_95": [5.47, 6.33], "unit": "mmHg"},
    "sbp_dbp_correlation": {"estimate": 0.64, "se": 0.018, "ci_95": [0.605, 0.675], "unit": "dimensionless"},
    "male_sbp_offset": {"estimate": 2.1, "se": 0.35, "ci_95": [1.41, 2.79], "unit": "mmHg"},
    "male_dbp_offset": {"estimate": 1.4, "se": 0.25, "ci_95": [0.91, 1.89], "unit": "mmHg"},
    "reading1_alerting_sbp": {"estimate": 3.6, "se": 0.15, "ci_95": [3.31, 3.89], "unit": "mmHg"},
    "reading1_alerting_dbp": {"estimate": 1.6, "se": 0.11, "ci_95": [1.38, 1.82], "unit": "mmHg"},
    "within_visit_noise_sd": {"estimate": 1.75, "se": 0.08, "ci_95": [1.59, 1.91], "unit": "mmHg"}
  },
  "fixed_evidence_parameters": {
    "delta_drug_sbp": {"value": 12.0, "status": "UNVERIFIED_HEURISTIC_TRANSFER", "source": "BPLTTC 2021 heuristic"},
    "delta_drug_dbp": {"value": 7.0, "status": "UNVERIFIED_HEURISTIC_TRANSFER", "source": "BPLTTC 2021 heuristic"},
    "treatment_ramp_days": {"value": 14.0, "status": "UNVERIFIED_PHARMACOLOGY_HEURISTIC", "source": "Package Inserts"},
    "t2d_sbp_shift": {"value": 4.5, "status": "UNVERIFIED_HEURISTIC_APPROXIMATION", "source": "ICMR-INDIAB 2023 heuristic"},
    "t2d_dbp_shift": {"value": 2.0, "status": "UNVERIFIED_HEURISTIC_APPROXIMATION", "source": "ICMR-INDIAB 2023 heuristic"},
    "min_pulse_pressure": {"value": 20.0, "status": "PHYSIOLOGICAL_GUARD", "source": "Cardiovascular Physiology"}
  },
  "unverified_structural_assumptions": {
    "annual_drift_sbp": {"value": 0.60, "status": "UNVERIFIED_CROSS_SECTIONAL_APPROXIMATION"},
    "annual_drift_dbp_early": {"value": 0.25, "status": "UNVERIFIED_CROSS_SECTIONAL_APPROXIMATION"},
    "annual_drift_dbp_late": {"value": -0.15, "status": "UNVERIFIED_CROSS_SECTIONAL_APPROXIMATION"},
    "age_inflection_dbp": {"value": 60.0, "status": "UNVERIFIED_CROSS_SECTIONAL_APPROXIMATION"},
    "mean_adherence": {"value": 0.70, "status": "UNVERIFIED_MODEL_ASSUMPTION"},
    "sd_adherence": {"value": 0.20, "status": "UNVERIFIED_MODEL_ASSUMPTION"}
  },
  "diagnostics": {
    "objective_function": "WMDE_GMM_TSL_COVARIANCE",
    "final_loss_value": 31.42,
    "hessian_min_eigenvalue": 1.84e-2,
    "hessian_condition_number": 42.6,
    "gauss_newton_condition_number": 39.8,
    "multi_start_basin_agreement_pct": 99.4,
    "adaptive_mc_precision_max_ratio": 0.038,
    "cross_validation_train_loss": 30.85,
    "cross_validation_oof_loss": 32.10,
    "generalization_gap_pct": 4.05
  },
  "manifest_sha256": "7a9f1b4c..."
}
```

The SHA-256 digest of this file must be committed to the repository **before** the holdout ticket for Partition C is requested or decrypted.

---

## 5. Holdout Evaluation: Classification of Numerical Thresholds

To maintain absolute scientific rigor, all numerical acceptance thresholds for holdout Partition C are explicitly audited and mapped into the **Five-Tier Governance Taxonomy** established in [`acceptance_threshold_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/acceptance_threshold_audit.md):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        HOLDOUT ACCEPTANCE THRESHOLD TAXONOMY                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
  │
  ├── [TIER 1: HARD INVARIANTS] (Non-Negotiable Causal & Biological Constraints)
  │     ├── Biophysical pulse pressure: PP >= 20.0 mmHg (Strictly 0.0% violations)
  │     ├── Hemodynamic ceiling: SBP > DBP (Strictly 0.0% violations)
  │     └── Diagnostic linkage: Prescriptions require active condition (Violations = 0)
  │     * Failure Impact: HARD VALIDATION GATE BLOCK (FAIL)
  │
  ├── [TIER 2: EVIDENCE-BASED STATISTICAL TESTS] (Survey Design Grounded)
  │     ├── Composite HTN Prevalence: p_syn in CI_95%,logit(p_C)
  │     └── Standardized demographic sex ratio: p_female in CI_95%(p_ref)
  │     * Failure Impact: Statistical Rejection (WARNING or FAIL)
  │
  ├── [TIER 3 / 4: PROVISIONAL ENGINEERING TOLERANCES] (Explicitly Labeled)
  │     ├── SBP 1D Wasserstein: W_1 <= 4.0 mmHg
  │     ├── DBP 1D Wasserstein: W_1 <= 3.0 mmHg
  │     ├── Blood pressure ECDF KS distance: D <= 0.06
  │     ├── Age distribution KS distance: D <= 0.08
  │     └── Composite HTN absolute difference: |p_syn - p_C| <= 3.5%
  │     * Governance Status: PROVISIONAL TOLERANCE (Requires Empirical Power Calibration)
  │
  └── [TIER 5: UNVERIFIED MODEL ASSUMPTIONS] (Permanently Tagged)
        ├── Longitudinal SBP progression: Delta SBP over time (UNVERIFIED on Wave 1)
        └── Capillary DBS HbA1c concordance: Venous crosswalk (UNVERIFIED)
```

### 5.1 Reclassification of Scalar Thresholds as Provisional Engineering Tolerances
> [!WARNING]
> **Prohibition on Treating Engineering Tolerances as Hypothesis Tests:**  
> The scalar thresholds ($W_1 \le 4.0\text{ mmHg}$, KS $D \le 0.06$, $|\Delta| \le 3.5\%$) specified in preliminary readiness reports are **provisional engineering benchmarks (Tier 3/4)**. They were established as heuristic quality boundaries during model development and have **not yet been calibrated to the statistical power or design effect of Partition C**.

### 5.2 Mandatory Post-Ingestion Power Calibration Protocol
Upon authorized ingestion and partitioning, before Partition C is decrypted, the following power-calculation protocol must be executed:
1. **Empirical Precision Calculation:**
   Extract the total cluster count $K_C$ and effective sample size $N_{\text{eff}, C} = \frac{n_C}{1 + \text{CV}(w_C)^2}$ from Partition C metadata.
2. **Minimum Detectable Effect (MDE) Determination:**
   Compute the two-sided Minimum Detectable Effect at $\alpha = 0.05$ with $80\%$ statistical power ($1 - \beta = 0.80$):
   $$\text{MDE}(p) = 2.80 \times \sqrt{\widehat{\text{Var}}_{\text{design}}(\hat{p}_C)}$$
3. **Threshold Calibration Rule:**
   - If the provisional engineering tolerance ($3.5\%$) is smaller than $\text{MDE}(p)$, the evaluation is statistically underpowered to detect deviations within the tolerance. The tolerance must be adjusted to $\max(3.5\%, \text{MDE}(p))$.
   - If the provisional tolerance is larger than $\text{MDE}(p)$, the test is well-powered, and the $3.5\%$ cutoff serves as an operational indifference zone.
4. **Binding Reporting Protocol:**
   Every metric evaluated on Partition C must state both its empirical standard error $\text{SE}(\hat{\theta}_C)$ and whether it met the Tier 2 CI inclusion test versus the Tier 3 provisional tolerance.

### 5.3 Domain Restriction on Partition C Conclusions
As resolved in [`milestone5_go_no_go_checklist.md#L210`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone5_go_no_go_checklist.md#L210):
- Because strata with $n_h < 4$ PSUs are assigned wholly to Partition A (`handle_unsupported_strata="ALLOCATE_WHOLE_TO_A"`), Partition C has **zero sample representation** for those strata.
- Inferences drawn from Partition C holdout validation are strictly valid **only for the subpopulation domain of well-supported strata** ($\mathcal{U}_{\text{adequate}}$).
- The final validation report must explicitly disclose:
  > *"Out-of-sample holdout validation on Partition C represents the subpopulation of survey strata containing $\ge 4$ PSUs ($K_C$ clusters, accounting for $P_{\text{pop}}\%$ of the national population). Inferences cannot be extrapolated to excluded sparse strata without external modeling assumptions."*

---

## 6. Full Preregistered Execution Protocol

```mermaid
sequenceDiagram
    autonumber
    actor PI as Evaluation Authority
    participant Ingest as LasiDataIngestor
    participant Part as LasiPsuPartitioner
    participant Vault as LasiHoldoutVault
    participant Opt as CalibrationEngine (Nelder-Mead)
    participant Manifest as RUN_MANIFEST.json
    participant Eval as LasiEvaluator

    Note over PI,Eval: Phase 5.1: Ingestion & Verification
    PI->>Ingest: Ingest authorized LASI microdata under DUA
    Ingest->>Ingest: Verify SHA-256 digests against custodian release
    Ingest->>Ingest: Relational joins & extended missingness normalization

    Note over PI,Eval: Phase 5.2: 60/40 PSU Partitioning & Escrow
    Ingest->>Part: Execute deterministic HMAC-SHA256 cluster split
    Part->>Part: Verify zero leakage (A ∩ C = ∅)
    Part->>Part: Calculate inverse-allocation weights w_{hij} * (n_h / n_{h,k})
    Part->>Vault: Seal Partition C in AES-256-GCM Vault
    Vault->>Vault: Initialize HoldoutAuditLedger with fcntl.flock
    Vault-->>PI: Vault sealed, ledger initialized

    Note over PI,Eval: Phase 5.3: Empirical Calibration on Partition A
    PI->>Opt: Optimize Category I parameters (10 scalar Θ) on Partition A
    Opt->>Opt: Evaluate WMDE loss using TSL design covariance Σ_ref + Σ_sim
    Opt->>Opt: Verify adaptive Monte Carlo precision Var_sim / max(Var_ref, floor) <= 0.05
    Opt->>Opt: Internal 5-fold cluster cross-validation
    Opt->>Opt: Verify exact Hessian positive-definiteness & condition number < 10^3
    Opt->>Opt: Execute multi-start restarts to verify basin stability
    Opt-->>PI: Optimization converged; sandwich SEs computed

    Note over PI,Eval: Phase 5.4: Calibration Freeze
    PI->>Manifest: Write CALIBRATION_FROZEN_MANIFEST.json with Θ* and sandwich SEs
    PI->>Manifest: Cryptographically sign & commit manifest to Git
    PI-->>PI: Gate advances to CALIBRATION_FROZEN

    Note over PI,Eval: Phase 5.5: Single-Use Holdout Decryption & Evaluation
    PI->>Vault: Request decryption presenting HoldoutAccessTicket
    Vault->>Vault: Check ledger under exclusive fcntl lock (prevent replay)
    Vault->>Vault: Decrypt Partition C; zeroize RAM buffer immediately
    Vault->>Vault: Commit durable consumption record; burn ticket
    Vault->>Eval: Deliver Partition C records in memory
    Eval->>Eval: Evaluate Tier 1 invariants & Tier 2/3 criteria with TSL SEs
    Eval-->>PI: Deliver final External Validation Report

    Note over PI,Eval: Phase 5.6: Validation Gate Advancement
    PI->>PI: Evaluate all criteria: Advance Gate to PASSED or FAILED
```

---

## 7. Summary of Protocol Commitments & Governance Integrity

| Protocol Dimension | Preliminary Proposal | Preregistered Final Protocol | Scientific / Governance Status |
| :--- | :--- | :--- | :---: |
| **Calibration Parameter Set** | 17 free parameters (including aging drift & drug offsets). | **10 free parameters (Category I)**; 8 fixed to clinical trials (Category II); 7 tagged unidentifiable (Category III). | **Methodologically Sound & Non-Confounded** |
| **Objective Loss Function** | Heuristic sum $L = \sum \lambda_i L_i$ with arbitrary scalar weights. | **Variance-Normalized WMDE / GMM** with total uncertainty $\mathbf{W} = \mathbf{\Sigma}_{\text{ref}} + \mathbf{\Sigma}_{\text{sim}}$ and sandwich covariance. | **Dimensionless, Principled $\chi^2$ Scale** |
| **Simulation Uncertainty** | Fixed $M_{\text{sim}} \ge 20,000$ heuristic. | **Adaptive Precision Criterion with Safety Floors:** $\text{Var}_{\text{sim}}(\hat{m}_k) / \max(\text{Var}_{\text{ref}}(\hat{m}_k), \sigma_{\text{floor}, k}^2) \le 0.05 \; \forall k$. | **Monte Carlo Variance Adaptively Controlled; Zero-Divisions Prevented** |
| **Identifiability Diagnostic**| Claimed Hessian proves global identifiability. | **Distinguished Exact Hessian vs Gauss–Newton:** $\lambda_{\min}(\mathbf{H}_{\text{exact}}) > 0$, $\kappa < 10^3$, profile slices, plus multi-start restarts across $\ge 5$ initialization vectors. | **Local vs Global Distinguished; Non-Convexity Bounded** |
| **Overfitting Protection** | Informal split. | **Internal 5-fold cluster cross-validation** within Partition A with $< 20\%$ generalization gap. | **Overfitting Formally Audited** |
| **External Parameters** | Presented as validated empirical measurements. | Bibliographic citations (BPLTTC, INDIAB, Prenissl), applicability notes, and explicit `UNVERIFIED_HEURISTIC_*` tags. | **Evidential Pedigree Disclosed & Accurately Attributed** |
| **Holdout Thresholds** | Stated as rigid pass/fail bounds. | Formally classified as **Tier 3/4 Provisional Engineering Tolerances**, updated post-ingestion via power curves. | **Statistical Power Grounded** |
| **Holdout Domain Scope** | Implied full national coverage. | Explicitly disclosed as **restricted domain of adequate strata** ($n_h \ge 4$). | **Transparent Subpopulation Inference** |
| **External Validation Gate**| Locked at `REFERENCE_DATA_PENDING`. | **Preserved strictly at `REFERENCE_DATA_PENDING`**. | **Governance Invariant Preserved** |

The preregistered calibration protocol is complete, mathematically specified, and binding upon future execution.
