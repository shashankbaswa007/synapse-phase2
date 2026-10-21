# Blood Pressure Missingness, Sample Sizes, and Audit Report

**Project:** SYNAPSE Phase 2 — Synthea-Inspired Synthetic Healthcare Generation  
**Document ID:** `DOC-RES-LASI-010`  
**Focus Area:** Longitudinal Telemetry Audit, Missingness Quantification, and Before-and-After Analysis  
**Date:** 2026-10-21  
**Git Revision:** `c71a39d`  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary

This report delivers a rigorous quantitative audit of sample sizes, paired blood-pressure availability, missingness, and strata coverage in SYNAPSE Phase 2. The audit evaluates a full synthetic population cohort ($N = 2,200$ synthetic patients, 575 older adults aged $\ge 45$) generated with fixed seed 42 under the standard Indian demographic profile (`india_default_v1.yaml`).

The analysis confirms the complete resolution of the longitudinal DBP export gap, verifies that 100% of recorded blood pressure encounters possess valid paired observations, documents the empirical missingness rate among community older adults, and contrasts the current data architecture against the pre-intervention baseline.

---

## 2. Comprehensive Blood Pressure Sample Size and Missingness Audit

All metrics are derived deterministically by `LasiExternalEvaluator` from exported CSV tables (`patients.csv`, `encounters.csv`, `observations.csv`, `conditions.csv`, `medications.csv`):

| Telemetry Audit Dimension | Count / Rate | Scientific Interpretation & Boundary |
| :--- | :---: | :--- |
| **Total Synthetic Population** | **2,200** | Full population cohort across all age groups (0 to 100 years). |
| **Eligible Older Adults (Age $\ge$ 45)** | **575 (26.14%)** | Target population for LASI Wave 1 comparison; satisfies minimum sample gate ($\ge 500$). |
| **Patients with $\ge$ 1 Valid Paired BP Measurement** | **235 (40.87%)** | Older adult patients who developed hypertension and entered clinical surveillance. |
| **Total Clinical BP Encounters** | **852** | Total outpatient visits where vitals were recorded during the simulation. |
| **Total Valid Longitudinal SBP Observations** | **852** | Total exported SBP observations in `observations.csv` (LOINC 8480-6). |
| **Total Valid Longitudinal DBP Observations** | **852** | Total exported DBP observations in `observations.csv` (LOINC 8462-4). |
| **Total Paired Observations (Same Encounter & Time)** | **852 (100.0%)** | Observations sharing exact `patient_id`, `encounter_id`, and `timestamp`. |
| **Patients with ONLY SBP (Missing DBP)** | **0 (0.0%)** | Zero unpaired SBP readings; no missing DBP among measured encounters. |
| **Patients with ONLY DBP (Missing SBP)** | **0 (0.0%)** | Zero unpaired DBP readings. |
| **Implausible Pulse Pressure Count** | **0 (0.0%)** | Observations violating $\text{PP} < 20$ mmHg, $\text{PP} > 110$ mmHg, or $\text{SBP} \le \text{DBP}$. |
| **Unmeasured Rate Across Older Adults** | **59.13% (340 / 575)** | Community older adults who did not have a hypertensive clinical encounter. |
| **Populated Age-Sex Strata** | **8 of 8 (100%)** | Complete coverage across Census SRS older adult strata. |
| **Overall Validation Gate Status** | **`REFERENCE_DATA_PENDING`** | Gated pending receipt of credentialed LASI microdata via IIPS. |

---

## 3. Populated Age-Sex Strata Audit (Census SRS Older Adults)

To ensure comparability without sparse-cell distortion, synthetic older adults were audited across the 8 standard Census SRS strata:

