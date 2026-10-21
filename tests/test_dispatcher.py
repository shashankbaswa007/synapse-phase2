"""
Unit tests for EventDispatcher routing and event handling.
"""

from datetime import datetime
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.state.models import ActionRequest


def test_event_dispatcher():
    dispatcher = EventDispatcher()

    actions_generated = []

    def mock_handler(event: SimulationEvent):
        req = ActionRequest(
            action_id="act-resp-1",
            action_type="VERIFY_PRESCRIPTION",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            target_entity_id="rx-10",
            scenario_instance_id=event.scenario_instance_id,
            patient_journey_id=event.patient_journey_id,
            correlation_id=event.correlation_id,
            requested_timestamp=event.scheduled_at,
        )
        return [req]

    dispatcher.register_handler("PrescriptionIssued", mock_handler)

    evt = SimulationEvent(
        scheduled_at=datetime.now(),
        event_type="PrescriptionIssued",
        source_department="clinical",
        scenario_instance_id="scen-1",
        patient_journey_id="pj-1",
        correlation_id="corr-1",
    )

    generated = dispatcher.dispatch(evt)
    assert len(generated) == 1
    assert generated[0].action_type == "VERIFY_PRESCRIPTION"
    assert len(dispatcher.event_history) == 1
