"""
Forward Hemodynamic Engine (Phase 2C Forward Diagnosis and Treatment Response).

Establishes a forward state-space architecture for cardiovascular physiology in SYNAPSE Phase 2:
- Separates latent continuous biological hemodynamics (SBP, DBP, pulse pressure) from
  observed measurement protocols, clinical diagnostic criteria, and medication exposure.
- Evaluates biological state evolution as a forward temporal trajectory rather than an
  inverted selection driven by categorical disease or treatment labels.
- Implements forward clinical diagnosis inference: diagnosis depends on observed measurements
  and documented diagnostic criteria, rather than automatically inheriting a latent condition label.
- Represents diagnosis and prescription initiation/discontinuation as timestamped events.
- Introduces a configurable treatment-response interface that lowers subsequent latent BP
  without rewriting historical measurements.
- Strictly separates prescribed medication possession from actual patient medication adherence (exposure).
- Preserves deterministic isolation using dedicated cryptographic PRNG streams.
- Runs behind an opt-in feature flag (LEGACY_CONDITIONAL vs. FORWARD_STATE_SPACE),
  preserving the legacy baseline as the default.
"""

import hashlib
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from enum import Enum
from pydantic import BaseModel, Field, model_validator

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.datagen.bp_measurement import (
    BpMeasurementProtocolConfig,
    BpMeasurementProtocolSimulator,
    BpProtocolResult,
    CommunityBpReading,
)
from synapse_simulator.evaluation.medication_status import (
    is_prescription_active_at,
    parse_timestamp,
    DEFAULT_ANTIHYPERTENSIVE_KEYWORDS,
)


# =============================================================================
# Feature Flag Modes and Provenance Tags
# =============================================================================

HEMODYNAMIC_ENGINE_LEGACY = "LEGACY_CONDITIONAL"
HEMODYNAMIC_ENGINE_FORWARD = "FORWARD_STATE_SPACE"
VALID_HEMODYNAMIC_MODES = {HEMODYNAMIC_ENGINE_LEGACY, HEMODYNAMIC_ENGINE_FORWARD}


class EvidentialStatus(str, Enum):
    """Classification of parameter grounding and evidential pedigree."""
    LITERATURE_CALIBRATED = "LITERATURE_CALIBRATED"
    PROVISIONAL_DEFAULT = "PROVISIONAL_DEFAULT"
    PHYSIOLOGICAL_GUARD = "PHYSIOLOGICAL_GUARD"
    STRUCTURAL_PLACEHOLDER = "STRUCTURAL_PLACEHOLDER"


# =============================================================================
# Forward Clinical Events (Phase 2C)
# =============================================================================

class ClinicalDiagnosisEvent(BaseModel):
    """Structured timestamped event representing an incident clinical diagnosis.

    Diagnosis occurs strictly when documented diagnostic criteria are satisfied upon
    observing clinical measurements at healthcare encounters.
    """
    event_id: str = Field(..., description="Unique diagnosis event identifier")
    patient_id: str = Field(..., description="Foreign key to patient record")
    condition_code: str = Field(default="I10", description="ICD-10 condition code")
    condition_name: str = Field(default="Essential (primary) hypertension", description="Diagnosis description")
    timestamp: datetime = Field(..., description="Exact clinical diagnosis timestamp")
    encounter_id: str = Field(..., description="Linked encounter identifier")
    criteria_met: str = Field(..., description="Documented diagnostic criteria satisfied")
    observed_sbp: float = Field(..., description="Observed SBP at diagnostic encounter (mmHg)")
    observed_dbp: float = Field(..., description="Observed DBP at diagnostic encounter (mmHg)")
    status: str = Field(default="Active", description="Clinical status of diagnosis")
    provenance: str = Field(default="FORWARD_CLINICAL_DIAGNOSIS_ENGINE", description="Provenance tag")


class PrescriptionEvent(BaseModel):
    """Structured timestamped event representing medication initiation or discontinuation."""
    event_id: str = Field(..., description="Unique prescription event identifier")
    patient_id: str = Field(..., description="Foreign key to patient record")
    prescription_id: str = Field(..., description="Linked prescription identifier")
    encounter_id: str = Field(..., description="Linked encounter identifier")
    drug_code: str = Field(default="AML-5", description="Drug code")
    drug_name: str = Field(default="Amlodipine", description="Prescribed medication name")
    dosage: str = Field(default="5mg", description="Medication dosage")
    frequency: str = Field(default="Once Daily", description="Administration frequency")
    start_time: datetime = Field(..., description="Prescription start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Discontinuation timestamp if stopped")
    status: str = Field(default="Dispensed", description="Prescription status: Dispensed, Active, Discontinued")
    discontinuation_reason: Optional[str] = Field(default=None, description="Reason for stopping if discontinued")
    timestamp: datetime = Field(..., description="Event timestamp")
    provenance: str = Field(default="FORWARD_PRESCRIPTION_ENGINE", description="Provenance tag")


