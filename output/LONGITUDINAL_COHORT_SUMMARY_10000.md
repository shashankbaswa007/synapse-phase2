# SYNAPSE Phase 2: Canonical 10,000-Patient Longitudinal Cohort Summary

## 1. Executive Summary & Simulation Specifications

The **SYNAPSE Phase 2** synthetic healthcare data generation platform has generated and validated a canonical synthetic cohort of **10,000 patients** simulated longitudinally over a **720-day observation window** (24 months) using a **7-day simulation timestep**.

| Simulation Parameter | Value / Specification | Provenance / Standard |
| :--- | :--- | :--- |
| **Cohort Size ($N$)** | 10,000 synthetic patients | Fixed canonical cohort |
| **Observation Window** | 720 days (Jan 1, 2024 – Dec 21, 2025) | Longitudinal multi-year evaluation |
| **Simulation Timestep ($\Delta t$)** | 7 days (weekly discrete-time transition) | Synthea state-machine cadence |
| **Pseudo-Random Seed** | `42` | Strictly deterministic reproducibility |
| **Demographic Baseline** | `config/population/india_default_v1.yaml` | Sample Registration System (SRS) 2021 |
| **Hemodynamic Engine** | `LEGACY_CONDITIONAL` (Default) | Validated conditional physiological distributions |
| **Survey Protocol** | `LASI_WAVE1_TRI_MEASUREMENT` v1.0.0 | Triplicate seated blood pressure protocol |
| **Background Mortality** | Enabled (SRS 2016–2020 Life Tables) | Age- and sex-stratified hazard sampling |
| **Analytical Output Path** | `data/synthetic/` | 18 standardized tabular CSVs |
| **Evaluation Verdict** | **PASS** (16 PASS, 0 WARN, 0 FAIL) | Preregistered acceptance bounds |
| **External Validation Gate** | **REFERENCE_DATA_PENDING** | Locked governance status |

---

## 2. Demographic Profile vs. Indian Census Standards

Demographics were sampled to match the **Sample Registration System (SRS) 2021** population age-sex distribution of India.

### 2.1 Sex Distribution
* **Male**: 5,150 (51.50%) — *SRS 2021 Reference: 51.50%* (**PASS**)
* **Female**: 4,850 (48.50%) — *SRS 2021 Reference: 48.50%* (**PASS**)

### 2.2 Age Pyramid Stratification

| Age Band | Total Count | Proportion (%) | Male Count (%) | Female Count (%) | SRS 2021 Benchmark | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **0–14 years** | 2,477 | 24.77% | 1,274 (51.4%) | 1,203 (48.6%) | 25.0% | **PASS** |
| **15–24 years** | 1,745 | 17.45% | 903 (51.7%) | 842 (48.3%) | 17.5% | **PASS** |
| **25–44 years** | 3,161 | 31.61% | 1,634 (51.7%) | 1,527 (48.3%) | 31.5% | **PASS** |
| **45–64 years** | 1,912 | 19.12% | 981 (51.3%) | 931 (48.7%) | 19.0% | **PASS** |
| **65+ years** | 705 | 7.05% | 358 (50.8%) | 347 (49.2%) | 7.0% | **PASS** |
| **Total** | **10,000** | **100.0%** | **5,150 (51.5%)** | **4,850 (48.5%)** | **100.0%** | **PASS** |

* **Adult Subpopulation (Age $\ge 20$, ICMR-INDIAB Standard)**: 6,675 patients (66.75% of total cohort; individuals age $< 20$: 3,325 / 33.25%).
* **Older Adult Subpopulation (Age 45+)**: 2,617 patients in demographic audit (26.17% of total cohort); 2,638 assessed in community survey wave.
* **Age Pyramid Divergence**: Jensen-Shannon Divergence (JSD) $= 0.00005$ ($\le 0.05$ threshold $\rightarrow$ **PASS**).
* **Age-by-Sex Divergence**: Jensen-Shannon Divergence (JSD) $= 0.00013$ ($\le 0.05$ threshold $\rightarrow$ **PASS**).

---

## 3. Disease Progression & Clinical Outcomes

The simulation tracks chronic progression and acute infectious waves across three primary disease modules.

