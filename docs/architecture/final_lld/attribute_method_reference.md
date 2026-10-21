# SYNAPSE Phase 2 — Complete Attribute & Method Reference

This document provides the full, unabridged symbol reference for every class in the SYNAPSE Phase 2 codebase.

## Module: `synapse_simulator/config.py`

> Simulator configuration settings.

### Class: `SimulatorSettings`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+project_name` (Class attribute)
- `+version` (Class attribute)
- `+environment` (Class attribute)
- `+rules_dir` (Class attribute)
- `+database_url` (Class attribute)
- `+redis_url` (Class attribute)
- `+default_random_seed` (Class attribute)
- `+outbox_batch_size` (Class attribute)
- `+max_causation_depth` (Class attribute)

---

## Module: `synapse_simulator/core/clock.py`

> Simulation Clock: Manages simulated time progression and timestamping.

### Class: `SimulationClock`
- **Docstring:** Manages virtual simulation time advancement.

**Instance Attributes:**
- `-_current_time` (Instance attribute)

**Declared Methods:**
- `+__init__(self, start_time: Optional[datetime]) -> None`
- `+current_time(self) -> datetime` {property}
- `+now(self) -> datetime`
- `+advance_to(self, target_time: datetime) -> datetime`
  *Description:* Advance clock to specified datetime (must be >= current_time).
- `+advance_by_seconds(self, seconds: float) -> datetime`
  *Description:* Advance clock by N seconds.
- `+advance_by_minutes(self, minutes: float) -> datetime`
  *Description:* Advance clock by N minutes.

---

## Module: `synapse_simulator/core/dispatcher.py`

> Event Dispatcher: Registers event handlers and routes emitted events to downstream domain handlers.

### Class: `EventDispatcher`
- **Docstring:** Routes emitted simulation events to registered departmental handlers.

**Declared Methods:**
- `+__init__(self) -> None`
- `+register_handler(self, event_type: str, handler: EventHandlerCallable) -> None`
  *Description:* Register a handler callback for an event type (prevents duplicates).
- `+dispatch(self, event: SimulationEvent) -> List[ActionRequest]`
  *Description:* Dispatch event to all matching handlers and collect generated ActionRequests.
- `+event_history(self) -> List[SimulationEvent]` {property}

---

## Module: `synapse_simulator/core/event_queue.py`

> Priority Queue for Discrete Event Simulation with deterministic ordering.

### Class: `SimulationEvent`
- **Inherits From:** `BaseModel`
- **Docstring:** Event model managed by the simulation priority queue.

**Class Attributes:**
- `+event_id` (Class attribute)
- `+scheduled_at` (Class attribute)
- `+priority` (Class attribute)
- `+event_type` (Class attribute)
- `+source_department` (Class attribute)
- `+target_department` (Class attribute)
- `+scenario_instance_id` (Class attribute)
- `+patient_journey_id` (Class attribute)
- `+correlation_id` (Class attribute)
- `+causation_id` (Class attribute)
- `+causation_depth` (Class attribute)
- `+sequence_number` (Class attribute)
- `+payload` (Class attribute)
- `+cancelled` (Class attribute)

**Declared Methods:**
- `+__lt__(self, other: 'SimulationEvent') -> bool`
  *Description:* Min-heap comparison based on scheduled timestamp, priority, causation depth, and sequence number.

---

### Class: `EventQueue`
- **Docstring:** Min-heap Priority Queue ordered by event timestamp and sequence number.

**Declared Methods:**
- `+__init__(self) -> None`
- `+push(self, event: SimulationEvent) -> None`
  *Description:* Schedule a new event into the priority queue.
- `+pop(self) -> Optional[SimulationEvent]`
  *Description:* Pop the next non-cancelled event in timestamp order.
- `+peek(self) -> Optional[SimulationEvent]`
  *Description:* Peek at the next non-cancelled event without removing it.
- `+cancel(self, event_id: str) -> bool`
  *Description:* Mark an event as cancelled.
- `+is_empty(self) -> bool`
- `+size(self) -> int`

---

## Module: `synapse_simulator/core/interfaces.py`

> Core Protocols: Defines structural typing contracts for simulation core components (DIP & ISP).

### Class: `IClock`
- **Inherits From:** `Protocol`
- **Docstring:** Monotonic simulation clock protocol.

**Declared Methods:**
- `+now(self) -> datetime`
- `+advance_to(self, target_time: datetime) -> datetime`
- `+advance_by_seconds(self, seconds: float) -> datetime`
- `+advance_by_minutes(self, minutes: float) -> datetime`

---

### Class: `IScheduler`
- **Inherits From:** `Protocol`
- **Docstring:** Priority heap action scheduler protocol.

**Declared Methods:**
- `+schedule_action(self, action_request: ActionRequest, scheduled_at: datetime, causation_depth: int) -> None`
- `+peek_next_due_time(self) -> Optional[datetime]`
- `+get_due_actions(self, current_time: datetime) -> List[Any]`
- `+invalidate_entity_actions(self, entity_table: str, entity_id: str) -> int`

---

### Class: `IEventQueue`
- **Inherits From:** `Protocol`
- **Docstring:** Priority event queue protocol.

**Declared Methods:**
- `+push(self, event: SimulationEvent) -> None`
- `+pop(self) -> Optional[SimulationEvent]`
- `+peek(self) -> Optional[SimulationEvent]`
- `+is_empty(self) -> bool`

---

### Class: `IEventDispatcher`
- **Inherits From:** `Protocol`
- **Docstring:** Event-to-handler routing protocol.

**Declared Methods:**
- `+register_handler(self, event_type: str, handler: Any) -> None`
- `+dispatch(self, event: SimulationEvent) -> List[ActionRequest]`

---

## Module: `synapse_simulator/core/scheduler.py`

> Future Action Scheduler: Manages scheduled future actions, priority ordering, cancellations, and state-change invalidations.

### Class: `ScheduledFutureAction`
- **Inherits From:** `BaseModel`
- **Docstring:** Represents a scheduled future action in the simulation timeline.

**Class Attributes:**
- `+action_id` (Class attribute)
- `+scheduled_at` (Class attribute)
- `+priority` (Class attribute)
- `+causation_depth` (Class attribute)
- `+sequence_number` (Class attribute)
- `+action_request` (Class attribute)
- `+status` (Class attribute)
- `+target_entity_key` (Class attribute)

**Declared Methods:**
- `+__lt__(self, other: 'ScheduledFutureAction') -> bool`
  *Description:* Deterministic comparison order: scheduled_at -> priority -> causation_depth -> sequence_number.

---

### Class: `FutureActionScheduler`
- **Docstring:** Heap-based Future Action Scheduler supporting deterministic ordering and state invalidation.

**Declared Methods:**
- `+__init__(self) -> None`
- `+schedule_action(self, action_request: ActionRequest, scheduled_at: datetime, priority: int, causation_depth: int) -> ScheduledFutureAction`
  *Description:* Schedule an action for execution at a future simulated timestamp.
- `+get_due_actions(self, current_time: datetime) -> List[ScheduledFutureAction]`
  *Description:* Retrieve all pending actions whose scheduled timestamp is <= current_time in deterministic order.
- `+peek_next_due_time(self) -> Optional[datetime]`
  *Description:* Peek timestamp of the next pending action.
- `+cancel_action(self, action_id: str) -> bool`
  *Description:* Mark a pending action as CANCELLED.
- `+reschedule_action(self, action_id: str, new_time: datetime) -> bool`
  *Description:* Reschedule a pending action to a new timestamp.
- `+invalidate_entity_actions(self, target_entity_table: str, target_entity_id: str) -> int`
  *Description:* Invalidate all pending scheduled actions for an entity whose state changed.
- `+size(self) -> int`
  *Description:* Count remaining pending actions.

---

## Module: `synapse_simulator/core/simulation_engine.py`

> Stage 6 Simulation Engine: Time-Driven & Event-Driven Core Execution Engine.

### Class: `SimulationEngine`
- **Docstring:** Core Time-Driven & Event-Driven Simulation Engine for Synapse Phase 2.

