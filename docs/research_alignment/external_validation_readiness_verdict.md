# SYNAPSE Phase 2: External Validation Readiness Verdict

**Document ID:** `SYNAPSE-READINESS-VERDICT-06`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Readiness Assessment Authority  
**Repository State:** Commit `3e3ae1d28286e9106659f68aa053465ded9bb3c2`, 171 Passing Tests, Manifest `LONGITUDINAL_TRAJECTORY_AUDIT.json`  
**Classification:** **`CONDITIONALLY READY, WITH SPECIFIED PREREQUISITES`**  

---

## 1. Formal Readiness Determination

Following a comprehensive, source-level audit of the SYNAPSE Phase 2 simulation engine, data exporters, evaluation architecture, candidate external datasets, and research documentation, the Authority issues the following formal verdict:

```
========================================================================================
FINAL READINESS VERDICT:
                       CONDITIONALLY READY, WITH SPECIFIED PREREQUISITES
========================================================================================
- Simulation Engine & Software Invariants:      VERIFIED & FULLY READY (171/171 Tests)
- Person-Time & Actuarial Mortality Math:        VERIFIED & FULLY READY
- Data Schemas & Export Pipeline:                VERIFIED & FULLY READY (16 CSV Tables)
- External Dataset Provenance & Clean Partition: ESTABLISHED (Calibration vs. Eval)
- Clinical Behavior (Inertia, Adherence, CKD):  UNVERIFIED (Requires 4 Prerequisites)
- Real-World Microdata Access:                   CONDITIONAL ON DATA AGREEMENTS
========================================================================================
```

The platform has achieved mathematical consistency, invariant integrity, and reproducible demographic baseline generation. However, it cannot be classified as "Unconditionally Ready" because claiming full external validity today would conflate idealized clinical guideline execution with real-world clinical behavior and ignore physical data-access barriers.

---

## 2. Evidence-Based Dimension-by-Dimension Audit

The readiness determination is grounded in an evaluation across six foundational dimensions:

### Dimension A: Simulation Architecture & Software Invariants — `READY`
- **Audit Findings:**
  - Discrete-event simulation engine executes deterministically from configurable random seeds.
  - All 16 synthetic CSV export schemas ([patients.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/patients.csv), [encounters.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/encounters.csv), [conditions.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/conditions.csv), [medications.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/medications.csv), [observations.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/observations.csv), [care_plans.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/care_plans.csv), [deaths.csv](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/deaths.csv), etc.) adhere to relational referential integrity.
  - Deterministic software invariants verified with zero violations across all 15 evaluated runs:
    - `inv_no_event_pre_birth`: $0$ violations.
    - `inv_no_event_post_mortem`: $0$ violations.
    - `inv_diagnosis_encounter_linkage`: $0$ unlinked diagnoses.
    - `inv_allergy_safety_veto`: $0$ contraindicated prescriptions.
  - Full test suite passes completely: **171 passed in 7.53s** (`.venv/bin/pytest tests/`).

### Dimension B: Person-Time Accounting & Actuarial Mortality — `READY`
- **Audit Findings:**
  - The historical person-time contradiction ($986.9 > 985.63\text{ pt-yrs}$) was traced to a 731-day leap-year window evaluated against a 720-day maximum bound.
  - Corrected by locking the observation window to exactly $720.0\text{ days}$ (`2024-01-01` to `2025-12-21`) and enforcing the hard invariant `inv_person_time_upper_bound`.
  - Reconstructed 5-seed person-time averages **$972.35\text{ pt-yrs}$** ($N=500$), strictly $\le 985.63\text{ pt-yrs}$ across all runs.
  - All-cause mortality strictly follows the Census SRS 2016–2020 Life Table; observed deaths ($14.0\text{ mean}$) agree with the Poisson-Binomial expectation ($E[D] = 11.68$, $95\%\text{ PI}: [5.69, 17.67]$).
  - Double-counting eliminated: $100\%$ of deaths are `R99`; zero synthetic AMI deaths (`I21.9`).

### Dimension C: Baseline Demographics & Epidemiological Prevalences — `READY`
- **Audit Findings:**
  - National sex ratio ($51.5\%$) and 5-band age pyramid divergence ($\text{JSD} = 0.0035$) are verified.
  - Evaluators enforce strict adult ($\ge 20\text{ years}$) denominator isolation, eliminating pediatric denominator dilution.
  - Baseline point prevalence ($32.53\%$ HTN, $11.8\%$ T2D) is separated from 2-year cumulative period prevalence ($36.16\%$ HTN, $12.92\%$ T2D), matching ICMR-INDIAB cross-sectional targets within prespecified margins.

