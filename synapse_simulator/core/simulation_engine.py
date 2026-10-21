"""
Stage 6 Simulation Engine: Time-Driven & Event-Driven Core Execution Engine.
"""

import uuid
import itertools
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.scheduler import FutureActionScheduler, ScheduledFutureAction
from synapse_simulator.core.event_queue import EventQueue, SimulationEvent
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.engine.orchestrator import ExecutionPipeline, ExecutionResult
from synapse_simulator.state.models import DomainEvent, DecisionStatus, ActionRequest

_domain_evt_counter = itertools.count()

class SimulationEngine:
    """Core Time-Driven & Event-Driven Simulation Engine for Synapse Phase 2."""

    def __init__(
        self,
        clock: Optional[SimulationClock] = None,
        scheduler: Optional[FutureActionScheduler] = None,
        event_queue: Optional[EventQueue] = None,
        dispatcher: Optional[EventDispatcher] = None,
        state_manager: Optional[StateManager] = None,
        rule_engine: Optional[RuleEngine] = None,
        execution_pipeline: Optional[ExecutionPipeline] = None,
    ):
        self.clock = clock or SimulationClock()
        self.scheduler = scheduler or FutureActionScheduler()
        self.event_queue = event_queue or EventQueue()
        self.dispatcher = dispatcher or EventDispatcher()
        self.state_manager = state_manager or StateManager()
        self.rule_engine = rule_engine
        self.pipeline = execution_pipeline

        if rule_engine and state_manager and not execution_pipeline:
            self.pipeline = ExecutionPipeline(state_manager, rule_engine)

        self.committed_events: List[DomainEvent] = []
        self.trace_log: List[Dict[str, Any]] = []

    def step(self) -> bool:
        """Process the single next temporal item (event or scheduled action). Returns True if processed, False if queue empty."""
        next_evt = self.event_queue.peek()
        next_action_time = self.scheduler.peek_next_due_time()

        if not next_evt and not next_action_time:
            return False

        evt_time = next_evt.scheduled_at if next_evt else None
        if evt_time and (not next_action_time or evt_time <= next_action_time):
            event = self.event_queue.pop()
            if event:
                self._process_simulation_event(event)
                return True
        else:
            self.clock.advance_to(next_action_time)
            due_actions = self.scheduler.get_due_actions(next_action_time)
            for saction in due_actions:
                self._process_scheduled_action(saction)
            return True

        return False

    def run_until(
        self,
        until_time: Optional[datetime] = None,
        max_events: int = 1000,
    ) -> List[DomainEvent]:
        """Run simulation loop until end time or max events limit reached."""
        processed = 0

        while processed < max_events:
            # Check next item timestamps
            next_evt = self.event_queue.peek()
            next_action_time = self.scheduler.peek_next_due_time()

            if not next_evt and not next_action_time:
                break  # Queue empty

            # Pick whichever is earlier
            evt_time = next_evt.scheduled_at if next_evt else None
            
            if evt_time and (not next_action_time or evt_time <= next_action_time):
                # Process next simulation event
                event = self.event_queue.pop()
                if not event:
                    break
                self._process_simulation_event(event)
            else:
                # Process due action
                current_target_time = next_action_time
                if until_time and current_target_time > until_time:
                    break
                self.clock.advance_to(current_target_time)
                due_actions = self.scheduler.get_due_actions(current_target_time)
                for saction in due_actions:
                    self._process_scheduled_action(saction)

            processed += 1

        return self.committed_events

    def _process_simulation_event(self, event: SimulationEvent) -> None:
        """Process a simulation event by advancing clock and generating action proposals."""
        self.clock.advance_to(event.scheduled_at)
        
        # Dispatch event to departmental handlers
        action_requests = self.dispatcher.dispatch(event)

        # Schedule generated action requests for immediate or delayed execution
        for req in action_requests:
            self.scheduler.schedule_action(
                action_request=req,
                scheduled_at=self.clock.now(),
                causation_depth=event.causation_depth,
            )

    def _process_scheduled_action(self, scheduled_action: ScheduledFutureAction) -> Tuple[ExecutionResult, DomainEvent]:
        """Execute a scheduled action through ExecutionPipeline, emitting formal DomainEvents."""
        action = scheduled_action.action_request

        if not self.pipeline:
            raise RuntimeError("ExecutionPipeline is required to process scheduled actions")

        result = self.pipeline.execute_action(
            action=action,
            simulated_timestamp=self.clock.now(),
            scenario_id=action.scenario_instance_id.split("-inst-")[0] if "-inst-" in action.scenario_instance_id else "SCEN",
            department_id=action.target_department,
            patient_id=action.payload.get("patient_id"),
            causation_depth=scheduled_action.causation_depth,
        )

        seq_num = next(_domain_evt_counter)

        if result.success and result.decision.status == DecisionStatus.ALLOWED:
            # 1. Create COMMITTED DomainEvent
            domain_event = DomainEvent(
                event_id=f"evt-{uuid.uuid4().hex[:10]}",
                event_type=result.emitted_events[0].event_type if result.emitted_events else f"{action.action_type}_Executed",
                timestamp=self.clock.now(),
                producer_domain=action.target_department,
                entity_table=action.target_entity_table,
                entity_id=action.target_entity_id,
                scenario_instance_id=action.scenario_instance_id,
                patient_journey_id=action.patient_journey_id,
                correlation_id=action.correlation_id,
                causation_id=action.action_id,
                causation_depth=scheduled_action.causation_depth,
                sequence_number=seq_num,
                status="COMMITTED",
                payload=action.payload,
            )
            self.committed_events.append(domain_event)

            # Record step in trace log
            self.trace_log.append({
                "time": self.clock.now().isoformat(),
                "action": action.action_type,
                "target_entity": f"{action.target_entity_table}:{action.target_entity_id}",
                "rule_winning": result.decision.winning_rule_id,
                "status": "ALLOWED",
                "domain_event": domain_event.event_type,
            })

            # Check if entity moved to terminal state, invalidate future pending actions for it
            entity_state = self.state_manager.get_entity_state(action.target_entity_table, action.target_entity_id)
            current_status = entity_state.get("status")
            if current_status in ["Cancelled", "Completed", "Archived", "Cancelled_Replaced", "Depleted", "Expired"]:
                self.scheduler.invalidate_entity_actions(action.target_entity_table, action.target_entity_id)

            # Route emitted outbox events to downstream dispatcher
            for outbox_evt in result.emitted_events:
                sim_evt = SimulationEvent(
                    scheduled_at=self.clock.now(),
                    event_type=outbox_evt.event_type,
                    source_department=outbox_evt.source_domain,
                    scenario_instance_id=outbox_evt.scenario_instance_id,
                    patient_journey_id=outbox_evt.patient_journey_id,
                    correlation_id=outbox_evt.correlation_id,
                    causation_id=action.action_id,
                    causation_depth=scheduled_action.causation_depth + 1,
                    payload=outbox_evt.payload,
                )
                self.event_queue.push(sim_evt)

        else:
            # 2. Create BLOCKED_FAILURE DomainEvent (Never a false success event!)
            failure_event_type = f"{action.action_type}_Blocked"
            if result.decision.events_to_emit:
                failure_event_type = result.decision.events_to_emit[0].event_type
            elif result.decision.winning_rule_id == "RULE-CLIN-ALLERGY-001":
                failure_event_type = "PrescriptionAllergyConflictDetected"
            elif result.decision.winning_rule_id == "RULE-GLOB-STOCK-001":
                failure_event_type = "InventoryShortageDetected"

            domain_event = DomainEvent(
                event_id=f"evt-err-{uuid.uuid4().hex[:10]}",
                event_type=failure_event_type,
                timestamp=self.clock.now(),
                producer_domain=action.target_department,
                entity_table=action.target_entity_table,
                entity_id=action.target_entity_id,
                scenario_instance_id=action.scenario_instance_id,
                patient_journey_id=action.patient_journey_id,
                correlation_id=action.correlation_id,
                causation_id=action.action_id,
                causation_depth=scheduled_action.causation_depth,
                sequence_number=seq_num,
                status="BLOCKED_FAILURE",
                payload={"reason": result.decision.reason, **action.payload},
            )
            self.committed_events.append(domain_event)

            self.trace_log.append({
                "time": self.clock.now().isoformat(),
                "action": action.action_type,
                "target_entity": f"{action.target_entity_table}:{action.target_entity_id}",
                "rule_winning": result.decision.winning_rule_id,
                "status": "BLOCKED",
                "domain_event": domain_event.event_type,
                "reason": result.decision.reason,
            })

            # Route failure event to dispatcher to trigger safety reaction (e.g. clinical alert)
            sim_evt = SimulationEvent(
                scheduled_at=self.clock.now(),
                event_type=failure_event_type,
                source_department=action.target_department,
                scenario_instance_id=action.scenario_instance_id,
                patient_journey_id=action.patient_journey_id,
                correlation_id=action.correlation_id,
                causation_id=action.action_id,
                causation_depth=scheduled_action.causation_depth + 1,
                payload=domain_event.payload,
            )
            self.event_queue.push(sim_evt)

        return result, domain_event
