# Root-Cause Analysis: Adult Hypertension Prevalence Discrepancy

**Audit Target:** Adult Essential Hypertension Prevalence (`prev_hypertension_adults`)  
**Empirical Benchmark:** ICMR-INDIAB 2023 National Survey ($30.70\%$, $95\%\text{ CI: } [29.30\%, 32.10\%]$)  
**Reported Synthetic Estimates:**
- Calibrated 5-Seed Monte Carlo ($N=100$): **$36.88\%$**
- Calibrated Single Cohort ($N=500$): **$39.30\%$**
- Multi-Seed Convergence Mean ($N=500$, 10 Seeds): **$35.90\%$**
- Large Cohort Asymptotic Estimate ($N=1000$): **$35.91\%$**

---

## 1. Executive Summary & Root Cause Statement

The synthetic adult hypertension prevalence is **not elevated due to an algorithmic bug or incorrect transition weights**.

The observed elevation from $30.70\%$ to $\sim 35.9\% - 39.3\%$ is the **direct, mathematically exact consequence of evaluating a 2-year longitudinal cumulative period prevalence against a cross-sectional point prevalence survey benchmark**.

### Key Findings
1. **Baseline Sampling is Mathematically Exact:** At $t=0$, baseline sampling yields an expected adult marginal prevalence of **$30.70\%$**, perfectly preserving the ICMR-INDIAB benchmark.
2. **Longitudinal Incident Accumulation:** Over the 24-month observation window (730 days), susceptible disease-free adults face an annual prospective incidence hazard of $\lambda = 0.035$/year ($3.44\%$/year transition probability). Because hypertension is a chronic, non-resolving disease, incident cases accumulate monotonically without remission.
3. **Theoretical 2-Year Period Prevalence:**
   $$\text{Expected Period Prevalence} = 30.70\% + (1 - 0.3070) \times \left[1 - (1 - 0.0344)^2\right] = 30.70\% + 4.68\% = \mathbf{35.38\%}$$
4. **Sampling Variance in Single Runs:** In a single run of $N=500$ (Seed 42), baseline hypertension happened to sample at $34.90\%$ due to binomial dispersion ($+1.7$ standard errors), which combined with $+4.40\%$ incident cases to yield $39.30\%$. When averaged across 10 independent seeds, the synthetic mean converges to **$35.90\%$**, matching the theoretical $35.38\%$ expectation.

---

## 2. Full Calculation Trace Through Simulation Lifecycle

```
[Target Cohort: Adults >= 20]
              │
              ▼
[1. Baseline Condition Sampling (t = 0)]
    ├── Sample T2D Status: P(T2D) = 11.40%
    └── Sample HTN Status Conditioned on T2D:
        ├── If Diabetic:      P(HTN | T2D) = 50.10%
        └── If Non-Diabetic:  P(HTN | no T2D) = 28.20%
        └── Expected Marginal: 0.114 * 0.501 + 0.886 * 0.282 = 30.70%
              │
              ▼
[2. Module Initialization & Incident Separation]
    ├── Baseline-Positive: Routed to ScreeningEncounter (Incident Onset Blocked)
    └── Baseline-Negative: Initialized at Initial -> AgeCheck (Susceptible Pool: 69.30%)
              │
              ▼
[3. Longitudinal Progression (t in [0, 730 days])]
    ├── Susceptible Adults Face Annual Hazard: lambda = 0.035/yr (p = 0.0344/yr)
    ├── Year 0 -> Year 1 Wave: 69.30% * 3.44% = +2.38% Incident Cases
    └── Year 1 -> Year 2 Wave: (69.30% - 2.38%) * 3.44% = +2.30% Incident Cases
    └── Total 2-Year Incident Accumulation: +4.68%
              │
              ▼
[4. Chronic Disease Persistence (No Remission)]
    └── Hypertension is Permanent (Persistence = 1.0, Zero Resolution)
              │
              ▼
[5. Final Export & Evaluation (t = 730 days)]
    ├── Numerator: All Adult Patients with "I10" in conditions.csv
    ├── Denominator: All Patients with Age >= 20 in patients.csv
    └── Evaluated Metric = Baseline (30.70%) + 2-Year Incident (4.68%) = 35.38% (Expected)
```

