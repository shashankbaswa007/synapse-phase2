"""
Population profile loader and sampling utilities.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml
import random

from synapse_simulator.population.models import (
    PopulationProfile,
    MissingReferenceStatisticError,
)


def load_population_profile(profile_path: Path) -> PopulationProfile:
    """Load and validate a PopulationProfile YAML file."""
    if not profile_path.exists():
        raise FileNotFoundError(f"Population profile not found at {profile_path}")

    with open(profile_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    if not isinstance(raw_data, dict):
        raise ValueError(f"Invalid YAML content in {profile_path}: expected dictionary root")

    return PopulationProfile.model_validate(raw_data)


class PopulationSampler:
    """Provides reproducible sampling of demographic and clinical baseline features from a profile."""

    def __init__(self, profile: PopulationProfile, rng: random.Random):
        self.profile = profile
        self.rng = rng

    def sample_age(self) -> int:
        """Sample an integer age according to age band distribution."""
        bands = self.profile.demographics.age_bands
        weights = [b.weight for b in bands]
        selected_band = self.rng.choices(bands, weights=weights, k=1)[0]
        return self.rng.randint(selected_band.min_age, selected_band.max_age)

    def sample_sex(self) -> str:
        """Sample sex (Male / Female)."""
        demo = self.profile.demographics
        return self.rng.choices(["Male", "Female"], weights=[demo.male_ratio, demo.female_ratio], k=1)[0]

    def has_condition_at_baseline(
        self,
        condition_code: str,
        age: int,
        sex: str,
        conditional_rate: Optional[float] = None,
    ) -> bool:
        """Evaluate if patient has a condition at baseline given age, sex, and optional comorbidity rate."""
        for prev in self.profile.prevalences:
            if prev.condition_code == condition_code:
                if age < prev.min_age or age > prev.max_age:
                    return False
                if conditional_rate is not None:
                    rate = conditional_rate
                else:
                    rate = prev.prevalence_percent
                    if sex == "Male" and prev.male_prevalence_percent is not None:
                        rate = prev.male_prevalence_percent
                    elif sex == "Female" and prev.female_prevalence_percent is not None:
                        rate = prev.female_prevalence_percent
                return (self.rng.random() * 100.0) < rate
        return False

    def get_annual_mortality_rate(self, age: int, sex: str) -> float:
        """Look up annual probability of death qx from life table."""
        if not self.profile.mortality:
            return 0.0
        for band in self.profile.mortality.bands:
            if band.min_age <= age <= band.max_age:
                if sex == "Male" and band.qx_male is not None:
                    return band.qx_male
                elif sex == "Female" and band.qx_female is not None:
                    return band.qx_female
                return band.qx_annual
        return 0.0