**Instance Attributes:**
- `-clock` (Instance attribute)
- `-dispatcher` (Instance attribute)
- `-event_queue` (Instance attribute)
- `-pipeline` (Instance attribute)
- `-rule_engine` (Instance attribute)
- `-scheduler` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, clock: Optional[SimulationClock], scheduler: Optional[FutureActionScheduler], event_queue: Optional[EventQueue], dispatcher: Optional[EventDispatcher], state_manager: Optional[StateManager], rule_engine: Optional[RuleEngine], execution_pipeline: Optional[ExecutionPipeline]) -> None`
- `+step(self) -> bool`
  *Description:* Process the single next temporal item (event or scheduled action). Returns True if processed, False if queue empty.
- `+run_until(self, until_time: Optional[datetime], max_events: int) -> List[DomainEvent]`
  *Description:* Run simulation loop until end time or max events limit reached.
- `+_process_simulation_event(self, event: SimulationEvent) -> None`
  *Description:* Process a simulation event by advancing clock and generating action proposals.
- `+_process_scheduled_action(self, scheduled_action: ScheduledFutureAction) -> Tuple[ExecutionResult, DomainEvent]`
  *Description:* Execute a scheduled action through ExecutionPipeline, emitting formal DomainEvents.

---

## Module: `synapse_simulator/datagen/billing_generator.py`

### Class: `BillingGenerator`

**Instance Attributes:**
- `-rng` (Instance attribute)

**Declared Methods:**
- `+__init__(self, rng: random.Random) -> None`
- `+generate_invoice(self, charges: List[InvoiceLineItem]) -> Dict[str, Any]`

---

## Module: `synapse_simulator/datagen/clinical_generator.py`

> Clinical Entity Generator: Context-aware generation of appointments, consultations,
diagnoses, vitals, and prescriptions. Consumes PatientContext + MedicalKnowledgeBase.

### Class: `ClinicalEntityGenerator`
- **Docstring:** Generates clinical records driven by patient context and medical knowledge.

**Instance Attributes:**
- `-kb` (Instance attribute)
- `-master_data` (Instance attribute)
- `-rng` (Instance attribute)

**Declared Methods:**
- `+__init__(self, knowledge_base: MedicalKnowledgeBase, master_data: MasterDataSnapshot, rng: random.Random) -> None`
- `+assign_doctor(self, patient: PatientContext) -> StaffProfile`
  *Description:* Assign a doctor from the master data pool.
- `+assign_room(self) -> str`
  *Description:* Assign an OPD consultation room.
- `+select_diagnosis(self, patient: PatientContext) -> DiagnosisEntry`
  *Description:* Select a contextually appropriate diagnosis for the patient.

Filters by:
- Patient age range
- Gender bias (if any)
- Weighted random selection from valid candidates
- `+select_medication(self, patient: PatientContext, diagnosis: DiagnosisEntry, force_conflict: bool) -> Tuple[DrugTreatment, bool]`
  *Description:* Select a medication for the diagnosis, respecting allergy constraints.

Args:
    patient: Patient context with allergy profile.
    diagnosis: Selected diagnosis.
    force_conflict: If True, intentionally pick a conflicting drug (for SCEN-V1-03).

Returns:
    Tuple of (selected treatment, is_allergy_conflict).
- `+generate_vitals(self, patient: PatientContext, diagnosis: DiagnosisEntry) -> GeneratedVitals`
  *Description:* Generate physiologically plausible vitals for patient + diagnosis context.

If diagnosis has fever-related symptoms, use febrile temperature range.
- `+generate_appointment_data(self, patient: PatientContext, appointment_id: str, scheduled_time: datetime) -> Dict[str, Any]`
  *Description:* Generate a complete appointment entity record.
- `+generate_consultation_data(self, patient: PatientContext, consultation_id: str, appointment_id: str, diagnosis: DiagnosisEntry, vitals: GeneratedVitals) -> Dict[str, Any]`
  *Description:* Generate a consultation record with diagnosis and vitals.
- `+generate_prescription_data(self, patient: PatientContext, prescription_id: str, consultation_id: str, treatment: DrugTreatment, is_conflict: bool) -> Dict[str, Any]`
  *Description:* Generate a prescription record from selected treatment.

---

## Module: `synapse_simulator/datagen/diagnostic_generator.py`

### Class: `DiagnosticGenerator`

**Instance Attributes:**
- `-rng` (Instance attribute)

**Declared Methods:**
- `+__init__(self, rng: random.Random) -> None`
- `+generate_lab_result(self, context: Any) -> GeneratedLabResult`
- `+generate_radiology_report(self, context: Any) -> GeneratedRadiologyReport`

---

## Module: `synapse_simulator/datagen/master_data.py`

> Master Data Generator: Generates hospital reference data (departments, staff, rooms, inventory).
Runs ONCE per simulation run. All patient journeys reference this shared master data.

### Class: `MasterDataGenerator`
- **Docstring:** Generates deterministic hospital master data from configuration.

**Instance Attributes:**
- `-fake` (Instance attribute)
- `-kb` (Instance attribute)
- `-rng` (Instance attribute)

**Declared Methods:**
- `+__init__(self, knowledge_base: MedicalKnowledgeBase, rng: random.Random) -> None`
- `+generate(self) -> MasterDataSnapshot`
  *Description:* Generate complete master data snapshot.
- `+seed_state_manager(self, state_manager: StateManager, snapshot: MasterDataSnapshot) -> None`
  *Description:* Seed StateManager with generated master data inventory batches.
- `+_generate_staff(self) -> List[StaffProfile]`
  *Description:* Generate staff profiles from department config.
- `+_generate_rooms(self) -> List[RoomRecord]`
  *Description:* Generate room records from department config.
- `+_generate_inventory(self) -> List[InventorySnapshot]`
  *Description:* Generate initial inventory batches from config.

---

## Module: `synapse_simulator/datagen/models.py`

> Data Generation Models: Persistent context objects that flow through the generation pipeline.

### Class: `PatientContext`
- **Inherits From:** `BaseModel`
- **Docstring:** Persistent patient context that flows through the entire journey.
Once created, this context is consumed by all downstream generators.

**Class Attributes:**
- `+patient_id` (Class attribute)
- `+name` (Class attribute)
- `+age` (Class attribute)
- `+gender` (Class attribute)
- `+allergies` (Class attribute)
- `+chronic_conditions` (Class attribute)
- `+insurance_type` (Class attribute)
- `+blood_group` (Class attribute)
- `+scenario_id` (Class attribute)
- `+encounter_id` (Class attribute)
- `+diagnosis_code` (Class attribute)
- `+diagnosis_name` (Class attribute)
- `+assigned_doctor_id` (Class attribute)
- `+assigned_room_id` (Class attribute)
- `+force_conflict` (Class attribute)

---

### Class: `StaffProfile`
- **Inherits From:** `BaseModel`
- **Docstring:** Generated staff member profile.

**Class Attributes:**
- `+staff_id` (Class attribute)
- `+name` (Class attribute)
- `+role` (Class attribute)
- `+department_id` (Class attribute)
- `+specialization` (Class attribute)
- `+qualification` (Class attribute)

---

### Class: `RoomRecord`
- **Inherits From:** `BaseModel`
- **Docstring:** Generated room/location record.

**Class Attributes:**
- `+room_id` (Class attribute)
- `+room_name` (Class attribute)
- `+department_id` (Class attribute)
- `+floor` (Class attribute)
- `+room_type` (Class attribute)

---

### Class: `InventorySnapshot`
- **Inherits From:** `BaseModel`
- **Docstring:** Runtime inventory batch state for a single drug type.

**Class Attributes:**
- `+batch_id` (Class attribute)
- `+drug_name` (Class attribute)
- `+drug_class` (Class attribute)
- `+quantity_available` (Class attribute)
- `+quantity_initial` (Class attribute)
- `+unit_cost` (Class attribute)
- `+status` (Class attribute)

---

### Class: `GeneratedVitals`
- **Inherits From:** `BaseModel`
- **Docstring:** Vitals snapshot for a consultation.

**Class Attributes:**
- `+temperature_c` (Class attribute)
- `+heart_rate_bpm` (Class attribute)
- `+systolic_bp` (Class attribute)
- `+diastolic_bp` (Class attribute)
- `+respiratory_rate` (Class attribute)
- `+spo2_percent` (Class attribute)

---

### Class: `GeneratedLabResult`
- **Inherits From:** `BaseModel`
- **Docstring:** A single lab test result with all component values.

**Class Attributes:**
- `+test_name` (Class attribute)
- `+components` (Class attribute)
- `+is_abnormal` (Class attribute)
- `+ordered_at` (Class attribute)
- `+resulted_at` (Class attribute)

---

### Class: `GeneratedRadiologyReport`
- **Inherits From:** `BaseModel`
- **Docstring:** A radiology imaging report.

**Class Attributes:**
- `+imaging_type` (Class attribute)
- `+findings` (Class attribute)
- `+impression` (Class attribute)
- `+is_abnormal` (Class attribute)
- `+ordered_at` (Class attribute)
- `+reported_at` (Class attribute)

---

### Class: `InvoiceLineItem`
- **Inherits From:** `BaseModel`
- **Docstring:** A single line item on a patient invoice.

**Class Attributes:**
- `+service_type` (Class attribute)
- `+service_name` (Class attribute)
- `+quantity` (Class attribute)
- `+unit_price` (Class attribute)
- `+total_price` (Class attribute)
- `+source_entity_id` (Class attribute)

---

### Class: `GenerationTrace`
- **Inherits From:** `BaseModel`
- **Docstring:** Traceability record: why was this entity generated?

**Class Attributes:**
- `+entity_table` (Class attribute)
- `+entity_id` (Class attribute)
- `+patient_id` (Class attribute)
- `+journey_id` (Class attribute)
- `+scenario_id` (Class attribute)
- `+caused_by_action` (Class attribute)
- `+caused_by_rule` (Class attribute)
- `+generation_timestamp` (Class attribute)
- `+generator_class` (Class attribute)
- `+context_snapshot` (Class attribute)

---

### Class: `MasterDataSnapshot`
- **Inherits From:** `BaseModel`
- **Docstring:** Complete generated master data for a simulation run.

**Class Attributes:**
- `+departments` (Class attribute)
- `+staff` (Class attribute)
- `+rooms` (Class attribute)
- `+inventory` (Class attribute)
- `+doctors` (Class attribute)
- `+pharmacists` (Class attribute)
- `+lab_technicians` (Class attribute)
- `+drug_batch_index` (Class attribute)

---

## Module: `synapse_simulator/datagen/patient_generator.py`

> Patient Profile Generator: Context-aware synthetic patient generation.
Attributes are NOT independent — age constrains conditions, allergies constrain medications,
and scenario requirements override defaults.

### Class: `PatientProfileGenerator`
- **Docstring:** Generates contextually consistent synthetic patient profiles.

**Instance Attributes:**
- `-fake` (Instance attribute)
- `-kb` (Instance attribute)
- `-rng` (Instance attribute)

**Declared Methods:**
- `+__init__(self, knowledge_base: MedicalKnowledgeBase, rng: random.Random) -> None`
- `+generate_patient(self, scenario_id: str, force_allergy: Optional[str], force_age_range: Optional[tuple]) -> PatientContext`
  *Description:* Generate a single patient profile with contextual consistency.

Args:
    scenario_id: Scenario this patient is assigned to.
    force_allergy: Force a specific allergy (e.g., for SCEN-V1-03).
    force_age_range: Override age range (min, max).
- `+_generate_age(self) -> int`
  *Description:* Generate age with realistic hospital OPD distribution.
- `+_generate_allergies(self, force_allergy: Optional[str]) -> List[str]`
  *Description:* Generate allergies using population prevalence rates.
- `+_generate_chronic_conditions(self, age: int) -> List[str]`
  *Description:* Generate chronic conditions correlated with patient age.

---

## Module: `synapse_simulator/departments/base.py`

> Base Department Handler abstract class.

### Class: `BaseDepartmentHandler`
- **Inherits From:** `ABC`
- **Docstring:** Abstract base class for departmental event handlers.

**Class Attributes:**
- `+department_name` (Class attribute)

**Declared Methods:**
- `+handle_event(self, event: SimulationEvent) -> List[ActionRequest]` {abstract}
  *Description:* Convert incoming simulation event into actionable domain ActionRequests.

---

## Module: `synapse_simulator/departments/clinical.py`

> Clinical Department Handler.

### Class: `ClinicalDepartmentHandler`
- **Inherits From:** `BaseDepartmentHandler`

**Class Attributes:**
- `+department_name` (Class attribute)

**Instance Attributes:**
- `-clinical_gen` (Instance attribute)
- `-patient_contexts` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, clinical_gen, patient_contexts, state_manager) -> None`
- `+handle_event(self, event: SimulationEvent) -> List[ActionRequest]`

---

## Module: `synapse_simulator/departments/finance.py`

> Finance Department Handler.

### Class: `FinanceDepartmentHandler`
- **Inherits From:** `BaseDepartmentHandler`

**Class Attributes:**
- `+department_name` (Class attribute)