| Condition / Clinical Outcome | Synthetic Count | Synthetic Rate | Reference Benchmark | Acceptance Range | Calibration Source | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Adult Hypertension (Age 20+)** | 2,324 | **34.82%** (period) | 30.7% | [27.0%, 35.0%] | ICMR-INDIAB 2023 | **PASS** |
| **Adult Type 2 Diabetes (Age 20+)** | 932 | **13.96%** (period) | 11.4% | [9.0%, 15.0%] | ICMR-INDIAB 2023 | **PASS** |
| **Comorbid HTN in Diabetic Adults** | 439 | **47.10%** | 50.1% | [40.0%, 60.0%] | ICMR-INDIAB 2023 | **PASS** |
| **Acute URTI Cumulative Attack Rate** | 7,165 | **71.65%** (720d) | 70.0% | [60.0%, 80.0%] | NHP India 2020 | **PASS** |
| **Acute URTI 14-Day Point Prevalence**| 482 | **4.82%** | 8.5% | [3.0%, 12.0%] | NHP India 2020 | **PASS** |
| **All-Cause Mortality (Deaths)** | 255 | **0.01311** /pt-yr | 0.00600 | $\le 0.02000$ | SRS Life Tables | **PASS** |
| **Active Care Plans Formulated** | 3,249 | 32.49% | N/A | N/A | Chronic disease mgmt | **PASS** |

### Staged Microvascular and End-Organ Complications
* **Essential Hypertension**: 2,324 patients.
* **Hypertensive Chronic Kidney Disease**: 24 patients (1.03% complication progression rate).
* **Type 2 Diabetes (Uncomplicated)**: 932 patients.
* **Diabetic Nephropathy**: 18 patients (1.93% complication progression rate).

---

## 4. Medication Pathways & Treatment Guidelines

Prescriptions adhere strictly to the **ICMR Standard Treatment Guidelines (STG) 2022** for hypertension and type 2 diabetes.

| Medication | Drug Class | Target Condition | Total Prescriptions | Prescribing Tier | First-Line Adherence | Status |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **Amoxicillin** | Aminopenicillin Antibiotic | Acute URTI | 7,163 | First-line symptomatic | N/A | **PASS** |
| **Amlodipine** | Dihydropyridine CCB | Hypertension | 2,321 | First-line monotherapy | **99.87%** (Ref: 100%) | **PASS** |
| **Telmisartan** | Angiotensin II Receptor Blocker | Hypertension | 1,664 | Second-line intensification | Stepped care | **PASS** |
| **Metformin** | Biguanide | Type 2 Diabetes | 928 | First-line monotherapy | **99.57%** (Ref: 100%) | **PASS** |
| **Glimepiride** | Sulfonylurea | Type 2 Diabetes | 867 | Second-line intensification | Stepped care | **PASS** |
| **Total** | — | — | **12,943** | — | — | **PASS** |

* **Allergy Safety Rule (`RULE-CLIN-ALLERGY-001`)**: Zero contraindicated prescriptions dispensed across all 12,943 prescription events (**PASS**).

---

## 5. Triplicate Seated Blood Pressure Protocol

At simulation day 360, a community health assessment wave was conducted for surviving older adults (age 45+) implementing the **`LASI_WAVE1_TRI_MEASUREMENT` v1.0.0** protocol.

* **Assessed Participants**: 2,638 older adults.
* **Total Blood Pressure Readings**: 7,914 readings (exactly 3 readings per participant).
* **Incomplete Assessments**: 0.

### Sequential Reading Hemodynamics
* **Reading 1 (Initial Seated)**: Mean SBP $= 130.14 \pm 9.41$ mmHg | Mean DBP $= 80.62 \pm 5.25$ mmHg.
* **Reading 2 (Post-Rest 1)**: Mean SBP $= 126.69 \pm 9.59$ mmHg | Mean DBP $= 79.11 \pm 5.36$ mmHg.
* **Reading 3 (Post-Rest 2)**: Mean SBP $= 126.61 \pm 9.56$ mmHg | Mean DBP $= 79.14 \pm 5.32$ mmHg.
* **Protocol Average (Mean of Readings 2 & 3)**: Mean SBP $= 126.65 \pm 9.54$ mmHg | Mean DBP $= 79.13 \pm 5.31$ mmHg.
* **Habituation Effect**: Initial familiarization drop of **$-3.45$ mmHg SBP** between Reading 1 and Reading 2.
* **Physiological Invariants**:
  * SBP > DBP: 7,914 / 7,914 readings (**100% compliant, 0 violations**).
  * Pulse Pressure $\ge 20$ mmHg: Minimum observed pulse pressure is **$22.60$ mmHg** (**0 violations**).

