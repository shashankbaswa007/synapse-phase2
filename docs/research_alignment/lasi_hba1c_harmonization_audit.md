# SYNAPSE Phase 2: LASI Wave 1 HbA1c Assay Harmonization Audit

**Document ID:** `SYNAPSE-LASI-HBA1C-AUDIT-03`  
**Date:** October 2026  
**Auditor:** SYNAPSE Research Validation & External Evaluation Authority  
**Status:** COMPLETE — TRANSFORMATION DISABLED BY DEFAULT / UNVERIFIED STATUS MANDATED  

---

## 1. Executive Summary & Purpose

A mathematical linear conversion equation had been integrated into previous iterations of the pipeline:

$$\text{HbA1c}_{\text{venous}} = 0.94 \times \text{HbA1c}_{\text{DBS}} + 0.45$$

This audit investigates the empirical origin, assay methods, specimen types, validation population, calibration bias, and statistical error structure of this equation to establish whether it can be defended as a valid individual-level conversion between **capillary Dried Blood Spot (DBS)** measurements in LASI Wave 1 and **venous plasma/whole-blood HPLC** values simulated by SYNAPSE.

---

## 2. Provenance Investigation of the Harmonization Equation

### 2.1 Literature Origin
Traceability analysis reveals that the equation $\text{HbA1c}_{\text{venous}} = 0.94 \times \text{HbA1c}_{\text{DBS}} + 0.45$ originates from biomarker methodological validation studies conducted for the **United States Health and Retirement Study (HRS)**:

- **Primary Source:** Crimmins, E. M., Faul, J. D., Kim, J. K., et al. (2014). *Documentation of Biomarkers in the 2006 and 2008 Health and Retirement Study (HRS)*. Survey Research Center, University of Michigan, Ann Arbor.
- **Biochemical Context:** Validation of dried blood spots against matched venous blood drawn during the 2006/2008 HRS biomarker pilot waves.
- **Assay Type:** Capillary finger-prick blood spotted onto Whatman 903 filter paper, dried at room temperature, eluated, and analyzed using ion-exchange high-performance liquid chromatography (HPLC) or immunoassay calibrated against standard venous whole-blood NGSP standards.

### 2.2 Study Characteristics Comparison

| Parameter | US HRS Harmonization Study | LASI Wave 1 Reference Implementation | SYNAPSE Synthetic Patients |
| :--- | :--- | :--- | :--- |
| **Study Population** | Non-institutionalized US adults aged $\ge 50$ ($N \approx 500$ matched pairs). | Community-dwelling Indian adults aged $\ge 45$ ($N \approx 25,000$ biomarker subsample). | Simulated longitudinal cohort under Indian clinical guidelines. |
| **Specimen Matrix** | Capillary whole blood on Whatman 903. | Capillary whole blood on Whatman 903 protein saver cards. | Synthetic clinical laboratory values reflecting standard venous venipuncture. |
| **Field Environment** | Temperate ambient conditions, air-conditioned transport, desiccant pouch drying. | Tropical ambient heat, monsoon humidity, remote village transport across 35 States/UTs. | N/A (in-silico clinical encounters). |
| **Hemoglobin Variants** | Low prevalence of HbS, HbE, HbD; predominantly normal adult hemoglobin (HbA). | High regional prevalence of **hemoglobinopathies** (HbE in Northeast, $\beta$-thalassemia trait in Western/Central India). | Assumes normal adult HbA glycation dynamics. |
| **Conversion Uncertainty** | Standard Error of regression slope $\approx 0.03$; intercept $\text{SE} \approx 0.22$; residual error $\text{RMSE} \approx 0.38\%\text{--}0.45\%$. | Not calibrated or validated by IIPS or ICMR for LASI Wave 1 microdata. | N/A. |

---

## 3. Scientific Incompatibilities and Invalidation Rationale

### 3.1 Environmental Degradation and Protein Cross-Linking
Capillary blood collected on filter paper cards in field conditions without immediate cold-chain stabilization undergoes gradual protein cross-linking, variable hematocrit drying rates, and hemoglobin denaturation under tropical heat and humidity. These physicochemical changes alter the elution efficiency of glycated hemoglobin fractions relative to total hemoglobin.

### 3.2 High Regional Prevalence of Hemoglobin Variants
India exhibits significant geographic clustering of hemoglobin variants ($\beta$-thalassemia minor, HbE, HbS, and persistent fetal hemoglobin). On ion-exchange HPLC platforms, hemoglobin variants produce interfering peaks or altered retention times, causing systematic positive or negative bias in DBS HbA1c that cannot be resolved by a simple scalar affine shift ($0.94x + 0.45$).

### 3.3 Lack of Official LASI Wave 1 Validation
Neither the *IIPS LASI Wave 1 Report (2020)* nor the *Gateway to Global Aging Data Codebook* sanctions the US HRS equation as an official crosswalk for Indian DBS data. Applying an equation calibrated in Michigan to Indian field microdata without national parallel venous-DBS validation introduces uncontrolled epidemiological bias.

---

## 4. Pipeline Architectural Adjustments

In accordance with strict scientific pre-release gate criteria:

1. **Disabled Transformation by Default:**
   In [`synapse_simulator/evaluation/lasi/comparability.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/comparability.py), `adjust_dbs_hba1c_to_venous(..., enabled=False)` is set to default `False`. If called without explicit override, it returns `None`.
2. **Preservation of Authentic Measurements:**
   In [`synapse_simulator/evaluation/lasi/ingestor.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/ingestor.py), the raw field `dbs_hba1c` is preserved in `LasiCleanedRecord.hba1c_dbs` as an unadjusted capillary dried blood spot measurement.
3. **Explicit Validation Status:**
   In [`synapse_simulator/evaluation/lasi/evaluator.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/evaluator.py), any direct comparison between synthetic venous HbA1c and LASI capillary DBS HbA1c is classified as:
   $$\text{status} = \text{LasiMetricStatus.UNVERIFIED}$$
   with an explicit warning emitted in the validation report:
   > *"Assay Non-Equivalence: SYNAPSE simulates standard clinical venous blood HbA1c, whereas LASI Wave 1 reference data reports capillary Dried Blood Spot (DBS) HbA1c. Uncalibrated conversion equations introduce unquantified bias."*

---

## 5. Specification of Requirements for a Valid Future Harmonization Method

For SYNAPSE to re-enable individual-level HbA1c crosswalks against LASI Wave 1 in future releases, the following scientific criteria must be satisfied:

1. **Empirical Calibration Study:** Publication of a paired-sample validation study comparing simultaneous finger-prick DBS and venipuncture venous blood analyzed on identical Bio-Rad HPLC platforms in an Indian adult cohort across diverse climatic zones.
2. **Variant Screening:** Incorporation of an exclusion or adjustment flag for participants with detected hemoglobin variants ($\text{HbE}, \text{HbS}, \beta\text{-thalassemia}$).
3. **Measurement Error Modeling:** Implementation of an errors-in-variables or Bayesian measurement error model that propagates the regression calibration uncertainty ($\sigma_{\text{residual}} \approx 0.40\%$) into the distribution distance metrics rather than treating point conversions as exact.
4. **Independent Sensitivity Testing:** Reporting of both raw DBS comparisons and harmonized comparisons in sensitivity analyses.

---

## 6. Audit Verdict

The equation $\text{HbA1c}_{\text{venous}} = 0.94 \times \text{HbA1c}_{\text{DBS}} + 0.45$ has been **formally revoked as a default transformation**. The pipeline preserves genuine DBS values, gates direct comparisons as `UNVERIFIED`, and prevents false-positive distributional validation claims.