**Instance Attributes:**
- `-billing_gen` (Instance attribute)
- `-patient_contexts` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, billing_gen, patient_contexts, state_manager) -> None`
- `+handle_event(self, event: SimulationEvent) -> List[ActionRequest]`

---

## Module: `synapse_simulator/departments/laboratory.py`

> Laboratory Department Handler.

### Class: `LaboratoryDepartmentHandler`
- **Inherits From:** `BaseDepartmentHandler`

**Class Attributes:**
- `+department_name` (Class attribute)

**Instance Attributes:**
- `-diagnostic_gen` (Instance attribute)
- `-patient_contexts` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, diagnostic_gen, patient_contexts, state_manager) -> None`
- `+handle_event(self, event: SimulationEvent) -> List[ActionRequest]`

---

## Module: `synapse_simulator/departments/pharmacy.py`

> Pharmacy Department Handler.

### Class: `PharmacyDepartmentHandler`
- **Inherits From:** `BaseDepartmentHandler`

**Class Attributes:**
- `+department_name` (Class attribute)

**Instance Attributes:**
- `-clinical_gen` (Instance attribute)
- `-patient_contexts` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, clinical_gen, patient_contexts, state_manager) -> None`
- `+handle_event(self, event: SimulationEvent) -> List[ActionRequest]`

---

## Module: `synapse_simulator/departments/radiology.py`

> Radiology Department Handler.

### Class: `RadiologyDepartmentHandler`
- **Inherits From:** `BaseDepartmentHandler`

**Class Attributes:**
- `+department_name` (Class attribute)

**Instance Attributes:**
- `-diagnostic_gen` (Instance attribute)
- `-patient_contexts` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, diagnostic_gen, patient_contexts, state_manager) -> None`
- `+handle_event(self, event: SimulationEvent) -> List[ActionRequest]`

---

## Module: `synapse_simulator/engine/orchestrator.py`

> Execution Pipeline Orchestrator: Coordinates StateManager, RuleEngine, and TransitionManager.

### Class: `ExecutionResult`
- **Inherits From:** `BaseModel`
- **Docstring:** Result of an action execution through the pipeline.

**Class Attributes:**
- `+success` (Class attribute)
- `+context` (Class attribute)
- `+decision` (Class attribute)
- `+state_applied` (Class attribute)
- `+causation_depth` (Class attribute)
- `+emitted_events` (Class attribute)
- `+command_proposals` (Class attribute)
- `+document_triggers` (Class attribute)

---

### Class: `ExecutionPipeline`
- **Docstring:** Core execution engine orchestrator connecting state management, rule evaluation, and event generation.

**Instance Attributes:**
- `-rule_engine` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, state_manager: StateManager, rule_engine: RuleEngine) -> None`
- `+execute_action(self, action: ActionRequest, simulated_timestamp: datetime, scenario_id: str, department_id: str, patient_id: Optional[str], causation_depth: int) -> ExecutionResult`
  *Description:* Process an ActionRequest through context build, rule evaluation, state application, and event output.

---

## Module: `synapse_simulator/exporter/csv_exporter.py`

> CSV Exporter for SYNAPSE Phase 2 Synthetic Hospital Simulator.
Centralized, deterministic export layer that serializes all validated structured simulation entities,
events, patient journeys, rule decisions, billing, inventory, and validation reports to UTF-8 CSV files.

### Class: `CSVExporter`
- **Docstring:** Exports structured simulation state and history into normalized, relational CSV datasets.

**Instance Attributes:**
- `-_cached_patient_enc_map` (Instance attribute)
- `-committed_events` (Instance attribute)
- `-dirs` (Instance attribute)
- `-journeys` (Instance attribute)
- `-master_data` (Instance attribute)
- `-metrics` (Instance attribute)
- `-output_dir` (Instance attribute)
- `-patient_contexts` (Instance attribute)
- `-state_manager` (Instance attribute)
- `-trace_log` (Instance attribute)

**Declared Methods:**
- `+__init__(self, state_manager: StateManager, master_data: MasterDataSnapshot, patient_contexts: Dict[str, PatientContext], committed_events: List[DomainEvent], journeys: List[PatientJourney], trace_log: Optional[List[Dict[str, Any]]], metrics: Optional[Dict[str, Any]], output_dir: Optional[Path]) -> None`
- `+get_canonical_encounter_id(self, pid: Optional[str]) -> str`
  *Description:* Look up the canonical encounter_id for a patient_id.
- `+_write_csv(self, file_path: Path, headers: List[str], rows: List[List[Any]]) -> Optional[Path]`
  *Description:* Write rows to UTF-8 CSV if rows exist. Avoid writing empty files unless explicitly required.
- `+export_all(self) -> Dict[str, Path]`
  *Description:* Export all structured datasets to CSV.
- `+_export_master_data(self) -> Dict[str, Path]`
- `+_export_patient_data(self) -> Dict[str, Path]`
- `+_export_clinical_data(self) -> Dict[str, Path]`
- `+_export_diagnostic_data(self) -> Dict[str, Path]`
- `+_export_pharmacy_data(self) -> Dict[str, Path]`
- `+_export_operational_data(self) -> Dict[str, Path]`
- `+_export_billing_data(self) -> Dict[str, Path]`
- `+_export_events(self) -> Dict[str, Path]`
- `+_export_journeys(self) -> Dict[str, Path]`
- `+_export_rule_decisions(self) -> Dict[str, Path]`
- `+_export_metadata(self) -> Dict[str, Path]`
- `+_validate_simplified_records(self, patient_rows: List[List[Any]], enc_rows: List[List[Any]], cond_rows: List[List[Any]], sym_rows: List[List[Any]], med_rows: List[List[Any]], lab_rows: List[List[Any]], rad_rows: List[List[Any]], inv_rows: List[List[Any]], pay_rows: List[List[Any]], evt_rows: List[List[Any]], journey_rows: List[List[Any]]) -> None`
  *Description:* Validate referential integrity, patient consistency, provenance, and temporal rules before export.
Fails loudly if any integrity invariant is violated.
- `+export_simplified_dataset(self, target_dir: Optional[Path]) -> Dict[str, Path]`
  *Description:* Export simplified flat relational CSV dataset to target_dir (e.g. data/synthetic/*.csv).

---

## Module: `synapse_simulator/exporter/data_exporter.py`

> Data Exporter: Serializes simulation transactions, state snapshots, and telemetry to files.

### Class: `DataExporter`
- **Docstring:** Exports synthetic hospital simulation results to JSON/CSV files.

**Declared Methods:**
- `+export_to_json(output_dir: Path, summary_data: Dict[str, Any], filename: str) -> Path` {static}
  *Description:* Export simulation metrics and state snapshots to a JSON file.

---

## Module: `synapse_simulator/exporter/document_generator.py`

> Document Generator for Synapse Phase 2.
Assembles and renders hospital documents (Prescriptions, Invoices, LabReports, RadReports, DischargeSummaries)
directly from validated structured StateManager database snapshots and DomainEvent history.

### Class: `DocumentGenerator`
- **Docstring:** Assembles and exports structured JSON metadata and human-readable Markdown documents.

**Instance Attributes:**
- `-committed_events` (Instance attribute)
- `-dirs` (Instance attribute)
- `-output_dir` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, state_manager: StateManager, committed_events: List[DomainEvent], output_dir: Path) -> None`
- `+generate_all(self) -> Dict[str, DocumentMetadata]`
  *Description:* Iterate over state manager and generate all appropriate documents.
- `+_write_document(self, doc_type: DocumentType, doc_id: str, patient_id: str, journey_id: str, scenario_id: str, source_table: str, source_id: str, source_action_id: str, source_event_id: str, content: str, payload: Dict[str, Any], created_at: Optional[datetime]) -> DocumentMetadata`
  *Description:* Helper to write checksummed files and return Pydantic metadata.
- `+_generate_prescriptions(self) -> None`
  *Description:* Assembles prescription documents and safety hold alerts from pharmacy tables.
- `+_generate_lab_reports(self) -> None`
  *Description:* Generates structured laboratory reports for completed orders.
- `+_generate_rad_reports(self) -> None`
  *Description:* Generates structured radiology imaging reports.
- `+_generate_invoices(self) -> None`
  *Description:* Assembles itemized billing invoices based on generated charges.
- `+_generate_discharge_summaries(self) -> None`
  *Description:* Assembles discharge summary documents at the end of patient journeys.
- `+_find_first_event(self, event_type: str, entity_id: Optional[str], journey_id: Optional[str]) -> Optional[DomainEvent]`
- `+_find_last_event_for_journey(self, journey_id: str) -> Optional[DomainEvent]`
- `+_get_scenario_id(self, instance_id: str) -> str`

---

## Module: `synapse_simulator/exporter/event_logger.py`

> Event Logger for Synapse Phase 2.
Persists domain events in JSON Lines format (events.jsonl) and provides query interfaces.

### Class: `EventLogger`
- **Docstring:** Manages sequential domain event storage, persistence, and querying.

**Instance Attributes:**
- `-file_path` (Instance attribute)
- `-output_dir` (Instance attribute)

**Declared Methods:**
- `+__init__(self, output_dir: Path) -> None`
- `+persist_events(self, events: List[DomainEvent]) -> Path`
  *Description:* Write domain events sequentially to events.jsonl.
- `+load_events(self) -> List[Dict[str, Any]]`
  *Description:* Read all persisted domain events from events.jsonl.
- `+query_by_journey_id(self, journey_id: str) -> List[Dict[str, Any]]`
  *Description:* Filter events belonging to a specific patient journey.
- `+query_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]`
  *Description:* Filter events belonging to a specific correlation transaction ID.
- `+query_by_entity_id(self, entity_id: str) -> List[Dict[str, Any]]`
  *Description:* Filter events related to a specific operational entity.
- `+query_by_event_type(self, event_type: str) -> List[Dict[str, Any]]`
  *Description:* Filter events by their event type classification.

---

## Module: `synapse_simulator/exporter/journey_trace.py`

> Journey Trace Formatter: Produces human-readable causal execution traces for Patient Journeys.

### Class: `JourneyTraceFormatter`
- **Docstring:** Formats PatientJourney execution data into human-readable causal traces.

**Declared Methods:**
- `+format_journey_trace(journey: PatientJourney) -> str` {static}

---

## Module: `synapse_simulator/exporter/lineage_mapper.py`

> Lineage Mapper for Synapse Phase 2.
Maps causal connections across: Action -> State Transition -> Event -> Document.

### Class: `LineageMapper`
- **Docstring:** Traces and exports structured lineage connections between events, states, and documents.

**Instance Attributes:**
- `-file_path` (Instance attribute)
- `-output_dir` (Instance attribute)

