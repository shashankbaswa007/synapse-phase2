# Estimand Definition, Survey Weighting, and Uncertainty Audit

**Project:** SYNAPSE Phase 2 Synthetic Healthcare Simulation  
**Audit Focus:** Formal Specification of Estimands A through E, Complex Survey Variance Estimation, and Deterministic PRNG  
**Target Reference Standard:** Longitudinal Ageing Study in India (LASI) Wave 1 Evaluation Framework  
**Evaluation Gate:** `REFERENCE_DATA_PENDING`  
**Date of Audit:** October 2026  

---

## 1. Executive Summary

This audit establishes the formal mathematical specifications, statistical properties, and inferential boundaries for all five evaluation estimands in SYNAPSE Phase 2. 

### Key Findings:
1. **Resolution of Ambiguities in Codebase:** The codebase contained naming collisions where two distinct metrics were labeled `ESTIMAND_C` (EHR Diagnosis vs Community Survey) and two were labeled `ESTIMAND_D` (Facility Attenders vs Longitudinal Trajectory). We establish a formal taxonomy: **A, B, C1, C2, D1, D2, E**.
2. **Strict Invariant Adherence:**
   - EHR diagnosis is NOT treated as equivalent to measurement-defined disease.
   - Missing clinical blood pressure is NOT interpreted as normotension.
   - Unassessable status rate ($59.13\%$) is formally isolated under Estimand E and never interpreted as disease prevalence.
   - Community prevalence ($41.71\%$) does NOT mix incompatible clinical visit criteria.
3. **Complex Survey Variance Limitations Documented:** Kish's effective sample size ($n_{\text{eff}} = (\sum w_i)^2 / \sum w_i^2$) accounts strictly for variance inflation from unequal weighting ($\text{DEFF}_w$). It does **NOT** account for cluster correlation ($\text{DEFF}_c$), stratification, or primary sampling units (PSUs). It is an unequal-weighting heuristic, not a substitute for full Taylor-series linearization or replication-based complex-survey variance estimation.
4. **Deterministic PRNG Verified:** The per-patient PRNG uses isolated stream derivations. Python's `random.Random(str)` hashes strings using `sha512` internally, guaranteeing zero dependency on `PYTHONHASHSEED` or process order.

---

## 2. Canonical Specification of Evaluation Estimands

```
                                  [All Older Adults (N = 575)]
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
    [Clinical Pathway (EHR)]                                      [Community Pathway (Survey)]
                 │                                                             │
   ┌─────────────┴─────────────┐                                               ▼
   ▼                           ▼                                   [Estimand C2: Community HTN]
[Assessable (N = 235)]   [Unassessable (N = 340)]                     (Survey SBP/DBP/Rx: 41.71%)
   │                           │
   ├── [Estimand B: 100.0%]    └── [Estimand E: 59.13%]
   │   (Clinic Screened HTN)       (Missing Clinical Status)
   │
   ├── [Estimand A: Index BP]
   │   (Mean SBP 156.4 mmHg)
   │
   ├── [Estimand C1: EHR Dx]
   │   (I10 in Record: 40.87%)
   │
   ├── [Estimand D1: Attenders]
   │   (HTN in OPD Visitors: 48.45%)
   │
   └── [Estimand D2: Trajectory]
       (Delta SBP: -16.92 mmHg; UNVERIFIED)
```

---

### Estimand A: Cross-Sectional Continuous Blood Pressure Distribution

- **Mathematical Definition:** Univariate probability distribution of patient-level index blood pressure:
  $$F_Y(y) = P(Y \le y), \quad Y \in \{\text{SBP}, \text{DBP}, \text{Pulse Pressure}\}$$
- **Target Population:** Older adults (age $\ge 45$) with at least one observed blood pressure measurement.
- **Unit of Analysis:** Individual patient (exactly one index measurement per patient).
- **Index Selection Rule:** Earliest chronologically recorded blood pressure encounter per patient.
- **Numerator & Denominator:** Continuous distributional moments (Mean, SD, Median, IQR, Quantiles $Q_{0.10}, Q_{0.25}, Q_{0.50}, Q_{0.75}, Q_{0.90}$); Clinical $N = 235$, Community $N = 561$.
- **Handling of Missing Data:** Complete-case analysis. Missing patients ($N = 340$ clinical, $N = 14$ community) are excluded from the distribution rather than imputed.
- **Medication Inclusion Rule:** All patients with valid index BP are included, irrespective of whether they are on medication.
- **Survey Weighting:** Reference data uses survey-weighted mean $\bar{y}_w = \frac{\sum w_i y_i}{\sum w_i}$ and weighted quantiles. Synthetic cohort uses unweighted empirical distribution ($w_i = 1.0$).
- **Inference & Hypothesis Testing:** Two-sample Kolmogorov-Smirnov test and 1-D Wasserstein distance against reference data. Sample size gate: $N \ge 30$ in both samples.
- **Interpretation & Limitations:** Clinical Estimand A reflects symptomatic/screening outpatient presentation (Mean SBP 156.44 mmHg, DBP 96.89 mmHg). Community Estimand A reflects general population vitals (Mean SBP 127.60 mmHg, DBP 79.81 mmHg). Directly comparing clinical Estimand A to LASI community survey data is an invalid design confounder.

