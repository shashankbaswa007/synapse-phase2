"""
Tests for Evaluator Mutation Resilience and Diagnostic Sensitivity (Audit Section 10).

Validates that the DatasetEvaluator detects deliberate anomalies, data corruptions,
and clinical invalidities in synthetic CSV outputs:
1. Encounters after death -> Triggers invariant violation (Zero Post-Mortem Events)
2. Inverted temporal timeline (Encounter before birth) -> Triggers invariant violation
3. Artificially elevated mortality (50% mortality in young cohort) -> Triggers WARNING/FAIL
4. Duplicate complications -> Correctly handles de-duplication in prevalence while flagging elevated risk
5. Incorrectly labeled treatment drugs (off-label / invalid regimen) -> Flags treatment guideline deviation
6. Missing foreign key encounter links -> Triggers Causal Invariant violation
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import csv

from synapse_simulator.evaluation.evaluator import (
    DatasetEvaluator,
    MetricStatus,
)


def write_test_dataset(
    tmp_path: Path,
    patients: list,
    deaths: list = None,
    encounters: list = None,
    conditions: list = None,
    medications: list = None,
):
    """Helper to write CSV fixtures for DatasetEvaluator."""
    deaths = deaths or []
    encounters = encounters or []
    conditions = conditions or []
    medications = medications or []

    with open(tmp_path / "patients.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", "age", "gender", "status", "birth_date"])
        writer.writeheader()
        for p in patients:
            writer.writerow(p)

    with open(tmp_path / "deaths.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["death_id", "patient_id", "death_date", "cause_code", "cause_name", "is_premature"])
        writer.writeheader()
        for d in deaths:
            writer.writerow(d)

    with open(tmp_path / "encounters.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["encounter_id", "patient_id", "start_time", "status", "encounter_type"])
        writer.writeheader()
        for e in encounters:
            writer.writerow(e)

    with open(tmp_path / "conditions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["condition_id", "patient_id", "encounter_id", "condition_code", "diagnosis_name", "status"])
        writer.writeheader()
        for c in conditions:
            writer.writerow(c)

    with open(tmp_path / "medications.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prescription_id", "patient_id", "condition_id", "drug_name", "dosage", "frequency", "status"])
        writer.writeheader()
        for m in medications:
            writer.writerow(m)


class TestEvaluatorMutations:
    """Deliberately altered and corrupted datasets to verify evaluator gates."""

    OBS_START = datetime(2024, 1, 1, 0, 0, 0)
    OBS_END = datetime(2025, 12, 31, 0, 0, 0)

    def test_mutation_1_encounter_after_death(self, tmp_path):
        """Mutation 1: Clinical encounter occurs 30 days after patient's recorded death."""
        death_dt = datetime(2024, 6, 1)
        post_mortem_enc_dt = datetime(2024, 7, 1)

        patients = [{"patient_id": "p_mut1", "age": "70", "gender": "M", "status": "Deceased", "birth_date": "1954-01-01"}]
        deaths = [{"death_id": "d1", "patient_id": "p_mut1", "death_date": death_dt.isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "False"}]
        encounters = [{"encounter_id": "e_zombie", "patient_id": "p_mut1", "start_time": post_mortem_enc_dt.isoformat(), "status": "Finished", "encounter_type": "Outpatient"}]

        write_test_dataset(tmp_path, patients, deaths, encounters)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        all_passed, invariants = evaluator.evaluate_invariants()

        assert all_passed is False
        inv_map = {inv.metric_id: inv for inv in invariants}
        post_mortem_inv = inv_map["inv_no_event_post_mortem"]
        assert post_mortem_inv.status == MetricStatus.FAIL
        assert post_mortem_inv.numerator == 1

    def test_mutation_2_encounter_before_birth(self, tmp_path):
        """Mutation 2: Clinical encounter occurs before patient's recorded birth date."""
        birth_dt = datetime(2024, 5, 1)
        pre_birth_enc_dt = datetime(2024, 3, 1)

        patients = [{"patient_id": "p_mut2", "age": "0", "gender": "F", "status": "Active", "birth_date": birth_dt.isoformat()}]
        encounters = [{"encounter_id": "e_pre", "patient_id": "p_mut2", "start_time": pre_birth_enc_dt.isoformat(), "status": "Finished", "encounter_type": "Outpatient"}]

        write_test_dataset(tmp_path, patients, encounters=encounters)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        all_passed, invariants = evaluator.evaluate_invariants()

        assert all_passed is False
        inv_map = {inv.metric_id: inv for inv in invariants}
        pre_birth_inv = inv_map["inv_no_event_pre_birth"]
        assert pre_birth_inv.status == MetricStatus.FAIL
        assert pre_birth_inv.numerator == 1

    def test_mutation_3_artificially_elevated_mortality(self, tmp_path):
        """Mutation 3: Extreme mortality rate (e.g. 50 deaths in 100 young patients, 50% crude rate).

        Must flag as WARNING or FAIL against SRS reference (0.006).
        """
        N = 100
        patients = [{"patient_id": f"p{i}", "age": "30", "gender": "M", "status": "Active", "birth_date": "1994-01-01"} for i in range(N)]
        deaths = [
            {"death_id": f"d{i}", "patient_id": f"p{i}", "death_date": (self.OBS_START + timedelta(days=100 + i)).isoformat(), "cause_code": "R99", "cause_name": "Natural", "is_premature": "True"}
            for i in range(50)
        ]

        write_test_dataset(tmp_path, patients, deaths)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        mort_metric = metrics["long_crude_mortality_rate"]
        assert mort_metric.synthetic_estimate > 0.20
        assert mort_metric.status in (MetricStatus.WARNING, MetricStatus.FAIL)

    def test_mutation_4_missing_encounter_for_diagnosis(self, tmp_path):
        """Mutation 4: Condition diagnosed with invalid or unlinked encounter ID."""
        patients = [{"patient_id": "p0", "age": "45", "gender": "M", "status": "Active", "birth_date": "1979-01-01"}]
        encounters = [{"encounter_id": "e_valid", "patient_id": "p0", "start_time": self.OBS_START.isoformat(), "status": "Finished", "encounter_type": "Outpatient"}]
        conditions = [
            {"condition_id": "c0", "patient_id": "p0", "encounter_id": "e_ghost", "condition_code": "I10", "diagnosis_name": "Essential Hypertension", "status": "Active"}
        ]

        write_test_dataset(tmp_path, patients, encounters=encounters, conditions=conditions)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        all_passed, invariants = evaluator.evaluate_invariants()

        assert all_passed is False
        inv_map = {inv.metric_id: inv for inv in invariants}
        causal_inv = inv_map["inv_diagnosis_encounter_linkage"]
        assert causal_inv.status == MetricStatus.FAIL
        assert causal_inv.numerator == 1

    def test_mutation_5_incorrect_off_label_treatment(self, tmp_path):
        """Mutation 5: Hypertension treated with non-guideline off-label drug (e.g. Paracetamol).

        First-line guideline alignment must drop to 0%.
        """
        patients = [{"patient_id": "p0", "age": "50", "gender": "M", "status": "Active", "birth_date": "1974-01-01"}]
        encounters = [{"encounter_id": "e0", "patient_id": "p0", "start_time": self.OBS_START.isoformat(), "status": "Finished", "encounter_type": "Outpatient"}]
        conditions = [{"condition_id": "c_htn", "patient_id": "p0", "encounter_id": "e0", "condition_code": "I10", "diagnosis_name": "Hypertension", "status": "Active"}]
        medications = [{"prescription_id": "m0", "patient_id": "p0", "condition_id": "c_htn", "drug_name": "Paracetamol", "dosage": "500mg", "frequency": "TID", "status": "Dispensed"}]

        write_test_dataset(tmp_path, patients, encounters=encounters, conditions=conditions, medications=medications)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        treatment_metrics = {m.metric_id: m for m in evaluator.evaluate_treatment_patterns()}

        firstline_htn = treatment_metrics["rx_firstline_hypertension"]
        assert firstline_htn.synthetic_estimate == 0.0
        assert firstline_htn.status in (MetricStatus.WARNING, MetricStatus.FAIL)

    def test_mutation_6_duplicate_condition_diagnoses(self, tmp_path):
        """Mutation 6: Patient diagnosed with CKD (I12.9) twice in multiple encounters.

        Evaluator must de-duplicate patient counts so patient is counted once.
        """
        patients = [{"patient_id": "p0", "age": "60", "gender": "M", "status": "Active", "birth_date": "1964-01-01"}]
        encounters = [
            {"encounter_id": "e0", "patient_id": "p0", "start_time": self.OBS_START.isoformat(), "status": "Finished", "encounter_type": "Outpatient"},
            {"encounter_id": "e1", "patient_id": "p0", "start_time": (self.OBS_START + timedelta(days=90)).isoformat(), "status": "Finished", "encounter_type": "Outpatient"},
        ]
        conditions = [
            {"condition_id": "c0", "patient_id": "p0", "encounter_id": "e0", "condition_code": "I10", "diagnosis_name": "HTN", "status": "Active"},
            {"condition_id": "c1", "patient_id": "p0", "encounter_id": "e0", "condition_code": "I12.9", "diagnosis_name": "CKD", "status": "Active"},
            {"condition_id": "c2", "patient_id": "p0", "encounter_id": "e1", "condition_code": "I12.9", "diagnosis_name": "CKD", "status": "Active"},
        ]

        write_test_dataset(tmp_path, patients, encounters=encounters, conditions=conditions)
        evaluator = DatasetEvaluator(tmp_path, observation_start=self.OBS_START, observation_end=self.OBS_END)
        metrics = {m.metric_id: m for m in evaluator.evaluate_longitudinal()}

        comp_metric = metrics["long_chronic_complication_rate"]
        assert comp_metric.numerator == 1
        assert comp_metric.denominator == 1
        assert comp_metric.synthetic_estimate == 1.0
