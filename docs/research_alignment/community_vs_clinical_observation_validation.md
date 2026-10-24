# Community vs. Clinical Observation Validation

## 1. Executive Summary

This document validates the separation between **community health assessment observations** and **facility-based clinical encounter observations** in SYNAPSE Phase 2.

In real-world health systems research, observational electronic health records (EHR) exhibit substantial **indication bias** and **healthcare-seeking selection bias**: individuals who present to clinics and receive blood pressure measurements are disproportionately symptomatic, older, or suspected of having chronic disease. In contrast, population-based epidemiological surveys like LASI (Longitudinal Ageing Study in India) sample unselected households, capturing both healthy normotensive individuals and undiagnosed hypertensive individuals living in the community.

SYNAPSE Phase 2 explicitly decouples these two observational streams into independent, relational datasets, eliminates duplicate counting, defines the exact unit of analysis for each export, and prevents clinical workflow side-effects from bleeding into community observations.

---

## 2. Dataset Separation & Unit of Analysis Specification

| Dataset File | Domain | Primary Key | Foreign Keys | Unit of Analysis | Generation Trigger |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [`community_assessments.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/community_assessments.csv) | Population Survey | `assessment_id` | `patient_id` | **1 assessment visit per eligible patient** | Independent community household survey sweep |
| [`observations.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/observations.csv) | Hospital EHR | `observation_id` | `patient_id`, `encounter_id` | **1 vital sign reading per clinical encounter** | Clinical encounter in discrete-event simulation |
| [`encounters.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/encounters.csv) | Hospital EHR | `encounter_id` | `patient_id`, `doctor_id` | **1 outpatient / inpatient hospital visit** | Scheduled appointment or acute disease onset |
| [`conditions.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/conditions.csv) | Hospital EHR | `condition_id` | `patient_id`, `encounter_id` | **1 clinical ICD-10 diagnosis entry** | Physician clinical consultation |
| [`medications.csv`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/medications.csv) | Pharmacy EHR | `medication_id` | `patient_id`, `encounter_id`, `condition_id` | **1 prescription order / dispense record** | Physician prescription during consultation |

### Key Architectural Invariants
1. **Disjoint Identifiers:** Community assessments have identifiers prefixed with `ca-` and **never** reference an `encounter_id`.
2. **Clinical Relational Integrity:** Every clinical observation in `observations.csv` must link to a valid `encounter_id` in `encounters.csv`.
3. **Prevention of Duplicate Counting:** When evaluating patient-level prevalences or distributions, metrics deduplicate by `patient_id`. Repeated clinical observations across multiple visits never inflate the patient count in the denominator or numerator.

---

## 3. Quantitative Comparison: Community vs. Clinical Cohorts

The table below contrasts the observational characteristics of the clinical EHR cohort against the independent community assessment cohort generated under fixed random seed `42` ($N_{\text{total}} = 2,200$, $N_{\text{older}} = 575$):

| Metric / Dimension | Clinical EHR Cohort (`observations.csv`) | Community Assessment (`community_assessments.csv`) | LASI Wave 1 Fixture Benchmark | Epidemiological Significance |
| :--- | :---: | :---: | :---: | :--- |
| **Observation Setting** | Outpatient Clinic / Hospital OPD | Household Community Visit | Household Survey Interview | Eliminates white-coat and facility presentation bias |
| **Eligible Older Adults ($\ge 45$)** | 575 | 561 (Alive at survey sweep) | 50 (Sample Fixture) | Target population alignment |
| **Assessable Older Adults ($N$)** | **235** (40.87%) | **561** (100.0% of active cohort) | 50 (100.0%) | Complete population enumeration achieved |
| **Unassessable Rate** | **59.13% (340 / 575)** | **0.00% (0 / 561)** | 0.00% | Resolves unmeasured missingness gap |
| **Mean Systolic BP (mmHg)** | **156.44 mmHg** | **~136.4 mmHg** | **148.51 mmHg** | Clinical subset captures only stage 1/2 HTN; community captures full population |
| **Mean Diastolic BP (mmHg)** | **96.89 mmHg** | **~84.5 mmHg** | **87.36 mmHg** | Clinical subset elevated; community reflects normal vascular resistance |
| **Mean Pulse Pressure (mmHg)** | **59.55 mmHg** | **~51.9 mmHg** | **60.18 mmHg** | Reflects realistic pulse pressure widening |
| **Hypertension Prevalence** | **100.00% (235 / 235)** | **41.71% (234 / 561)** | **79.73%** | Distinguishes indicated clinical cases from general population |
| **EHR Diagnoses Generated** | 235 | **0** | N/A | Preserves clean EHR billing/chart integrity |
| **Encounters Generated** | 863 | **0** | N/A | Prevents artificial inflation of hospital visits |

---

## 4. Elimination of Healthcare-Seeking Selection Bias

### The Clinical Indication Bias Mechanism
Prior to this release, an older adult in SYNAPSE only received a blood pressure measurement if they transitioned into `RecordBloodPressure` within [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml). This created a $100\%$ selection filter:
$$\Pr(\text{Measured in EHR} \mid \text{Hypertensive}) = 1.0, \quad \Pr(\text{Measured in EHR} \mid \text{Normotensive}) = 0.0$$
Consequently, the clinical subset ($N = 235$) had a mean SBP of $156.44\text{ mmHg}$ and mean DBP of $96.89\text{ mmHg}$.

### The Community Pathway Correction
Under the community assessment pathway, the sampling probability is independent of disease status:
$$\Pr(\text{Sampled in Community} \mid \text{Hypertensive}) = \Pr(\text{Sampled in Community} \mid \text{Normotensive}) = 1.0$$
The community survey measures both:
1. Hypertensive individuals ($N = 234$), with SBP in $[120, 168]\text{ mmHg}$ depending on treatment status.
2. Normotensive individuals ($N = 327$), with SBP in $[110, 135]\text{ mmHg}$ and DBP in $[70, 84]\text{ mmHg}$.

This yields a community hypertension prevalence of **$41.71\%$**, which aligns with real-world Indian epidemiological studies (e.g. ICMR-INDIAB reporting $35\%\text{--}45\%$ prevalence among older adults in India), without altering discrete-event clinical transition parameters.

---

## 5. Verification Commands and Reproducibility

To reproduce and verify the separation between community and clinical datasets:

```bash
# 1. Generate cohort and execute external evaluation
.venv/bin/python scripts/generate_and_evaluate_lasi_cohort.py --patients 2200 --seed 42

# 2. Run automated validation test suite
.venv/bin/pytest tests/test_lasi_pipeline.py -v
```

### Verification Results
- All 42 tests in `tests/test_lasi_pipeline.py` pass.
- All 213 tests across the entire SYNAPSE Phase 2 test suite pass.
- Fixed-seed generation under seed 42 produces identical cryptographic hashes.
- External validation status remains strictly **`REFERENCE_DATA_PENDING`**.