---

### Estimand B: Measurement-Defined Hypertension Prevalence Among Assessable Patients

- **Mathematical Definition:**
  $$\theta_B = P(\text{HTN} \mid \text{Assessable}) = \frac{\sum_{i=1}^{N_{\text{assessable}}} \mathbf{1}(\text{Index SBP}_i \ge 140 \lor \text{Index DBP}_i \ge 90 \lor \text{Active Rx}_i = 1)}{N_{\text{assessable}}}$$
- **Target Population:** Assessable older adults (individuals with observed clinical BP or active antihypertensive medication).
- **Unit of Analysis:** Individual assessable patient ($N_{\text{assessable}} = 235$).
- **Numerator:** Assessable older adults meeting clinical HTN criteria ($n = 235$).
- **Denominator:** Total assessable older adults ($N = 235$).
- **Current Value:** **100.00%** (95% Wilson Score CI: [98.40%, 100.00%]).
- **Handling of Missing Data:** Restricted strictly to assessable patients. Unmeasured individuals ($N = 340$) are NOT assumed normotensive; they are routed to Estimand E.
- **Medication Inclusion Rule:** Patients with active prescriptions for qualifying antihypertensives (Amlodipine, Telmisartan, Enalapril, Losartan, Atenolol, Metoprolol, Hydrochlorothiazide) are classified as hypertensive even if their measured blood pressure is controlled ($< 140/90$ mmHg).
- **Survey Weighting:** Unweighted for synthetic data; design-weighted proportion for reference data.
- **Confidence Interval Method:** Wilson score interval for synthetic; design-adjusted Wald interval for reference.
- **Interpretation & Limitations:** **Estimand B does NOT estimate population prevalence.** Because routine screening is absent for non-diseased clinic attenders, the assessable denominator is 100% composed of patients from `hypertension.yaml`. Estimand B reflects diagnostic yield among clinic-screened individuals.

---

### Estimand C1: EHR-Recorded Hypertension Diagnosis Prevalence

- **Mathematical Definition:**
  $$\theta_{C1} = \frac{\sum_{i=1}^{N_{\text{older}}} \mathbf{1}(\text{ICD-10 I10 in EHR}_i)}{N_{\text{older}}}$$
- **Target Population:** All synthetic older adults (age $\ge 45$, $N_{\text{older}} = 575$).
- **Unit of Analysis:** Individual patient.
- **Numerator:** Older adults with documented condition code `I10` ($n = 235$).
- **Denominator:** All older adults ($N = 575$).
- **Current Value:** **40.87%** (95% Wilson Score CI: [36.90%, 44.97%]).
- **Handling of Missing Data:** Patients without an `I10` diagnosis in `conditions.csv` are classified as non-diagnosed (negative for this specific estimand).
- **Medication Inclusion Rule:** Medication records do not affect this estimand; requires explicit diagnostic code.
- **Survey Weighting:** Unweighted synthetic.
- **Confidence Interval Method:** Wilson score interval.
- **Interpretation & Limitations:** Reflects medical record documentation rate. In real-world health systems, this measures clinical awareness and diagnosis, which significantly underestimates true community prevalence due to undiagnosed individuals.

---

### Estimand C2: Community Health Assessment Hypertension Prevalence

- **Mathematical Definition:**
  $$\theta_{C2} = \frac{\sum_{i=1}^{N_{\text{comm}}} \mathbf{1}(\text{Survey SBP}_i \ge 140 \lor \text{Survey DBP}_i \ge 90 \lor \text{Active Rx}_i = 1)}{N_{\text{comm}}}$$
