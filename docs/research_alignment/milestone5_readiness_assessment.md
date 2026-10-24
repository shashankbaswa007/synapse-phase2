# Milestone 5 Readiness Assessment: Secure External Data Governance, Pre-Ingestion Checklist, & Calibration Protocol

**Document ID:** `SYNAPSE-READINESS-2026-MILESTONE5-ASSESSMENT`  
**Classification:** Pre-Ingestion Governance, Survey Topology Verification, Empirical Calibration Plan, & Holdout Escrow Protocol  
**Target Repository:** `synapse-phase2` (`/Users/shashi/synapse/synapse-phase2`)  
**Preceding Milestone:** Milestone 4 (Complex Survey Inference, Cluster Partitioning, & Design-Based Variance Engine — **CLOSED & VERIFIED**)  
**Target Milestone:** Milestone 5 (Secure Reference Data Ingestion, Empirical Calibration, & Holdout Validation)  
**External Validation Gate Status:** **`REFERENCE_DATA_PENDING`** (Strictly Preserved & Locked)  
**Date of Assessment:** October 2026  
**Primary Auditor:** SYNAPSE Research Validation & External Evaluation Authority  

---

## 1. Executive Summary & Governance Invariants

### 1.1 Objective and Scope of Milestone 5 Readiness
Following the successful completion, mathematical verification, and formal closure of **Milestone 4** ([`milestone4_closure_report.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/milestone4_closure_report.md)), the SYNAPSE Phase 2 simulation architecture possesses a verified survey inference and partitioning pipeline:
1. Multi-format binary and tabular ingestion ([`ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py)).
2. Survey topology diagnostics and missingness handling ([`diagnostics.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/diagnostics.py), [`missingness.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/missingness.py)).
3. Deterministic 60/40 PSU cluster partitioning with inverse-allocation survey weighting ([`partitioner.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py)).
4. AES-256-GCM single-use cryptographic holdout vault with cross-process audit ledger locking ([`partitioner.py:HoldoutAuditLedger`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L182)).
5. Taylor Series Linearization (TSL) variance engine with finite population correction (FPC) partition guards and exact NIST Student's $t$ lookup ([`variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py)).

This readiness assessment establishes the binding prerequisites, data use agreements, storage controls, ingestion checklists, and preregistered calibration protocols required **before** ingesting, unblinding, or executing against genuine reference microdata from the **Longitudinal Ageing Study in India (LASI) Wave 1**.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MILESTONE 5 GOVERNANCE WORKFLOW                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │ Step 1: DUA Execution & Secure Storage Setup  │
                        │ (Air-gapped enclave, AES-256, POSIX 600/700)  │
                        └───────────────────────────────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │ Step 2: Pre-Ingestion Manifest & Codebook     │
                        │ (SHA-256 verify, missing sentinels, weights)  │
                        └───────────────────────────────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │ Step 3: Survey Topology & 60/40 Partitioning  │
                        │ (Diagnostics, HMAC-SHA256, inverse weights)   │
                        └───────────────────────────────────────────────┘
                                                │
                        ┌───────────────────────┴───────────────────────┐
                        ▼                                               ▼
     ┌─────────────────────────────────────┐         ┌─────────────────────────────────────┐
     │      Partition A (60% of PSUs)      │         │      Partition C (40% of PSUs)      │
     │      Calibration Domain Only        │         │   Encrypted Holdout Escrow Vault    │
     │   (Loss optimization, internal CV)  │         │  (Single-use ticket, process-lock)  │
     └─────────────────────────────────────┘         └─────────────────────────────────────┘
                        │                                               │
                        ▼                                               │
     ┌─────────────────────────────────────┐                            │
     │  Freeze Calibrated Parameters Θ*    │                            │
     │  Archive Formal Calibration Report  │                            │
     └─────────────────────────────────────┘                            │
                        │                                               │
                        ▼                                               ▼
     ┌─────────────────────────────────────────────────────────────────────────────────────┐
     │ Step 4: Single-Use Cryptographic Decryption & Holdout Validation Execution          │
     │ (Taylor Series Linearization, Predeclared Acceptance Thresholds, Audit Ledger Burn) │
     └─────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
     ┌─────────────────────────────────────────────────────────────────────────────────────┐
     │ Step 5: External Validation Gate Decision: PASSED / FAILED                          │
     └─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Strict Non-Negotiable Governance Invariants
