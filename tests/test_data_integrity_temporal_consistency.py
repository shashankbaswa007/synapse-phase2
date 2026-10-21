"""
Comprehensive Regression Test Suite for Data Integrity and Temporal Consistency.
Covers Tests 1 through 15 specified in the Phase 2 integrity audit requirements:
- Referential integrity of encounter_id and patient_id across all tables
- Lab patient/encounter association and null-safety
- Treatment provenance rules and evidence_ids preservation
- Encounter lifecycle and non-zero duration semantics
- Event scoping (in-encounter vs post-encounter boundaries)
- Causal event ordering
- Complete journey context propagation
- 10-patient and 100-patient full scale simulation verification
- Deterministic reproducibility across repeated seeded runs
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime

from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.exporter.csv_exporter import CSVExporter
from synapse_simulator.validation.integrity_auditor import IntegrityAuditor


@pytest.fixture(scope="module")
def sim_10_output(tmp_path_factory):
    """Run a 10-patient simulation once and export CSVs for targeted tests."""
    out_dir = tmp_path_factory.mktemp("test_sim_10")
    sim = HospitalSimulator(random_seed=42, enable_pubmed=True)
    sim.spawn_patients(10)
    sim.run(max_events=1500)

    exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=out_dir / "phase2",
    )
    exporter.export_simplified_dataset(target_dir=out_dir / "synthetic")

    auditor = IntegrityAuditor(sim.state_manager, sim.engine.committed_events)
    audit_report = auditor.audit_all()

    return {
        "dir": out_dir / "synthetic",
        "sim": sim,
        "exporter": exporter,
        "auditor": auditor,
        "audit_report": audit_report,
    }


def test_1_no_dangling_encounter_id_references(sim_10_output):
    """TEST 1: No dangling encounter_id references across child tables."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")
    valid_enc_ids = set(enc_df["encounter_id"].dropna())

    for fname in ["conditions.csv", "events.csv", "labs.csv", "medications.csv"]:
        fpath = data_dir / fname
        if fpath.exists():
            df = pd.read_csv(fpath)
            if "encounter_id" in df.columns:
                non_null_encs = df["encounter_id"].dropna()
                dangling = non_null_encs[~non_null_encs.isin(valid_enc_ids)]
                assert len(dangling) == 0, f"Dangling encounter_ids found in {fname}: {dangling.tolist()}"


def test_2_every_lab_has_valid_patient_id(sim_10_output):
    """TEST 2: Every lab record has a non-null, valid patient_id resolving to patients.csv."""
    data_dir = sim_10_output["dir"]
    patients_df = pd.read_csv(data_dir / "patients.csv")
    valid_pat_ids = set(patients_df["patient_id"].dropna())

    labs_df = pd.read_csv(data_dir / "labs.csv")
    assert len(labs_df) > 0, "Expected at least one lab order in 10-patient run"
    assert labs_df["patient_id"].isna().sum() == 0, "Found NULL patient_id in labs.csv"
    assert (labs_df["patient_id"] == "").sum() == 0, "Found empty patient_id in labs.csv"

    invalid_patients = labs_df[~labs_df["patient_id"].isin(valid_pat_ids)]
    assert len(invalid_patients) == 0, f"Labs reference non-existent patients: {invalid_patients.to_dict('records')}"


def test_3_every_lab_has_valid_encounter_id(sim_10_output):
    """TEST 3: Every lab record has a non-null, valid encounter_id resolving to encounters.csv."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")
    valid_enc_ids = set(enc_df["encounter_id"].dropna())

    labs_df = pd.read_csv(data_dir / "labs.csv")
    assert len(labs_df) > 0
    assert labs_df["encounter_id"].isna().sum() == 0, "Found NULL encounter_id in labs.csv"
    assert (labs_df["encounter_id"] == "").sum() == 0, "Found empty encounter_id in labs.csv"

    invalid_encs = labs_df[~labs_df["encounter_id"].isin(valid_enc_ids)]
    assert len(invalid_encs) == 0, f"Labs reference non-existent encounters: {invalid_encs.to_dict('records')}"


def test_4_lab_patient_matches_encounter_patient(sim_10_output):
    """TEST 4: Lab.patient_id == Encounter.patient_id for every lab record."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")
    enc_to_pat = dict(zip(enc_df["encounter_id"], enc_df["patient_id"]))

    labs_df = pd.read_csv(data_dir / "labs.csv")
    for _, row in labs_df.iterrows():
        lab_id = row["lab_id"]
        lab_pat = row["patient_id"]
        enc_id = row["encounter_id"]
        expected_pat = enc_to_pat.get(enc_id)
        assert lab_pat == expected_pat, (
            f"Lab '{lab_id}' patient '{lab_pat}' does not match encounter '{enc_id}' patient '{expected_pat}'"
        )