**Declared Methods:**
- `+__init__(self, output_dir: Path) -> None`
- `+generate_map(self, committed_events: List[DomainEvent], generated_docs: Dict[str, DocumentMetadata]) -> Path`
  *Description:* Construct and persist lineage_map.json from event log and generated documents.
- `+load_lineage_map(self) -> Dict[str, Any]`
  *Description:* Read and return lineage map content.

---

## Module: `synapse_simulator/generator/factory.py`

> Simulation Bootstrap Factory: Separates component instantiation, dependency resolution,
and handler wiring from the HospitalSimulator facade (SRP & DIP compliance).

### Class: `SimulationBootstrapFactory`
- **Docstring:** Assembles all simulation engines, data generators, and department handlers.

**Declared Methods:**
- `+bootstrap(sim: Any, random_seed: int, start_time: Optional[datetime], enable_pubmed: bool, pubmed_store_dir: Optional[Any], offline_mode: bool) -> None` {static}
  *Description:* Instantiate and wire simulation components into the simulator facade.
- `+wire_department_handlers(sim: Any) -> None` {static}
  *Description:* Instantiate departmental handlers and wire event listeners to dispatcher.

---

## Module: `synapse_simulator/generator/hospital_generator.py`

> Large-Scale Synthetic Hospital Simulator Engine with Stage 7 Workflow Integration.

### Class: `HospitalSimulator`
- **Docstring:** Orchestrates workflow-driven synthetic hospital patient journeys and cross-department execution.

**Declared Methods:**
- `+__init__(self, random_seed: int, start_time: Optional[datetime], enable_pubmed: bool, pubmed_store_dir: Optional[Any], offline_mode: bool) -> None`
- `+_setup_department_handlers(self) -> None`
  *Description:* Delegate department handler registration to factory.
- `+spawn_patients(self, patient_count: int) -> List[str]`
  *Description:* Generate and schedule N synthetic patient scenario journeys using WorkflowCoordinator.
- `+run(self, max_events: int, output_dir: Optional[str]) -> Dict[str, Any]`
  *Description:* Execute discrete event simulation loop until queue is empty or max_events reached.

---

## Module: `synapse_simulator/knowledge/loader.py`

> Medical Knowledge Base Loader: Loads and indexes curated medical domain knowledge from YAML.
Single access point for all diagnosis-treatment-drug-allergy-lab knowledge.

### Class: `MedicalKnowledgeBase`
- **Docstring:** Loads, validates, and provides lookup access to curated medical domain knowledge.

**Class Attributes:**
- `+DRUG_METADATA_DEFAULTS` (Class attribute)

**Instance Attributes:**
- `-knowledge_dir` (Instance attribute)
- `-master_data_config` (Instance attribute)
- `-pubmed_manager` (Instance attribute)
- `-service_pricing` (Instance attribute)

**Declared Methods:**
- `+__init__(self, knowledge_dir: Optional[Path]) -> None`
- `+load(self, enable_pubmed: bool, pubmed_store_dir: Optional[Path], offline_mode: bool) -> None`
  *Description:* Load all knowledge YAML files and build indexes, optionally enriching with PubMed evidence.
- `+load_pubmed_evidence(self, store_dir: Optional[Path], offline_mode: bool) -> None`
  *Description:* Populate medical knowledge diagnoses with validated PubMed treatment relationships via PubMedKnowledgeManager.
- `+_enrich_single_diagnosis_from_pubmed(self, diag: DiagnosisEntry, offline_mode: bool) -> None`
  *Description:* Retrieve and attach validated PubMed treatment evidence to a diagnosis.
- `+_load_medical_knowledge(self) -> None`
  *Description:* Load medical_knowledge.yaml.
- `+_load_master_data_config(self) -> None`
  *Description:* Load master_data_config.yaml.
- `+get_diagnosis_by_code(self, code: str) -> Optional[DiagnosisEntry]`
  *Description:* Retrieve a diagnosis by ICD-10 code.
- `+get_diagnoses_by_category(self, category: str) -> List[DiagnosisEntry]`
  *Description:* Retrieve all diagnoses in a category.
- `+get_diagnoses_for_age(self, age: int) -> List[DiagnosisEntry]`
  *Description:* Filter diagnoses valid for a patient's age.
- `+get_treatments_for_diagnosis(self, code: str) -> List[DrugTreatment]`
  *Description:* Get treatment options for a diagnosis code.
Dynamically enriches from PubMed if not already populated.
- `+get_allergy_conflicts(self, patient_allergies: List[str], drug_class: str) -> List[str]`
  *Description:* Check if a drug class conflicts with any of the patient's allergies.
Returns list of conflicting allergy names.
- `+is_drug_safe_for_patient(self, drug_name: str, drug_class: str, patient_allergies: List[str]) -> bool`
  *Description:* Check if a specific drug is safe given patient allergies.
- `+get_safe_alternatives(self, allergy_name: str) -> List[DrugTreatment]`
  *Description:* Get safe drug alternatives for a specific allergy.
- `+get_compatible_drugs_for_patient(self, diagnosis_code: str, patient_allergies: List[str]) -> List[DrugTreatment]`
  *Description:* Get treatments for a diagnosis that are safe for the patient's allergy profile.
- `+get_lab_test_range(self, test_name: str) -> Optional[LabTestRange]`
  *Description:* Get reference range for a lab test.
- `+get_service_price(self, service_type: str, service_name: str) -> float`
  *Description:* Get price for a hospital service.
- `+get_vitals_range_for_age(self, age: int) -> VitalsRange`
  *Description:* Get appropriate vitals range for a patient's age.
- `+get_radiology_findings(self, imaging_type: str) -> Optional[RadiologyFindings]`
  *Description:* Get template findings for an imaging type.

---

## Module: `synapse_simulator/knowledge/models.py`

> Pydantic data models for medical knowledge configuration.

### Class: `DrugTreatment`
- **Inherits From:** `BaseModel`
- **Docstring:** A single drug treatment option for a diagnosis.

**Class Attributes:**
- `+drug` (Class attribute)
- `+drug_class` (Class attribute)
- `+dosage` (Class attribute)
- `+frequency` (Class attribute)
- `+duration_days` (Class attribute)
- `+source` (Class attribute)
- `+evidence_ids` (Class attribute)

---

### Class: `DiagnosisEntry`
- **Inherits From:** `BaseModel`
- **Docstring:** A curated diagnosis with symptoms, treatments, labs, and imaging.

**Class Attributes:**
- `+code` (Class attribute)
- `+name` (Class attribute)
- `+category` (Class attribute)
- `+age_range` (Class attribute)
- `+gender_bias` (Class attribute)
- `+symptoms` (Class attribute)
- `+treatments` (Class attribute)
- `+lab_tests` (Class attribute)
- `+imaging` (Class attribute)

---

### Class: `AllergyEntry`
- **Inherits From:** `BaseModel`
- **Docstring:** Cross-reactivity entry for a specific allergy.

**Class Attributes:**
- `+cross_reactive_classes` (Class attribute)
- `+cross_reactive_drugs` (Class attribute)
- `+safe_alternatives` (Class attribute)

---

### Class: `ChronicCondition`
- **Inherits From:** `BaseModel`
- **Docstring:** Age-correlated chronic condition for patient generation.

**Class Attributes:**
- `+name` (Class attribute)
- `+min_age` (Class attribute)
- `+prevalence_percent` (Class attribute)

---

### Class: `AllergyPrevalence`
- **Inherits From:** `BaseModel`
- **Docstring:** Population-level allergy prevalence for patient generation.

**Class Attributes:**
- `+name` (Class attribute)
- `+prevalence_percent` (Class attribute)

---

### Class: `LabComponent`
- **Inherits From:** `BaseModel`
- **Docstring:** A single measurable lab component with reference ranges.

**Class Attributes:**
- `+name` (Class attribute)
- `+unit` (Class attribute)
- `+normal_range` (Class attribute)
- `+critical_low` (Class attribute)
- `+critical_high` (Class attribute)

---

### Class: `LabTestRange`
- **Inherits From:** `BaseModel`
- **Docstring:** Lab test with its measurable components.

**Class Attributes:**
- `+components` (Class attribute)

---

### Class: `RadiologyFindings`
- **Inherits From:** `BaseModel`
- **Docstring:** Template findings for radiology imaging types.

**Class Attributes:**
- `+normal` (Class attribute)
- `+abnormal` (Class attribute)

---

### Class: `VitalsRange`
- **Inherits From:** `BaseModel`
- **Docstring:** Physiological vitals ranges by age group.

**Class Attributes:**
- `+age_range` (Class attribute)
- `+temperature_c` (Class attribute)
- `+heart_rate_bpm` (Class attribute)
- `+systolic_bp` (Class attribute)
- `+diastolic_bp` (Class attribute)
- `+respiratory_rate` (Class attribute)
- `+spo2_percent` (Class attribute)

---

### Class: `ServicePricing`
- **Inherits From:** `BaseModel`
- **Docstring:** Hospital service pricing schedule.

**Class Attributes:**
- `+consultation_fee` (Class attribute)
- `+follow_up_fee` (Class attribute)
- `+lab_test_fees` (Class attribute)
- `+imaging_fees` (Class attribute)
- `+medication_markup_percent` (Class attribute)

---

### Class: `DepartmentRoomConfig`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+count` (Class attribute)
- `+prefix` (Class attribute)

---

### Class: `DepartmentStaffConfig`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+doctors` (Class attribute)
- `+nurses` (Class attribute)
- `+pharmacists` (Class attribute)
- `+pharmacy_technicians` (Class attribute)
- `+pathologists` (Class attribute)
- `+lab_technicians` (Class attribute)
- `+radiologists` (Class attribute)
- `+rad_technicians` (Class attribute)
- `+billing_clerks` (Class attribute)

---

### Class: `DepartmentConfig`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+id` (Class attribute)
- `+name` (Class attribute)
- `+type` (Class attribute)
- `+floor` (Class attribute)
- `+rooms` (Class attribute)
- `+staff` (Class attribute)

---

### Class: `InventoryConfig`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+drug_name` (Class attribute)
- `+drug_class` (Class attribute)
- `+batch_quantity` (Class attribute)
- `+unit_cost` (Class attribute)
- `+expiry_months` (Class attribute)

---

### Class: `OperatingHoursConfig`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+start_hour` (Class attribute)
- `+end_hour` (Class attribute)
- `+slot_duration_minutes` (Class attribute)
- `+days` (Class attribute)

---

### Class: `MasterDataConfig`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+departments` (Class attribute)
- `+specializations` (Class attribute)
- `+initial_inventory` (Class attribute)
- `+operating_hours` (Class attribute)

