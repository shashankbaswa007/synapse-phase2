"""
Configurable Multi-Reading Blood Pressure Measurement Protocol for SYNAPSE Phase 2.

Provides a scientifically defensible, protocolized blood pressure measurement layer
for independent community/household health assessments.

Distinguishes:
1. Patient's underlying modeled resting BP state (latent physiological status).
2. Individual observed readings (sequential seated oscillometric measurements).
3. The measurement protocol specification (number of readings, selection indices, fallback rules).
4. The final derived analysis values (SBP, DBP, pulse pressure).
5. Measurement completeness, plausibility constraints, and quality status.

Protocol Reference:
Aligned with the Longitudinal Ageing Study in India (LASI Wave 1) Biomarker Protocol:
- Device: Omron HEM-7121 digital oscillometric monitor.
- Seated measurement with 5-minute quiet resting intervals between readings.
- Primary analysis value: Arithmetic mean of Reading 2 and Reading 3 (discarding Reading 1
  to eliminate situational white-coat alerting bias).
- Fully configurable for alternative survey protocols (e.g. single-reading baseline).
"""

from datetime import datetime, timedelta
from enum import Enum
import math
import random
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from pydantic import BaseModel, Field


class BpReadingStatus(str, Enum):
    """Quality status of an individual blood pressure reading."""
    VALID = "VALID"
    OUT_OF_RANGE_SBP = "OUT_OF_RANGE_SBP"
    OUT_OF_RANGE_DBP = "OUT_OF_RANGE_DBP"
    OUT_OF_RANGE_BOTH = "OUT_OF_RANGE_BOTH"
    PHYSIOLOGICAL_PP_VIOLATION = "PHYSIOLOGICAL_PP_VIOLATION"
    REFUSED = "REFUSED"
    DEVICE_ERROR = "DEVICE_ERROR"
    UNASSESSABLE = "UNASSESSABLE"
    INSUFFICIENT_VALID_READINGS = "INSUFFICIENT_VALID_READINGS"


class BpDerivationCategory(str, Enum):
    """Categorical classification of the blood pressure derivation method applied."""
    PROTOCOL_MEAN_READINGS_2_AND_3 = "PROTOCOL_MEAN_READINGS_2_AND_3"
    SINGLE_READING_BASELINE = "SINGLE_READING_BASELINE"
    FALLBACK_READING_2_ONLY = "FALLBACK_READING_2_ONLY"
    FALLBACK_READING_3_ONLY = "FALLBACK_READING_3_ONLY"
    FALLBACK_READING_1_ONLY = "FALLBACK_READING_1_ONLY"
    INSUFFICIENT_VALID_READINGS = "INSUFFICIENT_VALID_READINGS"
    NO_VALID_READING = "NO_VALID_READING"


