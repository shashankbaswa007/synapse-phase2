"""
Stage 7 Unit Tests: Executable Workflow Definitions and Patient Journey progression.
"""

import pytest
from datetime import datetime
from synapse_simulator.workflows.model import PatientJourney, JourneyStatus
from synapse_simulator.workflows.coordinator import WorkflowCoordinator
from synapse_simulator.workflows.templates import get_all_scenario_workflows
from synapse_simulator.core.scheduler import FutureActionScheduler
from synapse_simulator.state.models import DecisionResult, DecisionStatus, DomainEvent


def test_workflow_templates_registration():
    scheduler = FutureActionScheduler()
    coordinator = WorkflowCoordinator(scheduler)
    workflows = get_all_scenario_workflows()

    assert "SCEN-V1-01" in workflows
    assert "SCEN-V1-02" in workflows
    assert "SCEN-V1-03" in workflows
    assert "SCEN-V1-04" in workflows

    for wdef in workflows.values():
        coordinator.register_workflow(wdef)

    assert len(coordinator.workflow_definitions) == 4


def test_patient_journey_workflow_progression():
    scheduler = FutureActionScheduler()
    coordinator = WorkflowCoordinator(scheduler)
    for wdef in get_all_scenario_workflows().values():
        coordinator.register_workflow(wdef)

    t0 = datetime(2026, 1, 1, 9, 0, 0)
    journey = PatientJourney(
        journey_id="pj-test-1",
        patient_id="pat-1",
        scenario_id="SCEN-V1-01",
        scenario_instance_id="SCEN-V1-01-inst-1",
        correlation_id="corr-1",
        start_time=t0,
    )

    action = coordinator.start_journey(journey, start_time=t0)
    assert action is not None
    assert action.action_type == "START_DOCTOR_CONSULTATION"
    assert journey.current_step_id == "step_consult"

    # Simulate ALLOWED decision and domain event for step_consult
    decision = DecisionResult(
        status=DecisionStatus.ALLOWED,
        winning_rule_id="RULE-WORK-OPD-010",
        reason="Allowed",
    )
    event = DomainEvent(
        event_id="evt-1",
        event_type="EncounterStarted",
        timestamp=t0,
        producer_domain="clinical",
        entity_table="clinical.appointments",
        entity_id="apt-1",
        scenario_instance_id=journey.scenario_instance_id,
        patient_journey_id=journey.journey_id,
        correlation_id=journey.correlation_id,
        sequence_number=1,
    )

    next_action = coordinator.advance_journey("pj-test-1", "step_consult", decision, event, current_time=t0)
    assert next_action is not None
    assert next_action.action_type == "VERIFY_PRESCRIPTION"
    assert journey.current_step_id == "step_verify"