---

## 3. Mathematical Proof of Baseline Marginal Invariance

The ICMR-INDIAB 2023 study establishes two empirical statistics:
1. Adult Hypertension Marginal Prevalence: $P(\text{HTN}) = 30.70\%$
2. Adult Type 2 Diabetes Marginal Prevalence: $P(\text{T2D}) = 11.40\%$
3. Comorbid Hypertension in Diabetic Patients: $P(\text{HTN}\mid\text{T2D}) = 50.10\%$

By the Law of Total Probability:
$$P(\text{HTN}) = P(\text{HTN}\mid\text{T2D}) \cdot P(\text{T2D}) + P(\text{HTN}\mid\text{no T2D}) \cdot P(\text{no T2D})$$

Substituting the empirical quantities:
$$0.3070 = (0.5010 \times 0.1140) + P(\text{HTN}\mid\text{no T2D}) \times (1 - 0.1140)$$
$$0.3070 = 0.057114 + 0.8860 \times P(\text{HTN}\mid\text{no T2D})$$
$$0.8860 \times P(\text{HTN}\mid\text{no T2D}) = 0.3070 - 0.057114 = 0.249886$$
$$P(\text{HTN}\mid\text{no T2D}) = \frac{0.249886}{0.8860} = \mathbf{0.282038 \quad (28.20\%)}$$

In `synapse_simulator/datagen/patient_generator.py` (lines 117–135), the conditional sampling logic is implemented as:
```python
cond_rate = 50.1 if has_t2d else 28.2 if age >= 20 else 0.0
```
Therefore, the expected baseline marginal prevalence is:
$$E[P(\text{HTN})] = (0.114 \times 0.501) + (0.886 \times 0.282) = 0.057114 + 0.249852 = \mathbf{30.6966\% \approx 30.70\%}$$
The baseline sampling preserves the intended marginal prevalence mathematically.

---

## 4. Empirical Verification Directly from Exported CSV Artifacts

We recomputed the marginal prevalence and conditional probabilities directly from the exported CSV records in `data/evaluation/test_calibrated_500/`.

### 4.1 Cohort Breakdown ($N=500$, Seed 42)
- Total Patients: **500**
- Eligible Adults (Age $\ge 20$): **341** ($68.20\%$)
- Pediatric Patients (Age $< 20$): **159** ($31.80\%$)

### 4.2 Baseline vs. Incident Separation via Encounter Timestamps
By tracking encounter start times ($t_{\text{enc}}$), diagnoses occurring during the initial screening window ($t_{\text{enc}} \le 2024\text{-}02\text{-}01$) were separated from incident diagnoses ($t_{\text{enc}} > 2024\text{-}02\text{-}01$):

| Cohort Stratum | Eligible Denominator | HTN Cases | Prevalence / Attack Rate | Theoretical Expectation |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline Diagnosed (Jan 2024)** | 341 adults | 119 | **$34.90\%$** | $30.70\% \pm 4.9\%$ (95% CI) |
| **Incident Diagnosed (Apr 2024 – May 2025)** | 341 adults | 15 | **$4.40\%$** | $4.68\%$ |
| **Total Cumulative 2-Year Cohort** | 341 adults | 134 | **$39.30\%$** | $35.38\%$ |

### 4.3 Baseline Comorbidity Cross-Tabulation ($t=0$)
- Diabetic Adults at Baseline: **27** ($7.92\%$)
- Non-Diabetic Adults at Baseline: **314** ($92.08\%$)
- Comorbid Adults (HTN $+$ T2D at Baseline): **15**
- Observed $P(\text{HTN}\mid\text{T2D}) = 15 / 27 = \mathbf{55.56\%}$ (Target: $50.10\%$)
- Observed $P(\text{HTN}\mid\text{no T2D}) = 104 / 314 = \mathbf{33.12\%}$ (Target: $28.20\%$)
- Observed Odds Ratio:
  $$\text{OR} = \frac{15 \times 210}{104 \times 12} = \frac{3150}{1248} = \mathbf{2.52} \quad (\text{Target: } 2.56)$$

