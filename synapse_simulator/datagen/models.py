"""
Data Generation Models: Persistent context objects that flow through the generation pipeline.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PatientContext(BaseModel):
    """Persistent patient context that flows through the entire journey.
    Once created, this context is consumed by all downstream generators."""
    patient_id: str
    name: str
    age: int
    gender: str
    allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)
    insurance_type: str = "General"
    blood_group: str = "O+"
    # Scenario-assigned fields
    scenario_id: str = ""
    encounter_id: Optional[str] = None
    diagnosis_code: Optional[str] = None
    diagnosis_name: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    assigned_room_id: Optional[str] = None
    force_conflict: bool = False
    # Longitudinal fields
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    is_alive: bool = True
    attributes: Dict[str, Any] = Field(default_factory=dict)
    latent_conditions: Dict[str, Any] = Field(default_factory=dict)
    baseline_conditions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    prescriptions: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_events: List[Dict[str, Any]] = Field(default_factory=list)


class StaffProfile(BaseModel):
    """Generated staff member profile."""
    staff_id: str
    name: str
    role: str  # doctor, nurse, pharmacist, lab_technician, etc.
    department_id: str
    specialization: Optional[str] = None
    qualification: str = ""


class RoomRecord(BaseModel):
    """Generated room/location record."""
    room_id: str
    room_name: str
    department_id: str
    floor: int = 0
    room_type: str = "consultation"


class InventorySnapshot(BaseModel):
    """Runtime inventory batch state for a single drug type."""
    batch_id: str
    drug_name: str
    drug_class: str
    quantity_available: int
    quantity_initial: int
    unit_cost: float
    status: str = "Active"


class GeneratedVitals(BaseModel):
    """Vitals snapshot for a consultation."""
    temperature_c: float
    heart_rate_bpm: int
    systolic_bp: int
    diastolic_bp: int
    respiratory_rate: int
    spo2_percent: int


class GeneratedLabResult(BaseModel):
    """A single lab test result with all component values."""
    test_name: str
    components: List[Dict[str, Any]] = Field(default_factory=list)
    is_abnormal: bool = False
    ordered_at: Optional[datetime] = None
    resulted_at: Optional[datetime] = None


class GeneratedRadiologyReport(BaseModel):
    """A radiology imaging report."""
    imaging_type: str
    findings: str = ""
    impression: str = ""
    is_abnormal: bool = False
    ordered_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None


class InvoiceLineItem(BaseModel):
    """A single line item on a patient invoice."""
    service_type: str  # consultation, lab_test, imaging, medication
    service_name: str
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    source_entity_id: str = ""  # FK back to the entity that caused this charge


class GenerationTrace(BaseModel):
    """Traceability record: why was this entity generated?"""
    entity_table: str
    entity_id: str
    patient_id: str
    journey_id: str
    scenario_id: str
    caused_by_action: str = ""
    caused_by_rule: str = ""
    generation_timestamp: datetime
    generator_class: str = ""
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)


class MasterDataSnapshot(BaseModel):
    """Complete generated master data for a simulation run."""
    departments: List[Dict[str, Any]] = Field(default_factory=list)
    staff: List[StaffProfile] = Field(default_factory=list)
    rooms: List[RoomRecord] = Field(default_factory=list)
    inventory: List[InventorySnapshot] = Field(default_factory=list)
    # Indexes for fast lookup
    doctors: List[StaffProfile] = Field(default_factory=list)
    pharmacists: List[StaffProfile] = Field(default_factory=list)
    lab_technicians: List[StaffProfile] = Field(default_factory=list)
    # Drug name -> batch_id mapping
    drug_batch_index: Dict[str, str] = Field(default_factory=dict)
