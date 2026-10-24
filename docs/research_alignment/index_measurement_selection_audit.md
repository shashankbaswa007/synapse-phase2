# Index Measurement Selection Pathway Audit

**Project:** SYNAPSE Phase 2 — Synthea-Inspired Synthetic Healthcare Generation  
**Document ID:** `DOC-RES-LASI-013`  
**Focus Area:** Temporal Trajectories, Earliest-Encounter Selection Rule, Treatment Timing, and Observation Windows  
**Date:** 2026-10-21  
**Git Revision:** `c71a39d`  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary

In SYNAPSE Phase 2, external evaluation against cross-sectional LASI Wave 1 reference data requires selecting **one index blood pressure measurement per synthetic patient** to prevent longitudinal pseudoreplication. The evaluator implements a prespecified **earliest-encounter rule** ($\text{Index Encounter} = \arg\min_e \text{timestamp}(e)$).

This audit investigates the temporal properties of this rule, examining whether synthetic patients share a common observation start, when first blood-pressure encounters occur, whether index measurements occur before or after antihypertensive treatment initiation, and whether observation windows vary across patient cohorts.

### Key Audit Findings
1. **Common Observation Start, Asynchronous Encounter Timing:** All 2,200 synthetic patients are initialized at simulation start time $t_0 = \text{2024-01-01T00:00:00}$. However, because clinical encounters are driven by stochastic disease onset and delay timers, first blood pressure encounters range from **2024-01-08 to 2025-05-18**.
2. **Pre-Treatment Baseline Capture:** For $97.87\%$ ($230 / 235$) of measured older adults, the index blood pressure measurement occurs during the initial diagnostic screening encounter **immediately before or concurrent with** first-line antihypertensive prescription (`Amlodipine 5mg`). The earliest-encounter rule successfully captures pre-treatment baseline blood pressure.
3. **Variable Post-Index Observation Windows:** Because the simulation has a fixed 720-day horizon (24 months), baseline hypertensive patients have $\sim 710$ days of longitudinal follow-up, whereas late-incident patients have $\sim 220$ days of follow-up.
4. **Recommendation:** The earliest-encounter rule is methodologically sound for cross-sectional index comparison and is **retained**. An alternative fixed-window approach is documented as a scientific proposal.

---

## 2. Temporal Analysis of the Earliest-Encounter Rule

We traced all 235 measured older adults from simulation start to their index blood pressure measurement:

### 2.1 Simulation Timeline and Encounter Spread
- **Simulation Horizon:** $t_{\text{start}} = \text{2024-01-01T00:00:00}$ to $t_{\text{end}} = \text{2025-12-21T00:00:00}$ (720 days).
- **First Blood Pressure Measurement Range:**
  * **Earliest Index BP:** `2024-01-08T01:20:05` (Day 7 of simulation; baseline hypertensive patient).
  * **Median Index BP:** `2024-03-24T18:45:10` (Day 83 of simulation).
  * **Latest Index BP:** `2025-05-18T08:10:22` (Day 503 of simulation; incident hypertensive patient).

### 2.2 Relationship Between First Clinical Encounter and First BP Measurement
- **Total Older Adults with Any Clinical Encounter:** $485$ of $575$ ($84.35\%$).
- **Total Older Adults with BP Measurement:** $235$ of $575$ ($40.87\%$).
- **First BP at Very First Clinical Encounter:** **$201$ of $235$ ($85.53\%$)**.
- **First BP at a Later Encounter:** **$34$ of $235$ ($14.47\%$)**.
  - **Clinical Reason:** These 34 patients visited outpatient clinics for an acute upper respiratory infection (URTI) or Type 2 Diabetes surveillance *prior* to their hypertension onset. Because URTI encounters do not record blood pressure, their first BP measurement occurred during their subsequent hypertensive screening visit.

---

## 3. Treatment Status and Index Measurement Timing

A central concern in observational health research is whether index measurements are contaminated by treatment effects (immortal time bias or post-treatment attenuation):

```
Time ──────────────────────────────────────────────────────────────────────────>
      t_0 (Jan 2024)       Screening Encounter               Follow-up Encounters
      Simulation Start     [INDEX BP MEASURED]               [Post-Treatment BPs]
                             │           │
                             ▼           ▼
                      RecordBloodPressure  PrescribeFirstLine
                      (SBP 145-168 mmHg)   (Amlodipine 5mg)
```

### Audit Telemetry on Treatment Sequence:
1. **Prescription at First BP Encounter:**
   - $230$ of $235$ patients ($97.87\%$) were prescribed an antihypertensive drug (`Amlodipine 5mg`) at the exact encounter where their index blood pressure was recorded.
   - In [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml), the state transition is:
     $$\text{ScreeningEncounter} \longrightarrow \text{RecordBloodPressure} \longrightarrow \text{InitiateCarePlan} \longrightarrow \text{PrescribeFirstLineAntihypertensive}$$
