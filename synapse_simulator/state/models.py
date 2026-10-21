"""
State data models, context payloads, status Enums, and proposal schemas.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Entity Status Enums (9 Core V1 Entities)
# --------------------------------------------------------------------------

class PatientStatus(str, Enum):
    REGISTERED = "Registered"
    ACTIVE = "Active"
    ARCHIVED = "Archived"
    DECEASED = "Deceased"


class AppointmentStatus(str, Enum):
    SCHEDULED = "Scheduled"
    CHECKED_IN = "Checked-In"
    IN_CONSULT = "In-Consult"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No-Show"


class EncounterStatus(str, Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"


class ConsultationStatus(str, Enum):
    IN_PROGRESS = "In-Progress"
    PENDING_RESULTS = "Pending-Results"
    COMPLETED = "Completed"


class LabOrderStatus(str, Enum):
    ORDERED = "Ordered"
    SAMPLE_COLLECTED = "Sample-Collected"
    COMPLETED = "Completed"
    REJECTED = "Rejected"


class RadOrderStatus(str, Enum):
    ORDERED = "Ordered"
    IMAGE_ACQUIRED = "Image-Acquired"
    REPORTED = "Reported"


class PrescriptionStatus(str, Enum):
    ISSUED = "Issued"
    VERIFICATION_PASSED = "Verification_Passed"
    DISPENSED = "Dispensed"
    BLOCKED_SAFETY_HOLD = "Blocked_Safety_Hold"
    CANCELLED_REPLACED = "Cancelled_Replaced"
    PARTIALLY_DISPENSED = "Partially_Dispensed"
    COMPLETED = "Completed"


class InventoryBatchStatus(str, Enum):
    ACTIVE = "Active"
    LOW_STOCK = "Low_Stock"
    DEPLETED = "Depleted"
    EXPIRED = "Expired"


class InvoiceStatus(str, Enum):
    DRAFT = "Draft"
    UNPAID = "Unpaid"
    PAID = "Paid"
    PARTIALLY_PAID = "Partially_Paid"
    CANCELLED = "Cancelled"


# --------------------------------------------------------------------------
# Action Request & Lineage Tracking Models
# --------------------------------------------------------------------------

class ActionRequest(BaseModel):
    action_id: str
    action_type: str
    target_department: str
    target_entity_table: str
    target_entity_id: str
    scenario_instance_id: str
    patient_journey_id: str
    correlation_id: str
    causation_id: Optional[str] = None
    requested_timestamp: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)
    extra_context: Dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------
# Engine Decision Proposal Schemas
# --------------------------------------------------------------------------

class StateTransitionProposal(BaseModel):
    target_entity_table: str
    target_entity_id: str
    field_name: str = "status"
    current_value: str
    new_value: str
    additional_updates: Dict[str, Any] = Field(default_factory=dict)


class CommandProposal(BaseModel):
    target_department: str
    command_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class OutboxEventProposal(BaseModel):
    event_type: str
    source_domain: str
    entity_reference: Dict[str, Any]
    scenario_instance_id: str
    patient_journey_id: str
    correlation_id: str
    causation_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class DocumentTriggerProposal(BaseModel):
    document_type: str
    encounter_id: str
    patient_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------
# Input Context & Decision Result
# --------------------------------------------------------------------------

class InputContext(BaseModel):
    simulated_timestamp: datetime
    scenario_id: str
    scenario_instance_id: str
    patient_journey_id: str
    correlation_id: str
    department_id: str
    proposed_action: ActionRequest
    patient_state: Dict[str, Any] = Field(default_factory=dict)
    entity_state: Dict[str, Any] = Field(default_factory=dict)
    resource_state: Dict[str, Any] = Field(default_factory=dict)
    extra_context: Dict[str, Any] = Field(default_factory=dict)


class DecisionStatus(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    REDIRECTED = "REDIRECTED"


class DecisionResult(BaseModel):
    status: DecisionStatus
    winning_rule_id: Optional[str] = None
    winning_rule_priority: int = 0
    reason: str
    permitted_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)
    state_transitions: List[StateTransitionProposal] = Field(default_factory=list)
    cross_department_effects: List[CommandProposal] = Field(default_factory=list)
    events_to_emit: List[OutboxEventProposal] = Field(default_factory=list)
    documents_to_trigger: List[DocumentTriggerProposal] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Formal Stage 6 Domain Event Model
# --------------------------------------------------------------------------

class DomainEvent(BaseModel):
    """Immutable domain event representing an actual state-changing fact (or explicit failure)."""
    event_id: str
    event_type: str
    event_version: str = "1.0.0"
    timestamp: datetime
    producer_domain: str
    entity_table: str
    entity_id: str
    scenario_instance_id: str
    patient_journey_id: str
    correlation_id: str
    causation_id: Optional[str] = None
    causation_depth: int = 0
    sequence_number: int = 0
    status: str = "COMMITTED"  # COMMITTED or BLOCKED_FAILURE
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

