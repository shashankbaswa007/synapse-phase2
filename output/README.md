# SYNAPSE Phase 2: Deliverables & Output Directory Catalog

## Overview

This directory (`output/`) contains the validated deliverables, technical reports, data summaries, visualizations, and historical reference archives for **SYNAPSE Phase 2**—a Synthea-inspired synthetic healthcare data generation and longitudinal patient trajectory simulation platform.

---

## 1. Primary SYNAPSE Phase 2 Deliverables

These deliverables represent the active, verified implementation of SYNAPSE Phase 2 based on the canonical 10,000-patient longitudinal cohort ($N=10,000$, seed 42, 720 days, timestep 7 days):

| Deliverable File | Format | Purpose & Description |
| :--- | :---: | :--- |
| **[`SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md`](file:///Users/shashi/synapse/synapse-phase2/output/SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md)** | Markdown | Comprehensive system architecture report covering disease state machines, treatment workflows, dual hemodynamic engines, triplicate BP protocol, and reproducibility instructions. |
| **[`LONGITUDINAL_COHORT_SUMMARY_10000.md`](file:///Users/shashi/synapse/synapse-phase2/output/LONGITUDINAL_COHORT_SUMMARY_10000.md)** | Markdown | Complete tabular summary of the 10,000-patient cohort: demographics, disease period prevalences, medication pathways, and survey findings. |
| **[`LONGITUDINAL_COHORT_SUMMARY_10000.json`](file:///Users/shashi/synapse/synapse-phase2/output/LONGITUDINAL_COHORT_SUMMARY_10000.json)** | JSON | Machine-readable metadata export of cohort metrics, table record counts, demographic stratifications, and SHA-256 digests. |
| **[`CLINICAL_EVALUATION_REPORT.md`](file:///Users/shashi/synapse/synapse-phase2/output/CLINICAL_EVALUATION_REPORT.md)** | Markdown | Comprehensive clinical evaluation report across 21 preregistered metrics (16 PASS, 0 WARN, 0 FAIL, 5 UNVERIFIED). |
| **[`simulation_results.json`](file:///Users/shashi/synapse/synapse-phase2/output/simulation_results.json)** | JSON | Master simulation run results, performance telemetry, and demographic breakdowns for the 10,000-patient cohort. |
| **[`integrity_report.json`](file:///Users/shashi/synapse/synapse-phase2/output/integrity_report.json)** | JSON | Deep dataset integrity audit verifying 0 primary-key collisions, 0 foreign-key dangling references, and 0 clinical safety invariant violations. |
| **[`lineage_map.json`](file:///Users/shashi/synapse/synapse-phase2/output/lineage_map.json)** | JSON | End-to-end data lineage tracing from demographic initialization (SRS 2021) through disease progression, hemodynamics, and CSV serialization. |

---

## 2. Publication-Grade Vector Visualizations (`visualizations/`)

Located in [`output/visualizations/`](file:///Users/shashi/synapse/synapse-phase2/output/visualizations/):

* **[`demographic_age_pyramid.svg`](file:///Users/shashi/synapse/synapse-phase2/output/visualizations/demographic_age_pyramid.svg)**: 5-band age-by-sex population pyramid comparing the synthetic cohort against SRS 2021 India Census benchmarks.
* **[`blood_pressure_distributions.svg`](file:///Users/shashi/synapse/synapse-phase2/output/visualizations/blood_pressure_distributions.svg)**: Sequential SBP/DBP trajectory across the triplicate seated blood pressure protocol (`LASI_WAVE1_TRI_MEASUREMENT` v1.0.0, $N=2,638$, 7,914 readings) demonstrating the $-3.45$ mmHg habituation drop.
* **[`disease_prevalence_comparison.svg`](file:///Users/shashi/synapse/synapse-phase2/output/visualizations/disease_prevalence_comparison.svg)**: Grouped benchmark chart comparing adult Hypertension, Type 2 Diabetes, comorbidity, and acute URTI rates against ICMR-INDIAB and NHP benchmarks.
* **[`simulation_architecture_workflow.svg`](file:///Users/shashi/synapse/synapse-phase2/output/visualizations/simulation_architecture_workflow.svg)**: System flow diagram illustrating the full 7-stage simulation lifecycle, from demographic sampling to the validation gate.
* **[`visualizations/README.md`](file:///Users/shashi/synapse/synapse-phase2/output/visualizations/README.md)**: Visualizations catalog and technical interpretation notes.

---

## 3. Historical Reference Archives

The subfolders below preserve historical deliverables from earlier discrete-event hospital operational modeling (August–September 2026). They are preserved for auditability and regression verification of `--mode hospital`:

* **[`output/phase2/`](file:///Users/shashi/synapse/synapse-phase2/output/phase2/)** ([`README.md`](file:///Users/shashi/synapse/synapse-phase2/output/phase2/README.md)): 100-patient hospital operational database run from September 2026 (departments, rooms, staff shifts, pharmacy inventory batches, billing receipts).
* **[`output/documents/`](file:///Users/shashi/synapse/synapse-phase2/output/documents/)** ([`README.md`](file:///Users/shashi/synapse/synapse-phase2/output/documents/README.md)): 230 synthesized text clinical documents (bills, discharge summaries, prescriptions) from August 2026.
* **[`output/10_patients/`](file:///Users/shashi/synapse/synapse-phase2/output/10_patients/)** ([`README.md`](file:///Users/shashi/synapse/synapse-phase2/output/10_patients/README.md)): 10-patient historical discrete-event hospital sample run from August 2026.
* **[`output/100_patients/`](file:///Users/shashi/synapse/synapse-phase2/output/100_patients/)** ([`README.md`](file:///Users/shashi/synapse/synapse-phase2/output/100_patients/README.md)): 100-patient historical discrete-event hospital sample run from August 2026.
* **`output/events.jsonl`**: Historical discrete-event stream from the early hospital prototype.

---

## 4. Cross-Reference to Canonical Dataset

The official generated synthetic dataset for SYNAPSE Phase 2 is maintained at:
```
data/synthetic/
```
Containing:
* 18 tabular CSV files (`patients.csv`, `encounters.csv`, `conditions.csv`, `medications.csv`, `symptoms.csv`, `observations.csv`, `community_assessments.csv`, `community_bp_readings.csv`, `care_plans.csv`, `deaths.csv`, etc.).
* `DATASET_MANIFEST.json` and `RUN_MANIFEST.json` with authoritative SHA-256 checksums.
* `FINAL_10000_DATASET_VALIDATION.json` and `FINAL_10000_DATASET_VALIDATION.md`.

---

## 5. Scientific Governance Statement

> **EXTERNAL VALIDATION GATE STATUS**:
>
> $$\mathbf{REFERENCE\_DATA\_PENDING}$$
>
> In accordance with scientific integrity guidelines:
> 1. No genuine individual participant microdata (from LASI Wave 1 or other restricted clinical sources) were accessed or processed.
> 2. All passing evaluations reflect engineering invariants and statistical calibration against public national aggregate statistics.
> 3. Clinical defaults and model parameters remain intact and unmanipulated.
