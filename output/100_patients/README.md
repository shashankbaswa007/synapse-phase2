# Historical Deliverable: 100-Patient Hospital Operational Run (August 2026)

## Overview & Provenance
This folder preserves historical simulation deliverables generated on **2026-08-28** by the initial discrete-event hospital operational simulator prototype (`HospitalSimulator` / `DocumentGenerator`).

* **Execution Date**: 2026-08-28
* **Patient Count**: 100
* **Architecture**: Discrete-event discrete-time hospital queue, staffing, and departmental workflow
* **Status**: **RETAINED HISTORICAL ARTIFACT** (Preserved for provenance and backward-compatibility reference)

## Included Artifacts
1. `events.jsonl`: Operational event stream (1,002 events) capturing appointment scheduling, triage, physician consultations, laboratory testing, radiology imaging, and pharmacy dispensing.
2. `simulation_results.json`: Execution metrics, rule hits (e.g., `RULE-WORK-OPD-010`, `RULE-GLOB-STOCK-001`, `RULE-CLIN-ALLERGY-001`), and journey completion states for 100 patients.
3. `integrity_report.json`: Document and referential integrity audit for the 100-patient run.
4. `lineage_map.json`: Complete event-causation tree linking ActionRequests, committed events, and generated clinical documents.
5. `documents/`: Rendered operational clinical and administrative documents:
   * `bills/`: Patient billing invoices (124 files).
   * `discharge_summaries/`: Inpatient discharge summaries (124 files).
   * `prescriptions/`: OPD prescriptions (150 files).
   * `lab_reports/`: Laboratory diagnostic results (30 files).
   * `rad_reports/`: Radiology diagnostic reports (30 files).

## Relationship to SYNAPSE Phase 2 Longitudinal Architecture
This operational run reflects early exploratory work on hospital queueing, billing, and document generation. It is superseded by the SYNAPSE Phase 2 Synthea-inspired longitudinal clinical disease simulator (`ExperimentRunner`, YAML state machines for Hypertension, T2D, and URTI, SRS 2021 life tables, and triplicate community BP measurements). These files are preserved intact for historical reference.
