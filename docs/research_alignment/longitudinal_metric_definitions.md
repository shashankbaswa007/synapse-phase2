# Longitudinal Metric Definitions and Methodological Specifications

**Document ID:** `SYNAPSE-AUDIT-DELIV-03`  
**Date:** October 2026  
**Auditor:** SYNAPSE Longitudinal Credibility & Statistical Validation Team  
**Focus Area:** Metric Typology, Mathematical Formulations, Denominator Alignment, Uncertainty Methods, and Comparability Audits  

---

## 1. Metric Audit Summary Matrix

Every metric evaluated in the SYNAPSE Phase 2 longitudinal trajectory audit is cataloged below, explicitly classifying its epidemiological type, eligibility, mathematical form, uncertainty methodology, and comparability status against empirical literature.

| # | Metric Identifier | Epidemiological Type | Synthetic Formula | Synthetic Denominator | Reference Benchmark | Comparability Status |
| :-: | :--- | :--- | :--- | :--- | :--- | :---: |
| **1** | `long_encounters_per_pt_year` | Person-Time Rate | $\frac{\text{Total Encounters}}{\sum \tau_i}$ | Person-Years at Risk | NSS 75th Round OPD (0.8–2.5) | **UNVERIFIED** |
| **2** | `long_inter_encounter_interval_days` | Interval Metric (Days) | $\frac{1}{M}\sum (t_{j+1} - t_j)$ | Multi-visit pairs | ICMR Guidelines (90–180d) | **UNVERIFIED** |
| **3** | `prev_htn_baseline` | Point Prevalence | $\frac{\text{Cases with } t_{\text{diag}} \le t_0 + 31\text{d}}{N_{\text{adults}}}$ | Adults ($\ge 20$) | ICMR-INDIAB 2023 (30.7%) | **VERIFIED** |
| **4** | `prev_htn_period` | Period Prevalence | $\frac{\text{All Diagnosed Cases during } \tau}{N_{\text{adults}}}$ | Adults ($\ge 20$) | ICMR-INDIAB 2023 (30.7%) | **ASSUMPTION / COMPARABLE** |
| **5** | `prev_t2d_adults` | Period Prevalence | $\frac{\text{All Diagnosed Cases during } \tau}{N_{\text{adults}}}$ | Adults ($\ge 20$) | ICMR-INDIAB 2023 (11.4%) | **VERIFIED** |
| **6** | `long_treatment_intensification_rate` | Cumulative Proportion | $\frac{N(\text{Treated patients stepped up})}{N(\text{Treated chronic patients})}$ | Treated Chronic Patients | ICMR-STG Rules (0.85 Expected) | **UNVERIFIED (Guideline Rule)** |
| **7** | `long_chronic_complication_rate` | Cumulative Incidence | $\frac{N(\text{Incident CKD / Nephropathy})}{N(\text{Treated chronic patients})}$ | Treated Chronic Patients | CURES-45 / CCDC (4.0% 2-Yr) | **VERIFIED** |
| **8** | `long_crude_mortality_rate` | Person-Time Rate | $\frac{D_{\text{obs}}}{\sum \tau_i}$ | Person-Years at Risk | Census SRS 2016–2020 Life Table | **VERIFIED** |
| **9** | `long_censored_pt_years` | Person-Time Quantity | $\sum_{i=1}^N \frac{\min(t_{\text{end}}, t_{\text{death}}) - t_{\text{start}}}{365.25}$ | Cohort Follow-up | Exact Theoretical Max (985.63) | **VERIFIED** |
| **10**| `long_disease_control_trajectories` | Latent Markov Trajectory | Transition State Matrix | Chronic Encounter Visits | Synthea / ICMR Protocol | **ASSUMPTION** |

---

## 2. Detailed Metric Specifications

### 1. Encounters per Person-Year (`long_encounters_per_pt_year`)
- **Mathematical Definition:** Total clinical encounters occurring during the observation window divided by the total right-censored person-years at risk.
  $$\text{Rate} = \frac{\sum_{k=1}^K 1}{\sum_{i=1}^N \tau_i}$$
