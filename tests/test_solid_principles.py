"""
Tests for SYNAPSE Phase 2 SOLID Compliance:
Verifies Protocol compliance, Bootstrap Factory, Scenario Polymorphism,
and Dynamic Rule Failure Resolution.
"""

import pytest
import random
from datetime import datetime

from synapse_simulator.core.interfaces import IClock, IScheduler, IEventQueue, IEventDispatcher
from synapse_simulator.state.interfaces import IStateReader, IStateWriter, IContextBuilder
from synapse_simulator.transitions.interfaces import ITransitionValidator
from synapse_simulator.scenarios.interfaces import IScenarioProfileHook

from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.scheduler import FutureActionScheduler
from synapse_simulator.core.event_queue import EventQueue
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.transitions.transition_manager import TransitionManager

from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.generator.factory import SimulationBootstrapFactory
from synapse_simulator.scenarios.base_scenario import BaseScenario
from synapse_simulator.scenarios.scen_v1_03_allergy import DrugAllergySafetyHoldScenario
from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.state.models import ActionRequest, DecisionResult, DecisionStatus, OutboxEventProposal, StateTransitionProposal, InputContext
from synapse_simulator.core.simulation_engine import SimulationEngine
from synapse_simulator.engine.orchestrator import ExecutionResult


def test_core_protocols_compliance():
    """Verify core classes fulfill runtime-checkable Protocol contracts (DIP & ISP)."""
    clock = SimulationClock()
    scheduler = FutureActionScheduler()
    queue = EventQueue()
    dispatcher = EventDispatcher()
    state_mgr = StateManager()

    assert isinstance(clock, IClock)
    assert isinstance(scheduler, IScheduler)
    assert isinstance(queue, IEventQueue)
    assert isinstance(dispatcher, IEventDispatcher)
    assert isinstance(state_mgr, IStateReader)
    assert isinstance(state_mgr, IStateWriter)
    assert isinstance(state_mgr, IContextBuilder)
    assert isinstance(TransitionManager, ITransitionValidator)


def test_single_responsibility_factory_bootstrap():
    """Verify SimulationBootstrapFactory extracts component instantiation from HospitalSimulator (SRP)."""
    sim = HospitalSimulator(random_seed=123, offline_mode=True)
    
    assert sim.clock is not None
    assert sim.scheduler is not None
    assert sim.event_queue is not None
    assert sim.dispatcher is not None
    assert sim.state_manager is not None
    assert sim.rule_engine is not None
    assert sim.engine is not None
    assert sim.kb is not None
    assert sim.coordinator is not None
    assert len(sim.coordinator.workflow_definitions) >= 4


def test_liskov_substitution_scenario_polymorphism():
    """Verify scenarios configure patient context and conflict flags polymorphically (LSP)."""
    allergy_scen = DrugAllergySafetyHoldScenario(instance_index=1)
    base_scens = [cls(instance_index=1) for cls in BaseScenario.__subclasses__() if cls != DrugAllergySafetyHoldScenario]

    assert isinstance(allergy_scen, IScenarioProfileHook)

    kb = MedicalKnowledgeBase()
    kb.load(enable_pubmed=False)
    rng = random.Random(42)
    patient_gen = PatientProfileGenerator(kb, rng)

    # Allergy scenario forces Penicillin allergy polymorphically
    pat_allergy = allergy_scen.create_patient_profile(patient_gen)
    assert "Penicillin" in pat_allergy.allergies
    assert allergy_scen.should_force_conflict() is True

    # Other scenarios do not force conflict by default
    for other_scen in base_scens:
        assert other_scen.should_force_conflict() is False


def test_open_closed_dynamic_failure_event():
    """Verify SimulationEngine dynamically resolves failure event types from rule results (OCP)."""
    scheduler = FutureActionScheduler()
    engine = SimulationEngine(scheduler=scheduler)

    action_req = ActionRequest(
        action_id="act-test-01",
        action_type="CUSTOM_ACTION",
        target_department="custom",
        target_entity_table="custom.entities",
        target_entity_id="cust-01",
        scenario_instance_id="scen-1-inst-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        requested_timestamp=datetime(2026, 1, 1, 8, 0),
    )

    valid_context = InputContext(
        simulated_timestamp=datetime(2026, 1, 1, 8, 0),
        scenario_id="scen-1",
        scenario_instance_id="scen-1-inst-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        department_id="custom",
        proposed_action=action_req,
    )

    class MockPipeline:
        def execute_action(self, **kwargs):
            return ExecutionResult(
                success=False,
                context=valid_context,
                decision=DecisionResult(
                    status=DecisionStatus.BLOCKED,
                    winning_rule_id="RULE-CUSTOM-DYNAMIC-001",
                    reason="Custom safety block",
                    blocked_actions=["CUSTOM_ACTION"],
                    events_to_emit=[
                        OutboxEventProposal(
                            event_type="CustomDynamicFailureDetected",
                            source_domain="custom",
                            entity_reference={"table_name": "test", "entity_id": "1"},
                            scenario_instance_id="scen-1",
                            patient_journey_id="pj-1",
                            correlation_id="corr-1",
                            causation_id="cause-1",
                        )
                    ],
                ),
                state_applied=False,
            )

    engine.pipeline = MockPipeline()  # type: ignore

    scheduled_action = scheduler.schedule_action(
        action_request=action_req,
        scheduled_at=datetime(2026, 1, 1, 8, 0),
    )

    result, domain_event = engine._process_scheduled_action(scheduled_action)

    assert domain_event.status == "BLOCKED_FAILURE"
    assert domain_event.event_type == "CustomDynamicFailureDetected"


def test_dependency_inversion_state_manager_validator():
    """Verify StateManager accepts an injected custom ITransitionValidator (DIP)."""
    class CustomValidator:
        called = False

        def validate_transition(self, entity_table: str, current_state: str, next_state: str):
            CustomValidator.called = True
            return True, None

        def is_terminal_state(self, entity_table: str, state: str):
            return False

    mgr = StateManager(transition_validator=CustomValidator())
    decision = DecisionResult(
        status=DecisionStatus.ALLOWED,
        winning_rule_id="RULE-TEST-01",
        reason="Test",
        state_transitions=[
            StateTransitionProposal(
                target_entity_table="clinical.appointments",
                target_entity_id="apt-01",
                field_name="status",
                current_value="Draft",
                new_value="Active",
            )
        ],
    )

    mgr.apply_decision(decision)
    assert CustomValidator.called is True
