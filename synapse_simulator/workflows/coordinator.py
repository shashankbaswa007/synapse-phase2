"""
Workflow Coordinator: Orchestrates PatientJourney workflow execution step-by-step.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from synapse_simulator.workflows.model import (
    PatientJourney,
    WorkflowDefinition,
    WorkflowStep,
    JourneyStatus,
)
from synapse_simulator.state.models import ActionRequest, DecisionResult, DecisionStatus, DomainEvent
from synapse_simulator.core.scheduler import FutureActionScheduler


class WorkflowCoordinator:
    """Coordinates patient journey step progression and cross-department workflows."""

    def __init__(self, scheduler: FutureActionScheduler):
        self.scheduler = scheduler
        self.active_journeys: Dict[str, PatientJourney] = {}
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        """Register a scenario workflow definition."""
        self.workflow_definitions[definition.scenario_id] = definition

    def start_journey(
        self,
        journey: PatientJourney,
        start_time: datetime,
    ) -> Optional[ActionRequest]:
        """Initialize and start a patient journey, scheduling its initial workflow step."""
        wdef = self.workflow_definitions.get(journey.scenario_id)
        if not wdef:
            raise ValueError(f"WorkflowDefinition not found for scenario '{journey.scenario_id}'")

        self.active_journeys[journey.journey_id] = journey
        journey.current_step_id = wdef.initial_step_id

        step = wdef.get_step(wdef.initial_step_id)
        if not step:
            return None

        # Build initial action request
        target_entity_id = journey.entity_references.get(
            step.target_entity_table, f"ent-{uuid.uuid4().hex[:8]}"
        )

        action = ActionRequest(
            action_id=f"act-{uuid.uuid4().hex[:8]}",
            action_type=step.action_type,
            target_department=step.target_department,
            target_entity_table=step.target_entity_table,
            target_entity_id=target_entity_id,
            scenario_instance_id=journey.scenario_instance_id,
            patient_journey_id=journey.journey_id,
            correlation_id=journey.correlation_id,
            requested_timestamp=start_time + timedelta(seconds=step.delay_seconds),
            payload={
                "patient_id": journey.patient_id,
                "journey_id": journey.journey_id,
                "step_id": step.step_id,
                **step.payload_template,
                **journey.entity_references,
            },
        )

        self.scheduler.schedule_action(
            action_request=action,
            scheduled_at=start_time + timedelta(seconds=step.delay_seconds),
        )

        return action

    def advance_journey(
        self,
        journey_id: str,
        current_step_id: str,
        decision: DecisionResult,
        event: DomainEvent,
        current_time: datetime,
    ) -> Optional[ActionRequest]:
        """Advance a patient journey to its next workflow step based on decision and domain event."""
        journey = self.active_journeys.get(journey_id)
        if not journey or journey.status != JourneyStatus.ACTIVE:
            return None

        # Guard against duplicate, stale, or rogue action events
        if journey.current_step_id != current_step_id:
            return None

        wdef = self.workflow_definitions.get(journey.scenario_id)
        if not wdef:
            return None

        step = wdef.get_step(current_step_id)
        if not step:
            return None

        journey.completed_steps.append(current_step_id)
        journey.trace_history.append({
            "step_id": current_step_id,
            "action_type": step.action_type,
            "status": decision.status,
            "rule": decision.winning_rule_id,
            "event_type": event.event_type,
            "timestamp": current_time.isoformat(),
        })

        if decision.status == DecisionStatus.ALLOWED:
            # Determine next step
            next_step_id = step.next_step_id

            # Check conditional branches if available
            if step.conditional_branches:
                new_state_val = event.payload.get("status") or event.payload.get("new_value")
                if new_state_val in step.conditional_branches:
                    next_step_id = step.conditional_branches[new_state_val]

            if next_step_id:
                next_step = wdef.get_step(next_step_id)
                if next_step:
                    journey.current_step_id = next_step_id
                    target_entity_id = journey.entity_references.get(
                        next_step.target_entity_table, f"ent-{uuid.uuid4().hex[:8]}"
                    )

                    next_action = ActionRequest(
                        action_id=f"act-{uuid.uuid4().hex[:8]}",
                        action_type=next_step.action_type,
                        target_department=next_step.target_department,
                        target_entity_table=next_step.target_entity_table,
                        target_entity_id=target_entity_id,
                        scenario_instance_id=journey.scenario_instance_id,
                        patient_journey_id=journey.journey_id,
                        correlation_id=journey.correlation_id,
                        causation_id=event.event_id,
                        requested_timestamp=current_time + timedelta(seconds=next_step.delay_seconds),
                        payload={
                            "patient_id": journey.patient_id,
                            "journey_id": journey.journey_id,
                            "step_id": next_step.step_id,
                            **next_step.payload_template,
                            **journey.entity_references,
                        },
                    )

                    self.scheduler.schedule_action(
                        action_request=next_action,
                        scheduled_at=current_time + timedelta(seconds=next_step.delay_seconds),
                    )
                    return next_action
            else:
                # Journey complete
                journey.status = JourneyStatus.COMPLETED
                journey.end_time = current_time
                journey.outcome = "SUCCESS_COMPLETED"
                journey.current_step_id = None
                return None
        else:
            # Action BLOCKED
            if step.failure_step_id:
                fail_step = wdef.get_step(step.failure_step_id)
                if fail_step:
                    journey.current_step_id = step.failure_step_id
                    target_entity_id = journey.entity_references.get(
                        fail_step.target_entity_table, f"ent-{uuid.uuid4().hex[:8]}"
                    )

                    recovery_action = ActionRequest(
                        action_id=f"act-rec-{uuid.uuid4().hex[:8]}",
                        action_type=fail_step.action_type,
                        target_department=fail_step.target_department,
                        target_entity_table=fail_step.target_entity_table,
                        target_entity_id=target_entity_id,
                        scenario_instance_id=journey.scenario_instance_id,
                        patient_journey_id=journey.journey_id,
                        correlation_id=journey.correlation_id,
                        causation_id=event.event_id,
                        requested_timestamp=current_time + timedelta(seconds=fail_step.delay_seconds),
                        payload={
                            "patient_id": journey.patient_id,
                            "journey_id": journey.journey_id,
                            "step_id": fail_step.step_id,
                            "blocked_rule": decision.winning_rule_id,
                            **fail_step.payload_template,
                            **journey.entity_references,
                        },
                    )

                    self.scheduler.schedule_action(
                        action_request=recovery_action,
                        scheduled_at=current_time + timedelta(seconds=fail_step.delay_seconds),
                    )
                    return recovery_action

            # No recovery step defined: mark journey as BLOCKED/TERMINATED
            journey.status = JourneyStatus.BLOCKED
            journey.end_time = current_time
            journey.outcome = f"BLOCKED_BY_{decision.winning_rule_id}"
            return None