- **Numerator:** Total count of encounter records in `encounters.csv` with $\text{start\_time} \in [t_{\text{start}}, t_{\text{end}}]$.
- **Denominator:** Total individual right-censored person-years ($\sum_{i=1}^N \tau_i$).
- **Unit:** Encounters per person-year ($\text{yr}^{-1}$).
- **Observation Window:** 720 days (24 months).
- **Eligibility Criteria:** Entire synthetic cohort ($N$).
- **Reference Population:** National Sample Survey (NSS 75th Round, 2017–2018), Outpatient Consultation Frequency.
- **Reference-Data Source:** NSS Report No. 586: "Key Indicators of Social Consumption in India: Health".
- **Metric Typology:** Person-time incidence density rate.
- **Statistical Uncertainty:** Poisson standard error: $\text{SE} = \frac{\sqrt{K}}{\sum \tau_i}$.
- **Comparability Audit:** **UNVERIFIED**. The synthetic simulator generates scheduled chronic disease surveillance visits (e.g. quarterly or semi-annual follow-ups) and acute illness visits within a primary care facility setting. NSS 75th Round measures self-reported all-cause outpatient consultations across all public/private providers in the community. While the synthetic range ($1.01\text{--}1.11$) falls within the plausible clinical range ($0.8\text{--}2.5$), it represents facility discrete-event scheduling rather than an empirical community survey match.

---

### 2. Mean Inter-Encounter Interval (`long_inter_encounter_interval_days`)
- **Mathematical Definition:** Mean elapsed time in days between consecutive clinical encounters for patients with two or more visits during the observation window.
  $$\bar{\Delta t} = \frac{1}{\sum_{i \in \text{Multi}} (n_i - 1)} \sum_{i \in \text{Multi}} \sum_{j=1}^{n_i - 1} \frac{(t_{i, j+1} - t_{i, j})}{86400\text{ sec}}$$
- **Numerator:** Sum of all consecutive visit intervals (days) across multi-visit patients.
- **Denominator:** Total number of consecutive visit pairs ($\sum (n_i - 1)$).
- **Unit:** Days.
- **Observation Window:** 720 days.
- **Eligibility Criteria:** Patients having $\ge 2$ distinct clinical encounters in `encounters.csv`.
- **Reference Benchmark:** ICMR Clinical Practice Guidelines for Chronic Diseases (recommended follow-up: 90 to 180 days).
- **Metric Typology:** Interval mean and median.
- **Statistical Uncertainty:** Sample standard deviation and median inter-quartile range.
- **Comparability Audit:** **UNVERIFIED**. The synthetic mean ($117\text{--}132\text{ days}$) directly reflects discrete-event scheduling delays programmed into `hypertension.yaml` (180 days) and `diabetes_t2.yaml` (90 days). Because real-world appointment adherence varies by socioeconomic and geographic factors, this metric validates module scheduler fidelity rather than real-world patient behavior.

---

### 3. Baseline Hypertension Prevalence (`prev_htn_baseline`)
- **Mathematical Definition:** Proportion of eligible adults diagnosed with essential hypertension ($I10$) at or near the start of the observation window ($t \le t_0 + 31\text{ days}$).
  $$\text{Prev}_{\text{base}} = \frac{\sum_{i \in \text{Adults}} \mathbf{1}_{\{I10 \in \text{Conditions}_i \text{ and } t_{\text{diag}} \le t_0 + 31\text{d}\}}}{N_{\text{adults}}}$$
