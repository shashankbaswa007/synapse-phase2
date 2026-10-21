"""
Unit tests for ExecutionPipeline orchestrator.
"""

import pytest
from datetime import datetime
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.engine.orchestrator import ExecutionPipeline
from synapse_simulator.state.models import ActionRequest, DecisionStatus


@pytest.fixture
def pipeline():
    repo = RuleRepository()
    repo.load_rules()
    rule_engine = RuleEngine(repo)
    state_manager = StateManager()
    return ExecutionPipeline(state_manager=state_manager, rule_engine=rule_engine)


def test_pipeline_execution_allowed(pipeline):
    # Setup initial state
    pipeline.state_manager.set_entity_state("clinical.appointments", "apt-101", {"status": "Checked-In"})

    action = ActionRequest(
        action_id="act-101",
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-101",
        scenario_instance_id="scen-101",
        patient_journey_id="pj-101",
        correlation_id="corr-101",
        requested_timestamp=datetime.now(),
    )

    result = pipeline.execute_action(
        action=action,
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-01",
        department_id="clinical",
    )

    assert result.success is True
    assert result.decision.status == DecisionStatus.ALLOWED
    assert result.state_applied is True
    assert len(result.emitted_events) == 1
    assert result.emitted_events[0].event_type == "EncounterStarted"

    # Verify updated state
    assert pipeline.state_manager.get_entity_state("clinical.appointments", "apt-101")["status"] == "In-Consult"


def test_pipeline_execution_causation_depth_limit(pipeline):
    action = ActionRequest(
        action_id="act-999",
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-999",
        scenario_instance_id="scen-999",
        patient_journey_id="pj-999",
        correlation_id="corr-999",
        requested_timestamp=datetime.now(),
    )

    result = pipeline.execute_action(
        action=action,
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-01",
        department_id="clinical",
        causation_depth=10,  # Exceeds max_causation_depth 10 limit
    )

    assert result.success is False
    assert result.decision.winning_rule_id == "CAUSATION_DEPTH_EXCEEDED"
