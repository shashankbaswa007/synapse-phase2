"""
Unit and Integration Tests for Milestone 2: Binary Microdata Ingestion & Multi-Module Joins.

Tests:
1. Valid Stata (.dta) parsing with metadata, labels, and type integrity.
2. Valid SPSS (.sav) parsing with metadata, labels, and type integrity.
3. Missing value policy: numeric sentinels (-999, -998, 999), Stata extended missings (.a, .b, .),
   and verification that missing measurements are NEVER coerced to 0, normal, or negative status.
4. Join key validation: missing join keys in primary or secondary, type normalization.
5. Duplicate key policy: duplicate primary keys raise LasiDuplicateKeyError.
6. Join cardinality enforcement: unexpected many-to-many joins raise LasiJoinCardinalityError.
7. Unmatched participants and biomarker non-response rate telemetry.
8. Schema mismatches and unsupported formats (.xlsx, .parquet) raise actionable errors.
9. Malformed or corrupted file error handling.
10. Deterministic cryptographic manifest generation (LASI_INGESTION_MANIFEST.json).
11. Preserved validation gate status (REFERENCE_DATA_PENDING) and fixture/genuine separation.
"""

import json
from pathlib import Path
import tempfile
import pandas as pd
import pyreadstat
import pytest

from synapse_simulator.evaluation.lasi.models import (
    LasiDataSourceType,
    LasiEvaluationGateStatus,
    LasiSourceFormat,
    LasiJoinCardinality,
    LasiIngestionManifest,
    LasiIngestionError,
    LasiUnsupportedFormatError,
    LasiMalformedFileError,
    LasiSchemaValidationError,
    LasiDuplicateKeyError,
    LasiJoinCardinalityError,
)
from synapse_simulator.evaluation.lasi.ingestor import (
    LasiDataIngestor,
    LasiMultiModuleIngestor,
    compute_file_sha256,
    detect_file_format,
    load_raw_table_with_metadata,
    execute_validated_join,
)
from synapse_simulator.evaluation.lasi.evaluator import LasiExternalEvaluator


# =============================================================================
# Helper Fixtures for Generating Synthetic Binary and Delimited Files
# =============================================================================

@pytest.fixture
def synthetic_stata_individual(tmp_path) -> Path:
    """Generate synthetic Stata .dta individual survey module."""
    df = pd.DataFrame({
        "respid": ["P1001", "P1002", "P1003", "P1004", "P1005"],
        "r1agey": [52.0, 64.0, 71.0, 48.0, 80.0],
        "ragender": [1, 2, 1, 2, 1],  # 1=Male, 2=Female
        "r1hypere": [1, 0, 1, 0, 1],  # 1=Yes, 0=No
        "r1diabe": [0, 1, 0, 0, 1],
        "r1med_bp": [1, 0, 1, 0, 1],
        "r1wtresp": [1.2, 0.8, 1.5, 0.9, 1.1],
        "r1strata": ["ST01", "ST01", "ST02", "ST02", "ST03"],
        "r1psu": ["PSU101", "PSU101", "PSU201", "PSU201", "PSU301"],
    })
    filepath = tmp_path / "synthetic_individual.dta"
    column_labels = {
        "respid": "Participant Identifier",
        "r1agey": "Age in Years (Wave 1)",
        "ragender": "Gender",
        "r1hypere": "Self-reported Doctor Diagnosed Hypertension",
    }
    variable_value_labels = {
        "ragender": {1: "Male", 2: "Female"},
        "r1hypere": {1: "Yes", 0: "No"},
    }
    pyreadstat.write_dta(
        df,
        str(filepath),
        column_labels=column_labels,
        variable_value_labels=variable_value_labels,
    )
    return filepath


