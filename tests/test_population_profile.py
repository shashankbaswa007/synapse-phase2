"""
Tests for Population Profile models, loader, and sampling.
"""

from pathlib import Path
import random
import pytest

from synapse_simulator.population.models import (
    PopulationProfile,
    ProvenanceRecord,
    SourceType,
    MissingReferenceStatisticError,
)
from synapse_simulator.population.loader import load_population_profile, PopulationSampler


PROFILE_PATH = Path(__file__).parent.parent / "config" / "population" / "india_default_v1.yaml"


def test_load_india_default_profile():
    profile = load_population_profile(PROFILE_PATH)
    assert profile.metadata.id == "pop-in-default-v1"
    assert profile.metadata.target_geography == "IN"
    assert len(profile.demographics.age_bands) == 5
    assert profile.demographics.male_ratio == 0.515
    assert "SRS_2021_DEMO" in profile.provenance_catalog
    assert "ICMR_INDIAB_2023_HTN" in profile.provenance_catalog
    assert "ICMR_INDIAB_2023_T2D" in profile.provenance_catalog
    assert "SRS_2016_2020_LIFE_TABLE" in profile.provenance_catalog
    assert len(profile.prevalences) >= 3
    assert profile.mortality is not None


def test_missing_provenance_raises():
    profile = load_population_profile(PROFILE_PATH)
    profile_dict = profile.model_dump()
    profile_dict["demographics"]["age_provenance_id"] = "NON_EXISTENT_PROV"

    with pytest.raises(MissingReferenceStatisticError):
        PopulationProfile.model_validate(profile_dict)


def test_geographic_mismatch_raises():
    profile = load_population_profile(PROFILE_PATH)
    profile_dict = profile.model_dump()
    # Change provenance geography to US without setting is_assumption = True
    profile_dict["provenance_catalog"]["SRS_2021_DEMO"]["geography"] = "US"
    profile_dict["provenance_catalog"]["SRS_2021_DEMO"]["is_assumption"] = False

    with pytest.raises(ValueError, match="Geographic mismatch"):
        PopulationProfile.model_validate(profile_dict)


def test_cross_geographic_assumption_allowed():
    profile = load_population_profile(PROFILE_PATH)
    profile_dict = profile.model_dump()
    # If tagged as assumption, cross-geographic borrowing is permitted
    profile_dict["provenance_catalog"]["SRS_2021_DEMO"]["geography"] = "US"
    profile_dict["provenance_catalog"]["SRS_2021_DEMO"]["is_assumption"] = True

    valid_profile = PopulationProfile.model_validate(profile_dict)
    assert valid_profile.provenance_catalog["SRS_2021_DEMO"].is_assumption is True


def test_population_sampler_distribution():
    profile = load_population_profile(PROFILE_PATH)
    rng1 = random.Random(42)
    sampler1 = PopulationSampler(profile, rng1)

    rng2 = random.Random(42)
    sampler2 = PopulationSampler(profile, rng2)

    # 1. Determinism
    ages1 = [sampler1.sample_age() for _ in range(100)]
    ages2 = [sampler2.sample_age() for _ in range(100)]
    assert ages1 == ages2

    # 2. Boundedness
    for a in ages1:
        assert 0 <= a <= 100

    # 3. Sex ratio approx check (N=2000)
    rng = random.Random(12345)
    sampler = PopulationSampler(profile, rng)
    sexes = [sampler.sample_sex() for _ in range(2000)]
    male_count = sexes.count("Male")
    male_prop = male_count / 2000
    # Expected 0.515 +- 0.03
    assert 0.48 <= male_prop <= 0.55

    # 4. Age-dependent condition check
    # Hypertension min_age is 20
    assert sampler.has_condition_at_baseline("I10", age=10, sex="Male") is False

    # 5. Mortality rate lookup
    rate_infant = sampler.get_annual_mortality_rate(age=2, sex="Male")
    rate_elderly = sampler.get_annual_mortality_rate(age=70, sex="Male")
    assert rate_infant == 0.0072
    assert rate_elderly == 0.0385
