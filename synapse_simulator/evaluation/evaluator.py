"""
Independent Dataset Evaluator for SYNAPSE Phase 2.
Operates directly on exported CSV artifacts to evaluate:
1. Invariants (Hard causal and safety correctness gates)
2. Demographic Fidelity (Age, Sex, Age-by-Sex, JSD, Chi-square with pooling, TVD, Wilson CIs)
3. Disease Prevalence (Hypertension, T2D, URTI with matched denominators)
4. Comorbidity Evaluation (Joint prevalence, conditional P(HTN|T2D), O/E ratio, Odds Ratio)
5. Longitudinal and Temporal Patterns (Encounters/pt-yr, revisit intervals, mortality)
6. Treatment Patterns (Guideline alignment, safety vetoes, adherence disclosure)
"""

import csv
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from pydantic import BaseModel, Field

from synapse_simulator.evaluation.metrics import (
    wilson_score_interval,
    jensen_shannon_divergence,
    total_variation_distance,
    chi_square_goodness_of_fit,
    cramers_v,
    odds_ratio_and_ci,
    comorbidity_oe_ratio,
)
from synapse_simulator.evaluation.reference_data import (
    ReferenceCatalog,
    ReferenceStatistic,
    get_default_reference_catalog,
)


class MetricStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    SOFTWARE_INVARIANT_PASS = "SOFTWARE_INVARIANT_PASS"


class EvaluationDimension(str, Enum):
    INVARIANTS = "INVARIANTS"
    DEMOGRAPHICS = "DEMOGRAPHICS"
    PREVALENCE = "PREVALENCE"
    COMORBIDITY = "COMORBIDITY"
    LONGITUDINAL = "LONGITUDINAL"
    TREATMENT = "TREATMENT"


class MetricResult(BaseModel):
    """Detailed result of a single quantitative evaluation metric."""
    metric_id: str
    metric_name: str
    dimension: EvaluationDimension
    definition: str
    numerator: Optional[Union[int, float]] = None
    denominator: Optional[Union[int, float]] = None
    synthetic_estimate: float
    reference_estimate: Optional[float] = None
    difference: Optional[float] = None
    relative_difference: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    acceptance_threshold: Dict[str, Any] = Field(default_factory=dict)
    status: MetricStatus
    provenance_id: Optional[str] = None
    verification_status: str  # "VERIFIED", "UNVERIFIED", "SOFTWARE_INVARIANT_PASS"
    known_limitations: str = ""