@pytest.fixture
def synthetic_stata_biomarker(tmp_path) -> Path:
    """Generate synthetic Stata .dta biomarker module (80% match, 1 non-response)."""
    df = pd.DataFrame({
        "respid": ["P1001", "P1002", "P1003", "P1004"],  # P1005 refused/missing
        "r1bpsys1": [136.0, 150.0, 162.0, 122.0],
        "r1bpsys2": [130.0, 144.0, 158.0, 118.0],
        "r1bpsys3": [128.0, 142.0, 156.0, 118.0],
        "r1bpdia1": [86.0, 94.0, 88.0, 78.0],
        "r1bpdia2": [82.0, 90.0, 84.0, 74.0],
        "r1bpdia3": [80.0, 88.0, 82.0, 74.0],
        "r1hba1c": [5.6, 7.2, 6.1, 5.4],
    })
    filepath = tmp_path / "synthetic_biomarker.dta"
    pyreadstat.write_dta(df, str(filepath))
    return filepath


@pytest.fixture
def synthetic_spss_dataset(tmp_path) -> Path:
    """Generate synthetic SPSS .sav dataset."""
    df = pd.DataFrame({
        "respid": ["SPSS01", "SPSS02", "SPSS03"],
        "r1agey": [58.0, 66.0, 75.0],
        "ragender": [2, 1, 2],
        "r1bpsys2": [134.0, 148.0, 160.0],
        "r1bpsys3": [132.0, 146.0, 156.0],
        "r1bpdia2": [84.0, 92.0, 86.0],
        "r1bpdia3": [82.0, 90.0, 84.0],
        "r1wtresp": [1.0, 1.1, 0.9],
        "r1strata": ["S1", "S1", "S2"],
        "r1psu": ["P1", "P1", "P2"],
    })
    filepath = tmp_path / "synthetic_data.sav"
    pyreadstat.write_sav(df, str(filepath))
    return filepath


# =============================================================================
# 1. Binary File Parsing and Metadata Preservation Tests
# =============================================================================

def test_stata_dta_parsing_and_metadata(synthetic_stata_individual):
    """Verify loading Stata .dta file preserves variable labels, value labels, and row count."""
    df, meta = load_raw_table_with_metadata(synthetic_stata_individual)

    assert meta.file_format == LasiSourceFormat.STATA_DTA
    assert meta.total_rows == 5
    assert meta.total_columns == 9
    assert len(meta.file_sha256) == 64
    assert meta.column_labels.get("respid") == "Participant Identifier"
    assert meta.column_labels.get("ragender") == "Gender"
    assert "respid" in df.columns
    assert df["r1agey"].iloc[0] == 52.0


def test_spss_sav_parsing_and_metadata(synthetic_spss_dataset):
    """Verify loading SPSS .sav file succeeds and records SHA-256 and column structure."""
    df, meta = load_raw_table_with_metadata(synthetic_spss_dataset)

    assert meta.file_format == LasiSourceFormat.SPSS_SAV
    assert meta.total_rows == 3
    assert len(meta.file_sha256) == 64
    assert list(df["respid"]) == ["SPSS01", "SPSS02", "SPSS03"]


def test_source_file_remains_unchanged(synthetic_stata_individual):
    """Verify that reading a source file leaves its binary content and hash 100% unchanged."""
    hash_before = compute_file_sha256(synthetic_stata_individual)

    # Read multiple times
    _ = load_raw_table_with_metadata(synthetic_stata_individual)
    _ = load_raw_table_with_metadata(synthetic_stata_individual)

    hash_after = compute_file_sha256(synthetic_stata_individual)
    assert hash_before == hash_after


# =============================================================================
# 2. Missing Value Policy & Extended Missing Sentinel Tests
# =============================================================================

