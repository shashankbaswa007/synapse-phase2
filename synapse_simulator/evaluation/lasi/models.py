"""
Pydantic Data Models and Schemas for LASI External Evaluation Pipeline.

Defines schemas for:
1. Ingested raw and normalized LASI Wave 1 reference records
2. Data quality audits and missingness reporting
3. Standardization parameters and population definitions
4. Metric results for demographic, blood pressure, HbA1c, and prevalence comparisons
5. External evaluation reporting with clear gate distinctions
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from pydantic import BaseModel, Field


class LasiDataSourceType(str, Enum):
    """Categorizes the origin and regulatory status of the reference dataset."""
    SYNTHETIC_TEST_FIXTURE = "SYNTHETIC_TEST_FIXTURE"
    GENUINE_LASI_MICRODATA = "GENUINE_LASI_MICRODATA"


class LasiEvaluationGateStatus(str, Enum):
    """Formal status of the overall external evaluation gate."""
    REFERENCE_DATA_PENDING = "REFERENCE_DATA_PENDING"
    PENDING_GENUINE_REFERENCE_DATA = "REFERENCE_DATA_PENDING"  # Backward-compatible alias
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    INSUFFICIENT_SAMPLE_SIZE = "INSUFFICIENT_SAMPLE_SIZE"


class LasiMetricStatus(str, Enum):
    """Evaluation status for an individual quantitative metric."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNVERIFIED = "UNVERIFIED"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    INSUFFICIENT_SAMPLE_SIZE = "INSUFFICIENT_SAMPLE_SIZE"
    INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE = "INSUFFICIENT_EFFECTIVE_SAMPLE_SIZE"
    REFERENCE_DATA_PENDING = "REFERENCE_DATA_PENDING"
    PENDING_REAL_MICRODATA = "REFERENCE_DATA_PENDING"  # Backward-compatible alias


class LasiComparisonPopulation(str, Enum):
    """Evaluation target cohort definition."""
    POPULATION_A_GENERAL_ADULTS = "POPULATION_A_GENERAL_ADULTS"  # Age >= 20
    POPULATION_B_OLDER_ADULTS = "POPULATION_B_OLDER_ADULTS"      # Age >= 45 (LASI-aligned)


class LasiCleanedRecord(BaseModel):
    """Cleaned, normalized, and validated LASI individual participant record."""
    participant_id: str = Field(..., description="Pseudonymized surrogate identifier (SHA-256 digest prefix)")
    age: float = Field(..., ge=18.0, le=120.0, description="Chronological age in years")
    gender: str = Field(..., description="Sex / Gender ('Male' or 'Female')")
    
    # Blood pressure readings (mmHg)
    sbp_reading1: Optional[float] = None
    sbp_reading2: Optional[float] = None
    sbp_reading3: Optional[float] = None
    sbp_mean: Optional[float] = None  # Protocolized mean of 2nd & 3rd readings
    
    dbp_reading1: Optional[float] = None
    dbp_reading2: Optional[float] = None
    dbp_reading3: Optional[float] = None
    dbp_mean: Optional[float] = None
    bp_derivation_method: str = Field(
        default="PROTOCOL_MEAN_READINGS_2_AND_3",
        description="Exact rule used: PROTOCOL_MEAN_READINGS_2_AND_3, FALLBACK_READING_2_ONLY, FALLBACK_READING_3_ONLY, FALLBACK_READING_1_ONLY, or EXCLUDED"
    )
    
    # Biomarkers
    hba1c: Optional[float] = None       # Primary analysis HbA1c (%)
    hba1c_dbs: Optional[float] = None   # Raw Dried Blood Spot assay (%)
    hba1c_venous: Optional[float] = None # Venous HPLC equivalent if explicitly enabled, else None
    
    # Self-reported physician-diagnosed chronic conditions
    diagnosed_hypertension: Optional[bool] = None
    diagnosed_diabetes: Optional[bool] = None
    diagnosed_ckd: Optional[bool] = None
    
    # Pharmacotherapy
    taking_bp_medication: Optional[bool] = None
    taking_diabetes_medication: Optional[bool] = None
    
    # Complex Survey Design
    survey_weight: Optional[float] = Field(default=1.0, ge=0.0)
    strata: Optional[str] = None
    psu: Optional[str] = None
    
    # Validity indicators
    is_valid_for_bp: bool = False
    is_valid_for_hba1c: bool = False


