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
)
from synapse_simulator.evaluation.lasi.ingestor import (
    LasiDataIngestor,
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
    "LasiDataIngestor",
    "PopulationComparabilityLayer",
    "get_age_band_older_adult",
    "CENSUS_SRS_OLDER_ADULT_WEIGHTS",
    "LasiExternalEvaluator",
    "LasiEvaluationReportFormatter",
]
