"""
Execution Pipeline Orchestrator: Coordinates StateManager, RuleEngine, and TransitionManager.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from synapse_simulator.config import settings
from synapse_simulator.state.models import (
    ActionRequest,
    InputContext,
    DecisionResult,
    DecisionStatus,
    StateTransitionProposal,
    CommandProposal,
    OutboxEventProposal,
    DocumentTriggerProposal,
)
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.rules.rule_engine import RuleEngine


class ExecutionResult(BaseModel):
    """Result of an action execution through the pipeline."""
    success: bool
    context: InputContext
    decision: DecisionResult
    state_applied: bool
    causation_depth: int = 0
    emitted_events: List[OutboxEventProposal] = Field(default_factory=list)
    command_proposals: List[CommandProposal] = Field(default_factory=list)
    document_triggers: List[DocumentTriggerProposal] = Field(default_factory=list)


class ExecutionPipeline:
    """Core execution engine orchestrator connecting state management, rule evaluation, and event generation."""

    def __init__(self, state_manager: StateManager, rule_engine: RuleEngine):
        self.state_manager = state_manager
        self.rule_engine = rule_engine

    def execute_action(
        self,
        action: ActionRequest,
        simulated_timestamp: datetime,
        scenario_id: str,
        department_id: str,
        patient_id: Optional[str] = None,
        causation_depth: int = 0,
    ) -> ExecutionResult:
        """Process an ActionRequest through context build, rule evaluation, state application, and event output."""

        # 1. Enforce max causation depth protection
        if causation_depth >= settings.max_causation_depth:
            empty_context = self.state_manager.build_input_context(
                proposed_action=action,
                simulated_timestamp=simulated_timestamp,
                scenario_id=scenario_id,
                department_id=department_id,
                patient_id=patient_id,
            )
            return ExecutionResult(
                success=False,
                context=empty_context,
                decision=DecisionResult(
                    status=DecisionStatus.BLOCKED,
                    winning_rule_id="CAUSATION_DEPTH_EXCEEDED",
                    reason=f"Action '{action.action_type}' exceeded max causation depth limit ({settings.max_causation_depth}).",
                    blocked_actions=[action.action_type],
                ),
                state_applied=False,
                causation_depth=causation_depth,
            )

        # 2. Build input context snapshot
        context = self.state_manager.build_input_context(
            proposed_action=action,
            simulated_timestamp=simulated_timestamp,
            scenario_id=scenario_id,
            department_id=department_id,
            patient_id=patient_id,
        )

        # 3. Evaluate context via RuleEngine
        decision = self.rule_engine.evaluate(context)

        # 4. Apply state transitions if allowed or required by blocking rules
        state_applied = False
        if decision.status == DecisionStatus.ALLOWED or decision.state_transitions:
            ts_str = simulated_timestamp.isoformat()
            for trans in decision.state_transitions:
                if trans.target_entity_table == "laboratory.laboratory_orders":
                    if trans.new_value in ("Completed", "Reported"):
                        trans.additional_updates.setdefault("completed_at", ts_str)
                    if action.payload.get("test_type"):
                        trans.additional_updates.setdefault("test_type", action.payload.get("test_type"))
                    if action.payload.get("test_name"):
                        trans.additional_updates.setdefault("test_name", action.payload.get("test_name"))
                    if action.payload.get("results"):
                        trans.additional_updates.setdefault("results", action.payload.get("results"))
                    if "is_abnormal" in action.payload:
                        trans.additional_updates.setdefault("is_abnormal", action.payload.get("is_abnormal"))
                elif trans.target_entity_table == "radiology.radiology_orders":
                    if trans.new_value in ("Reported", "Completed"):
                        trans.additional_updates.setdefault("completed_at", ts_str)
                    if action.payload.get("modality"):
                        trans.additional_updates.setdefault("modality", action.payload.get("modality"))
                    if action.payload.get("findings"):
                        trans.additional_updates.setdefault("findings", action.payload.get("findings"))
                    if action.payload.get("impression"):
                        trans.additional_updates.setdefault("impression", action.payload.get("impression"))
                    if "is_abnormal" in action.payload:
                        trans.additional_updates.setdefault("is_abnormal", action.payload.get("is_abnormal"))
                elif trans.target_entity_table == "finance.invoices":
                    if trans.new_value in ("Unpaid", "Paid"):
                        trans.additional_updates.setdefault("created_at", ts_str)
                    if trans.new_value == "Paid":
                        trans.additional_updates.setdefault("paid_at", ts_str)
            state_applied = self.state_manager.apply_decision(decision)

        success = decision.status == DecisionStatus.ALLOWED and state_applied

        return ExecutionResult(
            success=success,
            context=context,
            decision=decision,
            state_applied=state_applied,
            causation_depth=causation_depth,
            emitted_events=decision.events_to_emit if success else [],
            command_proposals=decision.cross_department_effects if success else [],
            document_triggers=decision.documents_to_trigger if success else [],
        )
