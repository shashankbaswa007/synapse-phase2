"""
Unit tests for 9 Core Entity State Machines and TransitionManager.
"""

import pytest
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
from synapse_simulator.transitions.state_machine import (
    PatientStateMachine,
    AppointmentStateMachine,
    PrescriptionStateMachine,
    InvoiceStateMachine,
)
from synapse_simulator.transitions.transition_manager import TransitionManager


def test_patient_state_machine_valid():
    assert PatientStateMachine.is_valid_transition("Registered", "Active")
    assert PatientStateMachine.is_valid_transition("Active", "Archived")
    assert PatientStateMachine.is_valid_transition("Active", "Active")


def test_patient_state_machine_invalid():
    assert not PatientStateMachine.is_valid_transition("Archived", "Active")


def test_appointment_state_machine_valid():
    assert AppointmentStateMachine.is_valid_transition("Scheduled", "Checked-In")
    assert AppointmentStateMachine.is_valid_transition("Checked-In", "In-Consult")
    assert AppointmentStateMachine.is_valid_transition("In-Consult", "Completed")
    assert AppointmentStateMachine.is_valid_transition("Scheduled", "Cancelled")


def test_appointment_state_machine_invalid():
    assert not AppointmentStateMachine.is_valid_transition("Scheduled", "Completed")
    assert not AppointmentStateMachine.is_valid_transition("Completed", "Scheduled")


def test_prescription_state_machine_valid():
    assert PrescriptionStateMachine.is_valid_transition("Issued", "Verification_Passed")
    assert PrescriptionStateMachine.is_valid_transition("Issued", "Blocked_Safety_Hold")
    assert PrescriptionStateMachine.is_valid_transition("Blocked_Safety_Hold", "Cancelled_Replaced")
    assert PrescriptionStateMachine.is_valid_transition("Verification_Passed", "Dispensed")
    assert PrescriptionStateMachine.is_valid_transition("Verification_Passed", "Partially_Dispensed")


def test_prescription_state_machine_invalid():
    assert not PrescriptionStateMachine.is_valid_transition("Issued", "Dispensed")
    assert not PrescriptionStateMachine.is_valid_transition("Completed", "Issued")


def test_transition_manager_validation():
    # Valid transition
    is_valid, err = TransitionManager.validate_transition("pharmacy.prescriptions", "Issued", "Verification_Passed")
    assert is_valid
    assert err is None

    # Invalid transition
    is_valid, err = TransitionManager.validate_transition("pharmacy.prescriptions", "Issued", "Completed")
    assert not is_valid
    assert "Cannot transition from 'Issued' to 'Completed'" in err

    # Non-tracked entity should pass
    is_valid, err = TransitionManager.validate_transition("unknown_table", "A", "B")
    assert is_valid
