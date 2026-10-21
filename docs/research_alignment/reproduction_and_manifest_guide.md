# Reproduction Guide and Machine-Readable Experiment Artifacts

**Target Platform:** SYNAPSE Phase 2 Synthetic Healthcare Data Generator & Evaluator  
**Prerequisites:** Python 3.11+, Virtual Environment `.venv` activated  

---

## 1. Reproduction Commands Quick-Reference

### 1.1 Run Full Regression & Invariant Test Suite (154 Tests)
```bash
.venv/bin/python -m pytest tests -v -p no:cacheprovider
```

### 1.2 Evaluate an Existing Exported CSV Dataset Independently
```bash
.venv/bin/python evaluate_dataset.py \
    --dataset-dir data/evaluation/test_calibrated_500 \
    --profile config/population/india_default_v1.yaml
```

### 1.3 Run a Single Cohort Experiment with Execution Manifest
```bash
.venv/bin/python run_evaluation_experiment.py \
    --patients 500 \
    --seed 42 \
    --output-dir data/experiments/audit_reproduction_n500
```

### 1.4 Run Multi-Seed Monte Carlo Experiment (10 Seeds)
```bash
.venv/bin/python run_evaluation_experiment.py \
    --patients 500 \
    --seeds 42,101,202,303,404,505,606,707,808,909 \
    --output-dir data/experiments/audit_reproduction_mc500
```

---

## 2. Machine-Readable Experiment Artifact Schemas

Every simulation run produces standardized, auditable JSON manifests.

### 2.1 Execution Manifest (`RUN_MANIFEST.json`)
Recorded in the output directory of every single run:
```json
{
  "manifest_version": "1.0.0",
  "run_id": "exp-seed42-n500-1792575020",
  "timestamp": "2026-10-21T15:20:00.123456",
  "git_commit": "3e3ae1d28286e9106659f68aa053465ded9bb3c2",
  "configuration": {
    "cohort_size": 500,
    "seed": 42,
    "observation_start": "2024-01-01T00:00:00",
    "observation_end": "2026-01-01T00:00:00",
    "timestep_days": 7,
    "profile_path": "config/population/india_default_v1.yaml",
    "output_dir": "data/evaluation/test_calibrated_500"
  },
  "performance_telemetry": {
    "simulation_seconds": 1.245,
    "export_seconds": 0.312,
    "total_generation_seconds": 1.557,
    "total_actions_emitted": 3840,
    "exported_file_count": 16,
    "peak_memory_mb": 42.15,
    "evaluation_seconds": 0.128
  },
  "evaluation_verdict": {
    "overall_status": "WARNING",
    "invariants_passed": true,
    "total_metrics": 18,
    "passed_metrics": 16,
    "warning_metrics": 1,
    "failed_metrics": 0,
    "unverified_metrics": 1
  }
}
```

### 2.2 Independent Evaluation Report (`EVALUATION_REPORT.json`)
Contains quantitative telemetry for all 18 metrics:
```json
{
  "dataset_directory": "/Users/shashi/synapse/synapse-phase2/data/evaluation/test_calibrated_500",
  "timestamp": "2026-10-21T15:20:01.000000",
  "total_metrics": 18,
  "passed_metrics": 16,
  "warning_metrics": 1,
  "failed_metrics": 0,
  "unverified_metrics": 1,
  "not_applicable_metrics": 0,
  "overall_status": "WARNING",
  "invariants_passed": true,
  "metrics": [
    {
      "metric_id": "prev_hypertension_adults",
      "metric_name": "Disease Prevalence: Essential Hypertension (Adults >= 20)",
      "dimension": "PREVALENCE",
      "definition": "Prevalence of essential hypertension (I10) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.",
      "numerator": 134,
      "denominator": 341,
      "synthetic_estimate": 39.3,
      "reference_estimate": 30.7,
      "difference": 8.6,
      "relative_difference": 0.2801,
      "confidence_interval": [34.26, 44.57],
      "acceptance_threshold": {
        "pass_abs_diff_max": 8.0,
        "warning_abs_diff_max": 15.0,
        "crude_cohort_cases": 134,
        "crude_cohort_prevalence_pct": 26.8,
        "baseline_point_cases": 119,
        "baseline_point_prevalence_pct": 34.9,
        "incident_cases": 15,
        "incident_attack_rate_pct": 4.4
      },
      "status": "WARNING",
      "provenance_id": "ICMR_INDIAB_2023_HTN",
      "verification_status": "VERIFIED",
      "known_limitations": "Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold."
    }
  ]
}
```

### 2.3 Multi-Seed Monte Carlo Summary (`MULTI_SEED_EXPERIMENT_SUMMARY.json`)
Preserves distribution statistics across seeds:
```json
{
  "cohort_size": 500,
  "seed_count": 10,
  "seeds": [42, 101, 202, 303, 404, 505, 606, 707, 808, 909],
  "timestamp": "2026-10-21T15:37:40.000000",
  "metrics_summary": {
    "prev_hypertension_adults": {
      "metric_id": "prev_hypertension_adults",
      "metric_name": "Disease Prevalence: Essential Hypertension (Adults >= 20)",
      "reference_estimate": 30.7,
      "mean": 35.90,
      "std_dev": 1.74,
      "mc_standard_error": 0.55,
      "min": 32.94,
      "max": 39.30,
      "estimated_bias": 5.20
    },
    "comorb_htn_in_t2d": {
      "metric_id": "comorb_htn_in_t2d",
      "metric_name": "Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes",
      "reference_estimate": 50.1,
      "mean": 50.17,
      "std_dev": 5.91,
      "mc_standard_error": 1.87,
      "min": 40.74,
      "max": 58.70,
      "estimated_bias": 0.07
    }
  }
}
```

---

## 3. Directory Layout of Verified Experiment Datasets

```
data/
├── evaluation/
│   ├── test_calibrated_100/       # N=100 Single Run (Seed 42)
│   ├── test_calibrated_500/       # N=500 Single Run (Seed 42)
│   └── calibrated_mc_500/         # N=100 Monte Carlo Baseline (Seeds: 42, 101, 202, 303, 404)
└── experiments/
    └── comprehensive_audit/       # Expanded Audit Experiments
        ├── mc_n100/               # N=100 (10 Seeds)
        ├── mc_n250/               # N=250 (10 Seeds)
        ├── mc_n500/               # N=500 (10 Seeds)
        ├── n1000_s42/             # N=1000 Scale Test (Seed 42)
        ├── AGGREGATED_MC_AUDIT.json
        └── sensitivity_duration/  # 12, 24, 36 Month Horizon Sweeps
            ├── 12_months/
            ├── 24_months/
            ├── 36_months/
            └── DURATION_SENSITIVITY.json
```