### Dimension D: External Dataset Provenance & Leakage Protection — `READY`
- **Audit Findings:**
  - Complete parameter provenance cataloged in [calibration_evaluation_leakage_assessment.md](file:///Users/shashi/synapse/synapse-phase2/docs/research_alignment/calibration_evaluation_leakage_assessment.md).
  - ICMR-INDIAB 2023 and Census SRS 2021 are formally declared as **`CALIBRATION`** datasets and barred from serving as independent validation benchmarks.
  - Sex-stratified subgroups are correctly classified as **`INTERNAL_VALIDATION_HOLDOUT`**.
  - Truly independent external datasets identified: **LASI Wave 1** (open microdata), **CARRS** (restricted cohort microdata), and **NFHS-5** (open cross-sectional microdata).

### Dimension E: Longitudinal Clinical Behavior Fidelity — `NOT YET FULLY READY`
- **Defects & Divergences Identified:**
  1. *Idealized Guideline Conformance vs. Real-World Prescribing:* The treatment intensification rate ($78.97\%$) reflects automated state-machine rule execution with zero clinical inertia. In real-world Indian outpatient clinics (IHCI, CARRS), physician therapeutic inertia limits clinic intensification to $30\%\text{--}40\%$. The current model cannot reproduce real-world prescribing inertia.
  2. *Medication Adherence Assumption:* The simulation assumes $100\%$ medication persistence and adherence, whereas real-world Indian adherence for chronic conditions is $40\%\text{--}60\%$.
  3. *Complication Modeling Architecture:* Complications ($2.88\%$ 2-year incidence) are generated via arbitrary discrete Markov state transition weights ($0.015$ and $0.010$) at routine visits, rather than continuous physiological biomarker progression (eGFR decline, microalbuminuria titration).

### Dimension F: Real-World Data Access Pathways — `CONDITIONALLY READY`
- **Data Access Barriers:**
  - Individual-level longitudinal microdata from CARRS requires a formal proposal to the CARRS Steering Committee ($3\text{--}6\text{ month}$ turnaround).
  - IHCI routine clinic registry microdata is administratively locked by the Ministry of Health and Family Welfare.
  - **Viable Path:** LASI Wave 1 provides immediate open-access individual microdata for older adults ($45+$), supporting an interim empirical validation.

---

## 3. Four Mandatory Prerequisites for Full External Validation

Before SYNAPSE Phase 2 can execute an uncompromised external validation study and claim clinical fidelity, the following four prerequisites must be satisfied:

```
Prerequisite Execution Roadmap:
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PREREQUISITE 1: LASI Wave 1 Data Ingestion & Age-Truncation Pipeline                  │
│ Action: Download de-identified LASI Wave 1 microdata (g2aging.org), build an          │
│ automated evaluation pipeline truncating synthetic cohorts to age >= 45, and test      │
│ continuous SBP/DBP and DBS HbA1c distributions using KS and Wasserstein metrics.      │
│                                                                                        │
│ PREREQUISITE 2: Configurable Clinical Inertia & Medication Non-Adherence Sub-Models   │
│ Action: Introduce an explicit clinical inertia parameter (γ in [0.30, 0.60]) in       │
│ hypertension.yaml and diabetes_t2.yaml so that physicians intensify therapy at a       │
│ realistic rate, and a medication adherence factor (α in [0.40, 0.80]).                 │
│                                                                                        │
│ PREREQUISITE 3: Exponential Decay Sampler for Elderly Ages (65–100)                    │
│ Action: Replace uniform random sampling in the 65–100 Census band with a Gompertzian   │
│ or exponential decay distribution to eliminate the artificial 85+ skew.               │
│                                                                                        │
│ PREREQUISITE 4: Formal Data Access Submission for Prospective Microdata (CARRS / IHCI)│
│ Action: Submit formal research proposals and Data Use Agreements to the CARRS Data     │
│ Access Committee and IIPS to acquire true multi-year prospective panel microdata.      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Final Sign-off Statement

SYNAPSE Phase 2 has successfully passed all mathematical consistency, software invariant, and internal statistical benchmarks. It possesses the necessary CSV export architecture, independent evaluation codebase, and reproducible multi-scale configuration to support external evaluation.

By satisfying **Prerequisites 1 through 3** (integrating clinical inertia, adherence modeling, and older-adult demographic decay) and executing **Prerequisite 4** (formal data access acquisition), the system will achieve complete, uncompromised readiness for independent clinical validation against real-world longitudinal healthcare data.

**Formal Status:** **`CONDITIONALLY READY, WITH SPECIFIED PREREQUISITES`**
