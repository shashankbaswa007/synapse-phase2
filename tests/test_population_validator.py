"""
Unit tests for Three-Tiered Population Validator:
- Mathematical accuracy of Wilson score interval
- Mathematical properties of Jensen-Shannon divergence
- Tier 1 Structural blocking on foreign-key violations
- Tier 2 Plausibility warning generation
- Tier 3 Verification status assignment (VERIFIED vs UNVERIFIED_ESTIMATE)
"""

from pathlib import Path
import csv
import pytest

from synapse_simulator.validation.population_validator import (
    calculate_wilson_interval,
    calculate_jensen_shannon_divergence,
    calculate_chi_square_stat,
    PopulationValidator,
)
from synapse_simulator.population.loader import load_population_profile


PROFILE_PATH = Path(__file__).parent.parent / "config" / "population" / "india_default_v1.yaml"


def test_calculate_wilson_interval():
    # 1. Standard proportion: k=10, n=100 -> ~[0.0552, 0.1744]
    lower, upper = calculate_wilson_interval(10, 100)
    assert 0.05 <= lower <= 0.06
    assert 0.16 <= upper <= 0.18

    # 2. Boundary: k=0
    lower0, upper0 = calculate_wilson_interval(0, 100)
    assert lower0 == 0.0
    assert 0.03 <= upper0 <= 0.04

    # 3. Boundary: k=n
    lowern, uppern = calculate_wilson_interval(100, 100)
    assert 0.96 <= lowern <= 0.97
    assert uppern == 1.0


def test_calculate_jensen_shannon_divergence():
    # 1. Identical distributions have JSD = 0.0
    p = [0.2, 0.5, 0.3]
    assert calculate_jensen_shannon_divergence(p, p) == 0.0

    # 2. Completely disjoint distributions have JSD = 1.0
    p_disjoint = [1.0, 0.0]
    q_disjoint = [0.0, 1.0]
    assert calculate_jensen_shannon_divergence(p_disjoint, q_disjoint) == 1.0

    # 3. Small shift has small divergence (< 0.05)
    p1 = [0.25, 0.25, 0.25, 0.25]
    p2 = [0.26, 0.24, 0.25, 0.25]
    assert calculate_jensen_shannon_divergence(p1, p2) < 0.01


def test_tier1_structural_blocks_on_dangling_fk(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    # Write patients.csv
    with open(dataset_dir / "patients.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"])
        writer.writerow(["pat-01", "Alice", "30", "Female", "O+", "General", "Active"])

    # Write encounters.csv with dangling patient
    with open(dataset_dir / "encounters.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"])
        writer.writerow(["enc-01", "pat-NONEXISTENT", "jny-01", "doc-01", "2026-01-01T10:00:00", "2026-01-01T10:30:00", "Closed", "Checkup"])

    validator = PopulationValidator(dataset_dir)
    res = validator.validate_tier1_structural()

    assert res["status"] == "BLOCK"
    assert res["blocks_publication"] is True
    assert res["error_count"] >= 1


def test_tier2_plausibility_warns_on_post_mortem_encounter(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    # Valid structural records
    with open(dataset_dir / "patients.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"])
        writer.writerow(["pat-01", "Bob", "70", "Male", "O+", "General", "Deceased"])

    # Death record at 2026-06-01
    with open(dataset_dir / "deaths.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"])
        writer.writerow(["dth-01", "pat-01", "2026-06-01T12:00:00", "I21.9", "Myocardial Infarction", "False"])

    # Post-mortem encounter at 2026-07-01
    with open(dataset_dir / "encounters.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["encounter_id", "patient_id", "journey_id", "doctor_id", "start_time", "end_time", "status", "chief_complaint"])
        writer.writerow(["enc-01", "pat-01", "jny-01", "doc-01", "2026-07-01T10:00:00", "2026-07-01T10:30:00", "Closed", "Checkup"])

    validator = PopulationValidator(dataset_dir)
    res = validator.validate_tier2_plausibility()

    assert res["status"] == "WARNING"
    assert res["blocks_publication"] is False
    assert any("Post-mortem" in w for w in res["warnings"])


def test_tier3_statistical_distinguishes_verified_from_unverified(tmp_path):
    profile = load_population_profile(PROFILE_PATH)
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    # 100 Patients
    with open(dataset_dir / "patients.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["patient_id", "name", "age", "gender", "blood_group", "insurance_type", "status"])
        for i in range(100):
            writer.writerow([f"pat-{i}", f"Patient {i}", str(20 + (i % 60)), "Male" if i < 52 else "Female", "O+", "General", "Active"])

    # Conditions: I10 has cited provenance ICMR_INDIAB_2023_HTN, UNKNOWN_CODE has none
    with open(dataset_dir / "conditions.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["condition_id", "patient_id", "encounter_id", "condition_code", "condition_name", "status"])
        for i in range(30):
            writer.writerow([f"cond-htn-{i}", f"pat-{i}", f"enc-{i}", "I10", "Hypertension", "Confirmed"])
        writer.writerow(["cond-unk-01", "pat-99", "enc-99", "UNKNOWN_99", "Heuristic Disease", "Confirmed"])

    validator = PopulationValidator(dataset_dir, population_profile=profile)
    res = validator.validate_tier3_statistical()

    metrics_map = {m["metric_name"]: m for m in res["metrics"]}

    # Sex ratio is backed by SRS_2021_DEMO (not assumption) -> VERIFIED
    sex_metric = metrics_map["Demographic: Male Sex Proportion"]
    assert sex_metric["verification_status"] == "VERIFIED"
    assert sex_metric["confidence_interval_95"] is not None

    # Hypertension is backed by ICMR_INDIAB_2023_HTN -> VERIFIED
    htn_metric = metrics_map["Prevalence: I10"]
    assert htn_metric["verification_status"] == "VERIFIED"
    assert htn_metric["reference_value_percent"] == 30.7

    # UNKNOWN_99 has no cited reference in profile -> UNVERIFIED_ESTIMATE
    unk_metric = metrics_map["Prevalence: UNKNOWN_99"]
    assert unk_metric["verification_status"] == "UNVERIFIED_ESTIMATE"
    assert unk_metric["reference_value_percent"] is None
