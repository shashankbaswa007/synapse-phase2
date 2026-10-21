"""
Workflow and Patient Journey Data Models for Stage 7.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JourneyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"


class WorkflowStep(BaseModel):
    """Definition of a single step within a scenario workflow."""
    step_id: str
    name: str
    action_type: str
    target_department: str
    target_entity_table: str
    delay_seconds: int = 0
    next_step_id: Optional[str] = None
    failure_step_id: Optional[str] = None
    conditional_branches: Dict[str, str] = Field(default_factory=dict)  # state_value -> next_step_id
    payload_template: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Complete executable workflow sequence/graph for a scenario."""
    workflow_id: str
    scenario_id: str
    name: str
    description: str
    initial_step_id: str
    steps: Dict[str, WorkflowStep] = Field(default_factory=dict)

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        return self.steps.get(step_id)


class PatientJourney(BaseModel):
    """Active instance tracking one patient's journey through a scenario workflow."""
    journey_id: str
    patient_id: str
    scenario_id: str
    scenario_instance_id: str
    correlation_id: str
    current_step_id: Optional[str] = None
    status: JourneyStatus = JourneyStatus.ACTIVE
    completed_steps: List[str] = Field(default_factory=list)
    entity_references: Dict[str, str] = Field(default_factory=dict)  # entity_type -> entity_id
    start_time: datetime
    end_time: Optional[datetime] = None
    outcome: str = "IN_PROGRESS"
    trace_history: List[Dict[str, Any]] = Field(default_factory=list)
