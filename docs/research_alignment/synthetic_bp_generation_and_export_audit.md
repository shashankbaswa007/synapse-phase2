# Synthetic Blood Pressure Generation and Export Audit

**Project:** SYNAPSE Phase 2 — Synthetic Healthcare Data Generation and Evaluation  
**Document ID:** `DOC-RES-LASI-007`  
**Focus Area:** End-to-End Tracing of Systolic and Diastolic Blood Pressure from Simulation to Evaluation  
**Date:** 2026-10-21  
**Git Revision:** `3e3ae1d28286e9106659f68aa053465ded9bb3c2`  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary

During the initial LASI Wave 1 pipeline audit, the evaluation report revealed:
* **863 SBP Observations** in older adults ($N=235$ distinct patients).
* **0 DBP Observations** exported in the synthetic cohort.

This audit conducted an end-to-end trace through all layers of the SYNAPSE architecture to identify the exact root cause of the missing diastolic blood pressure observations, verify schema compatibility, test whether DBP can survive export and evaluation, and establish why arbitrary formula synthesis was rejected under scientific governance principles.

---

## 2. End-to-End Blood Pressure Pipeline Trace

We traced blood pressure variables through all 6 architecture stages:

```
[1. Clinical Generator / Modules]
        │
        ├── OPD Vitals Generator (clinical_generator.py) -> generates (systolic_bp, diastolic_bp)
        │                                                    (isolated to episodic encounters)
        └── Longitudinal Module Engine (hypertension.yaml) -> generates ONLY SBP
                                                               (NO DBP state defined)
        ▼
[2. State Manager & Module Runner]
        │
        └── runner.longitudinal_observations -> contains ONLY SBP records
        ▼
[3. CSV Exporter (csv_exporter.py)]
        │
        └── exports runner.longitudinal_observations directly to observations.csv
        ▼
[4. Relational CSV Output (observations.csv)]
        │
        └── Contains SBP (8480-6), Glucose, HbA1c; ZERO DBP rows
        ▼
[5. LASI Ingestion & Evaluator (evaluator.py)]
        │
        ├── Evaluates SBP: 863 rows -> passes sample size gate (863 >= 30)
        └── Evaluates DBP: 0 rows -> assigns INSUFFICIENT_SAMPLE_SIZE
```

