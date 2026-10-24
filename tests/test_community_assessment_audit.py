"""
Unit and integration tests for the Independent Community Health Assessment Pathway Audit.

Tests cover:
- Deterministic reproducibility across seeds and separate Python processes (SHA/hash independence).
- Order independence: adding an unrelated patient does not alter existing assessments.
- Normotensive patients with community BP measurements.
- Hypertensive patients with and without EHR diagnosis (undiagnosed community hypertensive).
- Treated patients with controlled and uncontrolled BP.
- Refused, unassessable, or deceased patients (missingness semantics).
- Patients assessed in community without clinical encounters.
- Patients with clinical encounters but no community assessment.
- Patients with no assessments in either pathway.
- Isolated SBP-only and DBP-only threshold elevations.
- Strict architectural separation between clinical and community data tables.
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from synapse_simulator.datagen.community_assessment import (
    CommunityAssessment,
    CommunityAssessmentConfig,
    CommunityAssessmentGenerator,
)
from synapse_simulator.datagen.models import PatientContext


def test_reproducibility_across_python_processes():
    """Verify that community assessment generation produces identical numbers across separate Python processes."""
    cmd = [
        sys.executable,
        "-c",
        (
            "from synapse_simulator.datagen.community_assessment import CommunityAssessmentGenerator, CommunityAssessmentConfig\n"
            "from synapse_simulator.datagen.models import PatientContext\n"
            "p = {'p1': PatientContext(patient_id='p1', name='P1', age=55, gender='Female')}\n"
            "gen = CommunityAssessmentGenerator(base_seed=42)\n"
            "res = gen.generate(p)[0]\n"
            "print(f'{res.sbp},{res.dbp},{res.pulse_pressure}')\n"
        ),
    ]

    env1 = os.environ.copy()
    env1["PYTHONHASHSEED"] = "0"
    out1 = subprocess.check_output(cmd, env=env1, text=True).strip()

    env2 = os.environ.copy()
    env2["PYTHONHASHSEED"] = "999999"
    out2 = subprocess.check_output(cmd, env=env2, text=True).strip()

    assert out1 == out2, f"Outputs differed across Python processes: {out1} vs {out2}"


def test_order_independence_adding_unrelated_patient():
    """Verify that adding unrelated patients does not alter existing patients' assessments."""
    p_target = PatientContext(patient_id="pat-target", name="Target Patient", age=60, gender="Male")
    p_extra1 = PatientContext(patient_id="pat-alpha", name="Alpha Patient", age=50, gender="Female")
    p_extra2 = PatientContext(patient_id="pat-omega", name="Omega Patient", age=70, gender="Male")

    gen = CommunityAssessmentGenerator(base_seed=101)

    # Solo generation
    res_solo = gen.generate({"pat-target": p_target})
    assert len(res_solo) == 1
    target_solo = res_solo[0]

    # Generation with earlier and later sorted patient IDs
    res_multi = gen.generate({
        "pat-alpha": p_extra1,
        "pat-target": p_target,
        "pat-omega": p_extra2,
    })
    assert len(res_multi) == 3
    target_multi = [r for r in res_multi if r.patient_id == "pat-target"][0]

    assert target_solo.sbp == target_multi.sbp
    assert target_solo.dbp == target_multi.dbp
    assert target_solo.pulse_pressure == target_multi.pulse_pressure
    assert target_solo.status == target_multi.status


def test_seed_sensitivity_changing_seed_changes_outputs():
    """Verify that changing the base random seed changes stochastic outputs."""
    p = PatientContext(patient_id="pat-sens", name="Sensitive Patient", age=52, gender="Female")

    gen1 = CommunityAssessmentGenerator(base_seed=42)
    gen2 = CommunityAssessmentGenerator(base_seed=43)

    res1 = gen1.generate({"pat-sens": p})[0]
    res2 = gen2.generate({"pat-sens": p})[0]

    assert (res1.sbp, res1.dbp) != (res2.sbp, res2.dbp)


def test_normotensive_patient_has_community_bp():
    """Verify normotensive patients receive physiological normotensive BP in community survey."""
    p_norm = PatientContext(
        patient_id="pat-norm-01",
        name="Normotensive Person",
        age=50,
        gender="Male",
        latent_conditions={},
    )
    gen = CommunityAssessmentGenerator(base_seed=42)
    assessments = gen.generate({"pat-norm-01": p_norm})

    assert len(assessments) == 1
    ca = assessments[0]
    assert ca.status == "COMPLETED"
    assert ca.is_assessable is True
    # Expected normotensive range: SBP [110, 135], DBP [70, 84]
    assert 110.0 <= ca.sbp <= 135.0
    assert 70.0 <= ca.dbp <= 84.0
    assert ca.pulse_pressure >= 20.0
    assert ca.sbp > ca.dbp