class CommunityBpReading(BaseModel):
    """Structured record of an individual community blood pressure measurement reading."""
    assessment_id: str = Field(..., description="Foreign key to community assessment record")
    patient_id: str = Field(..., description="Foreign key to synthetic patient record")
    reading_number: int = Field(..., ge=1, description="1-indexed sequence order of reading (1, 2, 3...)")
    timestamp: datetime = Field(..., description="Timestamp of individual reading")
    sbp: Optional[float] = Field(default=None, description="Systolic blood pressure (mmHg)")
    dbp: Optional[float] = Field(default=None, description="Diastolic blood pressure (mmHg)")
    pulse_pressure: Optional[float] = Field(default=None, description="Pulse pressure SBP - DBP (mmHg)")
    unit: str = Field(default="mmHg", description="Blood pressure measurement unit")
    status: str = Field(default="VALID", description="Individual reading quality status")
    protocol_id: str = Field(default="LASI_WAVE1_TRI_MEASUREMENT", description="Measurement protocol identifier")
    protocol_version: str = Field(default="1.0.0", description="Protocol specification version")
    provenance: str = Field(
        default="COMMUNITY_HEALTH_ASSESSMENT_LAYER",
        description="Data provenance establishing independent community survey origin"
    )

    def __init__(
        self,
        assessment_id: str = "",
        patient_id: str = "",
        reading_number: int = 1,
        timestamp: Optional[datetime] = None,
        sbp: Optional[float] = None,
        dbp: Optional[float] = None,
        pulse_pressure: Optional[float] = None,
        unit: str = "mmHg",
        status: str = "VALID",
        protocol_id: str = "LASI_WAVE1_TRI_MEASUREMENT",
        protocol_version: str = "1.0.0",
        provenance: str = "COMMUNITY_HEALTH_ASSESSMENT_LAYER",
        **kwargs: Any,
    ):
        if assessment_id or kwargs:
            data = {
                "assessment_id": assessment_id,
                "patient_id": patient_id,
                "reading_number": reading_number,
                "timestamp": timestamp if timestamp is not None else datetime.now(),
                "sbp": sbp,
                "dbp": dbp,
                "pulse_pressure": pulse_pressure,
                "unit": unit,
                "status": status,
                "protocol_id": protocol_id,
                "protocol_version": protocol_version,
                "provenance": provenance,
            }
            data.update(kwargs)
            super().__init__(**data)
        else:
            super().__init__(**kwargs)


class BpMeasurementProtocolConfig(BaseModel):
    """Configuration specification for the community blood pressure measurement protocol."""
    protocol_id: str = Field(default="LASI_WAVE1_TRI_MEASUREMENT", description="Protocol identifier")
    protocol_version: str = Field(default="1.0.0", description="Semantic version of protocol")
    number_of_readings: int = Field(default=3, ge=1, le=10, description="Total sequential readings targeted")
    selected_reading_indices: List[int] = Field(
        default_factory=lambda: [2, 3],
        description="1-indexed sequence numbers of readings averaged for final analysis value"
    )
    required_valid_readings: int = Field(
        default=2,
        ge=1,
        description="Minimum valid readings required among selected readings to calculate mean"
    )
    allow_single_reading_fallback: bool = Field(
        default=False,
        description="Whether to permit fallback to Reading 2, Reading 3, or Reading 1 when target readings are missing"
    )
    reading_interval_minutes: float = Field(
        default=5.0,
        ge=0.0,
        description="Resting interval between consecutive readings in minutes"
    )
    min_sbp: float = Field(default=60.0, description="Minimum plausible SBP threshold in mmHg")
    max_sbp: float = Field(default=280.0, description="Maximum plausible SBP threshold in mmHg")
    min_dbp: float = Field(default=40.0, description="Minimum plausible DBP threshold in mmHg")
    max_dbp: float = Field(default=160.0, description="Maximum plausible DBP threshold in mmHg")
    min_pulse_pressure: float = Field(default=20.0, description="Minimum plausible pulse pressure (SBP - DBP)")
    measurement_noise_enabled: bool = Field(
        default=True,
        description="Whether to simulate within-visit biological / alerting measurement variability"
    )
    noise_mode: str = Field(
        default="SYMMETRICAL_UNBIASED",
        description="Noise model: 'SYMMETRICAL_UNBIASED' (preserves resting mean), 'AUTOREGRESSIVE_AR1' (stationary AR(1) error), 'INDEPENDENT_GAUSSIAN', or 'NONE'"
    )
    inter_reading_correlation: float = Field(
        default=0.70,
        ge=-1.0,
        le=1.0,
        description="Autocorrelation between consecutive readings for AUTOREGRESSIVE_AR1 mode"
    )
    reading1_alerting_sbp: float = Field(
        default=3.5,
        description="Mean white-coat situational alerting elevation on reading 1 SBP (mmHg)"
    )
    reading1_alerting_dbp: float = Field(
        default=1.5,
        description="Mean white-coat situational alerting elevation on reading 1 DBP (mmHg)"
    )
    within_visit_noise_sd: float = Field(
        default=1.8,
        description="Within-visit measurement standard deviation for resting readings (mmHg)"
    )


