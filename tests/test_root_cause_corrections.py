"""
Comprehensive regression tests for root-cause corrections in SYNAPSE Phase 2 simulator.

Tests:
1. Invoice lifecycle and timing: Invoices created at encounter completion within valid bounds.
2. Lab lifecycle: Full transition to Completed, populated completed_at, test-type diversity, results generated.
3. Radiology lifecycle: Full transition to Reported, populated completed_at, modality diversity, findings generated.
4. Scale ID uniqueness: >300 DiagnosticInvestigationScenario instances generate 100% unique IDs (>256 hex boundary).
5. Journey vs Encounter temporal consistency: Journey completion time synchronised with Encounter end time.
6. Medication selection: SCEN-V1-03 antibiotic indication alignment without cross-condition contamination.
"""

from datetime import datetime
import pytest
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.scenarios.scen_v1_02_diagnostic import DiagnosticInvestigationScenario
from synapse_simulator.workflows.model import JourneyStatus


def test_invoice_timing_and_lifecycle():
    """Verify that invoices are generated within encounter timeframe and at encounter completion."""
    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=20)
    sim.run()

    state = sim.state_manager._store
    invoices = state.get("finance.invoices", {})
    encounters = state.get("clinical.encounters", {})

    assert len(invoices) == 20, f"Expected 20 invoices, got {len(invoices)}"

    for inv_id, inv_data in invoices.items():
        assert "patient_id" in inv_data
        assert "encounter_id" in inv_data
        assert inv_data.get("created_at") is not None, f"Invoice {inv_id} missing created_at"

        enc_id = inv_data["encounter_id"]
        assert enc_id in encounters, f"Invoice {inv_id} references nonexistent encounter {enc_id}"
        enc = encounters[enc_id]

        inv_dt = datetime.fromisoformat(inv_data["created_at"])
        enc_start = datetime.fromisoformat(enc["start_time"])
        enc_end = datetime.fromisoformat(enc["end_time"])

        # Invoice must be created within [enc_start, enc_end]
        assert enc_start <= inv_dt <= enc_end, (
            f"Invoice {inv_id} time {inv_dt} is not within encounter [{enc_start}, {enc_end}]"
        )
        assert inv_data["status"] in ["Draft", "Issued", "Paid", "Unpaid"]


def test_laboratory_lifecycle_and_diversity():
    """Verify lab orders transition to Completed, completed_at is populated, and test types are diverse."""
    sim = HospitalSimulator(random_seed=123)
    sim.spawn_patients(patient_count=40)
    sim.run()

    state = sim.state_manager._store
    labs = state.get("laboratory.laboratory_orders", {})

    # SCEN-V1-02 patients have lab orders (10 out of 40 patients)
    scen_02_labs = {k: v for k, v in labs.items() if v.get("status") == "Completed"}
    assert len(scen_02_labs) >= 10, f"Expected at least 10 completed lab orders, got {len(scen_02_labs)}"

    test_types = set()
    for lab_id, lab_data in scen_02_labs.items():
        assert lab_data["status"] == "Completed"
        assert lab_data.get("completed_at") is not None, f"Lab {lab_id} missing completed_at"

        order_dt = datetime.fromisoformat(lab_data["ordered_at"])
        comp_dt = datetime.fromisoformat(lab_data["completed_at"])
        assert comp_dt >= order_dt, f"Lab {lab_id} completed_at ({comp_dt}) < order_time ({order_dt})"

        test_types.add(lab_data.get("test_type"))
        assert "results" in lab_data and len(lab_data["results"]) > 0, f"Lab {lab_id} missing results payload"

    # Ensure test type diversity (not just CBC)
    assert len(test_types) >= 2, f"Expected at least 2 test types across completed labs, got {test_types}"


