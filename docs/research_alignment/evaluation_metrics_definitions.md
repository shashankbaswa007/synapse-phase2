# SYNAPSE Phase 2 — Implemented Evaluation Metrics & Formal Definitions

## 1. Overview of Metric Hierarchy

SYNAPSE Phase 2 implements seventeen distinct quantitative evaluation metrics structured into six orthogonal dimensions:
1. **Invariants (`INVARIANTS`):** 4 metrics enforcing temporal, referential, and safety invariants.
2. **Demographics (`DEMOGRAPHICS`):** 3 metrics evaluating marginal and joint demographic structures.
3. **Disease Prevalence (`PREVALENCE`):** 3 metrics evaluating adult chronic and episodic conditions.
4. **Comorbidity (`COMORBIDITY`):** 1 metric evaluating multi-disease clustering.
5. **Longitudinal Dynamics (`LONGITUDINAL`):** 3 metrics evaluating encounter rates, inter-visit intervals, and mortality.
6. **Treatment & Clinical Practice (`TREATMENT`):** 3 metrics evaluating guideline conformance, safety, and adherence assumptions.

---

## 2. Invariant Metrics (Hard Correctness Gates)

Invariant checks are authoritative boolean safety and temporal gates. Any single violation immediately assigns a `FAIL` status to the run.

### 2.1 `inv_no_event_pre_birth`
- **Dimension:** `INVARIANTS`
- **Definition:** Asserts that for every patient $p \in \mathcal{P}$, no clinical encounter, procedure, or order timestamp $t_{event}$ precedes the patient's birth date $t_{birth}$.
- **Formula:**
  $$\text{Violations} = \sum_{e \in \mathcal{E}} \mathbb{I}(t_e < t_{\text{birth}}(\text{patient}(e)))$$
- **Acceptance Policy:** PASS if $\text{Violations} = 0$, else FAIL.
- **Reference Benchmark:** 0.00.

### 2.2 `inv_no_event_post_mortem`
- **Dimension:** `INVARIANTS`
- **Definition:** Asserts that for every deceased patient $p \in \mathcal{P}_{deceased}$, no clinical activity is recorded subsequent to $t_{death}$.
- **Formula:**
  $$\text{Violations} = \sum_{e \in \mathcal{E}} \mathbb{I}(t_e > t_{\text{death}}(\text{patient}(e)))$$
- **Acceptance Policy:** PASS if $\text{Violations} = 0$, else FAIL.
- **Reference Benchmark:** 0.00.

### 2.3 `inv_diagnosis_encounter_linkage`
- **Dimension:** `INVARIANTS`
- **Definition:** Verifies that every recorded diagnosis record $c \in \mathcal{C}$ references an encounter ID that resolves to a valid record in `encounters.csv`.
- **Formula:**
  $$\text{Violations} = \sum_{c \in \mathcal{C}} \mathbb{I}(c.\text{encounter\_id} \notin \mathcal{E}_{\text{ids}})$$
- **Acceptance Policy:** PASS if $\text{Violations} = 0$, else FAIL.
- **Reference Benchmark:** 0.00.

### 2.4 `inv_allergy_safety_veto`
- **Dimension:** `INVARIANTS`
- **Definition:** Validates clinical safety by verifying that no medication order is dispensed containing a drug to which the patient has an active documented allergy.
- **Formula:**
  $$\text{Violations} = \sum_{m \in \mathcal{M}} \mathbb{I}(\text{is\_contraindicated}(m.\text{drug}, \text{allergies}(\text{patient}(m))))$$
- **Acceptance Policy:** PASS if $\text{Violations} = 0$, else FAIL.
- **Reference Benchmark:** 0.00.

---

## 3. Demographic Fidelity Metrics

### 3.1 `demo_sex_distribution`
- **Dimension:** `DEMOGRAPHICS`
- **Definition:** Proportion of synthetic cohort identifying as male, compared to Census SRS 2021.
- **Formulas:**
  $$\hat{p}_{\text{male}} = \frac{N_{\text{male}}}{N_{\text{total}}} \times 100\%$$
  $$CI_{95\%} = \text{WilsonScore}(\hat{p}_{\text{male}}, N_{\text{total}}, z=1.95996)$$
