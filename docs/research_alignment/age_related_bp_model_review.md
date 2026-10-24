# Age-Related Blood Pressure Model Review

## 1. Executive Summary

This document reviews the baseline and longitudinal blood pressure modeling mechanisms in SYNAPSE Phase 2 to determine:
1. Whether blood pressure distributions vary by age in the existing clinical modules.
2. Whether patient age influences disease progression, vascular resistance, or antihypertensive treatment response.
3. Whether the current model produces unrealistic age-invariant blood pressure patterns.
4. What architectural and evidence-based decisions are required before introducing age-dependent vascular physiology.

**Mandatory Constraint:** In strict compliance with research governance rules, no parameters in [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml) or [`config/knowledge/medical_knowledge.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/knowledge/medical_knowledge.yaml) have been modified or tuned to artificially match the test fixture. All findings are documented as scientific decisions requiring genuine reference microdata calibration.

---

## 2. Review of Current Blood Pressure Modeling Architecture

### Baseline Module Specification (`config/modules/hypertension.yaml`)
In [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml), blood pressure generation is specified across three states:

```yaml
  AgeCheck:
    name: "AgeCheck"
    type: "Guard"
    guard_condition: "age >= 20"
    distributed_transition:
      - to: "HypertensionOnset"
        weight: 0.0344
      - to: "NormotensiveDelay"
        weight: 0.9656

  RecordBloodPressure:
    name: "RecordBloodPressure"
    type: "Observation"
    observation_code: "SBP"
    observation_min: 145.0
    observation_max: 168.0
    paired_observation_code: "DBP"
    paired_observation_min: 90.0
    paired_observation_max: 104.0

  MeasureFollowUpBP:
    name: "MeasureFollowUpBP"
    type: "Observation"
    observation_code: "SBP"
    observation_min: 120.0
    observation_max: 165.0
    paired_observation_code: "DBP"
    paired_observation_min: 75.0
    paired_observation_max: 100.0
    distributed_transition:
      - to: "BPControlled"
        weight: 0.60
      - to: "BPUncontrolled"
        weight: 0.40
```

### Knowledge Base Specification (`config/knowledge/medical_knowledge.yaml`)
In [`config/knowledge/medical_knowledge.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/knowledge/medical_knowledge.yaml#L389-L414), vitals ranges are stratified broadly into three categories:
- `adult` (age 18–90): SBP $[90, 140]\text{ mmHg}$, DBP $[60, 90]\text{ mmHg}$.
- `pediatric` (age 1–17): SBP $[80, 120]\text{ mmHg}$, DBP $[50, 80]\text{ mmHg}$.
- `elderly` (age 65–90): SBP $[100, 160]\text{ mmHg}$, DBP $[60, 95]\text{ mmHg}$.

---

## 3. Findings from the Scientific Audit

### Finding 1: Age-Invariant Blood Pressure Sampling within Clinical Modules
- In [`config/modules/hypertension.yaml`](file:///Users/shashi/synapse/synapse-phase2/config/modules/hypertension.yaml), once a patient satisfies the initial guard `age >= 20`, blood pressure sampling in `RecordBloodPressure` draws uniformly from:
  $$\text{SBP} \sim \text{Uniform}(145.0, 168.0)\text{ mmHg}, \quad \text{DBP} \sim \text{Uniform}(90.0, 104.0)\text{ mmHg}$$
- **This range does not vary with age.** A 25-year-old newly diagnosed with hypertension receives a blood pressure draw from the exact same uniform bounds as an 80-year-old patient.
- Similarly, in `MeasureFollowUpBP`, the follow-up range is static:
  $$\text{SBP} \sim \text{Uniform}(120.0, 165.0)\text{ mmHg}, \quad \text{DBP} \sim \text{Uniform}(75.0, 100.0)\text{ mmHg}$$

### Finding 2: Age-Invariant Progression and Treatment Response
- In `hypertension.yaml`, the probability of blood pressure control at follow-up (`MeasureFollowUpBP`) is fixed at $60\%$ (`BPControlled`) vs. $40\%$ (`BPUncontrolled`).
- This transition probability is completely invariant to:
  - Patient age (e.g., age 45 vs. age 75).
  - Duration of hypertension.
  - Presence of comorbidities (e.g., type 2 diabetes mellitus).
  - Therapy stage (monotherapy with Amlodipine vs. dual therapy with Telmisartan).

### Finding 3: Divergence from Physiological Reality (Arterial Stiffening & Isolated Systolic Hypertension)
Extensive cardiovascular epidemiological literature (e.g., Framingham Heart Study, ICMR-INDIAB, LASI Wave 1) establishes that human arterial aging exhibits marked age-dependent patterns:
1. **Systolic Blood Pressure:** Tends to rise continuously throughout adulthood due to progressive collagen cross-linking, elastolysis, and loss of arterial compliance in the aorta and large conduit vessels.
2. **Diastolic Blood Pressure:** Typically rises until approximately age 50–55, after which it plateaus or declines as arterial recoil diminishes during diastole.
3. **Isolated Systolic Hypertension (ISH) & Pulse Pressure Widening:** In adults aged 65 and older, the predominant phenotype is Isolated Systolic Hypertension ($\text{SBP} \ge 140\text{ mmHg} \land \text{DBP} < 90\text{ mmHg}$), with pulse pressure widening ($\text{PP} = \text{SBP} - \text{DBP} > 60\text{ mmHg}$).
4. **Current Simulator Behavior:** Because `RecordBloodPressure` enforces $\text{DBP} \in [90.0, 104.0]\text{ mmHg}$ for all initial presentations, the current model cannot produce true Isolated Systolic Hypertension at baseline, producing an artificially elevated DBP distribution in adults aged 70+.

---

## 4. Evaluation of Potential Bias in LASI Wave 1 Comparison

When comparing the current synthetic cohort against LASI Wave 1:
- In [`data/evaluation/lasi_cohort_500/seed_42/LASI_EVALUATION_REPORT.md`](file:///Users/shashi/synapse/synapse-phase2/data/evaluation/lasi_cohort_500/seed_42/LASI_EVALUATION_REPORT.md):
  - Mean Index SBP in synthetic clinical cohort: **$156.44\text{ mmHg}$** (Ref: $148.51\text{ mmHg}$, diff $+7.93\text{ mmHg}$).
  - Mean Index DBP in synthetic clinical cohort: **$96.89\text{ mmHg}$** (Ref: $87.36\text{ mmHg}$, diff $+9.53\text{ mmHg}$).
- The elevation in synthetic DBP ($96.89$ vs. $87.36\text{ mmHg}$) directly reflects the lower bound of $90.0\text{ mmHg}$ enforced by `RecordBloodPressure`, whereas real-world older adults in LASI frequently have DBP between $75\text{ and }85\text{ mmHg}$ despite elevated SBP.

---

## 5. Architectural & Scientific Recommendations (Future Phase Roadmap)

Rather than arbitrarily altering bounds to match the sample fixture, the following formal scientific decisions are recorded for future calibration against genuine authorized microdata:

1. **Age-Continuous Latent Vascular Function:**
   Model baseline SBP and DBP as continuous functions of age and sex:
   $$\text{SBP}_{\text{latent}}(a) = \beta_0 + \beta_1 a + \beta_2 a^2 + \epsilon_{\text{sbp}}$$
   $$\text{DBP}_{\text{latent}}(a) = \gamma_0 + \gamma_1 a - \gamma_2 (a - 50)^+ + \epsilon_{\text{dbp}}$$
   Where parameters $\beta$ and $\gamma$ must be empirically calibrated against authorized LASI Wave 1 individual microdata under an approved Data Use Agreement (DUA).
2. **Phenotype Stratification:**
   Introduce distinct hypertensive phenotypes in `hypertension.yaml`:
   - Essential Combined Systolic-Diastolic Hypertension ($\text{SBP} \ge 140 \land \text{DBP} \ge 90$).
   - Isolated Systolic Hypertension ($\text{SBP} \ge 140 \land \text{DBP} < 90$), with age-dependent incidence starting at age 55+.
3. **Comorbidity Coupling:**
   Condition treatment resistance and BP control probabilities on comorbid Type 2 Diabetes (`E11.9`) and chronic kidney disease (`I12.9`).

---

## 6. Conclusion & Governance Status

- **Status:** **REVIEW COMPLETED — PARAMETERS UNCHANGED**.
- **Audit Finding:** The existing model produces age-invariant BP sampling within clinical modules.
- **Action Taken:** In accordance with prompt restrictions, parameters have NOT been tweaked to fit fixture values.
- **External Validation Gate:** Remains strictly **`REFERENCE_DATA_PENDING`**.
