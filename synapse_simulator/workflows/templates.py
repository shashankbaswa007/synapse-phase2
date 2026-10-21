"""
Scenario Workflow Templates for Core V1 Scenarios (SCEN-V1-01 through SCEN-V1-04).
"""

from typing import Dict
from synapse_simulator.workflows.model import WorkflowDefinition, WorkflowStep


def get_all_scenario_workflows() -> Dict[str, WorkflowDefinition]:
    """Build and return executable workflow definitions for Stage 0 scenarios."""
    workflows: Dict[str, WorkflowDefinition] = {}

    # --------------------------------------------------------------------------
    # SCEN-V1-01: Routine Outpatient Journey Workflow
    # --------------------------------------------------------------------------
    scen_01_steps = {
        "step_consult": WorkflowStep(
            step_id="step_consult",
            name="Doctor Consultation",
            action_type="START_DOCTOR_CONSULTATION",
            target_department="clinical",
            target_entity_table="clinical.appointments",
            delay_seconds=0,
            next_step_id="step_verify",
        ),
        "step_verify": WorkflowStep(
            step_id="step_verify",
            name="Prescription Verification",
            action_type="VERIFY_PRESCRIPTION",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            delay_seconds=300,
            next_step_id="step_dispense",
        ),
        "step_dispense": WorkflowStep(
            step_id="step_dispense",
            name="Medicine Dispense",
            action_type="CONFIRM_MEDICINE_DISPENSE",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            delay_seconds=300,
            next_step_id="step_invoice",
        ),
        "step_invoice": WorkflowStep(
            step_id="step_invoice",
            name="Invoice Generation",
            action_type="GENERATE_INVOICE",
            target_department="finance",
            target_entity_table="finance.invoices",
            delay_seconds=300,
            next_step_id=None,
        ),
    }

    workflows["SCEN-V1-01"] = WorkflowDefinition(
        workflow_id="wdef-scen-v1-01",
        scenario_id="SCEN-V1-01",
        name="Routine Outpatient Journey Workflow",
        description="Outpatient consult, prescription verification, medicine dispense, and billing.",
        initial_step_id="step_consult",
        steps=scen_01_steps,
    )

    # --------------------------------------------------------------------------
    # SCEN-V1-02: Diagnostic Investigation Workflow
    # --------------------------------------------------------------------------
    scen_02_steps = {
        "step_consult_initial": WorkflowStep(
            step_id="step_consult_initial",
            name="Initial Doctor Consultation",
            action_type="START_DOCTOR_CONSULTATION",
            target_department="clinical",
            target_entity_table="clinical.appointments",
            delay_seconds=0,
            next_step_id="step_lab_order",
        ),
        "step_lab_order": WorkflowStep(
            step_id="step_lab_order",
            name="Lab Sample Collection",
            action_type="COLLECT_LAB_SAMPLE",
            target_department="laboratory",
            target_entity_table="laboratory.laboratory_orders",
            delay_seconds=600,
            next_step_id="step_rad_order",
        ),
        "step_rad_order": WorkflowStep(
            step_id="step_rad_order",
            name="Radiology Image Acquisition",
            action_type="ACQUIRE_RADIOLOGY_IMAGE",
            target_department="radiology",
            target_entity_table="radiology.radiology_orders",
            delay_seconds=600,
            next_step_id="step_invoice",
        ),
        "step_invoice": WorkflowStep(
            step_id="step_invoice",
            name="Invoice Generation",
            action_type="GENERATE_INVOICE",
            target_department="finance",
            target_entity_table="finance.invoices",
            delay_seconds=300,
            next_step_id=None,
        ),
    }

    workflows["SCEN-V1-02"] = WorkflowDefinition(
        workflow_id="wdef-scen-v1-02",
        scenario_id="SCEN-V1-02",
        name="Outpatient Diagnostic Investigation Workflow",
        description="OPD Consult leading to lab sample collection and radiology imaging.",
        initial_step_id="step_consult_initial",
        steps=scen_02_steps,
    )

    # --------------------------------------------------------------------------
    # SCEN-V1-03: Drug Allergy Safety Hold & Alert Workflow
    # --------------------------------------------------------------------------
    scen_03_steps = {
        "step_consult": WorkflowStep(
            step_id="step_consult",
            name="Doctor Consultation",
            action_type="START_DOCTOR_CONSULTATION",
            target_department="clinical",
            target_entity_table="clinical.appointments",
            delay_seconds=0,
            next_step_id="step_verify_allergy",
        ),
        "step_verify_allergy": WorkflowStep(
            step_id="step_verify_allergy",
            name="Prescription Allergy Verification",
            action_type="VERIFY_PRESCRIPTION",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            delay_seconds=300,
            next_step_id="step_dispense",
            failure_step_id="step_alert_notice",
            payload_template={"drug_class": "Beta-Lactam"},
        ),
        "step_dispense": WorkflowStep(
            step_id="step_dispense",
            name="Medicine Dispense",
            action_type="CONFIRM_MEDICINE_DISPENSE",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            delay_seconds=300,
            next_step_id="step_invoice",
        ),
        "step_alert_notice": WorkflowStep(
            step_id="step_alert_notice",
            name="Drug-Allergy Safety Alert Notice",
            action_type="CREATE_CLINICAL_ALERT",
            target_department="clinical",
            target_entity_table="clinical.encounters",
            delay_seconds=120,
            next_step_id="step_invoice",
        ),
        "step_invoice": WorkflowStep(
            step_id="step_invoice",
            name="Invoice Generation",
            action_type="GENERATE_INVOICE",
            target_department="finance",
            target_entity_table="finance.invoices",
            delay_seconds=300,
            next_step_id=None,
        ),
    }

    workflows["SCEN-V1-03"] = WorkflowDefinition(
        workflow_id="wdef-scen-v1-03",
        scenario_id="SCEN-V1-03",
        name="Drug Allergy Safety Hold Workflow",
        description="Prescription verification triggers Penicillin safety hold and alert notice.",
        initial_step_id="step_consult",
        steps=scen_03_steps,
    )

    # --------------------------------------------------------------------------
    # SCEN-V1-04: Inventory Stock Depletion & Shortage Workflow
    # --------------------------------------------------------------------------
    scen_04_steps = {
        "step_consult": WorkflowStep(
            step_id="step_consult",
            name="Doctor Consultation",
            action_type="START_DOCTOR_CONSULTATION",
            target_department="clinical",
            target_entity_table="clinical.appointments",
            delay_seconds=0,
            next_step_id="step_verify",
        ),
        "step_verify": WorkflowStep(
            step_id="step_verify",
            name="Prescription Verification",
            action_type="VERIFY_PRESCRIPTION",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            delay_seconds=300,
            next_step_id="step_dispense_stock",
        ),
        "step_dispense_stock": WorkflowStep(
            step_id="step_dispense_stock",
            name="Medicine Dispense Check",
            action_type="CONFIRM_MEDICINE_DISPENSE",
            target_department="pharmacy",
            target_entity_table="pharmacy.prescriptions",
            delay_seconds=300,
            next_step_id="step_invoice",
            failure_step_id="step_backorder",
            payload_template={"requested_quantity": 10},
        ),
        "step_invoice": WorkflowStep(
            step_id="step_invoice",
            name="Invoice Generation",
            action_type="GENERATE_INVOICE",
            target_department="finance",
            target_entity_table="finance.invoices",
            delay_seconds=300,
            next_step_id=None,
        ),
        "step_backorder": WorkflowStep(
            step_id="step_backorder",
            name="Inventory Backorder Notice",
            action_type="CREATE_CLINICAL_ALERT",
            target_department="clinical",
            target_entity_table="clinical.encounters",
            delay_seconds=120,
            next_step_id="step_invoice",
        ),
    }

    workflows["SCEN-V1-04"] = WorkflowDefinition(
        workflow_id="wdef-scen-v1-04",
        scenario_id="SCEN-V1-04",
        name="Inventory Depletion & Shortage Workflow",
        description="Medication dispense request exceeds stock, triggering RULE-GLOB-STOCK-001 block.",
        initial_step_id="step_consult",
        steps=scen_04_steps,
    )

    return workflows
