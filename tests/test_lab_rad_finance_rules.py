import pytest
from datetime import datetime
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.state.models import ActionRequest, InputContext
from synapse_simulator.state.state_manager import StateManager

@pytest.fixture
def engine():
    repo = RuleRepository()
    repo.load_rules()
    return RuleEngine(repo)

@pytest.fixture
def state_manager():
    sm = StateManager()
    sm.set_entity_state("laboratory.laboratory_orders", "lab-001", {"status": "Ordered"})
    sm.set_entity_state("radiology.radiology_orders", "rad-001", {"status": "Ordered"})
    sm.set_entity_state("finance.invoices", "inv-001", {"status": "Draft"})
    return sm

def test_lab_rule(engine, state_manager):
    action = ActionRequest(
        action_id="act-1",
        action_type="COLLECT_LAB_SAMPLE",
        target_department="laboratory",
        target_entity_table="laboratory.laboratory_orders",
        target_entity_id="lab-001",
        scenario_instance_id="scen-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        requested_timestamp=datetime.now()
    )
    context = state_manager.build_input_context(action, datetime.now(), "SCEN-V1-01", "laboratory")
    decision = engine.evaluate(context)
    assert decision.status == "ALLOWED"
    assert "RULE-STATE-LAB-010" in decision.winning_rule_id
    assert any(st.new_value == "Sample-Collected" for st in decision.state_transitions)
    assert any(ev.event_type == "LabSampleCollected" for ev in decision.events_to_emit)

def test_rad_rule(engine, state_manager):
    action = ActionRequest(
        action_id="act-2",
        action_type="ACQUIRE_RADIOLOGY_IMAGE",
        target_department="radiology",
        target_entity_table="radiology.radiology_orders",
        target_entity_id="rad-001",
        scenario_instance_id="scen-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        requested_timestamp=datetime.now()
    )
    context = state_manager.build_input_context(action, datetime.now(), "SCEN-V1-01", "radiology")
    decision = engine.evaluate(context)
    assert decision.status == "ALLOWED"
    assert "RULE-STATE-RAD-010" in decision.winning_rule_id
    assert any(st.new_value == "Image-Acquired" for st in decision.state_transitions)
    assert any(ev.event_type == "RadiologyImageAcquired" for ev in decision.events_to_emit)

def test_finance_rule(engine, state_manager):
    action = ActionRequest(
        action_id="act-3",
        action_type="GENERATE_INVOICE",
        target_department="finance",
        target_entity_table="finance.invoices",
        target_entity_id="inv-001",
        scenario_instance_id="scen-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        requested_timestamp=datetime.now()
    )
    context = state_manager.build_input_context(action, datetime.now(), "SCEN-V1-01", "finance")
    decision = engine.evaluate(context)
    assert decision.status == "ALLOWED"
    assert "RULE-STATE-FIN-010" in decision.winning_rule_id
    assert any(st.new_value == "Unpaid" for st in decision.state_transitions)
    assert any(ev.event_type == "InvoiceGenerated" for ev in decision.events_to_emit)
