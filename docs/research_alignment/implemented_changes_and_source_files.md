# Implemented Changes and Affected Source Files

**Document ID:** `SYNAPSE-AUDIT-DELIV-05`  
**Date:** October 2026  
**Auditor:** SYNAPSE Model Credibility & Clinical Trajectory Audit Team  
**Focus Area:** Traceability Matrix of Code Modifications, Schemas, and Test Extensions  

---

## 1. Summary of Implemented Architectural Modifications

In accordance with the longitudinal clinical trajectory audit and validation objectives, four core areas of the SYNAPSE Phase 2 platform were incrementally extended:

1. **Discrete Clinical Pathway Extensions (`config/modules/`):**
   - **Hypertension Module (`hypertension.yaml`):** Replaced static maintenance loop with dynamic follow-up blood pressure measurement (`MeasureFollowUpBP`), probabilistic control bifurcation (60% controlled vs 40% uncontrolled), guideline-directed step-up dual combination therapy (Telmisartan 40mg `TEL-40`), and target-organ renal damage evaluation (`HypertensiveCKD_Onset`, `I12.9`).
   - **Type 2 Diabetes Module (`diabetes_t2.yaml`):** Removed dead-end `TerminalState`. Introduced continuous quarterly surveillance loop (`QuarterlySurveillanceDelay`), follow-up HbA1c re-measurement (`MeasureFollowUpHbA1c`), glycemic control bifurcation (45% controlled vs 55% uncontrolled), step-up oral hypoglycemic intensification (Glimepiride 1mg `GLIM-1`), and microvascular complication onset (`DiabeticNephropathyOnset`, `E11.2`).
2. **Actuarial Mortality Stepping & Person-Time Censoring (`synapse_simulator/`):**
   - Corrected the actuarial expected mortality derivation under Census of India SRS 2016–2020 Life Tables.
   - Refactored `DatasetEvaluator.evaluate_longitudinal()` in `evaluator.py` to compute individual right-censored person-time accounting for exact dates of death:
     $$\tau_i = \frac{\min(t_{\text{obs\_end}}, t_{\text{death}, i}) - t_{\text{obs\_start}}}{365.25}$$
3. **Independent Longitudinal Evaluator Metrics (`evaluator.py`):**
   - Added `long_treatment_intensification_rate`: Measures the proportion of treated chronic patients receiving stepped-up dual therapy over 2 years.
   - Added `long_chronic_complication_rate`: Measures target-organ secondary complications (`I12.9`, `E11.2`) emerging longitudinally.
4. **Automated Trajectory Test Suite (`tests/`):**
   - Added `tests/test_longitudinal_trajectories.py` verifying continuous follow-up loops, treatment step-up orders, right-censored person-time calculations, and mutual exclusivity of death events.

---

## 2. Traceability Matrix of Affected Files

| Source File Path | Component | Type of Change | Key Changes & Functions |
| :--- | :--- | :--- | :--- |
| `config/modules/hypertension.yaml` | Clinical Module Configuration | Configuration Refinement | Added `MeasureFollowUpBP`, `BPControlled`, `BPUncontrolled`, `PrescribeStepUpAntihypertensive`, `CheckRenalComplication`, `HypertensiveCKD_Onset`. |
| `config/modules/diabetes_t2.yaml` | Clinical Module Configuration | Configuration Refinement | Removed `TerminalState`. Added `MeasureFollowUpHbA1c`, `GlycemicControlled`, `GlycemicUncontrolled`, `PrescribeStepUpHypoglycemic`, `DiabeticComplicationEvaluation`, `DiabeticNephropathyOnset`. |
| `synapse_simulator/evaluation/evaluator.py` | Independent Evaluation Engine | Engine Refactoring | Implemented right-censored person-time calculation; added `long_treatment_intensification_rate` and `long_chronic_complication_rate`. |
| `synapse_simulator/evaluation/experiment.py` | Controlled Experiment Runner | Execution Integration | Maintained life-table background hazard stepping ($p_{\text{step}} = 1 - (1 - q_x)^{\Delta t / 365.25}$) and ensured zero post-mortem action generation. |
| `tests/test_longitudinal_trajectories.py` | Automated Validation Suite | New Test Suite | Added 4 automated integration tests for clinical loops, step-up therapy, person-time censoring, and competing risk invariants. |

---

## 3. Backward Compatibility and Invariant Verification

1. **Deterministic Reproducibility:** Every simulation run with an identical pseudo-random seed reproduces bit-identical outputs.
2. **Schema Invariance:** All 16 exported CSV schemas (`patients.csv`, `encounters.csv`, `conditions.csv`, `medications.csv`, `observations.csv`, `deaths.csv`, etc.) retain identical column headers and foreign key linkages.
3. **Safety Rule Precedence:** No probabilistic transition can bypass the clinical safety rule engine (e.g. contraindications and allergy vetoes remain absolute).
