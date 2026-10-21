"""
SYNAPSE Phase 2 Evaluation Framework.
Provides independent, research-oriented evaluation of synthetic healthcare data
against empirical real-world reference statistics.
"""

from synapse_simulator.evaluation.evaluator import (
    DatasetEvaluator,
    EvaluationReport,
    MetricResult,
    MetricStatus,
    EvaluationDimension,
)
from synapse_simulator.evaluation.reference_data import (
    ReferenceCatalog,
    ReferenceStatistic,
    get_default_reference_catalog,
)
from synapse_simulator.evaluation.metrics import (
    wilson_score_interval,
    jensen_shannon_divergence,
    total_variation_distance,
    chi_square_goodness_of_fit,
    odds_ratio_and_ci,
    comorbidity_oe_ratio,
    distribution_quantiles,
    two_sample_ks_statistic,
    wasserstein_distance_1d,
    weighted_mean_and_variance,
    effective_sample_size,
    survey_design_effect_weighting,
    survey_weighted_proportion_and_ci,
)
from synapse_simulator.evaluation.report import EvaluationReportFormatter
from synapse_simulator.evaluation.experiment import ExperimentRunner, ExperimentConfig

__all__ = [
    "DatasetEvaluator",
    "EvaluationReport",
    "MetricResult",
    "MetricStatus",
    "EvaluationDimension",
    "ReferenceCatalog",
    "ReferenceStatistic",
    "get_default_reference_catalog",
    "wilson_score_interval",
    "jensen_shannon_divergence",
    "total_variation_distance",
    "chi_square_goodness_of_fit",
    "odds_ratio_and_ci",
    "comorbidity_oe_ratio",
    "distribution_quantiles",
    "two_sample_ks_statistic",
    "wasserstein_distance_1d",
    "weighted_mean_and_variance",
    "effective_sample_size",
    "survey_design_effect_weighting",
    "survey_weighted_proportion_and_ci",
    "EvaluationReportFormatter",
    "ExperimentRunner",
    "ExperimentConfig",
]
