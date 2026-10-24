# SYNAPSE Phase 2: Synthea-Inspired Synthetic Healthcare Data Generation and Longitudinal Simulation System

## Executive Summary

**SYNAPSE Phase 2** is a modular, Synthea-inspired longitudinal healthcare data generation and patient trajectory simulation engine. It generates rich, temporally coherent, causally consistent, and clinically plausible synthetic longitudinal health records modeled after Indian demographic, epidemiological, and health system patterns.

This document serves as the comprehensive technical report for the Phase 2 system, detailing:
1. Architectural foundations and disease state-machine models.
2. Treatment workflows and clinical guideline adherence.
3. The execution pipeline (`ExperimentRunner`) and CLI entry point (`generate_synthetic_data.py`).
4. Dual hemodynamic engines: default `LEGACY_CONDITIONAL` and experimental `FORWARD_STATE_SPACE`.
5. The community assessment triplicate seated blood pressure protocol (`LASI_WAVE1_TRI_MEASUREMENT` v1.0.0).
6. Canonical 10,000-patient cohort specifications, table schemas, and SHA-256 integrity checksums.
7. Reproducibility instructions and scientific governance (`REFERENCE_DATA_PENDING`).

---

## 1. Architectural Foundations

SYNAPSE Phase 2 transitions from early discrete-event hospital queue prototyping to a patient-centric, longitudinal microsimulation architecture inspired by the open-source **Synthea** framework, adapted for Indian healthcare delivery.

```
+-----------------------------------------------------------------------------------+
|                           SYNAPSE Phase 2 Architecture                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. Population Demography (SRS 2021) ---> Stratified Patient Initialization       |
|                                                    |                              |
|  2. Synthea State Machines ------------> 7-Day Timestep Progression Loop          |
|     * Hypertension (YAML)                          |                              |
|     * Type 2 Diabetes (YAML)                       v                              |
|     * Acute URTI (YAML)                Care-Seeking Triggers & OPD Encounters     |
|     * Background Mortality (Life Tables)           |                              |
|                                                    v                              |
|  3. Treatment & Safety ----------------> ICMR STG 2022 Guidelines                 |
|                                         Allergy Veto (RULE-CLIN-ALLERGY-001)      |
|                                                    |                              |
|  4. Hemodynamic Engines ---------------> LEGACY_CONDITIONAL (Default)             |
|                                         FORWARD_STATE_SPACE (Experimental)        |
|                                                    |                              |
|  5. Community Survey Protocol ---------> LASI_WAVE1_TRI_MEASUREMENT v1.0.0        |
|                                         (Triplicate Seated Readings at Day 360)   |
|                                                    |                              |
|  6. Analytical Serialization ----------> Standardized 18-Table CSV Schema         |
|                                         SHA-256 Manifest Verification             |
|                                                    |                              |
|  7. Evaluation & Validation Gate ------> 16 PASS Metrics, Zero Fatal Violations   |
|                                         Status: REFERENCE_DATA_PENDING            |
+-----------------------------------------------------------------------------------+
```

### 1.1 Demographic Baseline & Stratification
Each synthetic patient is initialized as an in-memory `PatientContext` with baseline physiological, sociodemographic, and genetic attributes drawn from the **Sample Registration System (SRS) 2021 India Census**:
* **Sex Stratification**: 51.5% male, 48.5% female.
* **Age Stratification**: 5 standard census bands (0–14: 25.0%, 15–24: 17.5%, 25–44: 31.5%, 45–64: 19.0%, 65+: 7.0%).
* **Baseline Health Risk**: Body Mass Index (BMI), baseline systolic/diastolic blood pressure, baseline fasting plasma glucose, and allergy predispositions.

---

## 2. Longitudinal Disease Progression Models

Longitudinal health trajectories are defined via declarative YAML state machines executed every $\Delta t = 7$ days over a 720-day observation window.

### 2.1 Essential Hypertension (`config/diseases/hypertension_v1.yaml`)
* **State Space**: `HEALTHY` $\rightarrow$ `PRE_HYPERTENSION` $\rightarrow$ `STAGE_1_HTN` $\rightarrow$ `STAGE_2_HTN` $\rightarrow$ `HYPERTENSIVE_CKD`.
* **Risk Modifiers**: Age $\ge 45$, elevated BMI ($\ge 25\ \text{kg/m}^2$), male sex, baseline sodium consumption.
* **Progression Dynamics**: Patients in `STAGE_1_HTN` experience elevated systolic/diastolic pressures. Without treatment, 1.0–2.0% annual transition to chronic kidney disease (`HYPERTENSIVE_CKD`) is modeled.
* **Treatment Escalation**:
  * First-Line: Monotherapy with **Amlodipine** (5 mg/day).
  * Intensification: Stepped-care escalation to **Telmisartan** (40 mg/day) if blood pressure remains uncontrolled after 90 days.