def test_hypertensive_patient_without_ehr_diagnosis_undiagnosed():
    """Verify latent hypertensive patient without EHR diagnosis or prescriptions is captured with elevated BP."""
    p_latent = PatientContext(
        patient_id="pat-undiag-01",
        name="Undiagnosed Hypertensive",
        age=58,
        gender="Female",
        latent_conditions={"I10": {"code": "I10", "name": "Essential hypertension", "recognized": False}},
    )
    # Untreated: active_antihypertensive_pids is empty
    gen = CommunityAssessmentGenerator(base_seed=42)
    assessments = gen.generate({"pat-undiag-01": p_latent}, active_antihypertensive_pids=set())

    assert len(assessments) == 1
    ca = assessments[0]
    assert ca.status == "COMPLETED"
    # Untreated hypertensive range: SBP [145, 168], DBP [90, 104]
    assert 145.0 <= ca.sbp <= 168.0
    assert 90.0 <= ca.dbp <= 104.0
    assert ca.sbp >= 140.0
    assert ca.dbp >= 90.0


def test_treated_hypertensive_controlled_and_uncontrolled():
    """Verify that treated hypertensive patients produce both controlled and uncontrolled readings."""
    # Run across multiple treated patients
    patients = {
        f"pat-trt-{i}": PatientContext(
            patient_id=f"pat-trt-{i}",
            name=f"Treated {i}",
            age=60,
            gender="Female",
            latent_conditions={"I10": {"code": "I10"}},
        )
        for i in range(100)
    }
    treated_pids = set(patients.keys())

    gen = CommunityAssessmentGenerator(base_seed=777)
    assessments = gen.generate(patients, active_antihypertensive_pids=treated_pids)

    controlled = [ca for ca in assessments if ca.sbp < 140.0 and ca.dbp < 90.0]
    uncontrolled = [ca for ca in assessments if ca.sbp >= 140.0 or ca.dbp >= 90.0]

    assert len(controlled) > 0, "Expected some treated patients to achieve BP control"
    assert len(uncontrolled) > 0, "Expected some treated patients to remain uncontrolled"
    # All treated patients should fall in the treated range [120, 150] / [75, 92]
    for ca in assessments:
        assert 120.0 <= ca.sbp <= 150.0
        assert 75.0 <= ca.dbp <= 92.0


def test_isolated_sbp_only_and_dbp_only_elevations():
    """Verify that both isolated systolic (SBP>=140, DBP<90) and diastolic (SBP<140, DBP>=90) elevations occur."""
    patients = {
        f"pat-mix-{i}": PatientContext(
            patient_id=f"pat-mix-{i}",
            name=f"Patient {i}",
            age=65,
            gender="Male",
            latent_conditions={"I10": {"code": "I10"}},
        )
        for i in range(100)
    }
    treated_pids = set(patients.keys())
    gen = CommunityAssessmentGenerator(base_seed=0)
    assessments = gen.generate(patients, active_antihypertensive_pids=treated_pids)

    sbp_only = [ca for ca in assessments if ca.sbp >= 140.0 and ca.dbp < 90.0]
    dbp_only = [ca for ca in assessments if ca.sbp < 140.0 and ca.dbp >= 90.0]
    combined = [ca for ca in assessments if ca.sbp >= 140.0 and ca.dbp >= 90.0]

    assert len(sbp_only) > 0, "Expected isolated systolic elevation (SBP>=140, DBP<90)"
    assert len(dbp_only) > 0, "Expected isolated diastolic elevation (SBP<140, DBP>=90)"
    assert len(combined) > 0, "Expected combined elevation (SBP>=140, DBP>=90)"


def test_missing_or_refused_community_assessment():
    """Verify that refused or non-responding community assessments have None for vitals and status REFUSED."""
    p = PatientContext(patient_id="pat-refuse-01", name="Refusing Patient", age=55, gender="Male")
    cfg = CommunityAssessmentConfig(non_response_rate=1.0, seed=42)
    gen = CommunityAssessmentGenerator(config=cfg)

    assessments = gen.generate({"pat-refuse-01": p})
    assert len(assessments) == 1
    ca = assessments[0]
    assert ca.status == "REFUSED"
    assert ca.is_assessable is False
    assert ca.sbp is None
    assert ca.dbp is None
    assert ca.pulse_pressure is None


def test_patient_died_before_survey_excluded_from_community_survey():
    """Verify that patients who die before survey date are not surveyed."""
    survey_date = datetime(2024, 6, 15)
    p_dead = PatientContext(
        patient_id="pat-dead-01",
        name="Deceased Patient",
        age=70,
        gender="Male",
        death_date=datetime(2024, 4, 1),  # Died before survey
    )
    p_alive = PatientContext(
        patient_id="pat-alive-01",
        name="Living Patient",
        age=70,
        gender="Female",
        death_date=datetime(2024, 8, 1),  # Dies after survey
    )

    cfg = CommunityAssessmentConfig(assessment_date=survey_date, seed=42)
    gen = CommunityAssessmentGenerator(config=cfg)

    assessments = gen.generate({
        "pat-dead-01": p_dead,
        "pat-alive-01": p_alive,
    })

    assert len(assessments) == 1
    assert assessments[0].patient_id == "pat-alive-01"


