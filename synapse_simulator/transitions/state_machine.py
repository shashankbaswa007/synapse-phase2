"""
State Machine definitions for the 9 Core V1 entities.
"""

from typing import Dict, Set, Tuple, Optional
from synapse_simulator.state.models import (
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


class BaseStateMachine:
    """Base State Machine providing structural transition validation."""
    entity_name: str = "BaseEntity"
    valid_transitions: Dict[str, Set[str]] = {}
    initial_state: str = ""
    terminal_states: Set[str] = set()

    @classmethod
    def is_valid_transition(cls, current_state: str, next_state: str) -> bool:
        if current_state == next_state:
            return True
        allowed = cls.valid_transitions.get(current_state, set())
        return next_state in allowed

    @classmethod
    def is_terminal(cls, state: str) -> bool:
        return state in cls.terminal_states


class PatientStateMachine(BaseStateMachine):
    entity_name = "patient.patients"
    initial_state = PatientStatus.REGISTERED.value
    terminal_states = {PatientStatus.ARCHIVED.value}
    valid_transitions = {
        PatientStatus.REGISTERED.value: {PatientStatus.ACTIVE.value, PatientStatus.ARCHIVED.value},
        PatientStatus.ACTIVE.value: {PatientStatus.ARCHIVED.value},
        PatientStatus.ARCHIVED.value: set(),
    }


class AppointmentStateMachine(BaseStateMachine):
    entity_name = "clinical.appointments"
    initial_state = AppointmentStatus.SCHEDULED.value
    terminal_states = {AppointmentStatus.COMPLETED.value, AppointmentStatus.CANCELLED.value, AppointmentStatus.NO_SHOW.value}
    valid_transitions = {
        AppointmentStatus.SCHEDULED.value: {
            AppointmentStatus.CHECKED_IN.value,
            AppointmentStatus.CANCELLED.value,
            AppointmentStatus.NO_SHOW.value,
        },
        AppointmentStatus.CHECKED_IN.value: {
            AppointmentStatus.IN_CONSULT.value,
            AppointmentStatus.CANCELLED.value,
        },
        AppointmentStatus.IN_CONSULT.value: {
            AppointmentStatus.COMPLETED.value,
        },
        AppointmentStatus.COMPLETED.value: set(),
        AppointmentStatus.CANCELLED.value: set(),
        AppointmentStatus.NO_SHOW.value: set(),
    }


class EncounterStateMachine(BaseStateMachine):
    entity_name = "clinical.encounters"
    initial_state = EncounterStatus.ACTIVE.value
    terminal_states = {EncounterStatus.CLOSED.value}
    valid_transitions = {
        EncounterStatus.ACTIVE.value: {EncounterStatus.CLOSED.value},
        EncounterStatus.CLOSED.value: set(),
    }


class ConsultationStateMachine(BaseStateMachine):
    entity_name = "clinical.consultations"
    initial_state = ConsultationStatus.IN_PROGRESS.value
    terminal_states = {ConsultationStatus.COMPLETED.value}
    valid_transitions = {
        ConsultationStatus.IN_PROGRESS.value: {
            ConsultationStatus.PENDING_RESULTS.value,
            ConsultationStatus.COMPLETED.value,
        },
        ConsultationStatus.PENDING_RESULTS.value: {
            ConsultationStatus.COMPLETED.value,
        },
        ConsultationStatus.COMPLETED.value: set(),
    }


class LabOrderStateMachine(BaseStateMachine):
    entity_name = "laboratory.laboratory_orders"
    initial_state = LabOrderStatus.ORDERED.value
    terminal_states = {LabOrderStatus.COMPLETED.value, LabOrderStatus.REJECTED.value}
    valid_transitions = {
        LabOrderStatus.ORDERED.value: {
            LabOrderStatus.SAMPLE_COLLECTED.value,
            LabOrderStatus.REJECTED.value,
        },
        LabOrderStatus.SAMPLE_COLLECTED.value: {
            LabOrderStatus.COMPLETED.value,
            LabOrderStatus.REJECTED.value,
        },
        LabOrderStatus.COMPLETED.value: set(),
        LabOrderStatus.REJECTED.value: set(),
    }


class RadOrderStateMachine(BaseStateMachine):
    entity_name = "radiology.radiology_orders"
    initial_state = RadOrderStatus.ORDERED.value
    terminal_states = {RadOrderStatus.REPORTED.value}
    valid_transitions = {
        RadOrderStatus.ORDERED.value: {RadOrderStatus.IMAGE_ACQUIRED.value},
        RadOrderStatus.IMAGE_ACQUIRED.value: {RadOrderStatus.REPORTED.value},
        RadOrderStatus.REPORTED.value: set(),
    }


class PrescriptionStateMachine(BaseStateMachine):
    entity_name = "pharmacy.prescriptions"
    initial_state = PrescriptionStatus.ISSUED.value
    terminal_states = {PrescriptionStatus.COMPLETED.value, PrescriptionStatus.CANCELLED_REPLACED.value}
    valid_transitions = {
        PrescriptionStatus.ISSUED.value: {
            PrescriptionStatus.VERIFICATION_PASSED.value,
            PrescriptionStatus.BLOCKED_SAFETY_HOLD.value,
            PrescriptionStatus.CANCELLED_REPLACED.value,
        },
        PrescriptionStatus.VERIFICATION_PASSED.value: {
            PrescriptionStatus.DISPENSED.value,
            PrescriptionStatus.PARTIALLY_DISPENSED.value,
            PrescriptionStatus.BLOCKED_SAFETY_HOLD.value,
        },
        PrescriptionStatus.BLOCKED_SAFETY_HOLD.value: {
            PrescriptionStatus.CANCELLED_REPLACED.value,
            PrescriptionStatus.VERIFICATION_PASSED.value,
        },
        PrescriptionStatus.DISPENSED.value: {
            PrescriptionStatus.COMPLETED.value,
        },
        PrescriptionStatus.PARTIALLY_DISPENSED.value: {
            PrescriptionStatus.DISPENSED.value,
            PrescriptionStatus.COMPLETED.value,
        },
        PrescriptionStatus.CANCELLED_REPLACED.value: set(),
        PrescriptionStatus.COMPLETED.value: set(),
    }


class InventoryBatchStateMachine(BaseStateMachine):
    entity_name = "pharmacy.inventory_batches"
    initial_state = InventoryBatchStatus.ACTIVE.value
    terminal_states = {InventoryBatchStatus.DEPLETED.value, InventoryBatchStatus.EXPIRED.value}
    valid_transitions = {
        InventoryBatchStatus.ACTIVE.value: {
            InventoryBatchStatus.LOW_STOCK.value,
            InventoryBatchStatus.DEPLETED.value,
            InventoryBatchStatus.EXPIRED.value,
        },
        InventoryBatchStatus.LOW_STOCK.value: {
            InventoryBatchStatus.DEPLETED.value,
            InventoryBatchStatus.EXPIRED.value,
        },
        InventoryBatchStatus.DEPLETED.value: set(),
        InventoryBatchStatus.EXPIRED.value: set(),
    }


class InvoiceStateMachine(BaseStateMachine):
    entity_name = "finance.invoices"
    initial_state = InvoiceStatus.DRAFT.value
    terminal_states = {InvoiceStatus.PAID.value, InvoiceStatus.CANCELLED.value}
    valid_transitions = {
        InvoiceStatus.DRAFT.value: {
            InvoiceStatus.UNPAID.value,
            InvoiceStatus.CANCELLED.value,
        },
        InvoiceStatus.UNPAID.value: {
            InvoiceStatus.PAID.value,
            InvoiceStatus.PARTIALLY_PAID.value,
            InvoiceStatus.CANCELLED.value,
        },
        InvoiceStatus.PARTIALLY_PAID.value: {
            InvoiceStatus.PAID.value,
            InvoiceStatus.CANCELLED.value,
        },
        InvoiceStatus.PAID.value: set(),
        InvoiceStatus.CANCELLED.value: set(),
    }


# Map of entity table names to state machine classes
ENTITY_STATE_MACHINES: Dict[str, type] = {
    "patient.patients": PatientStateMachine,
    "clinical.appointments": AppointmentStateMachine,
    "clinical.encounters": EncounterStateMachine,
    "clinical.consultations": ConsultationStateMachine,
    "laboratory.laboratory_orders": LabOrderStateMachine,
    "radiology.radiology_orders": RadOrderStateMachine,
    "pharmacy.prescriptions": PrescriptionStateMachine,
    "pharmacy.inventory_batches": InventoryBatchStateMachine,
    "finance.invoices": InvoiceStateMachine,
}