### 2.2 Type 2 Diabetes Mellitus (`config/diseases/type2_diabetes_v1.yaml`)
* **State Space**: `HEALTHY` $\rightarrow$ `PRE_DIABETES` $\rightarrow$ `T2D_UNCOMPLICATED` $\rightarrow$ `DIABETIC_NEPHROPATHY`.
* **Risk Modifiers**: Age $\ge 35$, elevated BMI, family history, sedentary activity.
* **Complications**: Microvascular renal complications develop in a fraction of patients over prolonged exposure ($1.93\%$ progression in canonical cohort).
* **Treatment Escalation**:
  * First-Line: Monotherapy with **Metformin** (500–1000 mg/day).
  * Intensification: Stepped-care escalation to **Glimepiride** (1–2 mg/day) for uncontrolled hyperglycemia.

### 2.3 Acute Upper Respiratory Tract Infection (`config/diseases/acute_urti_v1.yaml`)
* **State Space**: `SUSCEPTIBLE` $\rightarrow$ `INCUBATION` $\rightarrow$ `ACUTE_INFECTION` $\rightarrow$ `CONVALESCENT` $\rightarrow$ `SUSCEPTIBLE`.
* **Transmission Dynamics**: Seasonal multi-wave Poisson incidence with winter/monsoon surges.
* **Symptom Expression**: Fever, cough, sore throat, and rhinorrhea.
* **Resolution**: Median episode duration of 7–10 days. Treated with symptomatic therapy or first-line **Amoxicillin** for suspected secondary bacterial etiology.

### 2.4 Background All-Cause Mortality
Surviving patients are evaluated against annual age- and sex-stratified mortality rates from the **SRS 2016–2020 Life Tables**:
* Cumulative 720-day cohort mortality: 255 deaths across 10,000 patients ($0.01311$ per patient-year).
* Temporal Invariant: Deceased patients have zero subsequent encounters, orders, or prescriptions (`inv_no_event_post_mortem`).

---

## 3. Treatment Workflows & Clinical Safety

Care delivery is modeled through Outpatient Department (OPD) visits triggered by symptomatic presentation or routine chronic surveillance.

1. **Guideline Adherence**:
   * Prescribing rules enforce the **ICMR Standard Treatment Guidelines (STG) 2022**.
   * First-line adherence for hypertension is **99.87%** (Amlodipine monotherapy).
   * First-line adherence for diabetes is **99.57%** (Metformin monotherapy).
2. **Clinical Safety Mandate (`RULE-CLIN-ALLERGY-001`)**:
   * Patient allergy profiles (e.g., penicillin sensitivity) are checked prior to dispensing.
   * Contradicted prescriptions are vetoed with 100% compliance (**0 safety violations** across 12,943 prescriptions).

---

## 4. Hemodynamic Engines

SYNAPSE Phase 2 features two distinct hemodynamic modeling modes:

| Feature / Dimension | `LEGACY_CONDITIONAL` (Default) | `FORWARD_STATE_SPACE` (Opt-In Experimental) |
| :--- | :--- | :--- |
| **Status** | Production Default & Certified | Experimental Research Capability |
| **Mathematical Basis** | Stratified conditional multivariate distributions with pharmacodynamic offset vectors | Continuous state-space ordinary differential equations (ODEs) |
| **Variables Modeled** | SBP, DBP, Pulse Pressure, Heart Rate | Stroke volume, systemic vascular resistance (SVR), arterial compliance ($C$), baroreflex gain |
| **Computational Overhead** | Ultra-fast ($< 0.1$ ms per patient-step) | Moderate ($~1.5$ ms per patient-step) |
| **Deterministic Guarantee** | Fully reproducible under Seed 42 | Fully reproducible under Seed 42 |
| **Output Schema** | `observations.csv` (SBP, DBP), `community_bp_readings.csv` | `observations.csv` (SBP, DBP), `community_bp_readings.csv` |

The canonical 10,000-patient cohort in `data/synthetic/` was generated and verified using the **`LEGACY_CONDITIONAL`** engine.

---

## 5. Triplicate Seated Blood Pressure Community Protocol

