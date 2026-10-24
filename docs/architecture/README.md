# SYNAPSE Phase 2 — System Architecture Index

Welcome to the architectural documentation for **SYNAPSE Phase 2: Synthea-Inspired Longitudinal Synthetic Healthcare Simulation System**.

---

## 1. Primary Active Architecture

The active, canonical implementation of SYNAPSE Phase 2 is the **Synthea-inspired longitudinal population healthcare simulation system**. It models synthetic patient demographics, chronic disease progression, clinical encounters, treatment escalation, continuous hemodynamics, background life-table mortality, and standardized community blood pressure surveys.

| Document | Purpose & Scope | Link |
| :--- | :--- | :--- |
| **Longitudinal System Architecture** | Definitive architectural specification of the active 7-stage simulation pipeline, disease state machines, dual hemodynamic engines, community survey protocols, and validation gates. | [longitudinal_system_architecture.md](longitudinal_system_architecture.md) |
| **System Report & Calibration** | Comprehensive technical report on the canonical 10,000-patient release cohort ($N=10,000$, seed 42, 720 days, timestep 7 days). | [`output/SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md`](../../output/SYNAPSE_PHASE2_LONGITUDINAL_SYSTEM_REPORT.md) |
| **Clinical Evaluation Report** | Preregistered clinical invariant and statistical acceptance evaluation across 21 benchmarks (16 PASS, 0 WARN, 0 FAIL, 5 UNVERIFIED). | [`output/CLINICAL_EVALUATION_REPORT.md`](../../output/CLINICAL_EVALUATION_REPORT.md) |
| **Research & Calibration Archives** | 114 specialized research alignment documents covering survey design, variance estimation, BP measurement error models, and LASI protocol mappings. | [`docs/research_alignment/`](../research_alignment/) |

---

## 2. Canonical Execution Path

```
generate_synthetic_data.py (default: --mode longitudinal)
       │
       ▼
ExperimentRunner.generate_cohort()
       │
       ├─► [1] Demographic Sampling (Census SRS 2021) ──► PatientProfileGenerator
       ├─► [2] Disease Progression Engine ──────────────► ClinicalModuleRunner (YAML State Machines)
       │         • Hypertension (hypertension.yaml)
       │         • Type 2 Diabetes (diabetes_t2.yaml)
       │         • Acute URTI (urti.yaml)
       ├─► [3] Background Mortality (SRS Life Tables) ──► Annual q(x) Stepping
       ├─► [4] Continuous Hemodynamics ─────────────────► LEGACY_CONDITIONAL (default) / FORWARD_STATE_SPACE
       ├─► [5] Independent Community Survey ────────────► CommunityAssessmentGenerator (LASI_WAVE1_TRI_MEASUREMENT)
       └─► [6] Relational Serialization ────────────────► CSVExporter (18 Relational CSV Tables)
                 │
                 ▼
       DatasetAuditor & DatasetEvaluator
                 │
                 ▼
       DatasetValidationGate (Fail-fast promotion)
                 │
                 ▼
       data/synthetic/ + RUN_MANIFEST.json + DATASET_MANIFEST.json
```

---

## 3. Legacy Compatibility Mode (`--mode hospital`)

The earlier discrete-event hospital operational simulator (modeling queues, beds, inventory, and departmental billing) is preserved strictly for backward compatibility and historical regression testing.

| Archive | Description | Link |
| :--- | :--- | :--- |
| **Legacy Hospital Prototype Archive** | Preserves historical Low-Level Design (LLD), PlantUML diagrams, class index, and SOLID audit of the September 2026 hospital operational prototype. | [legacy_hospital_prototype/](legacy_hospital_prototype/) |
| **Legacy SOLID Audit** | SOLID principles audit of `HospitalSimulator` and departmental handlers. | [legacy_hospital_prototype/SYNAPSE_SOLID_LLD_ARCHITECTURE_ASSESSMENT.md](legacy_hospital_prototype/SYNAPSE_SOLID_LLD_ARCHITECTURE_ASSESSMENT.md) |
| **Legacy Verification Report** | September 29, 2026 verification report for the hospital operational prototype. | [legacy_hospital_prototype/legacy_verification_sept2026.md](legacy_hospital_prototype/legacy_verification_sept2026.md) |

> [!NOTE]
> The legacy hospital prototype is invoked **only** when explicitly passing `--mode hospital` to `generate_synthetic_data.py`. It is never invoked by default.