- **Reference Target:** 51.50% (SRS 2021).
- **Acceptance Policy:**
  - PASS: $|\hat{p}_{\text{male}} - 51.50| \le 5.0\%$
  - WARNING: $5.0\% < |\hat{p}_{\text{male}} - 51.50| \le 10.0\%$
  - FAIL: $|\hat{p}_{\text{male}} - 51.50| > 10.0\%$

### 3.2 `demo_age_pyramid_jsd`
- **Dimension:** `DEMOGRAPHICS`
- **Definition:** Jensen-Shannon Divergence (base 2) between synthetic age distribution and SRS 2021 5-band reference pyramid.
- **Formulas:**
  $$M = \frac{1}{2}(P + Q)$$
  $$JSD(P, Q) = \frac{1}{2} D_{KL}(P \parallel M) + \frac{1}{2} D_{KL}(Q \parallel M)$$
  $$\text{where } D_{KL}(A \parallel B) = \sum_i A_i \log_2 \frac{A_i}{B_i}$$
- **Auxiliary Diagnostics:**
  - Total Variation Distance: $TVD = \frac{1}{2}\sum |P_i - Q_i|$
  - Chi-Square Goodness-of-Fit with automated sparse bin pooling ($E_i \ge 5.0$)
  - Cramér's V effect size: $V = \sqrt{\frac{\chi^2}{N(k-1)}}$
- **Acceptance Policy:**
  - PASS: $JSD < 0.05$
  - WARNING: $0.05 \le JSD < 0.15$
  - FAIL: $JSD \ge 0.15$

### 3.3 `demo_age_by_sex_jsd`
- **Dimension:** `DEMOGRAPHICS`
- **Definition:** JSD across the 10-cell joint distribution matrix of 5 age intervals $\times$ 2 sexes against SRS 2021 Statement 19.
- **Acceptance Policy:**
  - PASS: $JSD < 0.08$
  - WARNING: $0.08 \le JSD < 0.20$
  - FAIL: $JSD \ge 0.20$

---

## 4. Disease Prevalence Metrics

### 4.1 `prev_hypertension_adults`
- **Dimension:** `PREVALENCE`
- **Definition:** Prevalence of essential hypertension (`I10`) among eligible adults aged $\ge 20$ years.
- **Formulas:**
  $$\hat{p}_{\text{HTN}} = \frac{K_{\text{HTN}, \text{age} \ge 20}}{N_{\text{age} \ge 20}} \times 100\%$$
- **Uncertainty:** Wilson Score 95% Confidence Interval.
- **Reference Target:** 30.70% (ICMR-INDIAB 2023).
- **Acceptance Policy:**
  - PASS: $|\hat{p}_{\text{HTN}} - 30.70| \le 8.0\%$
  - WARNING: $8.0\% < |\hat{p}_{\text{HTN}} - 30.70| \le 15.0\%$
  - FAIL: $|\hat{p}_{\text{HTN}} - 30.70| > 15.0\%$

### 4.2 `prev_diabetes_t2_adults`
- **Dimension:** `PREVALENCE`
- **Definition:** Prevalence of Type 2 Diabetes (`E11.9`) among eligible adults aged $\ge 20$ years.
- **Formulas:**
  $$\hat{p}_{\text{T2D}} = \frac{K_{\text{T2D}, \text{age} \ge 20}}{N_{\text{age} \ge 20}} \times 100\%$$
- **Reference Target:** 11.40% (ICMR-INDIAB 2023).
- **Acceptance Policy:**
  - PASS: $|\hat{p}_{\text{T2D}} - 11.40| \le 6.0\%$
  - WARNING: $6.0\% < |\hat{p}_{\text{T2D}} - 11.40| \le 12.0\%$
  - FAIL: $|\hat{p}_{\text{T2D}} - 11.40| > 12.0\%$

