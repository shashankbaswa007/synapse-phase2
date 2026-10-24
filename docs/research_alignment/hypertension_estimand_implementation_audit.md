# Hypertension Estimand Implementation and Independence Audit

**Project:** SYNAPSE Phase 2 — Synthea-Inspired Synthetic Healthcare Generation  
**Document ID:** `DOC-RES-LASI-012`  
**Focus Area:** Estimand Definitions, Metric Decoupling, Boolean Verification, and Code Traceability  
**Date:** 2026-10-21  
**Git Revision:** `c71a39d`  
**Overall Validation Gate Status:** **`REFERENCE_DATA_PENDING`**  

---

## 1. Executive Summary

This audit establishes the formal definition and implementation separation of hypertension estimands in SYNAPSE Phase 2, investigates why measurement-defined and EHR-recorded hypertension prevalence both equal **40.87%**, verifies the underlying Boolean conditions and source tables, and adds regression tests proving metric independence under counterfactual data states.

### Core Audit Verdict
1. **The Code Paths are Strictly Independent:** Measurement-defined hypertension and EHR-recorded hypertension query **completely separate source tables** using **completely separate Boolean logic**:
   - `lasi_prev_measurement_defined_htn_older_adult`: Queries `observations.csv` (vital signs) and `medications.csv` (antihypertensive prescriptions).
   - `lasi_prev_htn_older_adult`: Queries `conditions.csv` (ICD-10 condition code `I10`).
2. **Identical Prevalence (40.87%) is an Empirical Cohort Property, Not a Code Defect:** In `hypertension.yaml`, every patient who reaches `RecordBloodPressure` has an initial SBP in $[145, 168]$ mmHg and DBP in $[90, 104]$ mmHg and is simultaneously diagnosed with `I10` at their screening encounter. Healthy older adults ($N = 340$) have no BP recorded, no diagnosis, and no prescriptions. Hence, both numerators equal exactly $235$, and both denominators equal $575$ ($235 / 575 = 40.87\%$).
3. **Current Evaluator Computes a Healthcare-Observed Estimand:** The blood-pressure continuous metrics (`lasi_bp_sbp_distribution`, `lasi_bp_dbp_distribution`) represent the **blood-pressure distribution among synthetic older adults with qualifying clinical encounters**, NOT the general population distribution of all older adults.

---

## 2. Formal Definition of Estimands

To avoid comparing non-comparable populations, we formalize two distinct continuous blood-pressure estimands:

### Estimand 1: Population-Level Blood-Pressure Distribution
- **Target Population:** All eligible synthetic older adults residing in the community (Age $\ge 45$, $N = 575$).
- **Statistical Estimand:** The marginal cumulative distribution function $F_{\text{pop}}(y)$ of blood pressure (SBP, DBP, PP) across all older adults, regardless of whether they ever attended a clinic or received a diagnosis.
- **Reference Ground Truth:** LASI Wave 1 Household Survey (which tested all household respondents).
- **Simulator Availability:** **NOT CURRENTLY GENERATED.** In the current simulation, normotensive individuals who do not develop hypertension have zero blood pressure observations in `observations.csv`.

### Estimand 2: Healthcare-Observed Clinical Blood-Pressure Distribution
- **Target Population:** Synthetic older adults presenting to outpatient clinics who undergo blood pressure measurement ($N = 235$).
- **Statistical Estimand:** The conditional distribution $F_{\text{clinical}}(y \mid \text{Encounter} = 1, \text{Measured} = 1)$.
- **Simulator Availability:** **COMPUTED BY CURRENT EVALUATOR.** The current evaluator computes this conditional clinical distribution.

> [!WARNING]
> **METHODOLOGICAL NON-EQUIVALENCE**  
> Comparing Estimand 2 (measured clinical patients) directly against Estimand 1 (general population survey) introduces **indication bias**. The synthetic mean SBP of $156.44$ mmHg reflects a purely hypertensive outpatient presenting population, whereas the LASI fixture mean SBP of $148.51$ mmHg reflects an unselected community survey (containing normotensives).

---

