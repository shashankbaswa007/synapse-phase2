"""
State models and state manager module.

Provides thread-safe state store, state reader/writer interfaces, context builders,
and domain models for simulated entities, events, decisions, and transactions.
"""

from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.state.interfaces import (
    IStateReader,
    IStateWriter,
    IContextBuilder,
    IStateDecisionApplier,
)
from synapse_simulator.state.models import (
    InputContext,
    DecisionResult,
    DecisionStatus,
    DomainEvent,
    ActionRequest,
    StateTransitionProposal,
    CommandProposal,
    OutboxEventProposal,
    DocumentTriggerProposal,
    PatientStatus,
    AppointmentStatus,
    EncounterStatus,
    ConsultationStatus,
    LabOrderStatus,
    RadOrderStatus,
    PrescriptionStatus,
    InventoryBatchStatus,
    InvoiceStatus,
)

__all__ = [
    "StateManager",
    "IStateReader",
    "IStateWriter",
    "IContextBuilder",
    "IStateDecisionApplier",
    "InputContext",
    "DecisionResult",
    "DecisionStatus",
    "DomainEvent",
    "ActionRequest",
    "StateTransitionProposal",
    "CommandProposal",
    "OutboxEventProposal",
    "DocumentTriggerProposal",
    "PatientStatus",
    "AppointmentStatus",
    "EncounterStatus",
    "ConsultationStatus",
    "LabOrderStatus",
    "RadOrderStatus",
    "PrescriptionStatus",
    "InventoryBatchStatus",
    "InvoiceStatus",
]


