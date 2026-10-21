"""
Clinical Entity Generator: Context-aware generation of appointments, consultations,
diagnoses, vitals, and prescriptions. Consumes PatientContext + MedicalKnowledgeBase.
"""

import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.knowledge.models import DiagnosisEntry, DrugTreatment
from synapse_simulator.core.ids import new_id
from synapse_simulator.datagen.models import (
    PatientContext,
    MasterDataSnapshot,
    StaffProfile,
    GeneratedVitals,
)


class ClinicalEntityGenerator:
    """Generates clinical records driven by patient context and medical knowledge."""

    def __init__(self, knowledge_base: MedicalKnowledgeBase, master_data: MasterDataSnapshot, rng: random.Random):
        self.kb = knowledge_base
        self.master_data = master_data
        self.rng = rng

    def assign_doctor(self, patient: PatientContext) -> StaffProfile:
        """Assign a doctor from the master data pool."""
        doctors = self.master_data.doctors
        if not doctors:
            return StaffProfile(
                staff_id=new_id("doc-fallback-", 6),
                name="Dr. Fallback",
                role="doctor",
                department_id="DEPT-CLIN",
                specialization="General Medicine",
            )
        return self.rng.choice(doctors)

    def assign_room(self) -> str:
        """Assign an OPD consultation room."""
        clinical_rooms = [r for r in self.master_data.rooms if r.room_type == "consultation"]
        if clinical_rooms:
            return self.rng.choice(clinical_rooms).room_id
        return "OPD-001"

    def select_diagnosis(self, patient: PatientContext) -> DiagnosisEntry:
        """Select a contextually appropriate diagnosis for the patient.

        Filters by:
        - Patient age range
        - Gender bias (if any)
        - Weighted random selection from valid candidates
        """
        candidates = self.kb.get_diagnoses_for_age(patient.age)

        # Filter by gender bias
        filtered = []
        for d in candidates:
            if d.gender_bias is None:
                filtered.append(d)
            elif d.gender_bias == "F" and patient.gender == "Female":
                filtered.append(d)
            elif d.gender_bias == "M" and patient.gender == "Male":
                filtered.append(d)

        if not filtered:
            filtered = candidates if candidates else self.kb.diagnoses[:1]

        return self.rng.choice(filtered)

    def select_medication(
        self,
        patient: PatientContext,
        diagnosis: DiagnosisEntry,
        force_conflict: bool = False,
    ) -> Tuple[DrugTreatment, bool]:
        """Select a medication for the diagnosis, respecting allergy constraints.

        Args:
            patient: Patient context with allergy profile.
            diagnosis: Selected diagnosis.
            force_conflict: If True, intentionally pick a conflicting drug (for SCEN-V1-03).

        Returns:
            Tuple of (selected treatment, is_allergy_conflict).
        """
        treatments = self.kb.get_treatments_for_diagnosis(diagnosis.code)

        if force_conflict and patient.allergies:
            # Intentionally select a drug from diagnosis treatments that conflicts with patient allergies
            for treatment in treatments:
                conflicts = self.kb.get_allergy_conflicts(patient.allergies, treatment.drug_class)
                if conflicts:
                    return treatment, True

        # Normal path: filter to safe drugs
        safe_treatments = self.kb.get_compatible_drugs_for_patient(
            diagnosis.code, patient.allergies
        )

        if safe_treatments:
            return self.rng.choice(safe_treatments), False

        # All treatments conflict — use first treatment and flag the conflict
        if treatments:
            return treatments[0], True

        # Fallback (offline miss or unknown condition without fabricated evidence)
        fallback = DrugTreatment(
            drug="Paracetamol",
            drug_class="Analgesic",
            dosage="500mg",
            frequency="TDS",
            duration_days=5,
            source="internal_yaml",
            evidence_ids=[],
        )
        return fallback, False

    def generate_vitals(self, patient: PatientContext, diagnosis: DiagnosisEntry) -> GeneratedVitals:
        """Generate physiologically plausible vitals for patient + diagnosis context.

        If diagnosis has fever-related symptoms, use febrile temperature range.
        """
        vitals_range = self.kb.get_vitals_range_for_age(patient.age)
        febrile_range = self.kb.vitals_ranges.get("febrile")

        # Determine if febrile
        fever_symptoms = {"fever", "high_fever"}
        has_fever = bool(fever_symptoms & set(diagnosis.symptoms))

        if has_fever and febrile_range:
            temp = round(self.rng.uniform(febrile_range.temperature_c[0], febrile_range.temperature_c[1]), 1)
        else:
            temp = round(self.rng.uniform(vitals_range.temperature_c[0], vitals_range.temperature_c[1]), 1)

        return GeneratedVitals(
            temperature_c=temp,
            heart_rate_bpm=self.rng.randint(vitals_range.heart_rate_bpm[0], vitals_range.heart_rate_bpm[1]),
            systolic_bp=self.rng.randint(vitals_range.systolic_bp[0], vitals_range.systolic_bp[1]),
            diastolic_bp=self.rng.randint(vitals_range.diastolic_bp[0], vitals_range.diastolic_bp[1]),
            respiratory_rate=self.rng.randint(vitals_range.respiratory_rate[0], vitals_range.respiratory_rate[1]),
            spo2_percent=self.rng.randint(vitals_range.spo2_percent[0], vitals_range.spo2_percent[1]),
        )

    def generate_appointment_data(
        self,
        patient: PatientContext,
        appointment_id: str,
        scheduled_time: datetime,
    ) -> Dict[str, Any]:
        """Generate a complete appointment entity record."""
        doctor = self.assign_doctor(patient)
        room = self.assign_room()

        patient.assigned_doctor_id = doctor.staff_id
        patient.assigned_room_id = room

        return {
            "appointment_id": appointment_id,
            "patient_id": patient.patient_id,
            "doctor_id": doctor.staff_id,
            "doctor_name": doctor.name,
            "room_id": room,
            "scheduled_time": scheduled_time.isoformat(),
            "appointment_type": "New" if not patient.chronic_conditions else "Follow-Up",
            "status": "Checked-In",
        }

    def generate_consultation_data(
        self,
        patient: PatientContext,
        consultation_id: str,
        appointment_id: str,
        diagnosis: DiagnosisEntry,
        vitals: GeneratedVitals,
    ) -> Dict[str, Any]:
        """Generate a consultation record with diagnosis and vitals."""
        chief_complaint = ", ".join(diagnosis.symptoms[:3]) if diagnosis.symptoms else "General checkup"

        return {
            "consultation_id": consultation_id,
            "appointment_id": appointment_id,
            "patient_id": patient.patient_id,
            "doctor_id": patient.assigned_doctor_id,
            "diagnosis_code": diagnosis.code,
            "diagnosis_name": diagnosis.name,
            "chief_complaint": chief_complaint,
            "vitals": vitals.model_dump(),
            "status": "In-Progress",
        }

    def generate_prescription_data(
        self,
        patient: PatientContext,
        prescription_id: str,
        consultation_id: str,
        treatment: DrugTreatment,
        is_conflict: bool = False,
    ) -> Dict[str, Any]:
        """Generate a prescription record from selected treatment."""
        return {
            "prescription_id": prescription_id,
            "patient_id": patient.patient_id,
            "consultation_id": consultation_id,
            "drug_name": treatment.drug,
            "drug_class": treatment.drug_class,
            "dosage": treatment.dosage,
            "frequency": treatment.frequency,
            "duration_days": treatment.duration_days,
            "has_allergy_conflict": is_conflict,
            "source": getattr(treatment, "source", "internal_yaml"),
            "evidence_ids": getattr(treatment, "evidence_ids", []),
            "status": "Issued",
        }

