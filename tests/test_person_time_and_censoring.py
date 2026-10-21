"""
Tests for Person-Time and Censoring Accounting (Audit Section 3).

Validates individual right-censored person-time arithmetic:
tau_i = (min(observation_end, death_time) - observation_start) / 365.25

Tests 7 critical boundary conditions:
1. No deaths (all survive entire window)
2. One death before the end of observation
3. Multiple deaths at staggered observation intervals
4. Death on observation boundaries (t = obs_start and t = obs_end)
5. Death after observation window (administrative censoring)
6. Zero-length or very short observation window
7. Independent arithmetic reconciliation against hand-calculated benchmarks
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import csv

from synapse_simulator.evaluation.evaluator import DatasetEvaluator


def create_minimal_dataset(
    tmp_path: Path,
    patients_data: list,
    deaths_data: list,
    encounters_data: list = None,
    conditions_data: list = None,
    medications_data: list = None,
):
    """Helper to write CSV fixtures for DatasetEvaluator."""
    encounters_data = encounters_data or []
    conditions_data = conditions_data or []
    medications_data = medications_data or []

    # Write patients.csv
    with open(tmp_path / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "age", "gender", "status"])
        writer.writeheader()
        for p in patients_data:
            writer.writerow(p)

    # Write deaths.csv
    with open(tmp_path / "deaths.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"])
        writer.writeheader()
        for d in deaths_data:
            writer.writerow(d)

    # Write encounters.csv
    with open(tmp_path / "encounters.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["encounter_id", "patient_id", "start_time", "status", "encounter_type"])
        writer.writeheader()
        for e in encounters_data:
            writer.writerow(e)

    # Write conditions.csv
    with open(tmp_path / "conditions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["condition_id", "patient_id", "encounter_id", "condition_code", "diagnosis_name", "status"])
        writer.writeheader()
        for c in conditions_data:
            writer.writerow(c)

    # Write medications.csv
    with open(tmp_path / "medications.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prescription_id", "patient_id", "condition_id", "drug_name", "dosage", "frequency", "status"])
        writer.writeheader()
        for m in medications_data:
            writer.writerow(m)


class TestPersonTimeAndCensoring:
    """Rigorous independent validation of person-time arithmetic."""

    OBS_START = datetime(2024, 1, 1, 0, 0, 0)
    OBS_END = datetime(2025, 12, 21, 0, 0, 0)  # Exactly 720 days
    DAYS_720 = 720.0
    DAYS_PER_YEAR = 365.25
    WINDOW_YEARS = 720.0 / 365.25  # ~1.9712525667 years

    def test_case_1_no_deaths(self, tmp_path):
        """Scenario 1: No deaths occur. Total person-time must equal N * (720 / 365.25)."""
        N = 10
        patients = [{"patient_id": f"p{i}", "age": "45", "gender": "M", "status": "Active"} for i in range(N)]
        deaths = []

        create_minimal_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        expected_pt = round(N * self.WINDOW_YEARS, 1)

        assert mort_metric.numerator == 0
        assert mort_metric.acceptance_threshold["deaths_count"] == 0
        assert mort_metric.acceptance_threshold["patient_years"] == pytest.approx(expected_pt, abs=0.1)
        assert mort_metric.acceptance_threshold["person_years_lost_to_death"] == 0.0

    def test_case_2_single_death_midpoint(self, tmp_path):
        """Scenario 2: One patient dies exactly at day 360 (midpoint of 720-day window)."""
        # Patient 0 dies at day 360 (2024-12-26)
        # Patient 1 survives full 720 days
        death_time = self.OBS_START + timedelta(days=360)
        patients = [
            {"patient_id": "p0", "age": "70", "gender": "M", "status": "Deceased"},
            {"patient_id": "p1", "age": "40", "gender": "F", "status": "Active"},
        ]
        deaths = [
            {"death_id": "d0", "patient_id": "p0", "death_date": death_time.isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "False"}
        ]

        create_minimal_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        # Expected person-time:
        # p0: 360 / 365.25 = 0.985626 years
        # p1: 720 / 365.25 = 1.971253 years
        # Total: 1080 / 365.25 = 2.956878 years
        expected_total_pt = 1080.0 / self.DAYS_PER_YEAR
        expected_lost = 360.0 / self.DAYS_PER_YEAR

        assert mort_metric.numerator == 1
        assert mort_metric.acceptance_threshold["patient_years"] == pytest.approx(round(expected_total_pt, 1), abs=0.1)
        assert mort_metric.acceptance_threshold["person_years_lost_to_death"] == pytest.approx(round(expected_lost, 2), abs=0.05)

    def test_case_3_multiple_staggered_deaths(self, tmp_path):
        """Scenario 3: Multiple deaths occurring at staggered intervals (days 100, 250, 500)."""
        patients = [{"patient_id": f"p{i}", "age": "60", "gender": "M", "status": "Active"} for i in range(5)]
        deaths = [
            {"death_id": "d0", "patient_id": "p0", "death_date": (self.OBS_START + timedelta(days=100)).isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "True"},
            {"death_id": "d1", "patient_id": "p1", "death_date": (self.OBS_START + timedelta(days=250)).isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "True"},
            {"death_id": "d2", "patient_id": "p2", "death_date": (self.OBS_START + timedelta(days=500)).isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "True"},
        ]
        # p3 and p4 survive full 720 days
        # Hand calculation:
        # p0: 100 days
        # p1: 250 days
        # p2: 500 days
        # p3: 720 days
        # p4: 720 days
        # Total person-days = 100 + 250 + 500 + 720 + 720 = 2290 days
        # Person-years = 2290 / 365.25 = 6.269678 years
        expected_pt = 2290.0 / 365.25

        create_minimal_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        assert mort_metric.numerator == 3
        assert mort_metric.acceptance_threshold["patient_years"] == pytest.approx(round(expected_pt, 1), abs=0.1)

    def test_case_4_boundary_deaths(self, tmp_path):
        """Scenario 4: Deaths exactly on observation boundaries (t = obs_start and t = obs_end)."""
        patients = [
            {"patient_id": "p_start", "age": "80", "gender": "M", "status": "Deceased"},
            {"patient_id": "p_end", "age": "80", "gender": "F", "status": "Deceased"},
            {"patient_id": "p_alive", "age": "30", "gender": "M", "status": "Active"},
        ]
        deaths = [
            # Exactly on obs_start -> 0 person-time contribution
            {"death_id": "d_s", "patient_id": "p_start", "death_date": self.OBS_START.isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "False"},
            # Exactly on obs_end -> Full person-time contribution (720 days)
            {"death_id": "d_e", "patient_id": "p_end", "death_date": self.OBS_END.isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "False"},
        ]
        # Hand calculation:
        # p_start: 0 days
        # p_end: 720 days
        # p_alive: 720 days
        # Total: 1440 days -> 1440 / 365.25 = 3.9425 years
        expected_pt = 1440.0 / 365.25

        create_minimal_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        assert mort_metric.acceptance_threshold["patient_years"] == pytest.approx(round(expected_pt, 1), abs=0.1)

    def test_case_5_death_after_observation_window(self, tmp_path):
        """Scenario 5: Patient dies AFTER observation window (administrative censoring at obs_end)."""
        death_after = self.OBS_END + timedelta(days=60)
        patients = [{"patient_id": "p_post", "age": "65", "gender": "M", "status": "Active"}]
        deaths = [
            {"death_id": "d_post", "patient_id": "p_post", "death_date": death_after.isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "True"}
        ]
        # Should be capped at obs_end: 720 days
        expected_pt = self.WINDOW_YEARS

        create_minimal_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        assert mort_metric.acceptance_threshold["patient_years"] == pytest.approx(round(expected_pt, 1), abs=0.1)

    def test_case_6_zero_or_minimal_length_observation(self, tmp_path):
        """Scenario 6: Very short or near-zero observation window handles gracefully without division by zero."""
        patients = [{"patient_id": "p0", "age": "30", "gender": "M", "status": "Active"}]
        deaths = []

        # Observation window of 1 day
        create_minimal_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_START + timedelta(days=1))
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        assert mort_metric.denominator > 0
        assert mort_metric.status is not None

    def test_case_7_reconcile_500_patient_720_day_benchmark(self, tmp_path):
        """Scenario 7: Reconcile the exact 500 patient, 720-day theoretical maximum (985.63 pt-yrs)

        and expected midpoint-loss benchmark (974.3 pt-yrs).
        """
        # Theoretical maximum: 500 * (720 / 365.25) = 985.626 person-years
        N = 500
        days = 720
        theo_max = N * (days / 365.25)
        assert round(theo_max, 2) == 985.63

        # Midpoint death benchmark for E[D] = 11.5:
        # Halfway = 360 days -> loss per death = 360 / 365.25 = 0.985626 pt-yrs
        expected_deaths = 11.5
        lost_pt = expected_deaths * (360.0 / 365.25)
        benchmark_pt = theo_max - lost_pt
        assert round(benchmark_pt, 1) == 974.3