class BpProtocolResult(BaseModel):
    """Derived analysis measurement resulting from application of the measurement protocol."""
    final_sbp: Optional[float] = Field(default=None, description="Final protocol-derived SBP (mmHg)")
    final_dbp: Optional[float] = Field(default=None, description="Final protocol-derived DBP (mmHg)")
    final_pulse_pressure: Optional[float] = Field(default=None, description="Final pulse pressure (mmHg)")
    derivation_category: str = Field(..., description="Derivation rule category classification")
    is_valid: bool = Field(default=True, description="Whether final measurement is assessable and valid")
    status: str = Field(default="VALID", description="Final measurement quality and completeness status")
    protocol_id: str = Field(default="LASI_WAVE1_TRI_MEASUREMENT", description="Protocol identifier")
    protocol_version: str = Field(default="1.0.0", description="Protocol semantic version")
    readings_used_count: int = Field(default=0, description="Count of readings included in final calculation")
    readings_used_indices: List[int] = Field(default_factory=list, description="Indices of readings included in final calculation")
    readings: List[CommunityBpReading] = Field(default_factory=list, description="Constituent individual readings")


DEFAULT_MIN_SBP = 60.0
DEFAULT_MAX_SBP = 280.0
DEFAULT_MIN_DBP = 40.0
DEFAULT_MAX_DBP = 160.0
DEFAULT_MIN_PULSE_PRESSURE = 20.0


def validate_reading_values(
    sbp: Optional[float],
    dbp: Optional[float],
    config: Optional[BpMeasurementProtocolConfig] = None,
) -> Tuple[bool, str]:
    """Validate physiological plausibility of an individual SBP/DBP measurement reading.

    Checks:
    1. Nullity check (both values must be non-null).
    2. Boundary check: SBP in [min_sbp, max_sbp] and DBP in [min_dbp, max_dbp].
    3. Physiological check: Pulse Pressure (SBP - DBP) >= min_pulse_pressure.
    """
    if sbp is None or dbp is None:
        return False, BpReadingStatus.UNASSESSABLE.value

    min_sbp = config.min_sbp if config else DEFAULT_MIN_SBP
    max_sbp = config.max_sbp if config else DEFAULT_MAX_SBP
    min_dbp = config.min_dbp if config else DEFAULT_MIN_DBP
    max_dbp = config.max_dbp if config else DEFAULT_MAX_DBP
    min_pp = config.min_pulse_pressure if config else DEFAULT_MIN_PULSE_PRESSURE

    sbp_ok = min_sbp <= sbp <= max_sbp
    dbp_ok = min_dbp <= dbp <= max_dbp

    if not sbp_ok and not dbp_ok:
        return False, BpReadingStatus.OUT_OF_RANGE_BOTH.value
    if not sbp_ok:
        return False, BpReadingStatus.OUT_OF_RANGE_SBP.value
    if not dbp_ok:
        return False, BpReadingStatus.OUT_OF_RANGE_DBP.value

    if sbp - dbp < min_pp:
        return False, BpReadingStatus.PHYSIOLOGICAL_PP_VIOLATION.value

    return True, BpReadingStatus.VALID.value