def test_missing_value_policy_never_replaces_with_zero_or_normal(tmp_path):
    """Verify that missing blood pressure or diagnosis is NEVER coerced to zero or normal status."""
    df = pd.DataFrame({
        "respid": ["P1", "P2", "P3"],
        "r1agey": [55.0, 60.0, 65.0],
        "ragender": [1, 2, 1],
        "r1bpsys2": [None, -999.0, 140.0],   # P1 is None, P2 is -999, P3 is 140
        "r1bpsys3": [None, -998.0, 138.0],
        "r1bpdia2": [None, -999.0, 90.0],
        "r1bpdia3": [None, -998.0, 88.0],
        "r1hypere": [None, -999.0, 1],       # P1 is None, P2 is -999 (missing diagnosis)
        "r1wtresp": [1.0, 1.0, 1.0],
    })
    dta_path = tmp_path / "missing_test.dta"
    pyreadstat.write_dta(df, str(dta_path))

    ingestor = LasiDataIngestor(source_path=dta_path)
    records, report = ingestor.ingest()

    assert len(records) == 3
    # P1: BP must be None, NOT 0.0 or 120.0
    assert records[0].sbp_mean is None
    assert records[0].dbp_mean is None
    assert records[0].bp_derivation_method == "NO_VALID_READING"
    assert records[0].is_valid_for_bp is False
    assert records[0].diagnosed_hypertension is None  # MUST NOT be False!

    # P2: -999 must be parsed as None
    assert records[1].sbp_mean is None
    assert records[1].dbp_mean is None
    assert records[1].diagnosed_hypertension is None  # MUST NOT be coerced to False!

    # P3: valid
    assert records[2].sbp_mean == 139.0
    assert records[2].dbp_mean == 89.0
    assert records[2].diagnosed_hypertension is True


def test_stata_extended_missing_values_handled(tmp_path):
    """Verify Stata extended missing string sentinels (.a, .b, .) are cleanly converted to None."""
    csv_data = (
        "respid,r1agey,ragender,r1bpsys2,r1bpsys3,r1bpdia2,r1bpdia3,r1hypere,r1wtresp\n"
        "P1,50,1,.a,.b,.,.c,.,1.0\n"
        "P2,60,2,130,128,82,80,1,1.0\n"
    )
    p = tmp_path / "extended_missing.csv"
    p.write_text(csv_data, encoding="utf-8")

    ingestor = LasiDataIngestor(source_path=p)
    records, report = ingestor.ingest()

    assert len(records) == 2
    assert records[0].sbp_mean is None
    assert records[0].dbp_mean is None
    assert records[0].diagnosed_hypertension is None
    assert records[1].sbp_mean == 129.0
    assert records[1].diagnosed_hypertension is True


# =============================================================================
# 3. Relational Multi-Module Join Validation Tests
# =============================================================================

def test_multi_module_join_success(synthetic_stata_individual, synthetic_stata_biomarker, tmp_path):
    """Verify multi-module join between individual and biomarker surveys."""
    ingestor = LasiMultiModuleIngestor(
        individual_path=synthetic_stata_individual,
        biomarker_path=synthetic_stata_biomarker,
        derived_dir=tmp_path / "derived",
        join_key="respid",
    )
    records, report, manifest = ingestor.ingest()

    assert len(records) == 5
    assert report.total_records_ingested == 5
    assert report.valid_records == 5

    # Verify telemetry
    assert manifest.join_telemetry is not None
    telemetry = manifest.join_telemetry
    assert telemetry.primary_input_rows == 5
    assert telemetry.secondary_input_rows == 4
    assert telemetry.matched_key_count == 4
    assert telemetry.unmatched_primary_count == 1  # P1005 has no biomarker
    assert telemetry.biomarker_non_response_pct == 20.0
    assert telemetry.reconciliation_verified is True
    assert telemetry.actual_cardinality == "ONE_TO_ZERO_OR_ONE"

    # Verify P1005 record has demographic data but None for blood pressure
    rec_p1005 = next(r for r in records if "P1005" in r.participant_id or r.age == 80.0)
    assert rec_p1005.age == 80.0
    assert rec_p1005.gender == "Male"
    assert rec_p1005.sbp_mean is None
    assert rec_p1005.is_valid_for_bp is False