To support geriatric and cardiovascular research, SYNAPSE Phase 2 incorporates the **`LASI_WAVE1_TRI_MEASUREMENT` v1.0.0** protocol, modeled after the Longitudinal Ageing Study in India survey methodology.

### Protocol Specification
* **Target Population**: Surviving older adults (Age 45+) assessed at simulation day 360 ($N=2,638$).
* **Measurement Sequence**: Exactly three sequential seated blood pressure readings taken with an automated oscillometric digital monitor:
  1. *Reading 1*: Taken after 5 minutes of quiet seated rest. Reflects mild familiarization / clinic white-coat elevation.
  2. *Reading 2*: Taken after 2 minutes of seated rest. Reflects hemodynamic habituation.
  3. *Reading 3*: Taken after an additional 2 minutes of seated rest. Represents steady-state resting blood pressure.
* **Official Survey Measure**: The protocol average is calculated as the mean of Readings 2 and 3.

### Observed Hemodynamics in Canonical Cohort
* **Reading 1 Mean**: SBP $130.14 \pm 9.41$ mmHg | DBP $80.62 \pm 5.25$ mmHg.
* **Reading 2 Mean**: SBP $126.69 \pm 9.59$ mmHg | DBP $79.11 \pm 5.36$ mmHg.
* **Reading 3 Mean**: SBP $126.61 \pm 9.56$ mmHg | DBP $79.14 \pm 5.32$ mmHg.
* **Habituation Drop**: $-3.45$ mmHg systolic drop from Reading 1 to Reading 2.
* **Invariant Compliance**:
  * 7,914 readings generated across 2,638 assessments (100% complete).
  * Strictly SBP > DBP across all 7,914 readings (0 violations).
  * Pulse pressure $\ge 20$ mmHg across all 7,914 readings (minimum: $22.60$ mmHg).

---

## 6. Pipeline Execution & Generation Entry Points

The generation and evaluation pipeline is executed through two primary interfaces:

### 6.1 CLI Entry Point: `generate_synthetic_data.py`
The top-level script routes directly to the Phase 2 `ExperimentRunner`:
```bash
python3 generate_synthetic_data.py \
  --patients 10000 \
  --days 720 \
  --timestep 7 \
  --seed 42 \
  --output-dir data/synthetic \
  --profile config/population/india_default_v1.yaml \
  --hemodynamic-mode LEGACY_CONDITIONAL \
  --protocol tri_measurement \
  --evaluate-lasi
```

### 6.2 Programmatic Pipeline: `ExperimentRunner`
Located in `synapse_simulator/evaluation/experiment.py`, `ExperimentRunner` coordinates:
1. Instantiation of `IndiaPopulationGenerator` with seed 42.
2. 720-day longitudinal simulation with 7-day state updates.
3. Execution of `LASI_WAVE1_TRI_MEASUREMENT` wave survey.
4. Export through `CSVExporter` into isolated output directories.
5. Invariant checking and metric validation via `EvaluationRunner`, `DatasetAuditor`, and `DatasetValidationGate`.

---

## 7. Canonical 10,000-Patient Cohort Inventory & Checksums

The canonical synthetic dataset resides in `data/synthetic/` and comprises 18 tabular CSVs totaling 94,595 core operational records and 108,651 total records across all tables.

### Table Inventory

