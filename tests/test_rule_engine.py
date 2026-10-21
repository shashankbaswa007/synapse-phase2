"""
Unit tests for Rule Engine evaluation and 5-Level Precedence Hierarchy.
"""

import pytest
from datetime import datetime
from synapse_simulator.rules.models import (
    SynapseRule,
    PrecedenceLevel,
    RuleCategory,
    RuleSourceType,
    RulePreconditions,
    RuleConditions,
)
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.state.models import ActionRequest, InputContext, DecisionStatus
from synapse_simulator.state.state_manager import StateManager


@pytest.fixture
def repo():
    r = RuleRepository()
    r.load_rules()
    return r


@pytest.fixture
def rule_engine(repo):
    return RuleEngine(repo)


def test_yaml_rules_loaded(repo):
    assert len(repo.rules) >= 3
    assert repo.get_rule_by_id("RULE-GLOB-STOCK-001") is not None
    assert repo.get_rule_by_id("RULE-WORK-OPD-010") is not None
    assert repo.get_rule_by_id("RULE-CLIN-ALLERGY-001") is not None


def test_workflow_rule_allowed(rule_engine):
    action = ActionRequest(
        action_id="act-001",
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-100",
        scenario_instance_id="scen-inst-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        requested_timestamp=datetime.now(),
    )

    context = InputContext(
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-01",
        scenario_instance_id="scen-inst-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        department_id="clinical",
        proposed_action=action,
        entity_state={"status": "Checked-In"},
    )

    decision = rule_engine.evaluate(context)
    assert decision.status == DecisionStatus.ALLOWED
    assert decision.winning_rule_id == "RULE-WORK-OPD-010"
    assert len(decision.state_transitions) == 1
    assert decision.state_transitions[0].new_value == "In-Consult"


def test_allergy_safety_hold_blocked(rule_engine):
    action = ActionRequest(
        action_id="act-002",
        action_type="VERIFY_PRESCRIPTION",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-500",
        scenario_instance_id="scen-inst-3",
        patient_journey_id="pj-3",
        correlation_id="corr-3",
        requested_timestamp=datetime.now(),
        payload={"drug_class": "Beta-Lactam"},
    )

    context = InputContext(
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-03",
        scenario_instance_id="scen-inst-3",
        patient_journey_id="pj-3",
        correlation_id="corr-3",
        department_id="pharmacy",
        proposed_action=action,
        patient_state={"allergies": ["Penicillin", "Dust"]},
        entity_state={"status": "Issued"},
        extra_context={"drug_class": "Beta-Lactam"},
    )

    decision = rule_engine.evaluate(context)
    assert decision.status == DecisionStatus.BLOCKED
    assert decision.winning_rule_id == "RULE-CLIN-ALLERGY-001"
    assert "Blocked_Safety_Hold" in [t.new_value for t in decision.state_transitions]
    assert len(decision.cross_department_effects) == 1
    assert decision.cross_department_effects[0].target_department == "clinical"


def test_stock_non_negative_blocked(rule_engine):
    action = ActionRequest(
        action_id="act-003",
        action_type="CONFIRM_MEDICINE_DISPENSE",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-501",
        scenario_instance_id="scen-inst-4",
        patient_journey_id="pj-4",
        correlation_id="corr-4",
        requested_timestamp=datetime.now(),
        payload={"requested_quantity": 10},
    )

    context = InputContext(
        simulated_timestamp=datetime.now(),
        scenario_id="SCEN-V1-04",
        scenario_instance_id="scen-inst-4",
        patient_journey_id="pj-4",
        correlation_id="corr-4",
        department_id="pharmacy",
        proposed_action=action,
        entity_state={"status": "Issued"},
        resource_state={"quantity_available": 2},  # requested 10 > available 2
        extra_context={"requested_quantity": 10},
    )

    decision = rule_engine.evaluate(context)
    assert decision.status == DecisionStatus.BLOCKED
    assert decision.winning_rule_id == "RULE-GLOB-STOCK-001"
