# Updated Test Suite Coverage and Execution Results

**Execution Command:** `.venv/bin/python -m pytest tests -v -p no:cacheprovider`  
**Execution Timestamp:** October 2026  
**Total Tests:** **154 Passed (0 Failed, 0 Skipped, 0 Warnings)**  
**Execution Time:** **7.48 Seconds**  

---

## 1. Test Suite Architecture and Acceptance Layers

The SYNAPSE Phase 2 test suite enforces validation across three distinct layers:
1. **Layer 1: Structural & Causal Correctness Tests:** Enforces referential integrity, schema compliance, temporal ordering, and clinical safety invariants.
2. **Layer 2: Statistical Fidelity Tests:** Validates demographic distributions, disease prevalences, comorbidity odds ratios, and non-conflated acute attack rates.
3. **Layer 3: Clinical & Longitudinal Plausibility Tests:** Audits treatment guideline conformance, surveillance intervals, and actuarial mortality plausibility.

---

## 2. Detailed Breakdown of Newly Implemented Unit & Integration Tests

Three new test cases were added to `tests/test_evaluation_framework.py` to continuously verify the model audit corrections:

### 1. `test_baseline_vs_period_prevalence_breakdown`
- **Objective:** Verifies that `DatasetEvaluator` properly isolates baseline point cases ($t=0$) from cumulative period cases ($t \in [0, 2\text{ yrs}]$).
- **Mechanism:** Constructs a mock dataset with 10 adult patients, 2 baseline diagnoses at Day 5, and 2 incident diagnoses at Day 180.
- **Verification Assertions:**
  - Cumulative period prevalence is asserted to be $4 / 10 = 40.0\%$.
  - Baseline point cases isolated in `acceptance_threshold["baseline_point_cases"]` is asserted to be $2 / 10 = 20.0\%$.
  - Incident cases is asserted to be $2$ ($20.0\%$).
- **Status:** **PASSED.**

### 2. `test_background_life_table_mortality_and_invariants`
- **Objective:** Verifies that `ExperimentRunner` with `enable_background_mortality=True` produces expected life-table deaths and maintains strictly zero post-mortem events.
- **Mechanism:** Executes a 50-patient simulation over 24 months, generates `deaths.csv`, and executes full evaluation.
- **Verification Assertions:**
  - `report.invariants_passed` is strictly `True`.
  - `inv_no_event_post_mortem` records strictly $0$ violations.
  - `deaths.csv` is confirmed to exist and contain valid relational headers.
- **Status:** **PASSED.**

### 3. `test_treatment_rule_conformance_labeling`
- **Objective:** Verifies that pharmacotherapy metrics are formally labeled as rule conformance rather than real-world prescribing fidelity.
- **Mechanism:** Evaluates an exported synthetic dataset and inspects treatment metric metadata.
- **Verification Assertions:**
  - `metric_name` contains `"Rule Conformance"`.
  - `known_limitations` explicitly cites `"real-world"` Indian prescribing benchmarks (~45–65%).
- **Status:** **PASSED.**

---

## 3. Complete Test Execution Log Summary (154 Tests)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-8.3.3
rootdir: /Users/shashi/synapse/synapse-phase2
configfile: pyproject.toml

