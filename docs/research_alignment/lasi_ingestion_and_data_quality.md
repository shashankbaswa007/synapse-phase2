# SYNAPSE Phase 2: LASI Wave 1 Ingestion and Data Quality Specification

**Document ID:** `SYNAPSE-LASI-INGEST-01`  
**Date:** October 2026  
**Auditor / Engineer:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** IMPLEMENTED, TESTED & PENDING GENUINE MICRODATA  

---

## 1. Regulatory Context & Real-World Data Access Pathway

To conduct rigorous external validation of SYNAPSE Phase 2 synthetic health records, real-world microdata from the **Longitudinal Aging Study in India (LASI) Wave 1 (2017–2018)** was selected as the primary independent reference benchmark for older adults.

### 1.1 Data Governance & Licensing Verification
Before designing the ingestion pipeline, data access pathways were formally audited:
- **Hosting Repositories:** 
  1. *International Institute for Population Sciences (IIPS)*, Mumbai, India.
  2. *Gateway to Global Aging Data* ([g2aging.org](https://g2aging.org)), Program on Global Aging, Health & Policy, University of Southern California (USC).
- **Access Protocol:** LASI individual-level microdata is **restricted academic research data**. It is **not** anonymously or publicly downloadable via direct URL.
- **Access Requirements:**
  - Individual registered user account with academic or institutional affiliation.
  - Submission of a formal research abstract and study plan.
  - Electronic execution of the **LASI Data Use Agreement (DUA)**, which strictly prohibits:
    1. Redistribution of raw participant-level microdata.
    2. Attempting to identify or re-identify individual participants or households.
    3. Commercial exploitation or unauthorized sublicensing.
  - Typical turnaround time for approval is 24 to 48 hours.

### 1.2 Compliance Guarantee & Test Fixture Strategy
In strict adherence to governance constraints and research integrity rules:
> [!IMPORTANT]
> **NO DATA FABRICATION GUARANTEE**  
> 1. No access controls or licensing agreements were bypassed.  
> 2. No synthetic observations were falsely substituted or labeled as real patient data.  
> 3. The ingestion engine has been built and verified against a documented schema and a small, clearly marked structural verification test fixture:  
>    `data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`  
> 4. The overall external evaluation gate is formally classified as:  
>    **`PENDING_GENUINE_REFERENCE_DATA`**  
>    until authenticated LASI microdata is loaded into the pipeline.

---

## 2. Ingestion Pipeline Architecture

The ingestion module is implemented in [`synapse_simulator.evaluation.lasi.ingestor`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py) (`LasiDataIngestor`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   LASI INGESTION PIPELINE FLOW                         │
└────────────────────────────────────────────────────────────────────────┘
          │
          ▼
   [Raw LASI CSV/TSV]
          │
          ├──> 1. SHA-256 Provenance Hashing
          ├──> 2. Participant Pseudonymization (SHA-256 Surrogate IDs)
          ├──> 3. Duplicate Detection & De-duplication
          ├──> 4. Survey Missing Sentinel Normalization (-999, ., etc. -> None)
          ├──> 5. Physiological Range Validation & Outlier Flagging
          ├──> 6. Clinical Blood Pressure Averaging Protocol (Readings 2 & 3)
          ├──> 7. Complex Survey Metadata Extraction (Weights, Strata, PSU)
          │
          ▼
   [LasiCleanedRecord Collection] ───> [LasiDataQualityReport]
          │
          ▼
   [Derived De-identified CSV Export: data/evaluation/derived/]
```

### 2.1 Participant De-Identification & Privacy
LASI records contain survey identifiers (`prim_key`, `household_id`, `individual_id`, `r1id`). To ensure privacy:
- Raw survey IDs are immediately transformed using truncated SHA-256 digests (`lasi_p_{hash[:12]}`).
- No participant names, geographic GPS coordinates, or household keys are propagated into derived files or reports.
- Cleaned derived records are exported to `data/evaluation/derived/lasi_cleaned_records.csv` containing only anonymized surrogate IDs and analytical clinical fields.

### 2.2 Survey Missing-Value Sentinel Normalization
Survey instruments and statistical packages employ specific non-numeric or sentinel values for missingness. The ingestor normalizes the following to `None`:
- **String sentinels:** `""`, `"."`, `"NA"`, `"null"`, `"None"`, `"-999"`, `"-998"`, `"-997"`, `"-99"`, `"999"`, `"9999"`.
- **Numeric sentinels:** `-999`, `-998`, `-997`, `-99`, `999`, `9999`.

### 2.3 Physiological Range Validation Bounds
Observations violating plausible physiological limits are flagged as invalid and excluded from biomarker/vital distributions:
- **Age:** $18.0 \le \text{age} \le 120.0\text{ years}$ (Records outside this bound are excluded from analysis).
- **Systolic Blood Pressure (SBP):** $60.0 \le \text{SBP} \le 280.0\text{ mmHg}$.
- **Diastolic Blood Pressure (DBP):** $40.0 \le \text{DBP} \le 160.0\text{ mmHg}$.
- **HbA1c:** $3.5\% \le \text{HbA1c} \le 20.0\%$.

### 2.4 Clinical Blood Pressure Averaging Protocol
LASI field teams administered three seated blood pressure measurements using Omron HEM-7121 digital monitors at 5-minute intervals. The ingestor implements the protocolized averaging rules:
1. **Primary Protocol:** Mean of reading 2 and reading 3:
   $$\text{SBP}_{\text{mean}} = \frac{\text{SBP}_2 + \text{SBP}_3}{2}, \quad \text{DBP}_{\text{mean}} = \frac{\text{DBP}_2 + \text{DBP}_3}{2}$$
2. **Partial Reading Fallback:** If only reading 2 is valid, use reading 2; if only reading 3 is valid, use reading 3.
3. **Single Reading Fallback:** If neither reading 2 nor 3 is valid, but reading 1 is valid, use reading 1 with a provenance flag (`FALLBACK_READING_1`).
4. **All Missing:** If no readings are valid, SBP/DBP mean is set to `None`.

### 2.5 Complex Survey Design Preservation
LASI utilizes a multistage stratified cluster sampling design. The ingestor extracts and validates:
- **Individual Sampling Weight:** `r1wtresp` (rescaled non-response adjusted individual weight).
- **Stratification Unit:** `r1strata`.
- **Primary Sampling Unit (PSU) / Cluster:** `r1psu`.

---

## 3. Data Quality Audit Verification (Test Fixture Baseline)

The ingestion pipeline was verified against `data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`.

| Data Quality Attribute | Audit Finding | Verification Status |
| :--- | :--- | :--- |
| **Input File Path** | `data/evaluation/fixtures/lasi_wave1_sample_fixture.csv` | VERIFIED |
| **Source File SHA-256** | `f3e3b7a440cd743fb7b02c091bb4fe6ddefb96f907da0ce7a6875c6cd759d5a2` | DETERMINISTIC |
| **Total Ingested Records** | $50$ | COMPLETE |
| **Duplicates Detected** | $0$ | PASSED |
| **Valid Analysis Records** | $50$ | COMPLETE |
| **Excluded Demographic Rows** | $0$ | PASSED |
| **Survey Weights Present** | Yes ($100.0\%$ non-zero weights) | VERIFIED |
| **Strata & PSU Identified** | `r1strata` (13 distinct strata), `r1psu` (26 clusters) | VERIFIED |
| **Mean Reference Age** | $62.9\text{ years}$ (Range: $45.0\text{--}83.0$) | REALISTIC OLDER ADULT |
| **Mean Protocol SBP** | $146.8\text{ mmHg}$ (Range: $121.0\text{--}169.0$, $50$ valid) | VERIFIED PROTOCOL MEAN |
| **Mean Protocol DBP** | $86.6\text{ mmHg}$ (Range: $74.0\text{--}97.0$, $50$ valid) | VERIFIED PROTOCOL MEAN |
| **Mean HbA1c (DBS)** | $7.14\%$ (Range: $5.3\%\text{--}8.9\%$, $49$ valid, $1$ missing sentinel) | VERIFIED SENTINEL REMOVAL |

---

## 4. Software Error vs. Non-Comparable Metric Handling

The pipeline explicitly distinguishes software defects from domain non-comparability:
1. **Fatal Software Errors (Raise Exceptions):**
   - Missing required table (e.g. `patients.csv` not found).
   - Missing mandatory columns (`age`, `gender`, `observation_code`, `value`).
   - Completely empty reference dataset.
2. **Methodological Non-Comparability (Logged as `NOT_COMPARABLE`):**
   - Evaluating Population A (General Adults $< 45$) against LASI older adults.
   - Requesting longitudinal incidence metrics from cross-sectional survey data.
   - Endpoints where reference survey metadata lacks required laboratory confirmation.
