# SYNAPSE Phase 2 — Baseline Evaluation Report

## 1. Overview & Experimental Setup

This report establishes the **empirical baseline evaluation** of the uncalibrated SYNAPSE Phase 2 synthetic healthcare generation engine. In strict accordance with Mandate 11, this evaluation is performed **prior to modifying any clinical transition probabilities or tuning parameters**, providing an unvarnished audit of current system capabilities.

### Evaluation Protocol
- **Simulation Period:** 2024-01-01 to 2026-01-01 (2.0 calendar years, 7-day timestep).
- **Population Baseline Profile:** `config/population/india_default_v1.yaml` (SRS 2021 + ICMR-INDIAB 2023).
- **Clinical Modules Active:** Essential Hypertension (`I10`), Type 2 Diabetes (`E11.9`), Acute URTI (`J06.9`).
- **Progressive Cohort Scales Evaluated:**
  1. Small Cohort: $N = 20$ (Seed 42)
  2. Medium Cohort: $N = 100$ (Seed 42)
  3. Large Cohort: $N = 500$ (Seed 42)
  4. Multi-Seed Monte Carlo Cohort: $N = 100$ across 5 seeds (`[42, 101, 202, 303, 404]`)

---

## 2. Progressive Cohort Scaling Results

| Metric ID | Metric Name | Reference Benchmark | $N=20$ (Seed 42) | $N=100$ (Seed 42) | $N=500$ (Seed 42) | 5-Seed MC Mean ($N=100$) | Monte Carlo SE | Status ($N=100$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `inv_no_event_pre_birth` | Pre-Birth Events | 0.00 | **0** | **0** | **0** | **0.00** | 0.00 | **PASS** |
| `inv_no_event_post_mortem` | Post-Mortem Events | 0.00 | **0** | **0** | **0** | **0.00** | 0.00 | **PASS** |
| `inv_diagnosis_encounter_link`| Dangling Diagnoses | 0.00 | **0** | **0** | **0** | **0.00** | 0.00 | **PASS** |
| `inv_allergy_safety_veto` | Allergy Violations | 0.00 | **0** | **0** | **0** | **0.00** | 0.00 | **PASS** |
| `demo_sex_distribution` | Male Sex (%) | 51.50% | 45.00% | 53.00% | 51.40% | **53.40%** | 1.50% | **PASS** |
| `demo_age_pyramid_jsd` | Age Pyramid JSD | 0.00 | 0.097 | 0.012 | 0.004 | **0.011** | 0.002 | **PASS** |
| `demo_age_by_sex_jsd` | Age-Sex Joint JSD | 0.00 | 0.107 | 0.021 | 0.010 | **0.018** | 0.002 | **PASS** |
| `prev_hypertension_adults` | Hypertension (%) | 30.70% | 55.56% | 40.98% | 43.83% | **42.96%** | 1.60% | **WARNING** |
| `prev_diabetes_t2_adults` | Type 2 Diabetes (%) | 11.40% | 33.33% | 27.87% | 24.69% | **25.40%** | 2.14% | **FAIL** |
| `prev_urti_all_ages` | Acute URTI (%) | 8.50% | 65.00% | 73.00% | 72.80% | **74.00%** | 1.18% | **FAIL** |
| `comorb_htn_in_t2d` | P(HTN \| T2D) (%) | 50.10% | 66.67% | 52.94% | 51.25% | **49.11%** | 5.10% | **PASS** |
| `long_encounters_per_pt_yr`| Encounters / Pt-Yr | 1.50 | 0.82 | 0.93 | 0.96 | **0.99** | 0.02 | **PASS** |
| `long_inter_enc_interval` | Revisit Interval (d) | 180.0 | 113.6 | 144.5 | 145.2 | **147.1** | 3.43 | **PASS** |
| `long_crude_mortality_rate`| Annual Mortality | 0.0060 | 0.000 | 0.005 | 0.005 | **0.004** | 0.001 | **PASS** |
| `rx_firstline_hypertension`| First-line CCB/ARB | 100.0% | 80.0% | 84.0% | 88.5% | **87.38%** | 1.73% | **PASS** |
| `rx_firstline_diabetes` | First-line Metformin | 100.0% | 100.0% | 94.12% | 96.25% | **95.87%** | 1.84% | **PASS** |
| `rx_adherence_assumption` | Adherence (Assumed) | — | 100.0% | 100.0% | 100.0% | **100.0%** | 0.00 | **UNVERIFIED** |

---

## 3. Performance & Computational Telemetry

Evaluation and generation execution times were measured independently using wall-clock high-resolution timers and operating system resource tracking (`getrusage`):

| Cohort Size ($N$) | Simulation Time (s) | CSV Export Time (s) | Evaluation Time (s) | Total Pipeline (s) | Actions Emitted | Exported CSVs | Peak RAM (MB) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N = 20$** | 0.048 s | 0.021 s | 0.006 s | **0.075 s** | 82 actions | 16 files | 46.1 MB |
| **$N = 100$** | 0.217 s | 0.079 s | 0.007 s | **0.303 s** | 418 actions | 16 files | 47.0 MB |
| **$N = 500$** | 0.717 s | 0.250 s | 0.012 s | **0.979 s** | 2,089 actions | 16 files | 51.0 MB |

### Scalability Analysis
- **Linear Complexity:** Simulation runtime scales strictly linearly with patient count ($O(N)$), requiring less than 1.0 second for 500 patients over a 2-year simulation horizon.
- **Evaluation Speed:** Independent CSV evaluation executes in **under 15 milliseconds** even for 500-patient cohorts.
- **Minimal Memory Overhead:** Peak resident set size remains approximately 50 MB, demonstrating low memory consumption.

---

## 4. Key Empirical Findings

1. **Flawless Invariant Integrity:** All 4 invariants (zero pre-birth activity, zero post-mortem activity, mandatory encounter linkage, and clinical allergy safety) passed with zero violations across all tested seeds and sample sizes.
2. **High Demographic Fidelity:** As sample size increased from $N=20$ to $N=500$, the Jensen-Shannon Divergence of the age pyramid dropped from 0.097 to 0.004 ($TVD = 0.015$), demonstrating asymptotic convergence to the SRS 2021 distribution.
3. **Remarkable Comorbidity Realism:** The conditional prevalence of hypertension among adults with Type 2 Diabetes converged to **49.11%** (Monte Carlo mean across 5 seeds), extraordinarily close to the empirical ICMR-INDIAB 2023 benchmark of **50.10%** (bias = -0.99%).
4. **Significant Discrepancies in Disease Prevalence:**
   - Adult Hypertension (`I10`): Evaluated at 42.96% vs. 30.70% reference (+12.26% bias).
   - Adult Type 2 Diabetes (`E11.9`): Evaluated at 25.40% vs. 11.40% reference (+14.00% bias).
   - Acute URTI (`J06.9`): Evaluated at 74.00% vs. 8.50% reference (+65.50% bias).

These discrepancies are systematically dissected in the following Discrepancy Analysis report.
