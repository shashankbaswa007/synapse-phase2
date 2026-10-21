# SYNAPSE Phase 2 — Method-Level Execution Traces

This document provides step-by-step method-level traceability tables for the major workflows in SYNAPSE Phase 2.

---

## Trace 1: Application Startup & Bootstrap
| Step | File and Class | Method Called | Collaborators / Invoked | Output / State Effect |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `generate_synthetic_data.py` | `run_data_generation()` | `HospitalSimulator.__init__()` | CLI starts generation |
| 2 | `generator/hospital_generator.py:HospitalSimulator` | `__init__()` | `SimulationBootstrapFactory.bootstrap()` | Delegates assembly |
| 3 | `generator/factory.py:SimulationBootstrapFactory` | `bootstrap()` | `SimulationClock()`, `FutureActionScheduler()`, `EventQueue()` | Instantiates temporal core |
| 4 | `generator/factory.py:SimulationBootstrapFactory` | `bootstrap()` | `StateManager()`, `RuleRepository.load_rules()` | Loads YAML rules |
| 5 | `generator/factory.py:SimulationBootstrapFactory` | `bootstrap()` | `MedicalKnowledgeBase.load(enable_pubmed=True)` | Loads medical ontology & PubMed |
| 6 | `generator/factory.py:SimulationBootstrapFactory` | `wire_department_handlers()` | `dispatcher.register_handler()` | Wires 5 department handlers |

---

## Trace 2: Patient Arrival to Consultation Action Execution
| Step | File and Class | Method Called | Collaborators / Invoked | Output / State Effect |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `core/simulation_engine.py:SimulationEngine` | `_process_simulation_event()` | `dispatcher.dispatch(PatientArrived)` | Routes arrival event |
| 2 | `departments/clinical.py:ClinicalDepartmentHandler` | `handle_event()` | `clinical_gen.select_diagnosis()` | Generates consultation & Rx data |
| 3 | `departments/clinical.py:ClinicalDepartmentHandler` | `handle_event()` | Returns `[ActionRequest(START_DOCTOR_CONSULTATION)]` | Proposes action |
| 4 | `core/simulation_engine.py:SimulationEngine` | `_process_simulation_event()` | `scheduler.schedule_action()` | Queues action into min-heap |
| 5 | `core/simulation_engine.py:SimulationEngine` | `_process_scheduled_action()` | `pipeline.execute_action()` | Executes scheduled action |
| 6 | `engine/orchestrator.py:ExecutionPipeline` | `execute_action()` | `state_manager.build_input_context()` | Assembles InputContext |
| 7 | `rules/rule_engine.py:RuleEngine` | `evaluate()` | `evaluator.evaluate_rule()` | Evaluates active rules |
| 8 | `state/state_manager.py:StateManager` | `apply_decision()` | `transition_validator.validate_transition()` | Transitions appointment status |
| 9 | `core/simulation_engine.py:SimulationEngine` | `_process_scheduled_action()` | `committed_events.append(DomainEvent)` | Commits immutable DomainEvent |

---

## Trace 3: Allergy Safety Hold Detection (OCP & LSP)
| Step | File and Class | Method Called | Collaborators / Invoked | Output / State Effect |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `scenarios/scen_v1_03_allergy.py` | `create_patient_profile()` | `patient_gen.generate_patient(force_allergy='Penicillin')` | Injects allergy polymorphically |
| 2 | `core/simulation_engine.py:SimulationEngine` | `_process_scheduled_action()` | `pipeline.execute_action(VERIFY_PRESCRIPTION)` | Evaluates prescription action |
| 3 | `rules/rule_engine.py:RuleEngine` | `evaluate()` | Evaluates `RULE-CLIN-ALLERGY-001` | Condition matched: Beta-lactam conflicts with Penicillin |
| 4 | `rules/rule_engine.py:RuleEngine` | `evaluate()` | Returns `DecisionResult(BLOCKED, events_to_emit=['PrescriptionAllergyConflictDetected'])` | Blocks prescription |
| 5 | `core/simulation_engine.py:SimulationEngine` | `_process_scheduled_action()` | Inspects `result.decision.events_to_emit[0].event_type` | Emits `PrescriptionAllergyConflictDetected` dynamically |
| 6 | `core/simulation_engine.py:SimulationEngine` | `_process_scheduled_action()` | Emits `DomainEvent(status='BLOCKED_FAILURE')` | Logs clinical hold event |