- **Target Population:** Living community-dwelling older adults at survey date ($t = 180\text{ days}$, $N_{\text{comm}} = 561$).
- **Unit of Analysis:** Individual surveyed respondent.
- **Numerator:** Community respondents with measured SBP $\ge 140$, DBP $\ge 90$, or active antihypertensive medication ($n = 234$: 96 treated uncontrolled + 137 treated controlled + 1 untreated elevated).
- **Denominator:** Total completed community assessments ($N = 561$).
- **Current Value:** **41.71%** (95% Wilson Score CI: [37.69%, 45.86%]).
- **Handling of Missing Data:** Individuals who died prior to survey ($N = 14$) are excluded from denominator. Refusals/unassessable cases are tracked separately. Missing values are not classified as normotensive.
- **Medication Inclusion Rule:** Active treatment qualifies an individual as hypertensive regardless of measured BP control.
- **Survey Weighting:** Inverse probability of selection weight ($w_i = 1 / \text{sampling\_rate} = 1.0$).
- **Confidence Interval Method:** Wilson score interval for synthetic; complex survey-weighted CI for reference.
- **Interpretation & Limitations:** **This is the primary scientific counterpart for LASI Wave 1 population evaluation.** It captures both diagnosed and undiagnosed hypertensives in the general household setting without hospital selection bias.

---

### Estimand D1: Hypertension Prevalence Among Clinical Facility Attenders

- **Mathematical Definition:**
  $$\theta_{D1} = \frac{\sum_{i \in \text{Attenders}} \mathbf{1}(\text{Diagnosed HTN}_i)}{N_{\text{attenders}}}$$
- **Target Population:** Older adults who attended at least one clinical facility encounter during the 720-day horizon ($N_{\text{attenders}} = 485$).
- **Unit of Analysis:** Individual patient attending healthcare facilities.
- **Numerator:** Facility attenders diagnosed with hypertension ($n = 235$).
- **Denominator:** Total older adults with $\ge 1$ clinical encounter ($N = 485$).
- **Current Value:** **48.45%** (95% Wilson Score CI: [44.02%, 52.92%]).
- **Handling of Missing Data:** Older adults with zero encounters ($N = 90$) are excluded from denominator.
- **Interpretation & Limitations:** Quantifies Berkson's bias (healthcare-seeking enrichment). The prevalence among clinical attenders ($48.45\%$) is significantly higher than general population prevalence ($40.87\%$), reflecting that individuals with chronic diseases visit healthcare facilities more frequently.

---

### Estimand D2: Longitudinal Blood Pressure Trajectory and Treatment Response

- **Mathematical Definition:**
  $$\Delta_{\text{SBP}} = \frac{1}{N_{\text{multi}}} \sum_{i=1}^{N_{\text{multi}}} (\text{SBP}_{i, \text{final}} - \text{SBP}_{i, \text{initial}})$$
- **Target Population:** Patients with repeated longitudinal blood pressure observations ($\ge 2$ clinical visits, $N_{\text{multi}} = 235$).
- **Current Value:** Mean $\Delta_{\text{SBP}} = -16.92$ mmHg.
- **Evaluation Status:** **STRICTLY `UNVERIFIED`**.
- **Rationale for Unverified Status:** LASI Wave 1 is a cross-sectional survey. A single cross-sectional survey cannot validate multi-year longitudinal treatment response trajectories. Longitudinal validation requires multi-wave data (e.g. LASI Wave 2).

---

### Estimand E: Unassessable / Missing Clinical Blood Pressure Status Rate

- **Mathematical Definition:**
  $$\theta_E = \frac{N_{\text{older}} - N_{\text{assessable}}}{N_{\text{older}}} = \frac{340}{575}$$
- **Target Population:** All synthetic older adults ($N = 575$).
- **Unit of Analysis:** Individual patient.
- **Numerator:** Older adults with unobserved clinical blood pressure and no antihypertensive prescriptions ($n = 340$).
- **Denominator:** All older adults ($N = 575$).
- **Current Value:** **59.13%** (95% Wilson Score CI: [55.08%, 63.07%]).
- **Partitioning of Reasons:**
  - `VISITED_CLINIC_NO_BP_ORDERED`: $250 / 340$ ($73.53\%$) — attended clinic for other reasons (e.g. diabetes) but BP was never taken.
  - `NO_CLINICAL_VISITS`: $90 / 340$ ($26.47\%$) — did not attend any clinic during observation window.
- **Interpretation & Limitations:** Formally prevents false-negative misclassification. In EHR studies, unmeasured patients are frequently misclassified as healthy, introducing downward bias in disease prevalence. Estimand E must NEVER be conflated with disease prevalence or normotension.

