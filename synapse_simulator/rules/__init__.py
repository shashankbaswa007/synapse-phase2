"""
Rule Engine and Rule Repository package for SYNAPSE Phase 2.
Implements the 5-Level Precedence Hierarchy for clinical safety vetoes,
state transitions, cross-departmental effects, and event generation.
"""

from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.models import (
    SynapseRule,
    PrecedenceLevel,
    RuleCategory,
    RuleSourceType,
    RulePreconditions,
    RuleConditions,
    StateTransitionRuleEffect,
    CrossDepartmentRuleEffect,
    TemporalConstraints,
)
from synapse_simulator.rules.evaluator import RuleEvaluator

__all__ = [
    "RuleEngine",
    "RuleRepository",
    "SynapseRule",
    "PrecedenceLevel",
    "RuleCategory",
    "RuleSourceType",
    "RulePreconditions",
    "RuleConditions",
    "StateTransitionRuleEffect",
    "CrossDepartmentRuleEffect",
    "TemporalConstraints",
    "RuleEvaluator",
]

