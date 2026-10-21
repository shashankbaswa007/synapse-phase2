"""
Pydantic data models for medical knowledge configuration.
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class DrugTreatment(BaseModel):
    """A single drug treatment option for a diagnosis."""
    drug: str
    drug_class: str
    dosage: str
    frequency: str
    duration_days: int
    source: str = "internal_yaml"
    evidence_ids: List[str] = Field(default_factory=list)



class DiagnosisEntry(BaseModel):
    """A curated diagnosis with symptoms, treatments, labs, and imaging."""
    code: str
    name: str
    category: str
    age_range: List[int] = Field(default_factory=lambda: [1, 90])
    gender_bias: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    treatments: List[DrugTreatment] = Field(default_factory=list)
    lab_tests: List[str] = Field(default_factory=list)
    imaging: List[str] = Field(default_factory=list)


class AllergyEntry(BaseModel):
    """Cross-reactivity entry for a specific allergy."""
    cross_reactive_classes: List[str] = Field(default_factory=list)
    cross_reactive_drugs: List[str] = Field(default_factory=list)
    safe_alternatives: List[DrugTreatment] = Field(default_factory=list)


class ChronicCondition(BaseModel):
    """Age-correlated chronic condition for patient generation."""
    name: str
    min_age: int = 0
    prevalence_percent: float = 10.0


class AllergyPrevalence(BaseModel):
    """Population-level allergy prevalence for patient generation."""
    name: str
    prevalence_percent: float = 5.0


class LabComponent(BaseModel):
    """A single measurable lab component with reference ranges."""
    name: str
    unit: str
    normal_range: List[float]
    critical_low: float
    critical_high: float


class LabTestRange(BaseModel):
    """Lab test with its measurable components."""
    components: List[LabComponent] = Field(default_factory=list)


class RadiologyFindings(BaseModel):
    """Template findings for radiology imaging types."""
    normal: str = ""
    abnormal: List[str] = Field(default_factory=list)


class VitalsRange(BaseModel):
    """Physiological vitals ranges by age group."""
    age_range: List[int] = Field(default_factory=lambda: [1, 90])
    temperature_c: List[float] = Field(default_factory=lambda: [36.1, 37.2])
    heart_rate_bpm: List[int] = Field(default_factory=lambda: [60, 100])
    systolic_bp: List[int] = Field(default_factory=lambda: [90, 140])
    diastolic_bp: List[int] = Field(default_factory=lambda: [60, 90])
    respiratory_rate: List[int] = Field(default_factory=lambda: [12, 20])
    spo2_percent: List[int] = Field(default_factory=lambda: [95, 100])


class ServicePricing(BaseModel):
    """Hospital service pricing schedule."""
    consultation_fee: float = 500.0
    follow_up_fee: float = 300.0
    lab_test_fees: Dict[str, float] = Field(default_factory=dict)
    imaging_fees: Dict[str, float] = Field(default_factory=dict)
    medication_markup_percent: float = 20.0


# --- Master data config models ---

class DepartmentRoomConfig(BaseModel):
    count: int = 1
    prefix: str = "RM"


class DepartmentStaffConfig(BaseModel):
    doctors: int = 0
    nurses: int = 0
    pharmacists: int = 0
    pharmacy_technicians: int = 0
    pathologists: int = 0
    lab_technicians: int = 0
    radiologists: int = 0
    rad_technicians: int = 0
    billing_clerks: int = 0


class DepartmentConfig(BaseModel):
    id: str
    name: str
    type: str
    floor: int = 0
    rooms: DepartmentRoomConfig = Field(default_factory=DepartmentRoomConfig)
    staff: DepartmentStaffConfig = Field(default_factory=DepartmentStaffConfig)


class InventoryConfig(BaseModel):
    drug_name: str
    drug_class: str
    batch_quantity: int = 100
    unit_cost: float = 5.0
    expiry_months: int = 24


class OperatingHoursConfig(BaseModel):
    start_hour: int = 8
    end_hour: int = 18
    slot_duration_minutes: int = 15
    days: List[str] = Field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])


class MasterDataConfig(BaseModel):
    departments: List[DepartmentConfig] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list)
    initial_inventory: List[InventoryConfig] = Field(default_factory=list)
    operating_hours: OperatingHoursConfig = Field(default_factory=OperatingHoursConfig)
