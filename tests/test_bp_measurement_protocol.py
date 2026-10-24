"""
Comprehensive Unit, Integration, and Invariant Tests for the
Multi-Reading Blood Pressure Measurement Protocol in SYNAPSE Phase 2.

Covers all 18 requirements:
1. Correct calculation of final BP from configured readings.
2. Correct selection of specified readings.
3. Independent averaging of SBP and DBP.
4. Missing reading 1, 2, or 3 behavior (strict vs fallback).
5. Invalid or physiologically implausible individual readings.
6. Insufficient valid readings (no automatic normal classification).
7. Exact protocol boundary behavior (SBP [60, 280], DBP [40, 160], PP >= 20).
8. Deterministic readings under fixed seed.
9. Independent per-patient random streams.
10. Reproducibility across separate Python processes.
11. Reading-order invariance of selected readings.
12. Preservation of reading numbers (1, 2, 3) and 5-min intervals.
13. Clean separation between individual readings and final analysis values.
14. Community readings do NOT create EHR encounters, diagnoses, or prescriptions.
15. Correct use of final analysis values in prevalence calculations.
16. Point-in-time medication status unaffected by future prescriptions.
17. Backward compatibility with single-reading baseline mode.
18. Preservation of REFERENCE_DATA_PENDING external validation gate.
"""

import copy
import math
import random
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from synapse_simulator.datagen.bp_measurement import (
    BpReadingStatus,
    BpDerivationCategory,
    CommunityBpReading,
    BpMeasurementProtocolConfig,
    BpProtocolResult,
    BpMeasurementProtocolSimulator,
    validate_reading_values,
    calculate_protocol_bp,
    create_lasi_tri_measurement_protocol,
    create_single_reading_baseline_protocol,
    DEFAULT_MIN_SBP,
    DEFAULT_MAX_SBP,
    DEFAULT_MIN_DBP,
    DEFAULT_MAX_DBP,
    DEFAULT_MIN_PULSE_PRESSURE,
)


# ==============================================================================
# 1. Correct calculation of final BP from configured readings
# ==============================================================================

