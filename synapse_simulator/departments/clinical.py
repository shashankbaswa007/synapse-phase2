"""
Clinical Department Handler.
"""

import uuid
from typing import List
from synapse_simulator.departments.base import BaseDepartmentHandler
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest


class ClinicalDepartmentHandler(BaseDepartmentHandler):
    department_name = "clinical"

    def __init__(self, clinical_gen=None, patient_contexts=None, state_manager=None):
        self.clinical_gen = clinical_gen
        self.patient_contexts = patient_contexts or {}
        self.state_manager = state_manager

    def handle_event(self, event: SimulationEvent) -> List[ActionRequest]:
        actions: List[ActionRequest] = []

        if event.event_type == "PatientArrived":
            payload = dict(event.payload)
            patient_id = payload.get("patient_id")
            context = self.patient_contexts.get(patient_id)

            if self.clinical_gen and context and self.state_manager:
                if context.diagnosis_code:
                    diagnosis = self.clinical_gen.kb.get_diagnosis_by_code(context.diagnosis_code) or self.clinical_gen.select_diagnosis(context)
                else:
                    diagnosis = self.clinical_gen.select_diagnosis(context)
                    context.diagnosis_code = diagnosis.code
                    context.diagnosis_name = diagnosis.name

                vitals = self.clinical_gen.generate_vitals(context, diagnosis)
                
                force_conflict = getattr(context, "force_conflict", False) or (context.scenario_id == "SCEN-V1-03")
                treatment, is_conflict = self.clinical_gen.select_medication(context, diagnosis, force_conflict=force_conflict)

                apt_id = payload.get("appointment_id", "apt-001")
                consult_id = f"cons-{apt_id[4:]}" if apt_id.startswith("apt-") else f"cons-{uuid.uuid4().hex[:8]}"
                consult_data = self.clinical_gen.generate_consultation_data(context, consult_id, apt_id, diagnosis, vitals)
                self.state_manager.set_entity_state("clinical.consultations", consult_id, consult_data)

                rx_id = payload.get("prescription_id", f"rx-{uuid.uuid4().hex[:8]}")
                rx_data = self.clinical_gen.generate_prescription_data(context, rx_id, consult_id, treatment, is_conflict)
                self.state_manager.set_entity_state("pharmacy.prescriptions", rx_id, rx_data)

                payload.update({
                    "diagnosis_code": diagnosis.code,
                    "diagnosis_name": diagnosis.name,
                    "vitals": vitals.model_dump(),
                    "drug_name": treatment.drug,
                    "drug_class": treatment.drug_class,
                    "dosage": treatment.dosage,
                    "frequency": treatment.frequency,
                    "duration_days": treatment.duration_days,
                })

            # Generate action to start consultation
            actions.append(
                ActionRequest(
                    action_id=f"act-consult-{uuid.uuid4().hex[:8]}",
                    action_type="START_DOCTOR_CONSULTATION",
                    target_department="clinical",
                    target_entity_table="clinical.appointments",
                    target_entity_id=event.payload.get("appointment_id", "apt-001"),
                    scenario_instance_id=event.scenario_instance_id,
                    patient_journey_id=event.patient_journey_id,
                    correlation_id=event.correlation_id,
                    causation_id=event.event_id,
                    requested_timestamp=event.scheduled_at,
                    payload=payload,
                )
            )

        elif event.event_type == "CREATE_CLINICAL_ALERT":
            # Reaction to drug-allergy safety hold
            print(f"Clinical Alert Received: {event.payload.get('message', 'Allergy Conflict')}")

        return actions
