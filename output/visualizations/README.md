# SYNAPSE Phase 2 Visualizations Catalog

This directory contains vector SVG visualizations generated directly from the canonical 10,000-patient synthetic cohort (`data/synthetic/`, seed 42, 720 days, timestep 7).

## Catalog of Visualizations

### 1. `demographic_age_pyramid.svg`
* **Topic**: Population Demography & Stratified Sampling.
* **Underlying Data**: `data/synthetic/patients.csv` ($N=10,000$).
* **Description**: Bilateral horizontal age pyramid comparing synthetic cohort proportions (51.5% male, 48.5% female across 5 standard age bands: 0–14, 15–24, 25–44, 45–64, and 65+) against official Sample Registration System (SRS) 2021 India Census benchmarks.
* **Statistical Verification**:
  * Age Pyramid Jensen-Shannon Divergence (JSD): $0.00005$ ($\le 0.05$ threshold $\rightarrow$ **PASS**).
  * Age-by-Sex JSD: $0.00013$ ($\le 0.05$ threshold $\rightarrow$ **PASS**).

### 2. `blood_pressure_distributions.svg`
* **Topic**: Seated Blood Pressure Triplicate Protocol & Habituation Dynamics.
* **Underlying Data**: `data/synthetic/community_bp_readings.csv` (7,914 measurements across 2,638 older adult participants, age 45+).
* **Protocol**: `LASI_WAVE1_TRI_MEASUREMENT` v1.0.0.
* **Description**: Progression of systolic and diastolic blood pressure across three sequential seated measurements (Reading 1, Reading 2, Reading 3) and the official protocol average (mean of readings 2 & 3). Annotates the habituation / familiarization drop (mean SBP drops from $130.14 \pm 9.41$ mmHg in Reading 1 to $126.69 \pm 9.59$ mmHg in Reading 2 and $126.61 \pm 9.56$ mmHg in Reading 3).
* **Physiological Invariants**:
  * Strictly SBP > DBP: 0 violations across all 7,914 readings (**PASS**).
  * Pulse pressure $\ge 20$ mmHg: Minimum observed pulse pressure is $22.6$ mmHg (**PASS**).

### 3. `disease_prevalence_comparison.svg`
* **Topic**: Epidemiological Calibration & Chronic/Acute Disease Progression.
* **Underlying Data**: `data/synthetic/conditions.csv`, `patients.csv`, `symptoms.csv`.
* **Description**: Comparison of synthetic cohort disease metrics against national Indian clinical and epidemiological benchmarks:
  * **Adult Hypertension Period Prevalence**: $34.82\%$ ($2,324 / 6,675$ adults age $\ge 20$) vs. $30.7\%$ ICMR-INDIAB 2023 benchmark (target $[27\%, 35\%]$) $\rightarrow$ **PASS**.
  * **Adult Type 2 Diabetes Period Prevalence**: $13.96\%$ ($932 / 6,675$ adults age $\ge 20$) vs. $11.4\%$ ICMR-INDIAB 2023 benchmark (target $[9\%, 15\%]$) $\rightarrow$ **PASS**.
  * **Comorbid HTN in T2D Patients**: $47.10\%$ ($439 / 932$ diabetic adults) vs. $50.1\%$ ICMR-INDIAB benchmark (target $[40\%, 60\%]$) $\rightarrow$ **PASS**.
  * **Acute URTI Cumulative 720-Day Attack Rate**: $71.65\%$ ($7,165 / 10,000$ cohort) vs. $70.0\%$ National Health Profile 2020 (target $[60\%, 80\%]$) $\rightarrow$ **PASS**.
  * **Acute URTI 14-Day Point Prevalence**: $4.82\%$ vs. $8.5\%$ NHP 2020 benchmark (target $[3\%, 12\%]$) $\rightarrow$ **PASS**.

### 4. `simulation_architecture_workflow.svg`
* **Topic**: End-to-End Longitudinal Architecture & Governance Lifecycle.
* **Description**: Technical architecture flow illustrating:
  1. SRS 2021 demographic sampling and baseline risk profiling.
  2. Synthea-inspired YAML disease state progression (Hypertension, T2D, Acute URTI).
  3. Care-seeking triggers, OPD consultations, ICMR STG prescribing, and allergy safety filters (`RULE-CLIN-ALLERGY-001`).
  4. Hemodynamic engines (`LEGACY_CONDITIONAL` default, `FORWARD_STATE_SPACE` experimental) and survey wave sampling.
  5. Background mortality sampling via SRS 2016–2020 life tables.
  6. Analytical CSV serialization (18 standardized tables with SHA-256 manifests).
  7. Automated validation gate with locked status: `REFERENCE_DATA_PENDING`.

## Regeneration
To regenerate these visualizations directly from the canonical dataset, run:
```bash
python3 scratch/generate_visualizations.py
```
*(No external plotting GUI libraries required; generated via native vector XML SVG serialization).*