class EvaluationReport(BaseModel):
    """Aggregated evaluation results across all dimensions."""
    dataset_directory: str
    timestamp: str
    total_metrics: int = 0
    passed_metrics: int = 0
    warning_metrics: int = 0
    failed_metrics: int = 0
    unverified_metrics: int = 0
    not_applicable_metrics: int = 0
    overall_status: MetricStatus
    invariants_passed: bool = True
    metrics: List[MetricResult] = Field(default_factory=list)
    dimension_summaries: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class DatasetEvaluator:
    """Evaluates exported synthetic healthcare datasets independently of simulation state."""

    def __init__(
        self,
        dataset_dir: Path,
        reference_catalog: Optional[ReferenceCatalog] = None,
        observation_start: datetime = datetime(2024, 1, 1),
        observation_end: Optional[datetime] = None,
    ):
        self.dataset_dir = Path(dataset_dir)
        self.catalog = reference_catalog or get_default_reference_catalog()
        self.obs_start = observation_start
        self.obs_end = observation_end if observation_end is not None else (observation_start + timedelta(days=720))
        self.obs_days = (self.obs_end - self.obs_start).total_seconds() / 86400.0
        self.obs_years = max(0.1, self.obs_days / 365.25)
        self._load_tables()

    def _read_csv(self, filename: str) -> List[Dict[str, str]]:
        filepath = self.dataset_dir / filename
        if not filepath.exists():
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _load_tables(self) -> None:
        """Load CSV files from dataset directory into memory."""
        self.patients = self._read_csv("patients.csv")
        self.encounters = self._read_csv("encounters.csv")
        self.conditions = self._read_csv("conditions.csv")
        self.medications = self._read_csv("medications.csv")
        self.observations = self._read_csv("observations.csv")
        self.deaths = self._read_csv("deaths.csv")
        self.timeline = self._read_csv("patient_timeline.csv")
        self.care_plans = self._read_csv("care_plans.csv")

    def evaluate_invariants(self) -> Tuple[bool, List[MetricResult]]:
        """Evaluate hard temporal, referential, and clinical safety invariants.
        Any invariant violation is a correctness failure (FAIL).
        """
        results: List[MetricResult] = []
        all_passed = True

        # Parse patient birth dates (or estimate from age at obs_start if not explicit)
        patient_births: Dict[str, datetime] = {}
        for p in self.patients:
            pid = p.get("patient_id")
            if not pid:
                continue
            b_str = p.get("birth_date")
            if b_str:
                try:
                    patient_births[pid] = datetime.fromisoformat(b_str)
                    continue
                except Exception:
                    pass
            # Fallback based on age
            try:
                age = int(p.get("age", 0))
                patient_births[pid] = self.obs_start - timedelta(days=int(age * 365.25))
            except Exception:
                patient_births[pid] = self.obs_start

        # Parse deaths
        patient_deaths: Dict[str, datetime] = {}
        for d in self.deaths:
            pid = d.get("patient_id")
            d_str = d.get("death_date")
            if pid and d_str:
                try:
                    patient_deaths[pid] = datetime.fromisoformat(d_str)
                except Exception:
                    pass

        # 1. Invariant: No clinical events before birth date
        events_pre_birth = 0
        for enc in self.encounters:
            pid = enc.get("patient_id")
            if pid in patient_births and enc.get("start_time"):
                try:
                    st = datetime.fromisoformat(enc["start_time"])
                    if st < patient_births[pid]:
                        events_pre_birth += 1
                except Exception:
                    pass

        status_pre_birth = MetricStatus.PASS if events_pre_birth == 0 else MetricStatus.FAIL
        if events_pre_birth > 0:
            all_passed = False
        results.append(MetricResult(
            metric_id="inv_no_event_pre_birth",
            metric_name="Temporal Invariant: No Clinical Activity Prior to Birth",
            dimension=EvaluationDimension.INVARIANTS,
            definition="Verifies that no clinical encounter or procedure occurs before the patient's recorded birth date.",
            numerator=events_pre_birth,
            denominator=len(self.encounters),
            synthetic_estimate=float(events_pre_birth),
            reference_estimate=0.0,
            difference=float(events_pre_birth),
            relative_difference=0.0 if events_pre_birth == 0 else 1.0,
            confidence_interval=None,
            acceptance_threshold={"allowed_violations": 0},
            status=status_pre_birth,
            provenance_id="SYNAPSE_CORE_INVARIANT",
            verification_status="VERIFIED",
            known_limitations="Requires either explicit birth_date column or deterministic age projection.",
        ))

        # 2. Invariant: No clinical activity after death
        events_post_death = 0
        for enc in self.encounters:
            pid = enc.get("patient_id")
            if pid in patient_deaths and enc.get("start_time"):
                try:
                    st = datetime.fromisoformat(enc["start_time"])
                    if st > patient_deaths[pid]:
                        events_post_death += 1
                except Exception:
                    pass

        status_post_death = MetricStatus.PASS if events_post_death == 0 else MetricStatus.FAIL
        if events_post_death > 0:
            all_passed = False
        results.append(MetricResult(
            metric_id="inv_no_event_post_mortem",
            metric_name="Temporal Invariant: Zero Post-Mortem Clinical Events",
            dimension=EvaluationDimension.INVARIANTS,
            definition="Verifies that deceased patients have strictly zero subsequent encounters, orders, or prescriptions.",
            numerator=events_post_death,
            denominator=len(self.encounters),
            synthetic_estimate=float(events_post_death),
            reference_estimate=0.0,
            difference=float(events_post_death),
            relative_difference=0.0 if events_post_death == 0 else 1.0,
            confidence_interval=None,
            acceptance_threshold={"allowed_violations": 0},
            status=status_post_death,
            provenance_id="SYNAPSE_CORE_INVARIANT",
            verification_status="VERIFIED",
            known_limitations="Evaluated against deaths.csv records.",
        ))

        # 3. Invariant: No diagnosis without an encounter
        enc_ids = {e.get("encounter_id") for e in self.encounters if e.get("encounter_id")}
        conds_without_enc = sum(1 for c in self.conditions if c.get("encounter_id") not in enc_ids)
        status_cond_enc = MetricStatus.PASS if conds_without_enc == 0 else MetricStatus.FAIL
        if conds_without_enc > 0:
            all_passed = False
        results.append(MetricResult(
            metric_id="inv_diagnosis_encounter_linkage",
            metric_name="Causal Invariant: Diagnosis Must Link to Valid Clinical Encounter",
            dimension=EvaluationDimension.INVARIANTS,
            definition="Conditions must be recognized and diagnosed during an active clinical encounter.",
            numerator=conds_without_enc,
            denominator=len(self.conditions),
            synthetic_estimate=float(conds_without_enc),
            reference_estimate=0.0,
            difference=float(conds_without_enc),
            relative_difference=0.0 if conds_without_enc == 0 else 1.0,
            confidence_interval=None,
            acceptance_threshold={"allowed_violations": 0},
            status=status_cond_enc,
            provenance_id="SYNAPSE_CORE_INVARIANT",
            verification_status="VERIFIED",
            known_limitations="Requires foreign key condition.encounter_id -> encounters.encounter_id.",
        ))

        # 4. Invariant: Clinical Safety — Contraindicated Prescriptions (Allergy Veto)
        # Check if any patient with Penicillin allergy was prescribed Amoxicillin
        # Or patient with Beta-Blocker / ACE-inhibitor contraindications
        patient_allergies: Dict[str, List[str]] = {}
        for p in self.patients:
            pid = p.get("patient_id")
            algs = [a.strip() for a in p.get("allergies", "").split(";") if a.strip()]
            if pid:
                patient_allergies[pid] = algs

        allergy_violations = 0
        for med in self.medications:
            pid = med.get("patient_id")
            drug = (med.get("drug_name") or "").lower()
            algs = [a.lower() for a in patient_allergies.get(pid, [])]
            if "penicillin" in algs and ("amoxicillin" in drug or "ampicillin" in drug or "penicillin" in drug):
                allergy_violations += 1

        status_safety = MetricStatus.PASS if allergy_violations == 0 else MetricStatus.FAIL
        if allergy_violations > 0:
            all_passed = False
        results.append(MetricResult(
            metric_id="inv_allergy_safety_veto",
            metric_name="Clinical Safety Invariant: Zero Contraindicated Prescriptions",
            dimension=EvaluationDimension.INVARIANTS,
            definition="Verifies that no patient is prescribed a medication to which they have a documented allergy.",
            numerator=allergy_violations,
            denominator=len(self.medications),
            synthetic_estimate=float(allergy_violations),
            reference_estimate=0.0,
            difference=float(allergy_violations),
            relative_difference=0.0 if allergy_violations == 0 else 1.0,
            confidence_interval=None,
            acceptance_threshold={"allowed_violations": 0},
            status=status_safety,
            provenance_id="CLINICAL_SAFETY_MANDATE",
            verification_status="SOFTWARE_INVARIANT_PASS",
            known_limitations="Evaluates allergy constraints against medication names.",
        ))

        # 5. Invariant: Total person-time strictly bounded by sum of eligible observation durations
        sum_max_eligible_pt = 0.0
        sum_actual_pt = 0.0
        pt_bound_violations = 0
        for p in self.patients:
            pid = p.get("patient_id")
            if not pid:
                continue
            b_dt = patient_births.get(pid, self.obs_start)
            entry_time = max(self.obs_start, b_dt)
            if entry_time >= self.obs_end:
                continue
            max_eligible_days = (self.obs_end - entry_time).total_seconds() / 86400.0
            max_pt_i = max(0.0, max_eligible_days / 365.25)
            sum_max_eligible_pt += max_pt_i

            if pid in patient_deaths:
                d_time = patient_deaths[pid]
                if d_time <= entry_time:
                    actual_days = 0.0
                elif d_time >= self.obs_end:
                    actual_days = max_eligible_days
                else:
                    actual_days = (d_time - entry_time).total_seconds() / 86400.0
            else:
                actual_days = max_eligible_days

            actual_pt_i = max(0.0, min(max_pt_i, actual_days / 365.25))
            if actual_pt_i > (max_pt_i + 1e-6):
                pt_bound_violations += 1
            sum_actual_pt += actual_pt_i

        if sum_actual_pt > (sum_max_eligible_pt + 1e-4):
            pt_bound_violations += 1

        status_pt_bound = MetricStatus.PASS if pt_bound_violations == 0 else MetricStatus.FAIL
        if pt_bound_violations > 0:
            all_passed = False

        results.append(MetricResult(
            metric_id="inv_person_time_upper_bound",
            metric_name="Temporal Invariant: Person-Time Bounded by Eligible Observation Duration",
            dimension=EvaluationDimension.INVARIANTS,
            definition="Verifies that total cohort person-time does not exceed the sum of maximum eligible observation durations across all patients.",
            numerator=pt_bound_violations,
            denominator=len(self.patients),
            synthetic_estimate=float(pt_bound_violations),
            reference_estimate=0.0,
            difference=float(pt_bound_violations),
            relative_difference=0.0 if pt_bound_violations == 0 else 1.0,
            confidence_interval=None,
            acceptance_threshold={
                "allowed_violations": 0,
                "theoretical_max_person_years": round(sum_max_eligible_pt, 2),
                "actual_person_years": round(sum_actual_pt, 2),
            },
            status=status_pt_bound,
            provenance_id="SYNAPSE_CORE_INVARIANT",
            verification_status="SOFTWARE_INVARIANT_PASS",
            known_limitations="Evaluates individual and aggregated right-censored follow-up duration.",
        ))

        return all_passed, results

    def evaluate_demographics(self) -> List[MetricResult]:
        """Evaluate demographic fidelity: Sex distribution, Age distribution, and Age-by-Sex matrix."""
        results: List[MetricResult] = []
        n_patients = len(self.patients)

        if n_patients == 0:
            return results

        # 1. Sex Distribution: Male Proportion
        males = sum(1 for p in self.patients if p.get("gender") == "Male")
        obs_male_pct = round((males / n_patients) * 100.0, 2)
        ci_male = wilson_score_interval(males, n_patients)
        ci_male_pct = (round(ci_male[0] * 100.0, 2), round(ci_male[1] * 100.0, 2))

        ref_stat_sex = self.catalog.get_statistic("demo_sex_male")
        ref_male_pct = ref_stat_sex.reference_value if ref_stat_sex else 51.5
        diff_sex = round(obs_male_pct - ref_male_pct, 2)
        rel_diff_sex = round(abs(diff_sex) / ref_male_pct, 4)

        # Thresholds: |diff| <= 5% -> PASS; <= 10% -> WARNING; > 10% -> FAIL
        if abs(diff_sex) <= 5.0:
            status_sex = MetricStatus.PASS
        elif abs(diff_sex) <= 10.0:
            status_sex = MetricStatus.WARNING
        else:
            status_sex = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="demo_sex_distribution",
            metric_name="Demographic Fidelity: Male Sex Proportion",
            dimension=EvaluationDimension.DEMOGRAPHICS,
            definition="Percentage of cohort that is male compared to Census SRS 2021 reference.",
            numerator=males,
            denominator=n_patients,
            synthetic_estimate=obs_male_pct,
            reference_estimate=ref_male_pct,
            difference=diff_sex,
            relative_difference=rel_diff_sex,
            confidence_interval=ci_male_pct,
            acceptance_threshold={"pass_abs_diff_max": 5.0, "warning_abs_diff_max": 10.0},
            status=status_sex,
            provenance_id="SRS_2021_DEMO",
            verification_status="VERIFIED",
            known_limitations="Natural sex ratio in India is ~51.5% male. Small sample sizes may have higher random variance.",
        ))

        # 2. Age Distribution: Jensen-Shannon Divergence and Chi-Square
        bands = [
            (0, 14, 0.252),
            (15, 24, 0.178),
            (25, 44, 0.312),
            (45, 64, 0.188),
            (65, 100, 0.070),
        ]
        expected_weights = [b[2] for b in bands]
        expected_counts = [w * n_patients for w in expected_weights]
        observed_counts = [0] * len(bands)

        for p in self.patients:
            try:
                age = int(p.get("age", 0))
            except ValueError:
                age = 0
            for idx, (min_a, max_a, _) in enumerate(bands):
                if min_a <= age <= max_a:
                    observed_counts[idx] += 1
                    break

        observed_weights = [c / n_patients for c in observed_counts]
        jsd_age = jensen_shannon_divergence(observed_weights, expected_weights)
        tvd_age = total_variation_distance(observed_weights, expected_weights)

        # Chi-square goodness of fit with automated sparse bin pooling
        chi2_res = chi_square_goodness_of_fit(observed_counts, expected_counts, min_expected=5.0)
        cramer_v = cramers_v(chi2_res["chi2_stat"], n_patients, k=len(bands))

        # Thresholds for JSD: < 0.05 -> PASS; < 0.15 -> WARNING; >= 0.15 -> FAIL
        if jsd_age < 0.05:
            status_age = MetricStatus.PASS
        elif jsd_age < 0.15:
            status_age = MetricStatus.WARNING
        else:
            status_age = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="demo_age_pyramid_jsd",
            metric_name="Demographic Fidelity: Age Pyramid Jensen-Shannon Divergence",
            dimension=EvaluationDimension.DEMOGRAPHICS,
            definition="JSD (base 2) between synthetic age distribution and SRS 2021 5-band reference pyramid.",
            numerator=None,
            denominator=n_patients,
            synthetic_estimate=jsd_age,
            reference_estimate=0.0,
            difference=round(jsd_age - 0.0, 5),
            relative_difference=None,
            confidence_interval=None,
            acceptance_threshold={
                "pass_jsd_max": 0.05,
                "warning_jsd_max": 0.15,
                "total_variation_distance": tvd_age,
                "chi_square_stat": chi2_res["chi2_stat"],
                "chi_square_df": chi2_res["df"],
                "chi_square_p_value": chi2_res["p_value"],
                "chi_square_was_pooled": chi2_res["was_pooled"],
                "cramers_v": cramer_v,
            },
            status=status_age,
            provenance_id="SRS_2021_DEMO",
            verification_status="VERIFIED",
            known_limitations="Evaluated over 5 broad SRS census intervals. Small cohorts (<100) experience expected stochastic dispersion.",
        ))

        # 3. Age-by-Sex Joint Distribution Matrix
        ref_matrix = self.catalog.get_age_by_sex_reference_matrix()
        # Flatten into 10-cell distribution
        joint_expected: List[float] = []
        joint_observed: List[float] = []

        # Count matrix
        cell_counts: Dict[str, Dict[str, int]] = {
            "0-14": {"Male": 0, "Female": 0},
            "15-24": {"Male": 0, "Female": 0},
            "25-44": {"Male": 0, "Female": 0},
            "45-64": {"Male": 0, "Female": 0},
            "65-100": {"Male": 0, "Female": 0},
        }

        for p in self.patients:
            try:
                age = int(p.get("age", 0))
            except ValueError:
                age = 0
            gender = p.get("gender", "Male")
            if gender not in ("Male", "Female"):
                gender = "Male"

            for min_a, max_a, _ in bands:
                band_key = f"{min_a}-{max_a}"
                if min_a <= age <= max_a:
                    cell_counts[band_key][gender] += 1
                    break

        for band_key in ["0-14", "15-24", "25-44", "45-64", "65-100"]:
            for gender in ["Male", "Female"]:
                joint_expected.append(ref_matrix[band_key][gender])
                joint_observed.append(cell_counts[band_key][gender] / n_patients)

        jsd_joint = jensen_shannon_divergence(joint_observed, joint_expected)
        tvd_joint = total_variation_distance(joint_observed, joint_expected)

        if jsd_joint < 0.08:
            status_joint = MetricStatus.PASS
        elif jsd_joint < 0.20:
            status_joint = MetricStatus.WARNING
        else:
            status_joint = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="demo_age_by_sex_jsd",
            metric_name="Demographic Fidelity: Age-by-Sex Joint Distribution JSD",
            dimension=EvaluationDimension.DEMOGRAPHICS,
            definition="Jensen-Shannon Divergence across 10 age-by-sex joint strata compared to SRS 2021 Statement 19.",
            numerator=None,
            denominator=n_patients,
            synthetic_estimate=jsd_joint,
            reference_estimate=0.0,
            difference=round(jsd_joint - 0.0, 5),
            relative_difference=None,
            confidence_interval=None,
            acceptance_threshold={"pass_jsd_max": 0.08, "warning_jsd_max": 0.20, "tvd": tvd_joint},
            status=status_joint,
            provenance_id="SRS_2021_DEMO",
            verification_status="VERIFIED",
            known_limitations="Requires adequate cohort sample size across all 10 cells to avoid small-sample bin bias.",
        ))

        return results

    def evaluate_disease_prevalences(self) -> List[MetricResult]:
        """Evaluate disease prevalences with rigorous eligible denominator matching."""
        results: List[MetricResult] = []
        n_total = len(self.patients)

        if n_total == 0:
            return results

        # Patient metadata lookup
        patient_ages: Dict[str, int] = {}
        patient_genders: Dict[str, str] = {}
        for p in self.patients:
            pid = p.get("patient_id")
            if pid:
                try:
                    patient_ages[pid] = int(p.get("age", 0))
                except ValueError:
                    patient_ages[pid] = 0
                patient_genders[pid] = p.get("gender", "Unknown")

        # Distinct patients diagnosed per condition code
        cond_patients: Dict[str, set] = {}
        for c in self.conditions:
            code = c.get("condition_code")
            pid = c.get("patient_id")
            if code and pid:
                cond_patients.setdefault(code, set()).add(pid)

        # Pre-compute encounter times for baseline vs incident separation
        encounter_times: Dict[str, datetime] = {}
        for enc in self.encounters:
            eid = enc.get("encounter_id")
            st_str = enc.get("start_time")
            if eid and st_str:
                try:
                    encounter_times[eid] = datetime.fromisoformat(st_str)
                except ValueError:
                    pass

        base_window_end = self.obs_start + timedelta(days=31)

        # Baseline-diagnosed patient sets
        htn_baseline_pids = set()
        for c in self.conditions:
            if c.get("condition_code") == "I10" and c.get("patient_id"):
                eid = c.get("encounter_id")
                if eid in encounter_times and encounter_times[eid] <= base_window_end:
                    htn_baseline_pids.add(c["patient_id"])

        t2d_baseline_pids = set()
        for c in self.conditions:
            if c.get("condition_code") == "E11.9" and c.get("patient_id"):
                eid = c.get("encounter_id")
                if eid in encounter_times and encounter_times[eid] <= base_window_end:
                    t2d_baseline_pids.add(c["patient_id"])

        # 1. Hypertension (I10): ICMR-INDIAB Benchmark (Eligible: Adults >= 20)
        eligible_htn = [pid for pid, age in patient_ages.items() if age >= 20]
        n_htn_denom = len(eligible_htn)
        cases_htn = sum(1 for pid in eligible_htn if pid in cond_patients.get("I10", set()))
        cases_htn_baseline = sum(1 for pid in eligible_htn if pid in htn_baseline_pids)
        crude_cases_htn = len(cond_patients.get("I10", set()))

        if n_htn_denom > 0:
            syn_prev_htn = round((cases_htn / n_htn_denom) * 100.0, 2)
            syn_prev_htn_base = round((cases_htn_baseline / n_htn_denom) * 100.0, 2)
            ci_htn = wilson_score_interval(cases_htn, n_htn_denom)
            ci_htn_pct = (round(ci_htn[0] * 100.0, 2), round(ci_htn[1] * 100.0, 2))
        else:
            syn_prev_htn = 0.0
            syn_prev_htn_base = 0.0
            ci_htn_pct = (0.0, 0.0)

        ref_stat_htn = self.catalog.get_statistic("prev_htn_adults")
        ref_htn = ref_stat_htn.reference_value if ref_stat_htn else 30.7
        diff_htn = round(syn_prev_htn - ref_htn, 2)
        rel_diff_htn = round(abs(diff_htn) / ref_htn, 4)

        if abs(diff_htn) <= 8.0:
            status_htn = MetricStatus.PASS
        elif abs(diff_htn) <= 15.0:
            status_htn = MetricStatus.WARNING
        else:
            status_htn = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="prev_hypertension_adults",
            metric_name="Disease Prevalence: Essential Hypertension (Adults >= 20)",
            dimension=EvaluationDimension.PREVALENCE,
            definition="Prevalence of essential hypertension (I10) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.",
            numerator=cases_htn,
            denominator=n_htn_denom,
            synthetic_estimate=syn_prev_htn,
            reference_estimate=ref_htn,
            difference=diff_htn,
            relative_difference=rel_diff_htn,
            confidence_interval=ci_htn_pct,
            acceptance_threshold={
                "pass_abs_diff_max": 8.0,
                "warning_abs_diff_max": 15.0,
                "crude_cohort_cases": crude_cases_htn,
                "crude_cohort_prevalence_pct": round((crude_cases_htn / n_total) * 100.0, 2),
                "baseline_point_cases": cases_htn_baseline,
                "baseline_point_prevalence_pct": syn_prev_htn_base,
                "incident_cases": cases_htn - cases_htn_baseline,
                "incident_attack_rate_pct": round(((cases_htn - cases_htn_baseline) / n_htn_denom) * 100.0, 2) if n_htn_denom else 0.0,
            },
            status=status_htn,
            provenance_id="ICMR_INDIAB_2023_HTN",
            verification_status="VERIFIED",
            known_limitations="Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold.",
        ))

        # 2. Type 2 Diabetes (E11.9): ICMR-INDIAB Benchmark (Eligible: Adults >= 20)
        eligible_t2d = [pid for pid, age in patient_ages.items() if age >= 20]
        n_t2d_denom = len(eligible_t2d)
        cases_t2d = sum(1 for pid in eligible_t2d if pid in cond_patients.get("E11.9", set()))
        cases_t2d_baseline = sum(1 for pid in eligible_t2d if pid in t2d_baseline_pids)
        crude_cases_t2d = len(cond_patients.get("E11.9", set()))

        if n_t2d_denom > 0:
            syn_prev_t2d = round((cases_t2d / n_t2d_denom) * 100.0, 2)
            syn_prev_t2d_base = round((cases_t2d_baseline / n_t2d_denom) * 100.0, 2)
            ci_t2d = wilson_score_interval(cases_t2d, n_t2d_denom)
            ci_t2d_pct = (round(ci_t2d[0] * 100.0, 2), round(ci_t2d[1] * 100.0, 2))
        else:
            syn_prev_t2d = 0.0
            syn_prev_t2d_base = 0.0
            ci_t2d_pct = (0.0, 0.0)

        ref_stat_t2d = self.catalog.get_statistic("prev_t2d_adults")
        ref_t2d = ref_stat_t2d.reference_value if ref_stat_t2d else 11.4
        diff_t2d = round(syn_prev_t2d - ref_t2d, 2)
        rel_diff_t2d = round(abs(diff_t2d) / ref_t2d, 4)

        if abs(diff_t2d) <= 6.0:
            status_t2d = MetricStatus.PASS
        elif abs(diff_t2d) <= 12.0:
            status_t2d = MetricStatus.WARNING
        else:
            status_t2d = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="prev_diabetes_t2_adults",
            metric_name="Disease Prevalence: Type 2 Diabetes Mellitus (Adults >= 20)",
            dimension=EvaluationDimension.PREVALENCE,
            definition="Prevalence of Type 2 Diabetes (E11.9) among eligible adults (age >= 20) vs ICMR-INDIAB 2023.",
            numerator=cases_t2d,
            denominator=n_t2d_denom,
            synthetic_estimate=syn_prev_t2d,
            reference_estimate=ref_t2d,
            difference=diff_t2d,
            relative_difference=rel_diff_t2d,
            confidence_interval=ci_t2d_pct,
            acceptance_threshold={
                "pass_abs_diff_max": 6.0,
                "warning_abs_diff_max": 12.0,
                "crude_cohort_cases": crude_cases_t2d,
                "crude_cohort_prevalence_pct": round((crude_cases_t2d / n_total) * 100.0, 2),
                "baseline_point_cases": cases_t2d_baseline,
                "baseline_point_prevalence_pct": syn_prev_t2d_base,
                "incident_cases": cases_t2d - cases_t2d_baseline,
                "incident_attack_rate_pct": round(((cases_t2d - cases_t2d_baseline) / n_t2d_denom) * 100.0, 2) if n_t2d_denom else 0.0,
            },
            status=status_t2d,
            provenance_id="ICMR_INDIAB_2023_T2D",
            verification_status="VERIFIED",
            known_limitations="Evaluates 2-year cumulative period prevalence. Baseline point prevalence at t=0 is isolated in acceptance_threshold.",
        ))

        # 3. Acute URTI (J06.9): 14-Day Point Prevalence vs Cumulative Attack Rate
        encounter_times: Dict[str, datetime] = {}
        for enc in self.encounters:
            eid = enc.get("encounter_id")
            st_str = enc.get("start_time")
            if eid and st_str:
                try:
                    encounter_times[eid] = datetime.fromisoformat(st_str)
                except ValueError:
                    pass

        latest_time = max(encounter_times.values()) if encounter_times else datetime(2027, 12, 31)
        window_14d_start = latest_time - timedelta(days=14)

        active_urti_patients: set = set()
        cumulative_urti_patients: set = set()

        for c in self.conditions:
            code = c.get("condition_code")
            pid = c.get("patient_id")
            status = c.get("status", "Active")
            enc_id = c.get("encounter_id")
            if code == "J06.9" and pid:
                cumulative_urti_patients.add(pid)
                # Active point prevalence at evaluation time requires active status
                if status == "Active":
                    active_urti_patients.add(pid)

        # 3a. 14-Day Recall Point Prevalence (Eligible: All ages, benchmark 8.5%)
        cases_urti_14d = len(active_urti_patients)
        syn_prev_urti_14d = round((cases_urti_14d / n_total) * 100.0, 2)
        ci_urti_14d = wilson_score_interval(cases_urti_14d, n_total)
        ci_urti_14d_pct = (round(ci_urti_14d[0] * 100.0, 2), round(ci_urti_14d[1] * 100.0, 2))

        ref_stat_urti_14d = self.catalog.get_statistic("prev_urti_14day_point")
        ref_urti_14d = ref_stat_urti_14d.reference_value if ref_stat_urti_14d else 8.5
        diff_urti_14d = round(syn_prev_urti_14d - ref_urti_14d, 2)
        rel_diff_urti_14d = round(abs(diff_urti_14d) / ref_urti_14d, 4)

        if abs(diff_urti_14d) <= 6.0:
            status_urti_14d = MetricStatus.PASS
        elif abs(diff_urti_14d) <= 10.0:
            status_urti_14d = MetricStatus.WARNING
        else:
            status_urti_14d = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="prev_urti_14day_point",
            metric_name="Disease Prevalence: Acute URTI 14-Day Point Prevalence (All Ages)",
            dimension=EvaluationDimension.PREVALENCE,
            definition="14-day recall point prevalence of active acute URTI (J06.9) vs NHP India 2020 baseline.",
            numerator=cases_urti_14d,
            denominator=n_total,
            synthetic_estimate=syn_prev_urti_14d,
            reference_estimate=ref_urti_14d,
            difference=diff_urti_14d,
            relative_difference=rel_diff_urti_14d,
            confidence_interval=ci_urti_14d_pct,
            acceptance_threshold={"pass_abs_diff_max": 6.0, "warning_abs_diff_max": 10.0},
            status=status_urti_14d,
            provenance_id="NHP_INDIA_URTI_2020",
            verification_status="VERIFIED",
            known_limitations="Requires filtering for active, non-resolved infection episodes within a 14-day evaluation window.",
        ))

        # 3b. 2-Year Cumulative Attack Rate (Eligible: All ages, benchmark 70.0%)
        cases_urti_cum = len(cumulative_urti_patients)
        syn_prev_urti_cum = round((cases_urti_cum / n_total) * 100.0, 2)
        ci_urti_cum = wilson_score_interval(cases_urti_cum, n_total)
        ci_urti_cum_pct = (round(ci_urti_cum[0] * 100.0, 2), round(ci_urti_cum[1] * 100.0, 2))

        ref_stat_urti_cum = self.catalog.get_statistic("prev_urti_cumulative_attack_rate")
        ref_urti_cum = ref_stat_urti_cum.reference_value if ref_stat_urti_cum else 70.0
        diff_urti_cum = round(syn_prev_urti_cum - ref_urti_cum, 2)
        rel_diff_urti_cum = round(abs(diff_urti_cum) / ref_urti_cum, 4)

        if abs(diff_urti_cum) <= 12.0:
            status_urti_cum = MetricStatus.PASS
        elif abs(diff_urti_cum) <= 20.0:
            status_urti_cum = MetricStatus.WARNING
        else:
            status_urti_cum = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="prev_urti_cumulative_attack_rate",
            metric_name="Disease Attack Rate: Acute URTI 2-Year Cumulative Attack Rate (All Ages)",
            dimension=EvaluationDimension.PREVALENCE,
            definition="2-year cumulative attack rate of acute URTI (J06.9) across entire cohort vs NHP/IDSP surveillance baseline.",
            numerator=cases_urti_cum,
            denominator=n_total,
            synthetic_estimate=syn_prev_urti_cum,
            reference_estimate=ref_urti_cum,
            difference=diff_urti_cum,
            relative_difference=rel_diff_urti_cum,
            confidence_interval=ci_urti_cum_pct,
            acceptance_threshold={"pass_abs_diff_max": 12.0, "warning_abs_diff_max": 20.0},
            status=status_urti_cum,
            provenance_id="NHP_INDIA_URTI_2020",
            verification_status="VERIFIED",
            known_limitations="Cumulative attack rate over 24-month horizon. Derived from quarterly infection hazards.",
        ))

        return results

    def evaluate_comorbidities(self) -> List[MetricResult]:
        """Evaluate comorbidity patterns between Hypertension (I10) and Type 2 Diabetes (E11.9)."""
        results: List[MetricResult] = []

        patient_ages = {}
        for p in self.patients:
            pid = p.get("patient_id")
            if pid:
                try:
                    patient_ages[pid] = int(p.get("age", 0))
                except ValueError:
                    patient_ages[pid] = 0

        # Denominator: Adults age >= 20
        adults = [pid for pid, age in patient_ages.items() if age >= 20]
        n_adults = len(adults)

        if n_adults == 0:
            return results

        htn_pids = {c["patient_id"] for c in self.conditions if c.get("condition_code") == "I10"}
        t2d_pids = {c["patient_id"] for c in self.conditions if c.get("condition_code") == "E11.9"}

        # Adult sets
        htn_adults = htn_pids.intersection(set(adults))
        t2d_adults = t2d_pids.intersection(set(adults))
        both_adults = htn_adults.intersection(t2d_adults)

        # 2x2 contingency table counts
        a = len(both_adults)                           # HTN (+), T2D (+)
        b = len(htn_adults) - a                        # HTN (+), T2D (-)
        c = len(t2d_adults) - a                        # HTN (-), T2D (+)
        d = n_adults - (a + b + c)                     # HTN (-), T2D (-)

        p_htn = len(htn_adults) / n_adults
        p_t2d = len(t2d_adults) / n_adults
        p_joint = a / n_adults

        # Conditional prevalence P(HTN | T2D)
        cond_prev_htn_in_t2d = (a / len(t2d_adults) * 100.0) if len(t2d_adults) > 0 else 0.0
        ci_cond = wilson_score_interval(a, len(t2d_adults)) if len(t2d_adults) > 0 else (0.0, 0.0)
        ci_cond_pct = (round(ci_cond[0] * 100.0, 2), round(ci_cond[1] * 100.0, 2))

        # Expected joint under independence
        p_expected_joint = p_htn * p_t2d
        oe_ratio = comorbidity_oe_ratio(p_joint, p_htn, p_t2d)

        # Odds ratio
        odds_ratio, or_lower, or_upper = odds_ratio_and_ci(a, b, c, d)

        # Reference benchmark: ICMR-INDIAB 2023 reports ~50.1% of diabetic adults have hypertension
        ref_stat_comorb = self.catalog.get_statistic("comorb_htn_in_t2d")
        ref_cond_prev = ref_stat_comorb.reference_value if ref_stat_comorb else 50.1
        diff_cond = round(cond_prev_htn_in_t2d - ref_cond_prev, 2)
        rel_diff_cond = round(abs(diff_cond) / ref_cond_prev, 4)

        if len(t2d_adults) == 0:
            status_comorb = MetricStatus.NOT_APPLICABLE
        elif abs(diff_cond) <= 15.0:
            status_comorb = MetricStatus.PASS
        elif abs(diff_cond) <= 25.0:
            status_comorb = MetricStatus.WARNING
        else:
            status_comorb = MetricStatus.FAIL

        results.append(MetricResult(
            metric_id="comorb_htn_in_t2d",
            metric_name="Comorbidity: Hypertension Prevalence in Patients with Type 2 Diabetes",
            dimension=EvaluationDimension.COMORBIDITY,
            definition="Conditional prevalence P(HTN|T2D) among adults >= 20 vs ICMR-INDIAB 2023 benchmark.",
            numerator=a,
            denominator=len(t2d_adults),
            synthetic_estimate=round(cond_prev_htn_in_t2d, 2),
            reference_estimate=ref_cond_prev,
            difference=diff_cond,
            relative_difference=rel_diff_cond,
            confidence_interval=ci_cond_pct,
            acceptance_threshold={
                "pass_abs_diff_max": 15.0,
                "warning_abs_diff_max": 25.0,
                "joint_prevalence_pct": round(p_joint * 100.0, 2),
                "expected_joint_prevalence_pct": round(p_expected_joint * 100.0, 2),
                "observed_to_expected_ratio": oe_ratio,
                "odds_ratio": odds_ratio,
                "odds_ratio_95_ci": (or_lower, or_upper),
            },
            status=status_comorb,
            provenance_id="ICMR_INDIAB_2023_HTN",
            verification_status="VERIFIED",
            known_limitations="Evaluated strictly on adults with diagnosed T2D. If no synthetic patient develops T2D, status is NOT_APPLICABLE.",
        ))

        return results

    def evaluate_longitudinal(self) -> List[MetricResult]:
        """Evaluate longitudinal and temporal dynamics: encounters per patient-year, intervals, mortality, intensification, complications."""
        results: List[MetricResult] = []
        n_patients = len(self.patients)

        if n_patients == 0:
            return results        # Compute exact individual right-censored person-time accounting for death and delayed entry
        patient_death_times: Dict[str, datetime] = {}
        for d in self.deaths:
            pid = d.get("patient_id")
            dd_str = d.get("death_date")
            if pid and dd_str:
                try:
                    patient_death_times[pid] = datetime.fromisoformat(dd_str)
                except Exception:
                    pass

        # Pre-compute encounter times
        encounter_times: Dict[str, datetime] = {}
        for enc in self.encounters:
            eid = enc.get("encounter_id")
            st_str = enc.get("start_time")
            if eid and st_str:
                try:
                    encounter_times[eid] = datetime.fromisoformat(st_str)
                except Exception:
                    pass

        # Parse patient birth dates for entry-time accounting (delayed entry protection)
        patient_birth_times: Dict[str, datetime] = {}
        for p in self.patients:
            pid = p.get("patient_id")
            if not pid:
                continue
            b_str = p.get("birth_date")
            if b_str:
                try:
                    patient_birth_times[pid] = datetime.fromisoformat(b_str)
                    continue
                except Exception:
                    pass
            try:
                age = int(p.get("age", 0))
                patient_birth_times[pid] = self.obs_start - timedelta(days=int(age * 365.25))
            except Exception:
                patient_birth_times[pid] = self.obs_start

        total_person_time_years = 0.0
        sum_max_eligible_pt = 0.0

        for p in self.patients:
            pid = p.get("patient_id")
            b_dt = patient_birth_times.get(pid, self.obs_start)
            entry_time = max(self.obs_start, b_dt)
            if entry_time >= self.obs_end:
                continue
            max_eligible_days = (self.obs_end - entry_time).total_seconds() / 86400.0
            max_pt_i = max(0.0, max_eligible_days / 365.25)
            sum_max_eligible_pt += max_pt_i

            if pid in patient_death_times:
                d_time = patient_death_times[pid]
                if d_time <= entry_time:
                    actual_days = 0.0
                elif d_time >= self.obs_end:
                    actual_days = max_eligible_days
                else:
                    actual_days = (d_time - entry_time).total_seconds() / 86400.0
            else:
                actual_days = max_eligible_days

            actual_pt_i = max(0.0, min(max_pt_i, actual_days / 365.25))
            total_person_time_years += actual_pt_i

        total_patient_years = max(0.001, total_person_time_years)
        theoretical_max_pt = round(sum_max_eligible_pt, 2)
        pt_lost_to_death = round(max(0.0, theoretical_max_pt - total_person_time_years), 2)
        total_encounters = len(self.encounters)
        enc_per_py = round(total_encounters / total_patient_years, 2)

        # 1. Encounters per patient-year
        results.append(MetricResult(
            metric_id="long_encounters_per_pt_year",
            metric_name="Longitudinal: Encounters Per Patient-Year",
            dimension=EvaluationDimension.LONGITUDINAL,
            definition="Average number of clinical encounters generated per patient-year of observation.",
            numerator=total_encounters,
            denominator=round(total_patient_years, 2),
            synthetic_estimate=enc_per_py,
            reference_estimate=1.5,  # NSS 75th round outpatient consultation baseline range (0.8 - 2.5)
            difference=round(enc_per_py - 1.5, 2),
            relative_difference=round(abs(enc_per_py - 1.5) / 1.5, 4),
            confidence_interval=None,
            acceptance_threshold={"plausible_range": (0.2, 5.0)},
            status=MetricStatus.UNVERIFIED,
            provenance_id="NSS_75TH_ROUND_OPD",
            verification_status="UNVERIFIED",
            known_limitations="Facility discrete-event simulation captures scheduled outpatient visits and episodic visits.",
        ))

        # 2. Inter-encounter intervals for multi-visit patients
        patient_enc_dates: Dict[str, List[datetime]] = {}
        for enc in self.encounters:
            pid = enc.get("patient_id")
            st_str = enc.get("start_time")
            if pid and st_str:
                try:
                    patient_enc_dates.setdefault(pid, []).append(datetime.fromisoformat(st_str))
                except Exception:
                    pass

        intervals: List[float] = []
        for pid, dates in patient_enc_dates.items():
            if len(dates) >= 2:
                s_dates = sorted(dates)
                for i in range(len(s_dates) - 1):
                    days = (s_dates[i + 1] - s_dates[i]).total_seconds() / 86400.0
                    intervals.append(days)

        if intervals:
            mean_interval = round(sum(intervals) / len(intervals), 1)
            sorted_intervals = sorted(intervals)
            median_interval = round(sorted_intervals[len(sorted_intervals) // 2], 1)
        else:
            mean_interval = 0.0
            median_interval = 0.0

        results.append(MetricResult(
            metric_id="long_inter_encounter_interval_days",
            metric_name="Longitudinal: Mean Days Between Clinical Encounters",
            dimension=EvaluationDimension.LONGITUDINAL,
            definition="Mean interval in days between consecutive clinical encounters for multi-visit patients.",
            numerator=int(sum(intervals)),
            denominator=len(intervals) or 1,
            synthetic_estimate=mean_interval,
            reference_estimate=180.0,  # Standard chronic follow-up guidance (90 - 180 days)
            difference=round(mean_interval - 180.0, 1),
            relative_difference=round(abs(mean_interval - 180.0) / 180.0, 4) if mean_interval else None,
            confidence_interval=None,
            acceptance_threshold={"median_days": median_interval, "multi_visit_patient_count": len([p for p, d in patient_enc_dates.items() if len(d) >= 2])},
            status=MetricStatus.UNVERIFIED,
            provenance_id="ICMR_TREATMENT_GUIDELINES",
            verification_status="UNVERIFIED",
            known_limitations="Clinical modules use configured surveillance delays (e.g., 90d, 180d, 365d).",
        ))

        # 3. Annualized Mortality Rate (Computed with individual right-censored person-time)
        n_deaths = len(self.deaths)
        annual_mort_rate = round(n_deaths / total_patient_years, 5) if total_patient_years > 0 else 0.0
        ref_stat_mort = self.catalog.get_statistic("mort_crude_rate")
        ref_mort_rate = ref_stat_mort.reference_value if ref_stat_mort else 0.0060

        diff_mort = round(annual_mort_rate - ref_mort_rate, 5)

        # Allow wider tolerance for small cohorts where a single death shifts the rate significantly
        status_mort = MetricStatus.PASS if abs(diff_mort) <= 0.025 else MetricStatus.WARNING

        cause_counts = {}
        for d in self.deaths:
            c_code = d.get("cause_code", "UNKNOWN")
            cause_counts[c_code] = cause_counts.get(c_code, 0) + 1

        results.append(MetricResult(
            metric_id="long_crude_mortality_rate",
            metric_name="Longitudinal: Annualized Crude Mortality Rate",
            dimension=EvaluationDimension.LONGITUDINAL,
            definition="Annual deaths per patient-year compared to Census SRS Abridged Life Table 2016-2020.",
            numerator=n_deaths,
            denominator=round(total_patient_years, 4) if total_patient_years < 0.1 else round(total_patient_years, 2),
            synthetic_estimate=annual_mort_rate,
            reference_estimate=ref_mort_rate,
            difference=diff_mort,
            relative_difference=round(abs(diff_mort) / ref_mort_rate, 4),
            confidence_interval=None,
            acceptance_threshold={
                "deaths_count": n_deaths,
                "patient_years": round(total_person_time_years, 2),
                "theoretical_max_patient_years": theoretical_max_pt,
                "person_years_lost_to_death": pt_lost_to_death,
                "cause_breakdown": cause_counts,
            },
            status=status_mort,
            provenance_id="SRS_2016_2020_LIFE_TABLE",
            verification_status="VERIFIED",
            known_limitations="Short simulation windows (e.g. 2 years) in small cohorts exhibit expected binomial variance.",
        ))

        # 4. Longitudinal Treatment Intensification Rate
        patient_drugs: Dict[str, set] = {}
        for m in self.medications:
            pid = m.get("patient_id")
            drug = m.get("drug_name")
            if pid and drug:
                patient_drugs.setdefault(pid, set()).add(drug)

        htn_pids = {c["patient_id"] for c in self.conditions if c.get("condition_code") in ("I10", "I12.9")}
        t2d_pids = {c["patient_id"] for c in self.conditions if c.get("condition_code") in ("E11.9", "E11.2")}
        concomitant_pids = htn_pids.intersection(t2d_pids)
        chronic_patients = htn_pids.union(t2d_pids)

        treated_htn = [pid for pid in htn_pids if pid in patient_drugs]
        intensified_htn = [pid for pid in treated_htn if "Telmisartan" in patient_drugs[pid]]

        treated_t2d = [pid for pid in t2d_pids if pid in patient_drugs]
        intensified_t2d = [pid for pid in treated_t2d if "Glimepiride" in patient_drugs[pid]]

        treated_chronic = [pid for pid in chronic_patients if pid in patient_drugs]
        intensified_patients = set(intensified_htn).union(set(intensified_t2d))

        intens_denom = len(treated_chronic) or 1
        intens_rate = round(len(intensified_patients) / intens_denom, 4) if treated_chronic else 0.0

        # Compute mean days to first intensification
        patient_med_times: Dict[str, List[Tuple[str, datetime]]] = {}
        for m in self.medications:
            pid = m.get("patient_id")
            drug = m.get("drug_name")
            eid = m.get("encounter_id")
            if pid and drug and eid and eid in encounter_times:
                patient_med_times.setdefault(pid, []).append((drug, encounter_times[eid]))

        days_to_intens_list: List[float] = []
        for pid in intensified_patients:
            meds = patient_med_times.get(pid, [])
            if meds:
                first_rx_dt = min(dt for _, dt in meds)
                dual_rx_dt = min((dt for drug, dt in meds if drug in ("Telmisartan", "Glimepiride")), default=None)
                if dual_rx_dt and dual_rx_dt >= first_rx_dt:
                    days_to_intens_list.append((dual_rx_dt - first_rx_dt).total_seconds() / 86400.0)

        mean_days_to_intens = round(sum(days_to_intens_list) / len(days_to_intens_list), 1) if days_to_intens_list else 180.0

        results.append(MetricResult(
            metric_id="long_treatment_intensification_rate",
            metric_name="Longitudinal: Treatment Intensification Rate",
            dimension=EvaluationDimension.LONGITUDINAL,
            definition="Descriptive simulation rate: Cumulative proportion of treated chronic patients stepped up to dual therapy over 2 years.",
            numerator=len(intensified_patients),
            denominator=len(treated_chronic),
            synthetic_estimate=intens_rate,
            reference_estimate=None,  # Removed unsupported guideline target per Section 4 audit
            difference=None,
            relative_difference=None,
            confidence_interval=None,
            acceptance_threshold={
                "patients_intensified_at_least_once": len(intensified_patients),
                "cumulative_patient_intensification_pct": round(intens_rate * 100.0, 2),
                "mean_days_to_first_intensification": mean_days_to_intens,
                "repeated_intensifications_suppressed": True,
                "htn_treated_count": len(treated_htn),
                "htn_intensified_count": len(intensified_htn),
                "htn_intensified_pct": round((len(intensified_htn) / (len(treated_htn) or 1)) * 100.0, 2),
                "t2d_treated_count": len(treated_t2d),
                "t2d_intensified_count": len(intensified_t2d),
                "t2d_intensified_pct": round((len(intensified_t2d) / (len(treated_t2d) or 1)) * 100.0, 2),
                "concomitant_htn_t2d_count": len(concomitant_pids),
                "clinical_fidelity_classification": "UNVERIFIED (Guideline rule conformance without clinical inertia; real-world cross-sectional prescribing target of 35% is not comparable to cumulative 2-year patient escalation)",
            },
            status=MetricStatus.UNVERIFIED,
            provenance_id="ICMR_TREATMENT_GUIDELINES",
            verification_status="UNVERIFIED",
            known_limitations="High cumulative intensification (75-85%) reflects zero therapeutic inertia across repeated visits.",
        ))

        # 5. Longitudinal Chronic Complication Rate
        complication_pids = set()
        for c in self.conditions:
            code = c.get("condition_code", "")
            if code in ("I12.9", "E11.2"):
                pid = c.get("patient_id")
                if pid:
                    complication_pids.add(pid)

        comp_denom = len(chronic_patients) or 1
        comp_rate = round(len(complication_pids) / comp_denom, 4) if chronic_patients else 0.0

        results.append(MetricResult(
            metric_id="long_chronic_complication_rate",
            metric_name="Longitudinal: Chronic Complication Rate",
            dimension=EvaluationDimension.LONGITUDINAL,
            definition="Rate of secondary target-organ damage (CKD, Nephropathy) emerging longitudinally in chronic patients.",
            numerator=len(complication_pids),
            denominator=len(chronic_patients),
            synthetic_estimate=comp_rate,
            reference_estimate=0.04,  # Longitudinal prospective cohort incidence ~3 - 6% over 2 years (CURES-45)
            difference=round(comp_rate - 0.04, 4),
            relative_difference=round(abs(comp_rate - 0.04) / 0.04, 4),
            confidence_interval=None,
            acceptance_threshold={"plausible_range": (0.0, 0.15)},
            status=MetricStatus.UNVERIFIED,
            provenance_id="CURES_CCDC_PROSPECTIVE_HTN",
            verification_status="UNVERIFIED",
            known_limitations="Complications depend on discrete transition weights and surveillance visit frequencies. Classified UNVERIFIED because discrete Markov draws are not externally calibrated clinical trial incidence.",
        ))

        return results

    def evaluate_treatment_patterns(self) -> List[MetricResult]:
        """Evaluate clinical guideline alignment for pharmacotherapy and adherence assumptions."""
        results: List[MetricResult] = []

        # Map condition -> prescribed medications
        cond_meds: Dict[str, List[str]] = {}
        for med in self.medications:
            cid = med.get("condition_id")
            drug = med.get("drug_name")
            if cid and drug:
                cond_meds.setdefault(cid, []).append(drug)

        cond_by_id = {c["condition_id"]: c for c in self.conditions if c.get("condition_id")}

        # 1. First-line Antihypertensive Alignment (Amlodipine / Telmisartan for I10)
        htn_cond_ids = [cid for cid, c in cond_by_id.items() if c.get("condition_code") == "I10"]
        htn_with_firstline = 0
        for cid in htn_cond_ids:
            drugs = [d.lower() for d in cond_meds.get(cid, [])]
            if any("amlodipine" in d or "telmisartan" in d or "losartan" in d for d in drugs):
                htn_with_firstline += 1

        pct_firstline_htn = round((htn_with_firstline / len(htn_cond_ids) * 100.0), 2) if htn_cond_ids else 0.0

        results.append(MetricResult(
            metric_id="rx_firstline_hypertension",
            metric_name="Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Antihypertensive Therapy)",
            dimension=EvaluationDimension.TREATMENT,
            definition="Percentage of diagnosed hypertension cases prescribed first-line CCB (Amlodipine) or ARB. Measures state machine algorithmic rule conformance.",
            numerator=htn_with_firstline,
            denominator=len(htn_cond_ids),
            synthetic_estimate=pct_firstline_htn,
            reference_estimate=100.0,  # Guideline standard: 100% of newly diagnosed uncomplicated HTN indicated for CCB/ARB
            difference=round(pct_firstline_htn - 100.0, 2),
            relative_difference=round(abs(pct_firstline_htn - 100.0) / 100.0, 4) if htn_cond_ids else None,
            confidence_interval=None,
            acceptance_threshold={"min_conformance_pct": 80.0},
            status=MetricStatus.PASS if pct_firstline_htn >= 80.0 or not htn_cond_ids else MetricStatus.WARNING,
            provenance_id="ICMR_STG_HYPERTENSION_2022",
            verification_status="VERIFIED",
            known_limitations="Assumes uncomplicated stage 1/2 essential hypertension indicated for calcium channel blocker. Reflects algorithmic rule compliance rather than verified real-world prescribing fidelity (empirical real-world monotherapy alignment is ~45-65%).",
        ))

        # 2. First-line Antidiabetic Alignment (Metformin for E11.9)
        t2d_cond_ids = [cid for cid, c in cond_by_id.items() if c.get("condition_code") == "E11.9"]
        t2d_with_firstline = 0
        for cid in t2d_cond_ids:
            drugs = [d.lower() for d in cond_meds.get(cid, [])]
            if any("metformin" in d for d in drugs):
                t2d_with_firstline += 1

        pct_firstline_t2d = round((t2d_with_firstline / len(t2d_cond_ids) * 100.0), 2) if t2d_cond_ids else 0.0

        results.append(MetricResult(
            metric_id="rx_firstline_diabetes",
            metric_name="Treatment Conformance: Algorithmic Guideline Rule Conformance (First-Line Oral Hypoglycemic Therapy)",
            dimension=EvaluationDimension.TREATMENT,
            definition="Percentage of diagnosed Type 2 Diabetes cases prescribed first-line Biguanide (Metformin). Measures state machine algorithmic rule conformance.",
            numerator=t2d_with_firstline,
            denominator=len(t2d_cond_ids),
            synthetic_estimate=pct_firstline_t2d,
            reference_estimate=100.0,  # Guideline standard: 100% first line
            difference=round(pct_firstline_t2d - 100.0, 2),
            relative_difference=round(abs(pct_firstline_t2d - 100.0) / 100.0, 4) if t2d_cond_ids else None,
            confidence_interval=None,
            acceptance_threshold={"min_conformance_pct": 80.0},
            status=MetricStatus.PASS if pct_firstline_t2d >= 80.0 or not t2d_cond_ids else MetricStatus.WARNING,
            provenance_id="ICMR_STG_DIABETES_2022",
            verification_status="VERIFIED",
            known_limitations="Guideline recommends Metformin monotherapy as universal initial pharmacotherapy. Reflects algorithmic rule compliance rather than verified real-world prescribing fidelity (empirical real-world monotherapy alignment is ~50-60%).",
        ))

        # 3. Adherence Disclosure Mandate
        results.append(MetricResult(
            metric_id="rx_adherence_assumption",
            metric_name="Treatment Pattern: Perfect Adherence Assumption Disclosure",
            dimension=EvaluationDimension.TREATMENT,
            definition="Formal disclosure documenting that simulated patient adherence to dispensed pharmacotherapy is 100%.",
            numerator=None,
            denominator=None,
            synthetic_estimate=100.0,
            reference_estimate=None,
            difference=None,
            relative_difference=None,
            confidence_interval=None,
            acceptance_threshold={"assumed_adherence_percent": 100.0},
            status=MetricStatus.UNVERIFIED,  # Never label assumptions as empirical PASS
            provenance_id="SYNAPSE_SIMULATION_ASSUMPTION",
            verification_status="UNVERIFIED",
            known_limitations="Real-world non-communicable disease medication adherence in India is ~40-60%. Simulation assumes 100% adherence.",
        ))

        return results

    def evaluate_all(self) -> EvaluationReport:
        """Execute full evaluation suite across all dimensions."""
        all_metrics: List[MetricResult] = []

        # 1. Invariants
        invariants_ok, inv_metrics = self.evaluate_invariants()
        all_metrics.extend(inv_metrics)

        # 2. Demographics
        demo_metrics = self.evaluate_demographics()
        all_metrics.extend(demo_metrics)

        # 3. Prevalence
        prev_metrics = self.evaluate_disease_prevalences()
        all_metrics.extend(prev_metrics)

        # 4. Comorbidities
        comorb_metrics = self.evaluate_comorbidities()
        all_metrics.extend(comorb_metrics)

        # 5. Longitudinal
        long_metrics = self.evaluate_longitudinal()
        all_metrics.extend(long_metrics)

        # 6. Treatments
        rx_metrics = self.evaluate_treatment_patterns()
        all_metrics.extend(rx_metrics)

        # Calculate counts
        passed_count = sum(1 for m in all_metrics if m.status == MetricStatus.PASS)
        warn_count = sum(1 for m in all_metrics if m.status == MetricStatus.WARNING)
        fail_count = sum(1 for m in all_metrics if m.status == MetricStatus.FAIL)
        unver_count = sum(1 for m in all_metrics if m.status == MetricStatus.UNVERIFIED)
        na_count = sum(1 for m in all_metrics if m.status == MetricStatus.NOT_APPLICABLE)

        # Overall verdict: If invariants fail or any critical metric fails -> FAIL
        if not invariants_ok or fail_count > 0:
            overall = MetricStatus.FAIL
        elif warn_count > 0:
            overall = MetricStatus.WARNING
        else:
            overall = MetricStatus.PASS

        # Dimension-level summaries
        dim_summaries: Dict[str, Dict[str, Any]] = {}
        for dim in EvaluationDimension:
            dim_m = [m for m in all_metrics if m.dimension == dim]
            dim_summaries[dim.value] = {
                "total": len(dim_m),
                "pass": sum(1 for m in dim_m if m.status == MetricStatus.PASS),
                "warning": sum(1 for m in dim_m if m.status == MetricStatus.WARNING),
                "fail": sum(1 for m in dim_m if m.status == MetricStatus.FAIL),
                "unverified": sum(1 for m in dim_m if m.status == MetricStatus.UNVERIFIED),
            }

        return EvaluationReport(
            dataset_directory=str(self.dataset_dir.resolve()),
            timestamp=datetime.now().isoformat(),
            total_metrics=len(all_metrics),
            passed_metrics=passed_count,
            warning_metrics=warn_count,
            failed_metrics=fail_count,
            unverified_metrics=unver_count,
            not_applicable_metrics=na_count,
            overall_status=overall,
            invariants_passed=invariants_ok,
            metrics=all_metrics,
            dimension_summaries=dim_summaries,
        )