class LasiDataQualityReport(BaseModel):
    """Reproducible audit report of reference data ingestion and quality checks."""
    source_file: str
    file_sha256: str
    data_source_type: LasiDataSourceType
    total_records_ingested: int = 0
    duplicate_records_detected: int = 0
    valid_records: int = 0
    excluded_records: int = 0
    missingness_counts: Dict[str, int] = Field(default_factory=dict)
    out_of_range_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Survey design telemetry
    survey_weights_present: bool = False
    survey_weights_coverage_pct: float = 0.0
    effective_sample_size: float = 0.0
    design_effect_weighting: float = 1.0
    strata_present: bool = False
    psu_present: bool = False
    
    # Blood pressure protocol derivation counts
    bp_derivation_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Summaries
    age_summary: Dict[str, float] = Field(default_factory=dict)
    sbp_summary: Dict[str, float] = Field(default_factory=dict)
    dbp_summary: Dict[str, float] = Field(default_factory=dict)
    hba1c_summary: Dict[str, float] = Field(default_factory=dict)
    quality_flags: List[str] = Field(default_factory=list)


class LasiMetricResult(BaseModel):
    """Detailed quantitative result of an external evaluation metric."""
    metric_id: str
    metric_name: str
    category: str  # DEMOGRAPHICS, BLOOD_PRESSURE, HBA1C, PREVALENCE, SURVEY_DESIGN
    population: str
    standardized: bool = False
    synthetic_n: int
    reference_n: int
    synthetic_patient_count: Optional[int] = None
    synthetic_observation_count: Optional[int] = None
    estimand_type: Optional[str] = None
    synthetic_effective_n: Optional[float] = None
    reference_effective_n: Optional[float] = None
    design_effect: Optional[float] = None
    min_sample_size_required: int = 0
    min_effective_sample_size_required: float = 0.0
    synthetic_estimate: float
    reference_estimate: Optional[float] = None
    difference: Optional[float] = None
    synthetic_quantiles: Optional[Dict[str, float]] = None
    reference_quantiles: Optional[Dict[str, float]] = None
    quantile_differences: Optional[Dict[str, float]] = None
    ks_statistic: Optional[float] = None
    ks_p_value: Optional[float] = None
    wasserstein_distance: Optional[float] = None
    synthetic_ci: Optional[Tuple[float, float]] = None
    reference_ci: Optional[Tuple[float, float]] = None
    acceptance_threshold: Dict[str, Any] = Field(default_factory=dict)
    status: LasiMetricStatus
    comparability_notes: str = ""
    limitations: str = ""


class LasiEvaluationReport(BaseModel):
    """Comprehensive external validation report comparing SYNAPSE against LASI Wave 1."""
    evaluation_timestamp: str
    synthetic_dataset_dir: str
    reference_file: str
    reference_sha256: str
    reference_source_type: LasiDataSourceType
    overall_gate_status: LasiEvaluationGateStatus
    data_quality: LasiDataQualityReport
    metrics: List[LasiMetricResult] = Field(default_factory=list)
    calibration_leakage_veto: bool = True
    demographic_concordance: Dict[str, Any] = Field(default_factory=dict)
    blood_pressure_concordance: Dict[str, Any] = Field(default_factory=dict)
    hba1c_concordance: Dict[str, Any] = Field(default_factory=dict)
    prevalence_concordance: Dict[str, Any] = Field(default_factory=dict)
    limitations_disclosures: List[str] = Field(default_factory=list)
