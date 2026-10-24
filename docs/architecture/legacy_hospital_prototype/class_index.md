# SYNAPSE Phase 2 — Complete Class Index

| Class ID | Class Name | Module Path | Base Classes / Protocols | Category | Methods Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CLS-001` | **`SimulatorSettings`** | `synapse_simulator/config.py` | `BaseModel` | Production | 0 |
| `CLS-002` | **`SimulationClock`** | `synapse_simulator/core/clock.py` | `object` | Production | 6 |
| `CLS-003` | **`EventDispatcher`** | `synapse_simulator/core/dispatcher.py` | `object` | Production | 4 |
| `CLS-004` | **`SimulationEvent`** | `synapse_simulator/core/event_queue.py` | `BaseModel` | Production | 1 |
| `CLS-005` | **`EventQueue`** | `synapse_simulator/core/event_queue.py` | `object` | Production | 7 |
| `CLS-006` | **`IClock`** | `synapse_simulator/core/interfaces.py` | `Protocol` | Production | 4 |
| `CLS-007` | **`IScheduler`** | `synapse_simulator/core/interfaces.py` | `Protocol` | Production | 4 |
| `CLS-008` | **`IEventQueue`** | `synapse_simulator/core/interfaces.py` | `Protocol` | Production | 4 |
| `CLS-009` | **`IEventDispatcher`** | `synapse_simulator/core/interfaces.py` | `Protocol` | Production | 2 |
| `CLS-010` | **`ScheduledFutureAction`** | `synapse_simulator/core/scheduler.py` | `BaseModel` | Production | 1 |
| `CLS-011` | **`FutureActionScheduler`** | `synapse_simulator/core/scheduler.py` | `object` | Production | 8 |
| `CLS-012` | **`SimulationEngine`** | `synapse_simulator/core/simulation_engine.py` | `object` | Production | 5 |
| `CLS-013` | **`BillingGenerator`** | `synapse_simulator/datagen/billing_generator.py` | `object` | Production | 2 |
| `CLS-014` | **`ClinicalEntityGenerator`** | `synapse_simulator/datagen/clinical_generator.py` | `object` | Production | 9 |
| `CLS-015` | **`DiagnosticGenerator`** | `synapse_simulator/datagen/diagnostic_generator.py` | `object` | Production | 3 |
| `CLS-016` | **`MasterDataGenerator`** | `synapse_simulator/datagen/master_data.py` | `object` | Production | 6 |
| `CLS-017` | **`PatientContext`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-018` | **`StaffProfile`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-019` | **`RoomRecord`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-020` | **`InventorySnapshot`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-021` | **`GeneratedVitals`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-022` | **`GeneratedLabResult`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-023` | **`GeneratedRadiologyReport`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-024` | **`InvoiceLineItem`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-025` | **`GenerationTrace`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-026` | **`MasterDataSnapshot`** | `synapse_simulator/datagen/models.py` | `BaseModel` | Production | 0 |
| `CLS-027` | **`PatientProfileGenerator`** | `synapse_simulator/datagen/patient_generator.py` | `object` | Production | 5 |
| `CLS-028` | **`BaseDepartmentHandler`** | `synapse_simulator/departments/base.py` | `ABC` | Production | 1 |
| `CLS-029` | **`ClinicalDepartmentHandler`** | `synapse_simulator/departments/clinical.py` | `BaseDepartmentHandler` | Production | 2 |
| `CLS-030` | **`FinanceDepartmentHandler`** | `synapse_simulator/departments/finance.py` | `BaseDepartmentHandler` | Production | 2 |
| `CLS-031` | **`LaboratoryDepartmentHandler`** | `synapse_simulator/departments/laboratory.py` | `BaseDepartmentHandler` | Production | 2 |
| `CLS-032` | **`PharmacyDepartmentHandler`** | `synapse_simulator/departments/pharmacy.py` | `BaseDepartmentHandler` | Production | 2 |
| `CLS-033` | **`RadiologyDepartmentHandler`** | `synapse_simulator/departments/radiology.py` | `BaseDepartmentHandler` | Production | 2 |
| `CLS-034` | **`ExecutionResult`** | `synapse_simulator/engine/orchestrator.py` | `BaseModel` | Production | 0 |
| `CLS-035` | **`ExecutionPipeline`** | `synapse_simulator/engine/orchestrator.py` | `object` | Production | 2 |
| `CLS-036` | **`CSVExporter`** | `synapse_simulator/exporter/csv_exporter.py` | `object` | Production | 17 |
| `CLS-037` | **`DataExporter`** | `synapse_simulator/exporter/data_exporter.py` | `object` | Production | 1 |
| `CLS-038` | **`DocumentGenerator`** | `synapse_simulator/exporter/document_generator.py` | `object` | Production | 11 |
| `CLS-039` | **`EventLogger`** | `synapse_simulator/exporter/event_logger.py` | `object` | Production | 7 |
| `CLS-040` | **`JourneyTraceFormatter`** | `synapse_simulator/exporter/journey_trace.py` | `object` | Production | 1 |
| `CLS-041` | **`LineageMapper`** | `synapse_simulator/exporter/lineage_mapper.py` | `object` | Production | 3 |
| `CLS-042` | **`SimulationBootstrapFactory`** | `synapse_simulator/generator/factory.py` | `object` | Production | 2 |
| `CLS-043` | **`HospitalSimulator`** | `synapse_simulator/generator/hospital_generator.py` | `object` | Production | 4 |
| `CLS-044` | **`MedicalKnowledgeBase`** | `synapse_simulator/knowledge/loader.py` | `object` | Production | 18 |
| `CLS-045` | **`DrugTreatment`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-046` | **`DiagnosisEntry`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-047` | **`AllergyEntry`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-048` | **`ChronicCondition`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-049` | **`AllergyPrevalence`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-050` | **`LabComponent`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-051` | **`LabTestRange`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-052` | **`RadiologyFindings`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-053` | **`VitalsRange`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-054` | **`ServicePricing`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-055` | **`DepartmentRoomConfig`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-056` | **`DepartmentStaffConfig`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-057` | **`DepartmentConfig`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-058` | **`InventoryConfig`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-059` | **`OperatingHoursConfig`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-060` | **`MasterDataConfig`** | `synapse_simulator/knowledge/models.py` | `BaseModel` | Production | 0 |
| `CLS-061` | **`PubMedCache`** | `synapse_simulator/knowledge/pubmed/cache.py` | `object` | Production | 6 |
| `CLS-062` | **`PubMedClient`** | `synapse_simulator/knowledge/pubmed/client.py` | `object` | Production | 5 |
| `CLS-063` | **`KnowledgeExtractor`** | `synapse_simulator/knowledge/pubmed/extractor.py` | `object` | Production | 1 |
| `CLS-064` | **`PubMedArticle`** | `synapse_simulator/knowledge/pubmed/models.py` | `BaseModel` | Production | 0 |
| `CLS-065` | **`BiomedicalEntity`** | `synapse_simulator/knowledge/pubmed/models.py` | `BaseModel` | Production | 0 |
| `CLS-066` | **`KnowledgeRelation`** | `synapse_simulator/knowledge/pubmed/models.py` | `BaseModel` | Production | 0 |
| `CLS-067` | **`TargetQueryConfig`** | `synapse_simulator/knowledge/pubmed/models.py` | `BaseModel` | Production | 0 |
| `CLS-068` | **`PubMedIntegrationConfig`** | `synapse_simulator/knowledge/pubmed/models.py` | `BaseModel` | Production | 0 |
| `CLS-069` | **`TerminologyNormalizer`** | `synapse_simulator/knowledge/pubmed/normalizer.py` | `object` | Production | 2 |
| `CLS-070` | **`PubMedParser`** | `synapse_simulator/knowledge/pubmed/parser.py` | `object` | Production | 2 |
| `CLS-071` | **`PubMedKnowledgeManager`** | `synapse_simulator/knowledge/pubmed/retriever.py` | `object` | Production | 7 |
| `CLS-072` | **`PubMedKnowledgeStore`** | `synapse_simulator/knowledge/pubmed/store.py` | `object` | Production | 7 |
| `CLS-073` | **`KnowledgeValidator`** | `synapse_simulator/knowledge/pubmed/validator.py` | `object` | Production | 3 |
| `CLS-074` | **`RuleEvaluator`** | `synapse_simulator/rules/evaluator.py` | `object` | Production | 7 |
| `CLS-075` | **`PrecedenceLevel`** | `synapse_simulator/rules/models.py` | `IntEnum` | Production | 0 |
| `CLS-076` | **`RuleSourceType`** | `synapse_simulator/rules/models.py` | `str, Enum` | Production | 0 |
| `CLS-077` | **`RuleCategory`** | `synapse_simulator/rules/models.py` | `str, Enum` | Production | 0 |
| `CLS-078` | **`RulePreconditions`** | `synapse_simulator/rules/models.py` | `BaseModel` | Production | 0 |
| `CLS-079` | **`RuleConditions`** | `synapse_simulator/rules/models.py` | `BaseModel` | Production | 0 |
| `CLS-080` | **`StateTransitionRuleEffect`** | `synapse_simulator/rules/models.py` | `BaseModel` | Production | 0 |
| `CLS-081` | **`CrossDepartmentRuleEffect`** | `synapse_simulator/rules/models.py` | `BaseModel` | Production | 0 |
| `CLS-082` | **`TemporalConstraints`** | `synapse_simulator/rules/models.py` | `BaseModel` | Production | 0 |
| `CLS-083` | **`SynapseRule`** | `synapse_simulator/rules/models.py` | `BaseModel` | Production | 0 |
| `CLS-084` | **`RuleRepository`** | `synapse_simulator/rules/repository.py` | `object` | Production | 8 |
| `CLS-085` | **`RuleEngine`** | `synapse_simulator/rules/rule_engine.py` | `object` | Production | 2 |
| `CLS-086` | **`BaseScenario`** | `synapse_simulator/scenarios/base_scenario.py` | `ABC` | Production | 5 |
| `CLS-087` | **`IScenarioProfileHook`** | `synapse_simulator/scenarios/interfaces.py` | `Protocol` | Production | 4 |
| `CLS-088` | **`OutpatientRoutineScenario`** | `synapse_simulator/scenarios/scen_v1_01_opd.py` | `BaseScenario` | Production | 2 |
| `CLS-089` | **`DiagnosticInvestigationScenario`** | `synapse_simulator/scenarios/scen_v1_02_diagnostic.py` | `BaseScenario` | Production | 2 |
| `CLS-090` | **`DrugAllergySafetyHoldScenario`** | `synapse_simulator/scenarios/scen_v1_03_allergy.py` | `BaseScenario` | Production | 4 |
| `CLS-091` | **`InventoryDepletionScenario`** | `synapse_simulator/scenarios/scen_v1_04_inventory.py` | `BaseScenario` | Production | 2 |
| `CLS-092` | **`DocumentType`** | `synapse_simulator/state/document_models.py` | `str, Enum` | Production | 0 |
| `CLS-093` | **`DocumentStatus`** | `synapse_simulator/state/document_models.py` | `str, Enum` | Production | 0 |
| `CLS-094` | **`DocumentMetadata`** | `synapse_simulator/state/document_models.py` | `BaseModel` | Production | 0 |
| `CLS-095` | **`IStateReader`** | `synapse_simulator/state/interfaces.py` | `Protocol` | Production | 1 |
| `CLS-096` | **`IStateWriter`** | `synapse_simulator/state/interfaces.py` | `Protocol` | Production | 1 |
| `CLS-097` | **`IContextBuilder`** | `synapse_simulator/state/interfaces.py` | `Protocol` | Production | 1 |
| `CLS-098` | **`IStateDecisionApplier`** | `synapse_simulator/state/interfaces.py` | `Protocol` | Production | 1 |
| `CLS-099` | **`PatientStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-100` | **`AppointmentStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-101` | **`EncounterStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-102` | **`ConsultationStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-103` | **`LabOrderStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-104` | **`RadOrderStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-105` | **`PrescriptionStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-106` | **`InventoryBatchStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-107` | **`InvoiceStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-108` | **`ActionRequest`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-109` | **`StateTransitionProposal`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-110` | **`CommandProposal`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-111` | **`OutboxEventProposal`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-112` | **`DocumentTriggerProposal`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-113` | **`InputContext`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-114` | **`DecisionStatus`** | `synapse_simulator/state/models.py` | `str, Enum` | Production | 0 |
| `CLS-115` | **`DecisionResult`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-116` | **`DomainEvent`** | `synapse_simulator/state/models.py` | `BaseModel` | Production | 0 |
| `CLS-117` | **`StateManager`** | `synapse_simulator/state/state_manager.py` | `object` | Production | 5 |
| `CLS-118` | **`ITransitionValidator`** | `synapse_simulator/transitions/interfaces.py` | `Protocol` | Production | 2 |
| `CLS-119` | **`BaseStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `object` | Production | 2 |
| `CLS-120` | **`PatientStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-121` | **`AppointmentStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-122` | **`EncounterStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-123` | **`ConsultationStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-124` | **`LabOrderStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-125` | **`RadOrderStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-126` | **`PrescriptionStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-127` | **`InventoryBatchStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-128` | **`InvoiceStateMachine`** | `synapse_simulator/transitions/state_machine.py` | `BaseStateMachine` | Production | 0 |
| `CLS-129` | **`TransitionManager`** | `synapse_simulator/transitions/transition_manager.py` | `object` | Production | 2 |
| `CLS-130` | **`ConsistencyChecker`** | `synapse_simulator/validation/consistency_checker.py` | `object` | Production | 3 |
| `CLS-131` | **`DatasetAuditor`** | `synapse_simulator/validation/dataset_auditor.py` | `object` | Production | 3 |
| `CLS-132` | **`DocumentValidationError`** | `synapse_simulator/validation/document_validator.py` | `Exception` | Production | 0 |
| `CLS-133` | **`DocumentValidator`** | `synapse_simulator/validation/document_validator.py` | `object` | Production | 7 |
| `CLS-134` | **`IntegrityAuditor`** | `synapse_simulator/validation/integrity_auditor.py` | `object` | Production | 12 |
| `CLS-135` | **`WorkflowCoordinator`** | `synapse_simulator/workflows/coordinator.py` | `object` | Production | 4 |
| `CLS-136` | **`JourneyStatus`** | `synapse_simulator/workflows/model.py` | `str, Enum` | Production | 0 |
| `CLS-137` | **`WorkflowStep`** | `synapse_simulator/workflows/model.py` | `BaseModel` | Production | 0 |
| `CLS-138` | **`WorkflowDefinition`** | `synapse_simulator/workflows/model.py` | `BaseModel` | Production | 1 |
| `CLS-139` | **`PatientJourney`** | `synapse_simulator/workflows/model.py` | `BaseModel` | Production | 0 |