## 3. Code Path Tracing and Boolean Verification

We traced the exact code paths in [`synapse_simulator/evaluation/lasi/evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py):

### 3.1 Metric 1: Measurement-Defined Hypertension Prevalence
* **Metric ID:** `lasi_prev_measurement_defined_htn_older_adult`
* **Category:** `PREVALENCE`
* **Population:** `POPULATION_B_OLDER_ADULTS` (Age $\ge 45$)
* **Target Estimand:** Prespecified epidemiological bio-marker definition of hypertension.
* **Source Tables:** `observations.csv` (index paired observations) and `medications.csv` (prescriptions).
* **Exact Code Logic ([`evaluator.py` lines 771–793](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py#L771-L793)):**
  ```python
  antihypertensive_keywords = {
      "amlodipine", "telmisartan", "enalapril", "losartan",
      "hydrochlorothiazide", "atenolol", "metoprolol"
  }
  rx_older_pids = set()
  for rx in self.medications:
      p_id = rx.get("patient_id", "")
      d_name = (rx.get("drug_name") or rx.get("medicine_id") or "").lower()
      if any(med in d_name for med in antihypertensive_keywords):
          rx_older_pids.add(p_id)

  m_htn_pids = set()
  for r in index_paired_records:
      pid = r["patient_id"]
      if r["sbp"] >= 140.0 or r["dbp"] >= 90.0 or pid in rx_older_pids:
          m_htn_pids.add(pid)
  for pid in rx_older_pids:
      if pid in older_adult_pids:
          m_htn_pids.add(pid)

  n_m_htn = len(m_htn_pids)
  syn_m_htn_prev = round(100.0 * n_m_htn / n_older_total, 2)
  ```
* **Boolean Formula:**
  $$\text{MeasuredHTN}_i = (\text{IndexSBP}_i \ge 140.0) \lor (\text{IndexDBP}_i \ge 90.0) \lor (\text{Patient}_i \in \text{AntihypertensiveRx})$$
* **Denominator:** All eligible older adults ($N_{\text{older\_total}} = 575$).

### 3.2 Metric 2: EHR-Recorded Hypertension Diagnosis Prevalence
* **Metric ID:** `lasi_prev_htn_older_adult`
* **Category:** `PREVALENCE`
* **Population:** `POPULATION_B_OLDER_ADULTS` (Age $\ge 45$)
* **Target Estimand:** Documented clinical diagnosis in electronic health records.
* **Source Table:** `conditions.csv`.
* **Exact Code Logic ([`evaluator.py` lines 1025–1028](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py#L1025-L1028)):**
  ```python
  syn_htn_ids = {c["patient_id"] for c in self.conditions if c.get("condition_code") == "I10"}
  syn_htn_count = sum(1 for p in syn_older if p["patient_id"] in syn_htn_ids)
  syn_htn_prev = 100.0 * syn_htn_count / n_syn
  ```
* **Boolean Formula:**
  $$\text{DiagnosedHTN}_i = (\exists c \in \text{Conditions}_i : c.\text{condition\_code} = \text{"I10"})$$
* **Denominator:** All eligible older adults ($n_{\text{syn}} = 575$).

---

## 4. Root Cause of the 40.87% = 40.87% Prevalence Match

We proved by empirical cross-tabulation why the two metrics produce identical estimates in the generated cohort:

```
                                  EHR Diagnosis (I10)
                             Positive (+)      Negative (-)
  Measurement-Defined   (+)      235                0            235
  Hypertension          (-)        0              340            340
                                 235              340            575
```

### Explanatory Mechanisms in the Module State Machine:
1. **100% Concordance in Positive Class:**
   - In [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml), `RecordBloodPressure` is reached only via `ScreeningEncounter` (which diagnoses `I10`).
   - Every patient who reaches `RecordBloodPressure` receives an initial SBP draw from $[145.0, 168.0]$ mmHg and DBP draw from $[90.0, 104.0]$ mmHg.
   - Every single measured patient has $\text{SBP} \ge 140.0$ and $\text{DBP} \ge 90.0$.
   - Every single measured patient is also prescribed `Amlodipine 5mg` at that encounter or immediately following it.
   - Therefore, all 235 measured patients satisfy **both** the measurement definition and the diagnosis definition ($235 / 235 = 100\%$).
2. **100% Concordance in Negative Class:**
   - In the simulation, healthy older adults ($N = 340$) never enter the hypertension state machine.
   - They have zero entries in `conditions.csv` with code `I10`.
   - They have zero entries in `observations.csv` with code `SBP` or `DBP`.
   - They have zero entries in `medications.csv` with antihypertensive drugs.
   - Therefore, none of the 340 unmeasured older adults satisfy either definition.
3. **Conclusion:** The two metrics are **completely decoupled in implementation**, but evaluate to the same percentage ($40.87\%$) because **in SYNAPSE Phase 2, hypertension onset, clinical screening, blood pressure measurement, and diagnosis occur synchronously in the same state machine path**.

---

## 5. Automated Proofs of Metric Decoupling

To establish beyond doubt that the metrics are not coupled, five unit tests were implemented in [`tests/test_lasi_pipeline.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_lasi_pipeline.py#L1040-L1240):

| Test Function | Scenario Tested | Measurement-Defined HTN | EHR Diagnosed HTN | Verdict |
| :--- | :--- | :---: | :---: | :---: |
| `test_measurement_defined_htn_without_ehr_diagnosis` | Patient has measured BP $150/95$ mmHg, but zero records in `conditions.csv`. | **100.0% (1/1)** | **0.0% (0/1)** | **PASS** |
| `test_ehr_diagnosis_without_measurement_threshold` | Patient has `I10` in `conditions.csv`, but measured BP is $122/78$ mmHg and not on medications. | **0.0% (0/1)** | **100.0% (1/1)** | **PASS** |
| `test_antihypertensive_treatment_qualifies_measurement_definition` | Normal BP ($124/78$ mmHg) on Amlodipine vs Normal BP ($120/75$ mmHg) on Paracetamol. | **50.0% (1/2)** | **0.0% (0/2)** | **PASS** |
| `test_missing_bp_not_silently_treated_as_normal` | 1 measured patient ($135/85$ mmHg) and 1 unmeasured patient (no BP rows). | SBP Distribution $N = 1$ | Unmeasured Rate $50\%$ | **PASS** |
| `test_metric_denominators_separated_between_distributions_and_prevalence` | Verifies continuous BP uses $N=235$ denominator, while prevalence uses $N=575$. | Prev $N=575$ ($40.87\%$) | Cont $N=235$ ($156.44$) | **PASS** |

All tests pass deterministically (`pytest tests/test_lasi_pipeline.py` exited code 0).

---

## 6. Denominator Integrity Verification

| Metric ID | Computed Value | Correct Denominator | Value if Wrong Denominator Used | Denominator Status |
| :--- | :---: | :---: | :---: | :---: |
| `lasi_bp_sbp_distribution` | $156.44$ mmHg | $N = 235$ (Measured Pts) | Conflated with $852$ obs if not deduplicated | **VERIFIED CORRECT** |
| `lasi_bp_dbp_distribution` | $96.89$ mmHg | $N = 235$ (Measured Pts) | Conflated with $852$ obs if not deduplicated | **VERIFIED CORRECT** |
| `lasi_prev_measurement_defined_htn_older_adult` | $40.87\%$ ($235/575$) | $N = 575$ (All Older Adults) | $100.0\%$ ($235/235$) if restricted to measured | **VERIFIED CORRECT** |
| `lasi_prev_htn_older_adult` | $40.87\%$ ($235/575$) | $N = 575$ (All Older Adults) | $100.0\%$ ($235/235$) if restricted to measured | **VERIFIED CORRECT** |

---

## 7. Summary

The implementation of hypertension metrics in SYNAPSE Phase 2 is mathematically sound, correctly attributed to distinct source tables, and immune to denominator confusion. However, because blood pressure is captured only for hypertensive individuals, the continuous blood-pressure distribution reflects an outpatient hypertensive cohort (Estimand 2) rather than the general community population (Estimand 1).