---

## Module: `synapse_simulator/knowledge/pubmed/cache.py`

> Local File-Based Caching Layer for PubMed API Responses.

### Class: `PubMedCache`
- **Docstring:** Manages local JSON disk cache for PubMed PMIDs and search query results.

**Instance Attributes:**
- `-article_dir` (Instance attribute)
- `-cache_dir` (Instance attribute)
- `-query_dir` (Instance attribute)

**Declared Methods:**
- `+__init__(self, cache_dir: Optional[Path]) -> None`
- `+get_article(self, pmid: str) -> Optional[PubMedArticle]`
  *Description:* Retrieve cached article by PMID.
- `+save_article(self, article: PubMedArticle) -> None`
  *Description:* Save article to local JSON cache.
- `+get_query_pmids(self, query_id: str) -> Optional[List[str]]`
  *Description:* Retrieve cached list of PMIDs for a query ID.
- `+save_query_pmids(self, query_id: str, pmids: List[str]) -> None`
  *Description:* Save query PMIDs to cache.
- `+clear(self) -> None`
  *Description:* Clear cache files.

---

## Module: `synapse_simulator/knowledge/pubmed/client.py`

> NCBI E-utilities HTTP Client for PubMed API Integration.

### Class: `PubMedClient`
- **Docstring:** Client for fetching PubMed metadata and abstracts via NCBI E-utilities API.

**Class Attributes:**
- `+ESEARCH_URL` (Class attribute)
- `+EFETCH_URL` (Class attribute)

**Instance Attributes:**
- `-_last_request_time` (Instance attribute)
- `-cache` (Instance attribute)
- `-offline_mode` (Instance attribute)
- `-rate_limit_delay` (Instance attribute)
- `-timeout` (Instance attribute)

**Declared Methods:**
- `+__init__(self, cache: Optional[PubMedCache], timeout: int, rate_limit_delay: float, offline_mode: bool) -> None`
- `+_wait_rate_limit(self) -> None`
  *Description:* Enforce NCBI rate limit (max 3 req/sec).
- `+search_pmids(self, query: str, max_results: int) -> List[str]`
  *Description:* Search PubMed for a query string and return list of PMIDs.
- `+fetch_articles_by_pmids(self, pmids: List[str], query_topic: str) -> List[PubMedArticle]`
  *Description:* Fetch PubMedArticle objects for a list of PMIDs, using local cache first.
- `+execute_query(self, query_cfg: TargetQueryConfig, max_results: int) -> List[PubMedArticle]`
  *Description:* Execute search for a TargetQueryConfig, with caching and fallback.

---

## Module: `synapse_simulator/knowledge/pubmed/extractor.py`

> Biomedical Relationship Extractor.
Extracts structured candidate relationships (Disease -> Medicine, Medicine -> Adverse Effect, etc.)
from PubMed article titles, abstracts, and MeSH terms.

### Class: `KnowledgeExtractor`
- **Docstring:** Extracts candidate biomedical relations from PubMed article content.

**Class Attributes:**
- `+ADVERSE_EFFECT_KEYWORDS` (Class attribute)

**Declared Methods:**
- `+extract_relations_from_article(self, article: PubMedArticle) -> List[KnowledgeRelation]`
  *Description:* Extract candidate KnowledgeRelation objects from a single PubMed article.

---

## Module: `synapse_simulator/knowledge/pubmed/models.py`

> Pydantic Data Models for PubMed Biomedical Knowledge Integration.

### Class: `PubMedArticle`
- **Inherits From:** `BaseModel`
- **Docstring:** Structured record for a PubMed article.

**Class Attributes:**
- `+pmid` (Class attribute)
- `+title` (Class attribute)
- `+abstract` (Class attribute)
- `+publication_year` (Class attribute)
- `+journal` (Class attribute)
- `+authors` (Class attribute)
- `+mesh_terms` (Class attribute)
- `+keywords` (Class attribute)
- `+doi` (Class attribute)
- `+retrieved_at` (Class attribute)
- `+query_topic` (Class attribute)

---

### Class: `BiomedicalEntity`
- **Inherits From:** `BaseModel`
- **Docstring:** Extracted biomedical concept entity (Disease, Drug, Class, Adverse Effect, etc.).

**Class Attributes:**
- `+entity_id` (Class attribute)
- `+name` (Class attribute)
- `+canonical_name` (Class attribute)
- `+entity_type` (Class attribute)
- `+synonyms` (Class attribute)
- `+mesh_id` (Class attribute)
- `+synapse_catalog_id` (Class attribute)

---

### Class: `KnowledgeRelation`
- **Inherits From:** `BaseModel`
- **Docstring:** Evidence-backed relationship between biomedical entities.

**Class Attributes:**
- `+relation_id` (Class attribute)
- `+subject_entity` (Class attribute)
- `+subject_type` (Class attribute)
- `+predicate` (Class attribute)
- `+object_entity` (Class attribute)
- `+object_type` (Class attribute)
- `+pmid` (Class attribute)
- `+evidence_title` (Class attribute)
- `+confidence` (Class attribute)
- `+extraction_method` (Class attribute)
- `+source_snippet` (Class attribute)
- `+is_validated` (Class attribute)
- `+validation_status` (Class attribute)

---

### Class: `TargetQueryConfig`
- **Inherits From:** `BaseModel`
- **Docstring:** Configuration for a specific PubMed search query.

**Class Attributes:**
- `+id` (Class attribute)
- `+topic` (Class attribute)
- `+disease_code` (Class attribute)
- `+disease_name` (Class attribute)
- `+search_term` (Class attribute)
- `+category` (Class attribute)

---

### Class: `PubMedIntegrationConfig`
- **Inherits From:** `BaseModel`
- **Docstring:** Global configuration for PubMed knowledge integration.

**Class Attributes:**
- `+enabled` (Class attribute)
- `+offline_mode` (Class attribute)
- `+cache_dir` (Class attribute)
- `+store_dir` (Class attribute)
- `+max_results_per_query` (Class attribute)
- `+publication_year_min` (Class attribute)
- `+publication_year_max` (Class attribute)
- `+rate_limit_delay_seconds` (Class attribute)
- `+target_queries` (Class attribute)

---

## Module: `synapse_simulator/knowledge/pubmed/normalizer.py`

> Medicine and Clinical Terminology Normalizer.
Maps extracted terms from PubMed literature to Synapse Authoritative Vocabularies.

### Class: `TerminologyNormalizer`
- **Docstring:** Normalizes medical terminology, generic drug names, and clinical conditions.

**Class Attributes:**
- `+DRUG_SYNONYMS` (Class attribute)
- `+DISEASE_SYNONYMS` (Class attribute)

**Declared Methods:**
- `+normalize_drug_name(cls, raw_term: str) -> Optional[str]` {class}
  *Description:* Normalize a drug name string to Synapse canonical generic drug name.
- `+normalize_disease_name(cls, raw_term: str) -> Optional[Tuple[str, str]]` {class}
  *Description:* Normalize a disease term string to (icd_code, canonical_name).

---

## Module: `synapse_simulator/knowledge/pubmed/parser.py`

> NCBI E-utilities Response Parser for PubMed XML/JSON Data.

### Class: `PubMedParser`
- **Docstring:** Parses NCBI PubMed E-utilities XML and JSON responses into PubMedArticle objects.

**Declared Methods:**
- `+parse_esearch_json(json_data: Dict[str, Any]) -> List[str]` {static}
  *Description:* Parse PMID list from esearch JSON response.
- `+parse_efetch_xml(xml_content: str, query_topic: str) -> List[PubMedArticle]` {static}
  *Description:* Parse XML string returned by PubMed efetch into PubMedArticle list.

---

## Module: `synapse_simulator/knowledge/pubmed/retriever.py`

> PubMed Knowledge Retriever and Pipeline Manager.
Coordinates API fetching, parsing, extraction, normalization, validation, and storage.
Exposes evidence-backed medicine lookup API to Synapse.

### Class: `PubMedKnowledgeManager`
- **Docstring:** High-level facade for PubMed integration, evidence lookup, and ingestion pipeline.

**Instance Attributes:**
- `-articles` (Instance attribute)
- `-cache` (Instance attribute)
- `-client` (Instance attribute)
- `-config` (Instance attribute)
- `-config_path` (Instance attribute)
- `-extractor` (Instance attribute)
- `-kb` (Instance attribute)
- `-relations` (Instance attribute)
- `-store` (Instance attribute)
- `-validator` (Instance attribute)

**Declared Methods:**
- `+__init__(self, knowledge_base: Optional[MedicalKnowledgeBase], config_path: Optional[Path], offline_mode: bool) -> None`
- `+_load_config(self) -> PubMedIntegrationConfig`
  *Description:* Load pubmed.yaml config file.
- `+run_ingestion_pipeline(self) -> Dict[str, Any]`
  *Description:* Execute full PubMed ingestion pipeline across configured target queries.
- `+_find_query_config(self, condition_name: str, disease_code: Optional[str]) -> Optional[TargetQueryConfig]`
  *Description:* Find matching TargetQueryConfig from config by code or disease name.
- `+get_evidence_for_condition(self, condition_name: str, disease_code: Optional[str], offline_mode: Optional[bool]) -> List[KnowledgeRelation]`
  *Description:* Get validated treatment evidence for a condition using Cache HIT / MISS semantics.

Cache HIT:
    Returns stored/cached validated relationships. PubMed API is NOT called.
    
Cache MISS:
    If offline_mode: Returns empty list / existing cached without API call.
    If online_mode: Calls PubMedClient API (search_pmids -> fetch_articles_by_pmids),
    parses XML, extracts, normalizes, validates, stores in cache & store, and returns.
- `+find_candidate_medicines(self, condition_name: str) -> List[Dict[str, Any]]`
  *Description:* Look up evidence-backed candidate medicines for a disease condition.
- `+get_evidence_for_treatment(self, condition_name: str, drug_name: str) -> Optional[KnowledgeRelation]`
  *Description:* Retrieve PubMed evidence record for a specific (condition, drug) pair.

---

## Module: `synapse_simulator/knowledge/pubmed/store.py`

> Local Knowledge Store for PubMed Articles, Biomedical Entities, and Provenance-Backed Relationships.
Persists structured records into JSONL and JSON format.
Graph-compatible node & edge representation.

### Class: `PubMedKnowledgeStore`
- **Docstring:** Manages persistent disk storage of retrieved PubMed evidence, entities, and relations.

**Instance Attributes:**
- `-articles_file` (Instance attribute)
- `-entities_file` (Instance attribute)
- `-manifest_file` (Instance attribute)
- `-relations_file` (Instance attribute)
- `-store_dir` (Instance attribute)

