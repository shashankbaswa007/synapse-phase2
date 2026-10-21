"""
Clinical Module Framework Pydantic Data Models.
Defines 7 Control States, 11 Clinical States, and 4 Transition Types
aligned with the Synthea Generic Module Framework.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, model_validator


class ControlType(str, Enum):
    INITIAL = "Initial"
    TERMINAL = "Terminal"
    SIMPLE = "Simple"
    GUARD = "Guard"
    DELAY = "Delay"
    SET_ATTRIBUTE = "SetAttribute"
    COUNTER = "Counter"


class ClinicalType(str, Enum):
    ENCOUNTER = "Encounter"
    CONDITION_ONSET = "ConditionOnset"
    CONDITION_END = "ConditionEnd"
    MEDICATION_ORDER = "MedicationOrder"
    MEDICATION_END = "MedicationEnd"
    CARE_PLAN_START = "CarePlanStart"
    CARE_PLAN_END = "CarePlanEnd"
    PROCEDURE = "Procedure"
    OBSERVATION = "Observation"
    SYMPTOM = "Symptom"
    DEATH = "Death"


class TransitionType(str, Enum):
    DIRECT = "Direct"
    DISTRIBUTED = "Distributed"
    CONDITIONAL = "Conditional"
    COMPLEX = "Complex"


class DistributedTarget(BaseModel):
    to: str
    weight: float
    provenance_id: Optional[str] = None


class ConditionalTarget(BaseModel):
    to: str
    condition: str


class ComplexTarget(BaseModel):
    condition: str
    distributions: List[DistributedTarget]


class TransitionDefinition(BaseModel):
    """Encapsulates any of the 4 transition types."""
    direct: Optional[str] = None
    distributed: Optional[List[DistributedTarget]] = None
    conditional: Optional[List[ConditionalTarget]] = None
    complex_trans: Optional[List[ComplexTarget]] = None
    default_to: Optional[str] = None

    @model_validator(mode="after")
    def validate_single_transition_type(self) -> "TransitionDefinition":
        count = sum([
            1 if self.direct is not None else 0,
            1 if self.distributed is not None else 0,
            1 if self.conditional is not None else 0,
            1 if self.complex_trans is not None else 0,
        ])
        if count > 1:
            raise ValueError("State can define only one transition type (direct, distributed, conditional, or complex)")
        return self


class ModuleState(BaseModel):
    """Generic State representation capable of representing any of the 7 control or 11 clinical states."""
    name: str
    type: str  # Can match ControlType or ClinicalType
    description: Optional[str] = ""

    # Transitions
    direct_transition: Optional[str] = None
    distributed_transition: Optional[List[DistributedTarget]] = None
    conditional_transition: Optional[List[ConditionalTarget]] = None
    complex_transition: Optional[List[ComplexTarget]] = None
    default_transition: Optional[str] = None

    # Control State attributes
    guard_condition: Optional[str] = None
    delay_days: Optional[float] = None
    attribute_name: Optional[str] = None
    attribute_value: Optional[Any] = None
    counter_attribute: Optional[str] = None
    counter_action: Optional[str] = "increment"  # increment or decrement

    # Clinical State attributes
    encounter_type: Optional[str] = "outpatient"  # outpatient, inpatient, emergency
    encounter_reason: Optional[str] = None

    condition_code: Optional[str] = None
    condition_name: Optional[str] = None

    drug_code: Optional[str] = None
    drug_name: Optional[str] = None
    drug_class: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None

    plan_code: Optional[str] = None
    plan_name: Optional[str] = None

    procedure_code: Optional[str] = None
    procedure_name: Optional[str] = None

    observation_code: Optional[str] = None
    observation_name: Optional[str] = None
    observation_unit: Optional[str] = None
    observation_value: Optional[float] = None
    observation_min: Optional[float] = None
    observation_max: Optional[float] = None

    # Paired / Component Observation (e.g. Diastolic BP paired with Systolic BP)
    paired_observation_code: Optional[str] = None
    paired_observation_name: Optional[str] = None
    paired_observation_unit: Optional[str] = None
    paired_observation_value: Optional[float] = None
    paired_observation_min: Optional[float] = None
    paired_observation_max: Optional[float] = None

    symptom_name: Optional[str] = None
    symptom_severity: Optional[float] = 0.5  # 0.0 to 1.0

    death_cause_code: Optional[str] = None
    death_cause_name: Optional[str] = None


class ClinicalModule(BaseModel):
    """Declarative clinical pathway module."""
    id: str
    name: str
    version: str = "1.0.0"
    target_condition: Optional[str] = None
    description: str = ""
    provenance_ids: List[str] = Field(default_factory=list)
    initial_state: str = "Initial"
    states: Dict[str, ModuleState]

    @model_validator(mode="after")
    def validate_state_graph(self) -> "ClinicalModule":
        if self.initial_state not in self.states:
            raise ValueError(f"Module '{self.id}': initial_state '{self.initial_state}' does not exist in states")

        all_names = set(self.states.keys())
        for name, state in self.states.items():
            if state.direct_transition and state.direct_transition not in all_names:
                raise ValueError(f"State '{name}' has target '{state.direct_transition}' not in module states")
            if state.distributed_transition:
                for dt in state.distributed_transition:
                    if dt.to not in all_names:
                        raise ValueError(f"State '{name}' distributed target '{dt.to}' not in module states")
            if state.conditional_transition:
                for ct in state.conditional_transition:
                    if ct.to not in all_names:
                        raise ValueError(f"State '{name}' conditional target '{ct.to}' not in module states")
            if state.default_transition and state.default_transition not in all_names:
                raise ValueError(f"State '{name}' default target '{state.default_transition}' not in module states")
        return self