def test_5_pubmed_backed_treatment_has_evidence_ids(sim_10_output):
    """TEST 5: Treatments with source='pubmed_evidence' or 'internal_yaml+pubmed_evidence' must have valid evidence_ids."""
    data_dir = sim_10_output["dir"]
    meds_df = pd.read_csv(data_dir / "medications.csv")

    pubmed_backed = meds_df[meds_df["source"].isin(["pubmed_evidence", "internal_yaml+pubmed_evidence"])]
    assert len(pubmed_backed) > 0, "Expected at least one pubmed-backed treatment"

    for _, row in pubmed_backed.iterrows():
        ev = row.get("evidence_ids")
        assert pd.notna(ev) and str(ev).strip() != "" and str(ev).strip() != "None", (
            f"Medication '{row['medication_id']}' with source '{row['source']}' is missing PubMed evidence IDs"
        )


def test_6_internal_only_treatment_not_falsely_pubmed_backed(sim_10_output):
    """TEST 6: Treatments with source='internal_yaml' are not falsely marked with pubmed sources."""
    data_dir = sim_10_output["dir"]
    meds_df = pd.read_csv(data_dir / "medications.csv")

    internal_only = meds_df[meds_df["source"] == "internal_yaml"]
    for _, row in internal_only.iterrows():
        assert row["source"] == "internal_yaml"
        # Purely internal YAML treatment without PubMed enrichment does not fabricate PMIDs
        ev = row.get("evidence_ids")
        assert pd.isna(ev) or str(ev).strip() == "" or str(ev).strip() == "nan", (
            f"Pure internal medication '{row['medication_id']}' unexpectedly has evidence IDs: {ev}"
        )


def test_7_completed_encounters_have_valid_duration(sim_10_output):
    """TEST 7: Completed encounters have end_time > start_time (strictly positive duration)."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")

    enc_df["st"] = pd.to_datetime(enc_df["start_time"])
    enc_df["et"] = pd.to_datetime(enc_df["end_time"])
    enc_df["dur"] = (enc_df["et"] - enc_df["st"]).dt.total_seconds()

    closed_encs = enc_df[enc_df["status"] == "Closed"]
    assert len(closed_encs) > 0, "Expected closed encounters in simulation"
    assert (closed_encs["dur"] > 0).all(), (
        f"Found closed encounter with non-positive duration:\n{closed_encs[closed_encs['dur'] <= 0]}"
    )


def test_8_encounter_start_less_than_end_for_non_instantaneous(sim_10_output):
    """TEST 8: start_time <= end_time for all encounters, and start_time < end_time for all active workflows."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")

    enc_df["st"] = pd.to_datetime(enc_df["start_time"])
    enc_df["et"] = pd.to_datetime(enc_df["end_time"])

    # No negative durations
    assert (enc_df["et"] >= enc_df["st"]).all(), "Encounter end_time cannot be before start_time"
    # Min duration across simulated encounters should be strictly positive
    durations = (enc_df["et"] - enc_df["st"]).dt.total_seconds()
    assert durations.min() > 0, f"Expected strictly positive durations, min was {durations.min()}"