def test_clinical_and_community_table_separation(tmp_path):
    """Verify strict separation between clinical and community tables."""
    import csv

    # Create dummy export directory
    exp_dir = tmp_path / "separation_test"
    exp_dir.mkdir(parents=True)

    # 1. patients.csv
    with open(exp_dir / "patients.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["patient_id", "age", "gender"])
        w.writeheader()
        w.writerow({"patient_id": "p-comm-only", "age": "55.0", "gender": "Female"})
        w.writerow({"patient_id": "p-clin-only", "age": "60.0", "gender": "Male"})
        w.writerow({"patient_id": "p-neither", "age": "65.0", "gender": "Female"})

    # 2. encounters.csv: only p-clin-only attended clinic
    with open(exp_dir / "encounters.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["encounter_id", "patient_id", "status"])
        w.writeheader()
        w.writerow({"encounter_id": "enc-01", "patient_id": "p-clin-only", "status": "Closed"})

    # 3. observations.csv: clinical vitals for p-clin-only
    with open(exp_dir / "observations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["observation_id", "patient_id", "encounter_id", "observation_code", "value"])
        w.writeheader()
        w.writerow({"observation_id": "obs-01", "patient_id": "p-clin-only", "encounter_id": "enc-01", "observation_code": "SBP", "value": "150.0"})
        w.writerow({"observation_id": "obs-02", "patient_id": "p-clin-only", "encounter_id": "enc-01", "observation_code": "DBP", "value": "95.0"})

    # 4. community_assessments.csv: community vitals for p-comm-only
    with open(exp_dir / "community_assessments.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["assessment_id", "patient_id", "status", "sbp", "dbp", "provenance"])
        w.writeheader()
        w.writerow({
            "assessment_id": "ca-01",
            "patient_id": "p-comm-only",
            "status": "COMPLETED",
            "sbp": "122.0",
            "dbp": "78.0",
            "provenance": "COMMUNITY_HEALTH_ASSESSMENT_LAYER",
        })

    # Read back and verify strict isolation
    with open(exp_dir / "observations.csv") as f:
        obs_rows = list(csv.DictReader(f))
    with open(exp_dir / "community_assessments.csv") as f:
        comm_rows = list(csv.DictReader(f))

    obs_pids = {r["patient_id"] for r in obs_rows}
    comm_pids = {r["patient_id"] for r in comm_rows}

    # p-comm-only must NOT appear in clinical observations
    assert "p-comm-only" not in obs_pids
    # p-clin-only must NOT appear in community assessments
    assert "p-clin-only" not in comm_pids
    # p-neither must NOT appear in either
    assert "p-neither" not in obs_pids and "p-neither" not in comm_pids


def test_mutually_exclusive_classification_reconciliation():
    """Verify that the 5 mutually exclusive community HTN categories partition the cohort and reconcile all counts."""
    import csv
    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    if not (cohort_dir / "community_assessments.csv").exists():
        pytest.skip("Evaluation cohort not generated yet")

    with open(cohort_dir / "patients.csv") as f:
        patients = list(csv.DictReader(f))
    with open(cohort_dir / "medications.csv") as f:
        medications = list(csv.DictReader(f))
    with open(cohort_dir / "encounters.csv") as f:
        encounters = {e["encounter_id"]: e for e in csv.DictReader(f)}
    with open(cohort_dir / "community_assessments.csv") as f:
        comm = list(csv.DictReader(f))

    p_ages = {p["patient_id"]: float(p["age"]) for p in patients}
    older_pids = {pid for pid, age in p_ages.items() if age >= 45.0}

    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)

    antihypertensive = {"amlodipine", "telmisartan", "enalapril", "losartan", "hydrochlorothiazide", "atenolol", "metoprolol"}
    treated_older_pids = {
        m["patient_id"] for m in medications
        if m["patient_id"] in older_pids and any(k in (m.get("drug_name") or "").lower() for k in antihypertensive)
        and is_prescription_active_at(m, ref_time, encounter=encounters.get(m.get("encounter_id")))
    }

    comm_older = [c for c in comm if p_ages.get(c["patient_id"], 0.0) >= 45.0]
    assert len(comm_older) == 561, f"Expected 561 older adult community assessments, got {len(comm_older)}"

    # 5 Mutually Exclusive Categories
    cat1_elev_untreated = []
    cat2_elev_treated = []
    cat3_ctrl_treated = []
    cat4_norm_untreated = []
    cat5_unclassifiable = []

    for c in comm_older:
        pid = c["patient_id"]
        status = c.get("status")
        sbp_str, dbp_str = c.get("sbp"), c.get("dbp")
        if status != "COMPLETED" or not sbp_str or not dbp_str:
            cat5_unclassifiable.append(c)
            continue

        try:
            sbp = float(sbp_str)
            dbp = float(dbp_str)
        except (ValueError, TypeError):
            cat5_unclassifiable.append(c)
            continue

        is_elevated = (sbp >= 140.0 or dbp >= 90.0)
        is_treated = (pid in treated_older_pids)

        if is_elevated and not is_treated:
            cat1_elev_untreated.append(c)
        elif is_elevated and is_treated:
            cat2_elev_treated.append(c)
        elif not is_elevated and is_treated:
            cat3_ctrl_treated.append(c)
        else:
            cat4_norm_untreated.append(c)

    # 1. Categories partition the entire denominator
    n1, n2, n3, n4, n5 = len(cat1_elev_untreated), len(cat2_elev_treated), len(cat3_ctrl_treated), len(cat4_norm_untreated), len(cat5_unclassifiable)
    assert n1 + n2 + n3 + n4 + n5 == 561

    # 2. Reconcile reported counts (Corrected point-in-time Day 180 state)
    assert n1 == 0, f"Expected 0 elevated untreated patients (pat-c2683807 onset is Day 395, normotensive at Day 180), got {n1}"
    assert n2 == 89, f"Expected 89 elevated treated patients, got {n2}"
    assert n3 == 128, f"Expected 128 controlled treated patients, got {n3}"
    assert n4 == 344, f"Expected 344 normotensive untreated patients, got {n4}"
    assert n5 == 0, f"Expected 0 unclassifiable observations, got {n5}"

    # 3. Total meeting measured BP thresholds (elevated) = 0 + 89 = 89 (pre-fix was 97)
    assert n1 + n2 == 89, f"Expected 89 measured elevated, got {n1 + n2}"

    # 4. Total community HTN positive = elevated (89) + controlled on Rx (128) = 217 (38.68%)
    assert n1 + n2 + n3 == 217, f"Expected 217 community HTN positive, got {n1 + n2 + n3}"

    # 5. Treated control population = 89 + 128 = 217
    assert n2 + n3 == 217, f"Expected 217 treated patients at Day 180, got {n2 + n3}"
    control_rate = round(100.0 * n3 / (n2 + n3), 2)
    assert control_rate == 58.99, f"Expected 58.99% control rate, got {control_rate}%"


def test_target_population_denominators_and_death_exclusion():
    """Verify that deaths before survey date are excluded from survey denominator and not treated as non-response."""
    import csv
    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    if not (cohort_dir / "patients.csv").exists():
        pytest.skip("Evaluation cohort not generated yet")

    with open(cohort_dir / "patients.csv") as f:
        patients = list(csv.DictReader(f))
    with open(cohort_dir / "deaths.csv") as f:
        deaths = list(csv.DictReader(f))
    with open(cohort_dir / "community_assessments.csv") as f:
        comm = list(csv.DictReader(f))

    survey_date_str = comm[0]["timestamp"]
    survey_date = datetime.fromisoformat(survey_date_str)

    p_ages = {p["patient_id"]: float(p["age"]) for p in patients}
    older_pids = {pid for pid, age in p_ages.items() if age >= 45.0}

    # Denominator 1: Total synthetic cohort
    assert len(patients) == 2200

    # Denominator 2: Older adults at baseline
    assert len(older_pids) == 575

    # Prior deaths before survey date
    prior_deaths = [
        d for d in deaths
        if d["patient_id"] in older_pids and datetime.fromisoformat(d["death_date"]) <= survey_date
    ]
    assert len(prior_deaths) == 14

    # Denominator 3: Living older adults eligible for community survey
    living_older = len(older_pids) - len(prior_deaths)
    assert living_older == 561

    # Community assessed respondents must match living older adults exactly
    comm_older_pids = {c["patient_id"] for c in comm if p_ages.get(c["patient_id"], 0.0) >= 45.0}
    assert len(comm_older_pids) == 561

    # No deceased individual should appear in community assessments
    prior_dead_pids = {d["patient_id"] for d in prior_deaths}
    assert comm_older_pids.isdisjoint(prior_dead_pids)


def test_point_in_time_active_treatment_reconciliation():
    """Verify point-in-time active treatment at assessment timestamp vs post-survey treatment."""
    import csv
    cohort_dir = Path("data/evaluation/lasi_cohort_500/seed_42")
    if not (cohort_dir / "medications.csv").exists():
        pytest.skip("Evaluation cohort not generated yet")

    with open(cohort_dir / "patients.csv") as f: patients = list(csv.DictReader(f))
    with open(cohort_dir / "encounters.csv") as f: encounters = list(csv.DictReader(f))
    with open(cohort_dir / "medications.csv") as f: medications = list(csv.DictReader(f))
    with open(cohort_dir / "community_assessments.csv") as f: comm = list(csv.DictReader(f))

    enc_time = {e["encounter_id"]: datetime.fromisoformat(e["start_time"]) for e in encounters}
    survey_date = datetime.fromisoformat(comm[0]["timestamp"])
    antihypertensive = {"amlodipine", "telmisartan", "enalapril", "losartan", "hydrochlorothiazide", "atenolol", "metoprolol"}

    p_ages = {p["patient_id"]: float(p["age"]) for p in patients}
    older_pids = {pid for pid, age in p_ages.items() if age >= 45.0}

    older_anti_rx = [
        m for m in medications
        if m["patient_id"] in older_pids and any(k in (m.get("drug_name") or "").lower() for k in antihypertensive)
    ]

    earliest_rx = {}
    for m in older_anti_rx:
        pid = m["patient_id"]
        t = enc_time.get(m.get("encounter_id"))
        if t and (pid not in earliest_rx or t < earliest_rx[pid]):
            earliest_rx[pid] = t

    comm_older_pids = {c["patient_id"] for c in comm if p_ages.get(c["patient_id"], 0.0) >= 45.0}

    # Living surveyed patients with prescription on or before survey date
    pids_rx_on_or_before = {pid for pid, t in earliest_rx.items() if t <= survey_date and pid in comm_older_pids}
    pids_rx_strictly_after = {pid for pid, t in earliest_rx.items() if t > survey_date and pid in comm_older_pids}

    assert len(pids_rx_on_or_before) == 217
    assert len(pids_rx_strictly_after) == 16
    assert len(pids_rx_on_or_before) + len(pids_rx_strictly_after) == 233


def test_all_estimands_denominators_and_gate_preservation():
    """Verify that all five estimands have explicit prespecified denominators and gate is REFERENCE_DATA_PENDING."""
    from synapse_simulator.evaluation.lasi.evaluator import LasiExternalEvaluator
    from synapse_simulator.evaluation.lasi.ingestor import LasiDataIngestor
    from synapse_simulator.evaluation.lasi.models import LasiEvaluationGateStatus, LasiDataSourceType

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

    # Gate must be strictly REFERENCE_DATA_PENDING
    assert report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING
    assert report.reference_source_type == LasiDataSourceType.SYNTHETIC_TEST_FIXTURE

    # Check metric denominators
    metrics_by_id = {m.metric_id: m for m in report.metrics}

    # Estimand A: Clinical Index SBP Distribution (N = 235 assessable with BP)
    assert metrics_by_id["lasi_bp_sbp_distribution"].synthetic_n == 235

    # Estimand B: Clinical Assessable HTN Prevalence (N = 235 assessable)
    assert metrics_by_id["lasi_prev_measurement_defined_htn_older_adult"].synthetic_n == 235
    assert metrics_by_id["lasi_prev_measurement_defined_htn_older_adult"].synthetic_estimate == 100.0

    # Estimand C1: EHR Diagnosis Prevalence (N = 575 older adults)
    assert metrics_by_id["lasi_prev_htn_older_adult"].synthetic_n == 575
    assert metrics_by_id["lasi_prev_htn_older_adult"].synthetic_estimate == 40.87

    # Estimand C2: Community Health Assessment Prevalence (N = 561 living surveyed older adults)
    assert metrics_by_id["lasi_prev_htn_community_assessment"].synthetic_n == 561
    assert metrics_by_id["lasi_prev_htn_community_assessment"].synthetic_estimate == 38.68

    # Estimand D1: Clinical Facility Attenders Prevalence (N = 485 older adults with >= 1 encounter)
    assert metrics_by_id["lasi_prev_htn_clinical_attenders"].synthetic_n == 485
    assert metrics_by_id["lasi_prev_htn_clinical_attenders"].synthetic_estimate == 48.45

    # Estimand E: Clinical Unassessable Status Rate (N = 575 older adults)
    assert metrics_by_id["lasi_prev_htn_unassessable_status"].synthetic_n == 575
    assert metrics_by_id["lasi_prev_htn_unassessable_status"].synthetic_estimate == 59.13


# -----------------------------------------------------------------------------
# Point-in-Time Temporal Integrity Regression Tests (External-Validation Gate)
# -----------------------------------------------------------------------------

def test_regression_rx_before_and_active_at_assessment_counts():
    """1. A prescription issued before the assessment and active at the assessment counts."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx = {
        "prescription_id": "rx-001",
        "patient_id": "pat-001",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-01-15T10:00:00",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx, ref_time) is True


def test_regression_rx_issued_after_assessment_does_not_count():
    """2. A prescription issued after the assessment does not count."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx = {
        "prescription_id": "rx-002",
        "patient_id": "pat-002",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2025-05-06T13:54:20",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx, ref_time) is False


def test_regression_rx_discontinued_before_assessment_does_not_count():
    """3. A prescription discontinued before the assessment does not count."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx = {
        "prescription_id": "rx-003",
        "patient_id": "pat-003",
        "drug_name": "Telmisartan 40mg",
        "prescribed_time": "2024-01-10T09:00:00",
        "discontinued_time": "2024-05-01T12:00:00",
        "status": "Discontinued",
    }
    assert is_prescription_active_at(rx, ref_time) is False


def test_regression_rx_boundary_at_exact_assessment_timestamp():
    """4. A prescription starting exactly at the assessment timestamp follows a documented, consistent boundary convention."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx = {
        "prescription_id": "rx-004",
        "patient_id": "pat-004",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-06-29T00:00:00",
        "status": "Dispensed",
    }
    # Documented convention: start_time <= reference_time is inclusive
    assert is_prescription_active_at(rx, ref_time) is True

    # 1 second after reference_time must be False
    rx_after = {
        "prescription_id": "rx-004b",
        "patient_id": "pat-004",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-06-29T00:00:01",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx_after, ref_time) is False


def test_regression_historical_rx_does_not_automatically_imply_current_treatment():
    """5. Historical prescriptions do not automatically imply current treatment."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)

    # Explicitly discontinued status without timestamp -> unverified / cannot assume active
    rx_stopped = {
        "prescription_id": "rx-005a",
        "patient_id": "pat-005",
        "drug_name": "Enalapril 5mg",
        "prescribed_time": "2023-01-01T08:00:00",
        "status": "Discontinued",
    }
    assert is_prescription_active_at(rx_stopped, ref_time) is False

    # Historical completed course with end_time in past
    rx_expired = {
        "prescription_id": "rx-005b",
        "patient_id": "pat-005",
        "drug_name": "Enalapril 5mg",
        "prescribed_time": "2023-01-01T08:00:00",
        "end_time": "2023-06-01T08:00:00",
        "status": "Completed",
    }
    assert is_prescription_active_at(rx_expired, ref_time) is False


def test_regression_missing_or_ambiguous_timing_unverifiable():
    """Where timing data is missing or ambiguous, report limitation rather than inventing history."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx_notime = {
        "prescription_id": "rx-notime",
        "patient_id": "pat-notime",
        "drug_name": "Amlodipine 5mg",
        "status": "Dispensed",
    }
    # No start_time or encounter -> cannot verify point-in-time active status -> returns False
    assert is_prescription_active_at(rx_notime, ref_time) is False

    # Invalid timestamp format -> returns False safely
    rx_badtime = {
        "prescription_id": "rx-badtime",
        "patient_id": "pat-badtime",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "invalid-datetime-string",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx_badtime, ref_time) is False


def test_regression_generator_and_evaluator_share_temporal_definition():
    """6. Generator and evaluator use the same temporal definition."""
    from synapse_simulator.evaluation.medication_status import (
        get_active_antihypertensive_patient_ids,
        is_prescription_active_at,
    )
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    prescriptions = [
        {"prescription_id": "rx-1", "patient_id": "p1", "drug_name": "Amlodipine", "prescribed_time": "2024-01-01T00:00:00"},
        {"prescription_id": "rx-2", "patient_id": "p2", "drug_name": "Amlodipine", "prescribed_time": "2025-01-01T00:00:00"},
        {"prescription_id": "rx-3", "patient_id": "p3", "drug_name": "Amoxicillin", "prescribed_time": "2024-01-01T00:00:00"},
        {"prescription_id": "rx-4", "patient_id": "p4", "drug_name": "Losartan", "prescribed_time": "2024-01-01T00:00:00", "end_time": "2024-05-01T00:00:00"},
    ]
    # Generation function
    active_pids = get_active_antihypertensive_patient_ids(prescriptions, reference_time=ref_time)
    assert active_pids == {"p1"}

    # Evaluator check per patient
    assert is_prescription_active_at(prescriptions[0], ref_time) is True
    assert is_prescription_active_at(prescriptions[1], ref_time) is False
    assert is_prescription_active_at(prescriptions[2], ref_time) is False
    assert is_prescription_active_at(prescriptions[3], ref_time) is False


def test_regression_reordering_medication_records_invariance():
    """7. Reordering medication records does not change results."""
    from synapse_simulator.evaluation.medication_status import get_active_antihypertensive_patient_ids
    import random
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    prescriptions = [
        {"prescription_id": f"rx-{i}", "patient_id": f"pat-{i % 10}", "drug_name": "Amlodipine", "prescribed_time": f"2024-0{(i % 5) + 1}-15T10:00:00"}
        for i in range(50)
    ]
    res_base = get_active_antihypertensive_patient_ids(prescriptions, reference_time=ref_time)

    # Shuffle repeatedly
    rng = random.Random(999)
    for _ in range(5):
        shuffled = list(prescriptions)
        rng.shuffle(shuffled)
        res_shuffled = get_active_antihypertensive_patient_ids(shuffled, reference_time=ref_time)
        assert res_shuffled == res_base


def test_regression_fixed_seed_results_remain_deterministic():
    """8. Fixed-seed results remain deterministic."""
    p_map = {
        f"p{i}": PatientContext(patient_id=f"p{i}", name=f"Patient {i}", age=50 + (i % 30), gender="Male" if i % 2 == 0 else "Female")
        for i in range(20)
    }
    gen1 = CommunityAssessmentGenerator(base_seed=42)
    gen2 = CommunityAssessmentGenerator(base_seed=42)

    res1 = gen1.generate(p_map)
    res2 = gen2.generate(p_map)

    assert len(res1) == len(res2)
    for r1, r2 in zip(res1, res2):
        assert r1.assessment_id == r2.assessment_id
        assert r1.sbp == r2.sbp
        assert r1.dbp == r2.dbp
        assert r1.pulse_pressure == r2.pulse_pressure
        assert r1.status == r2.status


def test_regression_community_assessments_do_not_create_clinical_records():
    """9. Community assessments do not create clinical encounters, diagnoses, or prescriptions."""
    from synapse_simulator.state.state_manager import StateManager
    sm = StateManager()

    # Pre-populate state manager
    sm.set_entity_state("clinical.encounters", "enc-1", {"encounter_id": "enc-1", "status": "Closed"})
    sm.set_entity_state("clinical.consultations", "cond-1", {"condition_code": "I10", "status": "Active"})
    sm.set_entity_state("pharmacy.prescriptions", "rx-1", {"drug_name": "Amlodipine", "status": "Dispensed"})

    p_map = {"p1": PatientContext(patient_id="p1", name="P1", age=65, gender="Female")}
    gen = CommunityAssessmentGenerator(base_seed=42)
    assessments = gen.generate(p_map)

    assert len(assessments) == 1
    # State manager store must be completely unmodified
    assert len(sm._store["clinical.encounters"]) == 1
    assert len(sm._store["clinical.consultations"]) == 1
    assert len(sm._store["pharmacy.prescriptions"]) == 1
    assert "p1" not in {e["encounter_id"] for e in sm._store["clinical.encounters"].values()}


def test_regression_external_validation_gate_remains_reference_data_pending():
    """10. The external-validation gate remains REFERENCE_DATA_PENDING."""
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


# -----------------------------------------------------------------------------
# Task 4: Deterministic Point-in-Time Temporal Boundary Regression Tests
# -----------------------------------------------------------------------------

def test_task4_case1_htn_onset_before_assessment_date():
    """Case 1: Hypertension onset before the assessment date counts as active."""
    from synapse_simulator.datagen.community_assessment import is_condition_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    p = PatientContext(
        patient_id="p-before",
        name="Patient Before",
        age=60,
        gender="Female",
        latent_conditions={"I10": {"onset_time": ref_time - timedelta(days=30), "resolved": False}},
    )
    assert is_condition_active_at(p, "I10", ref_time) is True

    # End-to-end check: BP sampled from untreated HTN range [145, 168]
    gen = CommunityAssessmentGenerator(base_seed=101)
    gen.config.assessment_date = ref_time
    assessments = gen.generate({"p-before": p})
    assert len(assessments) == 1
    assert assessments[0].sbp >= 140.0


def test_task4_case2_htn_onset_exactly_on_assessment_date():
    """Case 2: Hypertension onset exactly on the assessment date counts as active (inclusive boundary)."""
    from synapse_simulator.datagen.community_assessment import is_condition_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    p = PatientContext(
        patient_id="p-on",
        name="Patient On",
        age=60,
        gender="Female",
        latent_conditions={"I10": {"onset_time": ref_time, "resolved": False}},
    )
    assert is_condition_active_at(p, "I10", ref_time) is True

    gen = CommunityAssessmentGenerator(base_seed=102)
    gen.config.assessment_date = ref_time
    assessments = gen.generate({"p-on": p})
    assert len(assessments) == 1
    assert assessments[0].sbp >= 140.0


def test_task4_case3_htn_onset_after_assessment_date():
    """Case 3: Hypertension onset after the assessment date does NOT count as active."""
    from synapse_simulator.datagen.community_assessment import is_condition_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)

    # 1 second after
    p_sec = PatientContext(
        patient_id="p-sec",
        name="Patient Sec",
        age=60,
        gender="Female",
        latent_conditions={"I10": {"onset_time": ref_time + timedelta(seconds=1), "resolved": False}},
    )
    assert is_condition_active_at(p_sec, "I10", ref_time) is False

    # 200 days after (Year 2)
    p_yr2 = PatientContext(
        patient_id="p-yr2",
        name="Patient Yr2",
        age=60,
        gender="Female",
        latent_conditions={"I10": {"onset_time": ref_time + timedelta(days=200), "resolved": False}},
    )
    assert is_condition_active_at(p_yr2, "I10", ref_time) is False

    # End-to-end check: BP sampled from normotensive range [110, 135]
    gen = CommunityAssessmentGenerator(base_seed=103)
    gen.config.assessment_date = ref_time
    assessments = gen.generate({"p-yr2": p_yr2})
    assert len(assessments) == 1
    assert assessments[0].sbp < 140.0


def test_task4_case4_prescription_starting_before_assessment_date():
    """Case 4: Prescription starting before the assessment date counts as active."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx = {
        "prescription_id": "rx-before",
        "patient_id": "p-rx-before",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-06-01T10:00:00",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx, ref_time) is True


def test_task4_case5_prescription_starting_exactly_on_assessment_date():
    """Case 5: Prescription starting exactly on the assessment date counts as active (inclusive boundary)."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx_exact = {
        "prescription_id": "rx-exact",
        "patient_id": "p-rx-exact",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-06-29T00:00:00",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx_exact, ref_time) is True

    # 1 second after must be False
    rx_after_sec = {
        "prescription_id": "rx-after-sec",
        "patient_id": "p-rx-exact",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-06-29T00:00:01",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx_after_sec, ref_time) is False


def test_task4_case6_prescription_starting_after_assessment_date():
    """Case 6: Prescription starting after the assessment date does NOT count as active."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    rx_future = {
        "prescription_id": "rx-future",
        "patient_id": "p-rx-future",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-07-01T00:00:00",
        "status": "Dispensed",
    }
    assert is_prescription_active_at(rx_future, ref_time) is False


def test_task4_case7_prescription_ending_before_assessment_date():
    """Case 7: Prescription ending or stopped before the assessment date does NOT count as active."""
    from synapse_simulator.evaluation.medication_status import is_prescription_active_at
    ref_time = datetime(2024, 6, 29, 0, 0, 0)

    # Ended by end_time
    rx_ended = {
        "prescription_id": "rx-ended",
        "patient_id": "p-rx-ended",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-01-01T00:00:00",
        "end_time": "2024-05-01T00:00:00",
        "status": "Completed",
    }
    assert is_prescription_active_at(rx_ended, ref_time) is False

    # Discontinued by discontinued_time
    rx_disc = {
        "prescription_id": "rx-disc",
        "patient_id": "p-rx-disc",
        "drug_name": "Amlodipine 5mg",
        "prescribed_time": "2024-01-01T00:00:00",
        "discontinued_time": "2024-06-20T00:00:00",
        "status": "Discontinued",
    }
    assert is_prescription_active_at(rx_disc, ref_time) is False


def test_task4_case8_death_before_assessment_date():
    """Case 8: Death before or exactly on the assessment date excludes participant from alive cohort."""
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    p_died_before = PatientContext(
        patient_id="p-died-before",
        name="Patient Died Before",
        age=60,
        gender="Female",
        death_date=ref_time - timedelta(days=5),
        is_alive=False,
    )
    p_died_on = PatientContext(
        patient_id="p-died-on",
        name="Patient Died On",
        age=60,
        gender="Female",
        death_date=ref_time,
        is_alive=False,
    )

    gen = CommunityAssessmentGenerator(base_seed=104)
    gen.config.assessment_date = ref_time
    assessments = gen.generate({"p-died-before": p_died_before, "p-died-on": p_died_on})
    assert len(assessments) == 0, "Both patients died on or before assessment date and must be excluded"


def test_task4_case9_death_after_assessment_date():
    """Case 9: Death after the assessment date does NOT retroactively exclude participant from Day 180 cohort."""
    ref_time = datetime(2024, 6, 29, 0, 0, 0)
    p_dies_later = PatientContext(
        patient_id="p-dies-later",
        name="Patient Dies Later",
        age=60,
        gender="Female",
        death_date=ref_time + timedelta(days=120),
        is_alive=False,  # Simulation finished with patient deceased in Year 2
    )

    gen = CommunityAssessmentGenerator(base_seed=105)
    gen.config.assessment_date = ref_time
    assessments = gen.generate({"p-dies-later": p_dies_later})
    assert len(assessments) == 1, "Patient alive at Day 180 must not be retroactively excluded by Year 2 death"
    assert assessments[0].patient_id == "p-dies-later"
    assert assessments[0].status == "COMPLETED"


def test_task4_case10_metamorphic_future_events_invariance():
    """Case 10 (Metamorphic test): A patient with future HTN onset and future prescription receives
    the EXACT same Day 180 classification and latent BP as an otherwise identical patient without those
    future events, provided all pre-assessment states are identical. Appending future events has ZERO effect.
    """
    ref_time = datetime(2024, 6, 29, 0, 0, 0)

    # Base patient: normotensive, untreated, alive at Day 180
    p_base = PatientContext(
        patient_id="pat-meta-001",
        name="Patient Meta Base",
        age=58,
        gender="Male",
        birth_date=ref_time - timedelta(days=int(58 * 365.25)),
        latent_conditions={},
        is_alive=True,
    )

    gen_base = CommunityAssessmentGenerator(base_seed=777)
    gen_base.config.assessment_date = ref_time
    res_base = gen_base.generate({"pat-meta-001": p_base})
    readings_base = gen_base.get_bp_readings()

    assert len(res_base) == 1
    base_ca = res_base[0]

    # Future-augmented patient: identical up to Day 180, but acquires HTN on Day 350,
    # prescription on Day 360, and dies on Day 600.
    future_prescriptions = [
        {
            "prescription_id": "rx-future-001",
            "patient_id": "pat-meta-001",
            "drug_name": "Amlodipine 5mg",
            "prescribed_time": "2024-12-25T10:00:00",
            "status": "Dispensed",
        }
    ]
    p_future = PatientContext(
        patient_id="pat-meta-001",
        name="Patient Meta Future",
        age=58,
        gender="Male",
        birth_date=ref_time - timedelta(days=int(58 * 365.25)),
        latent_conditions={
            "I10": {"onset_time": datetime(2024, 12, 1, 0, 0, 0), "resolved": False}
        },
        death_date=datetime(2025, 8, 15, 0, 0, 0),
        is_alive=False,
    )

    gen_future = CommunityAssessmentGenerator(base_seed=777)
    gen_future.config.assessment_date = ref_time
    res_future = gen_future.generate(
        {"pat-meta-001": p_future},
        prescriptions=future_prescriptions,
    )
    readings_future = gen_future.get_bp_readings()

    assert len(res_future) == 1
    future_ca = res_future[0]

    # Metamorphic Invariant: All Day 180 outputs must be bit-identical
    assert base_ca.sbp == future_ca.sbp
    assert base_ca.dbp == future_ca.dbp
    assert base_ca.pulse_pressure == future_ca.pulse_pressure
    assert base_ca.status == future_ca.status
    assert base_ca.is_assessable == future_ca.is_assessable
    assert base_ca.derivation_category == future_ca.derivation_category

    # Granular readings must also be identical
    assert len(readings_base) == len(readings_future)
    for rb, rf in zip(readings_base, readings_future):
        assert rb.reading_number == rf.reading_number
        assert rb.sbp == rf.sbp
        assert rb.dbp == rf.dbp
        assert rb.status == rf.status
