# FINAL SYNTHETIC DATASET VALIDATION REPORT — 1,000 PATIENTS

**Generated At:** 2026-10-13T17:48:53.335895  
**Completed At:** 2026-10-13T17:48:58.235826  
**Target Directory:** `data\.staging_test_gate_1000_c79aee`  
**Simulation Engine:** `HospitalSimulator` (Discrete Event Driven)  
**Knowledge Engine:** `PubMedKnowledgeManager` (Offline Multi-Condition Mesh Evidence)  
**Status / Verdict:** **PASS — DATASET READY FOR PHASE 3**  

---

## A. GENERATION SUMMARY

- **Requested Patient Count:** 1,000
- **Actual Unique Patient Count:** 1,000
- **Generation Status:** PASS
- **Start Time:** 2026-10-13T17:48:53.335895
- **End Time:** 2026-10-13T17:48:58.235826
- **Total Simulation Duration:** 3.68s
- **Events Processed:** 24,000
- **Random Seed:** 42
- **Configuration:** `enable_pubmed=True`, `offline_mode=True`

---

## B. DATASET INVENTORY

| Filename | Row Count | Column Count | Unique PKs | Duplicate PKs | File Size (KB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | 1,000 | 6 | 1,000 | 0 | 90.8 KB | PASS |
| `encounters.csv` | 1,000 | 8 | 1,000 | 0 | 116.3 KB | PASS |
| `events.csv` | 15,000 | 7 | 15,000 | 0 | 1619.0 KB | PASS |
| `generation_summary.csv` | 15 | 2 | 15 | 0 | 0.4 KB | PASS |
| `invoices.csv` | 1,000 | 6 | 1,000 | 0 | 69.9 KB | PASS |
| `journey_traces.csv` | 1,000 | 7 | 1,000 | 0 | 87.2 KB | PASS |
| `labs.csv` | 1,000 | 8 | 1,000 | 0 | 91.4 KB | PASS |
| `medications.csv` | 1,000 | 11 | 1,000 | 0 | 127.5 KB | PASS |
| `patients.csv` | 1,000 | 7 | 1,000 | 0 | 54.9 KB | PASS |
| `payments.csv` | 750 | 7 | 750 | 0 | 68.2 KB | PASS |
| `radiology.csv` | 1,000 | 9 | 1,000 | 0 | 122.6 KB | PASS |
| `symptoms.csv` | 3,771 | 5 | 3,771 | 0 | 272.6 KB | PASS |

---

## C. INVOICE LIFECYCLE

- **Total Invoices:** `1,000`
- **Invoices Created During Encounter:** `1,000`
- **Invoices Created Before Encounter:** `0` (Violations: 0)
- **Invoices Created After Encounter:** `0` (Legitimate Delayed Billing)
- **Invoice Status Distribution:** {'Paid': 750, 'Unpaid': 250}
- **Invalid Invoice References:** `0`
- **Invoice Lifecycle Verdict:** **PASS**

---

## D. LABORATORY LIFECYCLE

- **Laboratory Orders:** `1,000`
- **Sample Collected Events:** `250`
- **Tests Completed:** `250`
- **Pending Tests:** `750`
- **Missing Completion Timestamps:** `0`
- **Abnormal Results Flagged:** `43`
- **Event-to-Record Linkage Failures:** `0`
- **Test Type Distribution:**
  - `C-Reactive Protein`: 32
  - `CBC`: 479
  - `CRP`: 87
  - `Complete Blood Count`: 154
  - `ESR`: 6
  - `Erythrocyte Sedimentation Rate`: 6
  - `FBS`: 12
  - `Fasting Blood Sugar`: 9
  - `Glycated Hemoglobin (HbA1c)`: 5
  - `HbA1c`: 9
  - `Lipid Profile Panel`: 24
  - `Lipid_Panel`: 30
  - `Liver Function Panel`: 8
  - `Liver_Function`: 12
  - `Renal Function Panel`: 9
  - `Renal_Function`: 12
  - `Routine Urinalysis`: 3
  - `Urinalysis`: 60
  - `Urine_Culture`: 43
- **Laboratory Lifecycle Verdict:** **PASS**

---

## E. RADIOLOGY LIFECYCLE

- **Radiology Orders:** `1,000`
- **Acquisition Events:** `250`
- **Completed Studies:** `250`
- **Pending Studies:** `750`
- **Missing Completion Timestamps:** `0`
- **Abnormal Studies Flagged:** `30`
- **Event-to-Record Linkage Failures:** `0`
- **Modality Distribution:**
  - `CT Head`: 13
  - `Chest X-Ray`: 943
  - `Lumbar Spine X-Ray`: 44
- **Radiology Lifecycle Verdict:** **PASS**

---

## F. JOURNEY AND ENCOUNTER CONSISTENCY

- **Journeys Completed:** `750`
- **Encounters Completed/Closed:** `1,000`
- **Mismatched End Times (`journey.end != enc.end`):** `0`
- **SCEN-V1-02 Premature Journey Finishes:** `0`
- **Scenario-Specific Violations:** `0`
- **Journey/Encounter Consistency Verdict:** **PASS**

---

## G. MEDICATION AND CONDITION DIVERSITY

- **Total Medication Records:** `1,000`
- **Distinct Medications:** `37`
- **Distinct Diagnosed Conditions:** `15`
- **Top Medication Frequencies & Shares:**
  - `Paracetamol`: 220 records (22.0%)
  - `Amoxicillin`: 116 records (11.6%)
  - `Cephalexin`: 92 records (9.2%)
  - `Azithromycin`: 62 records (6.2%)
  - `Omeprazole`: 39 records (3.9%)
- **PubMed Provenance Coverage:** `1,000` records (100.0%)
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

- **Total Wall-Clock Runtime:** 4.9s
- **Simulation Runtime:** 3.68s
- **CSV Export Runtime:** 0.21s
- **Throughput:** 6518.6 events/sec, 5619.7 records/sec
- **Total Output Size:** 2.66 MB (2,786,020 bytes)
- **Failures / Retries:** `0`

---

## L. FINAL VERDICT

### PASS — DATASET READY FOR PHASE 3
