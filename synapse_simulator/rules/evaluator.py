"""
Rule Evaluator: Safe boolean expression evaluation against InputContext.
"""

from typing import Dict, Any, List
from simpleeval import SimpleEval
from synapse_simulator.state.models import InputContext
from synapse_simulator.rules.models import SynapseRule


class RuleEvaluator:
    """Evaluates rule preconditions and boolean conditions against an InputContext."""

    @staticmethod
    def evaluate_preconditions(rule: SynapseRule, context: InputContext) -> bool:
        """Check if action type matches and all required context keys exist."""
        pre = rule.preconditions
        if pre.action_type and pre.action_type != context.proposed_action.action_type:
            return False

        # Convert context to dict lookup for required keys check
        context_dict = RuleEvaluator._context_to_dict(context)
        for key in pre.required_context_keys:
            if not RuleEvaluator._has_key_path(context_dict, key):
                return False
        return True

    @staticmethod
    def evaluate_conditions(rule: SynapseRule, context: InputContext) -> bool:
        """Evaluate all_of, any_of, and none_of expressions."""
        conds = rule.conditions
        context_dict = RuleEvaluator._context_to_dict(context)

        # Build evaluation context for SimpleEval
        eval_context = {
            "context": context_dict,
            "action": context.proposed_action.model_dump(),
            "patient": context.patient_state,
            "entity": context.entity_state,
            "resource": context.resource_state,
        }

        # Evaluate `all_of` expressions (ALL must be True)
        if conds.all_of:
            for expr in conds.all_of:
                if not RuleEvaluator._eval_expr(expr, eval_context):
                    return False

        # Evaluate `any_of` expressions (AT LEAST ONE must be True)
        if conds.any_of:
            any_passed = any(RuleEvaluator._eval_expr(expr, eval_context) for expr in conds.any_of)
            if not any_passed:
                return False

        # Evaluate `none_of` expressions (NONE must be True)
        if conds.none_of:
            for expr in conds.none_of:
                if RuleEvaluator._eval_expr(expr, eval_context):
                    return False

        return True

    @staticmethod
    def _eval_expr(expr: str, eval_context: Dict[str, Any]) -> bool:
        """Safely evaluate a single pythonic expression using SimpleEval."""
        try:
            s = SimpleEval(names=eval_context)
            # Add custom helper functions if needed
            s.functions["CONTAINS"] = lambda container, item: item in container if container else False
            s.functions["EQUALS"] = lambda a, b: a == b
            result = s.eval(expr)
            return bool(result)
        except Exception as e:
            # Fallback simple string checks if simpleeval syntax differs
            return RuleEvaluator._fallback_eval(expr, eval_context)

    @staticmethod
    def _fallback_eval(expr: str, eval_context: Dict[str, Any]) -> bool:
        """Simple fallback string comparison logic."""
        if "CONTAINS" in expr:
            # e.g., "context.patient_allergies CONTAINS 'Penicillin'"
            parts = expr.split("CONTAINS")
            key_path = parts[0].strip()
            val = parts[1].strip().strip("'\"")
            container_val = RuleEvaluator._get_value_by_path(eval_context, key_path)
            if container_val is None:
                return False
            if isinstance(container_val, (list, set, tuple)):
                return val in container_val
            if isinstance(container_val, str):
                return val.lower() in container_val.lower()

        if "EQUALS" in expr:
            parts = expr.split("EQUALS")
            key_path = parts[0].strip()
            val = parts[1].strip().strip("'\"")
            actual_val = RuleEvaluator._get_value_by_path(eval_context, key_path)
            return str(actual_val) == str(val)

        return False

    @staticmethod
    def _context_to_dict(context: InputContext) -> Dict[str, Any]:
        """Convert InputContext snapshot into dict structure."""
        return context.model_dump()

    @staticmethod
    def _has_key_path(d: Dict[str, Any], path: str) -> bool:
        """Check if nested path exists in dictionary."""
        return RuleEvaluator._get_value_by_path(d, path) is not None

    @staticmethod
    def _get_value_by_path(d: Dict[str, Any], path: str) -> Any:
        """Retrieve nested dictionary value using dot notation (e.g. 'patient.allergies')."""
        keys = path.split(".")
        curr = d
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return None
        return curr
