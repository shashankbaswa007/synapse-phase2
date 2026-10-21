"""
Unit tests for StateManager in-memory snapshot and state transition application.
"""

import pytest
from datetime import datetime
from synapse_simulator.state.models import (
    ActionRequest,
    DecisionResult,
    DecisionStatus,
    StateTransitionProposal,
)
from synapse_simulator.state.state_manager import StateManager


def test_state_manager_store_and_retrieve():
    sm = StateManager()
    sm.set_entity_state("patient.patients", "pat-1", {"name": "John Doe", "status": "Registered"})

    state = sm.get_entity_state("patient.patients", "pat-1")
    assert state["name"] == "John Doe"
    assert state["status"] == "Registered"

    # Non-existent key returns empty dict
    assert sm.get_entity_state("patient.patients", "pat-99") == {}


def test_state_manager_build_input_context():
    sm = StateManager()
    sm.set_entity_state("patient.patients", "pat-10", {"allergies": ["Aspirin"], "status": "Active"})
    sm.set_entity_state("clinical.appointments", "apt-10", {"status": "Checked-In"})

    action = ActionRequest(
        action_id="act-10",
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-10",
        scenario_instance_id="scen-10",
        patient_journey_id="pj-10",
        correlation_id="corr-10",
        requested_timestamp=datetime.now(),
        payload={"note": "Routine checkup"},
    )

    context = sm.build_input_context(
        proposed_action=action,
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-01",
        department_id="clinical",
        patient_id="pat-10",
    )

    assert context.patient_state["allergies"] == ["Aspirin"]
    assert context.entity_state["status"] == "Checked-In"
    assert context.extra_context["note"] == "Routine checkup"


def test_state_manager_apply_valid_decision():
    sm = StateManager()
    sm.set_entity_state("clinical.appointments", "apt-20", {"status": "Checked-In"})

    proposal = StateTransitionProposal(
        target_entity_table="clinical.appointments",
        target_entity_id="apt-20",
        field_name="status",
        current_value="Checked-In",
        new_value="In-Consult",
        additional_updates={"doctor_id": "doc-5"},
    )

    decision = DecisionResult(
        status=DecisionStatus.ALLOWED,
        winning_rule_id="RULE-WORK-OPD-010",
        reason="Allowed",
        state_transitions=[proposal],
    )

    applied = sm.apply_decision(decision)
    assert applied is True

    updated_state = sm.get_entity_state("clinical.appointments", "apt-20")
    assert updated_state["status"] == "In-Consult"
    assert updated_state["doctor_id"] == "doc-5"


def test_state_manager_apply_invalid_transition():
    sm = StateManager()
    sm.set_entity_state("clinical.appointments", "apt-30", {"status": "Scheduled"})

    # Scheduled -> Completed is invalid without Checked-In & In-Consult
    proposal = StateTransitionProposal(
        target_entity_table="clinical.appointments",
        target_entity_id="apt-30",
        field_name="status",
        current_value="Scheduled",
        new_value="Completed",
    )

    decision = DecisionResult(
        status=DecisionStatus.ALLOWED,
        winning_rule_id="RULE-TEST",
        reason="Invalid state transition attempt",
        state_transitions=[proposal],
    )

    applied = sm.apply_decision(decision)
    assert applied is False
    assert sm.get_entity_state("clinical.appointments", "apt-30")["status"] == "Scheduled"