---

## 3. Audit of Weighting and Complex Survey Uncertainty

### 3.1 Kish's Effective Sample Size Evaluation

In `synapse_simulator/evaluation/metrics.py:500-547`, unequal weighting is adjusted via Kish's effective sample size:
$$n_{\text{eff}} = \frac{(\sum_{i=1}^n w_i)^2}{\sum_{i=1}^n w_i^2}$$
$$\text{DEFF}_w = \frac{n}{n_{\text{eff}}} = 1 + \text{CV}(w)^2$$
$$\text{SE}_{\text{weighted}} = \sqrt{\frac{p_w(1 - p_w)}{n_{\text{eff}}}}$$

### 3.2 Critical Methodological Boundary: Kish Effective Sample Size vs. Complex Survey Variance

> [!WARNING]
> **Kish's effective sample size is NOT a substitute for full complex-survey variance estimation.**

1. **What Kish's Formula Captures:** Kish's formula accounts *exclusively* for the variance inflation resulting from unequal selection probabilities ($\text{DEFF}_w$).
2. **What Kish's Formula Omits:**
   - **Clustering / Intra-Cluster Correlation ($\text{DEFF}_c$):** In multi-stage surveys like LASI Wave 1, individuals sampled from the same Primary Sampling Unit (PSU; village or urban ward) share environmental, socioeconomic, and dietary factors. Cluster variance inflation is defined as:
     $$\text{DEFF}_c = 1 + (\bar{m} - 1)\rho$$
     where $\bar{m}$ is the average cluster size and $\rho$ is the intracluster correlation coefficient. Kish's $n_{\text{eff}}$ completely ignores $\text{DEFF}_c$.
   - **Stratification Efficiency ($\text{DEFF}_s$):** Explicit stratification across states and urban/rural domains reduces sampling variance ($\text{DEFF}_s < 1.0$).
   - **Finite Population Correction (FPC):** Not accounted for in the Wald approximation.
3. **Missing Complex Survey Design Metadata:** The synthetic dataset currently does not emit PSU identifiers (`psu_id`) or stratum identifiers (`stratum_id`).
4. **Governing Recommendation:** When evaluating against genuine LASI Wave 1 microdata, reference variance must be computed using complex-survey Taylor series linearization or balanced repeated replication (BRR) survey procedures using the official PSU and strata weights, rather than relying solely on $\text{DEFF}_w$.

---

## 4. Deterministic PRNG Reproducibility Audit

### 4.1 String Seeding vs. Built-in `hash()`

Requirement 7 mandated verifying whether Python's built-in `hash()` was used in per-patient seeding:
- **Audit Finding:** Python's built-in `hash()` is **NOT** used anywhere in `CommunityAssessmentGenerator`.
- **Implementation in Code:**
  ```python
  pat_rng = random.Random(f"{self.base_seed}_comm_eval_{pid}")
  ```
- **CPython Internal Mechanism:** In CPython (Python 3.2+), when `random.Random(s)` is called with a `str` argument, CPython internally encodes the string to UTF-8 and passes it to `hashlib.sha512(s.encode()).digest()`. It does **not** invoke `sys.hash_randomization` or `hash()`.
- **Multi-Process Verification:** Verified via automated sub-processes that setting `PYTHONHASHSEED=0` vs `PYTHONHASHSEED=999999` yields bit-for-bit identical blood pressure values across processes.

### 4.2 Order Independence and Seed Sensitivity

- **Order Independence:** Tested by shuffling patient dictionary insertion order and adding unrelated patients. Each patient's pseudorandom stream depends exclusively on `(base_seed, pid)` and is strictly independent of cohort processing order.
- **Seed Sensitivity:** Changing `base_seed` from $42$ to $43$ alters individual blood pressure values across all patients while preserving bounded physiological properties ($PP \ge 20$ mmHg, $SBP > DBP$).

---

## 5. Compliance with Non-Negotiable Governance Constraints

1. **Preservation of Validation Gate:** The validation gate is maintained strictly as **`REFERENCE_DATA_PENDING`**.
2. **No Fixture Value Copying:** Parameter bounds in `community_assessment.py` (110–135, 120–150, 145–168 mmHg) were derived from clinical knowledge base ranges and module specifications, not from fixture test expectations.
3. **Zero Unsupported Transition Modifications:** Discrete-event simulation transitions in `hypertension.yaml` were left unmodified.
4. **All Software Tests Passing:** The complete test suite of 223 tests passes cleanly.