**Declared Methods:**
- `+__init__(self, store_dir: Optional[Path]) -> None`
- `+save_articles(self, articles: List[PubMedArticle]) -> None`
  *Description:* Write articles to articles.jsonl.
- `+save_relationships(self, relations: List[KnowledgeRelation]) -> None`
  *Description:* Write relationships to relationships.jsonl.
- `+save_manifest(self, metrics: Dict[str, Any]) -> None`
  *Description:* Save storage manifest with counts and execution metadata.
- `+load_articles(self) -> List[PubMedArticle]`
  *Description:* Load all articles from articles.jsonl.
- `+load_relationships(self) -> List[KnowledgeRelation]`
  *Description:* Load all relationships from relationships.jsonl.
- `+get_relationships_for_condition(self, condition_name: str) -> List[KnowledgeRelation]`
  *Description:* Load stored relationships matching condition name.

---

## Module: `synapse_simulator/knowledge/pubmed/validator.py`

> Biomedical Knowledge Validator.
Validates PubMed candidate relations against Synapse Authoritative Medicine Vocabulary & Safety Rules.

### Class: `KnowledgeValidator`
- **Docstring:** Validates extracted PubMed candidate relationships against Synapse Master Data & Safety Constraints.

**Instance Attributes:**
- `-kb` (Instance attribute)

**Declared Methods:**
- `+__init__(self, knowledge_base: MedicalKnowledgeBase) -> None`
- `+validate_relation(self, relation: KnowledgeRelation) -> KnowledgeRelation`
  *Description:* Validate a single candidate relation against Synapse authoritative catalog.
- `+validate_all(self, relations: List[KnowledgeRelation]) -> List[KnowledgeRelation]`
  *Description:* Validate a batch of candidate relations.

---

## Module: `synapse_simulator/rules/evaluator.py`

> Rule Evaluator: Safe boolean expression evaluation against InputContext.

### Class: `RuleEvaluator`
- **Docstring:** Evaluates rule preconditions and boolean conditions against an InputContext.

**Declared Methods:**
- `+evaluate_preconditions(rule: SynapseRule, context: InputContext) -> bool` {static}
  *Description:* Check if action type matches and all required context keys exist.
- `+evaluate_conditions(rule: SynapseRule, context: InputContext) -> bool` {static}
  *Description:* Evaluate all_of, any_of, and none_of expressions.
- `+_eval_expr(expr: str, eval_context: Dict[str, Any]) -> bool` {static}
  *Description:* Safely evaluate a single pythonic expression using SimpleEval.
- `+_fallback_eval(expr: str, eval_context: Dict[str, Any]) -> bool` {static}
  *Description:* Simple fallback string comparison logic.
- `+_context_to_dict(context: InputContext) -> Dict[str, Any]` {static}
  *Description:* Convert InputContext snapshot into dict structure.
- `+_has_key_path(d: Dict[str, Any], path: str) -> bool` {static}
  *Description:* Check if nested path exists in dictionary.
- `+_get_value_by_path(d: Dict[str, Any], path: str) -> Any` {static}
  *Description:* Retrieve nested dictionary value using dot notation (e.g. 'patient.allergies').

---

## Module: `synapse_simulator/rules/models.py`

> Pydantic schema definition for Synapse Rules.

### Class: `PrecedenceLevel`
- **Inherits From:** `IntEnum`

**Class Attributes:**
- `+LEVEL_1_SYSTEM_INTEGRITY` (Class attribute)
- `+LEVEL_2_CLINICAL_SAFETY` (Class attribute)
- `+LEVEL_3_DEPARTMENT_WORKFLOW` (Class attribute)
- `+LEVEL_4_SCENARIO_SPEC` (Class attribute)
- `+LEVEL_5_SIMULATION_HEURISTIC` (Class attribute)

---

### Class: `RuleSourceType`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+INTERNAL_DESIGN` (Class attribute)
- `+EXTERNAL_DOMAIN` (Class attribute)
- `+SIMULATION_HEURISTIC` (Class attribute)

---

### Class: `RuleCategory`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+CLINICAL_SAFETY` (Class attribute)
- `+WORKFLOW_SEQUENCE` (Class attribute)
- `+STATE_TRANSITION` (Class attribute)
- `+CROSS_DEPARTMENT` (Class attribute)
- `+DATA_INTEGRITY` (Class attribute)
- `+REFERENTIAL_INTEGRITY` (Class attribute)
- `+TEMPORAL_CONSTRAINT` (Class attribute)
- `+RESOURCE_AVAILABILITY` (Class attribute)
- `+SIMULATION_PROBABILITY` (Class attribute)

---

### Class: `RulePreconditions`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+action_type` (Class attribute)
- `+required_context_keys` (Class attribute)

---

### Class: `RuleConditions`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+all_of` (Class attribute)
- `+any_of` (Class attribute)
- `+none_of` (Class attribute)

---

### Class: `StateTransitionRuleEffect`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+target_entity` (Class attribute)
- `+target_field` (Class attribute)
- `+new_value` (Class attribute)
- `+additional_updates` (Class attribute)

---

### Class: `CrossDepartmentRuleEffect`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+target_department` (Class attribute)
- `+effect_type` (Class attribute)
- `+payload` (Class attribute)

---

### Class: `TemporalConstraints`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+min_delay_seconds` (Class attribute)
- `+max_delay_seconds` (Class attribute)
- `+must_occur_after_action` (Class attribute)

---

### Class: `SynapseRule`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+rule_id` (Class attribute)
- `+name` (Class attribute)
- `+category` (Class attribute)
- `+description` (Class attribute)
- `+source_type` (Class attribute)
- `+source_reference` (Class attribute)
- `+priority` (Class attribute)
- `+precedence_level` (Class attribute)
- `+version` (Class attribute)
- `+scenarios` (Class attribute)
- `+departments` (Class attribute)
- `+entities_affected` (Class attribute)
- `+preconditions` (Class attribute)
- `+conditions` (Class attribute)
- `+allowed_actions` (Class attribute)
- `+blocked_actions` (Class attribute)
- `+state_transitions` (Class attribute)
- `+cross_department_effects` (Class attribute)
- `+events_generated` (Class attribute)
- `+documents_triggered` (Class attribute)
- `+temporal_constraints` (Class attribute)

---

## Module: `synapse_simulator/rules/repository.py`

> Rule Repository: Loads YAML rule files and indexes SynapseRule objects in memory.

### Class: `RuleRepository`
- **Docstring:** Loads, validates, and indexes rules from YAML files.

**Instance Attributes:**
- `-rules_directory` (Instance attribute)

**Declared Methods:**
- `+__init__(self, rules_directory: Optional[Path]) -> None`
- `+load_rules(self) -> int`
  *Description:* Scan directory recursively and load all YAML rule files.
- `+register_rule(self, rule: SynapseRule) -> None`
  *Description:* Register a single rule in memory.
- `+get_rule_by_id(self, rule_id: str) -> Optional[SynapseRule]`
- `+find_applicable_rules(self, action_type: str, department_id: str, scenario_id: str) -> List[SynapseRule]`
  *Description:* Find candidate rules matching action_type, department, and scenario.
- `+_load_yaml_file(self, file_path: Path) -> None`
- `+_build_indexes(self) -> None`
- `+_index_single_rule(self, rule: SynapseRule) -> None`

---

## Module: `synapse_simulator/rules/rule_engine.py`

> Pure, side-effect-free Rule Engine implementing the 5-Level Precedence Hierarchy.

### Class: `RuleEngine`
- **Docstring:** Pure, side-effect-free Rule Engine.

**Instance Attributes:**
- `-repository` (Instance attribute)

**Declared Methods:**
- `+__init__(self, repository: RuleRepository) -> None`
- `+evaluate(self, context: InputContext) -> DecisionResult`
  *Description:* Evaluate an InputContext against candidate rules using 5-Level Precedence Hierarchy.

---

## Module: `synapse_simulator/scenarios/base_scenario.py`

> Base Scenario definition class.

### Class: `BaseScenario`
- **Inherits From:** `ABC`
- **Docstring:** Abstract base class for scenario setup and initial state generation.

**Class Attributes:**
- `+scenario_id` (Class attribute)
- `+name` (Class attribute)
- `+description` (Class attribute)

**Instance Attributes:**
- `-appointment_id` (Instance attribute)
- `-batch_id` (Instance attribute)
- `-correlation_id` (Instance attribute)
- `-patient_id` (Instance attribute)
- `-patient_journey_id` (Instance attribute)
- `-prescription_id` (Instance attribute)
- `-scenario_instance_id` (Instance attribute)

**Declared Methods:**
- `+__init__(self, instance_index: int) -> None`
- `+setup_initial_state(self, state_manager: StateManager) -> None` {abstract}
  *Description:* Initialize required entity state snapshots in StateManager.
- `+generate_initial_events(self, start_time: datetime) -> SimulationEvent` {abstract}
  *Description:* Create entry-point simulation event to trigger scenario execution.
- `+create_patient_profile(self, patient_gen: Any) -> Any`
  *Description:* Create patient profile using generator (polymorphically overridden by scenario subclasses).
- `+should_force_conflict(self) -> bool`
  *Description:* Whether this scenario intentionally forces a clinical conflict (LSP hook).

---

## Module: `synapse_simulator/scenarios/interfaces.py`

> Scenario Protocols: Defines contracts for polymorphic scenario execution and profile hooks (LSP).

### Class: `IScenarioProfileHook`
- **Inherits From:** `Protocol`
- **Docstring:** Protocol for scenario-level profile customization and initial state setup.

**Class Attributes:**
- `+scenario_id` (Class attribute)

**Declared Methods:**
- `+create_patient_profile(self, patient_gen: Any) -> Any`
- `+should_force_conflict(self) -> bool`
- `+setup_initial_state(self, state_manager: Any) -> None`
- `+generate_initial_events(self, start_time: datetime) -> SimulationEvent`

---

## Module: `synapse_simulator/scenarios/scen_v1_01_opd.py`

> SCEN-V1-01 Routine Outpatient Journey Generator.

### Class: `OutpatientRoutineScenario`
- **Inherits From:** `BaseScenario`

**Class Attributes:**
- `+scenario_id` (Class attribute)
- `+name` (Class attribute)
- `+description` (Class attribute)

**Declared Methods:**
- `+setup_initial_state(self, state_manager: StateManager) -> None`
- `+generate_initial_events(self, start_time: datetime) -> SimulationEvent`

---

## Module: `synapse_simulator/scenarios/scen_v1_02_diagnostic.py`

