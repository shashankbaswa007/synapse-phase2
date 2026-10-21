"""
Clinical Module Condition Evaluator.
Evaluates boolean expressions in Guard states and Conditional transitions
against patient attributes and medical history records.
"""

from typing import Dict, Any, Optional
from simpleeval import SimpleEval
from synapse_simulator.datagen.models import PatientContext


class ModuleConditionEvaluator:
    """Safe evaluation of module conditional expressions."""

    def __init__(self, patient: PatientContext, record_history: Optional[Dict[str, Any]] = None):
        self.patient = patient
        self.record = record_history or {}

        # Setup SimpleEval
        self.evaluator = SimpleEval()

        # Built-in helper functions
        self.evaluator.functions = {
            "has_condition": self._has_condition,
            "has_symptom": self._has_symptom,
            "latest_observation": self._latest_observation,
            "attribute": self._get_attribute,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
        }

        # Names available in expressions
        self.evaluator.names = {
            "age": patient.age,
            "gender": patient.gender,
            "patient_id": patient.patient_id,
            "is_alive": patient.is_alive,
            "attributes": patient.attributes,
        }

    def _has_condition(self, code_or_name: str) -> bool:
        """Check if patient has condition in chronic_conditions or latent_conditions."""
        # 1. Check patient chronic conditions
        if code_or_name in self.patient.chronic_conditions:
            return True
        # 2. Check latent / active conditions
        if code_or_name in self.patient.latent_conditions:
            return True
        for cond_dict in self.patient.latent_conditions.values():
            if isinstance(cond_dict, dict) and (cond_dict.get("code") == code_or_name or cond_dict.get("name") == code_or_name):
                return True
        # 3. Check record history
        diagnosed = self.record.get("diagnosed_conditions", [])
        if code_or_name in diagnosed:
            return True
        return False

    def _has_symptom(self, symptom_name: str) -> bool:
        symptoms = self.record.get("symptoms", [])
        return symptom_name in symptoms

    def _latest_observation(self, observation_code: str) -> Optional[float]:
        obs_map = self.record.get("observations", {})
        return obs_map.get(observation_code)

    def _get_attribute(self, key: str, default: Any = None) -> Any:
        return self.patient.attributes.get(key, default)

    def evaluate(self, expression: str) -> bool:
        """Evaluate a boolean expression safely."""
        if not expression or not expression.strip():
            return True

        expr = expression.strip()

        # Custom simple conversions if needed
        # Support CONTAINS keyword if present
        if " CONTAINS " in expr:
            parts = expr.split(" CONTAINS ")
            left_val = self.evaluator.eval(parts[0].strip())
            right_val = parts[1].strip().strip("'\"")
            if isinstance(left_val, (list, tuple, set, str)):
                return right_val in left_val
            return False

        if " EQUALS " in expr:
            parts = expr.split(" EQUALS ")
            left_val = self.evaluator.eval(parts[0].strip())
            right_val = parts[1].strip().strip("'\"")
            return str(left_val) == right_val

        try:
            result = self.evaluator.eval(expr)
            return bool(result)
        except Exception:
            # Fallback simple evaluation for standard comparisons
            return False
