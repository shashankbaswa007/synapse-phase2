# SYNAPSE Phase 2 — Legacy Discrete-Event Hospital Simulator (Historical LLD Archive)

> [!WARNING]
> **HISTORICAL / LEGACY COMPATIBILITY ARCHIVE**  
> This directory preserves the historical Low-Level Design (LLD), class indexes, and SOLID audit documentation for the earlier discrete-event hospital operational simulator prototype (August–September 2026).
>
> **Status:** SUPERSEDED for active development. Retained SOLELY for backward compatibility (`--mode hospital`) and existing regression test coverage.
>
> **Canonical Active System:** The active production implementation for SYNAPSE Phase 2 is the **Synthea-inspired longitudinal healthcare simulation system** documented in:
> - Root Entry Point: [`generate_synthetic_data.py`](file:///Users/shashi/synapse/synapse-phase2/generate_synthetic_data.py) (default: `--mode longitudinal`)
> - Canonical Architecture: [`docs/architecture/longitudinal_system_architecture.md`](file:///Users/shashi/synapse/synapse-phase2/docs/architecture/longitudinal_system_architecture.md)
> - Root Guide: [`README.md`](file:///Users/shashi/synapse/synapse-phase2/README.md)
> - Verified Cohort: [`data/synthetic/`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/) ($N=10,000$, seed 42)

---

## Documentation Navigation

| Document Name | Description | Link |
| :--- | :--- | :--- |
| **LLD Architecture Guide** | Comprehensive architecture specification of the implemented system | [current_lld_architecture.md](current_lld_architecture.md) |
| **SOLID Principles Assessment** | Detailed audit and verification of S, O, L, I, D compliance | [solid_assessment.md](solid_assessment.md) |
| **Repository Tree** | Complete package structure and file inventory | [repository_tree.md](repository_tree.md) |
| **Class Index** | Master index of all 100+ classes with unique identifiers | [class_index.md](class_index.md) |
| **Symbol Reference** | Complete method signatures, parameters, return types, and attributes | [attribute_method_reference.md](attribute_method_reference.md) |
| **Module Dependency Map** | Cross-package imports and internal/external dependency boundaries | [module_dependency_map.md](module_dependency_map.md) |
| **Source Change Delta** | Detailed record of files added and modified for SOLID compliance | [source_change_inventory.md](source_change_inventory.md) |
| **Automated Test Report** | Execution evidence for all 90 automated tests (100% pass) | [test_verification_report.md](test_verification_report.md) |
| **Execution Traces** | Step-by-step method-level traceability tables | [execution_traces.md](execution_traces.md) |
| **10,000-Patient Dataset Validation** | Full quantitative audit report for the 10,000 synthetic patient dataset | [FINAL_10000_DATASET_VALIDATION.md](FINAL_10000_DATASET_VALIDATION.md) |

---

## Architecture Diagrams

All editable PlantUML diagrams are stored in:
- `diagrams/`: 18 Class, Package, and Subsystem PUML diagrams.
- `sequences/`: 8 Method-level Sequence PUML diagrams.

---

## Phase 2 Final Acceptance Verdicts

| Acceptance Dimension | Verdict | Evidence |
| :--- | :---: | :--- |
| **Dimension A: SOLID / LLD Architecture** | **PASS — SOLID/LLD VERIFICATION COMPLETE** | All 5 SOLID principles verified; 90/90 tests passing; complete UML and symbol inventories documented. |
| **Dimension B: Dataset / Phase 3 Readiness** | **PASS — DATASET READY FOR PHASE 3** | Fresh 10,000-patient dataset verified; 0 dangling references; 0 nulls; 100% referential and clinical integrity. |
