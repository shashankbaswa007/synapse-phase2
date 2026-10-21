# SYNAPSE Phase 2 — Repository Tree & Package Organization

**Generated from active codebase inspection.**

```text
synapse phase2/
├── generate_synthetic_data.py
├── synapse_simulator/__init__.py
├── synapse_simulator/cli.py
├── synapse_simulator/config.py (1 classes)
├── synapse_simulator/core/__init__.py
├── synapse_simulator/core/clock.py (1 classes)
├── synapse_simulator/core/dispatcher.py (1 classes)
├── synapse_simulator/core/event_queue.py (2 classes)
├── synapse_simulator/core/interfaces.py (4 classes)
├── synapse_simulator/core/scheduler.py (2 classes)
├── synapse_simulator/core/simulation_engine.py (1 classes)
├── synapse_simulator/datagen/__init__.py
├── synapse_simulator/datagen/billing_generator.py (1 classes)
├── synapse_simulator/datagen/clinical_generator.py (1 classes)
├── synapse_simulator/datagen/diagnostic_generator.py (1 classes)
├── synapse_simulator/datagen/master_data.py (1 classes)
├── synapse_simulator/datagen/models.py (10 classes)
├── synapse_simulator/datagen/patient_generator.py (1 classes)
├── synapse_simulator/departments/__init__.py
├── synapse_simulator/departments/base.py (1 classes)
├── synapse_simulator/departments/clinical.py (1 classes)
├── synapse_simulator/departments/finance.py (1 classes)
├── synapse_simulator/departments/laboratory.py (1 classes)
├── synapse_simulator/departments/pharmacy.py (1 classes)
├── synapse_simulator/departments/radiology.py (1 classes)
├── synapse_simulator/engine/__init__.py
├── synapse_simulator/engine/orchestrator.py (2 classes)
├── synapse_simulator/exporter/__init__.py
├── synapse_simulator/exporter/csv_exporter.py (1 classes)
├── synapse_simulator/exporter/data_exporter.py (1 classes)
├── synapse_simulator/exporter/document_generator.py (1 classes)
├── synapse_simulator/exporter/event_logger.py (1 classes)
├── synapse_simulator/exporter/journey_trace.py (1 classes)
├── synapse_simulator/exporter/lineage_mapper.py (1 classes)
├── synapse_simulator/generator/__init__.py
├── synapse_simulator/generator/factory.py (1 classes)
├── synapse_simulator/generator/hospital_generator.py (1 classes)
├── synapse_simulator/knowledge/__init__.py
├── synapse_simulator/knowledge/loader.py (1 classes)
├── synapse_simulator/knowledge/models.py (16 classes)
├── synapse_simulator/knowledge/pubmed/__init__.py
├── synapse_simulator/knowledge/pubmed/cache.py (1 classes)
├── synapse_simulator/knowledge/pubmed/client.py (1 classes)
├── synapse_simulator/knowledge/pubmed/extractor.py (1 classes)
├── synapse_simulator/knowledge/pubmed/models.py (5 classes)
├── synapse_simulator/knowledge/pubmed/normalizer.py (1 classes)
├── synapse_simulator/knowledge/pubmed/parser.py (1 classes)
├── synapse_simulator/knowledge/pubmed/retriever.py (1 classes)
├── synapse_simulator/knowledge/pubmed/seed_cache.py
├── synapse_simulator/knowledge/pubmed/store.py (1 classes)
├── synapse_simulator/knowledge/pubmed/validator.py (1 classes)
├── synapse_simulator/rules/__init__.py
├── synapse_simulator/rules/evaluator.py (1 classes)
├── synapse_simulator/rules/models.py (9 classes)
├── synapse_simulator/rules/repository.py (1 classes)
├── synapse_simulator/rules/rule_engine.py (1 classes)
├── synapse_simulator/scenarios/__init__.py
├── synapse_simulator/scenarios/base_scenario.py (1 classes)
├── synapse_simulator/scenarios/interfaces.py (1 classes)
├── synapse_simulator/scenarios/scen_v1_01_opd.py (1 classes)
├── synapse_simulator/scenarios/scen_v1_02_diagnostic.py (1 classes)
├── synapse_simulator/scenarios/scen_v1_03_allergy.py (1 classes)
├── synapse_simulator/scenarios/scen_v1_04_inventory.py (1 classes)
├── synapse_simulator/state/__init__.py
├── synapse_simulator/state/document_models.py (3 classes)
├── synapse_simulator/state/interfaces.py (4 classes)
├── synapse_simulator/state/models.py (18 classes)
├── synapse_simulator/state/state_manager.py (1 classes)
├── synapse_simulator/transitions/__init__.py
├── synapse_simulator/transitions/interfaces.py (1 classes)
├── synapse_simulator/transitions/state_machine.py (10 classes)
├── synapse_simulator/transitions/transition_manager.py (1 classes)
├── synapse_simulator/validation/consistency_checker.py (1 classes)
├── synapse_simulator/validation/dataset_auditor.py (1 classes)
├── synapse_simulator/validation/document_validator.py (2 classes)
├── synapse_simulator/validation/integrity_auditor.py (1 classes)
├── synapse_simulator/workflows/__init__.py
├── synapse_simulator/workflows/coordinator.py (1 classes)
├── synapse_simulator/workflows/model.py (4 classes)
├── synapse_simulator/workflows/templates.py
├── tests/__init__.py
├── tests/test_data_integrity_temporal_consistency.py
├── tests/test_datagen.py
├── tests/test_dispatcher.py
├── tests/test_event_queue.py
├── tests/test_full_simulation.py
├── tests/test_lab_rad_finance_rules.py
├── tests/test_orchestrator.py
├── tests/test_phase2_csv_export.py
├── tests/test_pubmed_datagen_integration.py
├── tests/test_pubmed_treatment_architecture.py
├── tests/test_rule_engine.py
├── tests/test_solid_principles.py
├── tests/test_stage6_clock_scheduler.py
├── tests/test_stage6_domain_events.py
├── tests/test_stage6_loop_failure_protection.py
├── tests/test_stage6_ordering_causation.py
├── tests/test_stage6_reproducibility.py
├── tests/test_stage6_small_simulation.py
├── tests/test_stage7_cross_department.py
├── tests/test_stage7_patient_journeys.py
├── tests/test_stage7_scale.py
├── tests/test_stage7_workflows.py
├── tests/test_stage9_billing.py
├── tests/test_stage9_diagnostics.py
├── tests/test_stage9_discharge.py
├── tests/test_stage9_integrity.py
├── tests/test_stage9_persistence.py
├── tests/test_stage9_prescription.py
├── tests/test_state_machines.py
├── tests/test_state_manager.py
```

### Package Summary

- Total Python Modules: 111
- Total Classes: 139
- Production Modules: 80
- Test Modules: 31
