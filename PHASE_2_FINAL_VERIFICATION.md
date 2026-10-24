# SYNAPSE Phase 2 — Final System & Dataset Verification Report

**Project:** SYNAPSE — Longitudinal Synthetic Healthcare Data Generation Platform  
**Phase:** Phase 2 (Synthea-Inspired Longitudinal Population Simulator)  
**Status:** **COMPLETE — CANONICAL DATASET VERIFIED & RELEASE READY**  
**Canonical Cohort:** [`data/synthetic/`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/) ($N=10,000$, Seed 42, 720 Days, Timestep 7 Days)  
**Simulation Architecture:** `ExperimentRunner` (Declarative YAML State Machines & Forward Hemodynamics)  
**External Validation Gate:** `REFERENCE_DATA_PENDING`  
**Date:** 2026-10-24  

---

## 1. Executive Summary

This report establishes the final verification and acceptance of the **SYNAPSE Phase 2 canonical synthetic healthcare dataset**. The active implementation is the **Synthea-inspired longitudinal population healthcare simulator**, which models continuous synthetic patient lifetimes, chronic disease progression (hypertension, type 2 diabetes, acute URTI), clinical encounters, stepped-care treatment regimens, continuous hemodynamics, background all-cause life-table mortality, and community blood pressure surveys.

