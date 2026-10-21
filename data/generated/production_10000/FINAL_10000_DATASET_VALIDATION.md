# FINAL SYNTHETIC DATASET VALIDATION REPORT — 10,000 PATIENTS

**Generated At:** 2026-10-13T18:49:44.883298  
**Completed At:** 2026-10-13T18:50:03.177595  
**Target Directory:** `C:\AI\synapse phase2\data\generated\production_10000`  
**Simulation Engine:** `HospitalSimulator` (Discrete Event Driven)  
**Knowledge Engine:** `PubMedKnowledgeManager` (Offline Multi-Condition Mesh Evidence)  
**Status / Verdict:** **PASS — DATASET READY FOR PHASE 3**  

---

## A. GENERATION SUMMARY

- **Requested Patient Count:** 10,000
- **Actual Unique Patient Count:** 10,000
- **Generation Status:** PASS
- **Start Time:** 2026-10-13T18:49:44.883298
- **End Time:** 2026-10-13T18:50:03.177595
- **Total Simulation Duration:** 13.62s
- **Events Processed:** 112,500
- **Random Seed:** 42
- **Configuration:** `enable_pubmed=True`, `offline_mode=True`

---

## B. DATASET INVENTORY

| Filename | Row Count | Column Count | Unique PKs | Duplicate PKs | File Size (KB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `conditions.csv` | 10,000 | 6 | 10,000 | 0 | 908.3 KB | PASS |
| `encounters.csv` | 10,000 | 8 | 10,000 | 0 | 1162.2 KB | PASS |
| `events.csv` | 57,500 | 7 | 57,500 | 0 | 5749.6 KB | PASS |
| `generation_summary.csv` | 15 | 2 | 15 | 0 | 0.4 KB | PASS |
| `invoices.csv` | 10,000 | 6 | 10,000 | 0 | 693.4 KB | PASS |
| `journey_traces.csv` | 10,000 | 7 | 10,000 | 0 | 869.2 KB | PASS |
| `labs.csv` | 10,000 | 8 | 10,000 | 0 | 775.2 KB | PASS |
| `medications.csv` | 10,000 | 11 | 10,000 | 0 | 1273.2 KB | PASS |
| `patients.csv` | 10,000 | 7 | 10,000 | 0 | 549.0 KB | PASS |
| `payments.csv` | 10,000 | 7 | 10,000 | 0 | 908.3 KB | PASS |
| `radiology.csv` | 10,000 | 9 | 10,000 | 0 | 1085.1 KB | PASS |
| `symptoms.csv` | 37,652 | 5 | 37,652 | 0 | 2724.1 KB | PASS |

---

## C. INVOICE LIFECYCLE

- **Total Invoices:** `10,000`
- **Invoice Generated Events:** `10,000`
- **Paid Invoices:** `10,000`
- **Unpaid Invoices:** `0`
- **Payments Generated:** `10,000`
- **Payment Processed Events:** `10,000`
- **Invoices Created During Encounter:** `10,000`
- **Invoices Created Before Encounter:** `0`
- **Invoices Created After Encounter:** `0` (Legitimate Delayed Billing)
- **Invoice Status Distribution:** {'Paid': 10000}
- **Lifecycle Violations Total:** `0`
- **Invoice Lifecycle Verdict:** **PASS**

---

## D. LABORATORY LIFECYCLE

- **Laboratory Orders:** `10,000`
- **Completed Tests:** `2,500`
- **Pending Tests (Ordered):** `7,500`
- **Sample Collected Events:** `2,500`
- **Result Completed Events:** `2,500`
- **Ordered With Completed Timestamp Violations:** `0`
- **Completed Missing Timestamp Violations:** `0`
- **Event-to-Record Linkage Failures:** `0`
- **Lifecycle Violations Total:** `0`
- **Abnormal Results Flagged:** `396`
- **Test Type Distribution:**
  - `C-Reactive Protein`: 324
  - `CBC`: 4,598
  - `CRP`: 926
  - `Complete Blood Count`: 1,615
  - `ESR`: 67
  - `Erythrocyte Sedimentation Rate`: 34
  - `FBS`: 110
  - `Fasting Blood Sugar`: 64
  - `Glycated Hemoglobin (HbA1c)`: 53
  - `HbA1c`: 111
  - `Lipid Profile Panel`: 187
  - `Lipid_Panel`: 383
  - `Liver Function Panel`: 70
  - `Liver_Function`: 127
  - `Renal Function Panel`: 75
  - `Renal_Function`: 162
  - `Routine Urinalysis`: 42
  - `Urinalysis`: 532
  - `Urine Culture & Sensitivity`: 36
  - `Urine_Culture`: 484
- **Laboratory Lifecycle Verdict:** **PASS**

---

## E. RADIOLOGY LIFECYCLE

- **Radiology Orders:** `10,000`
- **Completed Studies (Reported):** `2,500`
- **Pending Studies (Ordered):** `7,500`
- **Acquisition Events:** `2,500`
- **Report Completed Events:** `2,500`
- **Ordered With Completed Timestamp Violations:** `0`
- **Completed Missing Timestamp Violations:** `0`
- **Event-to-Record Linkage Failures:** `0`
- **Lifecycle Violations Total:** `0`
- **Abnormal Studies Flagged:** `383`
- **Modality Distribution:**
  - `CT Head`: 164
  - `Chest X-Ray`: 9,379
  - `Lumbar Spine X-Ray`: 457
- **Radiology Lifecycle Verdict:** **PASS**

---

## F. JOURNEY AND ENCOUNTER CONSISTENCY

- **Journeys Completed:** `10,000`
- **Encounters Completed/Closed:** `10,000`
- **Mismatched End Times (`journey.end != enc.end`):** `0`
- **SCEN-V1-02 Premature Journey Finishes:** `0`
- **Scenario-Specific Violations:** `0`
- **Journey/Encounter Consistency Verdict:** **PASS**

---

## G. MEDICATION AND CONDITION DIVERSITY

- **Total Medication Records:** `10,000`
- **Distinct Medications:** `37`
- **Distinct Diagnosed Conditions:** `15`
- **Top Medication Frequencies & Shares:**
  - `Paracetamol`: 2,055 records (20.55%)
  - `Amoxicillin`: 1,061 records (10.61%)
  - `Cephalexin`: 926 records (9.26%)
  - `Azithromycin`: 621 records (6.21%)
  - `Ceftriaxone`: 382 records (3.82%)
- **PubMed Provenance Coverage:** `10,000` records (100.0%)
- **Unverified / Cross-Assigned Indications:** `0`
- **Medication Diversity Verdict:** **PASS**

---

## H. REFERENTIAL INTEGRITY

- **Total Dangling References:** `0`
- **Foreign Key Checks Performed:**
  - `encounters.patient_id -> patients.patient_id`: 0 dangling
  - `conditions.patient_id -> patients.patient_id`: 0 dangling
  - `conditions.encounter_id -> encounters.encounter_id`: 0 dangling
  - `symptoms.patient_id -> patients.patient_id`: 0 dangling
  - `symptoms.encounter_id -> encounters.encounter_id`: 0 dangling
  - `symptoms.condition_id -> conditions.condition_id`: 0 dangling
  - `medications.patient_id -> patients.patient_id`: 0 dangling
  - `medications.encounter_id -> encounters.encounter_id`: 0 dangling
  - `medications.condition_id -> conditions.condition_id`: 0 dangling
  - `labs.patient_id -> patients.patient_id`: 0 dangling
  - `labs.encounter_id -> encounters.encounter_id`: 0 dangling
  - `radiology.patient_id -> patients.patient_id`: 0 dangling
  - `radiology.encounter_id -> encounters.encounter_id`: 0 dangling
  - `invoices.patient_id -> patients.patient_id`: 0 dangling
  - `invoices.encounter_id -> encounters.encounter_id`: 0 dangling
  - `payments.invoice_id -> invoices.invoice_id`: 0 dangling
  - `payments.patient_id -> patients.patient_id`: 0 dangling
  - `events.patient_id -> patients.patient_id`: 0 dangling
  - `events.encounter_id -> encounters.encounter_id`: 0 dangling
  - `journey_traces.patient_id -> patients.patient_id`: 0 dangling
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

- **Total Wall-Clock Runtime:** 18.29s
- **Simulation Runtime:** 13.62s
- **CSV Export Runtime:** 1.07s
- **Throughput:** 8259.8 events/sec, 10121.6 records/sec
- **Total Output Size:** 16.31 MB (17,098,639 bytes)
- **Failures / Retries:** `0`

---

## L. FINAL VERDICT

### PASS — DATASET READY FOR PHASE 3