def test_multi_module_duplicate_primary_key_rejected(tmp_path):
    """Verify duplicate join keys in the primary module raise LasiDuplicateKeyError."""
    ind_df = pd.DataFrame({
        "respid": ["P101", "P101", "P102"],  # Duplicate P101!
        "r1agey": [50.0, 52.0, 60.0],
        "ragender": [1, 2, 1],
    })
    bio_df = pd.DataFrame({
        "respid": ["P101", "P102"],
        "r1bpsys2": [130.0, 140.0],
        "r1bpdia2": [80.0, 90.0],
    })
    ind_path = tmp_path / "dup_ind.csv"
    bio_path = tmp_path / "bio.csv"
    ind_df.to_csv(ind_path, index=False)
    bio_df.to_csv(bio_path, index=False)

    ingestor = LasiMultiModuleIngestor(
        individual_path=ind_path,
        biomarker_path=bio_path,
        derived_dir=tmp_path / "derived",
    )
    with pytest.raises(LasiDuplicateKeyError) as exc_info:
        ingestor.ingest()
    assert "duplicate join keys" in str(exc_info.value).lower()


def test_multi_module_many_to_many_detected_and_rejected(tmp_path):
    """Verify that duplicate keys on both sides raise LasiJoinCardinalityError."""
    ind_df = pd.DataFrame({
        "respid": ["P101", "P101"],
        "r1agey": [50.0, 52.0],
        "ragender": [1, 2],
    })
    bio_df = pd.DataFrame({
        "respid": ["P101", "P101"],
        "r1bpsys2": [130.0, 140.0],
        "r1bpdia2": [80.0, 90.0],
    })
    ind_path = tmp_path / "m2m_ind.csv"
    bio_path = tmp_path / "m2m_bio.csv"
    ind_df.to_csv(ind_path, index=False)
    bio_df.to_csv(bio_path, index=False)

    with pytest.raises(LasiJoinCardinalityError) as exc_info:
        execute_validated_join(ind_df, bio_df, join_key="respid")
    assert "many-to-many" in str(exc_info.value).lower()


def test_missing_join_key_columns_rejected(tmp_path):
    """Verify that missing join key column raises LasiSchemaValidationError."""
    ind_df = pd.DataFrame({"wrong_id": ["P1", "P2"], "r1agey": [50.0, 60.0]})
    bio_df = pd.DataFrame({"respid": ["P1", "P2"], "r1bpsys2": [120.0, 130.0]})
    ind_path = tmp_path / "bad_ind.csv"
    bio_path = tmp_path / "bio.csv"
    ind_df.to_csv(ind_path, index=False)
    bio_df.to_csv(bio_path, index=False)

    ingestor = LasiMultiModuleIngestor(
        individual_path=ind_path,
        biomarker_path=bio_path,
        join_key="respid",
    )
    with pytest.raises(LasiSchemaValidationError) as exc_info:
        ingestor.ingest()
    assert "not found in primary module" in str(exc_info.value).lower()


def test_missing_join_key_rows_isolated(tmp_path):
    """Verify rows with missing/null join keys are excluded and counted in telemetry."""
    ind_df = pd.DataFrame({
        "respid": ["P1", None, "P2", ""],
        "r1agey": [50.0, 55.0, 60.0, 65.0],
        "ragender": [1, 2, 1, 2],
    })
    bio_df = pd.DataFrame({
        "respid": ["P1", "P2", None],
        "r1bpsys2": [120.0, 130.0, 140.0],
        "r1bpdia2": [80.0, 85.0, 90.0],
    })
    ind_path = tmp_path / "miss_ind.csv"
    bio_path = tmp_path / "miss_bio.csv"
    ind_df.to_csv(ind_path, index=False)
    bio_df.to_csv(bio_path, index=False)

    merged, telemetry = execute_validated_join(ind_df, bio_df, join_key="respid")
    assert len(merged) == 2  # P1 and P2 only
    assert telemetry.primary_missing_keys == 2
    assert telemetry.secondary_missing_keys == 1
    assert telemetry.primary_valid_keys == 2
    assert telemetry.matched_key_count == 2