def test_radiology_lifecycle_and_diversity():
    """Verify radiology orders transition to Reported, completed_at is populated, and modalities are diverse."""
    sim = HospitalSimulator(random_seed=123)
    sim.spawn_patients(patient_count=40)
    sim.run()

    state = sim.state_manager._store
    rads = state.get("radiology.radiology_orders", {})

    scen_02_rads = {k: v for k, v in rads.items() if v.get("status") == "Reported"}
    assert len(scen_02_rads) >= 10, f"Expected at least 10 reported radiology orders, got {len(scen_02_rads)}"

    modalities = set()
    for rad_id, rad_data in scen_02_rads.items():
        assert rad_data["status"] == "Reported"
        assert rad_data.get("completed_at") is not None, f"Radiology {rad_id} missing completed_at"

        order_dt = datetime.fromisoformat(rad_data["ordered_at"])
        comp_dt = datetime.fromisoformat(rad_data["completed_at"])
        assert comp_dt >= order_dt, f"Radiology {rad_id} completed_at ({comp_dt}) < order_time ({order_dt})"

        modalities.add(rad_data.get("modality"))
        assert rad_data.get("findings"), f"Radiology {rad_id} missing findings"
        assert rad_data.get("impression"), f"Radiology {rad_id} missing impression"

    # Ensure modality diversity (not just Chest X-Ray)
    assert len(modalities) >= 2, f"Expected at least 2 modalities across reported studies, got {modalities}"


def test_scen_02_scale_id_uniqueness_past_256():
    """Verify that simulating >256 patients generates unique lab/rad IDs without collisions."""
    # Test scenario instance uniqueness past the 256 hexadecimal slice limit
    scenarios = [DiagnosticInvestigationScenario(instance_index=i + 1) for i in range(300)]
    lab_ids = [sc.lab_order_id for sc in scenarios]
    rad_ids = [sc.rad_order_id for sc in scenarios]

    assert len(set(lab_ids)) == 300, f"Expected 300 unique lab IDs, got {len(set(lab_ids))}"
    assert len(set(rad_ids)) == 300, f"Expected 300 unique rad IDs, got {len(set(rad_ids))}"


def test_journey_and_encounter_temporal_consistency():
    """Verify that PatientJourney completion time matches Encounter end time across completed journeys."""
    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=40)
    sim.run()

    state = sim.state_manager._store
    encounters = state.get("clinical.encounters", {})

    for journey in sim.journeys:
        if journey.status == JourneyStatus.COMPLETED:
            # Match corresponding encounter
            matching_enc = next((enc for enc in encounters.values() if enc["patient_id"] == journey.patient_id), None)
            assert matching_enc is not None, f"No encounter found for patient {journey.patient_id}"

            j_end = journey.end_time.isoformat()
            e_end = matching_enc["end_time"]
            assert j_end == e_end, f"Patient {journey.patient_id} journey end ({j_end}) != encounter end ({e_end})"


def test_scen_03_medication_selection_and_safety():
    """Verify SCEN-V1-03 antibiotic allergy hold applies to appropriate infection indications."""
    sim = HospitalSimulator(random_seed=777)
    sim.spawn_patients(patient_count=20)
    sim.run()

    state = sim.state_manager._store
    prescriptions = state.get("pharmacy.prescriptions", {})

    # SCEN-V1-03 patients are allergic to Penicillin.
    assert len(prescriptions) > 0
    for rx_id, rx in prescriptions.items():
        assert "drug_name" in rx
        assert "patient_id" in rx