### 4.3 `prev_urti_all_ages`
- **Dimension:** `PREVALENCE`
- **Definition:** Period prevalence of acute URTI (`J06.9`) across total cohort.
- **Reference Target:** 8.50% (NHP India 2020).
- **Acceptance Policy:**
  - PASS: $|\hat{p}_{\text{URTI}} - 8.50| \le 5.0\%$
  - WARNING: $5.0\% < |\hat{p}_{\text{URTI}} - 8.50| \le 10.0\%$
  - FAIL: $|\hat{p}_{\text{URTI}} - 8.50| > 10.0\%$

---

## 5. Comorbidity Metric

### 5.1 `comorb_htn_in_t2d`
- **Dimension:** `COMORBIDITY`
- **Definition:** Conditional prevalence of hypertension among patients diagnosed with Type 2 Diabetes ($P(\text{HTN} \mid \text{T2D})$) in adults $\ge 20$.
- **Formulas:**
  $$\hat{p}(\text{HTN} \mid \text{T2D}) = \frac{N_{\text{HTN} \cap \text{T2D}}}{N_{\text{T2D}}} \times 100\%$$
  $$\text{Observed-to-Expected Ratio } (O/E) = \frac{\hat{p}(\text{HTN} \cap \text{T2D})}{\hat{p}(\text{HTN}) \times \hat{p}(\text{T2D})}$$
  $$\text{Odds Ratio } (OR) = \frac{a \cdot d}{b \cdot c} \text{ (with Haldane-Anscombe zero-cell correction)}$$
- **Reference Target:** 50.10% (ICMR-INDIAB 2023).
- **Acceptance Policy:**
  - NOT_APPLICABLE: If $N_{\text{T2D}} = 0$.
  - PASS: $|\hat{p}(\text{HTN} \mid \text{T2D}) - 50.10| \le 15.0\%$
  - WARNING: $15.0\% < |\hat{p}(\text{HTN} \mid \text{T2D}) - 50.10| \le 25.0\%$
  - FAIL: Difference $> 25.0\%$.

---

## 6. Longitudinal Dynamics & Clinical Treatment Metrics

### 6.1 `long_encounters_per_pt_year`
- **Definition:** Total closed encounters per patient-year: $\frac{|\mathcal{E}|}{N \times \text{years}}$.
- **Acceptance Policy:** PASS if in plausible range $[0.2, 5.0]$, else WARNING. Tagged `UNVERIFIED`.

### 6.2 `long_inter_encounter_interval_days`
- **Definition:** Mean calendar days elapsed between consecutive outpatient visits for multi-visit patients.
- **Reference Standard:** 180.0 days (ICMR standard 3–6 month chronic review guideline).
- **Acceptance Policy:** PASS if in $[30, 365]$ days. Tagged `UNVERIFIED`.

### 6.3 `long_crude_mortality_rate`
- **Definition:** Annualized crude death rate: $\frac{|\mathcal{D}|}{N \times \text{years}}$.
- **Reference Target:** 0.0060 (SRS Abridged Life Table 2016–2020).
- **Acceptance Policy:** PASS if $|\hat{q} - 0.0060| \le 0.02$. Tagged `VERIFIED`.

### 6.4 `rx_firstline_hypertension`
- **Definition:** Percentage of diagnosed hypertension cases initiated on first-line Calcium-Channel Blocker (Amlodipine) or ARB.
- **Reference Target:** 100.0% (ICMR STG 2022).
- **Acceptance Policy:** PASS if $\ge 80.0\%$, else WARNING. Tagged `VERIFIED`.

### 6.5 `rx_firstline_diabetes`
- **Definition:** Percentage of diagnosed Type 2 Diabetes cases initiated on first-line Biguanide (Metformin).
- **Reference Target:** 100.0% (ICMR STG 2022).
- **Acceptance Policy:** PASS if $\ge 80.0\%$, else WARNING. Tagged `VERIFIED`.

### 6.6 `rx_adherence_assumption`
- **Definition:** Formal disclosure documenting that synthetic patient adherence to dispensed pharmacotherapy is 100%.
- **Acceptance Policy:** Strictly tagged `UNVERIFIED`. Never assigned `PASS` to avoid misleading assertions of real-world behavioral adherence.