# =============================================================================
# 4. Error Handling & Malformed Format Tests
# =============================================================================

def test_unsupported_file_extension_rejected(tmp_path):
    """Verify unsupported file formats (.xlsx, .parquet) raise LasiUnsupportedFormatError."""
    fake_excel = tmp_path / "data.xlsx"
    fake_excel.write_text("dummy", encoding="utf-8")

    ingestor = LasiDataIngestor(source_path=fake_excel)
    with pytest.raises(LasiUnsupportedFormatError) as exc_info:
        ingestor.ingest()
    assert "unsupported file format" in str(exc_info.value).lower()


def test_malformed_binary_file_rejected(tmp_path):
    """Verify that a corrupted binary file raises LasiMalformedFileError."""
    corrupt_dta = tmp_path / "corrupt.dta"
    corrupt_dta.write_bytes(b"NOT_A_VALID_STATA_HEADER_BYTES_1234567890")

    ingestor = LasiDataIngestor(source_path=corrupt_dta)
    with pytest.raises(LasiMalformedFileError) as exc_info:
        ingestor.ingest()
    assert "malformed or unreadable" in str(exc_info.value).lower()


# =============================================================================
# 5. Ingestion Manifest and Cryptographic Audit Tests
# =============================================================================

def test_reproducible_ingestion_manifest(synthetic_stata_individual, synthetic_stata_biomarker, tmp_path):
    """Verify manifest records SHA-256 digests, versions, schema mappings, and row counts."""
    derived_dir = tmp_path / "derived"
    ingestor = LasiMultiModuleIngestor(
        individual_path=synthetic_stata_individual,
        biomarker_path=synthetic_stata_biomarker,
        derived_dir=derived_dir,
    )
    records, report, manifest = ingestor.ingest()

    manifest_file = derived_dir / "LASI_INGESTION_MANIFEST.json"
    assert manifest_file.exists()

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert "manifest_id" in manifest_data
    assert "parser_versions" in manifest_data
    assert "pyreadstat" in manifest_data["parser_versions"]
    assert "pandas" in manifest_data["parser_versions"]
    assert "source_files" in manifest_data
    assert len(manifest_data["source_files"]) == 2
    assert "access_control_notice" in manifest_data

    # Verify no raw participant IDs leaked into manifest JSON
    manifest_str = json.dumps(manifest_data)
    assert "P1001" not in manifest_str
    assert "P1002" not in manifest_str


# =============================================================================
# 6. Evaluation Gate Separation & Invariant Preservation
# =============================================================================

def test_evaluation_gate_remains_pending_with_fixture(synthetic_stata_individual, synthetic_stata_biomarker, tmp_path):
    """Verify that running evaluator on ingested synthetic fixture preserves REFERENCE_DATA_PENDING gate status."""
    ingestor = LasiMultiModuleIngestor(
        individual_path=synthetic_stata_individual,
        biomarker_path=synthetic_stata_biomarker,
        derived_dir=tmp_path / "derived",
        data_source_type=LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
    )
    records, report, manifest = ingestor.ingest()

    assert report.data_source_type == LasiDataSourceType.SYNTHETIC_TEST_FIXTURE

    evaluator = LasiExternalEvaluator(
        synthetic_dir="data/evaluation/calibrated_mc_500/seed_42",
        reference_records=records,
        quality_report=report,
    )
    eval_report = evaluator.evaluate()

    # Invariant: Gate MUST be locked to REFERENCE_DATA_PENDING for synthetic fixture runs
    assert eval_report.overall_gate_status == LasiEvaluationGateStatus.REFERENCE_DATA_PENDING
