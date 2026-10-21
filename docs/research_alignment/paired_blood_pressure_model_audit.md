# Paired Blood Pressure Model Audit

**Project:** SYNAPSE Phase 2 — Synthea-Inspired Synthetic Healthcare Generation  
**Document ID:** `DOC-RES-LASI-008`  
**Focus Area:** Clinical State Machine Extension, Paired Blood Pressure Architecture, and Physiological Verification  
**Date:** 2026-10-21  
**Git Revision:** `c71a39d`  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary

In previous releases of SYNAPSE Phase 2, the external evaluation report revealed an asymmetry in vital sign telemetry: while 863 longitudinal Systolic Blood Pressure (SBP) observations were exported across 235 older adults, **zero** Diastolic Blood Pressure (DBP) observations were emitted or exported into `observations.csv`.

This audit documents the root cause, architectural redesign, implementation, and physiological validation of a **paired blood pressure observation pathway**. Rather than creating an artificial export-only shim or computing DBP using arbitrary scalar fractions (e.g. $0.65 \times \text{SBP}$), we extended the core clinical module state machine and runner engine. Paired blood pressure observations now retain identical patient IDs, encounter IDs, and timestamps, respect physiological pulse pressure bounds, and preserve existing longitudinal clinical transitions without altering disease prevalence, demographic weights, or treatment rules.

---

## 2. Root Cause Analysis of the DBP Export Gap

An exhaustive trace across the six architectural layers from generation to evaluation identified the exact locus of the defect:

```
[1. Clinical Generator / Modules]
        │
        ├── OPD Vitals Generator (clinical_generator.py) -> generates (sbp, dbp) for acute encounters
        │                                                    (isolated to consultation payloads)
        └── Longitudinal Module Engine (hypertension.yaml) -> DEFINED ONLY 'SBP' OBSERVATIONS
                                                               (NO DBP state defined in state machine)
        ▼
[2. Module Runner (engine.py)]
        │
        └── runner.longitudinal_observations -> accumulated ONLY SBP records
        ▼
[3. CSV Exporter (csv_exporter.py)]
        │
        └── Exported runner.longitudinal_observations verbatim to observations.csv
        ▼
[4. Relational CSV Output (observations.csv)]
        │
        └── Contained SBP, Glucose, HbA1c; ZERO longitudinal DBP rows
        ▼
[5. LASI Evaluator (evaluator.py)]
        │
        ├── SBP: 863 rows -> evaluated
        └── DBP: 0 rows -> triggered INSUFFICIENT_SAMPLE_SIZE
```

### Key Defect Findings:
1. **Module State Definition Omission:** In `config/modules/hypertension.yaml`, the `RecordBloodPressure` and `MeasureFollowUpBP` states defined `type: Observation` with `observation_code: SBP`. No corresponding state or parameter existed for DBP.
2. **Export Faithfulness:** `CSVExporter` in `synapse_simulator/exporter/csv_exporter.py` was operating correctly; it serialized exactly what `ClinicalModuleRunner` recorded. The export gap was an upstream simulation omission.
3. **Rejection of Synthetic Formula Fabrication:** Calculating DBP as a fixed multiplier of SBP (e.g. $\text{DBP} = k \times \text{SBP}$) was strictly rejected under research alignment principles. Such deterministic mathematical coupling creates artifactual correlation ($r=1.0$), destroys biological pulse pressure variance, and violates clinical realism.

---

## 3. Paired Blood Pressure Architectural Representation

To support paired observations without duplicating encounters or generating synthetic records solely to satisfy the evaluator, the clinical data model was extended to allow an observation state to declare a paired component:

### 3.1 Data Model Extension (`synapse_simulator/modules/models.py`)
`ModuleState` was extended with optional paired observation fields:
* `paired_observation_code: Optional[str]`: Primary code (e.g. `"DBP"`).
* `paired_observation_name: Optional[str]`: Human-readable name (e.g. `"Diastolic Blood Pressure"`).
* `paired_observation_unit: Optional[str]`: Units of measure (e.g. `"mmHg"`).
* `paired_observation_value: Optional[float]`: Deterministic value (if fixed).
* `paired_observation_min: Optional[float]`: Lower sampling bound (e.g. $90.0$ mmHg for baseline stage 1/2 HTN, $75.0$ mmHg for follow-up).
* `paired_observation_max: Optional[float]`: Upper sampling bound (e.g. $104.0$ mmHg for baseline, $100.0$ mmHg for follow-up).

### 3.2 State Machine YAML Definition (`config/modules/hypertension.yaml`)
Both hypertensive measurement states were updated with paired DBP declarations:

```yaml
  RecordBloodPressure:
    name: "RecordBloodPressure"
    type: "Observation"
    observation_code: "SBP"
    observation_name: "Systolic Blood Pressure"
    observation_unit: "mmHg"
    observation_min: 145.0
    observation_max: 168.0
    paired_observation_code: "DBP"
    paired_observation_name: "Diastolic Blood Pressure"
    paired_observation_unit: "mmHg"
    paired_observation_min: 90.0
    paired_observation_max: 104.0
    direct_transition: "InitiateHypertensionCarePlan"

  MeasureFollowUpBP:
    name: "MeasureFollowUpBP"
    type: "Observation"
    observation_code: "SBP"
    observation_name: "Systolic Blood Pressure"
    observation_unit: "mmHg"
    observation_min: 120.0
    observation_max: 160.0
    paired_observation_code: "DBP"
    paired_observation_name: "Diastolic Blood Pressure"
    paired_observation_unit: "mmHg"
    paired_observation_min: 75.0
    paired_observation_max: 100.0
    distributed_transition:
      - to: "BPControlled"
        weight: 0.60
      - to: "BPUncontrolled"
        weight: 0.40
```

### 3.3 Execution Engine Implementation (`synapse_simulator/modules/engine.py`)
In `_execute_state_action` for `ClinicalType.OBSERVATION.value`:
1. **Primary Emission (SBP):** Sampled from its independent physiological range ($145.0 - 168.0$ mmHg at baseline) using the patient's deterministic PRNG stream.
2. **Paired Emission (DBP):** When `state.paired_observation_code` is defined, DBP is sampled from its independent range ($90.0 - 104.0$ mmHg).
3. **Physiological Guard:** Enforces biological plausibility:
   $$\text{Pulse Pressure} (\text{PP}) = \text{SBP} - \text{DBP} \ge 20 \text{ mmHg}$$
   $$\text{SBP} > \text{DBP}$$
   If an extreme draw violates this guard, DBP is dynamically adjusted to preserve a plausible pulse pressure ($25 - 35$ mmHg).
4. **Relational Pairing Invariants:**
   * `patient_id`: Identical across SBP and DBP.
   * `encounter_id`: Identical across SBP and DBP (`enc_id = record.get("current_encounter_id")`).
   * `timestamp`: Identical across SBP and DBP (`event_time`).
   * `unit`: `"mmHg"`.
   * `is_abnormal`: Evaluated independently ($\text{SBP} \ge 140.0$, $\text{DBP} \ge 90.0$).

---

## 4. Invariance of Clinical Parameters

In accordance with strict project constraints, the following components were **NOT modified**:
1. **Demographic Distributions:** `config/population/india_default_v1.yaml` was left untouched.
2. **Disease Prevalence:** Baseline hypertension prevalence ($25.3\%$) and transition weights remain unchanged.
3. **Escalation & Treatment Rules:** Monotherapy and dual-therapy transition probabilities ($60\%$ controlled, $40\%$ uncontrolled) and drug choices (Amlodipine 5mg, Telmisartan 40mg) remain identical.
4. **Longitudinal Simulation Timing:** 7-day simulation clock and delay intervals (90-day screening delay, 90-day follow-up delay) remain untouched.

---

## 5. Verification and Traceability

| Requirement | Implementation Artifact | Verification Test | Status |
| :--- | :--- | :--- | :---: |
| **Paired Emission** | `engine.py` (lines 301-330) | `test_paired_blood_pressure_state_machine_emission` | **VERIFIED** |
| **Identical Encounter & Time** | `engine.py` | `test_paired_blood_pressure_state_machine_emission` | **VERIFIED** |
| **Physiological Range & PP** | `engine.py` | `test_implausible_pulse_pressure_flagged_in_evaluator` | **VERIFIED** |
| **Explicit Missingness** | `evaluator.py` (lines 405-440) | `test_missing_dbp_unpaired_observation_handled_explicitly` | **VERIFIED** |
| **Full Export Pipeline** | `csv_exporter.py` | `test_dbp_observation_survives_complete_export_and_evaluation` | **VERIFIED** |
| **Evaluation Ingestion** | `evaluator.py` | `test_prespecified_index_measurement_selection_prevents_pseudoreplication` | **VERIFIED** |

---

## 6. Conclusion

The paired blood pressure pathway is now natively implemented within the core clinical state machine. Longitudinal observations now contain paired SBP and DBP measurements sharing identical timestamps and encounters. Biological pulse pressure is maintained without formulaic scalar fabrication, establishing a sound data foundation for external evaluation against LASI Wave 1.
