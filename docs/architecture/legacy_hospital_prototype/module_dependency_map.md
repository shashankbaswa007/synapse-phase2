# SYNAPSE Phase 2 — Module Dependency & Import Map

| Module Path | External Imports | Internal Project Imports |
| :--- | :--- | :--- |
| `generate_synthetic_data.py` | `argparse, datetime, json, pathlib, sys, time, typing` | `synapse_simulator.exporter.csv_exporter, synapse_simulator.generator.hospital_generator, synapse_simulator.knowledge.pubmed.seed_cache, synapse_simulator.validation.dataset_auditor, synapse_simulator.validation.integrity_auditor` |
| `synapse_simulator/__init__.py` | `None` | `None` |
| `synapse_simulator/cli.py` | `argparse, pathlib, sys` | `None` |
| `synapse_simulator/config.py` | `os, pathlib, pydantic` | `None` |
| `synapse_simulator/core/__init__.py` | `None` | `synapse_simulator.core.clock, synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.core.interfaces` |
| `synapse_simulator/core/clock.py` | `datetime, typing` | `None` |
| `synapse_simulator/core/dispatcher.py` | `typing` | `synapse_simulator.core.event_queue, synapse_simulator.state.models` |
| `synapse_simulator/core/event_queue.py` | `datetime, heapq, itertools, pydantic, typing, uuid` | `None` |
| `synapse_simulator/core/interfaces.py` | `datetime, typing` | `synapse_simulator.core.event_queue, synapse_simulator.state.models` |
| `synapse_simulator/core/scheduler.py` | `datetime, heapq, itertools, pydantic, typing` | `synapse_simulator.state.models` |
| `synapse_simulator/core/simulation_engine.py` | `datetime, itertools, typing, uuid` | `synapse_simulator.core.clock, synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.core.scheduler, synapse_simulator.engine.orchestrator, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `synapse_simulator/datagen/__init__.py` | `None` | `None` |
| `synapse_simulator/datagen/billing_generator.py` | `datetime, random, typing` | `synapse_simulator.datagen.models` |
| `synapse_simulator/datagen/clinical_generator.py` | `datetime, random, typing, uuid` | `synapse_simulator.datagen.models, synapse_simulator.knowledge.loader, synapse_simulator.knowledge.models` |
| `synapse_simulator/datagen/diagnostic_generator.py` | `datetime, random, typing` | `synapse_simulator.datagen.models` |
| `synapse_simulator/datagen/master_data.py` | `datetime, faker, random, typing, uuid` | `synapse_simulator.datagen.models, synapse_simulator.knowledge.loader, synapse_simulator.knowledge.models, synapse_simulator.state.state_manager` |
| `synapse_simulator/datagen/models.py` | `datetime, pydantic, typing` | `None` |
| `synapse_simulator/datagen/patient_generator.py` | `faker, random, typing, uuid` | `synapse_simulator.datagen.models, synapse_simulator.knowledge.loader` |
| `synapse_simulator/departments/__init__.py` | `None` | `synapse_simulator.departments.base` |
| `synapse_simulator/departments/base.py` | `abc, typing` | `synapse_simulator.core.event_queue, synapse_simulator.state.models` |
| `synapse_simulator/departments/clinical.py` | `typing, uuid` | `synapse_simulator.core.event_queue, synapse_simulator.departments.base, synapse_simulator.state.models` |
| `synapse_simulator/departments/finance.py` | `typing, uuid` | `synapse_simulator.core.event_queue, synapse_simulator.departments.base, synapse_simulator.state.models` |
| `synapse_simulator/departments/laboratory.py` | `typing, uuid` | `synapse_simulator.core.event_queue, synapse_simulator.departments.base, synapse_simulator.state.models` |
| `synapse_simulator/departments/pharmacy.py` | `typing, uuid` | `synapse_simulator.core.event_queue, synapse_simulator.departments.base, synapse_simulator.state.models` |
| `synapse_simulator/departments/radiology.py` | `typing, uuid` | `synapse_simulator.core.event_queue, synapse_simulator.departments.base, synapse_simulator.state.models` |
| `synapse_simulator/engine/__init__.py` | `None` | `synapse_simulator.engine.orchestrator` |
| `synapse_simulator/engine/orchestrator.py` | `datetime, pydantic, typing` | `synapse_simulator.config, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `synapse_simulator/exporter/__init__.py` | `None` | `synapse_simulator.exporter.csv_exporter, synapse_simulator.exporter.data_exporter` |
| `synapse_simulator/exporter/csv_exporter.py` | `csv, datetime, os, pathlib, typing` | `synapse_simulator.datagen.models, synapse_simulator.state.models, synapse_simulator.state.state_manager, synapse_simulator.workflows.model` |
| `synapse_simulator/exporter/data_exporter.py` | `json, pathlib, typing` | `None` |
| `synapse_simulator/exporter/document_generator.py` | `datetime, hashlib, json, os, pathlib, typing, uuid` | `synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `synapse_simulator/exporter/event_logger.py` | `json, pathlib, typing` | `synapse_simulator.state.models` |
| `synapse_simulator/exporter/journey_trace.py` | `typing` | `synapse_simulator.workflows.model` |
| `synapse_simulator/exporter/lineage_mapper.py` | `datetime, json, pathlib, typing` | `synapse_simulator.state.document_models, synapse_simulator.state.models` |
| `synapse_simulator/generator/__init__.py` | `None` | `synapse_simulator.generator.hospital_generator` |
| `synapse_simulator/generator/factory.py` | `datetime, random, typing` | `synapse_simulator.core.clock, synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.core.scheduler, synapse_simulator.core.simulation_engine, synapse_simulator.datagen.billing_generator, synapse_simulator.datagen.clinical_generator, synapse_simulator.datagen.diagnostic_generator, synapse_simulator.datagen.master_data, synapse_simulator.datagen.patient_generator, synapse_simulator.departments.clinical, synapse_simulator.departments.finance, synapse_simulator.departments.laboratory, synapse_simulator.departments.pharmacy, synapse_simulator.departments.radiology, synapse_simulator.engine.orchestrator, synapse_simulator.knowledge.loader, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.state_manager, synapse_simulator.workflows.coordinator, synapse_simulator.workflows.templates` |
| `synapse_simulator/generator/hospital_generator.py` | `datetime, random, typing, uuid` | `synapse_simulator.core.clock, synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.core.scheduler, synapse_simulator.core.simulation_engine, synapse_simulator.datagen.billing_generator, synapse_simulator.datagen.clinical_generator, synapse_simulator.datagen.diagnostic_generator, synapse_simulator.datagen.master_data, synapse_simulator.datagen.models, synapse_simulator.datagen.patient_generator, synapse_simulator.departments.clinical, synapse_simulator.departments.finance, synapse_simulator.departments.laboratory, synapse_simulator.departments.pharmacy, synapse_simulator.departments.radiology, synapse_simulator.engine.orchestrator, synapse_simulator.generator.factory, synapse_simulator.knowledge.loader, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.scenarios.scen_v1_01_opd, synapse_simulator.scenarios.scen_v1_02_diagnostic, synapse_simulator.scenarios.scen_v1_03_allergy, synapse_simulator.scenarios.scen_v1_04_inventory, synapse_simulator.state.models, synapse_simulator.state.state_manager, synapse_simulator.workflows.coordinator, synapse_simulator.workflows.model, synapse_simulator.workflows.templates` |
| `synapse_simulator/knowledge/__init__.py` | `None` | `synapse_simulator.knowledge.loader` |
| `synapse_simulator/knowledge/loader.py` | `pathlib, typing, yaml` | `synapse_simulator.knowledge.models` |
| `synapse_simulator/knowledge/models.py` | `pydantic, typing` | `None` |
| `synapse_simulator/knowledge/pubmed/__init__.py` | `None` | `synapse_simulator.knowledge.pubmed.seed_cache` |
| `synapse_simulator/knowledge/pubmed/cache.py` | `json, pathlib, typing` | `synapse_simulator.knowledge.pubmed.models` |
| `synapse_simulator/knowledge/pubmed/client.py` | `json, pathlib, time, typing, urllib.parse, urllib.request` | `synapse_simulator.knowledge.pubmed.cache, synapse_simulator.knowledge.pubmed.models, synapse_simulator.knowledge.pubmed.parser` |
| `synapse_simulator/knowledge/pubmed/extractor.py` | `re, typing, uuid` | `synapse_simulator.knowledge.pubmed.models, synapse_simulator.knowledge.pubmed.normalizer` |
| `synapse_simulator/knowledge/pubmed/models.py` | `datetime, pydantic, typing` | `None` |
| `synapse_simulator/knowledge/pubmed/normalizer.py` | `re, typing` | `synapse_simulator.knowledge.pubmed.models` |
| `synapse_simulator/knowledge/pubmed/parser.py` | `typing, xml.etree.ElementTree` | `synapse_simulator.knowledge.pubmed.models` |
| `synapse_simulator/knowledge/pubmed/retriever.py` | `pathlib, typing, yaml` | `synapse_simulator.knowledge.loader, synapse_simulator.knowledge.pubmed.cache, synapse_simulator.knowledge.pubmed.client, synapse_simulator.knowledge.pubmed.extractor, synapse_simulator.knowledge.pubmed.models, synapse_simulator.knowledge.pubmed.normalizer, synapse_simulator.knowledge.pubmed.parser, synapse_simulator.knowledge.pubmed.store, synapse_simulator.knowledge.pubmed.validator` |
| `synapse_simulator/knowledge/pubmed/seed_cache.py` | `pathlib, typing` | `synapse_simulator.knowledge.pubmed.cache, synapse_simulator.knowledge.pubmed.models` |
| `synapse_simulator/knowledge/pubmed/store.py` | `datetime, json, pathlib, typing` | `synapse_simulator.knowledge.pubmed.models` |
| `synapse_simulator/knowledge/pubmed/validator.py` | `typing` | `synapse_simulator.knowledge.loader, synapse_simulator.knowledge.pubmed.models` |
| `synapse_simulator/rules/__init__.py` | `None` | `None` |
| `synapse_simulator/rules/evaluator.py` | `simpleeval, typing` | `synapse_simulator.rules.models, synapse_simulator.state.models` |
| `synapse_simulator/rules/models.py` | `enum, pydantic, typing` | `None` |
| `synapse_simulator/rules/repository.py` | `os, pathlib, typing, yaml` | `synapse_simulator.rules.models` |
| `synapse_simulator/rules/rule_engine.py` | `typing` | `synapse_simulator.rules.evaluator, synapse_simulator.rules.models, synapse_simulator.rules.repository, synapse_simulator.state.models` |
| `synapse_simulator/scenarios/__init__.py` | `None` | `synapse_simulator.scenarios.base_scenario` |
| `synapse_simulator/scenarios/base_scenario.py` | `abc, datetime, typing, uuid` | `synapse_simulator.core.event_queue, synapse_simulator.state.state_manager` |
| `synapse_simulator/scenarios/interfaces.py` | `datetime, typing` | `synapse_simulator.core.event_queue` |
| `synapse_simulator/scenarios/scen_v1_01_opd.py` | `datetime` | `synapse_simulator.core.event_queue, synapse_simulator.scenarios.base_scenario, synapse_simulator.state.state_manager` |
| `synapse_simulator/scenarios/scen_v1_02_diagnostic.py` | `datetime` | `synapse_simulator.core.event_queue, synapse_simulator.scenarios.base_scenario, synapse_simulator.state.state_manager` |
| `synapse_simulator/scenarios/scen_v1_03_allergy.py` | `datetime` | `synapse_simulator.core.event_queue, synapse_simulator.scenarios.base_scenario, synapse_simulator.state.state_manager` |
| `synapse_simulator/scenarios/scen_v1_04_inventory.py` | `datetime` | `synapse_simulator.core.event_queue, synapse_simulator.scenarios.base_scenario, synapse_simulator.state.state_manager` |
| `synapse_simulator/state/__init__.py` | `None` | `synapse_simulator.state.interfaces, synapse_simulator.state.state_manager` |
| `synapse_simulator/state/document_models.py` | `datetime, enum, pydantic, typing` | `None` |
| `synapse_simulator/state/interfaces.py` | `datetime, typing` | `synapse_simulator.state.models` |
| `synapse_simulator/state/models.py` | `datetime, enum, pydantic, typing` | `None` |
| `synapse_simulator/state/state_manager.py` | `datetime, typing` | `synapse_simulator.state.models, synapse_simulator.transitions.interfaces, synapse_simulator.transitions.transition_manager` |
| `synapse_simulator/transitions/__init__.py` | `None` | `synapse_simulator.transitions.interfaces, synapse_simulator.transitions.transition_manager` |
| `synapse_simulator/transitions/interfaces.py` | `typing` | `None` |
| `synapse_simulator/transitions/state_machine.py` | `typing` | `synapse_simulator.state.models` |
| `synapse_simulator/transitions/transition_manager.py` | `typing` | `synapse_simulator.transitions.state_machine` |
| `synapse_simulator/validation/consistency_checker.py` | `json, pathlib, typing` | `synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager, synapse_simulator.validation.document_validator, synapse_simulator.validation.integrity_auditor` |
| `synapse_simulator/validation/dataset_auditor.py` | `csv, datetime, json, os, pathlib, typing` | `None` |
| `synapse_simulator/validation/document_validator.py` | `typing` | `synapse_simulator.state.document_models, synapse_simulator.state.state_manager` |
| `synapse_simulator/validation/integrity_auditor.py` | `datetime, typing` | `synapse_simulator.state.models, synapse_simulator.state.state_manager, synapse_simulator.transitions.state_machine` |
| `synapse_simulator/workflows/__init__.py` | `None` | `synapse_simulator.workflows.model` |
| `synapse_simulator/workflows/coordinator.py` | `datetime, typing, uuid` | `synapse_simulator.core.scheduler, synapse_simulator.state.models, synapse_simulator.workflows.model` |
| `synapse_simulator/workflows/model.py` | `datetime, enum, pydantic, typing` | `None` |
| `synapse_simulator/workflows/templates.py` | `typing` | `synapse_simulator.workflows.model` |
| `tests/__init__.py` | `None` | `None` |
| `tests/test_data_integrity_temporal_consistency.py` | `datetime, pandas, pathlib, pytest` | `synapse_simulator.exporter.csv_exporter, synapse_simulator.generator.hospital_generator, synapse_simulator.validation.integrity_auditor` |
| `tests/test_datagen.py` | `pytest, random` | `synapse_simulator.datagen.clinical_generator, synapse_simulator.datagen.master_data, synapse_simulator.datagen.patient_generator, synapse_simulator.knowledge.loader` |
| `tests/test_dispatcher.py` | `datetime` | `synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.state.models` |
| `tests/test_event_queue.py` | `datetime, pytest` | `synapse_simulator.core.clock, synapse_simulator.core.event_queue` |
| `tests/test_full_simulation.py` | `pathlib, pytest` | `synapse_simulator.exporter.data_exporter, synapse_simulator.generator.hospital_generator` |
| `tests/test_lab_rad_finance_rules.py` | `datetime, pytest` | `synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_orchestrator.py` | `datetime, pytest` | `synapse_simulator.engine.orchestrator, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_phase2_csv_export.py` | `csv, pathlib, pytest, shutil` | `synapse_simulator.generator.hospital_generator` |
| `tests/test_pubmed_datagen_integration.py` | `generate_synthetic_data, os, pandas, pathlib, pytest, shutil, unittest.mock` | `synapse_simulator.exporter.csv_exporter, synapse_simulator.generator.hospital_generator, synapse_simulator.knowledge.loader, synapse_simulator.knowledge.pubmed.models, synapse_simulator.knowledge.pubmed.retriever, synapse_simulator.knowledge.pubmed.seed_cache` |
| `tests/test_pubmed_treatment_architecture.py` | `pathlib, pytest, yaml` | `synapse_simulator.generator.hospital_generator, synapse_simulator.knowledge.loader, synapse_simulator.knowledge.pubmed.retriever, synapse_simulator.knowledge.pubmed.seed_cache, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.models` |
| `tests/test_rule_engine.py` | `datetime, pytest` | `synapse_simulator.rules.models, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_solid_principles.py` | `datetime, pytest, random` | `synapse_simulator.core.clock, synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.core.interfaces, synapse_simulator.core.scheduler, synapse_simulator.core.simulation_engine, synapse_simulator.datagen.patient_generator, synapse_simulator.engine.orchestrator, synapse_simulator.generator.factory, synapse_simulator.generator.hospital_generator, synapse_simulator.knowledge.loader, synapse_simulator.scenarios.base_scenario, synapse_simulator.scenarios.interfaces, synapse_simulator.scenarios.scen_v1_03_allergy, synapse_simulator.state.interfaces, synapse_simulator.state.models, synapse_simulator.state.state_manager, synapse_simulator.transitions.interfaces, synapse_simulator.transitions.transition_manager` |
| `tests/test_stage6_clock_scheduler.py` | `datetime, pytest` | `synapse_simulator.core.clock, synapse_simulator.core.scheduler, synapse_simulator.state.models` |
| `tests/test_stage6_domain_events.py` | `datetime, pytest` | `synapse_simulator.core.scheduler, synapse_simulator.core.simulation_engine, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_stage6_loop_failure_protection.py` | `datetime, pytest` | `synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.engine.orchestrator, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_stage6_ordering_causation.py` | `datetime` | `synapse_simulator.core.event_queue, synapse_simulator.core.scheduler, synapse_simulator.state.models` |
| `tests/test_stage6_reproducibility.py` | `None` | `synapse_simulator.generator.hospital_generator` |
| `tests/test_stage6_small_simulation.py` | `datetime` | `synapse_simulator.core.clock, synapse_simulator.core.dispatcher, synapse_simulator.core.event_queue, synapse_simulator.core.scheduler, synapse_simulator.core.simulation_engine, synapse_simulator.departments.clinical, synapse_simulator.departments.pharmacy, synapse_simulator.rules.repository, synapse_simulator.rules.rule_engine, synapse_simulator.scenarios.scen_v1_01_opd, synapse_simulator.scenarios.scen_v1_03_allergy, synapse_simulator.state.state_manager` |
| `tests/test_stage7_cross_department.py` | `None` | `synapse_simulator.generator.hospital_generator` |
| `tests/test_stage7_patient_journeys.py` | `None` | `synapse_simulator.exporter.journey_trace, synapse_simulator.generator.hospital_generator` |
| `tests/test_stage7_scale.py` | `None` | `synapse_simulator.generator.hospital_generator` |
| `tests/test_stage7_workflows.py` | `datetime, pytest` | `synapse_simulator.core.scheduler, synapse_simulator.state.models, synapse_simulator.workflows.coordinator, synapse_simulator.workflows.model, synapse_simulator.workflows.templates` |
| `tests/test_stage9_billing.py` | `datetime, pathlib, pytest` | `synapse_simulator.exporter.document_generator, synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_stage9_diagnostics.py` | `datetime, pathlib, pytest` | `synapse_simulator.exporter.document_generator, synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_stage9_discharge.py` | `datetime, pathlib, pytest` | `synapse_simulator.exporter.document_generator, synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_stage9_integrity.py` | `datetime, json, pathlib, pytest` | `synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager, synapse_simulator.validation.consistency_checker, synapse_simulator.validation.document_validator, synapse_simulator.validation.integrity_auditor` |
| `tests/test_stage9_persistence.py` | `datetime, json, pathlib, pytest` | `synapse_simulator.exporter.event_logger, synapse_simulator.exporter.lineage_mapper, synapse_simulator.state.document_models, synapse_simulator.state.models` |
| `tests/test_stage9_prescription.py` | `datetime, pathlib, pytest` | `synapse_simulator.exporter.document_generator, synapse_simulator.state.document_models, synapse_simulator.state.models, synapse_simulator.state.state_manager` |
| `tests/test_state_machines.py` | `pytest` | `synapse_simulator.state.models, synapse_simulator.transitions.state_machine, synapse_simulator.transitions.transition_manager` |
| `tests/test_state_manager.py` | `datetime, pytest` | `synapse_simulator.state.models, synapse_simulator.state.state_manager` |