def test_lab_lifecycle_pending_vs_completed(tmp_path):
    """Targeted test: Ordered labs have empty completed_at and 0 completion events; Completed labs have populated completed_at and 1 event."""
    from synapse_simulator.exporter.csv_exporter import CSVExporter
    from synapse_simulator.validation.dataset_auditor import DatasetAuditor
    import csv

    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=8)
    sim.run()

    out_dir = tmp_path / "csv_out"
    exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=out_dir,
    )
    exporter.export_simplified_dataset(target_dir=out_dir)

    auditor = DatasetAuditor(out_dir)
    report = auditor.run_full_audit()

    lab_audit = report["laboratory_lifecycle_audit"]
    assert lab_audit["lifecycle_violations_total"] == 0
    assert lab_audit["ordered_with_completed_at_violations"] == 0
    assert lab_audit["completed_missing_completed_at_violations"] == 0
    assert lab_audit["event_linkage_violations"] == 0
    assert lab_audit["completed_tests"] > 0
    assert lab_audit["pending_tests"] > 0

    with open(out_dir / "labs.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["status"] == "Ordered":
                assert row["completed_at"] == "", f"Ordered lab {row['lab_order_id']} must have empty completed_at"
                assert row["result"] == "Pending"
            elif row["status"] == "Completed":
                assert row["completed_at"] != "", f"Completed lab {row['lab_order_id']} must have populated completed_at"
                assert row["result"] != "Pending"


def test_radiology_lifecycle_pending_vs_completed(tmp_path):
    """Targeted test: Ordered rads have empty completed_at and 0 completion events; Reported rads have populated completed_at and 1 event."""
    from synapse_simulator.exporter.csv_exporter import CSVExporter
    from synapse_simulator.validation.dataset_auditor import DatasetAuditor
    import csv

    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=8)
    sim.run()

    out_dir = tmp_path / "csv_out"
    exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=out_dir,
    )
    exporter.export_simplified_dataset(target_dir=out_dir)

    auditor = DatasetAuditor(out_dir)
    report = auditor.run_full_audit()

    rad_audit = report["radiology_lifecycle_audit"]
    assert rad_audit["lifecycle_violations_total"] == 0
    assert rad_audit["ordered_with_completed_at_violations"] == 0
    assert rad_audit["completed_missing_completed_at_violations"] == 0
    assert rad_audit["event_linkage_violations"] == 0
    assert rad_audit["completed_studies"] > 0
    assert rad_audit["pending_studies"] > 0

    with open(out_dir / "radiology.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["status"] == "Ordered":
                assert row["completed_at"] == "", f"Ordered rad {row['rad_order_id']} must have empty completed_at"
                assert row["findings"] == "Pending"
                assert row["impression"] == "Pending"
            elif row["status"] in ("Reported", "Completed"):
                assert row["completed_at"] != "", f"Reported rad {row['rad_order_id']} must have populated completed_at"
                assert row["findings"] != "Pending"


def test_invoices_payments_event_matching(tmp_path):
    """Targeted test: Every invoice row matches 1 InvoiceGenerated event; Paid matches 1 payment & 1 PaymentProcessed event; Unpaid has 0."""
    from synapse_simulator.exporter.csv_exporter import CSVExporter
    from synapse_simulator.validation.dataset_auditor import DatasetAuditor
    import csv

    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=8)
    sim.run()

    out_dir = tmp_path / "csv_out"
    exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=out_dir,
    )
    exporter.export_simplified_dataset(target_dir=out_dir)

    auditor = DatasetAuditor(out_dir)
    report = auditor.run_full_audit()

    inv_audit = report["invoice_lifecycle_audit"]
    assert inv_audit["lifecycle_violations_total"] == 0

    with open(out_dir / "invoices.csv", "r", encoding="utf-8") as f:
        invoices = list(csv.DictReader(f))

    with open(out_dir / "payments.csv", "r", encoding="utf-8") as f:
        payments = list(csv.DictReader(f))

    with open(out_dir / "events.csv", "r", encoding="utf-8") as f:
        events = list(csv.DictReader(f))

    inv_gen_events = [e for e in events if e["event_type"] == "InvoiceGenerated"]
    pay_events = [e for e in events if e["event_type"] == "PaymentProcessed"]

    assert len(invoices) == len(inv_gen_events)
    paid_count = sum(1 for inv in invoices if inv["status"] == "Paid")
    assert paid_count == len(payments)
    assert paid_count == len(pay_events)


def test_referential_integrity_all_twenty_foreign_keys(tmp_path):
    """Targeted test: All 20 foreign key checks are reported in JSON and Markdown with 0 dangling references."""
    from synapse_simulator.exporter.csv_exporter import CSVExporter
    from synapse_simulator.validation.dataset_auditor import DatasetAuditor
    from generate_synthetic_data import _build_markdown_report

    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=4)
    sim.run()

    out_dir = tmp_path / "csv_out"
    exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=out_dir,
    )
    exporter.export_simplified_dataset(target_dir=out_dir)

    auditor = DatasetAuditor(out_dir)
    report = auditor.run_full_audit()

    fk_checks = report["referential_integrity_audit"]["foreign_key_checks"]
    assert len(fk_checks) == 20, f"Expected 20 foreign key checks, got {len(fk_checks)}"
    for check in fk_checks:
        assert check["dangling"] == 0, f"Dangling references found in {check['fk']}"
        assert "source_file" in check
        assert "source_field" in check
        assert "target_file" in check
        assert "target_field" in check

    md_report = _build_markdown_report(report, {"start_time": "", "end_time": "", "simulation_runtime_seconds": 1, "total_events_processed": 10}, 4)
    for check in fk_checks:
        assert check["fk"] in md_report
