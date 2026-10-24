# FINAL SYNTHETIC DATASET VALIDATION REPORT — 1,000 PATIENTS

**Generated At:** 2026-10-13T16:34:48.088803  
**Completed At:** 2026-10-13T16:35:03.314535  
**Target Directory:** `data\test_stage_d`  
**Simulation Engine:** `HospitalSimulator` (Discrete Event Driven)  
**Knowledge Engine:** `PubMedKnowledgeManager` (Offline Multi-Condition Mesh Evidence)  
**Status / Verdict:** **PASS — DATASET READY FOR PHASE 3**  

---

## A. GENERATION SUMMARY

- **Patients Generated:** 1,000
- **Generation Status:** PASS
- **Total Simulation Runtime:** 14.12s
- **Total Wall-Clock Runtime:** 15.23s
- **Events Processed:** 24,000
- **Throughput:** 1699.4 events/second, 1808.5 records/second
- **Total Output Size:** 2.66 MB (2,786,020 bytes)

---

## B. DATASET COUNTS

| Filename | Row Count | Column Count | File Size (KB) | Status |
| :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | 1,000 | 6 | 90.8 KB | PASS |
| `encounters.csv` | 1,000 | 8 | 116.3 KB | PASS |
| `events.csv` | 15,000 | 7 | 1619.0 KB | PASS |
| `generation_summary.csv` | 15 | 2 | 0.4 KB | PASS |
| `invoices.csv` | 1,000 | 6 | 69.9 KB | PASS |
| `journey_traces.csv` | 1,000 | 7 | 87.2 KB | PASS |
| `labs.csv` | 1,000 | 8 | 91.4 KB | PASS |
| `medications.csv` | 1,000 | 11 | 127.5 KB | PASS |
| `patients.csv` | 1,000 | 7 | 54.9 KB | PASS |
| `payments.csv` | 750 | 7 | 68.2 KB | PASS |
| `radiology.csv` | 1,000 | 9 | 122.6 KB | PASS |
| `symptoms.csv` | 3,771 | 5 | 272.6 KB | PASS |

---

## C. REFERENTIAL INTEGRITY AUDIT

- **Total Dangling References:** `0`
- **Foreign Key Audits Performed:**
  - `encounters.patient_id` -> `patients.patient_id`: 0 dangling
  - `conditions.patient_id` -> `patients.patient_id`: 0 dangling
  - `conditions.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `symptoms.patient_id` -> `patients.patient_id`: 0 dangling
  - `symptoms.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `symptoms.condition_id` -> `conditions.condition_id`: 0 dangling
  - `medications.patient_id` -> `patients.patient_id`: 0 dangling
  - `medications.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `medications.condition_id` -> `conditions.condition_id`: 0 dangling
  - `labs.patient_id` -> `patients.patient_id`: 0 dangling
  - `labs.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `radiology.patient_id` -> `patients.patient_id`: 0 dangling
  - `radiology.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `invoices.patient_id` -> `patients.patient_id`: 0 dangling
  - `invoices.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `payments.invoice_id` -> `invoices.invoice_id`: 0 dangling
  - `payments.patient_id` -> `patients.patient_id`: 0 dangling
  - `events.patient_id` -> `patients.patient_id`: 0 dangling
  - `events.encounter_id` -> `encounters.encounter_id`: 0 dangling
  - `journey_traces.patient_id` -> `patients.patient_id`: 0 dangling
- **Referential Integrity Status:** **PASS**

---

## D. NULL / REQUIRED FIELD AUDIT

- **Total Required NULLs:** `0`
- **Required Field Integrity Status:** **PASS (100% Non-Null)**

