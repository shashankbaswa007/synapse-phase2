"""
Stage 6 Unit Tests: Event Loop Protection and Handler Failure Isolation.
"""

import pytest
from datetime import datetime
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.engine.orchestrator import ExecutionPipeline
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.models import ActionRequest


def test_handler_error_isolation():
    dispatcher = EventDispatcher()

    def faulty_handler(event: SimulationEvent):
        raise RuntimeError("Simulated department handler bug!")

    def healthy_handler(event: SimulationEvent):
        return [
            ActionRequest(
                action_id="act-ok",
                action_type="VERIFY_PRESCRIPTION",
                target_department="pharmacy",
                target_entity_table="pharmacy.prescriptions",
                target_entity_id="rx-1",
                scenario_instance_id=event.scenario_instance_id,
                patient_journey_id=event.patient_journey_id,
                correlation_id=event.correlation_id,
                requested_timestamp=event.scheduled_at,
            )
        ]

    dispatcher.register_handler("TestEvent", faulty_handler)
    dispatcher.register_handler("TestEvent", healthy_handler)

    evt = SimulationEvent(
        scheduled_at=datetime.now(),
        event_type="TestEvent",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    # Faulty handler exception is caught gracefully, healthy handler returns action
    generated = dispatcher.dispatch(evt)
    assert len(generated) == 1
    assert generated[0].action_id == "act-ok"


def test_causation_depth_limit_protection():
    repo = RuleRepository()
    repo.load_rules()
    rule_engine = RuleEngine(repo)
    state_manager = StateManager()
    pipeline = ExecutionPipeline(state_manager, rule_engine)

    action = ActionRequest(
        action_id="act-depth-10",
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-1",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
        requested_timestamp=datetime.now(),
    )

    # Max causation depth = 10
    result = pipeline.execute_action(
        action=action,
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-01",
        department_id="clinical",
        causation_depth=10,  # Exceeds max depth limit!
    )

    assert result.success is False
    assert result.decision.winning_rule_id == "CAUSATION_DEPTH_EXCEEDED"