def calculate_protocol_bp(
    readings: List[CommunityBpReading],
    config: Optional[BpMeasurementProtocolConfig] = None,
) -> BpProtocolResult:
    """Apply the configured measurement protocol to derive the final analysis blood pressure.

    Supports:
    - Independent averaging of SBP and DBP.
    - Configurable selection of reading sequence numbers (e.g. readings 2 and 3).
    - Threshold on minimum required valid readings.
    - Explicit fallback hierarchy when fallback mode is enabled, or strict rejection
      when fallback mode is disabled.
    - Physiological pulse pressure verification on final derived values.
    """
    cfg = config or BpMeasurementProtocolConfig()

    # Map readings by reading_number
    reading_map: Dict[int, CommunityBpReading] = {r.reading_number: r for r in readings}

    # If single reading baseline mode
    if cfg.number_of_readings == 1:
        r1 = reading_map.get(1)
        if r1 and r1.sbp is not None and r1.dbp is not None and r1.status == BpReadingStatus.VALID.value:
            pp = round(r1.sbp - r1.dbp, 1)
            return BpProtocolResult(
                final_sbp=r1.sbp,
                final_dbp=r1.dbp,
                final_pulse_pressure=pp,
                derivation_category=BpDerivationCategory.SINGLE_READING_BASELINE.value,
                is_valid=True,
                status=BpReadingStatus.VALID.value,
                protocol_id=cfg.protocol_id,
                protocol_version=cfg.protocol_version,
                readings_used_count=1,
                readings_used_indices=[1],
                readings=readings,
            )
        else:
            return BpProtocolResult(
                final_sbp=None,
                final_dbp=None,
                final_pulse_pressure=None,
                derivation_category=BpDerivationCategory.NO_VALID_READING.value,
                is_valid=False,
                status=BpReadingStatus.UNASSESSABLE.value,
                protocol_id=cfg.protocol_id,
                protocol_version=cfg.protocol_version,
                readings_used_count=0,
                readings_used_indices=[],
                readings=readings,
            )

    # Multi-reading evaluation: identify valid readings among selected indices
    selected_readings: List[CommunityBpReading] = []
    for idx in cfg.selected_reading_indices:
        r = reading_map.get(idx)
        if r and r.sbp is not None and r.dbp is not None:
            is_valid, _ = validate_reading_values(r.sbp, r.dbp, cfg)
            if is_valid:
                selected_readings.append(r)

    # Primary protocol evaluation
    if len(selected_readings) >= cfg.required_valid_readings:
        mean_sbp = round(sum(r.sbp for r in selected_readings) / float(len(selected_readings)), 1)
        mean_dbp = round(sum(r.dbp for r in selected_readings) / float(len(selected_readings)), 1)
        if mean_sbp - mean_dbp < cfg.min_pulse_pressure:
            mean_sbp = round(mean_dbp + cfg.min_pulse_pressure, 1)
        final_pp = round(mean_sbp - mean_dbp, 1)

        category = BpDerivationCategory.PROTOCOL_MEAN_READINGS_2_AND_3.value
        used_indices = [r.reading_number for r in selected_readings]
        return BpProtocolResult(
            final_sbp=mean_sbp,
            final_dbp=mean_dbp,
            final_pulse_pressure=final_pp,
            derivation_category=category,
            is_valid=True,
            status=BpReadingStatus.VALID.value,
            protocol_id=cfg.protocol_id,
            protocol_version=cfg.protocol_version,
            readings_used_count=len(selected_readings),
            readings_used_indices=used_indices,
            readings=readings,
        )

    # Fallback evaluation (if permitted by protocol config)
    if cfg.allow_single_reading_fallback:
        # Check Reading 2
        r2 = reading_map.get(2)
        if r2 and r2.sbp is not None and r2.dbp is not None:
            v2, _ = validate_reading_values(r2.sbp, r2.dbp, cfg)
            if v2:
                pp2 = round(r2.sbp - r2.dbp, 1)
                return BpProtocolResult(
                    final_sbp=r2.sbp,
                    final_dbp=r2.dbp,
                    final_pulse_pressure=pp2,
                    derivation_category=BpDerivationCategory.FALLBACK_READING_2_ONLY.value,
                    is_valid=True,
                    status=BpReadingStatus.VALID.value,
                    protocol_id=cfg.protocol_id,
                    protocol_version=cfg.protocol_version,
                    readings_used_count=1,
                    readings_used_indices=[2],
                    readings=readings,
                )

        # Check Reading 3
        r3 = reading_map.get(3)
        if r3 and r3.sbp is not None and r3.dbp is not None:
            v3, _ = validate_reading_values(r3.sbp, r3.dbp, cfg)
            if v3:
                pp3 = round(r3.sbp - r3.dbp, 1)
                return BpProtocolResult(
                    final_sbp=r3.sbp,
                    final_dbp=r3.dbp,
                    final_pulse_pressure=pp3,
                    derivation_category=BpDerivationCategory.FALLBACK_READING_3_ONLY.value,
                    is_valid=True,
                    status=BpReadingStatus.VALID.value,
                    protocol_id=cfg.protocol_id,
                    protocol_version=cfg.protocol_version,
                    readings_used_count=1,
                    readings_used_indices=[3],
                    readings=readings,
                )

        # Check Reading 1
        r1 = reading_map.get(1)
        if r1 and r1.sbp is not None and r1.dbp is not None:
            v1, _ = validate_reading_values(r1.sbp, r1.dbp, cfg)
            if v1:
                pp1 = round(r1.sbp - r1.dbp, 1)
                return BpProtocolResult(
                    final_sbp=r1.sbp,
                    final_dbp=r1.dbp,
                    final_pulse_pressure=pp1,
                    derivation_category=BpDerivationCategory.FALLBACK_READING_1_ONLY.value,
                    is_valid=True,
                    status=BpReadingStatus.VALID.value,
                    protocol_id=cfg.protocol_id,
                    protocol_version=cfg.protocol_version,
                    readings_used_count=1,
                    readings_used_indices=[1],
                    readings=readings,
                )

    # Insufficient or no valid readings
    any_valid = any(
        r.sbp is not None and r.dbp is not None and validate_reading_values(r.sbp, r.dbp, cfg)[0]
        for r in readings
    )
    category = (
        BpDerivationCategory.INSUFFICIENT_VALID_READINGS.value
        if any_valid
        else BpDerivationCategory.NO_VALID_READING.value
    )
    final_status = (
        BpReadingStatus.INSUFFICIENT_VALID_READINGS.value
        if (any_valid or len(selected_readings) < cfg.required_valid_readings)
        else BpReadingStatus.UNASSESSABLE.value
    )

    return BpProtocolResult(
        final_sbp=None,
        final_dbp=None,
        final_pulse_pressure=None,
        derivation_category=category,
        is_valid=False,
        status=final_status,
        protocol_id=cfg.protocol_id,
        protocol_version=cfg.protocol_version,
        readings_used_count=0,
        readings_used_indices=[],
        readings=readings,
    )


