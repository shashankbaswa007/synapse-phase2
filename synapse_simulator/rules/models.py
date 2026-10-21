"""
Pydantic schema definition for Synapse Rules.
"""

from enum import Enum, IntEnum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PrecedenceLevel(IntEnum):
    LEVEL_1_SYSTEM_INTEGRITY = 100   # Highest: FKs, non-negative stock, temporal ordering
    LEVEL_2_CLINICAL_SAFETY = 80     # Hard clinical holds, allergy contraindications
    LEVEL_3_DEPARTMENT_WORKFLOW = 60 # Required stage sequence, valid status change
    LEVEL_4_SCENARIO_SPEC = 40       # Scenario-specific overrides & triggers
    LEVEL_5_SIMULATION_HEURISTIC = 20# Lowest: Probabilities, arrival rates, delays


class RuleSourceType(str, Enum):
    INTERNAL_DESIGN = "INTERNAL_DESIGN"
    EXTERNAL_DOMAIN = "EXTERNAL_DOMAIN"
    SIMULATION_HEURISTIC = "SIMULATION_HEURISTIC"


class RuleCategory(str, Enum):
    CLINICAL_SAFETY = "CLINICAL_SAFETY"
    WORKFLOW_SEQUENCE = "WORKFLOW_SEQUENCE"
    STATE_TRANSITION = "STATE_TRANSITION"
    CROSS_DEPARTMENT = "CROSS_DEPARTMENT"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    TEMPORAL_CONSTRAINT = "TEMPORAL_CONSTRAINT"
    RESOURCE_AVAILABILITY = "RESOURCE_AVAILABILITY"
    SIMULATION_PROBABILITY = "SIMULATION_PROBABILITY"


class RulePreconditions(BaseModel):
    action_type: Optional[str] = None
    required_context_keys: List[str] = Field(default_factory=list)


class RuleConditions(BaseModel):
    all_of: List[str] = Field(default_factory=list)
    any_of: List[str] = Field(default_factory=list)
    none_of: List[str] = Field(default_factory=list)


class StateTransitionRuleEffect(BaseModel):
    target_entity: str
    target_field: str = "status"
    new_value: str
    additional_updates: Dict[str, Any] = Field(default_factory=dict)


class CrossDepartmentRuleEffect(BaseModel):
    target_department: str
    effect_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class TemporalConstraints(BaseModel):
    min_delay_seconds: int = 0
    max_delay_seconds: Optional[int] = None
    must_occur_after_action: Optional[str] = None


class SynapseRule(BaseModel):
    rule_id: str
    name: str
    category: RuleCategory
    description: str
    source_type: RuleSourceType
    source_reference: Optional[str] = None
    priority: int = 50
    precedence_level: PrecedenceLevel = PrecedenceLevel.LEVEL_3_DEPARTMENT_WORKFLOW
    version: str = "1.0.0"
    scenarios: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    entities_affected: List[str] = Field(default_factory=list)
    preconditions: RulePreconditions = Field(default_factory=RulePreconditions)
    conditions: RuleConditions = Field(default_factory=RuleConditions)
    allowed_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)
    state_transitions: List[StateTransitionRuleEffect] = Field(default_factory=list)
    cross_department_effects: List[CrossDepartmentRuleEffect] = Field(default_factory=list)
    events_generated: List[str] = Field(default_factory=list)
    documents_triggered: List[str] = Field(default_factory=list)
    temporal_constraints: Optional[TemporalConstraints] = None
