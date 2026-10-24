"""
Community Health Assessment Pathway for SYNAPSE Phase 2.

Provides an independent, population-level health assessment mechanism that collects
vital signs (blood pressure, pulse pressure) in a community/household setting without:
- Creating hospital/clinic visits (encounters.csv)
- Generating clinical EHR condition diagnoses (conditions.csv)
- Triggering clinical prescriptions or treatment modifications (medications.csv)
- Modifying clinical module state or discrete-event simulation transitions.

Preserves exact patient identity, measurement timestamp, SBP, DBP, units, provenance,
and missingness/unassessability semantics under reproducible random seeds.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field, model_validator

from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.datagen.bp_measurement import (
    BpMeasurementProtocolConfig,
    BpMeasurementProtocolSimulator,
    CommunityBpReading,
    BpReadingStatus,
    BpDerivationCategory,
    create_lasi_tri_measurement_protocol,
    create_single_reading_baseline_protocol,
)


class CommunityAssessment(BaseModel):
    """Structured record of an independent community/household health assessment."""
    assessment_id: str = Field(..., description="Unique assessment identifier (e.g., ca-p001)")
    patient_id: str = Field(..., description="Foreign key to patient record")
    timestamp: datetime = Field(..., description="Survey measurement timestamp")
    assessment_type: str = Field(default="COMMUNITY_HEALTH_ASSESSMENT", description="Assessment modality")
    sbp: Optional[float] = Field(default=None, description="Systolic blood pressure (mmHg)")
    dbp: Optional[float] = Field(default=None, description="Diastolic blood pressure (mmHg)")
    pulse_pressure: Optional[float] = Field(default=None, description="Pulse pressure (SBP - DBP, mmHg)")
    unit: str = Field(default="mmHg", description="Blood pressure measurement unit")
    survey_weight: float = Field(default=1.0, description="Inverse probability sampling weight")
    status: str = Field(default="COMPLETED", description="Assessment status: COMPLETED, REFUSED, UNAVAILABLE")
    provenance: str = Field(
        default="COMMUNITY_HEALTH_ASSESSMENT_LAYER",
        description="Data provenance establishing independent community origin"
    )
    is_assessable: bool = Field(default=True, description="Whether valid vital signs were obtained")
    protocol_id: str = Field(default="LASI_WAVE1_TRI_MEASUREMENT", description="Protocol identifier")
    derivation_category: str = Field(
        default=BpDerivationCategory.PROTOCOL_MEAN_READINGS_2_AND_3.value,
        description="Derivation category classification"
    )


from synapse_simulator.datagen.forward_hemodynamics import (
    ForwardHemodynamicConfig,
    ForwardHemodynamicSimulator,
    LatentHemodynamicState,
    HEMODYNAMIC_ENGINE_LEGACY,
    HEMODYNAMIC_ENGINE_FORWARD,
    VALID_HEMODYNAMIC_MODES,
)


class CommunityAssessmentConfig(BaseModel):
    """Configuration for community health assessment survey execution."""
    target_min_age: float = Field(default=45.0, description="Minimum age for evaluation cohort eligibility")
    assessment_date: datetime = Field(
        default=datetime(2024, 6, 15, 9, 30, 0),
        description="Fixed survey assessment reference timestamp"
    )
    sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Sampling fraction of eligible population")
    non_response_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Expected unassessable/refusal rate")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    bp_protocol_config: Optional[BpMeasurementProtocolConfig] = Field(
        default=None,
        description="Configuration for multi-reading blood pressure measurement protocol"
    )
    hemodynamic_engine_mode: str = Field(
        default=HEMODYNAMIC_ENGINE_LEGACY,
        description="Hemodynamic engine mode: LEGACY_CONDITIONAL (default) or FORWARD_STATE_SPACE"
    )
    forward_hemodynamic_config: Optional[ForwardHemodynamicConfig] = Field(
        default=None,
        description="Optional configuration for the experimental forward hemodynamic engine"
    )

    @model_validator(mode="after")
    def validate_hemodynamic_engine_mode(self) -> "CommunityAssessmentConfig":
        if self.hemodynamic_engine_mode not in VALID_HEMODYNAMIC_MODES:
            raise ValueError(
                f"Invalid hemodynamic_engine_mode '{self.hemodynamic_engine_mode}'. "
                f"Supported modes are: {sorted(list(VALID_HEMODYNAMIC_MODES))}"
            )
        return self


def is_condition_active_at(
    patient: PatientContext,
    condition_code: str,
    reference_time: datetime,
) -> bool:
    """Evaluate whether a condition was active in the patient at a specific point in time.

    Rules:
    1. Baseline Conditions: If condition_code is in baseline_conditions or chronic_conditions,
       it was present at baseline (observation_start <= reference_time).
    2. Latent Conditions:
       - Must have onset_time <= reference_time (inclusive lower bound).
       - If condition was resolved before or at reference_time (resolved is True and resolved_time <= reference_time),
         it is no longer active at reference_time.
       - If onset_time is present and onset_time > reference_time, it is NOT active at reference_time.
       - If onset_time is absent (e.g. test fixtures/mock contexts), defaults to True for backward compatibility.
    """
    if condition_code in patient.baseline_conditions:
        return True
    if any(c == condition_code or condition_code in c for c in patient.chronic_conditions):
        return True

    l_info = patient.latent_conditions.get(condition_code)
    if not l_info:
        return False

    onset = l_info.get("onset_time")
    # Future onset check (exclusive of past/present)
    if onset is not None and onset > reference_time:
        return False

    # Resolution check
    if l_info.get("resolved") and l_info.get("resolved_time"):
        resolved_time = l_info.get("resolved_time")
        if resolved_time <= reference_time:
            return False

    return True


class CommunityAssessmentGenerator:
    """Generates independent community health assessments for a synthetic population."""

    def __init__(self, config: Optional[CommunityAssessmentConfig] = None, base_seed: int = 42):
        self.config = config or CommunityAssessmentConfig(seed=base_seed)
        self.base_seed = self.config.seed
        proto_cfg = self.config.bp_protocol_config or create_lasi_tri_measurement_protocol()
        self.protocol_simulator = BpMeasurementProtocolSimulator(proto_cfg)
        self.all_bp_readings: List[CommunityBpReading] = []
        self.latent_hemodynamic_states: Dict[str, LatentHemodynamicState] = {}

        if self.config.hemodynamic_engine_mode == HEMODYNAMIC_ENGINE_FORWARD:
            fwd_cfg = self.config.forward_hemodynamic_config or ForwardHemodynamicConfig(
                engine_mode=HEMODYNAMIC_ENGINE_FORWARD
            )
            self.forward_simulator: Optional[ForwardHemodynamicSimulator] = ForwardHemodynamicSimulator(
                config=fwd_cfg,
                base_seed=self.base_seed,
            )
        else:
            self.forward_simulator = None

    def get_bp_readings(self) -> List[CommunityBpReading]:
        """Return all constituent blood pressure readings generated in the last sweep."""
        return self.all_bp_readings

    def get_latent_hemodynamic_states(self) -> Dict[str, LatentHemodynamicState]:
        """Return all latent hemodynamic states generated during the sweep (if forward mode was active)."""
        return self.latent_hemodynamic_states

    def generate(
        self,
        patients: Dict[str, PatientContext],
        active_antihypertensive_pids: Optional[set] = None,
        prescriptions: Optional[Any] = None,
        encounters: Optional[Any] = None,
    ) -> List[CommunityAssessment]:
        """Execute independent community survey sweep across all eligible synthetic patients.

        Args:
            patients: Map of patient_id -> PatientContext
            active_antihypertensive_pids: Optional set of patient IDs on active antihypertensive medication
            prescriptions: Optional prescription store / collection to dynamically derive active Rx
            encounters: Optional encounter store / collection for prescription linkage

        Returns:
            List of CommunityAssessment records
        """
        if active_antihypertensive_pids is not None:
            active_rx = active_antihypertensive_pids
        elif prescriptions is not None:
            from synapse_simulator.evaluation.medication_status import (
                is_prescription_active_at,
                DEFAULT_ANTIHYPERTENSIVE_KEYWORDS,
            )
            enc_map = {}
            if encounters:
                if isinstance(encounters, dict):
                    enc_map = encounters
                elif isinstance(encounters, list):
                    enc_map = {e.get("encounter_id"): e for e in encounters if e.get("encounter_id")}

            rx_list = prescriptions.values() if isinstance(prescriptions, dict) else prescriptions
            active_rx = set()
            for rx in rx_list:
                enc = enc_map.get(rx.get("encounter_id"))
                if is_prescription_active_at(
                    rx,
                    self.config.assessment_date,
                    encounter=enc,
                    target_drug_keywords=DEFAULT_ANTIHYPERTENSIVE_KEYWORDS,
                ):
                    active_rx.add(rx.get("patient_id"))
        else:
            active_rx = set()

        assessments: List[CommunityAssessment] = []
        self.all_bp_readings = []
        self.latent_hemodynamic_states = {}

        # Sort patient IDs for deterministic execution order
        sorted_pids = sorted(patients.keys())

        for pid in sorted_pids:
            p = patients[pid]

            # 1. Eligibility gate: Age >= target_min_age and alive at assessment date
            if p.birth_date:
                effective_age = (
                    self.config.assessment_date.year
                    - p.birth_date.year
                    - (
                        (self.config.assessment_date.month, self.config.assessment_date.day)
                        < (p.birth_date.month, p.birth_date.day)
                    )
                )
            else:
                effective_age = p.age

            if effective_age < self.config.target_min_age:
                continue

            if p.death_date is not None:
                if p.death_date <= self.config.assessment_date:
                    continue
            elif not p.is_alive:
                # Deceased with missing death timestamp cannot be verified as alive at assessment
                continue

            # Deterministic per-patient PRNG derived from base seed and patient ID
            pat_rng = random.Random(f"{self.base_seed}_comm_eval_{pid}")

            # 2. Probability Sampling
            if self.config.sampling_rate < 1.0:
                if pat_rng.random() > self.config.sampling_rate:
                    continue

            # 3. Non-response / Refusal / Unassessable status
            if self.config.non_response_rate > 0.0 and pat_rng.random() < self.config.non_response_rate:
                refused_readings = self.protocol_simulator.create_refused_readings(
                    assessment_id=f"ca-{pid}",
                    patient_id=pid,
                    assessment_date=self.config.assessment_date,
                )
                self.all_bp_readings.extend(refused_readings)
                assessments.append(CommunityAssessment(
                    assessment_id=f"ca-{pid}",
                    patient_id=pid,
                    timestamp=self.config.assessment_date,
                    assessment_type="COMMUNITY_HEALTH_ASSESSMENT",
                    sbp=None,
                    dbp=None,
                    pulse_pressure=None,
                    unit="mmHg",
                    survey_weight=round(1.0 / self.config.sampling_rate, 4) if self.config.sampling_rate > 0 else 1.0,
                    status="REFUSED",
                    provenance="COMMUNITY_HEALTH_ASSESSMENT_LAYER",
                    is_assessable=False,
                    protocol_id=self.protocol_simulator.config.protocol_id,
                    derivation_category=BpDerivationCategory.NO_VALID_READING.value,
                ))
                continue

            # 4. Underlying latent physiological health status at assessment date
            if self.config.hemodynamic_engine_mode == HEMODYNAMIC_ENGINE_FORWARD and self.forward_simulator is not None:
                latent_state = self.forward_simulator.get_latent_state_at(
                    patient=p,
                    target_time=self.config.assessment_date,
                    prescriptions=prescriptions if prescriptions is not None else active_rx,
                )
                self.latent_hemodynamic_states[pid] = latent_state
                underlying_sbp = latent_state.latent_sbp
                underlying_dbp = latent_state.latent_dbp
            else:
                has_htn = is_condition_active_at(p, "I10", self.config.assessment_date)
                is_treated = pid in active_rx

                # Measure vital signs based on established medical knowledge ranges
                # Normotensive range: SBP [110.0, 135.0], DBP [70.0, 84.0] (from adult/elderly knowledge base)
                # Hypertensive treated range: SBP [120.0, 150.0], DBP [75.0, 92.0] (from follow-up module range)
                # Hypertensive untreated range: SBP [145.0, 168.0], DBP [90.0, 104.0] (from screening module range)
                if has_htn:
                    if is_treated:
                        underlying_sbp = round(pat_rng.uniform(120.0, 150.0), 1)
                        underlying_dbp = round(pat_rng.uniform(75.0, 92.0), 1)
                    else:
                        underlying_sbp = round(pat_rng.uniform(145.0, 168.0), 1)
                        underlying_dbp = round(pat_rng.uniform(90.0, 104.0), 1)
                else:
                    underlying_sbp = round(pat_rng.uniform(110.0, 135.0), 1)
                    underlying_dbp = round(pat_rng.uniform(70.0, 84.0), 1)

                # Physiological safeguard: pulse pressure (PP = SBP - DBP) must be >= 20 mmHg
                if underlying_sbp - underlying_dbp < 20.0:
                    underlying_sbp = round(underlying_dbp + 25.0, 1)

            # Simulate protocolized readings and calculate final analysis measurement
            proto_result = self.protocol_simulator.simulate(
                underlying_sbp=underlying_sbp,
                underlying_dbp=underlying_dbp,
                assessment_id=f"ca-{pid}",
                patient_id=pid,
                assessment_date=self.config.assessment_date,
                pat_rng=pat_rng,
            )
            self.all_bp_readings.extend(proto_result.readings)

            weight = round(1.0 / self.config.sampling_rate, 4) if self.config.sampling_rate > 0 else 1.0

            assessments.append(CommunityAssessment(
                assessment_id=f"ca-{pid}",
                patient_id=pid,
                timestamp=self.config.assessment_date,
                assessment_type="COMMUNITY_HEALTH_ASSESSMENT",
                sbp=proto_result.final_sbp,
                dbp=proto_result.final_dbp,
                pulse_pressure=proto_result.final_pulse_pressure,
                unit="mmHg",
                survey_weight=weight,
                status="COMPLETED" if proto_result.is_valid else "UNASSESSABLE",
                provenance="COMMUNITY_HEALTH_ASSESSMENT_LAYER",
                is_assessable=proto_result.is_valid,
                protocol_id=proto_result.protocol_id,
                derivation_category=proto_result.derivation_category,
            ))

        return assessments