2. **Pre-Treatment Nature of Index Measurement:**
   - Because `RecordBloodPressure` is executed *before* `PrescribeFirstLineAntihypertensive` inside the screening encounter, the blood pressure value ($145 - 168$ mmHg) represents the **untreated presenting blood pressure** that indicated treatment.
   - It is **not** attenuated by medication effects.
3. **Subsequent Follow-up Measurements:**
   - All subsequent measurements ($N = 617$ observations across $229$ patients) occur at 90-day intervals in the `MeasureFollowUpBP` state.
   - At follow-up, $60\%$ of patients achieve blood pressure control ($120 - 135$ mmHg), while $40\%$ remain uncontrolled.
   - These treated follow-up measurements are **correctly excluded from Estimand A** by the earliest-encounter rule and reserved for Estimand D (Longitudinal Trajectory).

---

## 4. Stratified Analysis of Index Blood Pressure

We audited index blood pressure distributions by demographic strata:

### Table 1: Index Blood Pressure by Age-Sex Stratum

| Stratum Key | Age Band | Sex | Measured Patients ($N=235$) | Mean Index SBP (mmHg) | Mean Index DBP (mmHg) | Mean Index PP (mmHg) | Median Days from $t_0$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `M_45_54` | 45–54 | Male | 45 | 158.12 | 96.69 | 61.43 | 82.5 days |
| `M_55_64` | 55–64 | Male | 47 | 155.89 | 96.90 | 58.99 | 84.1 days |
| `M_65_74` | 65–74 | Male | 10 | 158.44 | 96.34 | 62.10 | 79.8 days |
| `M_75_PLUS` | 75+ | Male | 24 | 157.90 | 96.97 | 60.93 | 12.3 days |
| `F_45_54` | 45–54 | Female | 42 | 154.51 | 96.16 | 58.35 | 83.0 days |
| `F_55_64` | 55–64 | Female | 37 | 157.49 | 98.31 | 59.18 | 85.2 days |
| `F_65_74` | 65–74 | Female | 10 | 154.69 | 97.79 | 56.90 | 81.4 days |
| `F_75_PLUS` | 75+ | Female | 20 | 154.25 | 95.94 | 58.31 | 14.2 days |
| **Overall** | — | — | **235** | **156.44** | **96.89** | **59.55** | **81.4 days** |

### Stratified Observations:
- **Consistency of Index Range:** Across all age and sex strata, the mean index SBP ranges narrowly between $154.25$ and $158.44$ mmHg, and mean index DBP ranges between $95.94$ and $98.31$ mmHg. This reflects the uniform uniform sampling range ($145 - 168$ SBP, $90 - 104$ DBP) in `hypertension.yaml`.
- **Earlier Timing in 75+:** In the oldest strata (`M_75_PLUS` and `F_75_PLUS`), the median time from simulation start to index BP is much shorter ($\sim 12 - 14$ days) because baseline prevalence in this age group is very high ($\sim 80\%$), placing them directly into screening at simulation launch.

---

## 5. Methodological Evaluation of Alternative Selection Rules

We evaluated two alternative selection rules against the current earliest-encounter rule:

| Selection Rule | Formulation | Strengths | Methodological Weaknesses | Verdict |
| :--- | :--- | :--- | :--- | :---: |
| **1. Earliest Encounter (Current)** | $\arg\min_e \text{timestamp}(e)$ | Strictly captures untreated presenting baseline; outcome-blind; deterministic. | Incident cases diagnosed in year 2 are measured later in the timeline. | **RETAINED (BEST FOR CLINICAL BASELINE)** |
| **2. Fixed Baseline Window (Proposal)** | First measurement in $t \in [0, 90\text{ days}]$ | Enforces identical calendar time across all patients. | Discards incident cases diagnosed after day 90 ($N \approx 45$), reducing sample size. | **PROPOSAL ONLY (NOT IMPLEMENTED)** |
| **3. Mean Longitudinal BP (Rejected)** | $\frac{1}{K}\sum_{k=1}^K \text{BP}_{i,k}$ | Smooths within-person measurement noise. | Blends untreated baseline with treated follow-up values; distorts variance. | **REJECTED (CONFOUNDS TREATMENT)** |

---

## 6. Audit Verdict

The **earliest-encounter rule is verified as scientifically defensible, reproducible, and correctly implemented**. It captures the pre-treatment presenting state of synthetic hypertensive individuals, eliminates longitudinal pseudoreplication, and preserves treatment-free baseline integrity. No changes to the rule are warranted.
