"""
Population profile package for SYNAPSE Phase 2.
Provides versioned, provenance-tracked demographic and epidemiological distributions.
"""

from synapse_simulator.population.models import (
    ProvenanceRecord,
    AgeBandDistribution,
    DemographicsConfig,
    ConditionPrevalenceConfig,
    MortalityBandConfig,
    PopulationProfile,
)
from synapse_simulator.population.loader import load_population_profile

__all__ = [
    "ProvenanceRecord",
    "AgeBandDistribution",
    "DemographicsConfig",
    "ConditionPrevalenceConfig",
    "MortalityBandConfig",
    "PopulationProfile",
    "load_population_profile",
]
