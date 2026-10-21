# List of Justified Model Corrections and Governance Decisions

**Audit Phase:** SYNAPSE Phase 2 Research Validation & Credibility Audit  
**Implementation Standard:** Scientific Integrity First; No Artificial "Scorecard Tuning"  
**Codebase Files Modified:**
- `synapse_simulator/evaluation/experiment.py`
- `synapse_simulator/evaluation/evaluator.py`
- `tests/test_evaluation_framework.py`

---

## 1. Summary of Model and Evaluator Corrections

In accordance with the core scientific directive (*"Investigate discrepancies before calibrating them, verify reference definitions before comparing them, and do not lower incidence probabilities unless evidence demonstrates incidence is the source of the error"*), four controlled corrections were executed.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ JUSTIFIED CORRECTIONS SUMMARY:                                              │
│                                                                             │
│ 1. Life-Table Background Mortality Stepping:                                │
│    Integrated Census SRS annual qx stepping in discrete-event loop.         │
│    Result: Expected deaths restored to ~15 per 500 patients / 2 years.      │
│                                                                             │
│ 2. Dual Reporting of Baseline Point vs. Cumulative Period Prevalence:        │
│    Isolates baseline point prevalence (t=0) from longitudinal accumulation. │
│    Result: Resolves hypertension & diabetes cross-sectional comparisons.    │
│                                                                             │
│ 3. Pharmacotherapy Conformance Reclassification:                            │
│    Formally relabeled metrics as "Algorithmic Guideline Rule Conformance".   │
│    Result: Distinguishes generator state-machine compliance from fidelity.  │
│                                                                             │
│ 4. Retention of Documented Prospective Incidence Hazards:                   │
│    Explicitly REJECTED lowering transition weights (lambda = 0.035/yr).     │
│    Result: Preserves epidemiological grounding from CURES/CCDC studies.     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Technical Specifications of Implemented Corrections

### Correction 1: Background Life-Table Mortality Stepping
- **Component:** `synapse_simulator/evaluation/experiment.py`
- **Defect Identified:** `PopulationSampler.get_annual_mortality_rate(age, sex)` was previously defined but never called during the longitudinal stepping loop. Consequently, all non-hypertensive patients were immortal, and expected deaths across 500 patients over 2 years was depressed from $\mu = 14.12$ down to 2 (AMI only).
- **Justified Solution:**
  Implemented discrete life-table mortality hazard stepping:
  $$p_{\text{step}}(\Delta t) = 1 - (1 - q_x)^{\frac{\Delta t}{365.25}}$$
  When a patient dies:
  1. `patient.is_alive = False`
  2. `patient.death_date = curr_time`
  3. Terminal death event recorded in `runner.longitudinal_deaths` (`cause_code: "R99"`).
  4. Current step terminates with `continue`, and subsequent encounters are permanently blocked.
- **Empirical Validation:**
  Across 5 seeds ($N=500$, 24 months), observed mean deaths is **$15.00 \pm 5.96$**, aligning with the actuarial expectation of **$14.12\text{ deaths}$**. Layer 1 post-mortem violations remain strictly **$0$**.

---

### Correction 2: Disentangling Baseline Point from Cumulative Period Prevalence
- **Component:** `synapse_simulator/evaluation/evaluator.py`
- **Defect Identified:** The evaluator was comparing a 2-year cumulative period prevalence (which accumulates 2 years of incident cases with zero chronic disease remission) against cross-sectional point prevalence survey benchmarks (ICMR-INDIAB 2023: 30.70% for HTN, 11.40% for T2D).
- **Justified Solution:**
  The evaluator pre-computes diagnosis encounter timestamps ($t_{\text{enc}}$) to separate baseline-diagnosed cases ($t_{\text{enc}} \le t_{\text{start}} + 31\text{ days}$) from subsequent incident cases:
  - `acceptance_threshold["baseline_point_cases"]`: Number of adult cases diagnosed at baseline.
  - `acceptance_threshold["baseline_point_prevalence_pct"]`: Point prevalence at $t=0$, directly comparable to the cross-sectional survey benchmark ($30.70\%$).
  - `acceptance_threshold["incident_cases"]`: Count of longitudinal incident onsets.
  - `acceptance_threshold["incident_attack_rate_pct"]`: 2-year prospective incidence rate.
- **Empirical Validation:**
  In $N=500$ (Seed 42), the breakdown is verified:
  - Baseline HTN Point Prevalence: **$34.90\%$** (sampling variation around $30.70\%$)
  - Incident HTN Attack Rate: **$4.40\%$** (matching theoretical $4.68\%$)
  - Final Cumulative Period Prevalence: **$39.30\%$**

---

### Correction 3: Pharmacotherapy Rule Conformance Relabeling
- **Component:** `synapse_simulator/evaluation/evaluator.py`
- **Defect Identified:** Reported $100\%$ treatment alignment was described as "Treatment Guideline Alignment", implying high real-world clinical prescribing fidelity. In reality, it only measured that the deterministic state machine executed without branching.
- **Justified Solution:**
  1. Relabeled `metric_name` to:
     - `Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Antihypertensive Therapy)`
     - `Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Oral Hypoglycemic Therapy)`
  2. Updated `known_limitations` metadata to state:
     > *"Measures algorithmic rule compliance rather than verified real-world prescribing fidelity (empirical real-world monotherapy alignment in Indian surveys is ~45–65%)."*
  3. Formally locked `rx_adherence_assumption` to status **`UNVERIFIED`**.

---

### Correction 4: Rejection of Artificial Incidence Down-Calibration
- **Component:** `config/modules/hypertension.yaml` and `config/modules/diabetes_t2.yaml`
- **Audited Proposal:** An intuitive suggestion to lower the annual hypertension incidence probability from $0.0344$ to $\sim 0.005$ to artificially force the 2-year period prevalence down to $30.70\%$.
- **Justified Decision:** **REJECTED.**
  Epidemiological evidence from the CURES prospective cohort study and Prabhakaran et al. (JAHA 2017) proves that the annual incidence hazard in Indian adults is $\lambda = 0.035$/year ($3.44\%$/year). Lowering this parameter would corrupt the generator's longitudinal incidence validity solely to mask a cross-sectional vs. period prevalence definitional mismatch.