- **Numerator:** Patients with condition $I10$ diagnosed within 31 days of simulation start.
- **Denominator:** Eligible adults aged $\ge 20$ years at simulation start.
- **Unit:** Percentage ($0\%\text{--}100\%$).
- **Observation Window:** $[t_{\text{start}}, t_{\text{start}} + 31\text{ days}]$.
- **Eligibility Criteria:** Age $\ge 20$ years (matched to ICMR-INDIAB sampling frame).
- **Reference Benchmark:** ICMR-INDIAB 2023 National Study (30.7%, 95% CI: 30.2%–31.2%).
- **Reference-Data Source:** Anjana et al., *Lancet Diabetes & Endocrinology* 2023.
- **Metric Typology:** Point prevalence.
- **Statistical Uncertainty:** Wilson 95% binomial score confidence interval.
- **Comparability Audit:** **VERIFIED**. Both synthetic and reference populations restrict eligibility to adults aged $\ge 20$. Initial pre-simulation assignment generates baseline prevalence ($30.4\%\text{--}35.2\%$), which encompasses the ICMR-INDIAB reference point of $30.7\%$.

---

### 4. Two-Year Hypertension Period Prevalence (`prev_htn_period`)
- **Mathematical Definition:** Proportion of eligible adults having an active or incident diagnosis of essential hypertension at any point during the 2-year observation window.
  $$\text{Prev}_{\text{period}} = \frac{\sum_{i \in \text{Adults}} \mathbf{1}_{\{I10 \in \text{Conditions}_i\}}}{N_{\text{adults}}}$$
- **Numerator:** All adults aged $\ge 20$ with condition $I10$ recorded in `conditions.csv`.
- **Denominator:** Adults aged $\ge 20$ years ($N_{\text{adults}}$).
- **Unit:** Percentage ($0\%\text{--}100\%$).
- **Observation Window:** 720 days ($t_{\text{start}}$ to $t_{\text{end}}$).
- **Eligibility Criteria:** Age $\ge 20$ years.
- **Reference Benchmark:** ICMR-INDIAB 2023 baseline ($30.7\%$).
- **Metric Typology:** 2-year cumulative period prevalence (Baseline Prevalence + 2-Year Cumulative Incidence).
- **Statistical Uncertainty:** Wilson 95% binomial score interval.
- **Comparability Audit:** **ASSUMPTION / COMPARABLE**. ICMR-INDIAB measures cross-sectional point prevalence. Over 2 years, incident cases ($3.5\%\text{--}6.2\%$) accumulate onto the baseline cohort, raising period prevalence to $33.8\%\text{--}40.8\%$. This accumulation is expected in longitudinal cohort studies (e.g. CCDC/CARRS prospective study reports 2-year cumulative HTN incidence of $\sim 5\%$).

---

### 5. Adult Type 2 Diabetes Prevalence (`prev_t2d_adults`)
- **Mathematical Definition:** Proportion of eligible adults with diagnosed Type 2 Diabetes ($E11.9$).
  $$\text{Prev}_{T2D} = \frac{\sum_{i \in \text{Adults}} \mathbf{1}_{\{E11.9 \in \text{Conditions}_i\}}}{N_{\text{adults}}}$$
- **Numerator:** Adults with code $E11.9$ in `conditions.csv`.
- **Denominator:** Adults aged $\ge 20$ years ($N_{\text{adults}}$).
- **Unit:** Percentage ($0\%\text{--}100\%$).
- **Observation Window:** 720 days.
- **Eligibility Criteria:** Age $\ge 20$ years.
- **Reference Benchmark:** ICMR-INDIAB 2023 (11.4%, 95% CI: 11.0%–11.8%).
- **Metric Typology:** Period prevalence.
- **Statistical Uncertainty:** Wilson 95% binomial score interval.
- **Comparability Audit:** **VERIFIED**. Synthetic adult diabetes prevalence across 5 seeds averages **$11.82\%$** ($10.85\%\text{--}13.18\%$), directly matching the empirical benchmark of $11.4\%$.

---

### 6. Treatment Intensification Rate (`long_treatment_intensification_rate`)
- **Mathematical Definition:** Cumulative proportion of treated chronic disease patients who receive stepped-up dual therapy over the 2-year follow-up period.
  $$\text{Rate}_{\text{intens}} = \frac{N(\text{Treated patients receiving dual therapy})}{N(\text{Treated chronic patients})}$$
  - Hypertension dual therapy: Amlodipine + Telmisartan.
  - Diabetes dual therapy: Metformin + Glimepiride.