Prior to and throughout Milestone 5 execution, the following four rules are inviolable:
1. **Synthetic Data Exclusively During Assessment:** This readiness assessment is conducted entirely without genuine LASI microdata. All pipeline checks, unit tests, and performance profiles operate on synthetic fixtures (`lasi_wave1_sample_fixture.csv`, $N=51$).
2. **Zero Clinical Default Modifications:** No biological parameters, clinical transition probabilities, physiological guards ($\text{PP} \ge 20\text{ mmHg}$), or diagnostic criteria ($140/90\text{ mmHg}$) have been or will be adjusted during this assessment.
3. **No Claim of Empirical Validation:** Passing software unit, integration, or Monte Carlo tests verifies code execution only. The repository does **not** claim empirical epidemiological calibration or real-world validity.
4. **Validation Gate Strictly Locked:** The external validation gate in [`synapse_simulator/modules/models.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/modules/models.py#L97) and [`evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py#L124) remains firmly locked at:
   ```python
   REFERENCE_DATA_PENDING = "PENDING_EXTERNAL_REFERENCE_UNBLINDING"
   ```

---

## 2. DUA, Access Permissions, Storage Controls, and Data-Handling Restrictions

Genuine LASI microdata contains detailed socio-demographic, physical biomarker, and clinical health information collected from older adults across India. Ingesting and processing these data requires strict adherence to institutional, legal, and cryptographic controls.

### 2.1 Institutional Data Use Agreement (DUA) Framework

| Dimension | Regulatory & Legal Requirement | Implementation in SYNAPSE |
| :--- | :--- | :--- |
| **Data Custodian** | International Institute for Population Sciences (IIPS), Gov. of India, & Gateway to Global Aging Data (USC / NIA). | Registered research project under authorized DUA credentials. |
| **Permitted Research Scope** | Methodological evaluation, validation, and calibration of epidemiological simulation models of chronic disease in India. | Restricted strictly to `synapse-phase2` validation pipeline; no secondary or tangential research. |
| **Prohibition on Redistribution** | Raw or derivative microdata must never be re-distributed, sub-licensed, or shared with third parties. | Data stored strictly in air-gapped or access-controlled local directory; excluded from all Git remotes. |
| **Prohibition on Re-Identification** | Absolute legal prohibition on attempting to link individual respondents or households to external administrative registers, voter registries, or identity systems (e.g. Aadhaar). | Mandatory surrogate pseudonymization via SHA-256 HMAC ([`security.py:generate_surrogate_id`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/security.py#L42)). |
| **Reporting Aggregation Thresholds** | Cell suppression rules: No reporting of subpopulation cells where the unweighted respondent count $n < 20$, to prevent deductive disclosure. | Enforced in summary tables and reports generated by [`evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py). |

### 2.2 Access Permissions and Enclave Isolation

To prevent unauthorized access or leakage during execution:
1. **Host Environment Isolation:**
   - Ingestion and calibration must execute on a dedicated workstation or secured Virtual Private Cloud (VPC) compute instance.
   - Network egress must be disabled or strictly restricted to package repository mirrors during reference data processing.
2. **Role-Based Access Control (RBAC):**
   - Direct access to unencrypted raw microdata files is restricted to the designated principal evaluation engineer.
   - Automated scripts run under a dedicated system user account without administrative/root daemon privileges.

### 2.3 Storage Controls and Encryption at Rest

```
Host Filesystem (LUKS / FileVault AES-XTS-256)
└── /secure_data_enclave/
    ├── raw_reference/                  [POSIX: chmod 700 / 600, .gitignore]
    │   ├── lasi_wave1_individual.dta   (SHA-256 verified)
    │   ├── lasi_wave1_biomarker.dta    (SHA-256 verified)
    │   └── lasi_wave1_household.dta    (SHA-256 verified)
    ├── derived_partition_a/            [POSIX: chmod 700 / 600, .gitignore]
    │   └── lasi_partition_a.csv        (Calibration microdata: 60% PSUs)
    └── encrypted_holdout/              [POSIX: chmod 700 / 600, .gitignore]
        ├── lasi_holdout_vault.json     (AES-256-GCM encrypted: 40% PSUs)
        └── .synapse_holdout_ledger.json (fcntl.flock atomic consumption ledger)
```

1. **Filesystem Encryption:**
   - All physical storage volumes hosting raw or partitioned LASI data must employ hardware-accelerated full-disk encryption (macOS FileVault 2 / Linux LUKS with AES-XTS-256).
2. **POSIX File Permissions:**
   - Raw microdata directory: `chmod 700 /secure_data_enclave/raw_reference/`
   - Raw microdata files: `chmod 600 /secure_data_enclave/raw_reference/*.dta`
   - Generated vault and ledger: `chmod 600 lasi_holdout_vault.json .synapse_holdout_audit_ledger.json`
3. **Strict Version Control Containment (`.gitignore`):**
   - The repository's [`.gitignore`](file:///Users/shashi/synapse/synapse-phase2/.gitignore) has been verified to explicitly exclude:
     ```gitignore
     # Reference data and holdout audit ledgers
     data/reference/
     data/raw/
     *.dta
     *.sav
     *.ledger.json
     .synapse_holdout_audit_ledger.json
     lasi_holdout_vault.json
     ```
   - **Pre-Commit Hook Safeguard:** A pre-commit hook will be installed in `.git/hooks/pre-commit` to scan staged files for `.dta`, `.sav`, or file sizes exceeding 5 MB, aborting the commit if detected.

### 2.4 Ephemeral Memory Controls and Buffer Zeroization

1. **In-Memory Transformation Pipeline:**
   - Raw files are read into ephemeral Python heap memory via [`LasiDataIngestor`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py#L93).
   - Once cleaned records are constructed and partitioned by [`LasiPsuPartitioner`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L458), the raw data structures are deleted (`del raw_data`) and garbage collected.
2. **Holdout Vault Sealing:**
   - Partition C records are serialized to JSON in memory, encrypted using AES-256-GCM via [`LasiHoldoutVault.seal_holdout()`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L254), and written to disk **strictly as ciphertext**.
   - No unencrypted plaintext CSV or JSON files for Partition C may be written to disk.
3. **RAM Buffer Zeroization:**
   - As implemented in [`LasiHoldoutVault.decrypt_and_consume()`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L328), the decrypted bytearray buffer containing Partition C records is explicitly overwritten with zero bytes (`buffer[i] = 0`) immediately after parsing into Pydantic models.

---

## 3. Pre-Ingestion Checklist for Genuine LASI Release & Codebook Verification

Before the ingestion script is permitted to process genuine files, the data package must be audited against an exhaustive pre-ingestion checklist.

### 3.1 Release Identification & File Manifest

| Module | Expected Source File Name | Format | Official Custodian & Survey Source | Expected Ingestion Role |
| :--- | :--- | :---: | :--- | :--- |
| **Individual Core** | `lasi_wave1_individual.dta` / `H_LASI_a1.dta` | Stata 14+ (`.dta`) or SPSS (`.sav`) | IIPS LASI Wave 1 (2017–2018) / Gateway Harmonized | Demographics, self-reported conditions (`r1hypere`, `r1diabe`), medications (`r1bpmeds`), survey weights (`r1wtresp`). |
| **Biomarker** | `lasi_wave1_biomarker.dta` | Stata 14+ (`.dta`) or SPSS (`.sav`) | IIPS LASI Wave 1 Biomarker Module | Triplicated digital blood pressure measurements (`r1bpsys1-3`, `r1bpdia1-3`), dried blood spot HbA1c (`r1hba1c`). |
| **Household Roster** | `lasi_wave1_household.dta` | Stata 14+ (`.dta`) or SPSS (`.sav`) | IIPS LASI Wave 1 Household Module | Sampling strata (`r1strata`), primary sampling unit identifiers (`r1psu`), sector (`urban_rural`). |

**Pre-Ingestion Checksum Verification:**
Every raw file must match its expected SHA-256 checksum recorded in a sealed pre-ingestion manifest before ingestion proceeds. Any checksum mismatch immediately aborts execution.

### 3.2 Key Variable and Codebook Crosswalk

```
Raw LASI Microdata (Stata / SPSS)              Normalized Ingested Model (LasiCleanedRecord)
┌─────────────────────────────────┐            ┌───────────────────────────────────────────┐
│ HHID + IND_ID (Composite Key)   │ ─────────> │ participant_id (HMAC-SHA256 Surrogate)    │
│ r1agey / q003 (Age in years)    │ ─────────> │ age (float, valid [18, 120])              │
│ ragender / q002 (1=M, 2=F)      │ ─────────> │ gender ("Male" / "Female")                │
│ r1strata (Sampling Stratum)     │ ─────────> │ stratum_id (str)                          │
│ r1psu (Sampling Cluster)        │ ─────────> │ psu_id (str)                              │
│ r1wtresp (Respondent Weight)    │ ─────────> │ survey_weight (float > 0.0)               │
│ r1bpsys1, r1bpsys2, r1bpsys3    │ ─────────> │ sbp_reading1, sbp_reading2, sbp_reading3  │
│                                 │            │ sbp_mean = (sbp2 + sbp3) / 2.0            │
│ r1bpdia1, r1bpdia2, r1bpdia3    │ ─────────> │ dbp_reading1, dbp_reading2, dbp_reading3  │
│                                 │            │ dbp_mean = (dbp2 + dbp3) / 2.0            │
│ r1hypere (1=Yes, 2=No)          │ ─────────> │ self_reported_hypertension (bool)         │
│ r1bpmeds (1=Yes, 2=No)          │ ─────────> │ taking_bp_medication (bool)               │
│ r1diabe (1=Yes, 2=No)           │ ─────────> │ self_reported_diabetes (bool)             │
│ r1hba1c (Capillary DBS %)       │ ─────────> │ hba1c_dbs (float; UNVERIFIED / PENDING)   │
└─────────────────────────────────┘            └───────────────────────────────────────────┘
```

The mapping logic in [`synapse_simulator/evaluation/lasi/ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py) must adhere to the following variable specifications:

1. **Identifiers & Linkage Keys:**
   - Household Key: `HHID` (or `hhid`).
   - Individual Key: `IND_ID` / `PRIM_KEY` (or `prim_key`).
   - Relational Linkage Contract: Individual-to-Biomarker must be strictly `ONE_TO_ONE` or `ONE_TO_ZERO_OR_ONE`. Multiple biomarker records per individual trigger [`LasiDuplicateKeyError`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py#L41).
2. **Survey Design Structure:**
   - Stratum: `STRATA` / `SUBSTRATA` / `r1strata`. Must not be null; missing stratum is flagged for singleton diagnostics.
   - Cluster / PSU: `PSU` / `VILLAGE_CEB` / `r1psu`. Must uniquely identify the first-stage sampling unit within a stratum.
   - Survey Sampling Weight: `WEIGHT` / `W_IND` / `r1wtresp`. Must be strictly positive ($w_i > 0$). Records with zero or negative weights are logged and handled per missingness protocols.
3. **Blood Pressure Tri-Readings Protocol:**
   - Measured with Omron HEM-7121 digital monitor after 5 minutes seated rest.
   - Readings: `r1bpsys1`, `r1bpsys2`, `r1bpsys3` (systolic); `r1bpdia1`, `r1bpdia2`, `r1bpdia3` (diastolic).
   - Physiological plausibility bounds: $\text{SBP} \in [60.0, 280.0]\text{ mmHg}$, $\text{DBP} \in [40.0, 160.0]\text{ mmHg}$.
   - Protocol Averaging Rule:
     $$\text{SBP}_{\text{protocol}} = \frac{\text{SBP}_2 + \text{SBP}_3}{2}, \quad \text{DBP}_{\text{protocol}} = \frac{\text{DBP}_2 + \text{DBP}_3}{2}$$
   - Fallback Tracking: Records where reading 2 or 3 is missing or out-of-range are classified into exact derivation categories: `PROTOCOL_MEAN_READINGS_2_AND_3`, `FALLBACK_READING_2_ONLY`, `FALLBACK_READING_3_ONLY`, `FALLBACK_READING_1_ONLY`, or `NO_VALID_READING`.
4. **Biomarker Assay Comparability Boundary (HbA1c):**
   - LASI collected capillary finger-prick blood on Whatman 903 protein saver cards (Dried Blood Spots, DBS).
   - Capillary DBS HbA1c is **not directly comparable** to venous whole-blood HPLC simulated in SYNAPSE without an empirically validated biochemical transfer function.
   - The linear crosswalk ($0.94 \times \text{DBS} + 0.45$) remains disabled (`adjust_dbs_hba1c_to_venous(enabled=False)` in [`comparability.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/comparability.py#L98)). HbA1c metrics are classified as `UNVERIFIED` and excluded from pass/fail gating.

### 3.3 Missing-Value Conventions Checklist

Surveys developed in Stata and SPSS utilize distinct missing-value conventions that must be normalized to prevent erroneous data corruption:

| Platform / Sentinel Format | Raw Values / Codes | Interpretation | Ingestion Action in `LasiDataIngestor` |
| :--- | :--- | :--- | :--- |
| **Stata Extended Missing** | `.`, `.a`, `.b`, `.c`, ..., `.z` | Item non-response, refuse, don't know, skip pattern, not interviewed. | Mapped to `None` / `np.nan` and categorized in [`LasiMissingnessReport`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/models.py). |
| **SPSS Missing Codes** | `-99`, `-98`, `-97`, `999`, `99` | User-defined missing values (refusal, don't know, unmeasured). | Disambiguated using SPSS value label metadata. Valid physiological readings (e.g. SBP = 99 mmHg) are preserved; sentinel 99 in non-continuous fields is set to `None`. |
| **Zero/Negative Weights** | $w_i \le 0.0$ | Out-of-universe or non-response zeroed weight. | Counted in data quality audit; omitted from weighted Horvitz-Thompson estimation. |
| **Out-of-Range BP** | $\text{SBP} < 60 \lor \text{SBP} > 280$ | Measurement artifact, cuff deflation error, or transcription error. | Reading-level value set to `None`. If readings 2 and 3 invalid, triggers protocol fallback. If all 3 invalid, record excluded from BP estimands. |

---

## 4. Survey Design Compatibility: 60/40 PSU Partitioning & Variance Engine

Before execution against genuine data, the compatibility between the actual LASI survey topology and the implemented partitioning and variance estimation algorithms must be formally verified.

### 4.1 Sampling Design Topology of LASI Wave 1
LASI Wave 1 utilizes a multi-stage stratified cluster sampling design:
1. **First Stage (Stratification):** 35 States and Union Territories, further stratified into urban and rural sectors. In rural areas, sub-stratification is based on female literacy and geographic indices. In urban areas, sub-stratification is based on ward-level socio-economic status.
2. **Primary Sampling Units (PSUs):**
   - Rural areas: Primary Sampling Units are **villages** selected with Probability Proportional to Size (PPS).
   - Urban areas: Primary Sampling Units are **Census Enumeration Blocks (CEBs)** selected with PPS.
3. **Second Stage (Secondary Sampling Units):**
   - Households within selected PSUs sampled via circular systematic random sampling.
4. **Third Stage (Ultimate Sampling Units):**
   - All eligible resident individuals aged $\ge 45$ years and their spouses (regardless of age) within selected households.

### 4.2 Verification of Compatibility with 60/40 PSU Partitioning

```
                            STRATUM h (N_h PSUs in Population)
                      ┌──────────────────────────────────────────────┐
                      │ Sampled in LASI: n_h PSUs (Villages / CEBs)  │
                      └──────────────────────┬───────────────────────┘
                                             │
                       HMAC-SHA256 Deterministic Allocation (Seed K)
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
       Partition A: n_{h, A} PSUs                     Partition C: n_{h, C} PSUs
           (Target ~60% of n_h)                           (Target ~40% of n_h)
                      │                                             │
        All nested households &                       All nested households &
       individuals assigned to A                     individuals assigned to C
                      │                                             │
         Conditional Survey Weight:                    Conditional Survey Weight:
         w_{hij}^{(A)} = w_{hij} * (n_h / n_{h,A})    w_{hij}^{(C)} = w_{hij} * (n_h / n_{h,C})
```

The 60/40 PSU cluster partitioner ([`partitioner.py:LasiPsuPartitioner`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L458)) matches the actual LASI design through four verified mathematical properties:

1. **Cluster-Level Allocation (Zero Household/Participant Leakage):**
   - Randomization occurs strictly at the PSU level ($PSU_i$).
   - All households and participants residing in $PSU_i$ are assigned deterministically to the same partition.
   - Property: $A \cap C = \emptyset$ at PSU, household, and participant levels. This eliminates cluster contamination and guarantees that holdout observations are genuinely out-of-cluster.
2. **Stratum-Level Support Requirement ($n_h \ge 4$):**
   - To ensure both Partition A and Partition C receive at least 2 PSUs ($n_{h, A} \ge 2$, $n_{h, C} \ge 2$), each stratum must contain at least 4 PSUs.
   - For an allocation of $n_h = 4$, an exact $2:2$ split yields $df_{h, A} = 1$ and $df_{h, C} = 1$. For $n_h = 5$, a $3:2$ split yields $df_{h, A} = 2$ and $df_{h, C} = 1$.
   - In LASI Wave 1, most state-by-sector strata contain tens of PSUs ($n_h \gg 10$), easily satisfying $n_h \ge 4$.
3. **Small-Stratum and Singleton Handling:**
   - If empirical diagnostics reveal small strata with $n_h < 4$ (e.g. small Union Territories such as Lakshadweep or Chandigarh):
     - Naive geographic proximity collapsing is strictly prohibited (as documented in [`phase2d7_partitioning_design_decision.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d7_partitioning_design_decision.md)).
     - Protocol: When `handle_unsupported_strata="ALLOCATE_WHOLE_TO_A"`, the entire stratum is allocated to Partition A, contributing to calibration without creating an unstable singleton in holdout Partition C.
4. **Finite-Sample Unbiasedness of Partition Survey Weights:**
   - Subsampling PSUs within stratum $h$ scales the first-stage inclusion probability by $p_{h, k} = n_{h, k} / n_h$.
   - The conditional weight factor is:
     $$w_{hij}^{(k)} = w_{hij} \cdot \frac{n_h}{n_{h, k}}$$
   - As proven in Phase 2D.14 ([`phase2d14_final_statistical_claims_check.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d14_final_statistical_claims_check.md#L90)), this inverse-allocation weight ensures that Horvitz-Thompson population totals are strictly design-unbiased:
     $$E_D\left[\hat{Y}^{(k)}\right] \equiv Y$$

### 4.3 Compatibility with Design-Based Variance Estimation

The variance engine ([`variance.py:TaylorSurveyVarianceEstimator`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L90)) is directly compatible with the complex survey design:

1. **Taylor Series Linearization for Ratio Means and Proportions:**
   The linearized cluster total for observation $j$ in cluster $i$ of stratum $h$ with mean $\hat{\bar{Y}} = \hat{Y}/\hat{N}$ is:
   $$u_{hi} = \sum_{j=1}^{m_{hi}} w_{hij} (y_{hij} - \hat{\bar{Y}})$$
   The design-based variance estimator across strata is:
   $$\widehat{\text{Var}}(\hat{\bar{Y}}) = \frac{1}{\hat{N}^2} \sum_{h=1}^H \frac{n_h}{n_h - 1} (1 - f_h) \sum_{i=1}^{n_h} (u_{hi} - \bar{u}_h)^2$$
   where $\bar{u}_h = \frac{1}{n_h} \sum_{i=1}^{n_h} u_{hi} = 0$ when centered at the sample mean.
2. **Finite Population Correction (FPC) Guard on Partitions:**
   - In full-sample survey estimation, the first-stage sampling fraction is $f_h = n_h / N_h$, where $N_h$ is the total number of PSUs in the population sampling frame.
   - For a partition $k$, the actual sampling fraction of the population frame is:
     $$f_{h, k} = \frac{n_{h, k}}{N_h} = \frac{n_{h, k}}{n_h} \cdot \frac{n_h}{N_h} = p_{h, k} f_h$$
   - In LASI Wave 1, because the total number of villages and CEBs in India is vast ($N_h \gg 10^5$), first-stage sampling fractions are negligible ($f_h < 0.005$). Treating sampling as with-replacement ($f_h \approx 0 \implies 1 - f_h \approx 1$) is asymptotically valid.
   - However, if population frame counts $N_h$ are provided, [`variance.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L234) enforces that partition callers **must** scale the FPC fraction via `LasiPartitionResult.get_partition_fpc(...)` or provide `full_stratum_psu_counts`, raising `ValueError` if an unadjusted full-sample fraction is supplied.
3. **Design Degrees of Freedom and Critical Multipliers:**
   - Design degrees of freedom are calculated as:
     $$df = \sum_{h=1}^H n_h - H$$
   - For subpopulation domains or partitioned sets where $df \le 30$, Student's $t$ critical values ($t_{df, 0.975}$) are looked up via the exact NIST reference table ([`variance.py:_T_TABLE_95`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/variance.py#L35)), avoiding anti-conservative normal approximations ($z = 1.96$).
4. **Logit Transformation for Proportion Confidence Intervals:**
   - For prevalence and proportion estimands ($\hat{p} \in (0, 1)$), the variance engine applies a logit transformation:
     $$\hat{\eta} = \ln\left(\frac{\hat{p}}{1 - \hat{p}}\right), \quad \widehat{\text{Var}}(\hat{\eta}) = \frac{\widehat{\text{Var}}(\hat{p})}{(\hat{p}(1 - \hat{p}))^2}$$
     $$\text{CI}_{95\%}(\hat{p}) = \left[ \text{logit}^{-1}(\hat{\eta} - t_{df} \cdot \text{SE}(\hat{\eta})), \; \text{logit}^{-1}(\hat{\eta} + t_{df} \cdot \text{SE}(\hat{\eta})) \right]$$
   - This prevents invalid confidence limits $(< 0$ or $> 1$) near the boundaries.

---

## 5. Preregistered Calibration Protocol, Acceptance Criteria, & Holdout Escrow

To prevent data snooping, p-hacking, or post-hoc threshold adjustment, the calibration metrics, parameter targets, loss functions, acceptance criteria, and holdout access controls are predeclared in advance.

### 5.1 Free Parameter Inventory ($\mathbf{\Theta}$) for Empirical Calibration

As established in the Phase 2D calibration architecture ([`phase2d_calibration_validation_plan.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d_calibration_validation_plan.md#L45)), exactly **17 atomic parameters** across the forward causal simulation layers are free parameters to be estimated against **Partition A**:

| Parameter Symbol | Configuration Path | Baseline Provisional Default | Physical / Clinical Meaning | Calibration Target in Partition A |
| :--- | :--- | :---: | :--- | :--- |
| $\mu_{0, \text{sbp}}$ | `forward_hemodynamics.mean_sbp_anchor` | `120.0 mmHg` | Resting baseline SBP anchor for young normotensive adults. | Unmedicated normotensive adults (45–49 yrs) weighted mean. |
| $\sigma_{0, \text{sbp}}$ | `forward_hemodynamics.sd_sbp_anchor` | `9.0 mmHg` | Inter-individual standard deviation of resting baseline SBP. | Unmedicated normotensive adults (45–49 yrs) weighted SD. |
| $\mu_{0, \text{dbp}}$ | `forward_hemodynamics.mean_dbp_anchor` | `78.0 mmHg` | Resting baseline DBP anchor for young normotensive adults. | Unmedicated normotensive adults (45–49 yrs) weighted mean. |
| $\sigma_{0, \text{dbp}}$ | `forward_hemodynamics.sd_dbp_anchor` | `6.0 mmHg` | Inter-individual standard deviation of resting baseline DBP. | Unmedicated normotensive adults (45–49 yrs) weighted SD. |
| $\rho_0$ | `forward_hemodynamics.sbp_dbp_correlation` | `0.65` | Bivariate correlation between resting SBP and DBP. | Bivariate weighted correlation of unmedicated SBP and DBP. |
| $\beta_{\text{age, sbp}}$ | `forward_hemodynamics.annual_drift_sbp` | `0.60 mmHg/yr` | Cross-sectional vascular stiffening SBP age slope. | Survey regression: $\partial \text{SBP} / \partial \text{Age}$ (unmedicated 45–75 yrs). |
| $\beta_{\text{age, dbp1}}$ | `forward_hemodynamics.annual_drift_dbp_early` | `0.25 mmHg/yr` | Peripheral resistance DBP age slope prior to inflection age. | Survey regression: $\partial \text{DBP} / \partial \text{Age}$ (age $< 60$ yrs). |
| $\beta_{\text{age, dbp2}}$ | `forward_hemodynamics.annual_drift_dbp_late` | `-0.15 mmHg/yr` | Conduit stiffening DBP decline slope after inflection age. | Survey regression: $\partial \text{DBP} / \partial \text{Age}$ (age $\ge 60$ yrs). |
| $a_{\text{inflect}}$ | `forward_hemodynamics.age_inflection_dbp` | `60.0 yrs` | Age of peak population DBP plateau. | Piecewise linear change-point estimator on DBP. |
| $\gamma_{\text{t2d, sbp}}$ | `forward_hemodynamics.t2d_sbp_shift` | `4.5 mmHg` | Arterial stiffening SBP elevation in diabetic respondents. | Weighted contrast: $\text{SBP}_{\text{diabetic}} - \text{SBP}_{\text{non-diabetic}}$. |
| $\gamma_{\text{t2d, dbp}}$ | `forward_hemodynamics.t2d_dbp_shift` | `2.0 mmHg` | Arterial stiffening DBP elevation in diabetic respondents. | Weighted contrast: $\text{DBP}_{\text{diabetic}} - \text{DBP}_{\text{non-diabetic}}$. |
| $\delta_{\text{male, sbp}}$ | `forward_hemodynamics.male_sbp_offset` | `2.0 mmHg` | Biological sex offset in resting SBP at baseline. | Weighted contrast: $\text{SBP}_{\text{male}} - \text{SBP}_{\text{female}}$ (45–49 yrs). |
| $\delta_{\text{male, dbp}}$ | `forward_hemodynamics.male_dbp_offset` | `1.5 mmHg` | Biological sex offset in resting DBP at baseline. | Weighted contrast: $\text{DBP}_{\text{male}} - \text{DBP}_{\text{female}}$ (45–49 yrs). |
| $\alpha_{\text{alert, sbp}}$ | `bp_measurement.reading1_alerting_sbp` | `3.5 mmHg` | Situational white-coat alerting bias on Reading 1 (SBP). | Survey intra-individual contrast: $\text{mean}(R_1 - R_2)$. |
| $\alpha_{\text{alert, dbp}}$ | `bp_measurement.reading1_alerting_dbp` | `1.5 mmHg` | Situational white-coat alerting bias on Reading 1 (DBP). | Survey intra-individual contrast: $\text{mean}(R_1 - R_2)$. |
| $\sigma_{\text{within}}$ | `bp_measurement.within_visit_noise_sd` | `1.8 mmHg` | Within-visit biological / digital measurement noise. | Residual standard deviation between Reading 2 and Reading 3. |
| $\delta_{\text{drug, sbp}}$ | `forward_hemodynamics.delta_drug_sbp` | `12.0 mmHg` | Average treated blood pressure reduction effect (SBP). | Contrasts between treated and untreated diagnosed hypertensives. |

**Inviolable Parameters (Uncalibrated Constants):**
Biophysical boundaries ($\text{PP}_{\min} = 20.0\text{ mmHg}$, $\text{SBP} \in [70, 260]\text{ mmHg}$, $\text{DBP} \in [40, 150]\text{ mmHg}$) and clinical guideline rules ($140/90\text{ mmHg}$ hypertension definition; 2-visit confirmation requirement) are **not calibrated** and remain mathematically fixed.

### 5.2 Objective Calibration Loss Functions on Partition A

Calibration proceeds through an explicit multi-objective scalar loss function minimized over the parameter space $\mathbf{\Theta} \in \mathbb{R}^{17}$ using the downhill simplex algorithm (Nelder-Mead) with bounded box projections:

$$L(\mathbf{\Theta}; \mathcal{D}_A) = \lambda_1 L_{\text{dist}}(\text{SBP}) + \lambda_2 L_{\text{dist}}(\text{DBP}) + \lambda_3 L_{\text{prev}}(\text{HTN}) + \lambda_4 L_{\text{drift}} + \lambda_5 L_{\text{alert}}$$

1. **Distributional Loss ($L_{\text{dist}}$):**
   Evaluated using the 1-Dimensional Wasserstein-1 distance ($W_1$) between the simulated empirical distribution and the survey-weighted Partition A empirical distribution:
   $$W_1(F_{\text{syn}}, \hat{F}_{A, \text{weighted}}) = \int_0^1 \left| F_{\text{syn}}^{-1}(u) - \hat{F}_{A, \text{weighted}}^{-1}(u) \right| du$$
2. **Prevalence Loss ($L_{\text{prev}}$):**
   Standardized squared discrepancy weighted by the inverse design variance:
   $$L_{\text{prev}} = \frac{(\hat{p}_{\text{syn}}(\mathbf{\Theta}) - \hat{p}_{A, \text{htn}})^2}{\widehat{\text{Var}}(\hat{p}_{A, \text{htn}})}$$
3. **Internal Cluster Cross-Validation:**
   To protect against overfitting during calibration, 5-fold cluster cross-validation is performed **internally within Partition A**. Clusters (PSUs) are grouped into 5 folds; models calibrated on 4 folds are evaluated on the held-out fold within Partition A.
4. **Absolute Holdout Isolation:**
   Holdout Partition C is **never accessed** during the minimization of $L(\mathbf{\Theta}; \mathcal{D}_A)$.

### 5.3 Predeclared Acceptance Criteria for Independent Holdout Validation (Partition C)

Following calibration on Partition A, the calibrated parameter vector $\mathbf{\Theta}^*$ is frozen and registered. Validation is executed strictly once against **Partition C**. To pass Milestone 5, the simulation must satisfy all of the following predeclared criteria:

| Category | Metric / Estimand | Statistical Test / Distance | Binding Acceptance Threshold |
| :--- | :--- | :--- | :---: |
| **Demographics** | Older Adult Age Distribution ($\ge 45$) | Two-sample Kolmogorov-Smirnov ($D$) | $D \le 0.08$ |
| **Demographics** | Sex Proportion (Female %) | Absolute Difference ($|\Delta\%|$) | $|\Delta_{\text{female}}| \le 3.0\%$ |
| **Blood Pressure** | Protocol SBP Distribution ($\text{SBP}_{\text{proto}}$) | 1-D Wasserstein Distance ($W_1$) | $W_1 \le 4.0\text{ mmHg}$ |
| **Blood Pressure** | Protocol SBP Distribution ($\text{SBP}_{\text{proto}}$) | Two-sample Kolmogorov-Smirnov ($D$) | $D \le 0.06$ |
| **Blood Pressure** | Protocol DBP Distribution ($\text{DBP}_{\text{proto}}$) | 1-D Wasserstein Distance ($W_1$) | $W_1 \le 3.0\text{ mmHg}$ |
| **Blood Pressure** | Protocol DBP Distribution ($\text{DBP}_{\text{proto}}$) | Two-sample Kolmogorov-Smirnov ($D$) | $D \le 0.06$ |
| **Prevalence** | Composite HTN Prevalence (Estimand C2) | Survey-Weighted Absolute Difference | $|\hat{p}_{\text{syn}} - \hat{p}_{C}| \le 3.5\%$ |
| **Prevalence** | Composite HTN Prevalence (Estimand C2) | Design-Based 95% Logit CI Inclusion | $\hat{p}_{\text{syn}} \in \text{CI}_{95\%, \text{logit}}(\hat{p}_C)$ |
| **Clinical Integrity**| Physiological Invariants | Violations of $\text{PP} \ge 20$ or $\text{SBP} \le \text{DBP}$ | **Strictly 0.0% (Zero Tolerated)** |
| **Longitudinal** | Multi-Year Progression (Estimand D2) | Cross-Sectional Comparison | **STRICTLY UNVERIFIED** (Requires Wave 2) |

### 5.4 Holdout Access Controls & Cryptographic Escrow

```
                    HOLDOUT DECRYPTION & AUDIT ENGINE
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Verify Authorization Ticket (HoldoutAccessTicket)                   │
│    - Ticket ID matches authorized run manifest                         │
│    - Ticket not marked consumed in memory                              │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Acquire Cross-Process Advisory Lock (fcntl.flock)                  │
│    - Mutex lock on .synapse_holdout_audit_ledger.json.lock             │
│    - Symlink traversal defense verified                                │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Persistent Ledger Audit (HoldoutAuditLedger)                        │
│    - Check vault_id, ticket_id, and manifest_sha256 in ledger          │
│    - If any match found -> RAISE HoldoutAccessViolationError           │
├────────────────────────────────────────────────────────────────────────┤
│ 4. AES-256-GCM Decryption (LasiHoldoutVault)                           │
│    - Validate 96-bit NIST SP 800-38D Nonce and 32-byte Key             │
│    - Verify GCM 128-bit Authentication Tag                             │
│    - Parse records into LasiCleanedRecord models                       │
│    - Explicitly zeroize in-memory decrypted bytearray buffer           │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Commit Durable Consumption Record                                  │
│    - Write updated ledger via atomic tempfile & os.replace             │
│    - Execute os.fsync to guarantee disk persistence                    │
│    - Release fcntl lock; ticket permanently burned                     │
└────────────────────────────────────────────────────────────────────────┘
```

The holdout dataset is protected by the cryptographic escrow architecture audited in [`phase2d9_holdout_security_audit.md`](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/phase2d9_holdout_security_audit.md):
1. **Single-Use Authorization Ticket:**
   Access requires a cryptographically generated [`HoldoutAccessTicket`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L191) specifying `ticket_id`, `purpose`, and `authorized_by`.
2. **Persistent Audit Ledger:**
   The [`HoldoutAuditLedger`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L182) records consumption events across three distinct digests: `vault_id`, `ticket_id`, and `manifest_sha256`. Even if an analyst creates a cloned dictionary or restarts the Python process, re-decryption is blocked by [`HoldoutAccessViolationError`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/partitioner.py#L54).
3. **Concurrency Race Protection:**
   The ledger uses a dual-locking mechanism: an intra-process `threading.Lock` and a cross-process POSIX advisory lock via `fcntl.flock(lock_fd, fcntl.LOCK_EX)` on `.synapse_holdout_audit_ledger.json.lock`.
4. **Symlink Traversal Protection:**
   The ledger rejects any ledger path or lockfile that is a symbolic link (`os.path.islink`), mitigating symlink redirection attacks (CWE-59).
5. **Irreversible Consumption (Burning the Key):**
   Once decrypted for final validation, the holdout key and ticket are permanently burned in the audit ledger. Re-running validation against Partition C is impossible without generating a new partition from raw reference data.

---

## 6. External Validation Gate Locking & Transition Criteria

### 6.1 Current Gate Status
The external validation gate remains locked at:
```python
LasiEvaluationGateStatus.REFERENCE_DATA_PENDING
```

### 6.2 Binding Gate Transition Rules

```
                      EXTERNAL VALIDATION GATE STATE MACHINE
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                          [REFERENCE_DATA_PENDING]                               │
│                                     │                                           │
│                     (Authorized Microdata Ingested,                             │
│                      60/40 Partitioning Executed,                               │
│                     Partition C Sealed in Vault)                                │
│                                     │                                           │
│                                     ▼                                           │
│                           [CALIBRATION_ACTIVE]                                  │
│                                     │                                           │
│                     (Parameters Calibrated on A,                                │
│                     Internal 5-Fold CV Completed,                               │
│                     Parameter Vector Θ* Frozen)                                 │
│                                     │                                           │
│                                     ▼                                           │
│                           [CALIBRATION_FROZEN]                                  │
│                                     │                                           │
│                     (Holdout Ticket Issued,                                     │
│                     Vault Decrypted & Consumed,                                 │
│                     Partition C Evaluated)                                      │
│                                     │                                           │
│                     ┌───────────────┴───────────────┐                           │
│                     ▼                               ▼                           │
│     (All Criteria Satisfied)             (Any Criterion Violated)               │
│             [PASSED]                             [FAILED]                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

1. **Conditions Under Which Gate MUST NOT Advance:**
   - The gate MUST NOT advance solely because unit, integration, or Monte Carlo regression tests pass.
   - The gate MUST NOT advance against synthetic test fixtures (`lasi_wave1_sample_fixture.csv`).
   - The gate MUST NOT advance if calibration was performed using holdout Partition C or full-sample unpartitioned data.
   - The gate MUST NOT advance if the persistent audit ledger has been tampered with, deleted, or bypassed.
2. **Mandatory Conditions for Advancing to `CALIBRATION_FROZEN`:**
   - Genuine LASI reference data ingested under verified DUA with SHA-256 manifest.
   - Deterministic 60/40 cluster partition completed with verified zero-leakage invariant.
   - Partition C successfully sealed in AES-256-GCM vault with persistent ledger record.
   - Parameters $\mathbf{\Theta}^*$ estimated exclusively on Partition A and formally frozen.
3. **Mandatory Conditions for Advancing to `PASSED`:**
   - Single-use holdout ticket authorized and executed against Partition C.
   - All 9 quantitative acceptance criteria (Table in Section 5.3) satisfied.
   - Complex survey design standard errors and NIST Student's $t$ critical values computed via `variance.py`.
   - Comprehensive external validation report archived and signed off.

---

## 7. Execution Roadmap for Milestone 5

| Milestone Phase | Planned Activities | Deliverables / Artifacts | Verification Gate |
| :--- | :--- | :--- | :---: |
| **Phase 5.1** | Secure Ingestion & Survey Diagnostics | `data/reference/derived/SURVEY_DESIGN_DIAGNOSTICS.json`, `INGESTION_MANIFEST.json` | DUA Checksum Match |
| **Phase 5.2** | Deterministic 60/40 PSU Partitioning | `derived_partition_a/lasi_partition_a.csv`, `encrypted_holdout/lasi_holdout_vault.json` | Leakage Audit ($A \cap C = \emptyset$) |
| **Phase 5.3** | Empirical Calibration on Partition A | Internal 5-fold cross-validation loss optimization on free parameters $\mathbf{\Theta}$. | Simplex Convergence on A |
| **Phase 5.4** | Parameter Freeze & Preregistration | `docs/research_alignment/milestone5_frozen_calibration_report.md` | Formal Parameter Freeze |
| **Phase 5.5** | Holdout Evaluation on Partition C | Single-use unblinded execution of `LasiEvaluator` against Partition C via `HoldoutAccessTicket`. | Single-Use Ledger Burn |
| **Phase 5.6** | Final Gate Determination & Closure | `docs/research_alignment/milestone5_external_validation_report.md` | `PASSED` or `FAILED` |

---

## 8. Summary Readiness Verdict

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           MILESTONE 5 READINESS VERDICT                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ Pipeline Architecture & Ingestion Engine:           READY & VERIFIED (368 Tests Green)  │
│ Deterministic 60/40 PSU Partitioning Engine:        READY & VERIFIED (Leakage Free)     │
│ AES-256-GCM Cryptographic Holdout Vault:           READY & VERIFIED (Process-Locked)   │
│ Design-Based Variance & TSL Engine:                 READY & VERIFIED (FPC-Guarded)      │
│ Institutional Governance & DUA Protocol:            DOCUMENTED & BINDING                │
│ Pre-Ingestion Checklist & Missingness Taxonomy:     SPECIFIED & DEFENSIVE               │
│ Predeclared Loss Functions & Acceptance Criteria:    PRE-REGISTERED & FROZEN             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ OVERALL READINESS STATUS:                           READY_FOR_GOVERNED_EXECUTION        │
│ EXTERNAL VALIDATION GATE:                           REFERENCE_DATA_PENDING (LOCKED)     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

The SYNAPSE Phase 2 simulation pipeline is **fully prepared and verified** for Milestone 5. Ingestion of genuine LASI microdata may proceed immediately upon formal authorization of the research Data Use Agreement (DUA).
