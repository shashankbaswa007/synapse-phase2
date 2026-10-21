"""
Pure, side-effect-free Rule Engine implementing the 5-Level Precedence Hierarchy.
"""

from typing import List, Optional
from synapse_simulator.state.models import (
    InputContext,
    DecisionResult,
    DecisionStatus,
    StateTransitionProposal,
    CommandProposal,
    OutboxEventProposal,
    DocumentTriggerProposal,
)
from synapse_simulator.rules.models import SynapseRule, PrecedenceLevel
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.evaluator import RuleEvaluator


class RuleEngine:
    """Pure, side-effect-free Rule Engine."""

    def __init__(self, repository: RuleRepository):
        self.repository = repository

    def evaluate(self, context: InputContext) -> DecisionResult:
        """Evaluate an InputContext against candidate rules using 5-Level Precedence Hierarchy."""
        action_type = context.proposed_action.action_type
        department_id = context.department_id
        scenario_id = context.scenario_id

        # 1. Discover candidate rules
        candidate_rules = self.repository.find_applicable_rules(action_type, department_id, scenario_id)

        # 2. Filter rules whose preconditions & boolean conditions pass
        passing_rules: List[SynapseRule] = []
        for rule in candidate_rules:
            if RuleEvaluator.evaluate_preconditions(rule, context):
                if RuleEvaluator.evaluate_conditions(rule, context):
                    passing_rules.append(rule)

        if not passing_rules:
            # Default fallback if no rules match: Allow action with empty effects
            return DecisionResult(
                status=DecisionStatus.ALLOWED,
                winning_rule_id="DEFAULT_FALLBACK_ALLOW",
                winning_rule_priority=0,
                reason=f"No matching rules blocked action '{action_type}'. Approved by default fallback.",
                permitted_actions=[action_type],
            )

        # 3. Sort passing rules by Precedence Level (Highest Level Number First, then by Priority Integer)
        passing_rules.sort(key=lambda r: (int(r.precedence_level), r.priority), reverse=True)

        # 4. Check for Blocking Rules (Level 1 / Level 2 / Level 3 blocks override lower levels)
        for rule in passing_rules:
            if action_type in rule.blocked_actions or "*" in rule.blocked_actions:
                # Highest precedence rule BLOCKS the action
                state_proposals = [
                    StateTransitionProposal(
                        target_entity_table=eff.target_entity,
                        target_entity_id=context.proposed_action.target_entity_id,
                        field_name=eff.target_field,
                        current_value=str(context.entity_state.get("status", "Unknown")),
                        new_value=eff.new_value,
                        additional_updates=eff.additional_updates,
                    )
                    for eff in rule.state_transitions
                ]

                cmd_proposals = [
                    CommandProposal(
                        target_department=eff.target_department,
                        command_type=eff.effect_type,
                        payload=eff.payload,
                    )
                    for eff in rule.cross_department_effects
                ]

                outbox_events = [
                    OutboxEventProposal(
                        event_type=evt_type,
                        source_domain=context.department_id,
                        entity_reference={
                            "table_name": context.proposed_action.target_entity_table,
                            "entity_id": context.proposed_action.target_entity_id,
                        },
                        scenario_instance_id=context.scenario_instance_id,
                        patient_journey_id=context.patient_journey_id,
                        correlation_id=context.correlation_id,
                        causation_id=context.proposed_action.action_id,
                        payload=context.proposed_action.payload,
                    )
                    for evt_type in rule.events_generated
                ]

                doc_triggers = [
                    DocumentTriggerProposal(
                        document_type=doc_type,
                        encounter_id=context.correlation_id,
                        patient_id=str(context.patient_state.get("patient_id", "")),
                    )
                    for doc_type in rule.documents_triggered
                ]

                return DecisionResult(
                    status=DecisionStatus.BLOCKED,
                    winning_rule_id=rule.rule_id,
                    winning_rule_priority=rule.priority,
                    reason=f"Action '{action_type}' BLOCKED by {rule.precedence_level.name} rule '{rule.rule_id}': {rule.description}",
                    blocked_actions=[action_type],
                    state_transitions=state_proposals,
                    cross_department_effects=cmd_proposals,
                    events_to_emit=outbox_events,
                    documents_to_trigger=doc_triggers,
                )

        # 5. If no rule blocks, aggregate permitted actions and effects from passing rules
        winning_rule = passing_rules[0]
        aggregated_transitions: List[StateTransitionProposal] = []
        aggregated_effects: List[CommandProposal] = []
        aggregated_events: List[OutboxEventProposal] = []
        aggregated_documents: List[DocumentTriggerProposal] = []

        for rule in passing_rules:
            for eff in rule.state_transitions:
                aggregated_transitions.append(
                    StateTransitionProposal(
                        target_entity_table=eff.target_entity,
                        target_entity_id=context.proposed_action.target_entity_id,
                        field_name=eff.target_field,
                        current_value=str(context.entity_state.get("status", "Unknown")),
                        new_value=eff.new_value,
                        additional_updates=eff.additional_updates,
                    )
                )

            for eff in rule.cross_department_effects:
                aggregated_effects.append(
                    CommandProposal(
                        target_department=eff.target_department,
                        command_type=eff.effect_type,
                        payload=eff.payload,
                    )
                )

            for evt_type in rule.events_generated:
                aggregated_events.append(
                    OutboxEventProposal(
                        event_type=evt_type,
                        source_domain=context.department_id,
                        entity_reference={
                            "table_name": context.proposed_action.target_entity_table,
                            "entity_id": context.proposed_action.target_entity_id,
                        },
                        scenario_instance_id=context.scenario_instance_id,
                        patient_journey_id=context.patient_journey_id,
                        correlation_id=context.correlation_id,
                        causation_id=context.proposed_action.action_id,
                        payload=context.proposed_action.payload,
                    )
                )

            for doc_type in rule.documents_triggered:
                aggregated_documents.append(
                    DocumentTriggerProposal(
                        document_type=doc_type,
                        encounter_id=context.correlation_id,
                        patient_id=str(context.patient_state.get("patient_id", "")),
                    )
                )

        return DecisionResult(
            status=DecisionStatus.ALLOWED,
            winning_rule_id=winning_rule.rule_id,
            winning_rule_priority=winning_rule.priority,
            reason=f"Action '{action_type}' ALLOWED by precedence Level {winning_rule.precedence_level.value} rule '{winning_rule.rule_id}'.",
            permitted_actions=[action_type],
            state_transitions=aggregated_transitions,
            cross_department_effects=aggregated_effects,
            events_to_emit=aggregated_events,
            documents_to_trigger=aggregated_documents,
        )