### Stage 1: Clinical Generator vs. Module State Machine
1. In [`synapse_simulator.datagen.clinical_generator.ClinicalEntityGenerator.generate_vitals()`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/clinical_generator.py#L123-L150), both systolic and diastolic vitals are sampled:
   ```python
   # clinical_generator.py lines 135-144
   sbp_val = round(self.rng.normalvariate(sbp_mean, 10.0), 1)
   dbp_val = round(self.rng.normalvariate(dbp_mean, 6.0), 1)
   ```
   However, these vitals belong to episodic outpatient hospital visits (`GeneratedVitals`), which are stored within consultation payloads and are not routed to longitudinal time-series observation tables.

2. In [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml), the longitudinal state machine defines only SBP observation states:
   ```yaml
   # config/modules/hypertension.yaml lines 72-81
   RecordBloodPressure:
     type: Observation
     observation_code: "SBP"
     observation_name: "Systolic Blood Pressure"
     value: 145.0
     unit: "mmHg"
     direct_transition: ScheduleFollowUp
   ```
   and:
   ```yaml
   # config/modules/hypertension.yaml lines 112-121
   MeasureFollowUpBP:
     type: Observation
     observation_code: "SBP"
     observation_name: "Systolic Blood Pressure"
     value: 135.0
     unit: "mmHg"
     direct_transition: CheckTargetControl
   ```
   **Finding 1:** There is **no state in `hypertension.yaml` that emits a DBP observation**. The state machine was authored strictly with systolic blood pressure.

### Stage 2: Module Runner Accumulation
In [`synapse_simulator.modules.engine.ClinicalModuleRunner.step_patient()`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/modules/engine.py#L205-L250), observation states emit entries into `runner.longitudinal_observations`:
```python
self.longitudinal_observations.append({
    "observation_id": obs_id,
    "patient_id": patient.patient_id,
    "encounter_id": enc_id,
    "timestamp": current_time.isoformat(),
    "observation_code": state.observation_code,
    "observation_name": state.observation_name,
    "value": obs_val,
    "unit": state.unit,
    "is_abnormal": is_abnormal,
})
```
Because no DBP observation state exists in the module YAML, no DBP dictionary is ever appended to `runner.longitudinal_observations`.

### Stage 3: CSV Serialization & Export
In [`synapse_simulator.exporter.csv_exporter.CSVExporter.export_simplified_dataset()`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/exporter/csv_exporter.py#L380-L410):
```python
# observations.csv
obs_rows = []
if self.module_runner and hasattr(self.module_runner, "longitudinal_observations"):
    obs_rows = self.module_runner.longitudinal_observations
```
The exporter writes `obs_rows` verbatim to `observations.csv`. It does not filter out DBP; DBP is simply absent from `obs_rows`.

### Stage 4: Evaluator Ingestion
In [`synapse_simulator.evaluation.lasi.evaluator.LasiExternalEvaluator._evaluate_blood_pressure()`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py#L468-L547):
The evaluator filters `self.observations` for `obs.get("observation_code") == "DBP"`.
Finding 0 rows, it cleanly emits:
- Metric: `lasi_bp_dbp_distribution`
- Status: `INSUFFICIENT_SAMPLE_SIZE`
- Synthetic Estimate: `0.0`
- Comparability Note: `"Synthetic DBP observations not exported in current simulation cohort."`

---

## 3. Scientific Governance: Rejection of Formulaic Synthesis

An ad-hoc engineering temptation when faced with 0 DBP observations is to calculate DBP from SBP using a fixed formula, such as:
$$\text{DBP}_{\text{synthetic}} = 0.65 \times \text{SBP} \quad \text{or} \quad \text{DBP}_{\text{synthetic}} = \text{SBP} - 45$$

**This was strictly rejected on scientific and regulatory grounds:**
1. **Pulse Pressure Non-Linearity:** In older adults ($\ge 45$ years), arterial compliance decreases, causing pulse pressure ($\text{PP} = \text{SBP} - \text{DBP}$) to widen dramatically with age. In elderly populations, SBP often rises while DBP plateaus or falls (isolated systolic hypertension). A linear ratio creates an invalid correlation structure ($r = 1.0$), destroying epidemiological plausibility.
2. **False Validation Passing:** Fabricating observations to satisfy a metric gate constitutes scientific misconduct. If the generator does not model diastolic hemodynamics, the validator must report `INSUFFICIENT_SAMPLE_SIZE`, not generate synthetic numbers to force a `PASS`.
3. **Mandate Adherence:** User instructions explicitly forbid mathematical fabrication:
   - *"Do not synthesize DBP from SBP using an arbitrary formula."*
   - *"Do not fabricate clinical observations."*
   - *"Do not change disease prevalence, clinical transition probabilities, treatment rules, or population parameters merely to force the validation metrics to pass."*

---

## 4. Architecture Verification: End-to-End Regression Test

To prove that the pipeline schema, `CSVExporter`, and `LasiExternalEvaluator` correctly support DBP whenever legitimate observations are emitted, a regression test was added in [`tests/test_lasi_pipeline.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_lasi_pipeline.py#L692-L790):

### Regression Test Implementation: `test_dbp_observation_survives_complete_export_and_evaluation`
```python
def test_dbp_observation_survives_complete_export_and_evaluation(tmp_path):
    """Regression test: verify that a valid generated DBP observation survives the complete
    export and evaluation pipeline (runner -> observations.csv -> LasiExternalEvaluator)."""
    # 1. Emit both SBP and DBP observations into module runner
    runner.longitudinal_observations.append({
        "observation_id": "obs-sbp-01",
        "patient_id": pid,
        "encounter_id": enc_id,
        "timestamp": "2026-01-10T10:05:00",
        "observation_code": "SBP",
        "observation_name": "Systolic Blood Pressure",
        "value": 142.0,
        "unit": "mmHg",
        "is_abnormal": True,
    })
    runner.longitudinal_observations.append({
        "observation_id": "obs-dbp-01",
        "patient_id": pid,
        "encounter_id": enc_id,
        "timestamp": "2026-01-10T10:05:00",
        "observation_code": "DBP",
        "observation_name": "Diastolic Blood Pressure",
        "value": 88.0,
        "unit": "mmHg",
        "is_abnormal": True,
    })

    # 2. Export via CSVExporter
    exporter = CSVExporter(...)
    exporter.export_simplified_dataset(target_dir=out_dir)

    # 3. Verify observations.csv contains DBP row with correct columns
    with open(out_dir / "observations.csv") as f:
        rows = list(csv.DictReader(f))
    dbp_rows = [r for r in rows if r["observation_code"] == "DBP"]
    assert len(dbp_rows) == 1
    assert float(dbp_rows[0]["value"]) == 88.0

    # 4. Verify LasiExternalEvaluator parses and evaluates DBP
    evaluator = LasiExternalEvaluator(synthetic_dir=out_dir, ...)
    report = evaluator.evaluate()
    dbp_result = next(m for m in report.metrics if m.metric_id == "lasi_bp_dbp_distribution")
    assert dbp_result.synthetic_n == 1
    assert dbp_result.synthetic_estimate == 88.0
```

### Test Result
The test runs and passes synchronously as part of the 197-test suite:
```
tests/test_lasi_pipeline.py .......................... [100%]
197 passed in 7.72s
```

---

## 5. Root Cause Conclusion & Future Remediation Plan

| Investigation Item | Finding | Status |
| :--- | :--- | :---: |
| **Is DBP generated in clinical generator?** | Yes, in episodic OPD vitals generator. | Verified |
| **Is DBP emitted by `hypertension.yaml`?** | **No. State machine has only SBP states.** | **ROOT CAUSE IDENTIFIED** |
| **Does `observations.csv` schema support DBP?** | Yes, supports any LOINC/clinical observation. | Verified |
| **Does `CSVExporter` drop DBP?** | No, exports all runner observations faithfully. | Verified |
| **Does `LasiExternalEvaluator` handle DBP?** | Yes, full distribution + standardized metrics. | Verified & Hardened |
| **Does missing DBP break pipeline?** | No, cleanly gates out with `INSUFFICIENT_SAMPLE_SIZE`. | Verified |

### Remediation Path for Phase 3 (Model Expansion)
In Phase 3, when clinical modules are expanded:
1. Update `config/modules/hypertension.yaml` to include paired DBP observation states (or a dual vital-sign state) driven by physiological hemodynamics.
2. Calibrate diastolic distributions against NFHS-5 and LASI reference distributions.
3. Keep current gate status as `INSUFFICIENT_SAMPLE_SIZE` until legitimate model generation is added.
