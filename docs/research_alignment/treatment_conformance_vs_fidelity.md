# Treatment Conformance vs. Treatment Fidelity: Methodological Audit

**Audit Target:** Pharmacotherapy Metrics (`rx_firstline_hypertension`, `rx_firstline_diabetes`, `rx_adherence_assumption`)  
**Reported Synthetic Estimates:**
- First-Line Antihypertensive Alignment: **$100.00\%$** (134 of 134 diagnosed cases)
- First-Line Antidiabetic Alignment: **$100.00\%$** (31 of 31 diagnosed cases)
- Medication Adherence Assumption: **$100.00\%$** (Full Adherence Disclosure)

---

## 1. Executive Summary & Conceptual Distinction

A critical finding of this audit is that the reported $100\%$ treatment alignment reflects **algorithmic rule conformance to the generator's state machine, rather than empirical real-world prescribing fidelity**.

In real-world clinical practice in India, prospective registries and surveys (e.g., ICMR, CURES, SMART study) observe first-line monotherapy prescribing rates between **$45\%$ and $65\%$** due to clinical inertia, multi-drug combination regimens, patient financial constraints, contraindications, and delayed escalation.

To prevent misleading claims of "clinical realism", the SYNAPSE evaluation framework has formally established three distinct levels of pharmacotherapy evaluation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Algorithmic Rule Conformance                                             │
│    "Did the discrete-event state machine execute its programmed transition?"│
│    Synthetic Score: 100.00% (Deterministic state progression)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Clinical Guideline Alignment                                             │
│    "Does the programmed rule agree with standard treatment guidelines?"     │
│    Standard: ICMR Standard Treatment Guidelines 2022 (Amlodipine / Metformin)│
│    Synthetic Score: 100.00% Conformance to Guideline Monotherapy Rules      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Real-World Prescribing Fidelity                                          │
│    "Does the synthetic prescription distribution mirror observed practice?" │
│    Real-World Empirical Target: 45% - 65% Monotherapy Alignment             │
│    Synthetic Status: UNVERIFIED / ASSUMPTION                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Audit of Exact Numerator and Denominator Formulations

### 2.1 First-Line Antihypertensive Therapy (`rx_firstline_hypertension`)
- **Eligible Cohort (Denominator):** All distinct condition records with `condition_code == "I10"` in `conditions.csv`.
  - In $N=500$ (Seed 42): $N_{\text{denom}} = 134$ adult hypertension cases.
- **Conforming Cohort (Numerator):** Diagnosed `I10` condition IDs linked to a prescription in `medications.csv` for a Calcium Channel Blocker (Amlodipine) or Angiotensin Receptor Blocker (Telmisartan / Losartan).
  - In $N=500$ (Seed 42): $N_{\text{num}} = 134$.
- **Calculated Metric:** $\frac{134}{134} \times 100.0\% = \mathbf{100.00\%}$.
- **Code Trace in `hypertension.yaml`:**
  Every patient diagnosed in `ScreeningEncounter` transitions deterministically to `PrescribeAntihypertensive`:
  ```yaml
  PrescribeAntihypertensive:
    type: "MedicationOrder"
    drug_code: "AML-5"
    drug_name: "Amlodipine"
    drug_class: "Calcium-Channel-Blocker"
  ```
  Because the pathway lacks stochastic branching (e.g., beta-blockers, ACE-inhibitors, non-pharmacological lifestyle therapy, or physician refusal), the numerator is mathematically guaranteed to equal the denominator.

### 2.2 First-Line Oral Hypoglycemic Therapy (`rx_firstline_diabetes`)
- **Eligible Cohort (Denominator):** All distinct condition records with `condition_code == "E11.9"` in `conditions.csv`.
  - In $N=500$ (Seed 42): $N_{\text{denom}} = 31$ adult diabetes cases.
- **Conforming Cohort (Numerator):** Diagnosed `E11.9` condition IDs linked to a prescription for Biguanides (Metformin).
  - In $N=500$ (Seed 42): $N_{\text{num}} = 31$.
- **Calculated Metric:** $\frac{31}{31} \times 100.0\% = \mathbf{100.00\%}$.
- **Code Trace in `diabetes_t2.yaml`:**
  Every patient diagnosed in `DiagnosticEncounter` transitions deterministically through `InitiateDiabeticCarePlan` to `PrescribeMetformin`:
  ```yaml
  PrescribeMetformin:
    type: "MedicationOrder"
    drug_code: "MET-500"
    drug_name: "Metformin"
    drug_class: "Biguanide"
  ```
  There is zero branching for initial sulfonylurea monotherapy, DPP-4 inhibitors, or lifestyle-only management.

---

## 3. Disentangling Conformance from Real-World Fidelity

| Dimension | Synthetic Metric Behavior | Real-World Empirical Reality (India) | Audit Assessment |
| :--- | :--- | :--- | :--- |
| **Initial Drug Selection** | 100% Amlodipine for HTN; 100% Metformin for T2D. | Fixed-dose combinations (e.g. Telmisartan + Amlodipine, Metformin + Glimepiride) represent ~35% of initial prescriptions in urban private clinics. | Synthetic data lacks combination therapy diversity. |
| **Contraindication Handling** | Allergy vetoes enforced for Penicillin in URTI. No renal impairment contraindication modeled for Metformin. | Metformin is contraindicated in severe CKD (eGFR $< 30$ mL/min). Amlodipine is avoided in acute peripheral edema. | Partial contraindication handling; renal screening is not yet modeled. |
| **Prescribing Fidelity** | $100\%$ conformance to single guideline rule. | Empirical conformance in ICMR-INDIAB and SMART study ranges from **$48.2\%$ to $62.4\%$**. | **Do not label as high real-world fidelity.** |
| **Patient Adherence** | Assumed **$100\%$ perfect adherence**. | Real-world non-communicable disease medication adherence in India is **$42.6\% - 58.1\%$** (NSS 75th round, ICMR registries). | High-risk assumption that must be disclosed as **UNVERIFIED**. |

---

## 4. Impact of the Full-Adherence Assumption

In SYNAPSE Phase 2, simulated patients never skip doses, discontinue medications due to cost, or experience supply-chain stockouts.

### Consequences for Downstream Synthetic Realism:
1. **Suppression of Secondary Complications:** Because 100% of hypertensive patients maintain continuous Amlodipine therapy, stroke and ischemic heart disease complication rates in the synthetic cohort are artificially suppressed.
2. **Lack of Glycemic Failure:** Without non-adherence, patients never experience diabetic ketoacidosis or hyperosmolar hyperglycemic states.
3. **Optimistic Health Outcomes:** Synthetic cohorts will underestimate the health utilization and hospitalization costs observed in real-world Indian public health systems.

---

## 5. Standardized Acceptance Policy for Treatment Metrics

To maintain rigorous scientific governance, the evaluation framework adopts the following standards:

1. **Metric Relabeling:**  
   The metric names in `DatasetEvaluator` have been formally updated from "Treatment Guideline Alignment" to:
   - `Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Antihypertensive Therapy)`
   - `Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Oral Hypoglycemic Therapy)`
2. **Mandatory Limitation Disclosure:**  
   The `known_limitations` metadata explicitly discloses:
   > *"Measures algorithmic rule compliance to state transitions; real-world prescribing fidelity in Indian registry surveys is ~45–65%."*
3. **Adherence Assumption Enforcement:**  
   The metric `rx_adherence_assumption` is permanently locked with `status: MetricStatus.UNVERIFIED`. It can never be marked as an empirical `PASS`.
