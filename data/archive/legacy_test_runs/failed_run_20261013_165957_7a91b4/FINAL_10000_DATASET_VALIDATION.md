# FINAL SYNTHETIC DATASET VALIDATION REPORT — 100 PATIENTS

**Generated At:** 2026-10-13T16:59:56.499229  
**Completed At:** 2026-10-13T16:59:57.472962  
**Target Directory:** `data\.staging_test_gate_100_d04f33`  
**Simulation Engine:** `HospitalSimulator` (Discrete Event Driven)  
**Knowledge Engine:** `PubMedKnowledgeManager` (Offline Multi-Condition Mesh Evidence)  
**Status / Verdict:** **FAIL — DATASET NOT READY FOR PHASE 3**  

---

## A. GENERATION SUMMARY

- **Requested Patient Count:** 100
- **Actual Unique Patient Count:** 100
- **Generation Status:** FAIL
- **Start Time:** 2026-10-13T16:59:56.499229
- **End Time:** 2026-10-13T16:59:57.472962
- **Total Simulation Duration:** 0.41s
- **Events Processed:** 2,400
- **Random Seed:** 42
- **Configuration:** `enable_pubmed=True`, `offline_mode=True`

---

## B. DATASET INVENTORY

| Filename | Row Count | Column Count | Unique PKs | Duplicate PKs | File Size (KB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | 100 | 6 | 100 | 0 | 9.2 KB | PASS |
| `encounters.csv` | 100 | 8 | 100 | 0 | 11.7 KB | PASS |
| `events.csv` | 1,500 | 7 | 1,500 | 0 | 162.0 KB | PASS |
| `generation_summary.csv` | 15 | 2 | 15 | 0 | 0.4 KB | PASS |
| `invoices.csv` | 100 | 6 | 100 | 0 | 7.0 KB | PASS |
| `journey_traces.csv` | 100 | 7 | 100 | 0 | 8.8 KB | PASS |
| `labs.csv` | 100 | 8 | 100 | 0 | 9.2 KB | PASS |
| `medications.csv` | 100 | 11 | 100 | 0 | 12.9 KB | PASS |
| `patients.csv` | 100 | 7 | 100 | 0 | 5.6 KB | PASS |
| `payments.csv` | 75 | 7 | 75 | 0 | 6.9 KB | PASS |
| `radiology.csv` | 100 | 9 | 100 | 0 | 12.4 KB | PASS |
| `symptoms.csv` | 383 | 5 | 383 | 0 | 27.7 KB | PASS |

---

## C. INVOICE LIFECYCLE

- **Total Invoices:** `100`
- **Invoices Created During Encounter:** `100`
- **Invoices Created Before Encounter:** `0` (Violations: 0)
- **Invoices Created After Encounter:** `0` (Legitimate Delayed Billing)
- **Invoice Status Distribution:** {'Paid': 75, 'Unpaid': 25}
- **Invalid Invoice References:** `0`
- **Invoice Lifecycle Verdict:** **PASS**

---

## D. LABORATORY LIFECYCLE

- **Laboratory Orders:** `100`
- **Sample Collected Events:** `25`
- **Tests Completed:** `25`
- **Pending Tests:** `75`
- **Missing Completion Timestamps:** `0`
- **Abnormal Results Flagged:** `7`
- **Event-to-Record Linkage Failures:** `0`
- **Test Type Distribution:**
  - `C-Reactive Protein`: 5
  - `CBC`: 53
  - `CRP`: 10
  - `Complete Blood Count`: 14
  - `FBS`: 1
  - `Fasting Blood Sugar`: 1
  - `HbA1c`: 1
  - `Lipid Profile Panel`: 4
  - `Liver Function Panel`: 1
  - `Renal_Function`: 1
  - `Urinalysis`: 3
  - `Urine_Culture`: 6
- **Laboratory Lifecycle Verdict:** **PASS**

---

## E. RADIOLOGY LIFECYCLE

- **Radiology Orders:** `100`
- **Acquisition Events:** `25`
- **Completed Studies:** `25`
- **Pending Studies:** `75`
- **Missing Completion Timestamps:** `0`
- **Abnormal Studies Flagged:** `1`
- **Event-to-Record Linkage Failures:** `0`
- **Modality Distribution:**
  - `CT Head`: 1
  - `Chest X-Ray`: 93
  - `Lumbar Spine X-Ray`: 6
- **Radiology Lifecycle Verdict:** **PASS**

---

## F. JOURNEY AND ENCOUNTER CONSISTENCY

- **Journeys Completed:** `75`
- **Encounters Completed/Closed:** `100`
- **Mismatched End Times (`journey.end != enc.end`):** `75`
- **SCEN-V1-02 Premature Journey Finishes:** `0`
- **Scenario-Specific Violations:** `0`
- **Journey/Encounter Consistency Verdict:** **FAIL**

---

## G. MEDICATION AND CONDITION DIVERSITY

- **Total Medication Records:** `100`
- **Distinct Medications:** `26`
- **Distinct Diagnosed Conditions:** `15`
- **Top Medication Frequencies & Shares:**
  - `Paracetamol`: 18 records (18.0%)
  - `Amoxicillin`: 17 records (17.0%)
  - `Cephalexin`: 9 records (9.0%)
  - `Azithromycin`: 8 records (8.0%)
  - `Omeprazole`: 6 records (6.0%)
- **PubMed Provenance Coverage:** `100` records (100.0%)
- **Unverified / Cross-Assigned Indications:** `0`
- **Medication Diversity Verdict:** **PASS**

---

## H. REFERENTIAL INTEGRITY

- **Total Dangling References:** `0`
- **Foreign Key Checks Performed:**
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
- **Referential Integrity Verdict:** **PASS**

---

## I. TEMPORAL AND CAUSAL INTEGRITY

- **Invalid Encounter Durations (`start > end`):** `0`
- **Invalid Temporal Relationships (out-of-order events):** `0`
- **Invalid Terminal States:** `0`
- **Events Left Unprocessed:** `0`
- **Temporal Integrity Verdict:** **PASS**

---

## J. CLINICAL SAFETY AND PROVENANCE

- **Allergy Safety Violations (`RULE-CLIN-ALLERGY-001`):** `0`
- **Invalid State Transitions:** `0`
- **Missing PubMed Evidence:** `0`
- **Invalid Evidence References:** `0`
- **Fabricated PMIDs Detected:** `0`
- **Clinical Safety & Provenance Verdict:** **PASS**

---

## K. PERFORMANCE

- **Total Wall-Clock Runtime:** 0.97s
- **Simulation Runtime:** 0.41s
- **CSV Export Runtime:** 0.1s
- **Throughput:** 5822.0 events/sec, 2847.8 records/sec
- **Total Output Size:** 0.27 MB (280,182 bytes)
- **Failures / Retries:** `0`

---

## L. FINAL VERDICT

### FAIL — DATASET NOT READY FOR PHASE 3
