"""
Unit tests for SimulationClock and EventQueue priority queue.
"""

import pytest
from datetime import datetime, timedelta
from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.event_queue import SimulationEvent, EventQueue


def test_simulation_clock():
    start = datetime(2026, 1, 1, 9, 0, 0)
    clock = SimulationClock(start)
    assert clock.now() == start

    clock.advance_by_minutes(30)
    assert clock.now() == datetime(2026, 1, 1, 9, 30, 0)

    clock.advance_to(datetime(2026, 1, 1, 10, 0, 0))
    assert clock.now() == datetime(2026, 1, 1, 10, 0, 0)

    with pytest.raises(ValueError):
        clock.advance_to(datetime(2026, 1, 1, 8, 0, 0))


def test_event_queue_priority_order():
    eq = EventQueue()
    t0 = datetime(2026, 1, 1, 9, 0, 0)

    evt_late = SimulationEvent(
        scheduled_at=t0 + timedelta(minutes=15),
        event_type="LateEvent",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    evt_early = SimulationEvent(
        scheduled_at=t0 + timedelta(minutes=5),
        event_type="EarlyEvent",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    eq.push(evt_late)
    eq.push(evt_early)

    assert eq.size() == 2
    popped1 = eq.pop()
    assert popped1.event_type == "EarlyEvent"

    popped2 = eq.pop()
    assert popped2.event_type == "LateEvent"

    assert eq.is_empty()


def test_event_queue_cancellation():
    eq = EventQueue()
    t0 = datetime(2026, 1, 1, 9, 0, 0)

    evt1 = SimulationEvent(
        scheduled_at=t0,
        event_type="Event1",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    evt2 = SimulationEvent(
        scheduled_at=t0 + timedelta(minutes=5),
        event_type="Event2",
        source_department="clinical",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
    )

    eq.push(evt1)
    eq.push(evt2)

    eq.cancel(evt1.event_id)

    popped = eq.pop()
    assert popped.event_type == "Event2"
    assert eq.pop() is None
