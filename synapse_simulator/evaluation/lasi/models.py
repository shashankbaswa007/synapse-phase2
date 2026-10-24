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


# =============================================================================
# Ingestion Pipeline Exceptions
# =============================================================================

class LasiIngestionError(Exception):
    """Base exception for all LASI ingestion pipeline failures."""
    pass


class LasiUnsupportedFormatError(LasiIngestionError):
    """Raised when an unsupported file format or extension is provided."""
    pass


class LasiMalformedFileError(LasiIngestionError):
    """Raised when a file cannot be parsed or is corrupted."""
    pass


class LasiSchemaValidationError(LasiIngestionError):
    """Raised when required join keys or mandatory schema fields are missing."""
    pass


class LasiDuplicateKeyError(LasiIngestionError):
    """Raised when duplicate primary keys are detected in reference files."""
    pass


class LasiJoinCardinalityError(LasiIngestionError):
    """Raised when join cardinality violates the declared contract (e.g. unexpected many-to-many)."""
    pass


# =============================================================================
# Ingestion and Evaluation Enums
# =============================================================================

class LasiSourceFormat(str, Enum):
    """Supported binary and text source file formats for reference data."""
    STATA_DTA = "STATA_DTA"
    SPSS_SAV = "SPSS_SAV"
    CSV = "CSV"
    TSV = "TSV"


class LasiJoinCardinality(str, Enum):
    """Expected cardinality of relational module joins."""
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_ZERO_OR_ONE = "ONE_TO_ZERO_OR_ONE"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


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
    participant_id: str = Field(..., description="Pseudonymized surrogate identifier (HMAC/SHA-256 digest prefix)")
    household_id: Optional[str] = Field(default=None, description="Pseudonymized household identifier for cluster linkage")
    age: float = Field(..., ge=18.0, le=120.0, description="Chronological age in years")
    gender: str = Field(..., description="Sex / Gender ('Male' or 'Female')")
    state: Optional[str] = Field(default=None, description="State / geographic administrative unit")
    urban_rural: Optional[str] = Field(default=None, description="Urban / Rural sector ('Urban' or 'Rural')")
    
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
    partition_label: Optional[str] = Field(default=None, description="Partition membership: 'PARTITION_A', 'PARTITION_C', or None for full sample")
    
    # Participation and measurement availability indicators
    biomarker_participated: bool = Field(default=False, description="Whether participant was present in the biomarker module")
    bp_participated: bool = Field(default=False, description="Whether participant attempted/participated in blood pressure measurement")
    hba1c_participated: bool = Field(default=False, description="Whether participant provided blood sample for HbA1c testing")
    has_valid_survey_weight: bool = Field(default=False, description="Whether record contains a strictly positive valid survey weight")
    module_membership: Dict[str, bool] = Field(default_factory=dict, description="Module membership flags (e.g. {'individual': True, 'biomarker': True})")

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

    # Multi-module telemetry (optional)
    multi_module_joined: bool = False
    join_telemetry: Optional[Dict[str, Any]] = None

    # Detailed survey design diagnostics summary
    survey_design_diagnostics: Optional[Dict[str, Any]] = None


# =============================================================================
# Milestone 3: Survey Design, Topology, & Estimand Eligibility Schemas
# =============================================================================

class LasiEstimandSupportType(str, Enum):
    """Methodological basis and validity classification of an estimand."""
    OBSERVED_DATA_UNWEIGHTED = "OBSERVED_DATA_UNWEIGHTED"  # Naive complete-case sample statistic
    DESIGN_WEIGHTED_OBSERVED = "DESIGN_WEIGHTED_OBSERVED"  # Base survey weights applied (valid under MCAR/MAR in strata)
    NON_RESPONSE_ADJUSTED = "NON_RESPONSE_ADJUSTED"      # Reweighted with explicit non-response adjustment model
    UNSUPPORTED = "UNSUPPORTED"                          # Inadequate sample support or missing mandatory design fields


class LasiSurveyDesignFieldStatus(BaseModel):
    """Presence, completeness, and provenance of a complex survey design field."""
    field_name: str
    present: bool
    source_column: Optional[str] = None
    total_records: int
    non_null_count: int
    missing_count: int
    missingness_pct: float
    notes: str = ""


class LasiStratumPsuTopology(BaseModel):
    """Primary Sampling Unit (PSU) cluster structure within an individual sampling stratum."""
    stratum_id: str
    psu_count: int
    participant_count: int
    is_singleton: bool = False  # nh == 1: Cannot estimate stratum variance without collapsing or certainty
    is_low_support: bool = False  # nh < 2