> SCEN-V1-02 Outpatient Diagnostic Investigation Generator.

### Class: `DiagnosticInvestigationScenario`
- **Inherits From:** `BaseScenario`

**Class Attributes:**
- `+scenario_id` (Class attribute)
- `+name` (Class attribute)
- `+description` (Class attribute)

**Declared Methods:**
- `+setup_initial_state(self, state_manager: StateManager) -> None`
- `+generate_initial_events(self, start_time: datetime) -> SimulationEvent`

---

## Module: `synapse_simulator/scenarios/scen_v1_03_allergy.py`

> SCEN-V1-03 Clinical Safety Hold & Medication Replacement Generator.

### Class: `DrugAllergySafetyHoldScenario`
- **Inherits From:** `BaseScenario`

**Class Attributes:**
- `+scenario_id` (Class attribute)
- `+name` (Class attribute)
- `+description` (Class attribute)

**Declared Methods:**
- `+setup_initial_state(self, state_manager: StateManager) -> None`
- `+generate_initial_events(self, start_time: datetime) -> SimulationEvent`
- `+create_patient_profile(self, patient_gen) -> None`
  *Description:* Force Penicillin allergy for this scenario instance polymorphically.
- `+should_force_conflict(self) -> bool`
  *Description:* Force allergy conflict for safety hold testing.

---

## Module: `synapse_simulator/scenarios/scen_v1_04_inventory.py`

> SCEN-V1-04 Inventory Stock Depletion & Shortage Generator.

### Class: `InventoryDepletionScenario`
- **Inherits From:** `BaseScenario`

**Class Attributes:**
- `+scenario_id` (Class attribute)
- `+name` (Class attribute)
- `+description` (Class attribute)

**Declared Methods:**
- `+setup_initial_state(self, state_manager: StateManager) -> None`
- `+generate_initial_events(self, start_time: datetime) -> SimulationEvent`

---

## Module: `synapse_simulator/state/document_models.py`

> Pydantic data models for Stage 9 Document Metadata and Statuses.

### Class: `DocumentType`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+PRESCRIPTION` (Class attribute)
- `+INVOICE` (Class attribute)
- `+LAB_REPORT` (Class attribute)
- `+RAD_REPORT` (Class attribute)
- `+DISCHARGE_SUMMARY` (Class attribute)

---

### Class: `DocumentStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+FINAL` (Class attribute)
- `+REVISED` (Class attribute)
- `+CANCELLED` (Class attribute)

---

### Class: `DocumentMetadata`
- **Inherits From:** `BaseModel`
- **Docstring:** Authority metadata for a single generated hospital document.

**Class Attributes:**
- `+document_id` (Class attribute)
- `+document_type` (Class attribute)
- `+patient_id` (Class attribute)
- `+patient_journey_id` (Class attribute)
- `+scenario_id` (Class attribute)
- `+source_entity_table` (Class attribute)
- `+source_entity_id` (Class attribute)
- `+source_action_id` (Class attribute)
- `+source_event_id` (Class attribute)
- `+created_at` (Class attribute)
- `+document_version` (Class attribute)
- `+document_status` (Class attribute)
- `+file_path` (Class attribute)
- `+checksum` (Class attribute)
- `+metadata_payload` (Class attribute)

---

## Module: `synapse_simulator/state/interfaces.py`

> State Protocols: Segregated interfaces for reading, writing, and context building (ISP & DIP).

### Class: `IStateReader`
- **Inherits From:** `Protocol`
- **Docstring:** Read-only entity state access protocol.

**Declared Methods:**
- `+get_entity_state(self, table_name: str, entity_id: str) -> Dict[str, Any]`

---

### Class: `IStateWriter`
- **Inherits From:** `Protocol`
- **Docstring:** State mutation and initialization protocol.

**Declared Methods:**
- `+set_entity_state(self, table_name: str, entity_id: str, state: Dict[str, Any]) -> None`

---

### Class: `IContextBuilder`
- **Inherits From:** `Protocol`
- **Docstring:** Snapshot assembly for RuleEngine evaluation protocol.

**Declared Methods:**
- `+build_input_context(self, proposed_action: ActionRequest, simulated_timestamp: datetime, scenario_id: str, department_id: str, patient_id: Optional[str]) -> InputContext`

---

### Class: `IStateDecisionApplier`
- **Inherits From:** `Protocol`
- **Docstring:** Transition application protocol for approved decisions.

**Declared Methods:**
- `+apply_decision(self, decision: DecisionResult) -> bool`

---

## Module: `synapse_simulator/state/models.py`

> State data models, context payloads, status Enums, and proposal schemas.

### Class: `PatientStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+REGISTERED` (Class attribute)
- `+ACTIVE` (Class attribute)
- `+ARCHIVED` (Class attribute)

---

### Class: `AppointmentStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+SCHEDULED` (Class attribute)
- `+CHECKED_IN` (Class attribute)
- `+IN_CONSULT` (Class attribute)
- `+COMPLETED` (Class attribute)
- `+CANCELLED` (Class attribute)
- `+NO_SHOW` (Class attribute)

---

### Class: `EncounterStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ACTIVE` (Class attribute)
- `+CLOSED` (Class attribute)

---

### Class: `ConsultationStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+IN_PROGRESS` (Class attribute)
- `+PENDING_RESULTS` (Class attribute)
- `+COMPLETED` (Class attribute)

---

### Class: `LabOrderStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ORDERED` (Class attribute)
- `+SAMPLE_COLLECTED` (Class attribute)
- `+COMPLETED` (Class attribute)
- `+REJECTED` (Class attribute)

---

### Class: `RadOrderStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ORDERED` (Class attribute)
- `+IMAGE_ACQUIRED` (Class attribute)
- `+REPORTED` (Class attribute)

---

### Class: `PrescriptionStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ISSUED` (Class attribute)
- `+VERIFICATION_PASSED` (Class attribute)
- `+DISPENSED` (Class attribute)
- `+BLOCKED_SAFETY_HOLD` (Class attribute)
- `+CANCELLED_REPLACED` (Class attribute)
- `+PARTIALLY_DISPENSED` (Class attribute)
- `+COMPLETED` (Class attribute)

---

### Class: `InventoryBatchStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ACTIVE` (Class attribute)
- `+LOW_STOCK` (Class attribute)
- `+DEPLETED` (Class attribute)
- `+EXPIRED` (Class attribute)

---

### Class: `InvoiceStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+DRAFT` (Class attribute)
- `+UNPAID` (Class attribute)
- `+PAID` (Class attribute)
- `+PARTIALLY_PAID` (Class attribute)
- `+CANCELLED` (Class attribute)

---

### Class: `ActionRequest`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+action_id` (Class attribute)
- `+action_type` (Class attribute)
- `+target_department` (Class attribute)
- `+target_entity_table` (Class attribute)
- `+target_entity_id` (Class attribute)
- `+scenario_instance_id` (Class attribute)
- `+patient_journey_id` (Class attribute)
- `+correlation_id` (Class attribute)
- `+causation_id` (Class attribute)
- `+requested_timestamp` (Class attribute)
- `+payload` (Class attribute)

---

### Class: `StateTransitionProposal`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+target_entity_table` (Class attribute)
- `+target_entity_id` (Class attribute)
- `+field_name` (Class attribute)
- `+current_value` (Class attribute)
- `+new_value` (Class attribute)
- `+additional_updates` (Class attribute)

---

### Class: `CommandProposal`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+target_department` (Class attribute)
- `+command_type` (Class attribute)
- `+payload` (Class attribute)

---

### Class: `OutboxEventProposal`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+event_type` (Class attribute)
- `+source_domain` (Class attribute)
- `+entity_reference` (Class attribute)
- `+scenario_instance_id` (Class attribute)
- `+patient_journey_id` (Class attribute)
- `+correlation_id` (Class attribute)
- `+causation_id` (Class attribute)
- `+payload` (Class attribute)

---

### Class: `DocumentTriggerProposal`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+document_type` (Class attribute)
- `+encounter_id` (Class attribute)
- `+patient_id` (Class attribute)
- `+payload` (Class attribute)

---

### Class: `InputContext`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+simulated_timestamp` (Class attribute)
- `+scenario_id` (Class attribute)
- `+scenario_instance_id` (Class attribute)
- `+patient_journey_id` (Class attribute)
- `+correlation_id` (Class attribute)
- `+department_id` (Class attribute)
- `+proposed_action` (Class attribute)
- `+patient_state` (Class attribute)
- `+entity_state` (Class attribute)
- `+resource_state` (Class attribute)
- `+extra_context` (Class attribute)

---

### Class: `DecisionStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ALLOWED` (Class attribute)
- `+BLOCKED` (Class attribute)
- `+REDIRECTED` (Class attribute)

---

### Class: `DecisionResult`
- **Inherits From:** `BaseModel`

**Class Attributes:**
- `+status` (Class attribute)
- `+winning_rule_id` (Class attribute)
- `+winning_rule_priority` (Class attribute)
- `+reason` (Class attribute)
- `+permitted_actions` (Class attribute)
- `+blocked_actions` (Class attribute)
- `+state_transitions` (Class attribute)
- `+cross_department_effects` (Class attribute)
- `+events_to_emit` (Class attribute)
- `+documents_to_trigger` (Class attribute)

---

### Class: `DomainEvent`
- **Inherits From:** `BaseModel`
- **Docstring:** Immutable domain event representing an actual state-changing fact (or explicit failure).

**Class Attributes:**
- `+event_id` (Class attribute)
- `+event_type` (Class attribute)
- `+event_version` (Class attribute)
- `+timestamp` (Class attribute)
- `+producer_domain` (Class attribute)
- `+entity_table` (Class attribute)
- `+entity_id` (Class attribute)
- `+scenario_instance_id` (Class attribute)
- `+patient_journey_id` (Class attribute)
- `+correlation_id` (Class attribute)
- `+causation_id` (Class attribute)
- `+causation_depth` (Class attribute)
- `+sequence_number` (Class attribute)
- `+status` (Class attribute)
- `+payload` (Class attribute)
- `+metadata` (Class attribute)

---

## Module: `synapse_simulator/state/state_manager.py`

> State Manager: Maintains in-memory state snapshots and applies approved StateTransitionProposal objects.

### Class: `StateManager`
- **Docstring:** Authoritative State Manager managing entity state snapshots and transitions.

**Declared Methods:**
- `+__init__(self, transition_validator: Optional[ITransitionValidator]) -> None`
- `+get_entity_state(self, table_name: str, entity_id: str) -> Dict[str, Any]`
  *Description:* Retrieve entity state dictionary.