The earlier discrete-event hospital operational prototype (modeling queues, beds, inventory, and departmental billing) has been superseded and is maintained strictly as an isolated backward-compatibility mode (`--mode hospital`), with historical documentation preserved in [`docs/architecture/legacy_hospital_prototype/`](file:///Users/shashi/synapse/synapse-phase2/docs/architecture/legacy_hospital_prototype/).

---

## 2. Canonical Release Cohort Specification

The canonical Phase 2 release cohort is published in [`data/synthetic/`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/):

* **Patient Count:** 10,000 synthetic individuals
* **Random Seed:** `42` (100% deterministic reproducibility)
* **Observation Window:** 720 days (24 months, 2024-01-01 to 2025-12-22)
* **Simulation Timestep:** 7 days ($\Delta t = 7\text{ days}$)
* **Population Profile:** Census SRS 2021 India Profile ([`config/population/india_default_v1.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/population/india_default_v1.yaml))
* **Disease Progression Modules:**
  - Essential Hypertension ([`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml))
  - Type 2 Diabetes Mellitus ([`config/modules/diabetes_t2.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/diabetes_t2.yaml))
  - Acute URTI ([`config/modules/urti.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/urti.yaml))
* **Hemodynamic Engine Mode:** `LEGACY_CONDITIONAL` (default; `FORWARD_STATE_SPACE` supported as experimental opt-in)
* **Community Blood Pressure Protocol:** `LASI_WAVE1_TRI_MEASUREMENT` v1.0.0 (3 seated triplicate readings for older adults age $\ge 45$)

---

## 3. Relational Table Inventory & Cryptographic Manifest

All 18 exported relational CSV files match their authoritative SHA-256 checksums in [`data/synthetic/RUN_MANIFEST.json`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/RUN_MANIFEST.json) and [`DATASET_MANIFEST.json`](file:///Users/shashi/synapse/synapse-phase2/DATASET_MANIFEST.json):

| CSV Filename | Row Count | Column Count | Unique PKs | Duplicate PKs | File Size | SHA-256 Digest | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| `patients.csv` | 10,000 | 7 | 10,000 | 0 | 548.4 KB | `7b103bd2d3abc1e59f5cda00eb50049389b0e0ebbf9d82fe805f80b04cc3371b` | **MATCH** |
| `encounters.csv` | 21,730 | 8 | 21,730 | 0 | 2,631.4 KB | `5ae2ee8005e1ed3c95673186d2967d5b64ebe2aac743d18ebf4774a18b86e948` | **MATCH** |
| `conditions.csv` | 10,463 | 6 | 10,463 | 0 | 1,068.3 KB | `1dfba3c2742e5085439a1b9fb94317e85988468733c21a6432b554d000851412` | **MATCH** |
| `medications.csv` | 12,943 | 11 | 12,943 | 0 | 1,459.3 KB | `8f4bb56c5fee0e46884b34530fce615f9f7bf18ff531c153bbc534e28435a834` | **MATCH** |
| `symptoms.csv` | 39,444 | 5 | 39,444 | 0 | 2,846.7 KB | `d539033374ef27fcb0c7a8fcc4c0d2995baf62140b9c05524e14469290ab5d18` | **MATCH** |
| `observations.csv` | 23,198 | 9 | 23,198 | 0 | 2,329.3 KB | `61d9c292bb7d686fb967db9d637460d86a6ac0178577585d85edadf517820715` | **MATCH** |
| `care_plans.csv` | 3,249 | 8 | 3,249 | 0 | 411.6 KB | `37b12ad872f78d075bf04916c52215f95cc10ce143da324471495634da00732d` | **MATCH** |
| `deaths.csv` | 255 | 6 | 255 | 0 | 25.4 KB | `8c0f8e79ec60e4a3618f01365a7b883008f8d96d87b5e554a4ccfc391cdcbb39` | **MATCH** |
| `community_assessments.csv` | 2,638 | 11 | 2,638 | 0 | 378.8 KB | `0fefdbddc26a02bf93326cb2b6bd61d8a500bb0115d4e0277d50b3b6f5a7b807` | **MATCH** |
| `community_bp_readings.csv` | 7,914 | 12 | 7,914 | 0 | 1,128.5 KB | `8415502dffa32630b0704d2bb285f63d4d7b975ef052350b47ffc0ff2fb1008a` | **MATCH** |
| `generation_summary.csv` | 15 | 2 | 15 | 0 | 0.3 KB | `df83712c62fa77692d3c3f150496b2e08ab5803d8cbdd33d8c29855587c3ccf5` | **MATCH** |
| `patient_timeline.csv` | 0 | 5 | 0 | 0 | 0.1 KB | `3a0e8d071740b76e0752769bea690e1004edb328f3932fc82b271cde3a26079c` | **MATCH** |
| `labs.csv` | 0 | 8 | 0 | 0 | 0.1 KB | `108d77b970776e6d88a1f1ee66dac849b339e92530a7eb3d827390e10dbb85b7` | **MATCH** |
| `radiology.csv` | 0 | 9 | 0 | 0 | 0.1 KB | `2b71576fac1776a0e00aea80b1fb318952d93fb43db85b6cdedf3491b5bdbf5e` | **MATCH** |
| `invoices.csv` | 0 | 6 | 0 | 0 | 0.1 KB | `2f1d4001b78adc830ebeae577cda24abbba11be044837c255ea11585a9731e5c` | **MATCH** |
| `payments.csv` | 0 | 7 | 0 | 0 | 0.1 KB | `e425a99e5a69ec15905dd626bde52054bf874bfae7193b47ad676c2885980c12` | **MATCH** |
| `events.csv` | 0 | 7 | 0 | 0 | 0.1 KB | `58eb926874781b99b4fa002c1cbe47498f36340ba43559ca875feff0c15a21b7` | **MATCH** |
| `journey_traces.csv` | 0 | 7 | 0 | 0 | 0.1 KB | `6825c4bb8ab95d39ded492a85098883c81bb402f1403c1e85e81ad8f3c23a245` | **MATCH** |

---

## 4. Verification Dimensions & Acceptance Verdicts

### 4.1 Structural & Referential Integrity
- **Primary Key Collisions:** `0` collisions across all 18 tables.
- **Foreign Key Dangling References:** `0` dangling references (`patient_id`, `encounter_id`).
- **Required Field NULLs:** `0` missing values across mandatory clinical attributes.
- **Encounter Duration Validity:** `100%` valid ($t_{\text{end}} \ge t_{\text{start}}$).
- **Temporal Ordering:** `100%` valid ($t_{\text{birth}} \le t_{\text{event}} \le t_{\text{death}}$).

### 4.2 Clinical Safety & Domain Invariants
- **Allergy Contraindications:** `0` violations (`RULE-CLIN-ALLERGY-001` enforced).
- **Deceased Event Integrity:** `0` post-mortem encounters, orders, or prescriptions (`deaths.csv` enforced).
- **Physiological Limits:** $100\%$ valid seated blood pressures ($\text{SBP} > \text{DBP}$, pulse pressure $\ge 20\text{ mmHg}$, $70 \le \text{SBP} \le 260$, $40 \le \text{DBP} \le 160$).
- **Triplicate Survey Protocol:** Exactly 3 readings per assessed patient ($7,914 / 2,638 = 3.000$).
- **Habituation Drop:** Validated biophysical habituation effect from reading 1 to reading 3 ($-3.45\text{ mmHg}$ systolic drop).

### 4.3 Preregistered Clinical Acceptance Matrix
Evaluated via `DatasetEvaluator` across 21 benchmarks:
- **PASS:** 16 metrics (Sex distribution, Age pyramid JSD, Age-by-sex JSD, Adult hypertension prevalence, Adult T2D prevalence, Hypertension in T2D comorbidity, URTI 14-day point prevalence, URTI cumulative attack rate, Encounters per patient-year, Inter-encounter interval, Crude mortality rate, Person-time bounds, Encounter linkage, Prescription safety, Physiological BP limits, BP triplicate protocol).
- **WARN:** 0 metrics.
- **FAIL:** 0 metrics.
- **UNVERIFIED:** 5 metrics (Strictly locked under `REFERENCE_DATA_PENDING` awaiting authorized external reference ingestion).

---

## 5. Scientific Governance Statement

> **EXTERNAL VALIDATION GATE STATUS**:
>
> $$\mathbf{REFERENCE\_DATA\_PENDING}$$
>
> In accordance with research integrity standards:
> 1. No genuine individual participant microdata (from LASI Wave 1 or other restricted sources) were accessed or processed.
> 2. All evaluations reflect engineering invariants and statistical calibration against public national aggregate statistics (SRS 2021, ICMR-INDIAB 2023, NHP 2020).
> 3. Clinical defaults and model parameters remain intact and unmanipulated.

---

## 6. Execution Verification

The canonical dataset can be verified or re-evaluated at any time using:

```bash
# Verify integrity and clinical invariants of the canonical release
python evaluate_dataset.py --dataset-dir data/synthetic

# Run the complete test suite (374 automated tests)
pytest tests/
```

**Final Acceptance Verdict:** **PASS — CANONICAL SYNTHETIC DATASET READY FOR PHASE 3**