class LasiWeightDiagnostics(BaseModel):
    """Distributional, dispersion, and extreme-value diagnostics for sampling weights."""
    total_weights_observed: int
    missing_or_invalid_weights_count: int
    min_weight: float
    max_weight: float
    mean_weight: float
    median_weight: float
    std_weight: float
    cv_weight: float  # Coefficient of Variation = std / mean
    deff_w: float     # Kish DEFF due to weighting = 1 + CV^2
    kish_eff_n: float # Kish effective sample size = (sum w)^2 / sum w^2
    max_to_min_ratio: float
    extreme_weight_count: int
    extreme_weight_pct: float
    top_1_pct_weight_share: float
    top_5_pct_weight_share: float
    has_extreme_weights: bool = False
    weight_trimming_recommended: bool = False


class LasiDomainSupport(BaseModel):
    """Sample size and effective sample size support within a demographic or geographic domain."""
    domain_name: str
    sample_size_n: int
    weighted_n: float
    effective_n: float
    is_sparse: bool = False          # n < 30 or n_eff < 25
    is_severely_sparse: bool = False # n < 15


class LasiEstimandEligibility(BaseModel):
    """Eligibility determination and methodological constraints for a calibration or validation estimand."""
    estimand_id: str
    estimand_name: str
    target_variable: str
    required_fields: List[str]
    support_type: LasiEstimandSupportType
    is_eligible: bool
    missingness_pct: float
    sample_size_available: int
    effective_sample_size: float
    ineligibility_reasons: List[str] = Field(default_factory=list)
    methodological_notes: str = ""


class LasiSurveyDesignDiagnosticsReport(BaseModel):
    """Comprehensive, privacy-preserving aggregate audit of survey design and missingness."""
    diagnostics_timestamp: str
    source_label: str
    total_participants: int
    total_households: Optional[int] = None
    total_strata: int
    total_psus: int
    average_psu_size: float
    psu_size_min: int
    psu_size_max: int
    singleton_strata_count: int
    singleton_strata_pct: float
    low_support_strata_count: int
    field_statuses: Dict[str, LasiSurveyDesignFieldStatus] = Field(default_factory=dict)
    weight_diagnostics: LasiWeightDiagnostics
    stratum_topologies: List[LasiStratumPsuTopology] = Field(default_factory=list)
    domain_supports: Dict[str, LasiDomainSupport] = Field(default_factory=dict)
    missingness_rates: Dict[str, float] = Field(default_factory=dict)
    module_participation: Dict[str, Any] = Field(default_factory=dict)
    estimand_eligibilities: Dict[str, LasiEstimandEligibility] = Field(default_factory=dict)
    diagnostic_warnings: List[str] = Field(default_factory=list)


class LasiSourceFileMetadata(BaseModel):
    """Detailed provenance and structural metadata for an ingested raw source file."""
    file_path: str
    file_name: str
    file_sha256: str
    file_size_bytes: int
    file_format: LasiSourceFormat
    total_rows: int
    total_columns: int
    column_names: List[str] = Field(default_factory=list)
    column_labels: Dict[str, Optional[str]] = Field(default_factory=dict)
    variable_value_labels: Dict[str, Dict[Any, str]] = Field(default_factory=dict)
    has_user_missing_values: bool = False
    user_missing_counts: Dict[str, int] = Field(default_factory=dict)


class LasiJoinTelemetry(BaseModel):
    """Relational join telemetry tracking key integrity, match rates, and merge cardinality."""
    join_key: str
    expected_cardinality: LasiJoinCardinality
    actual_cardinality: str
    primary_module_name: str
    secondary_module_name: str
    primary_input_rows: int
    secondary_input_rows: int
    primary_valid_keys: int
    secondary_valid_keys: int
    primary_missing_keys: int
    secondary_missing_keys: int
    primary_duplicate_keys: int
    secondary_duplicate_keys: int
    merged_output_rows: int
    matched_key_count: int
    unmatched_primary_count: int
    unmatched_secondary_count: int
    biomarker_non_response_pct: float
    reconciliation_verified: bool


class LasiIngestionManifest(BaseModel):
    """Immutable cryptographic audit manifest for reference microdata ingestion."""
    manifest_id: str
    manifest_timestamp: str
    pipeline_version: str = "2.4.0"
    git_commit: Optional[str] = None
    data_source_type: LasiDataSourceType
    source_files: Dict[str, LasiSourceFileMetadata] = Field(default_factory=dict)
    join_telemetry: Optional[LasiJoinTelemetry] = None
    schema_mappings: Dict[str, str] = Field(default_factory=dict)
    missing_value_mappings: Dict[str, Any] = Field(default_factory=dict)
    row_counts: Dict[str, int] = Field(default_factory=dict)
    parser_versions: Dict[str, str] = Field(default_factory=dict)
    conversion_options: Dict[str, Any] = Field(default_factory=dict)
    survey_design_diagnostics_summary: Optional[Dict[str, Any]] = None
    access_control_notice: str = (
        "CONFIDENTIALITY NOTICE: Reference participant microdata is subject to strict "
        "Data Use Agreement (DUA) restrictions under IIPS / Gateway to Global Aging. "
        "Participant-level identifiers and raw records must never be exported to version control."
    )


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
