# SYNAPSE Phase 2 — Discrepancy Analysis

## 1. Executive Summary

The baseline evaluation of the uncalibrated SYNAPSE Phase 2 simulation identified three major quantitative discrepancies between synthetic outputs and empirical reference benchmarks:
1. **Essential Hypertension (`I10`):** Overestimated by **+12.26%** (Synthetic 42.96% vs. Reference 30.70%).
2. **Type 2 Diabetes Mellitus (`E11.9`):** Overestimated by **+14.00%** (Synthetic 25.40% vs. Reference 11.40%).
3. **Acute Upper Respiratory Infection (`J06.9`):** Overestimated by **+65.50%** (Synthetic 74.00% vs. Reference 8.50%).

Conversely, demographic distributions and the comorbidity relationship ($P(\text{HTN}\mid\text{T2D}) = 49.11\%$ vs. $50.10\%$) demonstrated remarkable fidelity.

In accordance with Mandate 11, this document investigates the structural, mathematical, and conceptual root causes of each discrepancy **prior to any recalibration**.

---

## 2. Root Cause Analysis by Condition

### 2.1 Essential Hypertension Discrepancy (+12.26%)
- **Empirical Reference:** Weighted national prevalence among Indian adults aged $\ge 20$ is **30.7%** (ICMR-INDIAB, Lancet 2023).
- **Synthetic Monte Carlo Mean:** **42.96%** (SE = 1.60%, range 39.5%–47.8%).

#### Identified Mechanisms:
1. **Prevalence vs. Incidence Superposition:**
   - In `PatientProfileGenerator`, baseline chronic conditions are assigned at generation time using `has_condition_at_baseline()`, seeding approximately 30.7% of eligible adults with baseline hypertension.
   - Concurrently, the longitudinal generic module `hypertension.yaml` evaluates all adults aged $\ge 25$ with an additional transition probability:
     ```yaml
     AgeCheck:
       guard_condition: "age >= 25"
       distributed_transition:
         - to: "HypertensionOnset"
           weight: 0.30
     ```
   - Consequently, uninfected patients have a 30% chance of developing new-onset hypertension during the observation period.
   - **Mathematical Effect:** The cohort accumulates both initial baseline prevalence ($P_0 \approx 0.307$) and longitudinal new-onset incidence ($(1 - P_0) \times I$), yielding a 2-year cumulative period prevalence:
     $$P_{\text{cumulative}} \approx 0.307 + (1 - 0.307) \times 0.20 \approx 0.445 \text{ (44.5\%)}$$
   - **Root Cause:** Conflation of cross-sectional baseline prevalence with dynamic longitudinal incidence rates.

---

### 2.2 Type 2 Diabetes Discrepancy (+14.00%)
- **Empirical Reference:** Weighted national adult prevalence is **11.4%** (ICMR-INDIAB, Lancet 2023).
- **Synthetic Monte Carlo Mean:** **25.40%** (SE = 2.14%, range 19.1%–31.8%).

#### Identified Mechanisms:
1. **Grossly Overestimated Annual Incidence Rate:**
   - Real-world epidemiological data from the ICMR-INDIAB longitudinal cohort indicates that the annual incidence rate of progression from normoglycemia to diabetes in Indian adults is approximately **1.0%–1.8% per year**.
   - In `diabetes_t2.yaml`, the state machine applies a **15% transition weight** to `PrediabetesOnset`, which subsequently progresses within 180 days to `DiabetesOnset`:
     ```yaml
     T2DAgeCheck:
       guard_condition: "age >= 25"
       distributed_transition:
         - to: "PrediabetesOnset"
           weight: 0.15
     ```
   - Over a 2-year simulation with cyclic re-evaluation after 365 days (`EuglycemicDelay`), roughly 25% of all adults transition to diabetes.
   - **Root Cause:** Hardcoded state-machine transition probabilities were parameterized using uncalibrated initial assumptions rather than empirical annual incidence rates.

---

### 2.3 Acute Upper Respiratory Tract Infection Discrepancy (+65.50%)
- **Empirical Reference:** National Health Portal India baseline is **8.5%** period prevalence.
- **Synthetic Monte Carlo Mean:** **74.00%** (SE = 1.18%, range 71.0%–78.0%).

#### Identified Mechanisms:
1. **Point Prevalence vs. 2-Year Longitudinal Cumulative Attack Rate:**
   - In national health surveys (e.g. NHP, NSSO), acute respiratory illness prevalence is measured using a **short recall window (typically 14 to 30 days)**. At any given moment, ~8.5% of the population has an active respiratory episode.
   - In `urti.yaml`, the infection state machine executes every 90 days (`HealthyIntervalDelay`):
     ```yaml
     states:
       Initial:
         distributed_transition:
           - to: "AcuteInfectionOnset"
             weight: 0.15
           - to: "HealthyIntervalDelay"
             weight: 0.85
     ```
   - In a 2-year simulation (730 days), each patient experiences approximately eight 90-day cycles.
   - The probability that a patient experiences **at least one** infection episode over 2 years is:
     $$P(\ge 1 \text{ episode in 2 years}) = 1 - (1 - 0.15)^8 = 1 - (0.85)^8 = 1 - 0.2725 = 72.75\%$$
   - **Root Cause:** A conceptual measurement incompatibility: `conditions.csv` aggregates all historical lifetime diagnoses over the entire 2-year simulation window, measuring **2-year cumulative attack rate (74%)**, whereas the survey benchmark represents **cross-sectional point prevalence (8.5%)**.

---

## 3. Comorbidity Fidelity Analysis

Despite the discrepancies in individual marginal prevalences, the **comorbidity conditional prevalence** demonstrated exceptional fidelity:
- **Synthetic Mean $P(\text{HTN}\mid\text{T2D})$:** **49.11%** (SE = 5.10%).
- **Reference Benchmark:** **50.10%** (ICMR-INDIAB 2023).
- **Systematic Bias:** **-0.99%** (Absolute difference less than 1.0 percentage point).

### Explanation:
In SYNAPSE Phase 2, both diabetes and hypertension module entry guards require `age >= 25` and share age-dependent physiological covariates. Because both conditions disproportionately develop in middle-aged and elderly adults, their conditional co-occurrence naturally mirrors real-world metabolic clustering.

---

## 4. Summary of Discrepancy Classifications

| Dimension | Discrepancy Type | Underlying Cause | Remediation Strategy |
| :--- | :--- | :--- | :--- |
| **Hypertension** | Superposition | Pre-seeding baseline chronic status AND running incidence module | Either initialize baseline cases as already in `MaintenanceDelay`, or calibrate module entry weight to match true empirical annual incidence (~3–4%/yr). |
| **Diabetes** | Rate Calibration | 15% annual transition weight exceeds true incidence (1.2%/yr) | Recalibrate `PrediabetesOnset` transition weight from 0.15 to ~0.02. |
| **URTI** | Denominator/Time Scope | Comparing 2-year cumulative attack rate (74%) to 14-day point prevalence (8.5%) | Formalize evaluation metric definition: either evaluate active infections at simulation end date (point prevalence) or compare cumulative attack rate against multi-year attack rate benchmarks. |