# =============================================================================
# Configuration Specification
# =============================================================================

class ForwardHemodynamicConfig(BaseModel):
    """Configuration for the experimental forward hemodynamic engine.

    All provisional parameters carry explicit evidential status metadata to prevent
    unsubstantiated claims of clinical calibration.
    """
    engine_mode: str = Field(
        default=HEMODYNAMIC_ENGINE_LEGACY,
        description="Hemodynamic engine mode: LEGACY_CONDITIONAL (default) or FORWARD_STATE_SPACE"
    )

    # 1. Baseline Latent Distribution Anchors (Young Adult / Early Middle-Age Population Distribution)
    mean_sbp_anchor: float = Field(
        default=120.0,
        description="Population mean resting SBP anchor at baseline (mmHg)"
    )
    sd_sbp_anchor: float = Field(
        default=9.0,
        description="Between-person standard deviation of resting baseline SBP (mmHg)"
    )
    mean_dbp_anchor: float = Field(
        default=78.0,
        description="Population mean resting DBP anchor at baseline (mmHg)"
    )
    sd_dbp_anchor: float = Field(
        default=6.0,
        description="Between-person standard deviation of resting baseline DBP (mmHg)"
    )
    sbp_dbp_correlation: float = Field(
        default=0.65,
        ge=-1.0,
        le=1.0,
        description="Bivariate correlation between baseline resting SBP and DBP"
    )

    # 2. Physiological Safeguards
    min_pulse_pressure: float = Field(
        default=20.0,
        description="Physiological minimum pulse pressure guard (SBP - DBP, mmHg)"
    )
    min_sbp: float = Field(default=70.0, description="Absolute physiological floor for SBP (mmHg)")
    max_sbp: float = Field(default=260.0, description="Absolute physiological ceiling for SBP (mmHg)")
    min_dbp: float = Field(default=40.0, description="Absolute physiological floor for DBP (mmHg)")
    max_dbp: float = Field(default=150.0, description="Absolute physiological ceiling for DBP (mmHg)")

    # 3. Longitudinal Vascular Aging Drift
    enable_aging_drift: bool = Field(
        default=True,
        description="Whether continuous vascular aging drift with advancing chronological age is enabled"
    )
    annual_drift_sbp: float = Field(
        default=0.60,
        description="Annual rate of systolic blood pressure rise due to vascular stiffening (mmHg/year)"
    )
    annual_drift_dbp_early: float = Field(
        default=0.25,
        description="Annual rate of diastolic blood pressure rise up to age inflection (mmHg/year)"
    )
    annual_drift_dbp_late: float = Field(
        default=-0.15,
        description="Annual rate of diastolic blood pressure change after age inflection (mmHg/year)"
    )
    age_inflection_dbp: float = Field(
        default=60.0,
        description="Age at which DBP plateaus and begins late-life decline, widening pulse pressure (years)"
    )

    # 4. Comorbidity Effect Shifts
    t2d_sbp_shift: float = Field(
        default=4.5,
        description="Provisional hemodynamic shift on SBP in patients with active Type 2 Diabetes (mmHg)"
    )
    t2d_dbp_shift: float = Field(
        default=2.0,
        description="Provisional hemodynamic shift on DBP in patients with active Type 2 Diabetes (mmHg)"
    )

    # 5. Sex-Specific Offsets
    male_sbp_offset: float = Field(
        default=2.0,
        description="Provisional physiological SBP offset for male individuals in young/middle age (mmHg)"
    )
    male_dbp_offset: float = Field(
        default=1.5,
        description="Provisional physiological DBP offset for male individuals in young/middle age (mmHg)"
    )

    # 6. Pharmacodynamic Treatment Response (Phase 2C)
    enable_treatment_response: bool = Field(
        default=True,
        description="Whether active antihypertensive treatment reduces latent continuous BP"
    )
    delta_drug_sbp: float = Field(
        default=12.0,
        description="Provisional resting SBP reduction for standard monotherapy (mmHg)"
    )
    delta_drug_dbp: float = Field(
        default=7.0,
        description="Provisional resting DBP reduction for standard monotherapy (mmHg)"
    )
    treatment_ramp_days: float = Field(
        default=14.0,
        description="Provisional elapsed days to achieve full steady-state pharmacological effect"
    )

    # 7. Medication Adherence Exposure (Phase 2C)
    adherence_mode: str = Field(
        default="POPULATION_DISTRIBUTION",
        description="Adherence regime: POPULATION_DISTRIBUTION, FULL_ADHERENCE, NON_ADHERENT, PARTIAL_ADHERENT, INDIVIDUAL_OVERRIDE"
    )
    mean_adherence: float = Field(
        default=0.70,
        description="Provisional population mean medication adherence factor (0.0 to 1.0)"
    )
    sd_adherence: float = Field(
        default=0.20,
        description="Provisional between-person standard deviation of medication adherence"
    )
    fixed_adherence_factor: Optional[float] = Field(
        default=None,
        description="Optional fixed adherence override factor [0.0, 1.0] for testing"
    )

    # 8. Clinical Diagnostic Criteria (Phase 2C)
    severe_sbp_threshold: float = Field(
        default=180.0,
        description="Observed SBP threshold for immediate diagnosis (Hypertensive Crisis, mmHg)"
    )
    severe_dbp_threshold: float = Field(
        default=120.0,
        description="Observed DBP threshold for immediate diagnosis (Hypertensive Crisis, mmHg)"
    )
    elevated_sbp_threshold: float = Field(
        default=140.0,
        description="Observed SBP threshold for clinical hypertension (mmHg)"
    )
    elevated_dbp_threshold: float = Field(
        default=90.0,
        description="Observed DBP threshold for clinical hypertension (mmHg)"
    )
    confirmed_elevated_visits_required: int = Field(
        default=2,
        description="Number of distinct visits with elevated readings required for non-severe diagnosis"
    )

    # 9. Evidential Metadata Registry
    parameter_provenance: Dict[str, str] = Field(
        default_factory=lambda: {
            "mean_sbp_anchor": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "sd_sbp_anchor": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "mean_dbp_anchor": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "sd_dbp_anchor": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "sbp_dbp_correlation": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "min_pulse_pressure": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "min_sbp": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "max_sbp": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "min_dbp": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "max_dbp": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "annual_drift_sbp": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "annual_drift_dbp_early": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "annual_drift_dbp_late": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "age_inflection_dbp": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "t2d_sbp_shift": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "t2d_dbp_shift": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "male_sbp_offset": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "male_dbp_offset": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "delta_drug_sbp": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "delta_drug_dbp": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "treatment_ramp_days": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "adherence_mode": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "mean_adherence": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "sd_adherence": EvidentialStatus.PROVISIONAL_DEFAULT.value,
            "severe_sbp_threshold": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "severe_dbp_threshold": EvidentialStatus.PHYSIOLOGICAL_GUARD.value,
            "elevated_sbp_threshold": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "elevated_dbp_threshold": EvidentialStatus.LITERATURE_CALIBRATED.value,
            "confirmed_elevated_visits_required": EvidentialStatus.LITERATURE_CALIBRATED.value,
        },
        description="Scientific evidence pedigree registry for all model parameters"
    )

    @model_validator(mode="after")
    def validate_engine_mode(self) -> "ForwardHemodynamicConfig":
        if self.engine_mode not in VALID_HEMODYNAMIC_MODES:
            raise ValueError(
                f"Invalid hemodynamic engine mode '{self.engine_mode}'. "
                f"Supported modes are: {sorted(list(VALID_HEMODYNAMIC_MODES))}"
            )
        return self