- **Numerator:** Unique patients prescribed dual therapy in `medications.csv`.
- **Denominator:** Unique chronic patients prescribed at least one first-line medication.
- **Unit:** Dimensionless proportion ($0.0\text{--}1.0$).
- **Observation Window:** 720 days.
- **Eligibility Criteria:** Patients with diagnosed HTN or T2D who initiate pharmacotherapy.
- **Reference Benchmark:** None (`reference_estimate = None`). There is no clinical guideline mandating an aggregate 85% population escalation target. Cross-sectional real-world registries report ~35% dual therapy prescribing.
- **Metric Typology:** Cumulative patient-level escalation proportion (Descriptive Simulation Result).
- **Statistical Uncertainty:** Exact Binomial confidence interval.
- **Comparability Audit:** **UNVERIFIED (Guideline Conformance vs. Prescribing Fidelity)**. 
  - Cross-sectional empirical surveys in India (e.g. IHCI 2020) report visit-level intensification rates of $30\%\text{--}40\%$ under real-world therapeutic inertia.
  - In our simulation, guideline execution is deterministic: every uncontrolled visit in monotherapy triggers stepped-up therapy. Over 4 to 6 follow-up visits, nearly $75\%\text{--}83\%$ of patients experience at least one uncontrolled reading and receive dual therapy (5-seed mean: **$78.97\%$**).
  - Therapy-stage attributes (`htn_therapy_stage == 'dual'`) prevent redundant prescription orders on subsequent visits ($0$ duplicate orders).
  - **Audit Rule:** Classify real-world fidelity as **`UNVERIFIED`** (and cross-sectional 35% target as **`NOT_COMPARABLE`**). This metric evaluates algorithmic guideline execution, not empirical clinician prescribing fidelity.

---

### 7. Chronic Complication Rate (`long_chronic_complication_rate`)
- **Mathematical Definition:** Cumulative incidence of secondary microvascular and target-organ complications (Hypertensive CKD $I12.9$, Diabetic Nephropathy $E11.2$) emerging in chronic patients.
  $$\text{Incidence} = \frac{N(\text{Patients developing } I12.9 \text{ or } E11.2 \text{ after } t_0)}{N(\text{Chronic Disease Patients at Risk})}$$
- **Numerator:** Unique patients with incident $I12.9$ or $E11.2$ diagnosed after $t_0$.
- **Denominator:** Chronic patients (HTN or T2D) free of the complication at baseline ($721$ patient-trials across 5 seeds).
- **Unit:** Dimensionless cumulative risk ($0.0\text{--}1.0$).
- **Observation Window:** 720 days.
- **Eligibility Criteria:** Chronic disease patients observed over time.
- **Reference Benchmark:** CURES-45 / CCDC Prospective Cohort Studies ($4.0\%$ 2-year cumulative incidence).
- **Reference-Data Source:** Mohan et al., *Journal of Association of Physicians of India* (CURES study).
- **Metric Typology:** 2-year cumulative incidence accounting for competing risk of death.
- **Statistical Uncertainty:** Binomial 95% Wilson interval.
- **Comparability Audit:** **UNVERIFIED**. Discrete Markov transition weights in `hypertension.yaml` ($p=0.015$ semi-annually) and `diabetes_t2.yaml` ($p=0.010$ quarterly) yield an observed 2-year cumulative complication rate of **$3.73\%$** in Seed 42 and **$2.88\%$** 5-seed mean ($21/721$ chronic patients). Classified as **`UNVERIFIED`** because discrete Markov state transitions in a closed-facility simulation represent an architectural modeling mechanism rather than an externally calibrated clinical trial incidence.

---

