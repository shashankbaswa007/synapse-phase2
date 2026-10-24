# SYNAPSE Phase 2B — Experimental Forward Hemodynamic Engine Implementation Report

**Document ID:** `SYNAPSE-REPORT-2026-FORWARD-HEMODYNAMICS-2B`  
**Classification:** Research Implementation, State-Space Architecture, and Determinism Verification  
**Target Repository:** `synapse-phase2`  
**Related Documents:**  
- [`docs/research_alignment/forward_disease_generation_architecture.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/forward_disease_generation_architecture.md)  
- [`docs/research_alignment/latent_bp_generation_clinical_realism_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/latent_bp_generation_clinical_realism_audit.md)  
- [`docs/research_alignment/point_in_time_state_integrity_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/point_in_time_state_integrity_audit.md)  
- [`docs/research_alignment/bp_measurement_error_model_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/bp_measurement_error_model_audit.md)  

**Current State Test Suite:** 285 passed, 0 failed in 8.88s (`.venv/bin/pytest`)  
**External Validation Gate Status:** `REFERENCE_DATA_PENDING` (Strictly Preserved)  

---

## 1. Executive Summary

This report documents the implementation of the first vertical slice of the **Forward Hemodynamic Engine** (`ForwardHemodynamicSimulator`) in SYNAPSE Phase 2B. 

Prior to Phase 2B, blood pressure generation in the community assessment pathway followed an inverted causal architecture: administrative disease diagnosis codes (`"I10"`) and clinical treatment flags (`is_treated`) directly selected segmented uniform blood pressure distributions ($[110, 135]$, $[120, 150]$, and $[145, 168]\text{ mmHg}$). This inverted structure introduced unphysical distribution gaps, artificially enforced perfect diagnostic specificity, and prevented realistic biological gradients across age and comorbidities.

