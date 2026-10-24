# Community Health Assessment Architecture

## 1. Executive Summary & Objective

This document establishes the architecture for the **Independent Community Health Assessment Pathway** in SYNAPSE Phase 2.

In previous releases of the synthetic simulator, all physiological vital signs (specifically Systolic Blood Pressure [SBP] and Diastolic Blood Pressure [DBP]) were emitted exclusively through the discrete-event clinical module for primary hypertension ([`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml)). This design created two fundamental methodological problems:
1. **Severe Indication Bias in Observational Records:** Only patients who developed hypertension and attended an outpatient clinical consultation ([`ScreeningEncounter`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml#L49-L55)) had blood pressure recorded ($N = 235$ older adults, $100\%$ hypertensive). Healthy, normotensive community members ($N = 340$) never attended an encounter and therefore had zero blood pressure observations in the synthetic EHR.
2. **Conflation of Survey Biomarkers and Hospital Records:** When comparing the synthetic population against population-level household surveys like the Longitudinal Ageing Study in India (LASI Wave 1), clinical outpatient encounters were mistakenly treated as if they were community survey visits.

To resolve this without corrupting hospital EHR semantics, SYNAPSE Phase 2 implements a dedicated, decoupled **Community Health Assessment Layer** ([`synapse_simulator/datagen/community_assessment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/community_assessment.py)). This pathway models independent community health worker / biomarker survey visits (analogous to LASI field enumerator visits or NFHS-5 household biomarker rounds) without creating synthetic hospital visits, without generating EHR billing codes, and without triggering clinical prescriptions.

---

## 2. Architectural Separation of Datasets

A strict architectural partition is enforced between facility-based Electronic Health Records (EHR) and population-level Community Health Assessments:

```
+---------------------------------------------------------------------------------------------------+
|                                  SYNTHETIC POPULATION BASELINE                                    |
|                             (PatientContext: Latent Biological State)                             |
+---------------------------------------------------------------------------------------------------+
                                  /                               \
                                 /                                 \
                                v                                   v
+-----------------------------------------------+   +-----------------------------------------------+
|             CLINICAL EHR PIPELINE             |   |         COMMUNITY ASSESSMENT PIPELINE         |
|  (Discrete-Event Hospital & Clinic Simulation)|   |    (Population Survey & Household Biomarkers) |
+-----------------------------------------------+   +-----------------------------------------------+
|  - Encounters: encounters.csv (OPD/IPD visits)|   |  - Assessments: community_assessments.csv     |
|  - Diagnoses: conditions.csv (ICD-10 I10)     |   |  - Target: All community older adults (>= 45) |
|  - Vitals: observations.csv (clinical visits) |   |  - Measured: Normotensive + Hypertensives     |
|  - Pharmacy: medications.csv (prescriptions)  |   |  - Provenance: COMMUNITY_HEALTH_ASSESSMENT    |
|  - Care Plans: care_plans.csv                 |   |  - No hospital visits or encounters created   |
|  - Selection: Symptom-seeking / indicated     |   |  - No clinical condition records generated    |
+-----------------------------------------------+   +-----------------------------------------------+
                                 \                                 /
                                  \                               /
                                   v                             v
+---------------------------------------------------------------------------------------------------+
|                             INDEPENDENT LASI EVALUATION FRAMEWORK                                 |
|                       (Distinct Estimands, Denominators, and Diagnostics)                         |
+---------------------------------------------------------------------------------------------------+
```

### Invariant Rules
1. **Zero Encounter Creation:** Executing a community health assessment does NOT add rows to [`encounters.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/encounters.csv) or create records in `clinical.encounters`.
2. **Zero Clinical Diagnosis Generation:** Field survey vital sign measurements do NOT generate physician diagnosis records in [`conditions.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/conditions.csv) and do NOT set `patient.latent_conditions["I10"]["recognized"] = True`.
3. **Zero Prescriptions or Care Plans:** Community assessments do NOT initiate medications in [`medications.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/medications.csv) or start care plans in [`care_plans.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/care_plans.csv).
4. **No Discrete-Event Engine Interference:** The community survey operates as an observational layer and does not mutate engine state machine transitions or delay counters.

---

## 3. Data Model and Schema Specification