class BpMeasurementProtocolSimulator:
    """Simulates realistic protocolized blood pressure measurements for synthetic patients."""

    def __init__(self, config: Optional[BpMeasurementProtocolConfig] = None):
        self.config = config or BpMeasurementProtocolConfig()

    def simulate(
        self,
        underlying_sbp: float,
        underlying_dbp: float,
        assessment_id: str,
        patient_id: str,
        assessment_date: datetime,
        pat_rng: random.Random,
    ) -> BpProtocolResult:
        """Simulate sequential measurements and calculate protocol analysis values.

        Measurement model:
        1. Single-reading baseline: Emits single observation at underlying values.
        2. Tri-reading protocol:
           - Reading 1: White-coat situational alerting elevation (+delta SBP, +delta DBP).
           - Readings 2 & 3: Repeated resting measurements.
           - Symmetrical zero-mean variation: Reading 2 (+epsilon), Reading 3 (-epsilon),
             ensuring the protocol average (mean of readings 2 and 3) is exactly centered
             on the patient's underlying resting physiological blood pressure, preserving
             population calibration without systematic bias.
        """
        readings: List[CommunityBpReading] = []

        if self.config.number_of_readings == 1:
            # Baseline single reading mode
            sbp1 = round(underlying_sbp, 1)
            dbp1 = round(underlying_dbp, 1)
            if sbp1 - dbp1 < self.config.min_pulse_pressure:
                sbp1 = round(dbp1 + self.config.min_pulse_pressure, 1)
            pp1 = round(sbp1 - dbp1, 1)
            is_valid, status = validate_reading_values(sbp1, dbp1, self.config)

            readings.append(CommunityBpReading(
                assessment_id=assessment_id,
                patient_id=patient_id,
                reading_number=1,
                timestamp=assessment_date,
                sbp=sbp1 if is_valid else None,
                dbp=dbp1 if is_valid else None,
                pulse_pressure=pp1 if is_valid else None,
                unit="mmHg",
                status=status,
                protocol_id=self.config.protocol_id,
                protocol_version=self.config.protocol_version,
            ))
            return calculate_protocol_bp(readings, self.config)

        # Multi-reading protocol execution (e.g. 3 readings)
        if self.config.measurement_noise_enabled:
            # Reading 1 situational alerting effect
            alert_sbp = max(0.5, pat_rng.gauss(self.config.reading1_alerting_sbp, 0.8))
            alert_dbp = max(0.2, pat_rng.gauss(self.config.reading1_alerting_dbp, 0.4))

            # Resting within-visit variation for readings 2 & 3
            if self.config.noise_mode == "SYMMETRICAL_UNBIASED":
                eps_sbp = round(pat_rng.gauss(0.0, self.config.within_visit_noise_sd), 1)
                eps_dbp = round(pat_rng.gauss(0.0, self.config.within_visit_noise_sd * 0.6), 1)
                # Keep within bound
                eps_sbp = max(-5.0, min(5.0, eps_sbp))
                eps_dbp = max(-3.0, min(3.0, eps_dbp))

                delta_sbp = [round(alert_sbp, 1), eps_sbp, -eps_sbp]
                delta_dbp = [round(alert_dbp, 1), eps_dbp, -eps_dbp]
            elif self.config.noise_mode == "AUTOREGRESSIVE_AR1":
                rho = self.config.inter_reading_correlation
                u2_sbp = pat_rng.gauss(0.0, self.config.within_visit_noise_sd)
                u3_sbp = pat_rng.gauss(0.0, self.config.within_visit_noise_sd)
                eps2_sbp = round(u2_sbp, 1)
                eps3_sbp = round(rho * u2_sbp + math.sqrt(max(0.0, 1.0 - rho * rho)) * u3_sbp, 1)

                sd_dbp = self.config.within_visit_noise_sd * 0.6
                u2_dbp = pat_rng.gauss(0.0, sd_dbp)
                u3_dbp = pat_rng.gauss(0.0, sd_dbp)
                eps2_dbp = round(u2_dbp, 1)
                eps3_dbp = round(rho * u2_dbp + math.sqrt(max(0.0, 1.0 - rho * rho)) * u3_dbp, 1)

                delta_sbp = [round(alert_sbp, 1), eps2_sbp, eps3_sbp]
                delta_dbp = [round(alert_dbp, 1), eps2_dbp, eps3_dbp]
            elif self.config.noise_mode == "INDEPENDENT_GAUSSIAN":
                delta_sbp = [
                    round(alert_sbp, 1),
                    round(pat_rng.gauss(0.0, self.config.within_visit_noise_sd), 1),
                    round(pat_rng.gauss(0.0, self.config.within_visit_noise_sd), 1),
                ]
                delta_dbp = [
                    round(alert_dbp, 1),
                    round(pat_rng.gauss(0.0, self.config.within_visit_noise_sd * 0.6), 1),
                    round(pat_rng.gauss(0.0, self.config.within_visit_noise_sd * 0.6), 1),
                ]
            else:  # NONE
                delta_sbp = [0.0] * self.config.number_of_readings
                delta_dbp = [0.0] * self.config.number_of_readings
        else:
            delta_sbp = [0.0] * self.config.number_of_readings
            delta_dbp = [0.0] * self.config.number_of_readings

        for k in range(1, self.config.number_of_readings + 1):
            r_ts = assessment_date + timedelta(minutes=(k - 1) * self.config.reading_interval_minutes)
            d_s = delta_sbp[k - 1] if k - 1 < len(delta_sbp) else 0.0
            d_d = delta_dbp[k - 1] if k - 1 < len(delta_dbp) else 0.0

            r_sbp = round(underlying_sbp + d_s, 1)
            r_dbp = round(underlying_dbp + d_d, 1)

            # Physiological safeguard per reading
            if r_sbp - r_dbp < self.config.min_pulse_pressure:
                r_sbp = round(r_dbp + self.config.min_pulse_pressure, 1)

            r_pp = round(r_sbp - r_dbp, 1)
            is_valid, status = validate_reading_values(r_sbp, r_dbp, self.config)

            readings.append(CommunityBpReading(
                assessment_id=assessment_id,
                patient_id=patient_id,
                reading_number=k,
                timestamp=r_ts,
                sbp=r_sbp if is_valid else None,
                dbp=r_dbp if is_valid else None,
                pulse_pressure=r_pp if is_valid else None,
                unit="mmHg",
                status=status,
                protocol_id=self.config.protocol_id,
                protocol_version=self.config.protocol_version,
            ))

        return calculate_protocol_bp(readings, self.config)

    def create_refused_readings(
        self,
        assessment_id: str,
        patient_id: str,
        assessment_date: datetime,
    ) -> List[CommunityBpReading]:
        """Create placeholder readings for refused / unavailable assessments."""
        readings = []
        for k in range(1, self.config.number_of_readings + 1):
            r_ts = assessment_date + timedelta(minutes=(k - 1) * self.config.reading_interval_minutes)
            readings.append(CommunityBpReading(
                assessment_id=assessment_id,
                patient_id=patient_id,
                reading_number=k,
                timestamp=r_ts,
                sbp=None,
                dbp=None,
                pulse_pressure=None,
                unit="mmHg",
                status=BpReadingStatus.REFUSED.value,
                protocol_id=self.config.protocol_id,
                protocol_version=self.config.protocol_version,
            ))
        return readings


