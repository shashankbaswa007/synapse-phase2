# SYNAPSE Phase 2 — Codebase Architecture & Directory Guide

This document provides a comprehensive, professional map of the **SYNAPSE Phase 2** repository. It outlines package boundaries, directory functions, entry points, configuration schemas, and data persistence lifecycles.

---

## 1. Top-Level Directory Organization

```
synapse-phase2/
├── generate_synthetic_data.py       # Primary CLI: Generates synthetic patient cohorts and runs validation gate
├── evaluate_dataset.py              # Independent Evaluator CLI: Benchmarks CSV directories against national priors
├── run_evaluation_experiment.py     # Experiment CLI: Single cohort & multi-seed Monte Carlo sweeps
├── README.md                        # Project landing page, quickstart, and scientific governance statement
├── PROJECT_STRUCTURE.md             # This document: Comprehensive architecture and directory roadmap
├── requirements.txt                 # Pinned dependencies (Pydantic, NumPy, SciPy, PyYAML, Faker, Pytest)
│
├── config/                          # Declarative simulation configurations & domain models
│   ├── modules/                     # Synthea-style generic YAML disease progression state machines
│   ├── population/                  # Census SRS 2021 demographic distributions for Indian states
│   └── knowledge/                   # Master clinical data, drug formulary, diagnostic codes, & PubMed
│
├── data/                            # Structured data workspace (released, experimental, & archived)
│   ├── synthetic/                   # Canonical released dataset (10,000 cohort, seed 42) + manifests
│   ├── archive/                     # Preserved legacy test runs and historical experimental outputs
│   ├── generated/                   # Preserved early exploratory hospital prototype runs
│   ├── experiments/                 # Monte Carlo simulation sweeps and experimental outputs
│   └── evaluation/                  # Ground-truth evaluation fixtures and benchmark tables
│
├── docs/                            # Research alignment, architectural specifications, and audits
│   ├── architecture/                # System architecture, LLDs, and legacy prototype archive
│   └── research_alignment/          # 114 research papers, variance derivations, and validation audits
│
├── output/                          # Publication-grade deliverables, summaries, and SVG charts
│   ├── SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md # Comprehensive 10,000-cohort technical report
│   ├── CLINICAL_EVALUATION_REPORT.md                # 21-benchmark clinical validation report
│   ├── LONGITUDINAL_COHORT_SUMMARY_10000.md         # Formatted Markdown cohort summary tables
│   └── visualizations/                              # High-resolution vector SVG diagnostic diagrams
│
├── synapse_simulator/               # Core Python library package
│   ├── core/                        # Event bus, clocks, dispatchers, and system interfaces
│   ├── datagen/                     # Demographic samplers, community assessment, forward hemodynamics
│   ├── departments/                 # Hospital departmental lifecycle handlers (clinical, finance, lab, etc.)
│   ├── engine/                      # Orchestrator and discrete-event execution pipelines
│   ├── evaluation/                  # Statistical evaluators, Wilson CIs, Taylor variance, LASI pipeline
│   ├── exporter/                    # Normalized relational CSV serializers
│   ├── generator/                   # Cohort generators and legacy hospital operational factory
│   ├── knowledge/                   # Clinical master data models and PubMed integration
│   ├── modules/                     # Synthea Generic Module Framework state machine engine
│   ├── population/                  # Population profile loaders and demographic probability tables
│   ├── rules/                       # 5-Level precedence rule engine for clinical safety vetoes
│   ├── scenarios/                   # Clinical scenario definitions and workflow drivers
│   ├── state/                       # Thread-safe state store, context builders, and domain models
│   ├── transitions/                 # State machine transition evaluators (Direct, Distributed, Conditional, Complex)
│   ├── validation/                  # DatasetAuditor, IntegrityAuditor, and DatasetValidationGate
│   └── workflows/                   # Standard operating procedure (SOP) workflow definitions
│
└── tests/                           # 374 automated regression and scientific validation tests
```

---

## 2. Package Architecture (`synapse_simulator/`)

The core library is structured into decoupled, single-responsibility modules following SOLID principles:

### 2.1 Simulation Engines & Lifecycles
| Subpackage | Role & Key Classes | Documentation Link |
| :--- | :--- | :--- |
| **`synapse_simulator.modules`** | Generic Module Framework: YAML state machines, condition evaluators, and state transitions. | [`modules/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/modules/__init__.py) |
| **`synapse_simulator.transitions`** | Implements the 4 Synthea transition types: `DirectTransition`, `DistributedTransition`, `ConditionalTransition`, `ComplexTransition`. | [`transitions/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/transitions/__init__.py) |
| **`synapse_simulator.datagen`** | Demographic sampling, forward state-space hemodynamics, habituation BP modeling, and community assessment. | [`datagen/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/datagen/__init__.py) |
| **`synapse_simulator.rules`** | 5-Level Precedence Hierarchy: System integrity, clinical safety vetoes, department workflows, scenarios, and heuristics. | [`rules/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/rules/__init__.py) |
| **`synapse_simulator.state`** | Thread-safe `StateManager`, immutable `DomainEvent` logging, and transactional context builders. | [`state/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/state/__init__.py) |

### 2.2 Evaluation & Research Validation
| Subpackage | Role & Key Classes | Documentation Link |
| :--- | :--- | :--- |
| **`synapse_simulator.evaluation`** | Statistical evaluation against national empirical priors (`DatasetEvaluator`, `ReferenceCatalog`, `ExperimentRunner`). | [`evaluation/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/__init__.py) |
| **`synapse_simulator.evaluation.lasi`** | LASI Wave 1 survey ingestion, Horvitz-Thompson weighting, Taylor series linearization variance, and 60/40 PSU partitioning. | [`evaluation/lasi/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/evaluation/lasi/__init__.py) |
| **`synapse_simulator.validation`** | Fail-fast validation gates (`DatasetValidationGate`), relational integrity auditing (`DatasetAuditor`), and clinical safety checks. | [`validation/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/validation/__init__.py) |

### 2.3 Persistence & Clinical Master Data
| Subpackage | Role & Key Classes | Documentation Link |
| :--- | :--- | :--- |
| **`synapse_simulator.exporter`** | Multi-table relational CSV serialization (`CSVExporter`, `DataExporter`) guaranteeing RFC 4180 compliance. | [`exporter/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/exporter/__init__.py) |
| **`synapse_simulator.knowledge`** | Master clinical entities (`MedicalKnowledgeBase`), ICD-10 diagnostic entries, drug formularies, lab reference ranges, and PubMed models. | [`knowledge/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/knowledge/__init__.py) |
| **`synapse_simulator.population`** | Census SRS 2021 India population profile loaders and empirical demographic tables. | [`population/__init__.py`](file:///Users/shashi/synapse/synapse-phase2/synapse_simulator/population/__init__.py) |

---

## 3. Data Workspace & Lifecycle (`data/`)

The data workspace is partitioned into strict operational boundaries:

```
data/
├── synthetic/               # Authoritative release directory
│   ├── *.csv                # 18 relational tables (11 populated clinical tables + 7 structural placeholders)
│   ├── DATASET_MANIFEST.json# Cryptographic SHA-256 manifests, row counts, column schemas
│   ├── RUN_MANIFEST.json    # Exact runtime parameters, execution duration, git commit hash
│   ├── FINAL_10000_DATASET_VALIDATION.md # Release verification report
│   └── README.md            # Directory schema documentation
│
├── archive/                 # Archived legacy test runs and historical staging
│   └── legacy_test_runs/    # test_stage_b, test_stage_c, test_stage_d, test_gate_100, etc.
│       └── README.md        # Archive catalogue & provenance
│
├── generated/               # Archived early hospital prototype runs (September 2026)
│   ├── final_10000/         # Historical discrete-event prototype run
│   ├── production_10000/    # Historical queue-artifact run
│   └── README.md            # Explanatory warning note
│
├── experiments/             # Active Monte Carlo and hyperparameter experiment outputs
└── evaluation/              # Ground-truth test fixtures and reference datasets
```

---

## 4. Execution Workflow Reference

### 4.1 Canonical 10,000 Cohort Generation
```bash
python generate_synthetic_data.py \
  --patients 10000 \
  --seed 42 \
  --days 720 \
  --timestep 7 \
  --output-dir data/synthetic
```

### 4.2 Independent Statistical Evaluation
```bash
python evaluate_dataset.py \
  --dataset-dir data/synthetic \
  --output-dir output
```

### 4.3 Multi-Seed Monte Carlo Sweep
```bash
python run_evaluation_experiment.py \
  --patients 250 \
  --seeds 42,101,202,303,404 \
  --output-dir data/experiments/monte_carlo_sweep
```

### 4.4 Automated Test Suite Execution
```bash
# Run all 374 regression tests
pytest tests/
```
