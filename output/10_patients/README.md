# Historical Deliverable: 10-Patient Hospital Operational Run (August 2026)

## Overview & Provenance
This folder preserves historical simulation deliverables generated on **2026-08-28** by the initial discrete-event hospital operational simulator prototype (`HospitalSimulator` / `DocumentGenerator`).

* **Execution Date**: 2026-08-28
* **Patient Count**: 10
* **Architecture**: Discrete-event discrete-time hospital queue and department workflow
* **Status**: **RETAINED HISTORICAL ARTIFACT** (Preserved for provenance and backward-compatibility reference)

## Included Artifacts
1. `events.jsonl`: Discrete operational event stream (126 events) capturing OPD consultations, lab order placement, and medication dispensing.
2. `simulation_results.json`: Execution metrics and department rule-check telemetry for the 10-patient sample.
3. `integrity_report.json`: Historical document validation report (27 generated clinical documents verified).
4. `lineage_map.json`: Causation depth and journey tracing across patient appointment lifecycles.
5. `documents/`: Sample rendered operational documents:
   * `bills/`: Patient billing invoices (20 files).
   * `discharge_summaries/`: Inpatient discharge summaries (20 files).
   * `prescriptions/`: OPD prescriptions (14 files).
   * `lab_reports/`: Laboratory diagnostic results (6 files).
   * `rad_reports/`: Radiology diagnostic reports (6 files).

## Relationship to SYNAPSE Phase 2 Longitudinal Architecture
This historical deliverable is superseded by the Synthea-inspired longitudinal clinical disease progression system located in `data/synthetic/` and documented in `output/SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md`. These files are retained unchanged to maintain operational audit records without modifying the canonical dataset.
