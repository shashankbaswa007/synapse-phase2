# SYNAPSE Phase 2 — Synthea-Inspired Longitudinal Synthetic Healthcare Simulation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-374%20passed-brightgreen.svg)](tests/)
[![Dataset Status](https://img.shields.io/badge/canonical%20cohort-10%2C000%20patients-success.svg)](data/synthetic/)
[![Validation Gate](https://img.shields.io/badge/validation%20gate-REFERENCE__DATA__PENDING-amber.svg)](docs/research_alignment/external_validation_contract.md)

**SYNAPSE Phase 2** delivers an agentic, Synthea-inspired longitudinal population healthcare simulation system tailored to Indian demographic, clinical, and epidemiological characteristics. The platform simulates continuous synthetic patient lifespans, chronic disease progression (hypertension, type 2 diabetes mellitus, acute URTI), clinical outpatient encounters, stepped-care treatment regimens, continuous hemodynamics, background all-cause life-table mortality, and standardized community blood pressure surveys.

---

## 1. Canonical System Architecture

The active, authoritative implementation of SYNAPSE Phase 2 follows an integrated 7-stage longitudinal simulation pipeline:

```
generate_synthetic_data.py (default: --mode longitudinal)
       │
       ▼
ExperimentRunner.generate_cohort()
       │
       ├─► [1] Demographic Population Sampling ────► Census SRS 2021 India Profiles
       ├─► [2] Disease Progression State Machines ──► YAML State Machines (config/modules/)
       │         • Essential Hypertension (hypertension.yaml)
       │         • Type 2 Diabetes Mellitus (diabetes_t2.yaml)
       │         • Acute URTI (urti.yaml)
       ├─► [3] Background All-Cause Mortality ──────► Census SRS 2016–2020 Life Tables
       ├─► [4] Continuous Hemodynamic Engine ───────► LEGACY_CONDITIONAL (default) / FORWARD_STATE_SPACE
       ├─► [5] Independent Community Survey ────────► LASI_WAVE1_TRI_MEASUREMENT v1.0.0
       └─► [6] Normalized Relational CSV Export ────► CSVExporter (18 Relational Tables)
                 │
                 ▼
       DatasetAuditor & DatasetEvaluator
                 │
                 ▼
       DatasetValidationGate (Fail-fast promotion)
                 │
                 ▼
       Published Dataset (data/synthetic/) + RUN_MANIFEST.json + DATASET_MANIFEST.json
```

### 1.1 Key Architectural Highlights
* **Primary Entry Point:** [`generate_synthetic_data.py`](file:///Users/shashi/synapse/synapse-phase2/generate_synthetic_data.py) (default mode: `longitudinal`).
* **Canonical Release Cohort:** [`data/synthetic/`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/) ($N=10,000$ patients, random seed `42`, 720-day observation window, 7-day timestep).
* **Disease Progression:** Declarative YAML state machines in [`config/modules/`](file:///Users/shashi/synapse/synapse-phase2/config/modules/) modeling chronic progression, treatment escalation, microvascular complications, and symptom expression.
* **Dual Hemodynamics:**
  - `LEGACY_CONDITIONAL` (default): Robust conditional Gaussian distributions conditioned on age, sex, BMI, and disease status.
  - `FORWARD_STATE_SPACE` (experimental opt-in): Continuous stochastic differential state-space modeling vascular resistance and treatment response.
* **Community Survey Protocol:** `LASI_WAVE1_TRI_MEASUREMENT` v1.0.0 captures independent household triplicate blood pressure readings for older adults ($\text{age} \ge 45$), strictly decoupled from hospital EHR visits and demonstrating the authentic $-3.45\text{ mmHg}$ habituation drop.
* **Validation & Integrity:** Zero primary-key collisions, zero dangling foreign keys, zero pre-birth or post-mortem violations, zero allergy contraindications, and 16 passing clinical acceptance metrics.
* **External Validation Gate:** Formally locked at `REFERENCE_DATA_PENDING` under strict research data governance.

---

## 2. Quickstart & Execution Commands

### 2.1 Generate Synthetic Data
```bash
# Generate the canonical 10,000-patient longitudinal dataset (default mode: longitudinal)
python generate_synthetic_data.py --patients 10000 --seed 42 --days 720 --timestep 7 --output-dir data/synthetic

# Generate experimental cohort with forward state-space hemodynamics
python generate_synthetic_data.py --patients 1000 --seed 42 --hemodynamic-mode FORWARD_STATE_SPACE --output-dir data/experiments/forward_1000
```

### 2.2 Evaluate an Exported Dataset
```bash
# Run independent evaluation on exported CSV directory against real-world benchmarks
python evaluate_dataset.py --dataset-dir data/synthetic
```

### 2.3 Run Controlled Experiments & Monte Carlo Sweeps
```bash
# Single cohort experiment
python run_evaluation_experiment.py --patients 100 --seed 42 --output-dir data/experiments/run_100

# Multi-seed Monte Carlo sweep (evaluating sampling variance vs model bias)
python run_evaluation_experiment.py --patients 250 --seeds 42,101,202,303,404 --output-dir data/experiments/mc_250
```

### 2.4 Run the Automated Test Suite
```bash
# Execute the complete regression test suite (374 tests)
pytest tests/
```

---

## 3. Repository Structure

```
synapse-phase2/
├── generate_synthetic_data.py   # Primary CLI entry point (default: --mode longitudinal)
├── evaluate_dataset.py          # Standalone independent dataset evaluator
├── run_evaluation_experiment.py # Controlled experiment runner & Monte Carlo harness
├── PHASE_2_FINAL_VERIFICATION.md# Definitive Phase 2 acceptance report
├── config/
│   ├── modules/                 # Canonical disease state machines (HTN, T2D, URTI)
│   ├── population/              # Census SRS 2021 India population profile
│   └── knowledge/               # Curated medical knowledge & PubMed configs
├── data/
│   ├── synthetic/               # Canonical release dataset (10,000 cohort, seed 42)
│   ├── experiments/             # Multi-seed experiment outputs and benchmarks
│   └── evaluation/              # Reference fixtures and test suites
├── docs/
│   ├── architecture/            # Primary system architecture documentation
│   │   ├── README.md            # Architecture index
│   │   ├── longitudinal_system_architecture.md # Definitive longitudinal specification
│   │   └── legacy_hospital_prototype/          # Historical LLD archive (mode=hospital)
│   └── research_alignment/      # 114 specialized research, survey, & variance reports
├── output/                      # Published deliverables, reports, and vector visualizations
│   ├── README.md                # Deliverables directory catalog
│   ├── SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md # Full system report
│   ├── CLINICAL_EVALUATION_REPORT.md                # 21-metric evaluation report
│   ├── LONGITUDINAL_COHORT_SUMMARY_10000.md         # Cohort summary table
│   └── visualizations/          # Publication-grade SVG vector charts
├── synapse_simulator/           # Core simulation packages
│   ├── evaluation/              # Evaluator, metrics, experiment runner, LASI pipeline
│   ├── modules/                 # State machine engine, loader, and evaluators
│   ├── population/              # Population profiles and demographic samplers
│   ├── datagen/                 # Patient generators, community assessment, forward hemodynamics
│   ├── validation/              # DatasetAuditor, IntegrityAuditor, DatasetValidationGate
│   ├── exporter/                # CSVExporter (relational serialization)
│   └── generator/               # Orchestrator & legacy hospital compatibility factory
└── tests/                       # 374 automated regression and validation tests
```

---

## 4. Legacy Compatibility Mode (`--mode hospital`)

The earlier discrete-event hospital operational simulator (modeling queues, beds, inventory, and departmental billing) has been superseded by the longitudinal simulator. It is maintained strictly as an isolated backward-compatibility mode:

* **Invocation:** Enabled **only** when explicitly passing `--mode hospital` to `generate_synthetic_data.py`.
* **Execution Engine:** `HospitalSimulator` (`synapse_simulator/generator/hospital_generator.py`).
* **Documentation:** Historical LLD and SOLID audit records are archived in [`docs/architecture/legacy_hospital_prototype/`](docs/architecture/legacy_hospital_prototype/).
* **Isolation Guarantee:** The legacy compatibility mode is never selected by default and cannot accidentally execute during canonical generation or evaluation.

---

## 5. Scientific Governance Statement

> **EXTERNAL VALIDATION GATE STATUS**:
>
> $$\mathbf{REFERENCE\_DATA\_PENDING}$$
>
> In accordance with research integrity standards:
> 1. **Zero Microdata Access:** No genuine individual participant microdata (from LASI Wave 1 or other restricted clinical databases) were accessed, processed, or reverse-engineered.
> 2. **Public Aggregate Reference Anchors:** All evaluations reflect engineering invariants and statistical calibration against public national aggregate statistics (SRS 2021, ICMR-INDIAB 2023, National Health Profile 2020).
> 3. **No Empirical Clinical Claim:** Evaluation passes indicate internal mathematical consistency and calibration alignment against aggregate population priors. They do not constitute empirical clinical validation of individual real-world outcomes.
