"""
Tests for Longitudinal CSV Export and Additive Tables:
- Verification of 12 simplified CSV schema backward compatibility
- Verification of 4 additive tables (patient_timeline, observations, care_plans, deaths)
- Multi-encounter and multi-condition referential integrity
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from synapse_simulator.exporter.csv_exporter import CSVExporter
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.datagen.master_data import MasterDataSnapshot
from synapse_simulator.modules.engine import ClinicalModuleRunner
from synapse_simulator.modules.loader import load_clinical_module


MODULES_DIR = Path(__file__).parent.parent / "config" / "modules"
COMMITTED_HEADERS_FILE = Path(__file__).parent.parent / "docs" / "research_alignment" / "baseline" / "csv_headers_committed.txt"


def test_headers_backward_compatibility(tmp_path):
    """Verify that all 12 simplified CSVs preserve exact committed header contracts."""
    out_dir = tmp_path / "export_check"
    out_dir.mkdir()

    sm = StateManager()
    md = MasterDataSnapshot()
    exp = CSVExporter(
        state_manager=sm,
        master_data=md,
        patient_contexts={},
        committed_events=[],
        journeys=[],
        output_dir=out_dir / "phase2",
    )
    res = exp.export_simplified_dataset(target_dir=out_dir)

    # Read committed headers reference
    committed_headers = {}
    with open(COMMITTED_HEADERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                fname, hdrs = line.strip().split(":", 1)
                committed_headers[fname.strip()] = hdrs.strip()

    for fname, expected_hdr in committed_headers.items():
        csv_file = out_dir / fname
        assert csv_file.exists(), f"File '{fname}' missing from simplified export"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            actual_hdr = ",".join(next(reader))
            assert actual_hdr == expected_hdr, f"Header mismatch in '{fname}':\nExpected: {expected_hdr}\nActual:   {actual_hdr}"


def test_longitudinal_multi_encounter_and_additive_export(tmp_path):
    """Verify multiple encounters per patient and additive longitudinal tables."""
    out_dir = tmp_path / "longitudinal_out"
    out_dir.mkdir()

    sm = StateManager()
    md = MasterDataSnapshot()

    # Create patient with 2 encounters and 2 conditions
    pid = "pat-long-01"
    pctx = PatientContext(
        patient_id=pid,
        name="Longitudinal Patient",
        age=55,
        gender="Female",
        allergies=[],
        chronic_conditions=["I10"],
    )

    # 2 Encounters in state store
    sm.set_entity_state("clinical.encounters", "enc-01", {
        "encounter_id": "enc-01", "patient_id": pid, "journey_id": "jny-01",
        "start_time": "2026-01-10T10:00:00", "end_time": "2026-01-10T10:30:00", "status": "Closed",
    })
    sm.set_entity_state("clinical.encounters", "enc-02", {
        "encounter_id": "enc-02", "patient_id": pid, "journey_id": "jny-01",
        "start_time": "2026-06-15T14:00:00", "end_time": "2026-06-15T14:30:00", "status": "Closed",
    })

    # 2 Consultations / Conditions
    sm.set_entity_state("clinical.consultations", "con-01", {
        "consultation_id": "con-01", "patient_id": pid, "encounter_id": "enc-01",
        "condition_id": "cond-long-01", "diagnosis_code": "I10", "diagnosis_name": "Essential Hypertension",
    })
    sm.set_entity_state("clinical.consultations", "con-02", {
        "consultation_id": "con-02", "patient_id": pid, "encounter_id": "enc-02",
        "condition_id": "cond-long-02", "diagnosis_code": "E11.9", "diagnosis_name": "Type 2 Diabetes",
    })

    # Set up module runner with observations, care plans, deaths
    htn_module = load_clinical_module(MODULES_DIR / "hypertension.yaml")
    runner = ClinicalModuleRunner([htn_module], base_seed=42)
    runner.initialize_patient(pctx)
    runner.longitudinal_observations.append({
        "observation_id": "obs-01",
        "patient_id": pid,
        "encounter_id": "enc-01",
        "timestamp": datetime(2026, 1, 10, 10, 15),
        "observation_code": "SBP",
        "observation_name": "Systolic Blood Pressure",
        "value": 150.0,
        "unit": "mmHg",
        "is_abnormal": True,
    })
    runner.longitudinal_care_plans.append({
        "care_plan_id": "cp-01",
        "patient_id": pid,
        "encounter_id": "enc-01",
        "plan_code": "CP-HTN",
        "plan_name": "Hypertension Care Protocol",
        "start_date": datetime(2026, 1, 10),
        "end_date": None,
        "status": "Active",
    })
    runner.longitudinal_deaths.append({
        "death_id": "dth-01",
        "patient_id": pid,
        "death_date": datetime(2026, 11, 20),
        "cause_code": "I21.9",
        "cause_name": "Acute myocardial infarction",
        "is_premature": False,
    })

    exp = CSVExporter(
        state_manager=sm,
        master_data=md,
        patient_contexts={pid: pctx},
        committed_events=[],
        journeys=[],
        module_runner=runner,
        output_dir=out_dir / "phase2",
    )
    exported = exp.export_simplified_dataset(target_dir=out_dir)

    # 1. Check all 4 additive tables exist
    assert "patient_timeline.csv" in exported
    assert "observations.csv" in exported
    assert "care_plans.csv" in exported
    assert "deaths.csv" in exported

    # 2. Check encounters.csv has 2 rows for the patient
    with open(out_dir / "encounters.csv", "r", encoding="utf-8") as f:
        enc_rows = list(csv.DictReader(f))
        assert len(enc_rows) == 2
        assert {r["encounter_id"] for r in enc_rows} == {"enc-01", "enc-02"}

    # 3. Check conditions.csv has 2 distinct condition IDs
    with open(out_dir / "conditions.csv", "r", encoding="utf-8") as f:
        cond_rows = list(csv.DictReader(f))
        assert len(cond_rows) == 2
        cond_ids = {r["condition_id"] for r in cond_rows}
        assert len(cond_ids) == 2

    # 4. Check observations.csv referential integrity
    with open(out_dir / "observations.csv", "r", encoding="utf-8") as f:
        obs_rows = list(csv.DictReader(f))
        assert len(obs_rows) == 1
        assert obs_rows[0]["patient_id"] == pid
        assert obs_rows[0]["encounter_id"] == "enc-01"
        assert obs_rows[0]["observation_code"] == "SBP"
        assert float(obs_rows[0]["value"]) == 150.0

    # 5. Check care_plans.csv
    with open(out_dir / "care_plans.csv", "r", encoding="utf-8") as f:
        cp_rows = list(csv.DictReader(f))
        assert len(cp_rows) == 1
        assert cp_rows[0]["plan_code"] == "CP-HTN"

    # 6. Check deaths.csv
    with open(out_dir / "deaths.csv", "r", encoding="utf-8") as f:
        dth_rows = list(csv.DictReader(f))
        assert len(dth_rows) == 1
        assert dth_rows[0]["cause_code"] == "I21.9"
