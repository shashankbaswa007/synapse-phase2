"""
Stage 6 Unit Tests: Simulation Clock and Future Action Scheduler.
"""

import pytest
from datetime import datetime, timedelta
from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.scheduler import FutureActionScheduler
from synapse_simulator.state.models import ActionRequest


def test_simulation_clock_time_math():
    clock = SimulationClock(datetime(2026, 1, 1, 8, 0, 0))
    assert clock.now() == datetime(2026, 1, 1, 8, 0, 0)

    clock.advance_by_minutes(45)
    assert clock.now() == datetime(2026, 1, 1, 8, 45, 0)

    clock.advance_to(datetime(2026, 1, 1, 12, 0, 0))
    assert clock.now() == datetime(2026, 1, 1, 12, 0, 0)


def test_future_action_scheduler_lifecycle():
    scheduler = FutureActionScheduler()
    t0 = datetime(2026, 1, 1, 9, 0, 0)

    act1 = ActionRequest(
        action_id="act-1",
        action_type="START_DOCTOR_CONSULTATION",
        target_department="clinical",
        target_entity_table="clinical.appointments",
        target_entity_id="apt-1",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
        requested_timestamp=t0,
    )

    act2 = ActionRequest(
        action_id="act-2",
        action_type="VERIFY_PRESCRIPTION",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-1",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
        requested_timestamp=t0 + timedelta(minutes=15),
    )

    scheduler.schedule_action(act1, scheduled_at=t0)
    scheduler.schedule_action(act2, scheduled_at=t0 + timedelta(minutes=15))

    assert scheduler.size() == 2

    # Retrieve due actions at t0
    due = scheduler.get_due_actions(t0)
    assert len(due) == 1
    assert due[0].action_id == "act-1"
    assert scheduler.size() == 1

    # Cancel act2
    scheduler.cancel_action("act-2")
    assert scheduler.size() == 0


def test_future_action_scheduler_invalidation_on_state_change():
    scheduler = FutureActionScheduler()
    t0 = datetime(2026, 1, 1, 9, 0, 0)

    act = ActionRequest(
        action_id="act-cancel-me",
        action_type="CONFIRM_MEDICINE_DISPENSE",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-99",
        scenario_instance_id="s1",
        patient_journey_id="pj1",
        correlation_id="c1",
        requested_timestamp=t0 + timedelta(minutes=30),
    )

    scheduler.schedule_action(act, scheduled_at=t0 + timedelta(minutes=30))
    assert scheduler.size() == 1

    # Prescription cancelled/replaced state change triggers invalidation of entity actions
    invalidated_count = scheduler.invalidate_entity_actions("pharmacy.prescriptions", "rx-99")
    assert invalidated_count == 1
    assert scheduler.size() == 0

    # Due actions at t0+30 returns empty list because action was invalidated
    due = scheduler.get_due_actions(t0 + timedelta(minutes=30))
    assert len(due) == 0