| Dataset | Column | Required? | NULL Count | Status |
| :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | `condition_code` | Yes | 0 | PASS |
| `conditions.csv` | `condition_id` | Yes | 0 | PASS |
| `conditions.csv` | `condition_name` | Yes | 0 | PASS |
| `conditions.csv` | `encounter_id` | Yes | 0 | PASS |
| `conditions.csv` | `patient_id` | Yes | 0 | PASS |
| `conditions.csv` | `status` | Yes | 0 | PASS |
| `encounters.csv` | `chief_complaint` | Yes | 0 | PASS |
| `encounters.csv` | `doctor_id` | Yes | 0 | PASS |
| `encounters.csv` | `encounter_id` | Yes | 0 | PASS |
| `encounters.csv` | `end_time` | Yes | 0 | PASS |
| `encounters.csv` | `journey_id` | Yes | 0 | PASS |
| `encounters.csv` | `patient_id` | Yes | 0 | PASS |
| `encounters.csv` | `start_time` | Yes | 0 | PASS |
| `encounters.csv` | `status` | Yes | 0 | PASS |
| `events.csv` | `event_id` | Yes | 0 | PASS |
| `events.csv` | `event_type` | Yes | 0 | PASS |
| `events.csv` | `source_department` | Yes | 0 | PASS |
| `events.csv` | `status` | Yes | 0 | PASS |
| `events.csv` | `timestamp` | Yes | 0 | PASS |
| `generation_summary.csv` | `metric_name` | Yes | 0 | PASS |
| `generation_summary.csv` | `metric_value` | Yes | 0 | PASS |
| `invoices.csv` | `created_at` | Yes | 0 | PASS |
| `invoices.csv` | `encounter_id` | Yes | 0 | PASS |
| `invoices.csv` | `invoice_id` | Yes | 0 | PASS |
| `invoices.csv` | `patient_id` | Yes | 0 | PASS |
| `invoices.csv` | `status` | Yes | 0 | PASS |
| `invoices.csv` | `total_amount` | Yes | 0 | PASS |
| `journey_traces.csv` | `completed_at` | Yes | 0 | PASS |
| `journey_traces.csv` | `journey_id` | Yes | 0 | PASS |
| `journey_traces.csv` | `patient_id` | Yes | 0 | PASS |
| `journey_traces.csv` | `scenario_id` | Yes | 0 | PASS |
| `journey_traces.csv` | `started_at` | Yes | 0 | PASS |
| `journey_traces.csv` | `status` | Yes | 0 | PASS |
| `journey_traces.csv` | `step_count` | Yes | 0 | PASS |
| `labs.csv` | `encounter_id` | Yes | 0 | PASS |
| `labs.csv` | `is_abnormal` | Yes | 0 | PASS |
| `labs.csv` | `lab_id` | Yes | 0 | PASS |
| `labs.csv` | `patient_id` | Yes | 0 | PASS |
| `labs.csv` | `result` | Yes | 0 | PASS |
| `labs.csv` | `status` | Yes | 0 | PASS |
| `labs.csv` | `test_name` | Yes | 0 | PASS |
| `medications.csv` | `condition_id` | Yes | 0 | PASS |
| `medications.csv` | `dosage` | Yes | 0 | PASS |
| `medications.csv` | `drug_name` | Yes | 0 | PASS |
| `medications.csv` | `encounter_id` | Yes | 0 | PASS |
| `medications.csv` | `frequency` | Yes | 0 | PASS |
| `medications.csv` | `medication_id` | Yes | 0 | PASS |
| `medications.csv` | `patient_id` | Yes | 0 | PASS |
| `medications.csv` | `source` | Yes | 0 | PASS |
| `medications.csv` | `status` | Yes | 0 | PASS |
| `patients.csv` | `age` | Yes | 0 | PASS |
| `patients.csv` | `blood_group` | Yes | 0 | PASS |
| `patients.csv` | `gender` | Yes | 0 | PASS |
| `patients.csv` | `insurance_type` | Yes | 0 | PASS |
| `patients.csv` | `name` | Yes | 0 | PASS |
| `patients.csv` | `patient_id` | Yes | 0 | PASS |
| `patients.csv` | `status` | Yes | 0 | PASS |
| `payments.csv` | `amount` | Yes | 0 | PASS |
| `payments.csv` | `invoice_id` | Yes | 0 | PASS |
| `payments.csv` | `patient_id` | Yes | 0 | PASS |
| `payments.csv` | `payment_id` | Yes | 0 | PASS |
| `payments.csv` | `payment_method` | Yes | 0 | PASS |
| `payments.csv` | `status` | Yes | 0 | PASS |
| `payments.csv` | `timestamp` | Yes | 0 | PASS |
| `radiology.csv` | `encounter_id` | Yes | 0 | PASS |
| `radiology.csv` | `findings` | Yes | 0 | PASS |
| `radiology.csv` | `impression` | Yes | 0 | PASS |
| `radiology.csv` | `is_abnormal` | Yes | 0 | PASS |
| `radiology.csv` | `modality` | Yes | 0 | PASS |
| `radiology.csv` | `patient_id` | Yes | 0 | PASS |
| `radiology.csv` | `radiology_id` | Yes | 0 | PASS |
| `radiology.csv` | `status` | Yes | 0 | PASS |
| `symptoms.csv` | `condition_id` | Yes | 0 | PASS |
| `symptoms.csv` | `encounter_id` | Yes | 0 | PASS |
| `symptoms.csv` | `patient_id` | Yes | 0 | PASS |
| `symptoms.csv` | `symptom_id` | Yes | 0 | PASS |
| `symptoms.csv` | `symptom_name` | Yes | 0 | PASS |