### Key Deliverables in Phase 2B:
1. **Isolated Forward State-Space Engine:** Implemented [`ForwardHemodynamicSimulator`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/forward_hemodynamics.py) in `synapse_simulator/datagen/forward_hemodynamics.py`, providing a continuous biophysical representation of unobserved resting blood pressure ($\text{SBP}_t$, $\text{DBP}_t$, pulse pressure).
2. **Deterministic Random Stream Derivation:** Engineered isolated 32-bit unsigned PRNG stream generation via SHA-256 (`derive_hemodynamic_seed`), eliminating PRNG stream cross-talk and side-effects on legacy simulations without relying on Python's randomized built-in `hash()`.
3. **Strict Opt-In Configuration Toggle:** Added `hemodynamic_engine_mode` supporting `LEGACY_CONDITIONAL` (default) and `FORWARD_STATE_SPACE`. All legacy pipelines, experiments, and regression tests remain 100% stable and unchanged under default configuration.
4. **Physiological Evolution Function:** Modeled continuous vascular stiffening drift ($\beta_{\text{age, SBP}} = 0.60\text{ mmHg/year}$, bilinear DBP inflection at age 60, and pulse pressure widening guard $\ge 20\text{ mmHg}$).
5. **Decoupled Measurement Protocol Integration:** Connected continuous latent states directly to the existing [`BpMeasurementProtocolSimulator`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/bp_measurement.py) without mutating the latent biological state.
6. **Explicit Evidential Status Registry:** All provisional parameters are tracked via an `EvidentialStatus` metadata registry (`LITERATURE_CALIBRATED`, `PROVISIONAL_DEFAULT`, `PHYSIOLOGICAL_GUARD`), ensuring that software tests do not claim unwarranted empirical calibration.
7. **Comprehensive Deterministic Testing:** Added 12 deterministic unit and integration tests covering all 10 mandated requirements in [`tests/test_forward_hemodynamics.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_forward_hemodynamics.py), bringing the test suite from 273 to 285 passing tests.

---

## 2. Architecture and Implemented Interfaces

The forward state-space architecture establishes a strict separation between biological physiology, observation protocols, diagnostic classifications, and treatment feedback:

```mermaid
flowchart TD
    subgraph PatientContextLayer [1. Patient Biology & Demographic Context]
        PAT[PatientContext: age, gender, birth_date, baseline_conditions]
    end

    subgraph DeterministicEntropyLayer [2. Isolated Cryptographic PRNG]
        SEED[derive_hemodynamic_seed: SHA-256(base_seed : stream_id : patient_id)]
        PRNG[Dedicated Patient random.Random]
        SEED --> PRNG
    end

    subgraph ForwardHemodynamicEngine [3. Forward Hemodynamic Engine (Phase 2B)]
        CFG[ForwardHemodynamicConfig: mode, anchors, drift, guards, evidential_metadata]
        BL[initialize_patient_baseline: Correlated Bivariate Normal Draw]
        EVOLVE[get_latent_state_at: Continuous Vascular Aging & Comorbidity Trajectory]
        STATE[LatentHemodynamicState: latent_sbp, latent_dbp, pulse_pressure, provenance]
        
        PAT & PRNG & CFG --> BL
        BL --> EVOLVE
        EVOLVE --> STATE
    end

    subgraph ObservationProtocolLayer [4. Observation & Measurement Protocol]
        PROTO[BpMeasurementProtocolSimulator: LASI Tri-Measurement or Single-Reading]
        READINGS[CommunityBpReading 1, 2, 3: Situational Alerting + Within-Visit AR(1) Noise]
        ANALYSIS[Protocol Analysis Result: Mean of Readings 2 and 3]
        
        STATE & PROTO --> READINGS
        READINGS --> ANALYSIS
    end

    subgraph CommunitySurveyLayer [5. Independent Survey Record]
        COMM[CommunityAssessment: sbp, dbp, pulse_pressure, protocol_id, survey_weight]
        ANALYSIS --> COMM
    end
```

### 2.1 Implemented Classes and Interfaces

1. **[`EvidentialStatus`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/forward_hemodynamics.py#L40-L46) (Enum):**
   Categorizes parameter provenance into:
   - `LITERATURE_CALIBRATED`: Grounded in epidemiological cohort literature (e.g., young adult population anchors).
   - `PROVISIONAL_DEFAULT`: Plausible heuristic defaults pending empirical microdata calibration.
   - `PHYSIOLOGICAL_GUARD`: Absolute biophysical bounds (e.g., minimum pulse pressure $\ge 20\text{ mmHg}$).
   - `STRUCTURAL_PLACEHOLDER`: Reserved interface parameters for subsequent phases.

2. **[`ForwardHemodynamicConfig`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/forward_hemodynamics.py#L52-L172) (Pydantic Model):**
   Controls engine mode, baseline anchors, physiological safeguards, aging drift coefficients, sex/comorbidity shifts, and registers parameter provenance. Enforces validation that `engine_mode \in {"LEGACY_CONDITIONAL", "FORWARD_STATE_SPACE"}`.

3. **[`LatentHemodynamicState`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/forward_hemodynamics.py#L178-L203) (Pydantic Model):**
   Authoritative representation of true resting biological hemodynamics at an exact simulation timestamp:
   - `patient_id: str`
   - `timestamp: datetime`
   - `latent_sbp: float`, `latent_dbp: float`, `pulse_pressure: float`
   - `baseline_sbp: float`, `baseline_dbp: float`
   - `cumulative_age_drift_sbp: float`, `cumulative_age_drift_dbp: float`
   - `comorbidity_shift_sbp: float`, `comorbidity_shift_dbp: float`
   - `treatment_effect_sbp: float`, `treatment_effect_dbp: float` (reserved for Phase 2C)
   - `provenance: str = "FORWARD_HEMODYNAMIC_SIMULATOR"`

4. **[`derive_hemodynamic_seed`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/forward_hemodynamics.py#L209-L224) (Function):**
   Generates a stable 32-bit unsigned integer using `hashlib.sha256(f"{base_seed}:{stream_id}:{patient_id}".encode("utf-8")).digest()[:4]`. Completely independent of Python's randomized `hash()`.

5. **[`ForwardHemodynamicSimulator`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/forward_hemodynamics.py#L230-L445) (Class):**
   - `initialize_patient_baseline(patient, observation_start)`: Generates baseline resting values from correlated bivariate normal distribution conditioned on sex and baseline diabetes comorbidity.
   - `get_latent_state_at(patient, target_time, observation_start, baseline_state)`: Evaluates continuous trajectory at `target_time` incorporating longitudinal aging drift and dynamic comorbidity onset.
   - `observe(latent_state, protocol_simulator, assessment_id, pat_rng)`: Feeds latent continuous blood pressure into measurement protocol without mutating the latent biological state.

---

## 3. Configuration and Feature Flag Isolation

To preserve complete backward compatibility, `LEGACY_CONDITIONAL` remains the strict default across all configuration models.

| Configuration Model | Field Name | Supported Values | Default Value | Validation Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `ForwardHemodynamicConfig` | `engine_mode` | `LEGACY_CONDITIONAL`, `FORWARD_STATE_SPACE` | `LEGACY_CONDITIONAL` | Raises `ValueError` on unsupported mode |
| `CommunityAssessmentConfig` | `hemodynamic_engine_mode` | `LEGACY_CONDITIONAL`, `FORWARD_STATE_SPACE` | `LEGACY_CONDITIONAL` | Raises `ValueError` on unsupported mode |
| `ExperimentConfig` | `hemodynamic_engine_mode` | `LEGACY_CONDITIONAL`, `FORWARD_STATE_SPACE` | `LEGACY_CONDITIONAL` | Raises `ValueError` on unsupported mode |

### Default Legacy Invariance Guarantee
When `hemodynamic_engine_mode` is omitted or set to `LEGACY_CONDITIONAL`:
- `CommunityAssessmentGenerator.forward_simulator` is set to `None`.
- The generation loop executes the legacy branch (`is_condition_active_at("I10")` + `pat_rng.uniform(...)`).
- The order and values of calls to `pat_rng` are bit-for-bit identical to the legacy implementation.
- All 273 legacy regression tests pass without deviation.

---

## 4. State Ownership and Temporal Semantics

### 4.1 Single Source of Truth
The architecture guarantees that authoritative physiological state is not duplicated across competing modules:
- The forward engine produces an immutable `LatentHemodynamicState` snapshot for any requested `(patient, timestamp)` tuple.
- In `CommunityAssessmentGenerator`, when `FORWARD_STATE_SPACE` is active, latent states are collected in `self.latent_hemodynamic_states[patient_id]`.
- The measurement protocol receives latent values as read-only inputs, applies situational alerting and noise, and returns a distinct `BpProtocolResult`.
- The latent physiological state is never modified or overwritten by the measurement protocol.

### 4.2 Temporal Semantics and Point-in-Time Integrity
The evaluation function `get_latent_state_at(patient, target_time)` respects strict point-in-time boundaries:
1. **Longitudinal Vascular Aging Drift:**
   $$\Delta t = \frac{\text{target\_time} - \text{baseline\_time}}{365.25\text{ days}}$$
   $$\text{Drift}_{\text{SBP}} = \beta_{\text{age, SBP}} \cdot \Delta t$$
   $$\text{Drift}_{\text{DBP}} = \begin{cases}
   \beta_{\text{age, DBP, early}} \cdot \Delta t & \text{if } \text{Age}_t \le 60 \\
   \beta_{\text{age, DBP, late}} \cdot \Delta t & \text{if } \text{Age}_0 \ge 60 \\
   \beta_{\text{age, DBP, early}} \cdot (60 - \text{Age}_0) + \beta_{\text{age, DBP, late}} \cdot (\text{Age}_t - 60) & \text{otherwise}
   \end{cases}$$
2. **Point-in-Time Comorbidity Invariance:**
   Incident diabetes onset occurring strictly after `target_time` has zero effect on the latent state at `target_time`.
3. **Future Diagnosis and Prescription Invariance:**
   Incident hypertension diagnoses (`"I10"`) and future medication prescriptions have zero influence on latent blood pressure generation.

---

## 5. Latent Versus Observed Blood Pressure

A fundamental accomplishment of Phase 2B is the strict separation between latent biophysical reality and observed clinical measurement:

| Dimension | Latent Hemodynamic State (`LatentHemodynamicState`) | Observed Reading (`CommunityBpReading`) | Analysis Measurement (`CommunityAssessment`) |
| :--- | :--- | :--- | :--- |
| **Concept** | True unobserved resting arterial pressure | Physical cuff inflation reading at a single instant | Derived clinical survey summary metric |
| **Alerting Effect** | None ($0.0\text{ mmHg}$) | Reading 1 includes white-coat alert ($+3.0$ to $+8.0\text{ mmHg}$) | Attenuated (Readings 2 & 3 averaged) |
| **Measurement Error** | None (pure biological signal) | Includes cuff inaccuracy ($\sigma_{\text{cuff}}$) and biological noise | Averaging reduces random noise variance by $50\%$ |
| **Diagnostic Influence**| None (causes downstream diagnosis) | Does not contain diagnostic labels | Subject to thresholding ($\ge 140/90\text{ mmHg}$) |
| **Data Table** | In-memory latent trajectory store | `community_bp_readings.csv` | `community_assessments.csv` |
| **Provenance Tag** | `FORWARD_HEMODYNAMIC_SIMULATOR` | `COMMUNITY_HEALTH_ASSESSMENT_LAYER` | `COMMUNITY_HEALTH_ASSESSMENT_LAYER` |

---

## 6. Model Parameters and Evidential Status Registry

In accordance with Phase 2 governance rules, no provisional parameter is claimed to be empirically calibrated without verified external reference data:

| Parameter Key | Default Value | Evidential Status | Clinical / Biophysical Rationale |
| :--- | :--- | :--- | :--- |
| `mean_sbp_anchor` | $120.0\text{ mmHg}$ | `LITERATURE_CALIBRATED` | Normotensive young adult population mean resting SBP anchor (AHA/ACC, JNC-8 baseline). |
| `sd_sbp_anchor` | $9.0\text{ mmHg}$ | `LITERATURE_CALIBRATED` | Between-person standard deviation of resting SBP in non-hypertensive reference cohorts. |
| `mean_dbp_anchor` | $78.0\text{ mmHg}$ | `LITERATURE_CALIBRATED` | Normotensive young adult population mean resting DBP anchor. |
| `sd_dbp_anchor` | $6.0\text{ mmHg}$ | `LITERATURE_CALIBRATED` | Between-person standard deviation of resting DBP in non-hypertensive reference cohorts. |
| `sbp_dbp_correlation` | $0.65$ | `LITERATURE_CALIBRATED` | Physiological correlation between resting systolic and diastolic pressures. |
| `min_pulse_pressure` | $20.0\text{ mmHg}$ | `PHYSIOLOGICAL_GUARD` | Incompressibility of intravascular blood column; prevents unphysical hemodynamic collapse. |
| `min_sbp` / `max_sbp` | $70.0 / 260.0\text{ mmHg}$ | `PHYSIOLOGICAL_GUARD` | Severe shock floor / extreme hypertensive crisis ceiling. |
| `min_dbp` / `max_dbp` | $40.0 / 150.0\text{ mmHg}$ | `PHYSIOLOGICAL_GUARD` | Diastolic coronary perfusion limit / extreme diastolic ceiling. |
| `annual_drift_sbp` | $0.60\text{ mmHg/yr}$ | `PROVISIONAL_DEFAULT` | Heuristic annual rate of SBP increase from aortic stiffening; pending LASI calibration. |
| `annual_drift_dbp_early`| $0.25\text{ mmHg/yr}$ | `PROVISIONAL_DEFAULT` | Heuristic annual rate of DBP rise in early adulthood; pending LASI calibration. |
| `annual_drift_dbp_late` | $-0.15\text{ mmHg/yr}$ | `PROVISIONAL_DEFAULT` | Heuristic rate of late-life DBP decline causing pulse pressure widening; pending calibration. |
| `age_inflection_dbp` | $60.0\text{ years}$ | `PROVISIONAL_DEFAULT` | Age at which DBP plateaus in epidemiological literature (Franklin et al., Circulation 1997). |
| `t2d_sbp_shift` | $+4.5\text{ mmHg}$ | `PROVISIONAL_DEFAULT` | Hemodynamic shift from arterial stiffness in diabetes; pending microdata calibration. |
| `t2d_dbp_shift` | $+2.0\text{ mmHg}$ | `PROVISIONAL_DEFAULT` | Hemodynamic shift in diastolic pressure in diabetes; pending microdata calibration. |
| `male_sbp_offset` | $+2.0\text{ mmHg}$ | `PROVISIONAL_DEFAULT` | Young/middle-age male hemodynamic offset; pending microdata calibration. |
| `male_dbp_offset` | $+1.5\text{ mmHg}$ | `PROVISIONAL_DEFAULT` | Young/middle-age male diastolic offset; pending microdata calibration. |

---

## 7. Scope Boundaries: Implemented vs. Deferred Functionality

```
+-----------------------------------------------------------------------------------+
| SYNAPSE Phase 2 Forward Architecture Scope Matrix                                 |
+-----------------------------------------------------------------------------------+
| COMPONENT                                  | STATUS     | TARGET PHASE            |
+--------------------------------------------+------------+-------------------------+
| Feature flag toggle (LEGACY vs FORWARD)    | COMPLETE   | Phase 2B (Current)      |
| Isolated SHA-256 PRNG stream derivation    | COMPLETE   | Phase 2B (Current)      |
| Correlated bivariate normal latent anchor  | COMPLETE   | Phase 2B (Current)      |
| Longitudinal vascular aging drift          | COMPLETE   | Phase 2B (Current)      |
| Protocol simulator integration             | COMPLETE   | Phase 2B (Current)      |
| Evidential status provenance registry      | COMPLETE   | Phase 2B (Current)      |
| ExperimentRunner integration & manifest    | COMPLETE   | Phase 2B (Current)      |
| 10-requirement regression test suite       | COMPLETE   | Phase 2B (Current)      |
+--------------------------------------------+------------+-------------------------+
| Multi-encounter clinical diagnosis rules   | DEFERRED   | Phase 2C                |
| Pharmacodynamic treatment response loop    | DEFERRED   | Phase 2C                |
| Medication adherence modulation (theta)    | DEFERRED   | Phase 2C                |
| Empirical LASI Wave 1 microdata calibration| DEFERRED   | Phase 2D                |
| External validation gate promotion         | DEFERRED   | Phase 2D                |
+-----------------------------------------------------------------------------------+
```

---

## 8. Verification Results (Task 7 & Final Verification)

### 8.1 Test Suite Execution
The test suite was executed using `.venv/bin/pytest`:

```bash
$ .venv/bin/pytest
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/shashi/synapse/synapse-phase2
plugins: Faker-40.43.0
collected 285 items

tests/test_bp_measurement_protocol.py .........................          [  8%]
tests/test_clinical_modules.py ......                                    [ 10%]
tests/test_community_assessment_audit.py ............................... [ 21%]
....                                                                     [ 23%]
tests/test_data_integrity_temporal_consistency.py ...............        [ 28%]
tests/test_datagen.py ...                                                [ 29%]
tests/test_determinism.py ..........                                     [ 32%]
tests/test_dispatcher.py .                                               [ 33%]
tests/test_end_to_end_acceptance.py .                                    [ 33%]
tests/test_evaluation_framework.py ....................                  [ 40%]
tests/test_evaluation_mutations.py ......                                [ 42%]
tests/test_event_queue.py ...                                            [ 43%]
tests/test_forward_hemodynamics.py ............                          [ 48%]
tests/test_full_simulation.py .                                          [ 48%]
tests/test_lab_rad_finance_rules.py ...                                  [ 49%]
tests/test_lasi_pipeline.py ..........................................   [ 64%]
tests/test_longitudinal_export.py ..                                     [ 64%]
tests/test_longitudinal_trajectories.py ....                             [ 66%]
tests/test_orchestrator.py ..                                            [ 67%]
tests/test_person_time_and_censoring.py .......                          [ 69%]
tests/test_phase2_csv_export.py ...                                      [ 70%]
tests/test_population_profile.py .....                                   [ 72%]
tests/test_population_validator.py .....                                 [ 74%]
tests/test_pubmed_datagen_integration.py ........                        [ 76%]
tests/test_pubmed_treatment_architecture.py ........                     [ 79%]
tests/test_root_cause_corrections.py ..........                          [ 83%]
tests/test_rule_engine.py ....                                           [ 84%]
tests/test_solid_principles.py .....                                     [ 86%]
tests/test_stage6_clock_scheduler.py ...                                 [ 87%]
tests/test_stage6_domain_events.py ..                                    [ 88%]
tests/test_stage6_loop_failure_protection.py ..                          [ 88%]
tests/test_stage6_ordering_causation.py ..                               [ 89%]
tests/test_stage6_reproducibility.py .                                   [ 89%]
tests/test_stage6_small_simulation.py .                                  [ 90%]
tests/test_stage7_cross_department.py .                                  [ 90%]
tests/test_stage7_patient_journeys.py .                                  [ 90%]
tests/test_stage7_scale.py .                                             [ 91%]
tests/test_stage7_workflows.py ..                                        [ 91%]
tests/test_stage9_billing.py .                                           [ 92%]
tests/test_stage9_diagnostics.py .                                       [ 92%]
tests/test_stage9_discharge.py .                                         [ 92%]
tests/test_stage9_integrity.py .                                         [ 93%]
tests/test_stage9_persistence.py ..                                      [ 94%]
tests/test_stage9_prescription.py .                                      [ 94%]
tests/test_state_machines.py .......                                     [ 96%]
tests/test_state_manager.py ....                                         [ 98%]
tests/test_validation_gate.py .....                                      [100%]

============================= 285 passed in 8.88s ==============================
```

### 8.2 Summary of Test Coverage for Task 7 Requirements

| Requirement | Test Function in [`tests/test_forward_hemodynamics.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_forward_hemodynamics.py) | Verification Status |
| :--- | :--- | :--- |
| **1. Reproducible latent-state initialization** | `test_req1_reproducible_latent_state_initialization` | PASS |
| **2. Independent patient PRNG streams** | `test_req2_independent_random_streams_across_patients` | PASS |
| **3. Invalid engine configuration rejected** | `test_req3_invalid_engine_configuration_rejected` | PASS |
| **4. Legacy mode remains default** | `test_req4_legacy_mode_remains_default` | PASS |
| **5. Legacy outputs unchanged & stream isolation**| `test_req5_legacy_outputs_unchanged_and_prng_isolation` | PASS |
| **6. Latent state distinct from observed values** | `test_req6_latent_state_distinct_from_observed_measurements` | PASS |
| **7. Future diagnoses/Rx invariance** | `test_req7_future_diagnoses_and_prescriptions_do_not_alter_latent_state`| PASS |
| **8. Repeated evaluation consistency** | `test_req8_repeated_evaluation_at_same_timestamp_consistent` | PASS |
| **9. Temporal evolution semantics & guards** | `test_req9_evolution_applied_according_to_temporal_semantics` | PASS |
| **10. Protocol integration & non-mutation** | `test_req10_bp_protocol_integration_and_invariance` | PASS |
| **Provenance transparency** | `test_evidential_metadata_and_provenance_transparency` | PASS |
| **End-to-End ExperimentRunner integration** | `test_experiment_runner_forward_hemodynamics_integration` | PASS |

---

## 9. Known Limitations and Pre-Calibration Blockers

While Phase 2B establishes the forward hemodynamic engine interface, several scientific and architectural prerequisites remain before `FORWARD_STATE_SPACE` can be promoted to the default production engine:

1. **Absence of Pharmacodynamic Treatment Feedback:**
   In Phase 2B, `treatment_effect_sbp` and `treatment_effect_dbp` are fixed at $0.0\text{ mmHg}$. Prescribed antihypertensive medications do not yet lower blood pressure continuously; this requires Phase 2C.
2. **Clinical Diagnosis Still Driven by Discrete Encounter Rules:**
   `hypertension.yaml` still transitions to `HypertensionOnset` via discrete transition rates rather than reading the patient's continuous latent blood pressure.
3. **Provisional Demographic and Aging Coefficients:**
   The annual drift coefficient ($0.60\text{ mmHg/year}$) and comorbidity shift ($+4.5\text{ mmHg}$) are heuristic placeholders from international literature and must be calibrated against Indian national survey microdata (LASI Wave 1).
4. **External Validation Gate Constraint:**
   The external validation gate remains strictly at **`REFERENCE_DATA_PENDING`**. Synthetic fixtures must not be represented as genuine external empirical data.
