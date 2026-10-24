# Historical Deliverable: Phase 2 Hospital Operational Run (September 2026)

## Overview & Provenance
This folder preserves historical simulation deliverables generated on **2026-09-02** by the exploratory hospital operational modeling suite (`HospitalSimulator` via `--mode hospital`).

* **Execution Date**: 2026-09-02
* **Patient Count**: 100
* **Architecture**: Discrete-event hospital departmental database schema (12 subdomains)
* **Status**: **RETAINED HISTORICAL ARTIFACT** (Preserved for backward-compatibility verification of `--mode hospital`)

## Folder Structure & Domain Schemas
* `master_data/`: Hospital configuration (departments, rooms, staff, doctors, nurses, medicine formulary).
* `patients/`: Patient demographics, allergies, medical history, chronic conditions, insurance, family history.
* `clinical/`: Appointments, consultations, clinical notes.
* `pharmacy/`: Prescriptions, medication dispensing records, pharmacy transactions.
* `diagnostics/`: Lab orders, lab samples, radiology orders.
* `operational/`: Room utilization, staff shift assignments.
* `billing/`: Inpatient/outpatient bills and payment receipts.
* `journeys/`: Patient journey status and step-level transitions.
* `events/`: Event stream dump.
* `metadata/`: Simulation metadata and run execution parameters.
* `validation/`: Integrity rule logs.
* `documents/`: Rendered clinical documents (bills, discharge summaries, prescriptions, lab and radiology reports).

## Relationship to SYNAPSE Phase 2 Canonical Architecture
In October 2026, SYNAPSE Phase 2 was unified around a Synthea-inspired longitudinal clinical state-machine architecture that models disease onset, chronic progression, medication escalation, community assessment waves, and background mortality across multi-year observation windows.

The canonical 10,000-patient longitudinal dataset is stored at `data/synthetic/` and documented in `output/SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md`. The files in `output/phase2/` are preserved as a historical snapshot of the discrete-event operational simulator.