### 4.4 Trace of Incident Cases Across the 24-Month Timeline
All 15 incident hypertension cases occurred in two distinct annual waves, perfectly reflecting the annual loop in `hypertension.yaml`:
- **Wave 1 (Year 0 -> Day 110, April 2024):** 5 incident cases diagnosed after `AsymptomaticDelay` (90 days).
  - `pat-a13e64f8` (2024-04-23), `pat-b3adcad6` (2024-04-24), `pat-616e045a` (2024-04-24), `pat-f43ca8fc` (2024-04-26), `pat-e88e2525` (2024-04-28).
- **Wave 2 (Year 1 -> Day 490, May 2025):** 10 incident cases diagnosed after `NormotensiveDelay` (365 days) + `AsymptomaticDelay` (90 days).
  - `pat-423b57f6`, `pat-5013612b`, `pat-a7ff46ff`, `pat-3a0f6e19`, `pat-f9e8c854`, `pat-815f2e46`, `pat-7f35a8e8`, `pat-83207b43`, `pat-9ca7084f`, `pat-1484180f`.
- **Annual Incidence Rate Observed:**
  $$I = \frac{15\text{ cases}}{222\text{ susceptible adults} \times 2.0\text{ years}} = \mathbf{3.38\% \text{ per person-year}}$$
This aligns with the configured annual transition weight of **$3.44\%$** ($0.0344$).

---

## 5. Investigation of Alternative Explanations

1. **Was repeated onset prevention bypassed?**  
   **No.** `ClinicalModuleRunner.initialize_patient` sets latent condition state for baseline-positive patients and places them in `ScreeningEncounter`. In `test_baseline_and_incident_separation_in_runner`, stepping a baseline-positive patient forward 104 timesteps (2 years) emits strictly 0 second onset actions.
2. **Did delayed entry change the prevalence?**  
   **No.** All patients in the evaluation experiment enter at `obs_start` (`2024-01-01`). There is no staggered open-cohort entry.
3. **Did condition resolution change the prevalence?**  
   **No.** In `hypertension.yaml`, hypertension is modeled as chronic and irreversible (no `ConditionEnd` state). Therefore, cases never resolve, causing cumulative period prevalence to strictly increase over time.
4. **Is the incidence probability too high?**  
   **No.** The annual incidence hazard $\lambda = 0.035$/year is derived from Indian prospective cohort studies (CURES, Prabhakaran et al., JAHA 2017). Lowering it would violate empirical incidence literature.

---

## 6. Controlled Correction and Resolution

### Definitional Clarification
The discrepancy is an artifact of **comparing a 2-year period prevalence against a cross-sectional point prevalence survey**:
- **ICMR-INDIAB 2023:** Point prevalence ($t = 0$) = **$30.70\%$**.
- **SYNAPSE Evaluation (24 Months):** Cumulative period prevalence ($t \in [0, 2\text{ yrs}]$) = **$35.38\%$ (Theoretical)** / **$35.90\%$ (Empirical)**.

### Implemented Model & Evaluator Corrections
1. **Preserve Incidence Hazards:** Transition probabilities in `hypertension.yaml` ($p = 0.0344$) are empirically grounded and must NOT be reduced.
2. **Enhanced Evaluator Reporting:** `DatasetEvaluator` has been updated to report both:
   - **Baseline Point Prevalence ($t=0$):** Isolated within `acceptance_threshold["baseline_point_prevalence_pct"]`, evaluated against the $30.70\%$ survey benchmark.
   - **Cumulative Period Prevalence ($t=2$ yrs):** Reported under `prev_hypertension_adults` with documented explanation of 2-year prospective accumulation.
