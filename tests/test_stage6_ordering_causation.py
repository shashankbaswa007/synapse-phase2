"""
Stage 6 Unit Tests: Event Ordering, Causation, and Correlation Lineage.
"""

from datetime import datetime, timedelta
from synapse_simulator.core.event_queue import EventQueue, SimulationEvent
from synapse_simulator.state.models import ActionRequest
from synapse_simulator.core.scheduler import FutureActionScheduler, ScheduledFutureAction


def test_deterministic_event_ordering():
    eq = EventQueue()
    t0 = datetime(2026, 1, 1, 9, 0, 0)

    # Push 3 events scheduled at the exact same timestamp but with different priorities and sequence numbers
    evt_p50 = SimulationEvent(
        scheduled_at=t0,
        priority=50,
        event_type="Evt_Priority50",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    evt_p10 = SimulationEvent(
        scheduled_at=t0,
        priority=10,  # Higher priority (lower integer)
        event_type="Evt_Priority10",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    eq.push(evt_p50)
    eq.push(evt_p10)

    first = eq.pop()
    assert first.event_type == "Evt_Priority10"
    second = eq.pop()
    assert second.event_type == "Evt_Priority50"


def test_causation_and_correlation_tracking():
    parent_action_id = "act-parent-1"
    patient_journey = "pj-100"
    correlation = "corr-100"

    act_parent = ActionRequest(
        action_id=parent_action_id,
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-1",
        scenario_instance_id="s1",
        patient_journey_id=patient_journey,
        correlation_id=correlation,
        requested_timestamp=datetime(2026, 1, 1, 9, 0, 0),
    )

    # Downstream action inherits correlation_id and sets causation_id to parent_action_id
    act_child = ActionRequest(
        action_id="act-child-2",
        action_type="VERIFY_PRESCRIPTION",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-1",
        scenario_instance_id="s1",
        patient_journey_id=patient_journey,
        correlation_id=correlation,
        causation_id=parent_action_id,
        requested_timestamp=datetime(2026, 1, 1, 9, 5, 0),
    )

    assert act_child.correlation_id == act_parent.correlation_id
    assert act_child.causation_id == act_parent.action_id
    assert act_child.patient_journey_id == act_parent.patient_journey_id