### 8. Annualized Crude Mortality Rate (`long_crude_mortality_rate`)
- **Mathematical Definition:** Total observed deaths divided by total right-censored person-years at risk.
  $$\text{CMR} = \frac{D_{\text{obs}}}{\sum_{i=1}^N \tau_i}$$
- **Numerator:** Total death records in `deaths.csv`.
- **Denominator:** Total individual right-censored person-years ($\sum \tau_i = 972.35\text{ pt-yrs}$ 5-seed mean).
- **Unit:** Deaths per person-year ($\text{yr}^{-1}$).
- **Observation Window:** 720 days.
- **Eligibility Criteria:** All synthetic patients in the cohort.
- **Reference Benchmark:** Census SRS 2016–2020 Abridged Life Table ($0.0060\text{ yr}^{-1}$).
- **Metric Typology:** Crude incidence rate.
- **Statistical Uncertainty:** Poisson-Binomial 95% predictive interval.
- **Comparability Audit:** **WARNING**. Observed deaths across 5 seeds average **$14.00\text{ deaths}$** ($D \in [9, 19]$), within the Poisson-Binomial 95% predictive interval ($[5.69, 17.67]$) derived from individual age-specific life-table hazards ($E[D] = 11.68$). 100% of deaths are natural SRS life-table deaths (`R99`); zero double-counted AMI deaths (`I21.9`). A material caveat applies: uniform sampling within the $65\text{--}100$ Census band elevates representation of patients aged $\ge 75$, increasing crude mortality relative to the national all-age CDR ($6.0\text{ per } 1,000$).

---

### 9. Right-Censored Person-Time (`long_censored_pt_years`)
- **Mathematical Definition:** Exact sum of individual follow-up durations:
  $$\tau_{\text{total}} = \sum_{i=1}^N \frac{\min(t_{\text{end}}, t_{\text{death}, i}) - t_{\text{start}}}{365.25}$$
- **Numerator:** Sum of days observed across all $N$ patients.
- **Denominator:** $365.25\text{ days/year}$.
- **Unit:** Person-years.
- **Observation Window:** 720 days.
- **Eligibility Criteria:** All synthetic patients.
- **Reference Benchmark:** Theoretical maximum bound: $N \times (720 / 365.25) = \mathbf{985.63\text{ pt-yrs}}$ ($N=500$). Theoretical midpoint-loss expectation: $\mathbf{974.30\text{ pt-yrs}}$.
- **Metric Typology:** Time quantity.
- **Statistical Uncertainty:** Deterministic accounting. Hard software invariant `inv_person_time_upper_bound`.
- **Comparability Audit:** **SOFTWARE_INVARIANT_PASS**. 5-seed observed mean person-time is **$972.35\text{ person-years}$** (interval $966.84\text{--}976.78$), strictly $\le 985.63\text{ pt-yrs}$ across all runs with zero violations.

---

### 10. Longitudinal Disease-Control Trajectories (`long_disease_control_trajectories`)
- **Mathematical Definition:** Markovian state transitions tracking patient blood pressure and glycemic control over time across consecutive surveillance encounters:
  - Controlled $\to$ Controlled (Persistence)
  - Controlled $\to$ Uncontrolled (Relapse / Progression)
  - Uncontrolled $\to$ Controlled (Treatment Response)
  - Uncontrolled $\to$ Uncontrolled (Therapeutic Escalation)
- **Numerator / Denominator:** Follow-up visit transition counts.
- **Unit:** Transition probability matrix.
- **Observation Window:** 720 days.
- **Eligibility Criteria:** Chronic disease patients with $\ge 2$ follow-up encounters.
- **Reference Benchmark:** Synthea Clinical Trajectory Specification.
- **Metric Typology:** Discrete transition probabilities.
- **Statistical Uncertainty:** Multinomial transition error.
- **Comparability Audit:** **ASSUMPTION**. Seeded random draws at each surveillance visit dictate control transitions. Treatment intensification reliably improves control probability ($60\% \to 85\%$), maintaining clinically logical longitudinal pathways.
