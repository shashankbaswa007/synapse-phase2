"""
Simulation Bootstrap Factory: Separates component instantiation, dependency resolution,
and handler wiring from the HospitalSimulator facade (SRP & DIP compliance).
"""

import random
from typing import Optional, Any, Dict
from datetime import datetime

from synapse_simulator.core.ids import reset as reset_ids
from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.scheduler import FutureActionScheduler
from synapse_simulator.core.event_queue import EventQueue
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.engine.orchestrator import ExecutionPipeline
from synapse_simulator.core.simulation_engine import SimulationEngine
from synapse_simulator.workflows.coordinator import WorkflowCoordinator
from synapse_simulator.workflows.templates import get_all_scenario_workflows

from synapse_simulator.departments.clinical import ClinicalDepartmentHandler
from synapse_simulator.departments.pharmacy import PharmacyDepartmentHandler
from synapse_simulator.departments.laboratory import LaboratoryDepartmentHandler
from synapse_simulator.departments.radiology import RadiologyDepartmentHandler
from synapse_simulator.departments.finance import FinanceDepartmentHandler

from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.datagen.master_data import MasterDataGenerator
from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
from synapse_simulator.datagen.clinical_generator import ClinicalEntityGenerator
from synapse_simulator.datagen.diagnostic_generator import DiagnosticGenerator
from synapse_simulator.datagen.billing_generator import BillingGenerator


class SimulationBootstrapFactory:
    """Assembles all simulation engines, data generators, and department handlers."""

    @staticmethod
    def bootstrap(
        sim: Any,
        random_seed: int = 42,
        start_time: Optional[datetime] = None,
        enable_pubmed: bool = True,
        pubmed_store_dir: Optional[Any] = None,
        offline_mode: bool = True,
    ) -> None:
        """Instantiate and wire simulation components into the simulator facade."""
        random.seed(random_seed)
        # Deterministic identifiers + tie-break sequences: same seed -> same IDs
        reset_ids(random_seed)
        sim.clock = SimulationClock(start_time or datetime(2026, 1, 1, 8, 0, 0))
        sim.scheduler = FutureActionScheduler()
        sim.event_queue = EventQueue()
        sim.dispatcher = EventDispatcher()
        sim.state_manager = StateManager()

        # Load rules and initialize engines
        sim.repository = RuleRepository()
        sim.repository.load_rules()
        sim.rule_engine = RuleEngine(sim.repository)
        sim.pipeline = ExecutionPipeline(sim.state_manager, sim.rule_engine)

        sim.engine = SimulationEngine(
            clock=sim.clock,
            scheduler=sim.scheduler,
            event_queue=sim.event_queue,
            dispatcher=sim.dispatcher,
            state_manager=sim.state_manager,
            rule_engine=sim.rule_engine,
            execution_pipeline=sim.pipeline,
        )

        # Initialize knowledge base and data generators
        sim.kb = MedicalKnowledgeBase()
        sim.kb.load(enable_pubmed=enable_pubmed, pubmed_store_dir=pubmed_store_dir, offline_mode=offline_mode)
        sim.rng = random.Random(random_seed)

        sim.master_data_gen = MasterDataGenerator(sim.kb, sim.rng)
        sim.master_data_snapshot = sim.master_data_gen.generate()
        sim.master_data_gen.seed_state_manager(sim.state_manager, sim.master_data_snapshot)

        sim.patient_gen = PatientProfileGenerator(sim.kb, sim.rng)
        sim.clinical_gen = ClinicalEntityGenerator(sim.kb, sim.master_data_snapshot, sim.rng)
        sim.diagnostic_gen = DiagnosticGenerator(sim.rng, knowledge_base=sim.kb)
        sim.billing_gen = BillingGenerator(sim.rng)

        sim.patient_contexts = {}

        # Workflow Coordinator
        sim.coordinator = WorkflowCoordinator(sim.scheduler)
        for wdef in get_all_scenario_workflows().values():
            sim.coordinator.register_workflow(wdef)

        # Register department handlers
        SimulationBootstrapFactory.wire_department_handlers(sim)

    @staticmethod
    def wire_department_handlers(sim: Any) -> None:
        """Instantiate departmental handlers and wire event listeners to dispatcher."""
        clinical = ClinicalDepartmentHandler(sim.clinical_gen, sim.patient_contexts, sim.state_manager)
        pharmacy = PharmacyDepartmentHandler(sim.clinical_gen, sim.patient_contexts, sim.state_manager)
        lab = LaboratoryDepartmentHandler(sim.diagnostic_gen, sim.patient_contexts, sim.state_manager)
        rad = RadiologyDepartmentHandler(sim.diagnostic_gen, sim.patient_contexts, sim.state_manager)
        fin = FinanceDepartmentHandler(sim.billing_gen, sim.patient_contexts, sim.state_manager)

        sim.dispatcher.register_handler("PatientArrived", clinical.handle_event)
        sim.dispatcher.register_handler("CREATE_CLINICAL_ALERT", clinical.handle_event)

        # Intra-step department handlers
        sim.dispatcher.register_handler("LabOrderCreated", lab.handle_event)
        sim.dispatcher.register_handler("LabSampleCollected", lab.handle_event)
        sim.dispatcher.register_handler("RadOrderCreated", rad.handle_event)
        sim.dispatcher.register_handler("RadiologyImageAcquired", rad.handle_event)

        sim.dispatcher.register_handler("ADD_INVOICE_LINE_ITEM", fin.handle_event)
        sim.dispatcher.register_handler("InvoiceGenerated", fin.handle_event)