| CSV Filename | Row Count | Primary Key | Foreign Keys | File Size | SHA-256 Checksum |
| :--- | :---: | :--- | :--- | :---: | :--- |
| `patients.csv` | 10,000 | `patient_id` | — | 561 KB | `7b103bd2d3abc1e59f5cda00eb50049389b0e0ebbf9d82fe805f80b04cc3371b` |
| `encounters.csv` | 21,730 | `encounter_id` | `patient_id` | 2.69 MB | `5ae2ee8005e1ed3c95673186d2967d5b64ebe2aac743d18ebf4774a18b86e948` |
| `conditions.csv` | 10,463 | `condition_id` | `patient_id`, `encounter_id` | 1.09 MB | `1dfba3c2742e5085439a1b9fb94317e85988468733c21a6432b554d000851412` |
| `medications.csv` | 12,943 | `medication_id`| `patient_id`, `encounter_id`, `condition_id` | 1.49 MB | `8f4bb56c5fee0e46884b34530fce615f9f7bf18ff531c153bbc534e28435a834` |
| `symptoms.csv` | 39,444 | `symptom_id` | `patient_id`, `encounter_id`, `condition_id` | 2.92 MB | `d539033374ef27fcb0c7a8fcc4c0d2995baf62140b9c05524e14469290ab5d18` |
| `observations.csv` | 23,198 | `observation_id`| `patient_id`, `encounter_id` | 2.39 MB | `61d9c292bb7d686fb967db9d637460d86a6ac0178577585d85edadf517820715` |
| `community_assessments.csv` | 2,638 | `assessment_id` | `patient_id` | 388 KB | `0fefdbddc26a02bf93326cb2b6bd61d8a500bb0115d4e0277d50b3b6f5a7b807` |
| `community_bp_readings.csv` | 7,914 | `assessment_id`+`reading_number` | `assessment_id`, `patient_id` | 1.16 MB | `8415502dffa32630b0704d2bb285f63d4d7b975ef052350b47ffc0ff2fb1008a` |
| `care_plans.csv` | 3,249 | `care_plan_id` | `patient_id`, `encounter_id` | 422 KB | `37b12ad872f78d075bf04916c52215f95cc10ce143da324471495634da00732d` |
| `deaths.csv` | 255 | `death_id` | `patient_id` | 26 KB | `8c0f8e79ec60e4a3618f01365a7b883008f8d96d87b5e554a4ccfc391cdcbb39` |
| `generation_summary.csv` | 15 | — | — | 357 B | `df83712c62fa77692d3c3f150496b2e08ab5803d8cbdd33d8c29855587c3ccf5` |
| `events.csv` | 0 | `event_id` | `patient_id` | 80 B | `58eb926874781b99b4fa002c1cbe47498f36340ba43559ca875feff0c15a21b7` |
| `invoices.csv` | 0 | `invoice_id` | `patient_id`, `encounter_id` | 67 B | `2f1d4001b78adc830ebeae577cda24abbba11be044837c255ea11585a9731e5c` |
| `journey_traces.csv` | 0 | `journey_id` | `patient_id` | 77 B | `6825c4bb8ab95d39ded492a85098883c81bb402f1403c1e85e81ad8f3c23a245` |
| `labs.csv` | 0 | `lab_id` | `patient_id`, `encounter_id` | 81 B | `108d77b970776e6d88a1f1ee66dac849b339e92530a7eb3d827390e10dbb85b7` |
| `patient_timeline.csv` | 0 | `timeline_id` | `patient_id` | 67 B | `3a0e8d071740b76e0752769bea690e1004edb328f3932fc82b271cde3a26079c` |
| `payments.csv` | 0 | `payment_id` | `patient_id`, `invoice_id` | 73 B | `e425a99e5a69ec15905dd626bde52054bf874bfae7193b47ad676c2885980c12` |
| `radiology.csv` | 0 | `radiology_id`| `patient_id`, `encounter_id` | 99 B | `2b71576fac1776a0e00aea80b1fb318952d93fb43db85b6cdedf3491b5bdbf5e` |

---

## 8. Reproducibility & Verification Instructions

To reproduce the canonical dataset or run independent validation checks without altering canonical data:

### 8.1 Cohort Regeneration Command
```bash
python3 generate_synthetic_data.py \
  --patients 10000 \
  --days 720 \
  --timestep 7 \
  --seed 42 \
  --output-dir data/synthetic_reproducibility_test \
  --profile config/population/india_default_v1.yaml \
  --hemodynamic-mode LEGACY_CONDITIONAL \
  --protocol tri_measurement \
  --evaluate-lasi
```

### 8.2 Full Verification Suite Execution
```bash
# Run full unit and integration regression test suite (374 tests expected)
.venv/bin/pytest tests/ -v

# Run dataset evaluation against canonical directory
python3 evaluate_dataset.py --dataset-dir data/synthetic
```

---

## 9. Scientific Integrity & Governance Statement

> **FORMAL GOVERNANCE DECLARATION**:
> The external clinical validation status for SYNAPSE Phase 2 is strictly maintained as:
>
> $$\mathbf{REFERENCE\_DATA\_PENDING}$$
>
> 1. **No Access to Confidential Survey Microdata**: At no point during development, calibration, or evaluation were genuine individual participant records from LASI Wave 1 or other restricted clinical databases accessed, linked, or reverse-engineered.
> 2. **Engineering vs. Clinical Validation**: The 16 passing metrics certify software correctness, referential integrity, and macro-level statistical calibration against public aggregate tables. They do not constitute empirical diagnostic validation.
> 3. **Preservation of Clinical Defaults**: Simulation parameters and hazard ratios are maintained according to medical literature and national guidelines. They have not been artificially manipulated to force arbitrary metric compliance.
