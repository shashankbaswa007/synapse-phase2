"""
LASI Wave 1 External Validation Pipeline Package.

Exposes:
- LasiDataIngestor: Multi-format ingestion, de-identification, and data quality reporting
- PopulationComparabilityLayer: Standardizing and matching target populations
- LasiExternalEvaluator: Evaluating synthetic healthcare records against LASI Wave 1 reference data
- Models and schemas for data quality, metrics, and evaluation reporting
"""

from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiDataQualityReport,
    LasiDataSourceType,
    LasiEvaluationGateStatus,
    LasiMetricStatus,
    LasiMetricResult,
    LasiEvaluationReport,
    LasiComparisonPopulation,
    LasiSourceFormat,
    LasiJoinCardinality,
    LasiSourceFileMetadata,
    LasiJoinTelemetry,
    LasiIngestionManifest,
    LasiIngestionError,
    LasiUnsupportedFormatError,
    LasiMalformedFileError,
    LasiSchemaValidationError,
    LasiDuplicateKeyError,
    LasiJoinCardinalityError,
    LasiEstimandSupportType,
    LasiSurveyDesignFieldStatus,
    LasiStratumPsuTopology,
    LasiWeightDiagnostics,
    LasiDomainSupport,
    LasiEstimandEligibility,
    LasiSurveyDesignDiagnosticsReport,
)
from synapse_simulator.evaluation.lasi.security import (
    KeyedPseudonymizer,
    CONFIDENTIALITY_NOTICE,
)
from synapse_simulator.evaluation.lasi.missingness import (
    VariableMissingValuePolicy,
    UNIVERSAL_STRING_MISSINGS,
)
from synapse_simulator.evaluation.lasi.diagnostics import (
    LasiSurveyDesignDiagnostics,
)
from synapse_simulator.evaluation.lasi.variance import (
    SingletonHandlingStrategy,
    LasiSurveyVarianceEngine,
    student_t_critical_value,
)
from synapse_simulator.evaluation.lasi.partitioner import (
    PartitionLabel,
    StratumSupportStatus,
    LasiPartitionConfig,
    LasiClusterAllocation,
    LasiCovariateBalanceReport,
    LasiPartitionResult,
    LasiPsuPartitioner,
    HoldoutAccessTicket,
    HoldoutAuditLedger,
    LasiHoldoutVault,
    LasiPartitioningError,
    LasiLeakageError,
    LasiUnsupportedStratumError,
    HoldoutAccessViolationError,
)
from synapse_simulator.evaluation.lasi.ingestor import (
    LasiDataIngestor,
    LasiMultiModuleIngestor,
    compute_file_sha256,
    detect_file_format,
    load_raw_table_with_metadata,
    execute_validated_join,
)
from synapse_simulator.evaluation.lasi.comparability import (
    PopulationComparabilityLayer,
    get_age_band_older_adult,
    CENSUS_SRS_OLDER_ADULT_WEIGHTS,
)
from synapse_simulator.evaluation.lasi.evaluator import (
    LasiExternalEvaluator,
    LasiEvaluationReportFormatter,
)

__all__ = [
    "LasiCleanedRecord",
    "LasiDataQualityReport",
    "LasiDataSourceType",
    "LasiEvaluationGateStatus",
    "LasiMetricStatus",
    "LasiMetricResult",
    "LasiEvaluationReport",
    "LasiComparisonPopulation",
    "LasiSourceFormat",
    "LasiJoinCardinality",
    "LasiSourceFileMetadata",
    "LasiJoinTelemetry",
    "LasiIngestionManifest",
    "LasiIngestionError",
    "LasiUnsupportedFormatError",
    "LasiMalformedFileError",
    "LasiSchemaValidationError",
    "LasiDuplicateKeyError",
    "LasiJoinCardinalityError",
    "LasiEstimandSupportType",
    "LasiSurveyDesignFieldStatus",
    "LasiStratumPsuTopology",
    "LasiWeightDiagnostics",
    "LasiDomainSupport",
    "LasiEstimandEligibility",
    "LasiSurveyDesignDiagnosticsReport",
    "KeyedPseudonymizer",
    "CONFIDENTIALITY_NOTICE",
    "VariableMissingValuePolicy",
    "UNIVERSAL_STRING_MISSINGS",
    "LasiSurveyDesignDiagnostics",
    "SingletonHandlingStrategy",
    "LasiSurveyVarianceEngine",
    "student_t_critical_value",
    "PartitionLabel",
    "StratumSupportStatus",
    "LasiPartitionConfig",
    "LasiClusterAllocation",
    "LasiCovariateBalanceReport",
    "LasiPartitionResult",
    "LasiPsuPartitioner",
    "HoldoutAccessTicket",
    "LasiHoldoutVault",
    "LasiPartitioningError",
    "LasiLeakageError",
    "LasiUnsupportedStratumError",
    "HoldoutAccessViolationError",
    "LasiDataIngestor",
    "LasiMultiModuleIngestor",
    "compute_file_sha256",
    "detect_file_format",
    "load_raw_table_with_metadata",
    "execute_validated_join",
    "PopulationComparabilityLayer",
    "get_age_band_older_adult",
    "CENSUS_SRS_OLDER_ADULT_WEIGHTS",
    "LasiExternalEvaluator",
    "LasiEvaluationReportFormatter",
]
