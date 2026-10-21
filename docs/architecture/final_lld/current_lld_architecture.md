# SYNAPSE Phase 2 — Current Low-Level Design (LLD) Architecture

**Document Version:** 2.1 (Post-SOLID Refactoring)  
**Status:** Authoritative Implemented Architecture  
**Date:** 2026-10-09  

---

## 1. Executive Summary & Design Overview

The SYNAPSE Phase 2 synthetic hospital simulator operates as a discrete-event, time-driven and event-driven simulation platform. It models outpatient departments (OPD), diagnostic orders (laboratory and radiology), pharmacy dispensing, operational inventory, and billing.

Following recent architectural improvements, the codebase implements clean SOLID principles:
- **SimulationBootstrapFactory:** Encapsulates initialization, dependency resolution, and event-dispatcher wiring.
- **Protocol Ports:** Lightweight `typing.Protocol` interfaces (`IClock`, `IScheduler`, `IEventQueue`, `IEventDispatcher`, `IStateReader`, `IStateWriter`, `ITransitionValidator`, `IScenarioProfileHook`).
- **Dynamic Rule Failure Event Mapping:** Blocking rules declare their emitted failure event types in YAML without hardcoded checks in the simulation engine.
- **Polymorphic Scenario Hooks:** Scenarios configure patient context profiles polymorphically.

---

## 2. Core Subsystems

### 2.1 Discrete-Event Simulation Kernel (`synapse_simulator.core`)
- **`SimulationClock`:** Tracks simulated time monotonically.
- **`FutureActionScheduler`:** Min-heap priority queue of temporal actions.
- **`EventQueue`:** Priority queue of domain events.
- **`EventDispatcher`:** Routes incoming events to registered departmental handlers.
- **`SimulationEngine`:** Core temporal execution loop advancing clock, draining queues, and executing actions.

### 2.2 Execution & State Management (`synapse_simulator.state` & `synapse_simulator.engine`)
- **`ExecutionPipeline`:** Orchestrates context assembly, rule arbitration, and atomic state transitions.
- **`StateManager`:** Multi-table in-memory entity store implementing `IStateReader` and `IStateWriter`.
- **`TransitionManager`:** Finite state machine validator enforcing lifecycle transitions.

### 2.3 Rule & Cognitive Engine (`synapse_simulator.rules`)
- **`RuleRepository`:** Loads declarative rules from YAML files.
- **`RuleEvaluator`:** Evaluates boolean condition expressions.
- **`RuleEngine`:** Evaluates all active rules for an action, resolves priority, and produces a `DecisionResult`.

### 2.4 Patient Journey Workflows (`synapse_simulator.workflows`)
- **`WorkflowCoordinator`:** Traverses graph-based clinical pathway definitions.
- **`PatientJourney`:** State machine representing an individual patient's longitudinal pathway.

### 2.5 Medical Knowledge & PubMed Architecture (`synapse_simulator.knowledge`)
- **`MedicalKnowledgeBase`:** Curated medical ontology loader.
- **`PubMedKnowledgeManager`:** Offline-first PubMed retrieval pipeline extracting evidence-backed treatments and assigning PMIDs for causal provenance.

### 2.6 Persistence & Auditing (`synapse_simulator.exporter` & `synapse_simulator.validation`)
- **`CSVExporter`:** Serializes relational state into 12 simplified CSV files and 21 normalized tables.
- **`IntegrityAuditor`:** Real-time simulation state auditor.
- **`DatasetAuditor`:** Post-export CSV integrity and referential validation engine.

---

## 3. Subsystem Cross-Reference

Refer to the accompanying diagrams:
- [Repository Overview](diagrams/repository_overview.puml)
- [Module Dependencies](diagrams/module_dependencies.puml)
- [Inheritance and Protocols](diagrams/inheritance_and_interfaces.puml)
- [Simulation Engine Detail](diagrams/simulation_engine.puml)