def test_9_in_encounter_events_occur_within_boundaries(sim_10_output):
    """TEST 9: In-encounter events occur within [start_time, end_time]."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")
    evt_df = pd.read_csv(data_dir / "events.csv")

    enc_bounds = {}
    for _, row in enc_df.iterrows():
        enc_bounds[row["encounter_id"]] = (
            pd.to_datetime(row["start_time"]),
            pd.to_datetime(row["end_time"]),
        )

    post_encounter_types = {
        "PatientDischarged", "PatientJourneyCompleted", "EncounterCompleted",
        "BillingPaymentProcessed", "PaymentProcessed", "FollowUpScheduled",
    }

    in_encounter_events = evt_df[~evt_df["event_type"].isin(post_encounter_types)]
    for _, row in in_encounter_events.iterrows():
        enc_id = row.get("encounter_id")
        if pd.notna(enc_id) and enc_id in enc_bounds:
            st, et = enc_bounds[enc_id]
            ts = pd.to_datetime(row["timestamp"])
            assert st <= ts, f"Event {row['event_id']} ({row['event_type']}) ts {ts} < start {st}"
            assert ts <= et, f"In-encounter event {row['event_id']} ({row['event_type']}) ts {ts} > end {et}"


def test_10_post_encounter_events_semantics(sim_10_output):
    """TEST 10: Events that are post-encounter occur on or after encounter start_time."""
    data_dir = sim_10_output["dir"]
    enc_df = pd.read_csv(data_dir / "encounters.csv")
    evt_df = pd.read_csv(data_dir / "events.csv")

    enc_starts = dict(zip(enc_df["encounter_id"], pd.to_datetime(enc_df["start_time"])))

    for _, row in evt_df.iterrows():
        enc_id = row.get("encounter_id")
        if pd.notna(enc_id) and enc_id in enc_starts:
            st = enc_starts[enc_id]
            ts = pd.to_datetime(row["timestamp"])
            assert ts >= st, f"Event {row['event_id']} occurred before encounter start {st}"


def test_11_causal_event_ordering_is_valid(sim_10_output):
    """TEST 11: Causally dependent events occur in valid chronological order."""
    report = sim_10_output["audit_report"]
    causal_section = report.get("causal_event_ordering", {})
    assert causal_section.get("success", False), (
        f"Causal event ordering failed: {causal_section.get('errors')}"
    )


def test_12_patient_journey_preserves_canonical_ids(sim_10_output):
    """TEST 12: A complete patient journey preserves patient_id and encounter_id across all tables."""
    data_dir = sim_10_output["dir"]
    patients = pd.read_csv(data_dir / "patients.csv")
    encounters = pd.read_csv(data_dir / "encounters.csv")
    conditions = pd.read_csv(data_dir / "conditions.csv")
    medications = pd.read_csv(data_dir / "medications.csv")

    for pid in patients["patient_id"]:
        # Each patient has exactly one primary encounter in this simulation
        pat_encs = encounters[encounters["patient_id"] == pid]
        assert len(pat_encs) == 1, f"Expected 1 encounter for patient {pid}, found {len(pat_encs)}"
        canonical_enc = pat_encs.iloc[0]["encounter_id"]

        # All conditions for this patient link to this canonical encounter
        pat_conds = conditions[conditions["patient_id"] == pid]
        for _, c in pat_conds.iterrows():
            assert c["encounter_id"] == canonical_enc, (
                f"Condition {c['condition_id']} has enc_id {c['encounter_id']} != {canonical_enc}"
            )

        # All medications for this patient link to this canonical encounter
        pat_meds = medications[medications["patient_id"] == pid]
        for _, m in pat_meds.iterrows():
            assert m["encounter_id"] == canonical_enc, (
                f"Medication {m['medication_id']} has enc_id {m['encounter_id']} != {canonical_enc}"
            )


def test_13_10_patient_simulation_passes_all_integrity_checks(sim_10_output):
    """TEST 13: 10-patient simulation passes all integrity checks cleanly."""
    report = sim_10_output["audit_report"]
    assert report.get("success", False), f"Integrity audit failed with errors: {report.get('errors')}"
    assert report["identity_referential"]["success"]
    assert report["patient_and_encounter_consistency"]["success"]
    assert report["encounter_duration"]["success"]
    assert report["provenance_integrity"]["success"]
    assert report["temporal_encounter_boundaries"]["success"]
    assert report["causal_event_ordering"]["success"]


def test_14_100_patient_simulation_passes_all_integrity_checks(tmp_path):
    """TEST 14: 100-patient simulation passes all integrity checks at scale."""
    sim = HospitalSimulator(random_seed=42, enable_pubmed=True)
    sim.spawn_patients(100)
    sim.run(max_events=15000)

    exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=tmp_path / "phase2",
    )
    exported = exporter.export_simplified_dataset(target_dir=tmp_path / "synthetic")
    assert len(exported) >= 7

    auditor = IntegrityAuditor(sim.state_manager, sim.engine.committed_events)
    report = auditor.audit_all()
    assert report["success"], f"100-patient audit failed: {report.get('errors')}"
    assert report["identity_referential"]["success"]
    assert report["patient_and_encounter_consistency"]["success"]
    assert report["encounter_duration"]["success"]
    assert report["provenance_integrity"]["success"]
    assert report["temporal_encounter_boundaries"]["success"]
    assert report["causal_event_ordering"]["success"]


def test_15_repeated_execution_with_same_seed_is_reproducible(tmp_path):
    """TEST 15: Repeated execution with the same seed produces identical clinical characteristics and metrics."""
    # Run 1
    sim1 = HospitalSimulator(random_seed=999, enable_pubmed=True)
    sim1.spawn_patients(4)
    m1 = sim1.run(max_events=600)

    exp1 = CSVExporter(
        sim1.state_manager, sim1.master_data_snapshot, sim1.patient_contexts,
        sim1.engine.committed_events, sim1.journeys, output_dir=tmp_path / "run1"
    )
    exp1.export_simplified_dataset(tmp_path / "run1_csv")

    # Run 2 with identical seed
    sim2 = HospitalSimulator(random_seed=999, enable_pubmed=True)
    sim2.spawn_patients(4)
    m2 = sim2.run(max_events=600)

    exp2 = CSVExporter(
        sim2.state_manager, sim2.master_data_snapshot, sim2.patient_contexts,
        sim2.engine.committed_events, sim2.journeys, output_dir=tmp_path / "run2"
    )
    exp2.export_simplified_dataset(tmp_path / "run2_csv")

    # 1. Metrics identity
    assert m1["total_patients"] == m2["total_patients"]
    assert m1["total_events_processed"] == m2["total_events_processed"]
    assert m1["decisions_allowed"] == m2["decisions_allowed"]
    assert m1["decisions_blocked"] == m2["decisions_blocked"]

    # 2. Compare exported clinical attributes
    p1 = pd.read_csv(tmp_path / "run1_csv" / "patients.csv")
    p2 = pd.read_csv(tmp_path / "run2_csv" / "patients.csv")
    assert p1["age"].tolist() == p2["age"].tolist()
    assert p1["gender"].tolist() == p2["gender"].tolist()
    assert p1["blood_group"].tolist() == p2["blood_group"].tolist()

    c1 = pd.read_csv(tmp_path / "run1_csv" / "conditions.csv")
    c2 = pd.read_csv(tmp_path / "run2_csv" / "conditions.csv")
    assert c1["condition_code"].tolist() == c2["condition_code"].tolist()
    assert c1["condition_name"].tolist() == c2["condition_name"].tolist()

    med1 = pd.read_csv(tmp_path / "run1_csv" / "medications.csv")
    med2 = pd.read_csv(tmp_path / "run2_csv" / "medications.csv")
    assert med1["drug_name"].tolist() == med2["drug_name"].tolist()
    assert med1["source"].tolist() == med2["source"].tolist()

    enc1 = pd.read_csv(tmp_path / "run1_csv" / "encounters.csv")
    enc2 = pd.read_csv(tmp_path / "run2_csv" / "encounters.csv")
    dur1 = (pd.to_datetime(enc1["end_time"]) - pd.to_datetime(enc1["start_time"])).dt.total_seconds().tolist()
    dur2 = (pd.to_datetime(enc2["end_time"]) - pd.to_datetime(enc2["start_time"])).dt.total_seconds().tolist()
    assert dur1 == dur2

    ev1 = pd.read_csv(tmp_path / "run1_csv" / "events.csv")
    ev2 = pd.read_csv(tmp_path / "run2_csv" / "events.csv")
    assert ev1["event_type"].tolist() == ev2["event_type"].tolist()
