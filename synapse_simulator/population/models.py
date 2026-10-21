"""
Population Profile Data Models.
Defines schemas for demographic, epidemiological, and mortality distributions
with mandatory provenance metadata and geographic validation.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    GOVERNMENT_CENSUS = "GOVERNMENT_CENSUS"
    PEER_REVIEWED_STUDY = "PEER_REVIEWED_STUDY"
    CLINICAL_GUIDELINE = "CLINICAL_GUIDELINE"
    ESTIMATED_ASSUMPTION = "ESTIMATED_ASSUMPTION"


class MissingReferenceStatisticError(Exception):
    """Raised when a required population statistic has no cited empirical reference."""
    pass


class ProvenanceRecord(BaseModel):
    """Provenance citation for a demographic or epidemiological statistic."""
    provenance_id: str
    title: str
    publisher: str
    year: int
    source_type: SourceType
    url_or_ref: str
    geography: str = "IN"
    is_assumption: bool = False
    sample_size: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("provenance_id")
    def validate_provenance_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("provenance_id cannot be empty")
        return v.strip()


class AgeBandDistribution(BaseModel):
    """Defines a single age band and its population weight."""
    min_age: int
    max_age: int
    weight: float

    @model_validator(mode="after")
    def validate_bounds(self) -> "AgeBandDistribution":
        if self.min_age < 0:
            raise ValueError(f"min_age must be non-negative, got {self.min_age}")
        if self.max_age < self.min_age:
            raise ValueError(f"max_age ({self.max_age}) must be >= min_age ({self.min_age})")
        if self.weight < 0.0:
            raise ValueError(f"weight must be non-negative, got {self.weight}")
        return self


class DemographicsConfig(BaseModel):
    """Demographic structure for population generation."""
    age_provenance_id: str
    age_bands: List[AgeBandDistribution]
    sex_provenance_id: str
    male_ratio: float = 0.50
    female_ratio: float = 0.50

    @model_validator(mode="after")
    def validate_ratios(self) -> "DemographicsConfig":
        total_sex = self.male_ratio + self.female_ratio
        if not (0.999 <= total_sex <= 1.001):
            raise ValueError(f"male_ratio + female_ratio must sum to 1.0, got {total_sex}")
        total_age_weight = sum(b.weight for b in self.age_bands)
        if not (0.999 <= total_age_weight <= 1.001):
            raise ValueError(f"age_bands weights must sum to 1.0, got {total_age_weight}")
        return self


class ConditionPrevalenceConfig(BaseModel):
    """Epidemiological prevalence for a chronic or acute condition."""
    condition_code: str
    condition_name: str
    provenance_id: str
    min_age: int = 0
    max_age: int = 120
    prevalence_percent: float
    male_prevalence_percent: Optional[float] = None
    female_prevalence_percent: Optional[float] = None
    is_acute: bool = False
    annual_incidence_rate: Optional[float] = None

    @model_validator(mode="after")
    def validate_prevalence(self) -> "ConditionPrevalenceConfig":
        if not (0.0 <= self.prevalence_percent <= 100.0):
            raise ValueError(f"prevalence_percent must be in [0, 100], got {self.prevalence_percent}")
        return self


class MortalityBandConfig(BaseModel):
    """Annual probability of death (qx) for an age interval."""
    min_age: int
    max_age: int
    qx_annual: float
    qx_male: Optional[float] = None
    qx_female: Optional[float] = None


class MortalityConfig(BaseModel):
    """Life table configuration."""
    provenance_id: str
    bands: List[MortalityBandConfig] = Field(default_factory=list)


class PopulationProfileMetadata(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    target_geography: str = "IN"
    reference_year: int = 2021
    description: str = ""


class PopulationProfile(BaseModel):
    """Versioned, provenance-backed population profile."""
    schema_version: str = "1.0.0"
    metadata: PopulationProfileMetadata
    provenance_catalog: Dict[str, ProvenanceRecord]
    demographics: DemographicsConfig
    prevalences: List[ConditionPrevalenceConfig] = Field(default_factory=list)
    mortality: Optional[MortalityConfig] = None

    @model_validator(mode="after")
    def validate_provenance_integrity(self) -> "PopulationProfile":
        target_geo = self.metadata.target_geography

        def check_provenance(prov_id: str, context_desc: str) -> None:
            if prov_id not in self.provenance_catalog:
                raise MissingReferenceStatisticError(
                    f"Profile '{self.metadata.id}': {context_desc} references undeclared provenance_id '{prov_id}'"
                )
            record = self.provenance_catalog[prov_id]
            if not record.is_assumption and record.geography != target_geo:
                raise ValueError(
                    f"Geographic mismatch: Profile is for '{target_geo}', but provenance '{prov_id}' is from '{record.geography}'. "
                    "Cross-geographic borrowing is strictly forbidden unless explicitly tagged as is_assumption: true."
                )

        check_provenance(self.demographics.age_provenance_id, "demographics.age_bands")
        check_provenance(self.demographics.sex_provenance_id, "demographics.sex_distribution")

        for prev in self.prevalences:
            check_provenance(prev.provenance_id, f"prevalences.{prev.condition_code}")

        if self.mortality:
            check_provenance(self.mortality.provenance_id, "mortality")

        return self