# =============================================================================
# Latent Physiological State Representation
# =============================================================================

class LatentHemodynamicState(BaseModel):
    """Authoritative representation of a patient's unobserved true resting hemodynamic state.

    Strictly distinct from observed clinical readings (which carry situational alerting
    and device measurement error) and administrative diagnostic classifications.
    """
    patient_id: str = Field(..., description="Unique patient identifier")
    timestamp: datetime = Field(..., description="Exact simulation timestamp of the physiological state")
    latent_sbp: float = Field(..., description="True resting systolic blood pressure (mmHg)")
    latent_dbp: float = Field(..., description="True resting diastolic blood pressure (mmHg)")
    pulse_pressure: float = Field(..., description="Pulse pressure: SBP - DBP (mmHg)")
    baseline_sbp: float = Field(..., description="Individual patient baseline resting SBP (mmHg)")
    baseline_dbp: float = Field(..., description="Individual patient baseline resting DBP (mmHg)")
    cumulative_age_drift_sbp: float = Field(default=0.0, description="Cumulative age-related SBP drift (mmHg)")
    cumulative_age_drift_dbp: float = Field(default=0.0, description="Cumulative age-related DBP drift (mmHg)")
    comorbidity_shift_sbp: float = Field(default=0.0, description="Comorbidity-induced SBP shift (mmHg)")
    comorbidity_shift_dbp: float = Field(default=0.0, description="Comorbidity-induced DBP shift (mmHg)")
    treatment_effect_sbp: float = Field(default=0.0, description="Active pharmacodynamic SBP reduction (mmHg)")
    treatment_effect_dbp: float = Field(default=0.0, description="Active pharmacodynamic DBP reduction (mmHg)")
    adherence_factor: float = Field(default=1.0, description="Patient medication adherence exposure factor [0.0, 1.0]")
    active_prescriptions_count: int = Field(default=0, description="Number of active antihypertensive prescriptions at timestamp")
    is_valid: bool = Field(default=True, description="Whether physiological state satisfies plausibility guards")
    engine_version: str = Field(default="2.2.0-alpha", description="Forward engine interface version")
    provenance: str = Field(
        default="FORWARD_HEMODYNAMIC_SIMULATOR",
        description="Data provenance establishing forward physiological generation"
    )