- `+set_entity_state(self, table_name: str, entity_id: str, state: Dict[str, Any]) -> None`
  *Description:* Set/initialize entity state dictionary.
- `+build_input_context(self, proposed_action: ActionRequest, simulated_timestamp: datetime, scenario_id: str, department_id: str, patient_id: Optional[str]) -> InputContext`
  *Description:* Assemble an InputContext snapshot for Rule Engine evaluation.
- `+apply_decision(self, decision: DecisionResult) -> bool`
  *Description:* Apply approved StateTransitionProposal objects to update entity state store.

---

## Module: `synapse_simulator/transitions/interfaces.py`

> Transition Protocols: Defines transition validation contract (DIP).

### Class: `ITransitionValidator`
- **Inherits From:** `Protocol`
- **Docstring:** Protocol for state machine transition validation.

**Declared Methods:**
- `+validate_transition(self, entity_table: str, current_state: str, next_state: str) -> Tuple[bool, Optional[str]]`
- `+is_terminal_state(self, entity_table: str, state: str) -> bool`

---

## Module: `synapse_simulator/transitions/state_machine.py`

> State Machine definitions for the 9 Core V1 entities.

### Class: `BaseStateMachine`
- **Docstring:** Base State Machine providing structural transition validation.

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+valid_transitions` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)

**Declared Methods:**
- `+is_valid_transition(cls, current_state: str, next_state: str) -> bool` {class}
- `+is_terminal(cls, state: str) -> bool` {class}

---

### Class: `PatientStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `AppointmentStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `EncounterStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `ConsultationStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `LabOrderStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `RadOrderStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `PrescriptionStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `InventoryBatchStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

### Class: `InvoiceStateMachine`
- **Inherits From:** `BaseStateMachine`

**Class Attributes:**
- `+entity_name` (Class attribute)
- `+initial_state` (Class attribute)
- `+terminal_states` (Class attribute)
- `+valid_transitions` (Class attribute)

---

## Module: `synapse_simulator/transitions/transition_manager.py`

> Transition Manager: Validates entity structural state transitions.

### Class: `TransitionManager`
- **Docstring:** Validates whether proposed status transitions comply with entity state machines.

**Declared Methods:**
- `+validate_transition(entity_table: str, current_state: str, next_state: str) -> Tuple[bool, Optional[str]]` {static}
- `+is_terminal_state(entity_table: str, state: str) -> bool` {static}

---

## Module: `synapse_simulator/validation/consistency_checker.py`

> Consistency Checker for Synapse Phase 2.
Performs cross-layer validation across database records, event logs, lineage map, and document outputs.
Outputs a machine-readable validation report (integrity_report.json).

### Class: `ConsistencyChecker`
- **Docstring:** Verifies that Database, Event Log, Lineage Map, and Documents are consistent across layers.

**Instance Attributes:**
- `-auditor` (Instance attribute)
- `-committed_events` (Instance attribute)
- `-doc_validator` (Instance attribute)
- `-generated_docs` (Instance attribute)
- `-lineage_map_path` (Instance attribute)
- `-output_dir` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, state_manager: StateManager, committed_events: List[DomainEvent], generated_docs: Dict[str, DocumentMetadata], lineage_map_path: Path, output_dir: Path) -> None`
- `+check_all(self) -> Path`
  *Description:* Execute full cross-layer consistency checks and output integrity_report.json.
- `+_run_cross_layer_checks(self, results: Dict[str, Any]) -> None`
  *Description:* Run structural consistency checks across Database, Events, and Lineage Map.

---

## Module: `synapse_simulator/validation/dataset_auditor.py`

> Dataset Integrity Auditor for SYNAPSE Phase 2 Synthetic Data.
Performs comprehensive multi-table referential integrity, required field NULL audits,
temporal duration validation, duplicate key detection, PubMed provenance verification,
and scenario distribution analysis directly against exported CSV files.

### Class: `DatasetAuditor`
- **Docstring:** Audits exported CSV datasets for referential, temporal, schema, and clinical integrity.

**Class Attributes:**
- `+REQUIRED_SCHEMAS` (Class attribute)

**Instance Attributes:**
- `-dataset_dir` (Instance attribute)

**Declared Methods:**
- `+__init__(self, dataset_dir: Path) -> None`
- `+load_datasets(self) -> None`
  *Description:* Load all CSV files from target directory.
- `+run_full_audit(self) -> Dict[str, Any]`
  *Description:* Execute full suite of integrity audits.

---

## Module: `synapse_simulator/validation/document_validator.py`

> Document Validator for Synapse Phase 2.
Compares generated document metadata and content against authoritative structured database state.

### Class: `DocumentValidationError`
- **Inherits From:** `Exception`
- **Docstring:** Raised when there is an integrity mismatch between a document and the database state.

---

### Class: `DocumentValidator`
- **Docstring:** Validates rendered document data against database snapshots in StateManager.

**Instance Attributes:**
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, state_manager: StateManager) -> None`
- `+validate_document(self, doc: DocumentMetadata) -> Tuple[bool, List[str]]`
  *Description:* Validate document fields against the StateManager database records.
Returns a tuple of (is_valid, list_of_errors).
- `+_validate_prescription(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None`
- `+_validate_invoice(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None`
- `+_validate_lab_report(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None`
- `+_validate_rad_report(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None`
- `+_validate_discharge_summary(self, doc: DocumentMetadata, db_record: Dict[str, Any], errors: List[str]) -> None`

---

## Module: `synapse_simulator/validation/integrity_auditor.py`

> Integrity Auditor for Synapse Phase 2.
Performs deep structural validation of patient contexts, temporal sequencing, state machines, and rules.

### Class: `IntegrityAuditor`
- **Docstring:** Performs global database integrity, temporal sequencing, and rule constraint verification.

**Instance Attributes:**
- `-committed_events` (Instance attribute)
- `-state_manager` (Instance attribute)

**Declared Methods:**
- `+__init__(self, state_manager: StateManager, committed_events: List[DomainEvent]) -> None`
- `+audit_all(self) -> Dict[str, Any]`
  *Description:* Perform all audits and compile report.
- `+audit_referential_integrity(self) -> Dict[str, Any]`
  *Description:* Verify foreign key relationships across all entity tables.
- `+audit_patient_and_encounter_consistency(self) -> Dict[str, Any]`
  *Description:* Verify cross-record consistency between patient_id and encounter_id.
- `+audit_encounter_duration(self) -> Dict[str, Any]`
  *Description:* Verify that encounters have valid non-negative and non-zero duration.
- `+audit_provenance_integrity(self) -> Dict[str, Any]`
  *Description:* Verify treatment knowledge provenance (PubMed vs internal_yaml).
- `+audit_temporal_encounter_boundaries(self) -> Dict[str, Any]`
  *Description:* Verify in-encounter events occur within encounter boundaries.
- `+audit_causal_ordering(self) -> Dict[str, Any]`
  *Description:* Ensure causally dependent events occur in valid order.
- `+audit_temporal_sequencing(self) -> Dict[str, Any]`
  *Description:* Verify that event timestamps conform to causal ordering (e.g. consult before dispense).
- `+audit_state_transitions(self) -> Dict[str, Any]`
  *Description:* Verify that entity state histories correspond to valid state machine paths.
- `+audit_resource_constraints(self) -> Dict[str, Any]`
  *Description:* Ensure no inventory batch quantities became negative.
- `+audit_rule_compliance(self) -> Dict[str, Any]`
  *Description:* Verify that rules were executed correctly (e.g. blocked actions did not result in success states).

---

## Module: `synapse_simulator/workflows/coordinator.py`

> Workflow Coordinator: Orchestrates PatientJourney workflow execution step-by-step.

### Class: `WorkflowCoordinator`
- **Docstring:** Coordinates patient journey step progression and cross-department workflows.

**Instance Attributes:**
- `-scheduler` (Instance attribute)

**Declared Methods:**
- `+__init__(self, scheduler: FutureActionScheduler) -> None`
- `+register_workflow(self, definition: WorkflowDefinition) -> None`
  *Description:* Register a scenario workflow definition.
- `+start_journey(self, journey: PatientJourney, start_time: datetime) -> Optional[ActionRequest]`
  *Description:* Initialize and start a patient journey, scheduling its initial workflow step.
- `+advance_journey(self, journey_id: str, current_step_id: str, decision: DecisionResult, event: DomainEvent, current_time: datetime) -> Optional[ActionRequest]`
  *Description:* Advance a patient journey to its next workflow step based on decision and domain event.

---

## Module: `synapse_simulator/workflows/model.py`

> Workflow and Patient Journey Data Models for Stage 7.

### Class: `JourneyStatus`
- **Inherits From:** `str, Enum`

**Class Attributes:**
- `+ACTIVE` (Class attribute)
- `+COMPLETED` (Class attribute)
- `+BLOCKED` (Class attribute)
- `+TERMINATED` (Class attribute)

---

### Class: `WorkflowStep`
- **Inherits From:** `BaseModel`
- **Docstring:** Definition of a single step within a scenario workflow.

**Class Attributes:**
- `+step_id` (Class attribute)
- `+name` (Class attribute)
- `+action_type` (Class attribute)
- `+target_department` (Class attribute)
- `+target_entity_table` (Class attribute)
- `+delay_seconds` (Class attribute)
- `+next_step_id` (Class attribute)
- `+failure_step_id` (Class attribute)
- `+conditional_branches` (Class attribute)
- `+payload_template` (Class attribute)

---

### Class: `WorkflowDefinition`
- **Inherits From:** `BaseModel`
- **Docstring:** Complete executable workflow sequence/graph for a scenario.

**Class Attributes:**
- `+workflow_id` (Class attribute)
- `+scenario_id` (Class attribute)
- `+name` (Class attribute)
- `+description` (Class attribute)
- `+initial_step_id` (Class attribute)
- `+steps` (Class attribute)

**Declared Methods:**
- `+get_step(self, step_id: str) -> Optional[WorkflowStep]`

---

### Class: `PatientJourney`
- **Inherits From:** `BaseModel`
- **Docstring:** Active instance tracking one patient's journey through a scenario workflow.

**Class Attributes:**
- `+journey_id` (Class attribute)
- `+patient_id` (Class attribute)
- `+scenario_id` (Class attribute)
- `+scenario_instance_id` (Class attribute)
- `+correlation_id` (Class attribute)
- `+current_step_id` (Class attribute)
- `+status` (Class attribute)
- `+completed_steps` (Class attribute)
- `+entity_references` (Class attribute)
- `+start_time` (Class attribute)
- `+end_time` (Class attribute)
- `+outcome` (Class attribute)
- `+trace_history` (Class attribute)

---
