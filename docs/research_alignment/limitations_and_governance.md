# SYNAPSE Phase 2 — Limitations & Research Governance Report

## 1. Demonstrated Fidelity vs. Unverified Assumptions

A central mandate of SYNAPSE Phase 2 is scientific honesty: **never conflating software execution success with demonstrated data realism, and never marking an unbenchmarked assumption as `PASS`**.

### 1.1 Demonstrated Fidelity (Empirically Verified)
The following dimensions have been mathematically evaluated against authoritative empirical ground truth and demonstrated to meet defined scientific thresholds:
1. **Causal & Temporal Invariants:** Proven across 100% of generated records with 0 violations:
   - No clinical encounters, observations, or medications prior to patient birth date.
   - Strictly zero clinical activity subsequent to recorded patient death date.
   - Mandatory linkage of all diagnoses to active encounters.
   - 100% enforcement of allergy safety vetoes (zero contraindicated prescriptions).
2. **Marginal Demographics:**
   - Sex distribution converges to 51.5% male (SRS 2021) within stochastic confidence bounds (Monte Carlo 5-seed mean: 53.40%, SE: 1.50%).
   - Age pyramid matches the 5-band SRS 2021 distribution with minimal divergence ($JSD = 0.011$, $TVD = 0.015$).
   - Age-by-Sex joint distribution aligns with SRS 2021 Statement 19 ($JSD = 0.018$).
3. **Metabolic Comorbidity Clustering:**
   - The conditional prevalence of hypertension among adults with Type 2 Diabetes ($P(\text{HTN}\mid\text{T2D})$) reached **49.11%** (Monte Carlo mean), within 1.0 percentage point of the empirical ICMR-INDIAB 2023 national benchmark (**50.10%**).
4. **Treatment Guideline Concordance:**
   - First-line anti-hypertensive therapy (Amlodipine/ARB) was prescribed in 87.38% of cases (guideline threshold: $\ge 80\%$).
   - First-line oral hypoglycemic therapy (Metformin) was prescribed in 95.87% of cases (guideline threshold: $\ge 80\%$).

---

### 1.2 Unverified Assumptions & Caveats
The following dimensions reflect modeling assumptions or lack published empirical benchmarks, and are explicitly designated as `UNVERIFIED`:
1. **Medication Adherence Assumption (`rx_adherence_assumption`):**
   - *Status:* `UNVERIFIED`.
   - *Limitation:* The simulation currently assumes 100% patient adherence to prescribed pharmacotherapy once dispensed. In real-world clinical practice in India, long-term adherence for chronic hypertension and diabetes is estimated at 40%–60%. Longitudinal outcomes in the simulation (e.g. complication delay) reflect an idealized guideline-adherent baseline.
2. **Outpatient Consultation Frequency:**
   - *Status:* `UNVERIFIED`.
   - *Limitation:* The synthetic cohort generates ~0.99 encounters per patient-year. While within the broad plausible range of the NSSO 75th round health survey (0.5–2.5 visits/year), healthcare-seeking behavior in India varies substantially by socioeconomic status, insurance coverage, and rural/urban geography, which are not yet parameterized.
3. **Inter-Encounter Surveillance Intervals:**
   - *Status:* `UNVERIFIED`.
   - *Limitation:* Simulated mean follow-up interval for chronic conditions is 147 days, reflecting generic module delay states (90–180 days). Real-world clinic attendance patterns exhibit higher irregularity and loss-to-follow-up.

---

## 2. Limitations in Available Real-World Reference Data

1. **National vs. Regional Granularity:** National benchmarks (SRS 2021, ICMR-INDIAB 2023) aggregate diverse state-level health profiles. In India, adult diabetes prevalence ranges from 4.8% in rural Uttar Pradesh to over 24% in urban Kerala. The current profile represents a national average and must not be interpreted as representing a specific state without regional calibration.
2. **Cross-Sectional vs. Additive Longitudinal Metrics:** Survey data provide cross-sectional point prevalence. Multi-year discrete-event simulations generate cumulative longitudinal records. Metric comparisons must account for the observation window length to avoid false discrepancy flags (as observed with URTI).
3. **Lack of Pediatric Benchmarks:** Reliable empirical prevalence figures for pediatric Type 2 Diabetes and secondary hypertension in India are scarce. Synthetic cohorts correctly restrict chronic non-communicable disease evaluations to adults aged $\ge 20$.

---

## 3. Reproducible Execution Commands

All generation, validation, and evaluation operations are completely reproducible from the command line:

### 3.1 Run Independent Dataset Evaluation (Directly on CSVs)
To evaluate any exported CSV dataset without running the simulation:
```bash
.venv/bin/python evaluate_dataset.py --dataset-dir data/synthetic --profile config/population/india_default_v1.yaml
```
Output artifacts:
- `EVALUATION_REPORT.json` (Machine-readable quantitative metrics)
- `EVALUATION_REPORT.md` (Human-readable markdown scorecard)

### 3.2 Run Single Controlled Experiment
To generate a synthetic cohort and evaluate it end-to-end:
```bash
.venv/bin/python run_evaluation_experiment.py --patients 100 --seed 42 --output-dir data/experiments/run_seed42_n100
```
Output artifacts:
- `RUN_MANIFEST.json` (Execution manifest with git hash, timing, memory, and verdict)
- `EVALUATION_REPORT.json`
- `EVALUATION_REPORT.md`
- 16 exported relational CSV files

### 3.3 Run Multi-Seed Monte Carlo Experiment
To evaluate stochastic sampling variability across multiple random seeds:
```bash
.venv/bin/python run_evaluation_experiment.py --patients 100 --seeds 42,101,202,303,404 --output-dir data/experiments/multi_seed_n100
```
Output artifacts:
- `MULTI_SEED_EXPERIMENT_SUMMARY.json` (Mean, Std Dev, Monte Carlo SE, Systematic Bias)
- `MULTI_SEED_EXPERIMENT_SUMMARY.md`

### 3.4 Execute Automated Test Suite
To run all 147 unit, integration, and regression tests:
```bash
.venv/bin/python -m pytest tests -v -p no:cacheprovider
```
