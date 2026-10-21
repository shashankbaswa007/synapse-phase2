"""
Patient Profile Generator: Context-aware synthetic patient generation.
Attributes are NOT independent — age constrains conditions, allergies constrain medications,
and scenario requirements override defaults.
"""

import uuid
import random
from typing import List, Optional

from faker import Faker

from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.datagen.models import PatientContext


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

    def __init__(self, knowledge_base: MedicalKnowledgeBase, rng: random.Random):
        self.kb = knowledge_base
        self.rng = rng
        self.fake = Faker()
        Faker.seed(rng.randint(0, 2**31))

    def generate_patient(
        self,
        scenario_id: str = "",
        force_allergy: Optional[str] = None,
        force_age_range: Optional[tuple] = None,
    ) -> PatientContext:
        """Generate a single patient profile with contextual consistency.

        Args:
            scenario_id: Scenario this patient is assigned to.
            force_allergy: Force a specific allergy (e.g., for SCEN-V1-03).
            force_age_range: Override age range (min, max).
        """
        patient_id = f"pat-{uuid.uuid4().hex[:8]}"

        # 1. Generate age
        if force_age_range:
            age = self.rng.randint(force_age_range[0], force_age_range[1])
        else:
            # Realistic age distribution skewed towards working-age adults
            age = self._generate_age()

        # 2. Generate gender
        gender = self.rng.choices(_GENDERS, weights=_GENDER_WEIGHTS, k=1)[0]

        # 3. Generate name (gender-aware)
        if gender == "Male":
            name = self.fake.name_male()
        else:
            name = self.fake.name_female()

        # 4. Generate allergies (prevalence-based, with scenario override)
        allergies = self._generate_allergies(force_allergy)

        # 5. Generate chronic conditions (age-correlated)
        chronic_conditions = self._generate_chronic_conditions(age)

        # 6. Insurance type (weighted random)
        insurance_type = self.rng.choices(_INSURANCE_TYPES, weights=_INSURANCE_WEIGHTS, k=1)[0]

        # 7. Blood group (population distribution)
        blood_group = self.rng.choices(_BLOOD_GROUPS, weights=_BLOOD_WEIGHTS, k=1)[0]

        return PatientContext(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            allergies=allergies,
            chronic_conditions=chronic_conditions,
            insurance_type=insurance_type,
            blood_group=blood_group,
            scenario_id=scenario_id,
        )

    def _generate_age(self) -> int:
        """Generate age with realistic hospital OPD distribution."""
        # Mixture of distributions:
        # 15% pediatric (1-17), 55% adult (18-64), 30% elderly (65-90)
        band = self.rng.random()
        if band < 0.15:
            return self.rng.randint(1, 17)
        elif band < 0.70:
            return self.rng.randint(18, 64)
        else:
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
