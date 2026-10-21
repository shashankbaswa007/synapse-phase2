"""
Stage 6 Unit Tests: Domain Event Model and Event Creation.
"""

import pytest
from datetime import datetime
from synapse_simulator.state.models import DomainEvent, ActionRequest
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.core.simulation_engine import SimulationEngine
from synapse_simulator.core.scheduler import FutureActionScheduler


def test_domain_event_model():
    evt = DomainEvent(
        event_id="evt-100",
        event_type="PrescriptionVerified",
        timestamp=datetime(2026, 1, 1, 9, 0, 0),
        producer_domain="pharmacy",
        entity_table="pharmacy.prescriptions",
        entity_id="rx-1",
        scenario_instance_id="s-inst-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
        causation_id="act-1",
        causation_depth=1,
        sequence_number=1,
        status="COMMITTED",
        payload={"drug": "Amoxicillin"},
    )

    assert evt.event_id == "evt-100"
    assert evt.status == "COMMITTED"
    assert evt.sequence_number == 1


def test_blocked_action_emits_failure_event_not_success():
    repo = RuleRepository()
    repo.load_rules()
    rule_engine = RuleEngine(repo)
    state_manager = StateManager()
    scheduler = FutureActionScheduler()
    engine = SimulationEngine(scheduler=scheduler, state_manager=state_manager, rule_engine=rule_engine)

    # Setup patient with Penicillin allergy
    state_manager.set_entity_state("patient.patients", "pat-1", {"allergies": ["Penicillin"]})
    state_manager.set_entity_state("pharmacy.prescriptions", "rx-1", {"status": "Issued"})

    # Action: VERIFY_PRESCRIPTION for Beta-Lactam drug
    action = ActionRequest(
        action_id="act-verify-1",
        action_type="VERIFY_PRESCRIPTION",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-1",
        scenario_instance_id="SCEN-V1-03-inst-1",
        patient_journey_id="pj-3",
        correlation_id="corr-3",
        requested_timestamp=datetime(2026, 1, 1, 9, 0, 0),
        payload={"drug_class": "Beta-Lactam", "patient_id": "pat-1"},
    )

    scheduler.schedule_action(action, scheduled_at=datetime(2026, 1, 1, 9, 0, 0))
    events = engine.run_until(max_events=10)

    assert len(events) == 1
    failed_event = events[0]
    assert failed_event.status == "BLOCKED_FAILURE"
    assert failed_event.event_type == "PrescriptionAllergyConflictDetected"
    assert failed_event.event_type != "PrescriptionVerified"  # Ensures no false success event!