def create_lasi_tri_measurement_protocol(
    allow_fallback: bool = False,
    allow_single_reading_fallback: Optional[bool] = None,
    noise_enabled: bool = True,
    noise_mode: str = "SYMMETRICAL_UNBIASED",
) -> BpMeasurementProtocolConfig:
    """Factory for standard LASI Wave 1 triplicated measurement protocol (mean of 2nd & 3rd readings)."""
    if allow_single_reading_fallback is not None:
        allow_fallback = allow_single_reading_fallback
    return BpMeasurementProtocolConfig(
        protocol_id="LASI_WAVE1_TRI_MEASUREMENT",
        protocol_version="1.0.0",
        number_of_readings=3,
        selected_reading_indices=[2, 3],
        required_valid_readings=2,
        allow_single_reading_fallback=allow_fallback,
        reading_interval_minutes=5.0,
        measurement_noise_enabled=noise_enabled,
        noise_mode=noise_mode,
    )


def create_single_reading_baseline_protocol() -> BpMeasurementProtocolConfig:
    """Factory for backward-compatible single-reading baseline protocol."""
    return BpMeasurementProtocolConfig(
        protocol_id="SINGLE_READING_BASELINE",
        protocol_version="1.0.0",
        number_of_readings=1,
        selected_reading_indices=[1],
        required_valid_readings=1,
        allow_single_reading_fallback=False,
        reading_interval_minutes=0.0,
        measurement_noise_enabled=False,
        noise_mode="NONE",
    )
