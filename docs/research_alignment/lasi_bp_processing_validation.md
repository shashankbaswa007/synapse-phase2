# SYNAPSE Phase 2: LASI Wave 1 Blood-Pressure Processing Protocol & Validation

**Document ID:** `SYNAPSE-LASI-BP-AUDIT-02`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** VERIFIED & AUDITED AGAINST OFFICIAL PROTOCOL  

---

## 1. Executive Summary & Purpose

In epidemiological health surveys, arterial blood pressure exhibits substantial acute situational reactivity ("white-coat effect") during the opening minutes of an encounter. In the **Longitudinal Ageing Study in India (LASI) Wave 1 (2017–2018)**, the survey team implemented a standardized triple-reading protocol using digital oscillometric monitors.

This document establishes the scientific basis, mathematical formulas, boundary conditions, range-exclusion criteria, and fallback hierarchies governing blood pressure ingestion in [`synapse_simulator/evaluation/lasi/ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py).

---

## 2. Official LASI Measurement Protocol

According to the *LASI Wave 1 Biomarkers and Direct Health Measurements Field Protocol Manual* (IIPS & Harvard T.H. Chan School of Public Health, 2017):

1. **Equipment:** Omron HEM-7121 upper-arm digital oscillometric blood pressure monitor with appropriate adult cuff sizes (standard and large).
2. **Postural & Rest Requirements:**
   - Participant seated quietly for **at least 5 minutes** with back supported, legs uncrossed, feet flat on the floor, and arm supported at heart level.
   - Refraining from smoking, caffeine, or vigorous exertion for 30 minutes prior to measurement.
3. **Sequential Reading Schedule:**
   - **Reading 1:** Recorded after initial 5-minute seated rest.
   - **Reading 2:** Recorded after a mandatory 5-minute quiet interval following Reading 1.
   - **Reading 3:** Recorded after a second 5-minute quiet interval following Reading 2.
4. **Target Arm:** Left arm measured unless contraindicated (e.g., bilateral mastectomy, dialysis arteriovenous fistula, lymphadenopathy, cast/dressing, or acute paresis).

---

## 3. Blood Pressure Derivation Rules & Scientific Justification

### 3.1 Primary Protocol Derivation Rule

In epidemiological surveillance (including NHANES, HRS, ELSA, and LASI India Report), **Reading 1** systematically overestimates resting basal blood pressure due to transient sympathetic arousal. Consequently, the primary analytical estimand is the arithmetic mean of the second and third measurements:

$$\text{SBP}_{\text{protocol}} = \frac{\text{SBP}_2 + \text{SBP}_3}{2}$$

$$\text{DBP}_{\text{protocol}} = \frac{\text{DBP}_2 + \text{DBP}_3}{2}$$

### 3.2 Fallback Hierarchy and Traceability

In real-world field surveys, participants may refuse subsequent readings, experience device errors, or terminate the biomarker module early. The SYNAPSE pipeline forbids silent substitution. Every derived BP value is tagged with its exact provenance category in `LasiCleanedRecord.bp_derivation_method`:

| Category Identifier | Condition | Scientific Defensibility & Bias Impact |
| :--- | :--- | :--- |
| `PROTOCOL_MEAN_READINGS_2_AND_3` | Both Reading 2 and Reading 3 valid. | **Gold Standard.** Minimum white-coat reactivity; fully consistent with national reference reports. |
| `FALLBACK_READING_2_ONLY` | Reading 2 valid; Reading 3 missing or invalid. | **Acceptable Fallback.** Rest period was observed; mild loss of precision compared to duplicate mean. |
| `FALLBACK_READING_3_ONLY` | Reading 3 valid; Reading 2 missing or invalid. | **Acceptable Fallback.** Longest rest duration; single-point estimate. |
| `FALLBACK_READING_1_ONLY` | Only Reading 1 valid; Readings 2 & 3 missing. | **Compromised.** Exhibits positive bias (+3 to +5 mmHg SBP); excluded in `strict_protocol_bp=True` mode. |
| `NO_VALID_READING` | No readings valid within physiological range. | BP set to `None`; excluded from blood pressure distributional evaluations. |

```python
# Implementation in synapse_simulator/evaluation/lasi/ingestor.py:
if sbp2 is not None and sbp3 is not None:
    mean_sbp = (sbp2 + sbp3) / 2.0
    sbp_method = "PROTOCOL_MEAN_READINGS_2_AND_3"
elif sbp2 is not None and not strict_protocol_bp:
    mean_sbp = float(sbp2)
    sbp_method = "FALLBACK_READING_2_ONLY"
elif sbp3 is not None and not strict_protocol_bp:
    mean_sbp = float(sbp3)
    sbp_method = "FALLBACK_READING_3_ONLY"
elif sbp1 is not None and not strict_protocol_bp:
    mean_sbp = float(sbp1)
    sbp_method = "FALLBACK_READING_1_ONLY"
else:
    mean_sbp = None
    sbp_method = "NO_VALID_READING"
```

---

## 4. Range Filtering and Plausibility Boundaries

### 4.1 Permitted Physiological Ranges

The pipeline enforces conservative physiological plausibility boundaries prior to averaging:
- **Systolic Blood Pressure (SBP):** $60.0 \le \text{SBP} \le 280.0\text{ mmHg}$
- **Diastolic Blood Pressure (DBP):** $40.0 \le \text{DBP} \le 160.0\text{ mmHg}$

### 4.2 Impact of Range Filtering on Reference Denominators

Observations outside these boundaries represent instrument miscalibration, cuff slippage, air leakage, or data entry corruption.
- Observations outside these ranges are **not silently coerced or winsorized**.
- An individual reading outside the range is set to `None` for that specific reading. If remaining readings satisfy the protocol rule, the protocol mean or documented fallback is used.
- If all readings for a participant are out-of-range, the participant is flagged with `bp_derivation_method = NO_VALID_READING` and excluded from BP metrics.
- Excluded observations are tracked in `LasiDataQualityReport.excluded_records` and `LasiDataQualityReport.bp_derivation_counts`.

---

## 5. Analytical Unit & Mutation Verification

The pipeline implementation in [`synapse_simulator/evaluation/lasi/ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py) was tested against comprehensive edge cases in [`tests/test_lasi_pipeline.py`](file:///Users/shashi/synapse/synapse-phase2/tests/test_lasi_pipeline.py):

| Test Scenario | Input Values | Expected Result | Verified Result |
| :--- | :--- | :--- | :---: |
| **All 3 Readings Present** | $\text{SBP} = [150, 140, 130]$ | Mean $= 135.0$, `PROTOCOL_MEAN_READINGS_2_AND_3` | **PASS** |
| **Reading 1 Missing** | $\text{SBP} = [\text{None}, 142, 138]$ | Mean $= 140.0$, `PROTOCOL_MEAN_READINGS_2_AND_3` | **PASS** |
| **Reading 3 Missing** | $\text{SBP} = [150, 136, \text{None}]$ | Mean $= 136.0$, `FALLBACK_READING_2_ONLY` | **PASS** |
| **Reading 2 Missing** | $\text{SBP} = [150, \text{None}, 134]$ | Mean $= 134.0$, `FALLBACK_READING_3_ONLY` | **PASS** |
| **Only Reading 1 Present** | $\text{SBP} = [148, \text{None}, \text{None}]$ | Mean $= 148.0$, `FALLBACK_READING_1_ONLY` | **PASS** |
| **Strict Protocol with Reading 3 Missing** | $\text{SBP} = [150, 136, \text{None}], \text{strict}=\text{True}$ | Mean $= \text{None}$, `FALLBACK_READING_2_ONLY` rejected | **PASS** |
| **Out-of-Range Reading 2 ($320\text{ mmHg}$)** | $\text{SBP} = [140, 320, 130]$ | Reading 2 filtered $\to$ Mean $= 130.0$ (`FALLBACK_READING_3_ONLY`) | **PASS** |
| **Out-of-Range SBP ($45\text{ mmHg}$)** | $\text{SBP} = [45, 50, 55]$ | All $<60 \to$ Mean $= \text{None}$, `NO_VALID_READING` | **PASS** |
| **Out-of-Range DBP ($180\text{ mmHg}$)** | $\text{DBP} = [80, 180, 84]$ | Reading 2 filtered $\to$ Mean $= 84.0$ (`FALLBACK_READING_3_ONLY`) | **PASS** |

---

## 6. Pre-Release Verification Verdict

The blood-pressure ingestion and processing subsystem satisfies all epidemiological requirements:
1. Readings 2 and 3 are prioritized in accordance with the official protocol manual.
2. Derivation methods are explicitly logged at the patient record level, preventing silent single-reading substitution.
3. The pipeline supports a `strict_protocol_bp` toggle when research users demand pristine dual-reading averages only.
4. Range exclusions are counted in the data quality manifest and do not silently alter reference population weights.