tests/test_audit_trail.py::test_audit_event_logging PASSED                [  0%]
tests/test_audit_trail.py::test_audit_trail_integrity PASSED             [  1%]
tests/test_clinical_modules.py::test_load_all_three_clinical_modules PASSED [  1%]
tests/test_clinical_modules.py::test_evaluator_guard_conditions PASSED   [  2%]
tests/test_clinical_modules.py::test_module_runner_single_step PASSED    [  3%]
tests/test_clinical_modules.py::test_module_runner_delays PASSED         [  3%]
tests/test_clinical_modules.py::test_module_terminal_state PASSED        [  4%]
tests/test_clinical_modules.py::test_patient_seed_derivation_deterministic PASSED [  5%]
tests/test_clinical_modules.py::test_end_to_end_module_runner_progression PASSED [  5%]
tests/test_determinism.py::test_two_cohorts_same_seed_are_byte_identical PASSED [  6%]
tests/test_determinism.py::test_two_cohorts_different_seeds_diverge PASSED [  7%]
tests/test_end_to_end_acceptance.py::test_deterministic_reproducibility PASSED [  7%]
tests/test_end_to_end_acceptance.py::test_cross_seed_stochastic_variation PASSED [  8%]
tests/test_end_to_end_acceptance.py::test_population_fidelity_under_scale PASSED [  9%]
tests/test_end_to_end_acceptance.py::test_longitudinal_clinical_integrity PASSED [  9%]
tests/test_end_to_end_acceptance.py::test_mandatory_temporal_ordering PASSED [ 10%]
tests/test_end_to_end_acceptance.py::test_unbroken_causal_chains PASSED   [ 11%]
tests/test_end_to_end_acceptance.py::test_deceased_patients_cease_clinical_activity PASSED [ 11%]
tests/test_end_to_end_acceptance.py::test_allergy_safety_veto_unbypassable PASSED [ 12%]
tests/test_end_to_end_acceptance.py::test_backward_compatible_csv_schemas PASSED [ 13%]
tests/test_end_to_end_acceptance.py::test_tier1_structural_failure_blocks_dataset PASSED [ 13%]
tests/test_end_to_end_acceptance.py::test_tier2_statistical_distinguishes_verified_from_unverified PASSED [ 14%]
tests/test_end_to_end_acceptance.py::test_operational_scenarios_still_functional PASSED [ 14%]
tests/test_end_to_end_acceptance.py::test_linear_scaling_and_benchmark_timing PASSED [ 15%]
tests/test_evaluation_framework.py::test_wilson_score_interval_hand_calculated PASSED [ 16%]
tests/test_evaluation_framework.py::test_jensen_shannon_divergence_math PASSED [ 16%]
tests/test_evaluation_framework.py::test_total_variation_distance_math PASSED [ 17%]
tests/test_evaluation_framework.py::test_chi_square_pooling_math PASSED   [ 18%]
tests/test_evaluation_framework.py::test_cramers_v_math PASSED            [ 18%]
tests/test_evaluation_framework.py::test_odds_ratio_and_ci_math PASSED   [ 19%]
tests/test_evaluation_framework.py::test_comorbidity_oe_ratio_math PASSED [ 20%]
tests/test_evaluation_framework.py::test_evaluator_invariants_pass_on_clean_data PASSED [ 20%]
tests/test_evaluation_framework.py::test_evaluator_invariant_fails_on_event_pre_birth PASSED [ 21%]
tests/test_evaluation_framework.py::test_evaluator_invariant_fails_on_post_mortem_encounter PASSED [ 22%]
tests/test_evaluation_framework.py::test_evaluator_invariant_fails_on_dangling_encounter PASSED [ 22%]
tests/test_evaluation_framework.py::test_evaluator_invariant_fails_on_allergy_contraindication PASSED [ 23%]
tests/test_evaluation_framework.py::test_demographic_sex_ratio_evaluation PASSED [ 24%]
tests/test_evaluation_framework.py::test_demographic_age_pyramid_jsd_evaluation PASSED [ 24%]
tests/test_evaluation_framework.py::test_disease_prevalence_adult_denominator_filtering PASSED [ 25%]
tests/test_evaluation_framework.py::test_comorbidity_odds_ratio_and_conditional_prevalence PASSED [ 26%]
tests/test_evaluation_framework.py::test_longitudinal_encounters_per_pt_year PASSED [ 26%]
tests/test_evaluation_framework.py::test_treatment_patterns_and_adherence_disclosure PASSED [ 27%]
tests/test_evaluation_framework.py::test_evaluator_empty_and_single_patient PASSED [ 27%]
tests/test_evaluation_framework.py::test_experiment_runner_manifest_generation PASSED [ 28%]
tests/test_evaluation_framework.py::test_multi_seed_monte_carlo_execution PASSED [ 29%]
tests/test_evaluation_framework.py::test_baseline_and_incident_separation_in_runner PASSED [ 29%]
tests/test_evaluation_framework.py::test_timestep_dependent_incidence_probability_conversion PASSED [ 30%]
tests/test_evaluation_framework.py::test_point_prevalence_vs_cumulative_attack_rate_distinction PASSED [ 31%]
tests/test_evaluation_framework.py::test_held_out_data_isolation PASSED   [ 31%]
tests/test_evaluation_framework.py::test_baseline_vs_period_prevalence_breakdown PASSED [ 32%]
tests/test_evaluation_framework.py::test_background_life_table_mortality_and_invariants PASSED [ 33%]
tests/test_evaluation_framework.py::test_treatment_rule_conformance_labeling PASSED [ 33%]
... [102 additional tests across scenarios, rules, hospital generators, and departments] ...

============================= 154 passed in 7.48s ==============================
```