| Stratum ID | Age Group | Sex | Synthetic Count ($N=575$) | Reference Count ($N=50$) | Census SRS 2021 Weight ($W_s$) | Strata Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `M_45_54` | 45–54 | Male | 118 | 9 | 0.2014 | **POPULATED** |
| `M_55_64` | 55–64 | Male | 102 | 7 | 0.1472 | **POPULATED** |
| `M_65_74` | 65–74 | Male | 54 | 5 | 0.0982 | **POPULATED** |
| `M_75_PLUS` | 75+ | Male | 25 | 2 | 0.0485 | **POPULATED** |
| `F_45_54` | 45–54 | Female | 108 | 11 | 0.2086 | **POPULATED** |
| `F_55_64` | 55–64 | Female | 88 | 8 | 0.1491 | **POPULATED** |
| `F_65_74` | 65–74 | Female | 52 | 5 | 0.0964 | **POPULATED** |
| `F_75_PLUS` | 75+ | Female | 28 | 3 | 0.0506 | **POPULATED** |

*All 8 strata are fully populated ($N_s \ge 25$ in all synthetic strata), permitting robust direct standardization without zero-cell imputation.*

---

## 4. Before-and-After Analysis of Blood Pressure Availability

The following table contrasts the synthetic cohort before and after the paired blood pressure model implementation:

| Pipeline Dimension | Pre-Correction Baseline | Current Post-Correction Cohort | Scientific Impact |
| :--- | :---: | :---: | :--- |
| **Total SBP Observations** | 863 | 852 | Preserved longitudinal surveillance volume. |
| **Total DBP Observations** | **0** | **852** | **Resolved missing observation defect.** |
| **Paired Observation Rate** | **0.0%** | **100.0%** | All observations paired at exact encounter & timestamp. |
| **Index Measurement Pathway** | Not Implemented (Pooled all visits) | **Prespecified Index BP (Earliest Encounter)** | **Eliminated pseudoreplication and sample size inflation.** |
| **Patient-Level Sample Size ($N_{\text{pts}}$)** | Conflated with observations ($N=863$) | **235 distinct patients** | Respects independent observation assumptions. |
| **Pulse Pressure Distribution** | Not Computable ($\text{DBP} = \text{None}$) | **Mean 59.55 mmHg (Ref: 60.18 mmHg)** | **Biological arterial stiffness fidelity ($W_1 = 1.23$ mmHg).** |
| **Measurement-Defined HTN** | Evaluated on SBP only | **Evaluated on SBP, DBP, and Rx** | Exact clinical case definition ($\ge 140 \lor \ge 90 \lor \text{Rx}$). |
| **Longitudinal Trajectory** | Conflated with cross-sectional | **Segregated into Estimand D (UNVERIFIED)** | Avoids false validation claims on single-wave data. |
| **Validation Gate Status** | `REFERENCE_DATA_PENDING` | `REFERENCE_DATA_PENDING` | **Safeguards preserved; no premature PASS claims.** |

---

## 5. Unresolved Clinical and Statistical Limitations

While the paired blood pressure data pathway is technically and architecturally complete, several important scientific limitations remain documented:

1. **Unmeasured Community Individuals (59.13%):**
   In real-world surveys (such as LASI), trained field investigators measure blood pressure for *all* consenting household participants regardless of whether they have a doctor visit. In SYNAPSE, blood pressure is recorded at outpatient clinical encounters. Older adults who do not experience a hypertensive screening encounter during the simulation remain unmeasured in EHR tables.
2. **Provisional Acceptance Thresholds:**
   The acceptance thresholds for continuous distributional similarity (Wasserstein distance $W_1 \le 4.0$ mmHg, Kolmogorov-Smirnov $KS \le 0.08$) remain provisional pending formal epidemiological consensus for synthetic health models.
3. **Reference Data Authorization Requirement:**
   Current evaluations are conducted against a structural test fixture (`data/evaluation/fixtures/lasi_wave1_sample_fixture.csv`). Genuine external evaluation requires credentialed microdata obtained through the International Institute for Population Sciences (IIPS) and Gateway to Global Aging Data under an executed Data Use Agreement (DUA).
4. **Single-Wave Cross-Sectional Constraint:**
   Longitudinal blood pressure trajectories and treatment response ($\Delta \text{SBP} = -14.47$ mmHg) cannot be certified against LASI Wave 1. Longitudinal validity must remain formally **`UNVERIFIED`** until multi-wave longitudinal panel data are accessible.

---

## 6. Audit Verdict

The paired blood pressure data model and patient-level comparison pathway are verified, reproducible, and fully integrated. The overall validation status remains strictly **`REFERENCE_DATA_PENDING`**.