# =============================================================================
# Deterministic PRNG Seed Derivation
# =============================================================================

def derive_hemodynamic_seed(
    base_seed: int,
    patient_id: str,
    stream_id: str = "forward_hemodynamics"
) -> int:
    """Deterministically derive an isolated 32-bit unsigned PRNG seed for a patient.

    Guarantees:
    - Never consumes entropy from the legacy simulation or evaluation random streams.
    - Completely independent of Python's process-randomized built-in hash() function.
    - Stable across platforms, operating systems, and process lifecycles.
    """
    token = f"{base_seed}:{stream_id}:{patient_id}".encode("utf-8")
    digest = hashlib.sha256(token).digest()
    return int.from_bytes(digest[:4], byteorder="big")


# =============================================================================
# Forward Hemodynamic Simulator
# =============================================================================

class ForwardHemodynamicSimulator:
    """Experimental forward hemodynamic engine for continuous cardiovascular state generation."""

    def __init__(
        self,
        config: Optional[ForwardHemodynamicConfig] = None,
        base_seed: int = 42,
    ):
        self.config = config or ForwardHemodynamicConfig()
        self.base_seed = base_seed

    def get_patient_rng(self, patient_id: str) -> random.Random:
        """Obtain a dedicated, isolated PRNG stream for a specific patient."""
        seed = derive_hemodynamic_seed(self.base_seed, patient_id, stream_id="forward_hemodynamics")
        return random.Random(seed)

    def get_patient_adherence(self, patient_id: str) -> float:
        """Deterministically determine the patient's medication adherence exposure factor [0.0, 1.0].

        Preserves strict separation between prescription possession and biological exposure:
        A patient may hold an active prescription in the EHR while exhibiting zero or partial
        medication adherence.
        """
        if self.config.fixed_adherence_factor is not None:
            return max(0.0, min(1.0, float(self.config.fixed_adherence_factor)))

        mode = (self.config.adherence_mode or "POPULATION_DISTRIBUTION").upper()
        if mode == "FULL_ADHERENCE":
            return 1.0
        elif mode == "NON_ADHERENT":
            return 0.0
        elif mode == "PARTIAL_ADHERENT":
            return 0.5

        # POPULATION_DISTRIBUTION
        seed = derive_hemodynamic_seed(self.base_seed, patient_id, stream_id="forward_adherence")
        rng = random.Random(seed)
        val = rng.gauss(self.config.mean_adherence, self.config.sd_adherence)
        return max(0.0, min(1.0, round(val, 2)))

    def initialize_patient_baseline(
        self,
        patient: PatientContext,
        observation_start: datetime = datetime(2024, 1, 1),
    ) -> LatentHemodynamicState:
        """Initialize patient baseline resting SBP and DBP from biological factors.

        CRITICAL ARCHITECTURAL GUARANTEE:
        This initialization does NOT inspect final hypertension diagnosis ('I10' in latent_conditions)
        or future prescription status to choose the baseline distribution. It draws from a single,
        continuous bivariate biological population distribution conditioned strictly on patient
        demographics and baseline comorbidity.
        """
        rng = self.get_patient_rng(patient.patient_id)

        # 1. Bivariate normal standard draws (Box-Muller / Cholesky decomposition)
        z1 = rng.gauss(0.0, 1.0)
        z2 = rng.gauss(0.0, 1.0)
        rho = self.config.sbp_dbp_correlation

        # Correlated standard normal variables
        w_sbp = z1
        w_dbp = rho * z1 + math.sqrt(max(0.0, 1.0 - rho * rho)) * z2

        # 2. Scaled baseline physiological anchors
        sbp_0 = self.config.mean_sbp_anchor + self.config.sd_sbp_anchor * w_sbp
        dbp_0 = self.config.mean_dbp_anchor + self.config.sd_dbp_anchor * w_dbp

        # 3. Baseline Demographic Adjustments (Sex)
        is_male = (getattr(patient, "gender", "").capitalize() == "Male")
        if is_male:
            sbp_0 += self.config.male_sbp_offset
            dbp_0 += self.config.male_dbp_offset

        # 4. Baseline Comorbidity Shift (Diabetes)
        has_t2d = (
            "E11.9" in getattr(patient, "baseline_conditions", {})
            or any("Diabetes" in c or c == "E11.9" for c in getattr(patient, "chronic_conditions", []))
        )
        c_shift_sbp = self.config.t2d_sbp_shift if has_t2d else 0.0
        c_shift_dbp = self.config.t2d_dbp_shift if has_t2d else 0.0
        sbp_0 += c_shift_sbp
        dbp_0 += c_shift_dbp

        # 5. Physiological Safeguards
        sbp_0 = max(self.config.min_sbp, min(self.config.max_sbp, sbp_0))
        dbp_0 = max(self.config.min_dbp, min(self.config.max_dbp, dbp_0))
        if sbp_0 - dbp_0 < self.config.min_pulse_pressure:
            sbp_0 = dbp_0 + self.config.min_pulse_pressure + 5.0

        sbp_0 = round(sbp_0, 1)
        dbp_0 = round(dbp_0, 1)
        pp_0 = round(sbp_0 - dbp_0, 1)

        # Determine reference anchor timestamp
        ref_time = observation_start

        return LatentHemodynamicState(
            patient_id=patient.patient_id,
            timestamp=ref_time,
            latent_sbp=sbp_0,
            latent_dbp=dbp_0,
            pulse_pressure=pp_0,
            baseline_sbp=sbp_0,
            baseline_dbp=dbp_0,
            cumulative_age_drift_sbp=0.0,
            cumulative_age_drift_dbp=0.0,
            comorbidity_shift_sbp=c_shift_sbp,
            comorbidity_shift_dbp=c_shift_dbp,
            treatment_effect_sbp=0.0,
            treatment_effect_dbp=0.0,
            adherence_factor=1.0,
            active_prescriptions_count=0,
            is_valid=True,
            engine_version="2.2.0-alpha",
            provenance="FORWARD_HEMODYNAMIC_SIMULATOR",
        )

    def get_latent_state_at(
        self,
        patient: PatientContext,
        target_time: datetime,
        observation_start: datetime = datetime(2024, 1, 1),
        baseline_state: Optional[LatentHemodynamicState] = None,
        prescriptions: Optional[Union[List[Dict[str, Any]], Dict[str, Any], List[PrescriptionEvent]]] = None,
    ) -> LatentHemodynamicState:
        """Evaluate the patient's continuous latent biological hemodynamic state at target_time.

        Applies forward biological evolution:
        - Continuous vascular aging drift with advancing chronological age.
        - Pulse pressure widening based on age inflection.
        - Incident comorbidity onset occurring on or before target_time.
        - Dynamic pharmacodynamic treatment response based on active prescriptions and adherence.
        - Preserves temporal integrity: events after target_time have zero effect.
        """
        # Obtain baseline state deterministically if not provided
        b_state = baseline_state or self.initialize_patient_baseline(patient, observation_start)

        # Calculate elapsed time in years from baseline anchor
        elapsed_days = (target_time - b_state.timestamp).total_seconds() / 86400.0
        elapsed_years = max(0.0, elapsed_days / 365.25)

        # Patient chronological age at target time
        if getattr(patient, "birth_date", None):
            birth_dt = patient.birth_date
            patient_age_target = (target_time - birth_dt).total_seconds() / (86400.0 * 365.25)
        else:
            patient_age_target = float(getattr(patient, "age", 45.0)) + elapsed_years

        # 1. Vascular Aging Drift
        drift_sbp = 0.0
        drift_dbp = 0.0
        if self.config.enable_aging_drift and elapsed_years > 0.0:
            drift_sbp = self.config.annual_drift_sbp * elapsed_years

            # Bilinear DBP drift: rises until age_inflection_dbp, then declines
            inflection = self.config.age_inflection_dbp
            age_base = patient_age_target - elapsed_years

            if patient_age_target <= inflection:
                drift_dbp = self.config.annual_drift_dbp_early * elapsed_years
            elif age_base >= inflection:
                drift_dbp = self.config.annual_drift_dbp_late * elapsed_years
            else:
                years_early = inflection - age_base
                years_late = patient_age_target - inflection
                drift_dbp = (
                    self.config.annual_drift_dbp_early * years_early
                    + self.config.annual_drift_dbp_late * years_late
                )

        # 2. Dynamic Comorbidity Shift (checks whether T2D active on or before target_time)
        t2d_active = False
        if "E11.9" in getattr(patient, "baseline_conditions", {}):
            t2d_active = True
        elif "E11.9" in getattr(patient, "latent_conditions", {}):
            l_info = patient.latent_conditions["E11.9"]
            onset = l_info.get("onset_time")
            if onset is not None and onset <= target_time:
                resolved = l_info.get("resolved") and (l_info.get("resolved_time") <= target_time)
                if not resolved:
                    t2d_active = True

        comorb_sbp = self.config.t2d_sbp_shift if t2d_active else 0.0
        comorb_dbp = self.config.t2d_dbp_shift if t2d_active else 0.0

        # 3. Dynamic Pharmacodynamic Treatment Response (Phase 2C)
        active_rxs = []
        rx_source = prescriptions
        if rx_source is None and getattr(patient, "prescriptions", None):
            rx_source = patient.prescriptions

        if rx_source:
            if isinstance(rx_source, set):
                if patient.patient_id in rx_source:
                    steady_state_start = target_time - timedelta(days=max(14.0, self.config.treatment_ramp_days))
                    active_rxs.append({"drug_name": "amlodipine", "start_time": steady_state_start, "status": "Dispensed", "patient_id": patient.patient_id})
            else:
                rx_list = rx_source.values() if isinstance(rx_source, dict) else rx_source
                for rx in rx_list:
                    if isinstance(rx, str):
                        if rx == patient.patient_id:
                            steady_state_start = target_time - timedelta(days=max(14.0, self.config.treatment_ramp_days))
                            active_rxs.append({"drug_name": "amlodipine", "start_time": steady_state_start, "status": "Dispensed", "patient_id": patient.patient_id})
                    elif isinstance(rx, (dict, BaseModel)):
                        rx_pid = rx.get("patient_id") if isinstance(rx, dict) else getattr(rx, "patient_id", None)
                        if rx_pid is None or rx_pid == patient.patient_id:
                            if is_prescription_active_at(rx, target_time):
                                active_rxs.append(rx)

        treatment_sbp = 0.0
        treatment_dbp = 0.0
        adherence_val = 1.0

        if active_rxs and self.config.enable_treatment_response:
            adherence_val = self.get_patient_adherence(patient.patient_id)
            # Calculate pharmacological onset ramp from earliest active prescription start time
            earliest_start = None
            for rx in active_rxs:
                rx_dict = rx.model_dump() if hasattr(rx, "model_dump") else (rx.dict() if hasattr(rx, "dict") else rx)
                st_str = rx_dict.get("start_time") or rx_dict.get("prescribed_time") or rx_dict.get("timestamp")
                st_dt = parse_timestamp(st_str)
                if st_dt:
                    if earliest_start is None or st_dt < earliest_start:
                        earliest_start = st_dt

            ramp_factor = 1.0
            if earliest_start and self.config.treatment_ramp_days > 0.0:
                elapsed_rx_days = max(0.0, (target_time - earliest_start).total_seconds() / 86400.0)
                ramp_factor = min(1.0, elapsed_rx_days / self.config.treatment_ramp_days)

            treatment_sbp = round(adherence_val * self.config.delta_drug_sbp * ramp_factor, 2)
            treatment_dbp = round(adherence_val * self.config.delta_drug_dbp * ramp_factor, 2)

        # Net latent blood pressure
        net_sbp = b_state.baseline_sbp + drift_sbp + (comorb_sbp - b_state.comorbidity_shift_sbp) - treatment_sbp
        net_dbp = b_state.baseline_dbp + drift_dbp + (comorb_dbp - b_state.comorbidity_shift_dbp) - treatment_dbp

        # Physiological guards
        net_sbp = max(self.config.min_sbp, min(self.config.max_sbp, net_sbp))
        net_dbp = max(self.config.min_dbp, min(self.config.max_dbp, net_dbp))
        if net_sbp - net_dbp < self.config.min_pulse_pressure:
            net_sbp = net_dbp + self.config.min_pulse_pressure

        net_sbp = round(net_sbp, 1)
        net_dbp = round(net_dbp, 1)
        net_pp = round(net_sbp - net_dbp, 1)

        return LatentHemodynamicState(
            patient_id=patient.patient_id,
            timestamp=target_time,
            latent_sbp=net_sbp,
            latent_dbp=net_dbp,
            pulse_pressure=net_pp,
            baseline_sbp=b_state.baseline_sbp,
            baseline_dbp=b_state.baseline_dbp,
            cumulative_age_drift_sbp=round(drift_sbp, 2),
            cumulative_age_drift_dbp=round(drift_dbp, 2),
            comorbidity_shift_sbp=comorb_sbp,
            comorbidity_shift_dbp=comorb_dbp,
            treatment_effect_sbp=treatment_sbp,
            treatment_effect_dbp=treatment_dbp,
            adherence_factor=adherence_val if active_rxs else 1.0,
            active_prescriptions_count=len(active_rxs),
            is_valid=True,
            engine_version="2.2.0-alpha",
            provenance="FORWARD_HEMODYNAMIC_SIMULATOR",
        )

    def evaluate_clinical_diagnosis(
        self,
        patient: PatientContext,
        encounter_id: str,
        encounter_time: datetime,
        observed_sbp: float,
        observed_dbp: float,
        clinical_history: Optional[Dict[str, Any]] = None,
    ) -> Optional[ClinicalDiagnosisEvent]:
        """Evaluate documented clinical diagnostic criteria for hypertension (ICD-10 I10).

        Clinical Diagnostic Rules (Layer D):
        1. Severe Elevation (Hypertensive Crisis / Urgency):
           Observed SBP >= severe_sbp_threshold (180 mmHg) OR DBP >= severe_dbp_threshold (120 mmHg)
           at an encounter triggers IMMEDIATE clinical diagnosis.
        2. Repeated Moderate / Stage 2 Elevation:
           Observed SBP >= elevated_sbp_threshold (140 mmHg) OR DBP >= elevated_dbp_threshold (90 mmHg)
           requires >= confirmed_elevated_visits_required (default 2) distinct encounters
           with elevated readings before confirming clinical diagnosis.
        3. Normal or Single Non-Severe Elevated Reading:
           A single non-severe elevated reading is tracked as pending confirmation without
           recording a formal ICD-10 I10 diagnosis in the EHR. Normal readings do not diagnose.
        """
        # Check if already diagnosed on or prior to encounter_time
        has_diagnosed = False
        if clinical_history and "I10" in clinical_history.get("diagnosed_conditions", []):
            has_diagnosed = True
        elif patient.latent_conditions.get("I10", {}).get("recognized"):
            dx_t = patient.latent_conditions.get("I10", {}).get("diagnosis_time")
            if dx_t is None or dx_t <= encounter_time:
                has_diagnosed = True

        if has_diagnosed:
            return None

        # Record this clinical visit's blood pressure in patient clinical visit history
        visits = patient.attributes.setdefault("clinical_bp_visits", [])
        is_severe = (
            observed_sbp >= self.config.severe_sbp_threshold
            or observed_dbp >= self.config.severe_dbp_threshold
        )
        is_elevated = (
            observed_sbp >= self.config.elevated_sbp_threshold
            or observed_dbp >= self.config.elevated_dbp_threshold
        )

        visit_record = {
            "encounter_id": encounter_id,
            "timestamp": encounter_time.isoformat() if isinstance(encounter_time, datetime) else str(encounter_time),
            "sbp": observed_sbp,
            "dbp": observed_dbp,
            "is_severe": is_severe,
            "is_elevated": is_elevated,
        }
        if not any(v.get("encounter_id") == encounter_id and v.get("timestamp") == visit_record["timestamp"] for v in visits):
            visits.append(visit_record)

        criteria_met = None
        if is_severe:
            criteria_met = "SEVERE_ELEVATION_IMMEDIATE"
        elif is_elevated:
            # Count distinct encounters with elevated blood pressure occurring on or prior to encounter_time
            # (strictly preventing future encounters from confirming a historical diagnosis)
            elevated_encounters = {
                v["encounter_id"]
                for v in visits
                if v.get("is_elevated")
                and v.get("encounter_id")
                and (parse_timestamp(v.get("timestamp")) is None or parse_timestamp(v.get("timestamp")) <= encounter_time)
            }
            if len(elevated_encounters) >= self.config.confirmed_elevated_visits_required:
                criteria_met = "REPEATED_ELEVATED_BP_CONFIRMED"

        if criteria_met:
            event_id = f"dx-htn-{patient.patient_id}-{len(visits)}"
            return ClinicalDiagnosisEvent(
                event_id=event_id,
                patient_id=patient.patient_id,
                condition_code="I10",
                condition_name="Essential (primary) hypertension",
                timestamp=encounter_time,
                encounter_id=encounter_id,
                criteria_met=criteria_met,
                observed_sbp=observed_sbp,
                observed_dbp=observed_dbp,
                status="Active",
                provenance="FORWARD_CLINICAL_DIAGNOSIS_ENGINE",
            )

        return None

    def create_prescription_event(
        self,
        patient_id: str,
        prescription_id: str,
        encounter_id: str,
        drug_code: str = "AML-5",
        drug_name: str = "Amlodipine",
        dosage: str = "5mg",
        frequency: str = "Once Daily",
        start_time: Optional[datetime] = None,
        timestamp: Optional[datetime] = None,
    ) -> PrescriptionEvent:
        """Create a timestamped prescription initiation event."""
        st = start_time or datetime(2024, 1, 1)
        ts = timestamp or st
        return PrescriptionEvent(
            event_id=f"evt-rx-{prescription_id}",
            patient_id=patient_id,
            prescription_id=prescription_id,
            encounter_id=encounter_id,
            drug_code=drug_code,
            drug_name=drug_name,
            dosage=dosage,
            frequency=frequency,
            start_time=st,
            end_time=None,
            status="Dispensed",
            discontinuation_reason=None,
            timestamp=ts,
            provenance="FORWARD_PRESCRIPTION_ENGINE",
        )

    def discontinue_prescription_event(
        self,
        prescription: Union[PrescriptionEvent, Dict[str, Any]],
        discontinuation_time: datetime,
        reason: str = "Physician Discontinued",
    ) -> PrescriptionEvent:
        """Create a timestamped prescription discontinuation event."""
        if hasattr(prescription, "model_copy"):
            rx_data = prescription.model_dump()
        elif hasattr(prescription, "copy"):
            rx_data = prescription.copy()
        else:
            rx_data = dict(prescription)

        rx_data["end_time"] = discontinuation_time
        rx_data["status"] = "Discontinued"
        rx_data["discontinuation_reason"] = reason
        rx_data["timestamp"] = discontinuation_time
        return PrescriptionEvent(**rx_data)

    def observe(
        self,
        latent_state: LatentHemodynamicState,
        protocol_simulator: BpMeasurementProtocolSimulator,
        assessment_id: str,
        pat_rng: random.Random,
    ) -> BpProtocolResult:
        """Connect the latent biological state to the existing blood pressure measurement protocol.

        Strictly preserves the conceptual separation between:
        1. Latent unobserved SBP/DBP.
        2. Individual observed readings with situational alerting and within-visit error.
        3. Derived protocol analysis measurement (mean of readings 2 and 3).

        The measurement protocol NEVER modifies or overwrites the latent biological state.
        """
        return protocol_simulator.simulate(
            underlying_sbp=latent_state.latent_sbp,
            underlying_dbp=latent_state.latent_dbp,
            assessment_id=assessment_id,
            patient_id=latent_state.patient_id,
            assessment_date=latent_state.timestamp,
            pat_rng=pat_rng,
        )