---

## 6. Canonical Dataset Manifest & Checksums

The synthetic cohort is serialized across 18 tabular CSVs in `data/synthetic/`. All checksums match `DATASET_MANIFEST.json` and `RUN_MANIFEST.json`.

| Filename | Record Count | File Size (Bytes) | SHA-256 Digest |
| :--- | :---: | :---: | :--- |
| `patients.csv` | 10,000 | 561,602 | `7b103bd2d3abc1e59f5cda00eb50049389b0e0ebbf9d82fe805f80b04cc3371b` |
| `encounters.csv` | 21,730 | 2,694,609 | `5ae2ee8005e1ed3c95673186d2967d5b64ebe2aac743d18ebf4774a18b86e948` |
| `conditions.csv` | 10,463 | 1,093,976 | `1dfba3c2742e5085439a1b9fb94317e85988468733c21a6432b554d000851412` |
| `medications.csv` | 12,943 | 1,494,353 | `8f4bb56c5fee0e46884b34530fce615f9f7bf18ff531c153bbc534e28435a834` |
| `symptoms.csv` | 39,444 | 2,915,045 | `d539033374ef27fcb0c7a8fcc4c0d2995baf62140b9c05524e14469290ab5d18` |
| `observations.csv` | 23,198 | 2,385,170 | `61d9c292bb7d686fb967db9d637460d86a6ac0178577585d85edadf517820715` |
| `community_assessments.csv` | 2,638 | 387,898 | `0fefdbddc26a02bf93326cb2b6bd61d8a500bb0115d4e0277d50b3b6f5a7b807` |
| `community_bp_readings.csv` | 7,914 | 1,155,570 | `8415502dffa32630b0704d2bb285f63d4d7b975ef052350b47ffc0ff2fb1008a` |
| `care_plans.csv` | 3,249 | 421,527 | `37b12ad872f78d075bf04916c52215f95cc10ce143da324471495634da00732d` |
| `deaths.csv` | 255 | 25,999 | `8c0f8e79ec60e4a3618f01365a7b883008f8d96d87b5e554a4ccfc391cdcbb39` |
| `generation_summary.csv` | 15 | 357 | `df83712c62fa77692d3c3f150496b2e08ab5803d8cbdd33d8c29855587c3ccf5` |
| `events.csv` | 0 | 80 | `58eb926874781b99b4fa002c1cbe47498f36340ba43559ca875feff0c15a21b7` |
| `invoices.csv` | 0 | 67 | `2f1d4001b78adc830ebeae577cda24abbba11be044837c255ea11585a9731e5c` |
| `journey_traces.csv` | 0 | 77 | `6825c4bb8ab95d39ded492a85098883c81bb402f1403c1e85e81ad8f3c23a245` |
| `labs.csv` | 0 | 81 | `108d77b970776e6d88a1f1ee66dac849b339e92530a7eb3d827390e10dbb85b7` |
| `patient_timeline.csv` | 0 | 67 | `3a0e8d071740b76e0752769bea690e1004edb328f3932fc82b271cde3a26079c` |
| `payments.csv` | 0 | 73 | `e425a99e5a69ec15905dd626bde52054bf874bfae7193b47ad676c2885980c12` |
| `radiology.csv` | 0 | 99 | `2b71576fac1776a0e00aea80b1fb318952d93fb43db85b6cdedf3491b5bdbf5e` |

---

## 7. Governance & External Clinical Validation Lock

> **GOVERNANCE NOTICE**:
> The validation gate status for SYNAPSE Phase 2 remains strictly set to:
>
> $$\mathbf{REFERENCE\_DATA\_PENDING}$$
>
> 1. **Zero Microdata Access**: Neither genuine Longitudinal Ageing Study in India (LASI) microdata nor restricted survey responses were accessed or processed.
> 2. **Engineering vs. Empirical Validation**: All passing metrics reflect statistical calibration against published national survey aggregate tables (SRS 2021, ICMR-INDIAB 2023, NHP 2020) and relational integrity unit tests.
> 3. **Non-Clinical Certification**: Synthetic data outputs must not be represented as an empirical clinical substitute without external validation against authorized reference data.
