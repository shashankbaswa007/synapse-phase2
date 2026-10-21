# FINAL SYNTHETIC DATASET VALIDATION REPORT — 10 PATIENTS

**Generated At:** 2026-10-13T16:34:27.514837  
**Completed At:** 2026-10-13T16:34:28.032099  
**Target Directory:** `data\test_stage_b`  
**Simulation Engine:** `HospitalSimulator` (Discrete Event Driven)  
**Knowledge Engine:** `PubMedKnowledgeManager` (Offline Multi-Condition Mesh Evidence)  
**Status / Verdict:** **PASS — DATASET READY FOR PHASE 3**  

---

## A. GENERATION SUMMARY

- **Patients Generated:** 10
- **Generation Status:** PASS
- **Total Simulation Runtime:** 0.03s
- **Total Wall-Clock Runtime:** 0.52s
- **Events Processed:** 236
- **Throughput:** 6777.6 events/second, 554.9 records/second
- **Total Output Size:** 0.03 MB (28,751 bytes)

---

## B. DATASET COUNTS

| Filename | Row Count | Column Count | File Size (KB) | Status |
| :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | 10 | 6 | 1.0 KB | PASS |
| `encounters.csv` | 10 | 8 | 1.2 KB | PASS |
| `events.csv` | 147 | 7 | 15.9 KB | PASS |
| `generation_summary.csv` | 15 | 2 | 0.3 KB | PASS |
| `invoices.csv` | 10 | 6 | 0.8 KB | PASS |
| `journey_traces.csv` | 10 | 7 | 0.9 KB | PASS |
| `labs.csv` | 10 | 8 | 1.0 KB | PASS |
| `medications.csv` | 10 | 11 | 1.4 KB | PASS |
| `patients.csv` | 10 | 7 | 0.6 KB | PASS |
| `payments.csv` | 7 | 7 | 0.7 KB | PASS |
| `radiology.csv` | 10 | 9 | 1.4 KB | PASS |
| `symptoms.csv` | 38 | 5 | 2.8 KB | PASS |

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

- **PubMed-Backed Treatment Records:** `10`
- **Missing Required Evidence IDs:** `0`
- **Invalid Evidence References:** `0`
- **Fabricated PMIDs Detected:** `0`
- **Provenance Integrity Status:** **PASS**

---

## H. DUPLICATE PRIMARY KEY AUDIT

| Dataset | Primary Key | Total Records | Unique IDs | Duplicate IDs | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | `condition_id` | 10 | 10 | 0 | PASS |
| `encounters.csv` | `encounter_id` | 10 | 10 | 0 | PASS |
| `events.csv` | `event_id` | 147 | 147 | 0 | PASS |
| `generation_summary.csv` | `metric_name` | 15 | 15 | 0 | PASS |
| `invoices.csv` | `invoice_id` | 10 | 10 | 0 | PASS |
| `journey_traces.csv` | `journey_id` | 10 | 10 | 0 | PASS |
| `labs.csv` | `lab_id` | 10 | 10 | 0 | PASS |
| `medications.csv` | `medication_id` | 10 | 10 | 0 | PASS |
| `patients.csv` | `patient_id` | 10 | 10 | 0 | PASS |
| `payments.csv` | `payment_id` | 7 | 7 | 0 | PASS |
| `radiology.csv` | `radiology_id` | 10 | 10 | 0 | PASS |
| `symptoms.csv` | `symptom_id` | 38 | 38 | 0 | PASS |

---

## I. SCENARIO DISTRIBUTION

| Scenario ID | Scenario Name | Patient Count | Percentage |
| :--- | :--- | :--- | :--- |
| `SCEN-V1-01` | Routine Outpatient Journey | 3 | 30.0% |
| `SCEN-V1-02` | Outpatient Diagnostic Investigation | 3 | 30.0% |
| `SCEN-V1-03` | Drug Allergy Safety Hold & Alert | 2 | 20.0% |
| `SCEN-V1-04` | Inventory Stock Depletion & Shortage | 2 | 20.0% |

---

## J. PATIENT-LEVEL CONNECTIVITY

- **Total Unique Patients:** `10`
- **Patients with Encounters:** `10` (100.0%)
- **Patients with Conditions:** `10` (100.0%)
- **Patients with Symptoms:** `10` (100.0%)
- **Patients with Medications:** `10` (100.0%)
- **Patients with Diagnostic Labs:** `10`
- **Patients with Diagnostic Radiology:** `10`
- **Patients with Invoices:** `10` (100.0%)
- **Patients with Payments:** `7`
- **Patients with Events:** `10` (100.0%)

---

## K. FINAL VERDICT

### PASS — DATASET READY FOR PHASE 3
