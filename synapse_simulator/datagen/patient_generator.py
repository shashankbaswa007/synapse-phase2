"""
Patient Profile Generator: Context-aware synthetic patient generation.
Attributes are NOT independent — age constrains conditions, allergies constrain medications,
and scenario requirements override defaults.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from faker import Faker

from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.core.ids import new_id
from synapse_simulator.population.models import PopulationProfile
from synapse_simulator.population.loader import PopulationSampler


# Insurance distribution weights
_INSURANCE_TYPES = ["General", "Private", "Government", "Corporate", "Self-Pay"]
_INSURANCE_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

# Blood group distribution weights
_BLOOD_GROUPS = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
_BLOOD_WEIGHTS = [0.38, 0.27, 0.22, 0.05, 0.04, 0.02, 0.01, 0.01]

# Gender distribution
_GENDERS = ["Male", "Female"]
_GENDER_WEIGHTS = [0.50, 0.50]


class PatientProfileGenerator:
    """Generates contextually consistent synthetic patient profiles."""

    def __init__(
        self,
        knowledge_base: MedicalKnowledgeBase,
        rng: random.Random,
        population_profile: Optional[PopulationProfile] = None,
    ):
        self.kb = knowledge_base
        self.rng = rng
        self.profile = population_profile
        self.sampler = PopulationSampler(population_profile, rng) if population_profile else None
        self.fake = Faker()
        Faker.seed(rng.randint(0, 2**31))

    def generate_patient(
        self,
        scenario_id: str = "",
        force_allergy: Optional[str] = None,
        force_age_range: Optional[Tuple[int, int]] = None,
        observation_start: Optional[datetime] = None,
    ) -> PatientContext:
        """Generate a single patient profile with contextual consistency.

        Args:
            scenario_id: Scenario this patient is assigned to.
            force_allergy: Force a specific allergy (e.g., for SCEN-V1-03).
            force_age_range: Override age range (min, max).
            observation_start: Simulation observation start timestamp.
        """
        patient_id = new_id("pat-", 8)

        # 1. Generate age
        if force_age_range:
            age = self.rng.randint(force_age_range[0], force_age_range[1])
        elif self.sampler:
            age = self.sampler.sample_age()
        else:
            # Realistic age distribution skewed towards working-age adults
            age = self._generate_age()

        # 2. Generate gender
        if self.sampler:
            gender = self.sampler.sample_sex()
        else:
            gender = self.rng.choices(_GENDERS, weights=_GENDER_WEIGHTS, k=1)[0]

        # 3. Generate name (gender-aware)
        if gender == "Male":
            name = self.fake.name_male()
        else:
            name = self.fake.name_female()

        # 4. Generate allergies (prevalence-based, with scenario override)
        allergies = self._generate_allergies(force_allergy)

        # 5. Longitudinal birth date
        ref_date = observation_start or datetime(2026, 1, 1, 0, 0, 0)
        day_offset = self.rng.randint(0, 364) if self.sampler else 0
        birth_date = ref_date - timedelta(days=int(age * 365.25) + day_offset)

        # 6. Generate chronic conditions (age-correlated) with verified baseline provenance & comorbidity
        baseline_conditions: Dict[str, Dict[str, Any]] = {}
        chronic_conditions = []
        if self.sampler and self.profile and self.profile.prevalences:
            # 1. Diabetes (E11.9) baseline sampling
            has_t2d = False
            t2d_prev = next((p for p in self.profile.prevalences if p.condition_code == "E11.9"), None)
            if t2d_prev and self.sampler.has_condition_at_baseline("E11.9", age, gender):
                has_t2d = True
                chronic_conditions.append(t2d_prev.condition_name)
                years_with_condition = min(max(1.0, (age - 20) * 0.25), 8.0)
                past_days = int(years_with_condition * 365.25) + self.rng.randint(0, 180)
                past_onset = ref_date - timedelta(days=past_days)
                if past_onset < birth_date:
                    past_onset = birth_date + timedelta(days=int(365.25 * min(20, max(1, age // 2))))
                baseline_conditions["E11.9"] = {
                    "condition_code": "E11.9",
                    "condition_name": t2d_prev.condition_name,
                    "onset_date": past_onset,
                    "is_baseline": True,
                    "status": "Active",
                }

            # 2. Hypertension (I10) baseline sampling conditioned on diabetes status
            # ICMR-INDIAB 2023: P(HTN|T2D) = 50.1%, while P(HTN|no T2D) = 28.2% (marginal = 30.7%)
            htn_prev = next((p for p in self.profile.prevalences if p.condition_code == "I10"), None)
            if htn_prev:
                cond_rate = 50.1 if has_t2d else (28.2 if age >= 20 else 0.0)
                if self.sampler.has_condition_at_baseline("I10", age, gender, conditional_rate=cond_rate):
                    chronic_conditions.append(htn_prev.condition_name)
                    years_with_condition = min(max(1.0, (age - 20) * 0.25), 8.0)
                    past_days = int(years_with_condition * 365.25) + self.rng.randint(0, 180)
                    past_onset = ref_date - timedelta(days=past_days)
                    if past_onset < birth_date:
                        past_onset = birth_date + timedelta(days=int(365.25 * min(20, max(1, age // 2))))
                    baseline_conditions["I10"] = {
                        "condition_code": "I10",
                        "condition_name": htn_prev.condition_name,
                        "onset_date": past_onset,
                        "is_baseline": True,
                        "status": "Active",
                    }

            # 3. Any other chronic conditions
            for prev in self.profile.prevalences:
                if prev.condition_code not in ["I10", "E11.9"] and not prev.is_acute:
                    if self.sampler.has_condition_at_baseline(prev.condition_code, age, gender):
                        chronic_conditions.append(prev.condition_name)
                        years_with_condition = min(max(1.0, (age - 20) * 0.25), 8.0)
                        past_days = int(years_with_condition * 365.25) + self.rng.randint(0, 180)
                        past_onset = ref_date - timedelta(days=past_days)
                        if past_onset < birth_date:
                            past_onset = birth_date + timedelta(days=int(365.25 * min(20, max(1, age // 2))))
                        baseline_conditions[prev.condition_code] = {
                            "condition_code": prev.condition_code,
                            "condition_name": prev.condition_name,
                            "onset_date": past_onset,
                            "is_baseline": True,
                            "status": "Active",
                        }
        else:
            chronic_conditions = self._generate_chronic_conditions(age)
            for c_name in chronic_conditions:
                c_code = "I10" if "Hypertension" in c_name else ("E11.9" if "Diabetes" in c_name else "CHRONIC")
                past_onset = ref_date - timedelta(days=int(365.25 * 3))
                if past_onset < birth_date:
                    past_onset = birth_date + timedelta(days=int(365.25 * min(20, max(1, age // 2))))
                baseline_conditions[c_code] = {
                    "condition_code": c_code,
                    "condition_name": c_name,
                    "onset_date": past_onset,
                    "is_baseline": True,
                    "status": "Active",
                }

        # 7. Insurance type (weighted random)
        insurance_type = self.rng.choices(_INSURANCE_TYPES, weights=_INSURANCE_WEIGHTS, k=1)[0]

        # 8. Blood group (population distribution)
        blood_group = self.rng.choices(_BLOOD_GROUPS, weights=_BLOOD_WEIGHTS, k=1)[0]

        return PatientContext(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            allergies=allergies,
            chronic_conditions=chronic_conditions,
            baseline_conditions=baseline_conditions,
            insurance_type=insurance_type,
            blood_group=blood_group,
            scenario_id=scenario_id,
            birth_date=birth_date,
        )

    def _generate_age(self) -> int:
        """Generate age with realistic hospital OPD distribution."""
        # Mixture of distributions:
        # 15% pediatric (1-17), 55% adult (18-64), 30% elderly (65-90)
        band = self.rng.random()
        if band < 0.15:
            return self.rng.randint(1, 17)
        if band < 0.70:
            return self.rng.randint(18, 64)
        return self.rng.randint(65, 90)

    def _generate_allergies(self, force_allergy: Optional[str] = None) -> List[str]:
        """Generate allergies using population prevalence rates."""
        allergies: List[str] = []

        if force_allergy:
            allergies.append(force_allergy)

        for ap in self.kb.allergy_prevalence:
            if ap.name in allergies:
                continue  # Already forced
            if self.rng.random() * 100 < ap.prevalence_percent:
                allergies.append(ap.name)

        return allergies

    def _generate_chronic_conditions(self, age: int) -> List[str]:
        """Generate chronic conditions correlated with patient age."""
        conditions: List[str] = []
        for cc in self.kb.chronic_conditions:
            if age < cc.min_age:
                continue  # Too young for this condition
            if self.rng.random() * 100 < cc.prevalence_percent:
                conditions.append(cc.name)
        return conditions