---

## E. TEMPORAL AUDIT

- **Invalid Encounter Durations (start > end):** `0`
- **Invalid Temporal Relationships (out-of-order events):** `0`
- **Temporal Integrity Status:** **PASS**

---

## F. CLINICAL / RULE INTEGRITY

- **Allergy Safety Violations (`RULE-CLIN-ALLERGY-001`):** `0`
- **Invalid State Transitions:** `0`
- **Clinical Safety Integrity Status:** **PASS**

---

## G. PUBMED PROVENANCE AUDIT

- **PubMed-Backed Treatment Records:** `1,000`
- **Missing Required Evidence IDs:** `0`
- **Invalid Evidence References:** `0`
- **Fabricated PMIDs Detected:** `0`
- **Provenance Integrity Status:** **PASS**

---

## H. DUPLICATE PRIMARY KEY AUDIT

| Dataset | Primary Key | Total Records | Unique IDs | Duplicate IDs | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | `condition_id` | 1,000 | 1,000 | 0 | PASS |
| `encounters.csv` | `encounter_id` | 1,000 | 1,000 | 0 | PASS |
| `events.csv` | `event_id` | 15,000 | 15,000 | 0 | PASS |
| `generation_summary.csv` | `metric_name` | 15 | 15 | 0 | PASS |
| `invoices.csv` | `invoice_id` | 1,000 | 1,000 | 0 | PASS |
| `journey_traces.csv` | `journey_id` | 1,000 | 1,000 | 0 | PASS |
| `labs.csv` | `lab_id` | 1,000 | 1,000 | 0 | PASS |
| `medications.csv` | `medication_id` | 1,000 | 1,000 | 0 | PASS |
| `patients.csv` | `patient_id` | 1,000 | 1,000 | 0 | PASS |
| `payments.csv` | `payment_id` | 750 | 750 | 0 | PASS |
| `radiology.csv` | `radiology_id` | 1,000 | 1,000 | 0 | PASS |
| `symptoms.csv` | `symptom_id` | 3,771 | 3,771 | 0 | PASS |

---

## I. SCENARIO DISTRIBUTION

| Scenario ID | Scenario Name | Patient Count | Percentage |
| :--- | :--- | :--- | :--- |
| `SCEN-V1-01` | Routine Outpatient Journey | 250 | 25.0% |
| `SCEN-V1-02` | Outpatient Diagnostic Investigation | 250 | 25.0% |
| `SCEN-V1-03` | Drug Allergy Safety Hold & Alert | 250 | 25.0% |
| `SCEN-V1-04` | Inventory Stock Depletion & Shortage | 250 | 25.0% |

---

## J. PATIENT-LEVEL CONNECTIVITY

- **Total Unique Patients:** `1,000`
- **Patients with Encounters:** `1,000` (100.0%)
- **Patients with Conditions:** `1,000` (100.0%)
- **Patients with Symptoms:** `1,000` (100.0%)
- **Patients with Medications:** `1,000` (100.0%)
- **Patients with Diagnostic Labs:** `1,000`
- **Patients with Diagnostic Radiology:** `1,000`
- **Patients with Invoices:** `1,000` (100.0%)
- **Patients with Payments:** `750`
- **Patients with Events:** `1,000` (100.0%)

---

## K. FINAL VERDICT

### PASS — DATASET READY FOR PHASE 3
