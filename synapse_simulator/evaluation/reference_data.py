"""
Reference Data Management Layer for SYNAPSE Phase 2 Evaluation.
Manages empirical real-world reference statistics, provenance verification,
target evaluation populations, eligible denominators, and measurement methodologies.
Separates calibration parameters from internal holdout sub-strata and external evaluation data.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from pydantic import BaseModel, Field

from synapse_simulator.population.models import PopulationProfile, ProvenanceRecord
from synapse_simulator.population.loader import load_population_profile


class BenchmarkRole(str, Enum):
    """Explicit scientific role of an empirical reference statistic."""
    CALIBRATION = "CALIBRATION"                                         # Used to parameterize simulation baseline or transition probabilities
    MODEL_SELECTION = "MODEL_SELECTION"                                 # Used to evaluate architecture or choose structural modeling assumptions
    INTERNAL_VALIDATION_HOLDOUT = "INTERNAL_VALIDATION_HOLDOUT"         # Sub-stratum from same study (e.g. sex/state sub-groups) for internal consistency
    EXTERNAL_INDEPENDENT_EVALUATION = "EXTERNAL_INDEPENDENT_EVALUATION" # Independent empirical study / external data source for unbiased audit


class ReferenceStatistic(BaseModel):
    """Rigorous definition of an empirical real-world reference benchmark."""
    statistic_id: str
    provenance_id: str
    title: str
    publisher: str
    year: int
    source_type: str
    geography: str = "IN"
    url_or_ref: str
    target_dimension: str  # DEMOGRAPHICS, PREVALENCE, INCIDENCE, COMORBIDITY, MORTALITY, LONGITUDINAL, TREATMENT
    condition_code: Optional[str] = None
    population_definition: str
    eligible_min_age: int = 0
    eligible_max_age: int = 120
    eligible_gender: Optional[str] = None
    denominator_definition: str  # "total_patients", "adults_gte_20", "adults_with_t2d_gte_20", "patient_years"
    reference_value: float
    reference_ci_95: Optional[Tuple[float, float]] = None
    is_assumption: bool = False
    sample_size: Optional[int] = None
    measurement_methodology: str = ""
    known_limitations: str = ""
    role: BenchmarkRole = BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION


class EvaluationPopulationMetadata(BaseModel):
    """Metadata describing the target evaluation population."""
    name: str = "India National Representative Synthetic Baseline"
    geography: str = "IN"
    reference_years: List[int] = [2020, 2021, 2022, 2023]
    eligible_age_range: Tuple[int, int] = (0, 100)
    supported_conditions: List[str] = ["I10", "E11.9", "J06.9"]
    observation_period_years: float = 2.0
    known_synthetic_differences: List[str] = Field(default_factory=lambda: [
        "Synthea-style discrete-event simulation model with discrete weekly timesteps.",
        "Closed healthcare facility model: encounters and prescriptions reflect attended clinical care.",
        "Adherence to prescribed therapy is assumed perfect within the simulated cohort.",
        "Baseline chronic conditions are initialized at simulation start for patients above eligibility age."
    ])


class ReferenceCatalog:
    """Central repository of verified reference statistics and evaluation benchmarks."""

    def __init__(self, profile: Optional[PopulationProfile] = None):
        self.profile = profile
        self.metadata = EvaluationPopulationMetadata()
        self.statistics: Dict[str, ReferenceStatistic] = {}
        self._build_catalog()

    def _build_catalog(self) -> None:
        """Populate catalog with empirical benchmarks from population profile and literature."""
        # 1. Demographics: Sex Ratio (Census SRS 2021)
        male_ratio = self.profile.demographics.male_ratio if self.profile else 0.515
        prov_sex = self.profile.demographics.sex_provenance_id if self.profile else "SRS_2021_DEMO"
        self.statistics["demo_sex_male"] = ReferenceStatistic(
            statistic_id="demo_sex_male",
            provenance_id=prov_sex,
            title="Sample Registration System Statistical Report 2021 - Sex Ratio",
            publisher="Office of the Registrar General & Census Commissioner, India",
            year=2021,
            source_type="GOVERNMENT_CENSUS",
            geography="IN",
            url_or_ref="https://censusindia.gov.in/nada/index.php/catalog/44377",
            target_dimension="DEMOGRAPHICS",
            population_definition="All resident individuals in India, all ages",
            eligible_min_age=0,
            eligible_max_age=120,
            denominator_definition="total_patients",
            reference_value=round(male_ratio * 100.0, 2),
            reference_ci_95=(51.2, 51.8),
            measurement_methodology="National annual demographic survey covering ~8.4 million sampled individuals.",
            known_limitations="Reflects natural sex ratio at birth and gender-differential survival in India.",
            role=BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION,
        )

        # 2. Demographics: Age Distribution (SRS 2021 5-Band Pyramid)
        self.statistics["demo_age_pyramid"] = ReferenceStatistic(
            statistic_id="demo_age_pyramid",
            provenance_id="SRS_2021_DEMO",
            title="Sample Registration System Statistical Report 2021 - Age Distribution",
            publisher="Office of the Registrar General & Census Commissioner, India",
            year=2021,
            source_type="GOVERNMENT_CENSUS",
            geography="IN",
            url_or_ref="https://censusindia.gov.in/nada/index.php/catalog/44377",
            target_dimension="DEMOGRAPHICS",
            population_definition="All resident individuals in India across 5 standard census age bands",
            eligible_min_age=0,
            eligible_max_age=120,
            denominator_definition="total_patients",
            reference_value=0.0,
            measurement_methodology="Sample Registration System 2021 abridged age distribution (0-14: 25.2%, 15-24: 17.8%, 25-44: 31.2%, 45-64: 18.8%, 65+: 7.0%).",
            known_limitations="Census 2021 fieldwork was delayed; SRS 2021 estimates are sample-based projections.",
            role=BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION,
        )

        # 3. Demographics: Age-by-Sex Joint Distribution (SRS 2021 Statement 19)
        self.statistics["demo_age_by_sex"] = ReferenceStatistic(
            statistic_id="demo_age_by_sex",
            provenance_id="SRS_2021_DEMO",
            title="SRS Statistical Report 2021 - Statement 19: Population Distribution by Broad Age Groups and Sex",
            publisher="Office of the Registrar General & Census Commissioner, India",
            year=2021,
            source_type="GOVERNMENT_CENSUS",
            geography="IN",
            url_or_ref="https://censusindia.gov.in/nada/index.php/catalog/44377",
            target_dimension="DEMOGRAPHICS",
            population_definition="Joint distribution of age bands by sex for national Indian population",
            eligible_min_age=0,
            eligible_max_age=120,
            denominator_definition="total_patients",
            reference_value=0.0,
            measurement_methodology="SRS 2021 cross-tabulation of age intervals and gender.",
            known_limitations="Aggregated into 5 standard broad intervals.",
            role=BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION,
        )

        # 4. Disease Prevalence: Hypertension (ICMR-INDIAB 2023 - Calibration Target)
        self.statistics["prev_htn_adults"] = ReferenceStatistic(
            statistic_id="prev_htn_adults",
            provenance_id="ICMR_INDIAB_2023_HTN",
            title="Metabolic non-communicable disease health report of India: the ICMR-INDIAB national cross-sectional study",
            publisher="The Lancet Diabetes & Endocrinology",
            year=2023,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=113043,
            url_or_ref="Lancet Diabetes Endocrinol. 2023 Jul;11(7):474-489. doi: 10.1016/S2213-8587(23)00119-5",
            target_dimension="PREVALENCE",
            condition_code="I10",
            population_definition="Adult population of India aged >= 20 years",
            eligible_min_age=20,
            eligible_max_age=120,
            denominator_definition="adults_gte_20",
            reference_value=30.7,
            reference_ci_95=(29.3, 32.1),
            measurement_methodology="Multi-stage cluster sampling across 31 states/UTs; SBP >= 140 or DBP >= 90 mmHg or self-reported medication.",
            known_limitations="Restricted strictly to adults aged >= 20. Denominator must NOT include pediatric patients (0-19).",
            role=BenchmarkRole.CALIBRATION,
        )

        # 5. Disease Incidence: Hypertension Annual Incidence (CURES / CCDC Cohort Studies)
        self.statistics["inc_htn_annual"] = ReferenceStatistic(
            statistic_id="inc_htn_annual",
            provenance_id="CURES_CCDC_HYPERTENSION_INCIDENCE_2014",
            title="Incidence of hypertension and associated risk factors in urban and rural Indian populations: Prospective Cohort Study",
            publisher="Journal of Hypertension",
            year=2014,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=8400,
            url_or_ref="J Hypertens. 2014;32(4):760-768; Prabhakaran et al. JAHA 2017",
            target_dimension="INCIDENCE",
            condition_code="I10",
            population_definition="Normotensive Indian adults aged 20–70 followed longitudinally",
            eligible_min_age=20,
            eligible_max_age=120,
            denominator_definition="patient_years",
            reference_value=0.035,  # 3.5% per year (35 cases per 1,000 person-years)
            reference_ci_95=(0.030, 0.042),
            measurement_methodology="Prospective cohort re-examination every 2 years.",
            known_limitations="Higher in urban than rural areas; pooled rate provides realistic national hazard.",
            role=BenchmarkRole.CALIBRATION,
        )

        # 6. Disease Prevalence: Type 2 Diabetes (ICMR-INDIAB 2023 - Calibration Target)
        self.statistics["prev_t2d_adults"] = ReferenceStatistic(
            statistic_id="prev_t2d_adults",
            provenance_id="ICMR_INDIAB_2023_T2D",
            title="Metabolic non-communicable disease health report of India: the ICMR-INDIAB national cross-sectional study",
            publisher="The Lancet Diabetes & Endocrinology",
            year=2023,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=113043,
            url_or_ref="Lancet Diabetes Endocrinol. 2023 Jul;11(7):474-489. doi: 10.1016/S2213-8587(23)00119-5",
            target_dimension="PREVALENCE",
            condition_code="E11.9",
            population_definition="Adult population of India aged >= 20 years",
            eligible_min_age=20,
            eligible_max_age=120,
            denominator_definition="adults_gte_20",
            reference_value=11.4,
            reference_ci_95=(10.2, 12.5),
            measurement_methodology="OGTT, fasting plasma glucose, or HbA1c >= 6.5% or prior diagnosis.",
            known_limitations="Restricted strictly to adults aged >= 20. Excludes pediatric patients.",
            role=BenchmarkRole.CALIBRATION,
        )

        # 7. Disease Incidence: Type 2 Diabetes Annual Incidence (CARRS Cohort Study)
        self.statistics["inc_t2d_annual"] = ReferenceStatistic(
            statistic_id="inc_t2d_annual",
            provenance_id="CARRS_DIABETES_INCIDENCE_2021",
            title="Incidence of Diabetes in South Asian Adults: The Center for Cardiometabolic Risk Reduction in South Asia (CARRS) Cohort",
            publisher="BMJ Open / Lancet Diabetes Endocrinol",
            year=2021,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=12000,
            url_or_ref="BMJ Open 2021;11:e047468; Lancet Diabetes Endocrinol 2020;8(1):42-51",
            target_dimension="INCIDENCE",
            condition_code="E11.9",
            population_definition="South Asian adults aged >= 20 free of baseline diabetes followed over 2 to 6 years",
            eligible_min_age=20,
            eligible_max_age=120,
            denominator_definition="patient_years",
            reference_value=0.015,  # 1.5% per year (15 cases per 1,000 person-years)
            reference_ci_95=(0.012, 0.018),
            measurement_methodology="Annual blood testing (fasting glucose / HbA1c) in longitudinal cohort.",
            known_limitations="Substantially higher in prediabetes (~5-7%/yr); average across general adult population is ~1.5%/yr.",
            role=BenchmarkRole.CALIBRATION,
        )

        # 8. Internal Validation Holdout: Gender-Stratified Diabetes Prevalences (ICMR-INDIAB 2023)
        self.statistics["prev_t2d_male_subgroup"] = ReferenceStatistic(
            statistic_id="prev_t2d_male_subgroup",
            provenance_id="ICMR_INDIAB_2023_T2D",
            title="ICMR-INDIAB 2023 - Male Subgroup Diabetes Prevalence",
            publisher="The Lancet Diabetes & Endocrinology",
            year=2023,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=53896,
            url_or_ref="Lancet Diabetes Endocrinol. 2023 Jul;11(7):474-489",
            target_dimension="PREVALENCE",
            condition_code="E11.9",
            population_definition="Indian adult males aged >= 20 years",
            eligible_min_age=20,
            eligible_max_age=120,
            eligible_gender="Male",
            denominator_definition="adult_males_gte_20",
            reference_value=12.1,
            reference_ci_95=(10.8, 13.4),
            measurement_methodology="Subgroup stratification by sex from ICMR-INDIAB survey.",
            known_limitations="Internal subgroup holdout from the same study as the national benchmark. Demonstrates subgroup consistency, not external validation.",
            role=BenchmarkRole.INTERNAL_VALIDATION_HOLDOUT,
        )

        self.statistics["prev_t2d_female_subgroup"] = ReferenceStatistic(
            statistic_id="prev_t2d_female_subgroup",
            provenance_id="ICMR_INDIAB_2023_T2D",
            title="ICMR-INDIAB 2023 - Female Subgroup Diabetes Prevalence",
            publisher="The Lancet Diabetes & Endocrinology",
            year=2023,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=59147,
            url_or_ref="Lancet Diabetes Endocrinol. 2023 Jul;11(7):474-489",
            target_dimension="PREVALENCE",
            condition_code="E11.9",
            population_definition="Indian adult females aged >= 20 years",
            eligible_min_age=20,
            eligible_max_age=120,
            eligible_gender="Female",
            denominator_definition="adult_females_gte_20",
            reference_value=10.7,
            reference_ci_95=(9.5, 11.9),
            measurement_methodology="Subgroup stratification by sex from ICMR-INDIAB survey.",
            known_limitations="Internal subgroup holdout from the same study as the national benchmark.",
            role=BenchmarkRole.INTERNAL_VALIDATION_HOLDOUT,
        )

        # 9. Acute URTI: 14-Day Point Prevalence (NHP India 2020)
        self.statistics["prev_urti_14day_point"] = ReferenceStatistic(
            statistic_id="prev_urti_14day_point",
            provenance_id="NHP_INDIA_URTI_2020",
            title="National Health Portal India - Acute Respiratory Infections 14-Day Point Prevalence Baseline",
            publisher="Ministry of Health and Family Welfare, Government of India",
            year=2020,
            source_type="GOVERNMENT_CENSUS",
            geography="IN",
            url_or_ref="https://www.nhp.gov.in/disease/respiratory/upper-respiratory-tract-infection",
            target_dimension="PREVALENCE",
            condition_code="J06.9",
            population_definition="Community population of India, all ages, active within a 14-day recall window",
            eligible_min_age=0,
            eligible_max_age=120,
            denominator_definition="total_patients",
            reference_value=8.5,
            reference_ci_95=(6.5, 11.0),
            measurement_methodology="Active acute respiratory infection episodes within a 14-day survey recall window.",
            known_limitations="Requires filtering for active, non-resolved infection episodes within a 14-day evaluation window.",
            role=BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION,
        )
        self.statistics["prev_urti_all"] = self.statistics["prev_urti_14day_point"]

        # 10. Acute URTI: 2-Year Cumulative Attack Rate (Community Surveillance Baseline)
        self.statistics["prev_urti_cumulative_attack_rate"] = ReferenceStatistic(
            statistic_id="prev_urti_cumulative_attack_rate",
            provenance_id="NHP_INDIA_URTI_2020",
            title="NHP India / Integrated Disease Surveillance Programme (IDSP) - 2-Year Cumulative Attack Rate Baseline",
            publisher="National Centre for Disease Control (NCDC), India",
            year=2020,
            source_type="GOVERNMENT_CENSUS",
            geography="IN",
            url_or_ref="https://idsp.nic.in/",
            target_dimension="PREVALENCE",
            condition_code="J06.9",
            population_definition="Proportion of community individuals experiencing at least one URTI episode over 24 months",
            eligible_min_age=0,
            eligible_max_age=120,
            denominator_definition="total_patients",
            reference_value=70.0,  # 70% cumulative attack rate over 2 years (derived from ~0.45 episodes/pt-year)
            reference_ci_95=(60.0, 80.0),
            measurement_methodology="Cumulative lifetime/period incidence of acute respiratory infection over 2 years.",
            known_limitations="Derived from annual episode frequency (~0.45/yr): 1 - exp(-0.45 * 2) ~ 60%-75%.",
            role=BenchmarkRole.MODEL_SELECTION,
        )

        # 11. Comorbidity: Hypertension co-occurring with Type 2 Diabetes (ICMR-INDIAB 2023)
        self.statistics["comorb_htn_in_t2d"] = ReferenceStatistic(
            statistic_id="comorb_htn_in_t2d",
            provenance_id="ICMR_INDIAB_2023_HTN",
            title="ICMR-INDIAB 2023: Metabolic Comorbidity of Hypertension in Type 2 Diabetes",
            publisher="The Lancet Diabetes & Endocrinology",
            year=2023,
            source_type="PEER_REVIEWED_STUDY",
            geography="IN",
            sample_size=113043,
            url_or_ref="Lancet Diabetes Endocrinol. 2023 Jul;11(7):474-489 (Table 3)",
            target_dimension="COMORBIDITY",
            population_definition="Indian adults aged >= 20 with diagnosed Type 2 Diabetes",
            eligible_min_age=20,
            eligible_max_age=120,
            denominator_definition="adults_with_t2d_gte_20",
            reference_value=50.1,  # 50.1% of diabetic adults have hypertension
            reference_ci_95=(47.5, 52.7),
            measurement_methodology="Subgroup cross-tabulation of blood pressure measurements among diabetic participants.",
            known_limitations="Demonstrates substantial positive clinical clustering (O/E ratio ~ 1.63 relative to independence).",
            role=BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION,
        )

        # 12. Mortality: Annual Crude Mortality Rate (SRS Life Tables 2016-2020)
        self.statistics["mort_crude_rate"] = ReferenceStatistic(
            statistic_id="mort_crude_rate",
            provenance_id="SRS_2016_2020_LIFE_TABLE",
            title="SRS Based Abridged Life Tables 2016-2020 - Crude Mortality Rate",
            publisher="Office of the Registrar General & Census Commissioner, India",
            year=2022,
            source_type="GOVERNMENT_CENSUS",
            geography="IN",
            url_or_ref="Census of India SRS Life Table 2016-20",
            target_dimension="MORTALITY",
            population_definition="Resident population of India, all ages",
            eligible_min_age=0,
            eligible_max_age=120,
            denominator_definition="patient_years",
            reference_value=0.0060,  # 6.0 deaths per 1,000 person-years (0.6%)
            reference_ci_95=(0.0055, 0.0065),
            measurement_methodology="Annual registration of vital events in sampled rural and urban units.",
            known_limitations="Synthetic cohorts may experience stochastic mortality variance over short observation windows.",
            role=BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION,
        )

    def get_statistic(self, stat_id: str) -> Optional[ReferenceStatistic]:
        """Retrieve a reference benchmark by its identifier."""
        return self.statistics.get(stat_id)

    def is_verified(self, stat_id: str) -> bool:
        """Check whether a benchmark is backed by a verified, non-assumption empirical citation."""
        stat = self.statistics.get(stat_id)
        if not stat:
            return False
        return not stat.is_assumption and stat.source_type in ("GOVERNMENT_CENSUS", "PEER_REVIEWED_STUDY", "CLINICAL_GUIDELINE")

    def get_calibration_targets(self) -> Dict[str, ReferenceStatistic]:
        """Return benchmarks strictly designated for model calibration."""
        return {k: v for k, v in self.statistics.items() if v.role == BenchmarkRole.CALIBRATION}

    def get_holdout_targets(self) -> Dict[str, ReferenceStatistic]:
        """Return benchmarks designated for internal holdout validation."""
        return {k: v for k, v in self.statistics.items() if v.role == BenchmarkRole.INTERNAL_VALIDATION_HOLDOUT}

    def get_independent_targets(self) -> Dict[str, ReferenceStatistic]:
        """Return benchmarks designated for external independent evaluation."""
        return {k: v for k, v in self.statistics.items() if v.role == BenchmarkRole.EXTERNAL_INDEPENDENT_EVALUATION}

    def get_age_by_sex_reference_matrix(self) -> Dict[str, Dict[str, float]]:
        """Returns empirical joint distribution P(age_band, sex) from SRS 2021."""
        return {
            "0-14": {"Male": 0.1329, "Female": 0.1191},
            "15-24": {"Male": 0.0937, "Female": 0.0843},
            "25-44": {"Male": 0.1586, "Female": 0.1534},
            "45-64": {"Male": 0.0958, "Female": 0.0922},
            "65-100": {"Male": 0.0340, "Female": 0.0360},
        }


def get_default_reference_catalog(profile_path: Optional[Path] = None) -> ReferenceCatalog:
    """Factory helper to load reference catalog from default or specified population profile."""
    if profile_path and profile_path.exists():
        profile = load_population_profile(profile_path)
    else:
        default_path = Path(__file__).resolve().parent.parent.parent / "config" / "population" / "india_default_v1.yaml"
        profile = load_population_profile(default_path) if default_path.exists() else None
    return ReferenceCatalog(profile=profile)