The assessment layer is formalized in [`synapse_simulator/datagen/community_assessment.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/community_assessment.py) via Pydantic schema:

```python
class CommunityAssessment(BaseModel):
    assessment_id: str          # e.g., "ca-p001"
    patient_id: str             # Foreign key to patient context
    timestamp: datetime         # Scheduled survey date
    assessment_type: str        # "COMMUNITY_HEALTH_ASSESSMENT"
    sbp: Optional[float]        # Measured Systolic BP (mmHg)
    dbp: Optional[float]        # Measured Diastolic BP (mmHg)
    pulse_pressure: Optional[float] # SBP - DBP (mmHg)
    unit: str                   # "mmHg"
    survey_weight: float        # Inverse selection probability weight
    status: str                 # "COMPLETED", "REFUSED", "UNAVAILABLE"
    provenance: str             # "COMMUNITY_HEALTH_ASSESSMENT_LAYER"
    is_assessable: bool         # True if valid vital signs obtained
```

### Relational Schema Contract (`community_assessments.csv`)

| Column Name | Type | Nullable | Description | Example |
| :--- | :--- | :---: | :--- | :--- |
| `assessment_id` | `VARCHAR(32)` | No | Primary key for assessment record | `ca-p00000001` |
| `patient_id` | `VARCHAR(32)` | No | Foreign key to `patients.patient_id` | `p00000001` |
| `timestamp` | `ISO8601` | No | Timestamp of field measurement | `2024-06-15T09:30:00` |
| `assessment_type` | `VARCHAR(64)` | No | Assessment classification | `COMMUNITY_HEALTH_ASSESSMENT` |
| `sbp` | `FLOAT` | Yes | Systolic Blood Pressure in mmHg | `124.5` |
| `dbp` | `FLOAT` | Yes | Diastolic Blood Pressure in mmHg | `78.0` |
| `pulse_pressure` | `FLOAT` | Yes | SBP - DBP in mmHg | `46.5` |
| `unit` | `VARCHAR(16)` | No | Measurement unit | `mmHg` |
| `survey_weight` | `FLOAT` | No | Inverse probability weight | `1.0` |
| `status` | `VARCHAR(32)` | No | Field collection outcome | `COMPLETED` |
| `provenance` | `VARCHAR(64)` | No | Provenance identifier | `COMMUNITY_HEALTH_ASSESSMENT_LAYER` |

Notice that unlike [`observations.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/observations.csv), this table has **no `encounter_id`**, explicitly preventing relational joins that would falsely link community field readings to hospital stays.

---

## 4. Sampling Design and Target Population

### Target Population Definition
The target population for the external evaluation pathway is **community-dwelling older adults aged 45 years and older** residing in the synthetic population:
$$\mathcal{P}_{\text{eval}} = \{ p \in \mathcal{P} \mid \text{age}(p, t_{\text{survey}}) \ge 45.0 \land \text{alive}(p, t_{\text{survey}}) \}$$

### Sampling Mechanism
The sampling configuration is governed by `CommunityAssessmentConfig`:
1. **Sampling Fraction ($\pi$):** Default is complete enumeration ($\pi = 1.0$) of all eligible older adults ($N = 575$). The architecture supports probability sampling ($0 < \pi \le 1.0$) with survey weights automatically calculated as $w_i = 1 / \pi$.
2. **Survey Sweep Window:** The survey sweep is scheduled at a fixed mid-observation window ($t = \text{observation\_start} + 180\text{ days}$), reflecting a cross-sectional household survey sweep.
3. **Non-Response / Missingness Modeling:** Unassessable or refusing participants are modeled explicitly:
   - If non-response triggers, `status = "REFUSED"`, `sbp = None`, `dbp = None`, `is_assessable = False`.
   - These records appear in the dataset as unassessable records and are evaluated under Estimand E rather than being dropped or imputed as normal.

---

## 5. Physiological Vital Sign Generation Model

Vital sign values generated in community assessments are grounded strictly in the **existing medical knowledge base** ([`config/knowledge/medical_knowledge.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/knowledge/medical_knowledge.yaml)) and clinical module specifications ([`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml)), without ad-hoc parameter tuning:

1. **Hypertensive Patients (Untreated):**
   - SBP drawn from $[145.0, 168.0]\text{ mmHg}$ (as defined in `RecordBloodPressure`).
   - DBP drawn from $[90.0, 104.0]\text{ mmHg}$.
2. **Hypertensive Patients (Treated on Antihypertensive Rx):**
   - Evaluates whether patient is actively prescribed Amlodipine, Telmisartan, Enalapril, or Atenolol at $t_{\text{survey}}$.
   - SBP drawn from $[120.0, 150.0]\text{ mmHg}$ (as defined in `MeasureFollowUpBP`).
   - DBP drawn from $[75.0, 92.0]\text{ mmHg}$.
3. **Normotensive Community Members:**
   - SBP drawn from $[110.0, 135.0]\text{ mmHg}$ (as defined in `vitals_ranges.adult` and `elderly`).
   - DBP drawn from $[70.0, 84.0]\text{ mmHg}$.
4. **Physiological Pulse Pressure Invariant:**
   - For all generated records, pulse pressure ($\text{PP} = \text{SBP} - \text{DBP}$) is strictly verified to satisfy $\text{PP} \ge 20.0\text{ mmHg}$.

---

## 6. Determinism and Seed Management

To guarantee bit-for-bit reproducibility across runs:
- The `CommunityAssessmentGenerator` derives an isolated, independent pseudo-random number generator for every patient:
  $$\text{PRNG}_p = \text{Random}(\text{hash}(\text{base\_seed}, \text{"comm\_eval"}, \text{patient\_id}))$$
- This guarantees that adding or removing community assessments never alters the sequence of random numbers consumed by the discrete-event simulation engine, preserving perfect reproducibility of clinical encounters and trajectories.
