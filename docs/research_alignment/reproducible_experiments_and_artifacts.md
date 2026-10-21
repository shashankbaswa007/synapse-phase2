# Reproducible Experiments and Machine-Readable Artifacts Guide

**Document ID:** `SYNAPSE-AUDIT-DELIV-07`  
**Date:** October 2026  
**Auditor:** SYNAPSE Longitudinal Credibility & Statistical Validation Team  
**Focus Area:** CLI Commands, JSON Schemas, Machine-Readable Manifests, Git Hashing, and Multi-Seed Reproducibility  

---

## 1. CLI Commands for Complete Experiment Reproduction

All longitudinal trajectory experiments and evaluation reports can be reproduced deterministically using standard Python CLI tools.

### 1.1 Execute the Automated Regression Test Suite
```bash
# Run the complete 171-test regression and mutation suite
.venv/bin/pytest tests/ -v
```

### 1.2 Execute Multi-Scale Multi-Seed Trajectory Experiment (15 Runs)
```bash
# Executes 5 seeds (42, 101, 202, 303, 404) across N=100, 250, 500
# Updates data/experiments/longitudinal_trajectories/LONGITUDINAL_TRAJECTORY_AUDIT.json
.venv/bin/python scripts/run_longitudinal_audit.py
```

### 1.3 Execute Single-Cohort Controlled Trajectory Experiment
```bash
# Run a single 500-patient cohort with seed 42
.venv/bin/python run_evaluation_experiment.py \
  --patients 500 \
  --seed 42 \
  --output-dir data/experiments/trajectory_single_500 \
  --profile config/population/india_default_v1.yaml
```

### 1.4 Standalone Independent CSV Evaluation
```bash
# Evaluate an existing exported dataset independently directly from CSV files
.venv/bin/python evaluate_dataset.py \
  --data-dir data/experiments/longitudinal_trajectories/n500_s42 \
  --reference config/population/india_default_v1.yaml \
  --output-json data/experiments/longitudinal_trajectories/n500_s42/INDEPENDENT_EVALUATION.json
```

---

## 2. Machine-Readable Experiment Artifacts

All empirical runs from this audit are preserved in:
`data/experiments/longitudinal_trajectories/`

### 2.1 File Directory Layout
```
data/experiments/longitudinal_trajectories/
├── LONGITUDINAL_TRAJECTORY_AUDIT.json      <- Aggregated multi-scale Monte Carlo summary
├── n100_s42/ ... n100_s404/                <- Cohort of 100 runs (Seeds 42, 101, 202, 303, 404)
│   ├── RUN_MANIFEST.json                   <- Execution parameters, Git commit, duration
│   ├── EVALUATION_REPORT.json              <- Full 20-metric evaluation report
│   ├── EVALUATION_REPORT.md                <- Markdown formatted report
│   ├── patients.csv, encounters.csv, ...   <- 16 exported longitudinal CSV tables
├── n250_s42/ ... n250_s404/                <- Cohort of 250 runs
└── n500_s42/ ... n500_s404/                <- Cohort of 500 runs
```

### 2.2 Schema of `LONGITUDINAL_TRAJECTORY_AUDIT.json`
```json
{
  "n500": {
    "cohort_size": 500,
    "seeds": [42, 101, 202, 303, 404],
    "runs": [
      {
        "seed": 42,
        "cohort_size": 500,
        "invariants_passed": true,
        "elapsed_seconds": 0.98,
        "metrics": {
          "long_encounters_per_pt_year": 1.11,
          "long_inter_encounter_interval_days": 132.8,
          "long_crude_mortality_rate": 0.02038,
          "long_deaths_count": 20,
          "long_censored_pt_years": 981.3,
          "long_treatment_intensification_rate": 0.7516,
          "long_chronic_complication_rate": 0.0373,
          "prev_htn_baseline": 35.19,
          "prev_htn_period": 41.35,
          "prev_t2d_adults": 11.44
        },
        "diagnostics": {
          "cause_breakdown": { "R99": 20 },
          "htn_intensified_pct": 74.5,
          "t2d_intensified_pct": 77.8,
          "person_years_lost_to_death": 4.33
        }
      }
    ],
    "summary": {
      "long_deaths_count": { "mean": 14.8, "std": 5.2154, "min": 10, "max": 20 },
      "long_censored_pt_years": { "mean": 986.9, "std": 4.887, "min": 981.3, "max": 991.5 },
      "long_treatment_intensification_rate": { "mean": 0.7972, "std": 0.0378, "min": 0.7516, "max": 0.8409 },
      "long_chronic_complication_rate": { "mean": 0.0308, "std": 0.0143, "min": 0.0075, "max": 0.0408 }
    }
  }
}
```

### 2.3 Environmental Provenance and Git Lineage
- **Repository Commit:** `3e3ae1d`
- **Python Environment:** Python 3.11.5 (`.venv/bin/python`)
- **Core Dependencies:** `pytest==9.1.1`, `pydantic>=2.0`, `pyyaml>=6.0`, `faker>=40.0`
- **Output Determinism:** Identical seeds produce bitwise-identical CSV file outputs and identical SHA-256 hashes across independent runs.