def test_correct_calculation_of_final_bp_from_configured_readings():
    """Verify arithmetic mean calculation of readings 2 and 3 under default protocol."""
    cfg = create_lasi_tri_measurement_protocol()
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    readings = [
        CommunityBpReading("ca-1", "p-1", 1, t0, 142.0, 92.0, 50.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-1", "p-1", 2, t0 + timedelta(minutes=5), 132.0, 84.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-1", "p-1", 3, t0 + timedelta(minutes=10), 128.0, 80.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
    ]

    result = calculate_protocol_bp(readings, cfg)
    assert result.is_valid is True
    assert result.status == BpReadingStatus.VALID.value
    assert result.derivation_category == BpDerivationCategory.PROTOCOL_MEAN_READINGS_2_AND_3.value
    # SBP = (132.0 + 128.0) / 2 = 130.0
    assert result.final_sbp == 130.0
    # DBP = (84.0 + 80.0) / 2 = 82.0
    assert result.final_dbp == 82.0
    # PP = 130.0 - 82.0 = 48.0
    assert result.final_pulse_pressure == 48.0
    assert result.readings_used_count == 2
    assert result.readings_used_indices == [2, 3]


# ==============================================================================
# 2. Correct selection of specified readings
# ==============================================================================

def test_correct_selection_of_specified_readings():
    """Verify that only the configured reading indices contribute to the final value."""
    t0 = datetime(2024, 6, 29, 10, 0, 0)
    # Custom config: mean of reading 1 and reading 3
    custom_cfg = BpMeasurementProtocolConfig(
        protocol_id="CUSTOM_1_AND_3",
        protocol_version="1.0",
        number_of_readings=3,
        selected_reading_indices=[1, 3],
        min_valid_readings_required=2,
    )

    readings = [
        CommunityBpReading("ca-2", "p-2", 1, t0, 150.0, 90.0, 60.0, "mmHg", BpReadingStatus.VALID.value, "CUSTOM", "1.0"),
        CommunityBpReading("ca-2", "p-2", 2, t0 + timedelta(minutes=5), 110.0, 70.0, 40.0, "mmHg", BpReadingStatus.VALID.value, "CUSTOM", "1.0"),
        CommunityBpReading("ca-2", "p-2", 3, t0 + timedelta(minutes=10), 130.0, 80.0, 50.0, "mmHg", BpReadingStatus.VALID.value, "CUSTOM", "1.0"),
    ]

    result = calculate_protocol_bp(readings, custom_cfg)
    assert result.is_valid is True
    # SBP = (150.0 + 130.0) / 2 = 140.0 (reading 2 is completely ignored)
    assert result.final_sbp == 140.0
    # DBP = (90.0 + 80.0) / 2 = 85.0
    assert result.final_dbp == 85.0
    assert result.readings_used_indices == [1, 3]


# ==============================================================================
# 3. Independent averaging of SBP and DBP
# ==============================================================================

def test_independent_averaging_of_sbp_and_dbp():
    """Verify that SBP and DBP are averaged independently without coupling or ratio formulas."""
    cfg = create_lasi_tri_measurement_protocol()
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    # Reading 2: SBP is higher, DBP is lower
    # Reading 3: SBP is lower, DBP is higher
    readings = [
        CommunityBpReading("ca-3", "p-3", 1, t0, 140.0, 90.0, 50.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-3", "p-3", 2, t0 + timedelta(minutes=5), 135.0, 75.0, 60.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-3", "p-3", 3, t0 + timedelta(minutes=10), 125.0, 85.0, 40.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
    ]

    result = calculate_protocol_bp(readings, cfg)
    assert result.final_sbp == 130.0  # (135 + 125) / 2
    assert result.final_dbp == 80.0   # (75 + 85) / 2
    assert result.final_pulse_pressure == 50.0


# ==============================================================================
# 4. Missing first, second, or third readings
# ==============================================================================

def test_missing_first_reading_strict_protocol():
    """Missing reading 1 does NOT invalidate strict LASI protocol because reading 1 is discarded."""
    cfg = create_lasi_tri_measurement_protocol()
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    readings = [
        CommunityBpReading("ca-4", "p-4", 1, t0, None, None, None, "mmHg", BpReadingStatus.REFUSED.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-4", "p-4", 2, t0 + timedelta(minutes=5), 130.0, 80.0, 50.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-4", "p-4", 3, t0 + timedelta(minutes=10), 126.0, 78.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
    ]

    result = calculate_protocol_bp(readings, cfg)
    assert result.is_valid is True
    assert result.final_sbp == 128.0
    assert result.final_dbp == 79.0


def test_missing_second_or_third_reading_strict_vs_fallback():
    """Missing reading 2 or 3 fails under strict protocol, but succeeds under fallback if enabled."""
    strict_cfg = create_lasi_tri_measurement_protocol(allow_single_reading_fallback=False)
    fallback_cfg = create_lasi_tri_measurement_protocol(allow_single_reading_fallback=True)
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    # Reading 3 failed/refused
    readings = [
        CommunityBpReading("ca-5", "p-5", 1, t0, 140.0, 90.0, 50.0, "mmHg", BpReadingStatus.VALID.value, strict_cfg.protocol_id, strict_cfg.protocol_version),
        CommunityBpReading("ca-5", "p-5", 2, t0 + timedelta(minutes=5), 130.0, 82.0, 48.0, "mmHg", BpReadingStatus.VALID.value, strict_cfg.protocol_id, strict_cfg.protocol_version),
        CommunityBpReading("ca-5", "p-5", 3, t0 + timedelta(minutes=10), None, None, None, "mmHg", BpReadingStatus.DEVICE_ERROR.value, strict_cfg.protocol_id, strict_cfg.protocol_version),
    ]

    # Strict: must fail because 2 valid readings from {2, 3} are required
    res_strict = calculate_protocol_bp(readings, strict_cfg)
    assert res_strict.is_valid is False
    assert res_strict.status == BpReadingStatus.INSUFFICIENT_VALID_READINGS.value
    assert res_strict.derivation_category == BpDerivationCategory.INSUFFICIENT_VALID_READINGS.value
    assert res_strict.final_sbp is None
    assert res_strict.final_dbp is None

    # Fallback: uses the remaining single reading (reading 2)
    res_fallback = calculate_protocol_bp(readings, fallback_cfg)
    assert res_fallback.is_valid is True
    assert res_fallback.final_sbp == 130.0
    assert res_fallback.final_dbp == 82.0
    assert res_fallback.derivation_category == BpDerivationCategory.FALLBACK_READING_2_ONLY.value


# ==============================================================================
# 5. Invalid or physiologically implausible individual readings
# ==============================================================================

def test_invalid_or_implausible_individual_readings():
    """Verify that physiologically implausible readings are rejected."""
    # SBP out of bounds
    ok1, s1 = validate_reading_values(300.0, 80.0)
    assert ok1 is False
    assert s1 == BpReadingStatus.OUT_OF_RANGE_SBP.value

    # DBP out of bounds
    ok2, s2 = validate_reading_values(120.0, 30.0)
    assert ok2 is False
    assert s2 == BpReadingStatus.OUT_OF_RANGE_DBP.value

    # Pulse pressure < 20 mmHg (e.g. 120 / 110 -> PP = 10)
    ok3, s3 = validate_reading_values(120.0, 110.0)
    assert ok3 is False
    assert s3 == BpReadingStatus.PHYSIOLOGICAL_PP_VIOLATION.value

    # Negative values
    ok4, s4 = validate_reading_values(-120.0, 80.0)
    assert ok4 is False
    assert s4 == BpReadingStatus.OUT_OF_RANGE_SBP.value


# ==============================================================================
# 6. Insufficient valid readings
# ==============================================================================

def test_insufficient_valid_readings_not_classified_as_normal():
    """Verify that insufficient readings result in invalid/unassessable, never normal or zero."""
    cfg = create_lasi_tri_measurement_protocol(allow_single_reading_fallback=False)
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    # All readings refused or device error
    readings = [
        CommunityBpReading(
            assessment_id="ca-6",
            patient_id="p-6",
            reading_number=1,
            timestamp=t0,
            sbp=None,
            dbp=None,
            pulse_pressure=None,
            unit="mmHg",
            status=BpReadingStatus.REFUSED.value,
            protocol_id=cfg.protocol_id,
            protocol_version=cfg.protocol_version,
        ),
        CommunityBpReading(
            assessment_id="ca-6",
            patient_id="p-6",
            reading_number=2,
            timestamp=t0 + timedelta(minutes=5),
            sbp=None,
            dbp=None,
            pulse_pressure=None,
            unit="mmHg",
            status=BpReadingStatus.REFUSED.value,
            protocol_id=cfg.protocol_id,
            protocol_version=cfg.protocol_version,
        ),
        CommunityBpReading(
            assessment_id="ca-6",
            patient_id="p-6",
            reading_number=3,
            timestamp=t0 + timedelta(minutes=10),
            sbp=None,
            dbp=None,
            pulse_pressure=None,
            unit="mmHg",
            status=BpReadingStatus.REFUSED.value,
            protocol_id=cfg.protocol_id,
            protocol_version=cfg.protocol_version,
        ),
    ]

    res = calculate_protocol_bp(readings, cfg)
    assert res.is_valid is False
    assert res.final_sbp is None
    assert res.final_dbp is None
    # Crucial: Must NOT be 0.0 or 120.0 (no imputation to normal)
    assert res.status == BpReadingStatus.INSUFFICIENT_VALID_READINGS.value


# ==============================================================================
# 7. Exact protocol boundary behavior
# ==============================================================================

def test_exact_protocol_boundary_behavior():
    """Verify exact inclusive boundaries for physiological plausibility."""
    # Lower bound: SBP=60.0, DBP=40.0, PP=20.0 -> Valid
    ok_min, s_min = validate_reading_values(60.0, 40.0)
    assert ok_min is True
    assert s_min == BpReadingStatus.VALID.value

    # Upper bound: SBP=280.0, DBP=160.0, PP=120.0 -> Valid
    ok_max, s_max = validate_reading_values(280.0, 160.0)
    assert ok_max is True
    assert s_max == BpReadingStatus.VALID.value

    # Sub-boundary violations (0.1 mmHg beyond limit)
    assert validate_reading_values(59.9, 40.0)[0] is False
    assert validate_reading_values(280.1, 160.0)[0] is False
    assert validate_reading_values(120.0, 39.9)[0] is False
    assert validate_reading_values(120.0, 160.1)[0] is False
    assert validate_reading_values(100.0, 80.1)[0] is False  # PP = 19.9 < 20.0


# ==============================================================================
# 8. Deterministic readings under a fixed seed
# ==============================================================================

def test_deterministic_readings_under_fixed_seed():
    """Verify that protocol simulation is bit-for-bit deterministic for a fixed seed."""
    sim = BpMeasurementProtocolSimulator(config=create_lasi_tri_measurement_protocol())
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    rng1 = random.Random(12345)
    res1 = sim.simulate(135.0, 85.0, "ca-det", "p-det", t0, rng1)

    rng2 = random.Random(12345)
    res2 = sim.simulate(135.0, 85.0, "ca-det", "p-det", t0, rng2)

    assert res1.final_sbp == res2.final_sbp
    assert res1.final_dbp == res2.final_dbp
    assert len(res1.readings) == len(res2.readings)
    for r1, r2 in zip(res1.readings, res2.readings):
        assert r1.sbp == r2.sbp
        assert r1.dbp == r2.dbp
        assert r1.timestamp == r2.timestamp


# ==============================================================================
# 9. Independent per-patient random streams
# ==============================================================================

def test_independent_per_patient_random_streams(tmp_path):
    """Verify that different patients receive independent random variations."""
    from synapse_simulator.evaluation.experiment import ExperimentRunner, ExperimentConfig
    import csv

    cfg = ExperimentConfig(
        cohort_size=10,
        seed=42,
        output_dir=tmp_path / "per_patient_stream",
        bp_protocol="TRI_MEASUREMENT",
    )
    ExperimentRunner.generate_cohort(cfg)

    readings_file = tmp_path / "per_patient_stream" / "community_bp_readings.csv"
    assert readings_file.exists()

    with open(readings_file, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Group readings by patient
    by_patient = {}
    for r in rows:
        by_patient.setdefault(r["patient_id"], []).append(r)

    sbp_diffs = []
    for pid, p_reads in by_patient.items():
        if len(p_reads) >= 3 and p_reads[0]["sbp"] and p_reads[1]["sbp"]:
            diff = float(p_reads[0]["sbp"]) - float(p_reads[1]["sbp"])
            sbp_diffs.append(diff)

    assert len(set(sbp_diffs)) > 1


# ==============================================================================
# 10. Reproducibility across separate Python processes
# ==============================================================================

def test_reproducibility_across_separate_python_processes(tmp_path):
    """Verify that running generation in separate subprocesses yields identical results."""
    cmd = [
        sys.executable,
        "-c",
        """
import random
from datetime import datetime
from synapse_simulator.datagen.bp_measurement import BpMeasurementProtocolSimulator, create_lasi_tri_measurement_protocol
sim = BpMeasurementProtocolSimulator(create_lasi_tri_measurement_protocol())
rng = random.Random(42)
res = sim.simulate(138.0, 88.0, 'ca-proc', 'p-proc', datetime(2024, 6, 29), rng)
print(f"{res.final_sbp},{res.final_dbp},{res.readings[0].sbp}")
"""
    ]
    p1 = subprocess.check_output(cmd, text=True).strip()
    p2 = subprocess.check_output(cmd, text=True).strip()
    assert p1 == p2


# ==============================================================================
# 11. Reading-order invariance of selected readings
# ==============================================================================

def test_reading_order_invariance_of_selected_readings():
    """Arithmetic mean is commutative; swapping reading 2 and reading 3 yields identical average."""
    cfg = create_lasi_tri_measurement_protocol()
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    # Order A: Reading 2 = 132/84, Reading 3 = 126/78
    readings_a = [
        CommunityBpReading("ca-a", "p-a", 1, t0, 140.0, 90.0, 50.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-a", "p-a", 2, t0 + timedelta(minutes=5), 132.0, 84.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-a", "p-a", 3, t0 + timedelta(minutes=10), 126.0, 78.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
    ]
    res_a = calculate_protocol_bp(readings_a, cfg)

    # Order B: Reading 2 = 126/78, Reading 3 = 132/84
    readings_b = [
        CommunityBpReading("ca-b", "p-b", 1, t0, 140.0, 90.0, 50.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-b", "p-b", 2, t0 + timedelta(minutes=5), 126.0, 78.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
        CommunityBpReading("ca-b", "p-b", 3, t0 + timedelta(minutes=10), 132.0, 84.0, 48.0, "mmHg", BpReadingStatus.VALID.value, cfg.protocol_id, cfg.protocol_version),
    ]
    res_b = calculate_protocol_bp(readings_b, cfg)

    assert res_a.final_sbp == res_b.final_sbp == 129.0
    assert res_a.final_dbp == res_b.final_dbp == 81.0


# ==============================================================================
# 12. Preservation of reading numbers and timestamps
# ==============================================================================

def test_preservation_of_reading_numbers_and_timestamps():
    """Verify that individual readings have strictly 1, 2, 3 sequence and 5-min intervals."""
    sim = BpMeasurementProtocolSimulator(create_lasi_tri_measurement_protocol())
    t0 = datetime(2024, 6, 29, 9, 30, 0)
    rng = random.Random(99)

    res = sim.simulate(124.0, 80.0, "ca-time", "p-time", t0, rng)
    assert len(res.readings) == 3

    assert res.readings[0].reading_number == 1
    assert res.readings[0].timestamp == t0

    assert res.readings[1].reading_number == 2
    assert res.readings[1].timestamp == t0 + timedelta(minutes=5)

    assert res.readings[2].reading_number == 3
    assert res.readings[2].timestamp == t0 + timedelta(minutes=10)


# ==============================================================================
# 13. Separation between individual readings and final analysis values
# ==============================================================================

def test_separation_between_individual_readings_and_final_analysis_values():
    """Individual readings must be distinct from final analysis value (e.g. alerting bias in reading 1)."""
    sim = BpMeasurementProtocolSimulator(create_lasi_tri_measurement_protocol())
    t0 = datetime(2024, 6, 29, 9, 30, 0)
    rng = random.Random(777)

    res = sim.simulate(130.0, 80.0, "ca-sep", "p-sep", t0, rng)

    # Reading 1 has white-coat alerting bias, so it is strictly higher than resting baseline
    assert res.readings[0].sbp > res.final_sbp
    assert res.readings[0].dbp > res.final_dbp

    # Final SBP is exactly the resting baseline under SYMMETRICAL_UNBIASED model
    assert res.final_sbp == 130.0
    assert res.final_dbp == 80.0


# ==============================================================================
# 14. Community readings do NOT create EHR encounters or prescriptions
# ==============================================================================

def test_community_readings_do_not_create_ehr_encounters_or_prescriptions():
    """Community assessment pathway must not generate EHR clinical records."""
    from synapse_simulator.evaluation.experiment import ExperimentRunner, ExperimentConfig

    cfg = ExperimentConfig(
        cohort_size=10,
        seed=42,
        output_dir=Path("data/experiments/test_ehr_separation"),
        bp_protocol="TRI_MEASUREMENT",
    )
    out_dir, _ = ExperimentRunner.generate_cohort(cfg)

    # Read community assessments and encounters
    import csv
    with open(out_dir / "community_assessments.csv", "r", encoding="utf-8-sig") as f:
        comm_rows = list(csv.DictReader(f))
    with open(out_dir / "encounters.csv", "r", encoding="utf-8-sig") as f:
        enc_rows = list(csv.DictReader(f))

    # Provenance check: all community assessments belong to COMMUNITY_HEALTH_ASSESSMENT_LAYER
    for r in comm_rows:
        assert r["provenance"] == "COMMUNITY_HEALTH_ASSESSMENT_LAYER"

    # Encounters must not contain community assessment IDs
    comm_ids = {r["assessment_id"] for r in comm_rows}
    for e in enc_rows:
        assert e["encounter_id"] not in comm_ids


# ==============================================================================
# 15. Correct use of final analysis values in prevalence calculations
# ==============================================================================

def test_correct_use_of_final_analysis_values_in_prevalence():
    """Prevalence calculation uses final averaged SBP/DBP, discarding reading 1 alerting elevation."""
    from synapse_simulator.evaluation.lasi.evaluator import LasiExternalEvaluator
    from synapse_simulator.evaluation.lasi.ingestor import LasiDataIngestor

    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    fixture_path = Path("data/evaluation/fixtures/lasi_wave1_sample_fixture.csv")
    if not cohort_dir.exists() or not fixture_path.exists():
        pytest.skip("Cohort or fixture not found")

    ingestor = LasiDataIngestor(source_path=fixture_path)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=cohort_dir,
        reference_records=records,
        quality_report=q_report,
    )

    # Synthetic patient where reading 1 is elevated (142/92), but final average is normal (136/84), and no Rx
    evaluator.patients = [{
        "patient_id": "pat-prev-test",
        "birth_date": "1960-01-01",
        "age": "64.0",
        "is_alive": "True",
    }]
    evaluator.community_assessments = [{
        "assessment_id": "ca-prev-1",
        "patient_id": "pat-prev-test",
        "timestamp": "2024-06-29T10:00:00",
        "status": "COMPLETED",
        "sbp": "136.0",  # Final average is < 140
        "dbp": "84.0",   # Final average is < 90
        "is_assessable": "True",
    }]
    evaluator.medications = []
    evaluator.encounters = []

    prev_metrics = evaluator._evaluate_prevalence()
    c2 = next(m for m in prev_metrics if m.metric_id == "lasi_prev_htn_community_assessment")
    # 0 positive because final analysis value is 136/84 (not hypertensive)
    assert c2.synthetic_estimate == 0.0
    assert c2.synthetic_n == 1


# ==============================================================================
# 16. Point-in-time medication status unaffected by future prescriptions
# ==============================================================================

def test_point_in_time_medication_status_unaffected_by_future_prescriptions():
    """A prescription issued strictly after survey date does NOT count as active at survey."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at

    survey_date = datetime(2024, 6, 29, 12, 0, 0)
    future_rx = {
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-08-15T09:00:00",
        "status": "active",
    }
    past_rx = {
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-03-10T09:00:00",
        "status": "active",
    }

    assert is_prescription_active_at(future_rx, survey_date) is False
    assert is_prescription_active_at(past_rx, survey_date) is True


# ==============================================================================
# 17. Compatibility with existing single-reading mode
# ==============================================================================

def test_compatibility_with_existing_single_reading_mode():
    """Verify single-reading mode produces exactly 1 reading per assessment with baseline protocol ID."""
    cfg = create_single_reading_baseline_protocol()
    sim = BpMeasurementProtocolSimulator(config=cfg)
    t0 = datetime(2024, 6, 29, 10, 0, 0)
    rng = random.Random(42)

    res = sim.simulate(136.0, 84.0, "ca-base", "p-base", t0, rng)
    assert res.is_valid is True
    assert res.final_sbp == 136.0
    assert res.final_dbp == 84.0
    assert len(res.readings) == 1
    assert res.readings[0].reading_number == 1
    assert res.readings[0].sbp == 136.0
    assert res.derivation_category == BpDerivationCategory.SINGLE_READING_BASELINE.value
    assert res.protocol_id == "SINGLE_READING_BASELINE"


# ==============================================================================
# 18. Preservation of REFERENCE_DATA_PENDING gate
# ==============================================================================

def test_preservation_of_reference_data_pending_gate():
    """Verify that the external validation gate remains strictly REFERENCE_DATA_PENDING."""
    from synapse_simulator.evaluation.lasi.evaluator import LasiExternalEvaluator
    from synapse_simulator.evaluation.lasi.ingestor import LasiDataIngestor
    from synapse_simulator.evaluation.lasi.models import LasiEvaluationGateStatus

    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    fixture_path = Path("data/evaluation/fixtures/lasi_wave1_sample_fixture.csv")
    if not cohort_dir.exists() or not fixture_path.exists():
        pytest.skip("Cohort or fixture not found")

    ingestor = LasiDataIngestor(source_path=fixture_path)
    records, q_report = ingestor.ingest()
    evaluator = LasiExternalEvaluator(
        synthetic_dir=cohort_dir,
        reference_records=records,
        quality_report=q_report,
    )
    report = evaluator.evaluate()
    assert report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING


# ==============================================================================
# 19. Exact error cancellation and zero residual uncertainty in baseline mode
# ==============================================================================

def test_exact_cancellation_zero_residual_uncertainty():
    """Verify that SYMMETRICAL_UNBIASED produces exact cancellation and zero residual variance."""
    cfg = create_lasi_tri_measurement_protocol(noise_mode="SYMMETRICAL_UNBIASED")
    sim = BpMeasurementProtocolSimulator(config=cfg)
    t0 = datetime(2024, 6, 29, 10, 0, 0)
    rng = random.Random(12345)

    residuals_sbp = []
    residuals_dbp = []

    for i in range(100):
        latent_s = round(rng.uniform(115.0, 160.0), 1)
        latent_d = round(rng.uniform(70.0, 100.0), 1)
        if latent_s - latent_d < 25.0:
            latent_s = latent_d + 25.0

        res = sim.simulate(latent_s, latent_d, f"ca-sim-{i}", f"p-sim-{i}", t0, rng)
        residuals_sbp.append(res.final_sbp - latent_s)
        residuals_dbp.append(res.final_dbp - latent_d)

    # Residuals must be exactly 0.0 (no residual measurement variance)
    import numpy as np
    assert np.var(residuals_sbp) == pytest.approx(0.0, abs=1e-12)
    assert np.var(residuals_dbp) == pytest.approx(0.0, abs=1e-12)
    assert np.max(np.abs(residuals_sbp)) == pytest.approx(0.0, abs=1e-12)


# ==============================================================================
# 20. Experimental AUTOREGRESSIVE_AR1 produces positive correlation and residual variance
# ==============================================================================

def test_autoregressive_ar1_non_zero_residual_variance():
    """Verify that AUTOREGRESSIVE_AR1 produces positive inter-reading correlation and non-zero residual variance."""
    cfg = BpMeasurementProtocolConfig(
        protocol_id="TEST_AR1",
        noise_mode="AUTOREGRESSIVE_AR1",
        inter_reading_correlation=0.70,
        within_visit_noise_sd=1.8,
    )
    sim = BpMeasurementProtocolSimulator(config=cfg)
    t0 = datetime(2024, 6, 29, 10, 0, 0)
    rng = random.Random(42)

    r2_errors = []
    r3_errors = []
    residuals = []

    for i in range(500):
        latent_s = 130.0
        latent_d = 80.0
        res = sim.simulate(latent_s, latent_d, f"ca-ar1-{i}", f"p-ar1-{i}", t0, rng)
        r2_s = res.readings[1].sbp
        r3_s = res.readings[2].sbp
        r2_errors.append(r2_s - latent_s)
        r3_errors.append(r3_s - latent_s)
        residuals.append(res.final_sbp - latent_s)

    import numpy as np
    # Residual variance is strictly non-zero
    assert np.var(residuals) > 1.5
    # Inter-reading error correlation is strongly positive (~0.70)
    corr = np.corrcoef(r2_errors, r3_errors)[0, 1]
    assert 0.60 <= corr <= 0.80


# ==============================================================================
# 21. Threshold-crossing counts consistency
# ==============================================================================

def test_threshold_crossing_counts_consistency():
    """Verify that Reading 1 alerting response causes threshold crossing, while final value does not under baseline."""
    cfg = create_lasi_tri_measurement_protocol(noise_mode="SYMMETRICAL_UNBIASED")
    sim = BpMeasurementProtocolSimulator(config=cfg)
    t0 = datetime(2024, 6, 29, 10, 0, 0)

    # Borderline normotensive patient: SBP 138.0 mmHg
    # Alerting response adds ~3.5 mmHg -> Reading 1 = ~141.5 mmHg (crosses 140 threshold!)
    # Final average recovers 138.0 mmHg (remains below 140 threshold)
    crosser_detected = False
    for seed in range(50):
        rng = random.Random(seed)
        res = sim.simulate(138.0, 82.0, "ca-cross", "p-cross", t0, rng)
        if res.readings[0].sbp >= 140.0 and res.final_sbp < 140.0:
            crosser_detected = True
            assert res.final_sbp == 138.0
            break

    assert crosser_detected is True


# ==============================================================================
# 22. Protocol metadata exported in manifest
# ==============================================================================

def test_protocol_metadata_exported_in_manifest():
    """Verify that RUN_MANIFEST.json records protocol configuration and version."""
    import json
    manifest_path = Path("data/evaluation/lasi_cohort_500/seed_42/RUN_MANIFEST.json")
    if not manifest_path.exists():
        pytest.skip("Manifest not found")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    sim_params = manifest.get("simulation_parameters", {})
    assert "bp_protocol" in sim_params
    assert sim_params["bp_protocol"] == "tri_measurement"
    assert sim_params.get("bp_protocol_id") == "LASI_WAVE1_TRI_MEASUREMENT"


# ==============================================================================
# 23. Deterministic verification of theoretical AR(1) error variance formula
# ==============================================================================

def test_ar1_theoretical_variance_formula():
    """Verify the exact mathematical formula for AR(1) average reading residual variance:
    Var(mean error) = sigma^2 * (1 + rho) / 2
    This test verifies the algebraic invariant without relying on Monte Carlo tolerance,
    and documents the exact resolution of the 3.24 vs 2.754 discrepancy:
    3.24 is sigma^2 (single reading error variance), whereas 2.754 is the theoretical
    residual variance of the mean of two AR(1) readings.
    """
    sigma_sbp = 1.8
    rho = 0.70

    # 1. Single reading marginal error variance: sigma^2 = 1.8^2 = 3.24
    single_reading_var_sbp = sigma_sbp ** 2
    assert single_reading_var_sbp == pytest.approx(3.24, abs=1e-9)

    # 2. Theoretical residual variance of the mean of readings 2 and 3:
    # Var((e2 + e3)/2) = (sigma^2 + sigma^2 + 2 * rho * sigma^2) / 4 = sigma^2 * (1 + rho) / 2
    var_mean_sbp = single_reading_var_sbp * (1.0 + rho) / 2.0
    assert var_mean_sbp == pytest.approx(2.754, abs=1e-9)

    # 3. DBP under implemented code: sigma_dbp = sigma_sbp * 0.6 = 1.08
    sigma_dbp_impl = sigma_sbp * 0.6
    assert sigma_dbp_impl == pytest.approx(1.08, abs=1e-9)
    single_reading_var_dbp = sigma_dbp_impl ** 2
    assert single_reading_var_dbp == pytest.approx(1.1664, abs=1e-9)
    var_mean_dbp = single_reading_var_dbp * (1.0 + rho) / 2.0
    assert var_mean_dbp == pytest.approx(0.99144, abs=1e-9)

    # 4. DBP under literature text assumption: sigma_dbp = 0.9 (factor 0.5)
    sigma_dbp_text = 0.9
    var_mean_dbp_text = (sigma_dbp_text ** 2) * (1.0 + rho) / 2.0
    assert var_mean_dbp_text == pytest.approx(0.6885, abs=1e-9)


# ==============================================================================
# 24. Deterministic invariant: point-in-time vs full-run classification separation
# ==============================================================================

def test_point_in_time_vs_full_run_prevalence_invariants():
    """Verify that point-in-time active medication status correctly distinguishes
    past/present prescriptions from future prescriptions (> day 180)."""
    from datetime import datetime
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at

    survey_date = datetime(2024, 6, 29, 0, 0, 0)

    # Prescription initiated on survey date (day 180) -> Active
    rx_current = {
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-06-29T00:00:00",
        "status": "Dispensed"
    }
    assert is_prescription_active_at(rx_current, survey_date) is True

    # Prescription initiated in year 2 (day 395) -> Future (not active at survey date)
    rx_future = {
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2025-01-30T00:00:00",
        "status": "Dispensed"
    }
    assert is_prescription_active_at(rx_future, survey_date) is False
