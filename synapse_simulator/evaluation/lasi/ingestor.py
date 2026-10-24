"""
LASI Wave 1 Multi-Format Binary and Tabular Ingestor and Quality Auditor.

Implements Milestone 2:
1. Multi-format loading supporting Stata (.dta), SPSS (.sav), and delimited text (.csv, .tsv)
   via pyreadstat and pandas, with immutable source file hashing.
2. Participant pseudonymization / de-identification using SHA-256 prefixes.
3. Explicit variable normalization, preserving variable labels, value labels, and source metadata.
4. Comprehensive missing value handling: Stata extended missings (.a-.z, .), SPSS user missings,
   and numeric sentinels (-999, -998, -997, -99, 999, 9999). Never silently replaces missing
   measurements with zero, normal BP, or negative disease status.
5. Validated multi-module joins (Individual Survey + Biomarker Module) with key validation,
   duplicate detection, cardinality enforcement, biomarker non-response calculation,
   and row-count reconciliation.
6. Protocol-compliant blood pressure averaging (2nd & 3rd reading average with fallback auditing).
7. Complex survey design extraction (sampling weights, strata, PSU, Kish effective sample size).
8. Immutable cryptographic ingestion manifest generation (LASI_INGESTION_MANIFEST.json).
9. Export of derived, de-identified evaluation datasets (lasi_cleaned_records.csv).
"""

import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

import pandas as pd
import pyreadstat

from synapse_simulator.evaluation.metrics import (
    effective_sample_size,
    survey_design_effect_weighting,
)
from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiDataQualityReport,
    LasiDataSourceType,
    LasiSourceFormat,
    LasiJoinCardinality,
    LasiSourceFileMetadata,
    LasiJoinTelemetry,
    LasiIngestionManifest,
    LasiIngestionError,
    LasiUnsupportedFormatError,
    LasiMalformedFileError,
    LasiSchemaValidationError,
    LasiDuplicateKeyError,
    LasiJoinCardinalityError,
)
from synapse_simulator.evaluation.lasi.comparability import (
    PopulationComparabilityLayer,
)
from synapse_simulator.evaluation.lasi.security import (
    KeyedPseudonymizer,
    CONFIDENTIALITY_NOTICE,
)
from synapse_simulator.evaluation.lasi.missingness import (
    VariableMissingValuePolicy,
    UNIVERSAL_STRING_MISSINGS,
)
from synapse_simulator.evaluation.lasi.diagnostics import (
    LasiSurveyDesignDiagnostics,
)


# Known missing value sentinel representations in LASI / survey microdata
NUMERIC_MISSING_CODES = {-999, -998, -997, -99, 9999, 999, 999.0, 9999.0, -999.0, -998.0, -997.0, -99.0}
STRING_MISSING_VALUES = {
    "", ".", "na", "nan", "null", "none", "-999", "-998", "-997", "-99", "999", "9999",
    ".a", ".b", ".c", ".d", ".e", ".f", ".g", ".h", ".i", ".j", ".k", ".l", ".m",
    ".n", ".o", ".p", ".q", ".r", ".s", ".t", ".u", ".v", ".w", ".x", ".y", ".z",
}

# Plausible physiological validation ranges
MIN_AGE, MAX_AGE = 18.0, 120.0
MIN_SBP, MAX_SBP = 60.0, 280.0
MIN_DBP, MAX_DBP = 40.0, 160.0
MIN_HBA1C, MAX_HBA1C = 3.5, 20.0

# Supported binary and text file extensions
SUPPORTED_EXTENSIONS = {
    ".dta": LasiSourceFormat.STATA_DTA,
    ".sav": LasiSourceFormat.SPSS_SAV,
    ".csv": LasiSourceFormat.CSV,
    ".tsv": LasiSourceFormat.TSV,
}


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Compute hex SHA-256 checksum of an immutable source file."""
    path = Path(filepath)
    if not path.exists():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def detect_file_format(filepath: Union[str, Path]) -> LasiSourceFormat:
    """Detect file format from extension, raising LasiUnsupportedFormatError if unsupported."""
    path = Path(filepath)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported_str = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise LasiUnsupportedFormatError(
            f"Unsupported file format '{suffix}' for {path.name}. Supported formats: {supported_str}"
        )
    return SUPPORTED_EXTENSIONS[suffix]


def load_raw_table_with_metadata(
    filepath: Union[str, Path]
) -> Tuple[pd.DataFrame, LasiSourceFileMetadata]:
    """Load a Stata (.dta), SPSS (.sav), CSV, or TSV file, preserving metadata.

    Source files remain strictly unchanged.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    fmt = detect_file_format(path)
    file_sha256 = compute_file_sha256(path)
    file_size = path.stat().st_size

    column_labels: Dict[str, Optional[str]] = {}
    variable_value_labels: Dict[str, Dict[Any, str]] = {}
    has_user_missing = False
    user_missing_counts: Dict[str, int] = {}

    try:
        if fmt == LasiSourceFormat.STATA_DTA:
            # Read Stata file via pyreadstat preserving user missing codes
            df, meta = pyreadstat.read_dta(str(path), user_missing=True)
            column_labels = meta.column_names_to_labels or {}
            variable_value_labels = meta.variable_value_labels or {}
            missing_ranges = getattr(meta, "missing_ranges", {})
            has_user_missing = bool(missing_ranges)
            if missing_ranges:
                user_missing_counts = {col: len(ranges) for col, ranges in missing_ranges.items()}

        elif fmt == LasiSourceFormat.SPSS_SAV:
            # Read SPSS file via pyreadstat preserving user missing codes
            df, meta = pyreadstat.read_sav(str(path), user_missing=True)
            column_labels = meta.column_names_to_labels or {}
            variable_value_labels = meta.variable_value_labels or {}
            missing_ranges = getattr(meta, "missing_ranges", {})
            has_user_missing = bool(missing_ranges)
            if missing_ranges:
                user_missing_counts = {col: len(ranges) for col, ranges in missing_ranges.items()}

        elif fmt in {LasiSourceFormat.CSV, LasiSourceFormat.TSV}:
            delimiter = "\t" if fmt == LasiSourceFormat.TSV else ","
            if fmt == LasiSourceFormat.CSV:
                with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                    first_line = f.readline()
                    if "\t" in first_line and "," not in first_line:
                        delimiter = "\t"
            df = pd.read_csv(str(path), sep=delimiter, encoding="utf-8-sig", low_memory=False)

        else:
            raise LasiUnsupportedFormatError(f"Unsupported format: {fmt}")

    except (pyreadstat.PyreadstatError, pd.errors.ParserError, Exception) as e:
        if isinstance(e, (LasiUnsupportedFormatError, FileNotFoundError)):
            raise
        raise LasiMalformedFileError(f"Malformed or unreadable file at {path}: {str(e)}") from e

    metadata = LasiSourceFileMetadata(
        file_path=str(path.resolve()),
        file_name=path.name,
        file_sha256=file_sha256,
        file_size_bytes=file_size,
        file_format=fmt,
        total_rows=len(df),
        total_columns=len(df.columns),
        column_names=list(df.columns),
        column_labels=column_labels,
        variable_value_labels=variable_value_labels,
        has_user_missing_values=has_user_missing,
        user_missing_counts=user_missing_counts,
    )

    return df, metadata


def execute_validated_join(
    primary_df: pd.DataFrame,
    secondary_df: pd.DataFrame,
    primary_name: str = "individual_survey",
    secondary_name: str = "biomarker_module",
    join_key: str = "respid",
    expected_cardinality: LasiJoinCardinality = LasiJoinCardinality.ONE_TO_ZERO_OR_ONE,
) -> Tuple[pd.DataFrame, LasiJoinTelemetry]:
    """Execute validated relational join between two survey modules.

    Enforces:
    1. Join key existence in both modules (checking case-insensitive aliases).
    2. Missing key detection (missing keys are never treated as matching identifiers).
    3. Duplicate key detection on primary module (0 duplicates permitted).
    4. Explicit cardinality validation (prevents unexpected many-to-many joins).
    5. Row-count reconciliation before and after joining.
    6. Non-response calculation for secondary module.
    """
    # 1. Resolve join key in primary module
    primary_cols_lower = {str(c).strip().lower(): str(c) for c in primary_df.columns}
    secondary_cols_lower = {str(c).strip().lower(): str(c) for c in secondary_df.columns}

    resolved_primary_key = None
    if join_key.lower() in primary_cols_lower:
        resolved_primary_key = primary_cols_lower[join_key.lower()]
    else:
        for alias in ["respid", "prim_key", "individual_id", "participant_id", "r1id", "subjid", "id"]:
            if alias in primary_cols_lower:
                resolved_primary_key = primary_cols_lower[alias]
                break

    if not resolved_primary_key:
        raise LasiSchemaValidationError(
            f"Join key '{join_key}' not found in primary module '{primary_name}'. "
            f"Available columns: {list(primary_df.columns[:15])}"
        )

    resolved_secondary_key = None
    if join_key.lower() in secondary_cols_lower:
        resolved_secondary_key = secondary_cols_lower[join_key.lower()]
    else:
        for alias in ["respid", "prim_key", "individual_id", "participant_id", "r1id", "subjid", "id"]:
            if alias in secondary_cols_lower:
                resolved_secondary_key = secondary_cols_lower[alias]
                break

    if not resolved_secondary_key:
        raise LasiSchemaValidationError(
            f"Join key '{join_key}' not found in secondary module '{secondary_name}'. "
            f"Available columns: {list(secondary_df.columns[:15])}"
        )

    # 2. Key Cleaning and Type Normalization
    def clean_key_series(series: pd.Series) -> pd.Series:
        def clean_val(v: Any) -> str:
            if v is None or pd.isna(v):
                return ""
            v_str = str(v).strip()
            # If float with .0, normalize (e.g. 1001.0 -> 1001)
            if v_str.endswith(".0"):
                v_str = v_str[:-2]
            if v_str.lower() in STRING_MISSING_VALUES or v_str in {"-999", "-998", "-99"}:
                return ""
            return v_str

        return series.apply(clean_val)

    primary_clean_keys = clean_key_series(primary_df[resolved_primary_key])
    secondary_clean_keys = clean_key_series(secondary_df[resolved_secondary_key])

    primary_missing_keys = int((primary_clean_keys == "").sum())
    secondary_missing_keys = int((secondary_clean_keys == "").sum())

    # Filter out missing keys
    primary_valid_mask = primary_clean_keys != ""
    secondary_valid_mask = secondary_clean_keys != ""

    primary_valid = primary_df[primary_valid_mask].copy()
    primary_valid["__join_key_norm"] = primary_clean_keys[primary_valid_mask]

    secondary_valid = secondary_df[secondary_valid_mask].copy()
    secondary_valid["__join_key_norm"] = secondary_clean_keys[secondary_valid_mask]
    secondary_valid["__in_biomarker_module"] = True

    # 3. Duplicate Key Detection
    primary_duplicate_count = int(primary_valid["__join_key_norm"].duplicated().sum())
    secondary_duplicate_count = int(secondary_valid["__join_key_norm"].duplicated().sum())

    if primary_duplicate_count > 0 and secondary_duplicate_count > 0:
        raise LasiJoinCardinalityError(
            f"Fatal Many-to-Many join detected on '{join_key}'! "
            f"Primary module '{primary_name}' has {primary_duplicate_count} duplicate keys and "
            f"secondary module '{secondary_name}' has {secondary_duplicate_count} duplicate keys."
        )

    if primary_duplicate_count > 0:
        raise LasiDuplicateKeyError(
            f"Primary module '{primary_name}' contains {primary_duplicate_count} duplicate join keys for '{join_key}'. "
            f"Primary keys in the individual survey must be strictly unique."
        )

    if secondary_duplicate_count > 0:
        if expected_cardinality in {LasiJoinCardinality.ONE_TO_ONE, LasiJoinCardinality.ONE_TO_ZERO_OR_ONE}:
            raise LasiJoinCardinalityError(
                f"Secondary module '{secondary_name}' contains {secondary_duplicate_count} duplicate join keys for '{join_key}', "
                f"violating expected cardinality '{expected_cardinality.value}'."
            )

    # 4. Perform Relational Left Join
    # Drop colliding columns from secondary except join key and marker
    common_cols = (set(primary_valid.columns) & set(secondary_valid.columns)) - {"__join_key_norm", "__in_biomarker_module"}
    secondary_renamed = secondary_valid.copy()
    for col in common_cols:
        secondary_renamed = secondary_renamed.rename(columns={col: f"{col}_{secondary_name}"})

    merged_df = pd.merge(
        primary_valid,
        secondary_renamed,
        on="__join_key_norm",
        how="left",
    )

    # Reconcile row counts
    reconciliation_verified = (len(merged_df) == len(primary_valid))
    if not reconciliation_verified:
        raise LasiJoinCardinalityError(
            f"Row count reconciliation failed! Primary rows: {len(primary_valid)}, Merged rows: {len(merged_df)}"
        )

    # 5. Compute Match Telemetry
    p_keys = set(primary_valid["__join_key_norm"])
    s_keys = set(secondary_valid["__join_key_norm"])
    matched_count = len(p_keys & s_keys)
    unmatched_primary = len(p_keys - s_keys)
    unmatched_secondary = len(s_keys - p_keys)
    non_response_pct = round((unmatched_primary / max(1, len(p_keys))) * 100.0, 2)

    actual_cardinality = "ONE_TO_ONE" if unmatched_primary == 0 and secondary_duplicate_count == 0 else "ONE_TO_ZERO_OR_ONE"

    # Drop temporary normalization column
    merged_df = merged_df.drop(columns=["__join_key_norm"])

    telemetry = LasiJoinTelemetry(
        join_key=join_key,
        expected_cardinality=expected_cardinality,
        actual_cardinality=actual_cardinality,
        primary_module_name=primary_name,
        secondary_module_name=secondary_name,
        primary_input_rows=len(primary_df),
        secondary_input_rows=len(secondary_df),
        primary_valid_keys=len(primary_valid),
        secondary_valid_keys=len(secondary_valid),
        primary_missing_keys=primary_missing_keys,
        secondary_missing_keys=secondary_missing_keys,
        primary_duplicate_keys=primary_duplicate_count,
        secondary_duplicate_keys=secondary_duplicate_count,
        merged_output_rows=len(merged_df),
        matched_key_count=matched_count,
        unmatched_primary_count=unmatched_primary,
        unmatched_secondary_count=unmatched_secondary,
        biomarker_non_response_pct=non_response_pct,
        reconciliation_verified=reconciliation_verified,
    )

    return merged_df, telemetry


class LasiDataIngestor:
    """Loads, cleans, validates, and summarizes LASI Wave 1 reference microdata.

    Supports:
    - Single-table loading (.dta, .sav, .csv, .tsv).
    - Multi-module relational joining (Individual + Biomarker).
    - Immutable cryptographic manifest generation (LASI_INGESTION_MANIFEST.json).
    - Full backward compatibility with existing tests and evaluator pipeline.
    """

    def __init__(
        self,
        source_path: Optional[Union[str, Path]] = None,
        derived_dir: Optional[Union[str, Path]] = None,
        data_source_type: LasiDataSourceType = LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
        strict_protocol_bp: bool = False,
        enable_venous_hba1c: bool = False,
        # Multi-module options
        individual_module_path: Optional[Union[str, Path]] = None,
        biomarker_module_path: Optional[Union[str, Path]] = None,
        join_key: str = "respid",
        expected_cardinality: LasiJoinCardinality = LasiJoinCardinality.ONE_TO_ZERO_OR_ONE,
        # Security & Missingness options
        pseudonymization_key: Optional[Union[str, bytes]] = None,
        variable_missing_policy: Optional[VariableMissingValuePolicy] = None,
    ):
        self.source_path = Path(source_path) if source_path else None
        self.individual_module_path = Path(individual_module_path) if individual_module_path else None
        self.biomarker_module_path = Path(biomarker_module_path) if biomarker_module_path else None
        self.join_key = join_key
        self.expected_cardinality = expected_cardinality

        if derived_dir:
            self.derived_dir = Path(derived_dir)
        elif self.source_path:
            self.derived_dir = self.source_path.parent / "derived"
        elif self.individual_module_path:
            self.derived_dir = self.individual_module_path.parent / "derived"
        else:
            self.derived_dir = Path("data/evaluation/lasi/derived")

        self.data_source_type = data_source_type
        self.strict_protocol_bp = strict_protocol_bp
        self.enable_venous_hba1c = enable_venous_hba1c
        self.pseudonymizer = KeyedPseudonymizer(secret_key=pseudonymization_key)
        self.missing_policy = variable_missing_policy or VariableMissingValuePolicy()
        self.diagnostics_report = None

        self.file_sha256 = ""
        self.cleaned_records: List[LasiCleanedRecord] = []
        self.quality_report: Optional[LasiDataQualityReport] = None
        self.manifest: Optional[LasiIngestionManifest] = None
        self.join_telemetry: Optional[LasiJoinTelemetry] = None
        self.source_files_metadata: Dict[str, LasiSourceFileMetadata] = {}

    def calculate_file_sha256(self) -> str:
        """Compute SHA-256 hash of the primary raw input file for provenance tracking."""
        target = self.source_path or self.individual_module_path
        if not target or not target.exists():
            return ""
        return compute_file_sha256(target)

    def _parse_float(self, value: Any) -> Optional[float]:
        """Safely parse float, mapping known survey missing codes to None."""
        if value is None or pd.isna(value):
            return None
        v_str = str(value).strip().lower()
        if v_str in STRING_MISSING_VALUES:
            return None
        try:
            val = float(v_str)
            if math.isnan(val) or math.isinf(val):
                return None
            if val in NUMERIC_MISSING_CODES:
                return None
            return val
        except (ValueError, TypeError):
            return None

    def _parse_bool(self, value: Any) -> Optional[bool]:
        """Parse survey indicator variables (1=Yes, 0=No, 2=No)."""
        if value is None or pd.isna(value):
            return None
        v_str = str(value).strip().lower()
        if v_str in STRING_MISSING_VALUES:
            return None
        if v_str in {"1", "1.0", "true", "yes", "y"}:
            return True
        if v_str in {"0", "0.0", "2", "2.0", "false", "no", "n"}:
            return False
        return None

    def _calculate_average_bp(
        self,
        r1: Optional[float],
        r2: Optional[float],
        r3: Optional[float],
    ) -> Tuple[Optional[float], str]:
        """Apply LASI clinical averaging rule for blood pressure.
        
        Protocol rule:
        - Primary measurement is the arithmetic mean of reading 2 and reading 3.
        - If only reading 2 is valid, use reading 2 (FALLBACK_READING_2_ONLY).
        - If only reading 3 is valid, use reading 3 (FALLBACK_READING_3_ONLY).
        - If neither 2 nor 3 is valid, fallback to reading 1 (FALLBACK_READING_1_ONLY).
        - If none are valid, return (None, NO_VALID_READING).
        """
        valid_2 = r2 is not None and (MIN_SBP <= r2 <= MAX_SBP or MIN_DBP <= r2 <= MAX_DBP)
        valid_3 = r3 is not None and (MIN_SBP <= r3 <= MAX_SBP or MIN_DBP <= r3 <= MAX_DBP)
        valid_1 = r1 is not None and (MIN_SBP <= r1 <= MAX_SBP or MIN_DBP <= r1 <= MAX_DBP)

        if valid_2 and valid_3:
            return round((r2 + r3) / 2.0, 1), "MEAN_2_3"
        elif valid_2:
            return round(r2, 1), "READING_2_ONLY"
        elif valid_3:
            return round(r3, 1), "READING_3_ONLY"
        elif valid_1:
            return round(r1, 1), "FALLBACK_READING_1"
        else:
            return None, "NO_VALID_READING"

    def ingest(self) -> Tuple[List[LasiCleanedRecord], LasiDataQualityReport]:
        """Ingest reference dataset (single-file or multi-module), clean records, and build manifest."""
        if self.individual_module_path and self.biomarker_module_path:
            records, report, _ = self.ingest_modules(
                individual_path=self.individual_module_path,
                biomarker_path=self.biomarker_module_path,
                join_key=self.join_key,
                expected_cardinality=self.expected_cardinality,
            )
            return records, report

        if not self.source_path or not self.source_path.exists():
            raise FileNotFoundError(f"LASI reference file not found: {self.source_path}")

        # Single-file ingestion pipeline
        df, meta = load_raw_table_with_metadata(self.source_path)
        self.file_sha256 = meta.file_sha256
        self.source_files_metadata = {self.source_path.name: meta}

        records, report = self._process_dataframe(
            df=df,
            source_file_label=str(self.source_path),
            file_sha256=meta.file_sha256,
        )

        # Generate cryptographic manifest
        manifest = self._generate_manifest(
            source_files={self.source_path.name: meta},
            join_telemetry=None,
            row_counts={
                "total_rows_ingested": report.total_records_ingested,
                "valid_records": report.valid_records,
                "excluded_records": report.excluded_records,
            },
        )
        self.manifest = manifest

        if self.derived_dir:
            self._write_derived_csv()
            self._write_manifest(manifest)
            diag_engine = LasiSurveyDesignDiagnostics(
                records=records,
                source_label=str(self.source_path),
                join_telemetry=None,
            )
            diag_engine.export_report_artifacts(self.derived_dir)

        return records, report

    def ingest_modules(
        self,
        individual_path: Union[str, Path],
        biomarker_path: Union[str, Path],
        join_key: str = "respid",
        expected_cardinality: LasiJoinCardinality = LasiJoinCardinality.ONE_TO_ZERO_OR_ONE,
    ) -> Tuple[List[LasiCleanedRecord], LasiDataQualityReport, LasiIngestionManifest]:
        """Ingest and join multi-module LASI Stata/SPSS/CSV files."""
        ind_path = Path(individual_path)
        bio_path = Path(biomarker_path)

        ind_df, ind_meta = load_raw_table_with_metadata(ind_path)
        bio_df, bio_meta = load_raw_table_with_metadata(bio_path)

        self.source_files_metadata = {
            ind_path.name: ind_meta,
            bio_path.name: bio_meta,
        }
        self.file_sha256 = ind_meta.file_sha256

        # Execute validated join
        merged_df, join_telemetry = execute_validated_join(
            primary_df=ind_df,
            secondary_df=bio_df,
            primary_name=ind_path.name,
            secondary_name=bio_path.name,
            join_key=join_key,
            expected_cardinality=expected_cardinality,
        )
        self.join_telemetry = join_telemetry

        # Process joined dataset
        records, report = self._process_dataframe(
            df=merged_df,
            source_file_label=f"{ind_path.name} + {bio_path.name}",
            file_sha256=ind_meta.file_sha256,
        )

        report.multi_module_joined = True
        report.join_telemetry = join_telemetry.model_dump()

        # Build manifest
        manifest = self._generate_manifest(
            source_files=self.source_files_metadata,
            join_telemetry=join_telemetry,
            row_counts={
                "individual_input_rows": join_telemetry.primary_input_rows,
                "biomarker_input_rows": join_telemetry.secondary_input_rows,
                "merged_output_rows": join_telemetry.merged_output_rows,
                "valid_cleaned_records": report.valid_records,
                "excluded_records": report.excluded_records,
            },
        )
        self.manifest = manifest

        if self.derived_dir:
            self._write_derived_csv()
            self._write_manifest(manifest)
            diag_engine = LasiSurveyDesignDiagnostics(
                records=records,
                source_label=f"{ind_path.name} + {bio_path.name}",
                join_telemetry=join_telemetry,
            )
            diag_engine.export_report_artifacts(self.derived_dir)

        return records, report, manifest

    def _process_dataframe(
        self,
        df: pd.DataFrame,
        source_file_label: str,
        file_sha256: str,
    ) -> Tuple[List[LasiCleanedRecord], LasiDataQualityReport]:
        """Normalize dataframe rows into LasiCleanedRecord objects and calculate quality statistics."""
        seen_ids = set()
        duplicate_count = 0
        total_rows = len(df)
        excluded_count = 0

        missingness: Dict[str, int] = {
            "age": 0, "gender": 0, "sbp_mean": 0, "dbp_mean": 0,
            "hba1c": 0, "diagnosed_hypertension": 0, "diagnosed_diabetes": 0,
            "survey_weight": 0,
        }
        out_of_range: Dict[str, int] = {
            "age": 0, "sbp": 0, "dbp": 0, "hba1c": 0,
        }
        quality_flags: List[str] = []

        bp_derivation_counts: Dict[str, int] = {
            "PROTOCOL_MEAN_READINGS_2_AND_3": 0,
            "FALLBACK_READING_2_ONLY": 0,
            "FALLBACK_READING_3_ONLY": 0,
            "FALLBACK_READING_1_ONLY": 0,
            "NO_VALID_READING": 0,
        }

        cleaned_records: List[LasiCleanedRecord] = []

        fn_lower = {str(fn).strip().lower(): str(fn) for fn in df.columns}

        def get_val(row_dict: Dict[str, Any], *aliases: str) -> Optional[Any]:
            for alias in aliases:
                a_lower = alias.lower()
                if a_lower in fn_lower:
                    val = row_dict.get(fn_lower[a_lower])
                    if val is not None and not (isinstance(val, float) and math.isnan(val)):
                        return val
            return None

        # Convert dataframe to record dictionaries
        records_iter = df.to_dict(orient="records")

        for row_idx, row in enumerate(records_iter, start=1):
            # 1. Identifier extraction & keyed pseudonymization
            raw_id = get_val(
                row, "participant_id", "respid", "individual_id", "subjid", "r1id", "id", "prim_key"
            )
            surrogate_id = self.pseudonymizer.pseudonymize_participant(raw_id, fallback_index=row_idx)

            if surrogate_id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(surrogate_id)

            # Household linkage key
            raw_hhid = get_val(row, "household_id", "hhid", "r1hhid", "householdid", "hh_id")
            if raw_hhid is None and "household" in fn_lower:
                raw_hhid = row.get(fn_lower["household"])
            if raw_hhid is None and "prim_key" in fn_lower and raw_id != row.get(fn_lower["prim_key"]):
                raw_hhid = row.get(fn_lower["prim_key"])
            surrogate_hhid = self.pseudonymizer.pseudonymize_household(raw_hhid)

            # Geographic indicators
            raw_state = get_val(row, "state", "r1state", "state_name", "state_code")
            state_str = str(raw_state).strip() if raw_state is not None and str(raw_state).strip().lower() not in UNIVERSAL_STRING_MISSINGS else None

            raw_urban = get_val(row, "urban_rural", "urban", "sector", "r1urban", "rural")
            urban_str = None
            if raw_urban is not None:
                u_cand = str(raw_urban).strip().lower()
                if u_cand not in UNIVERSAL_STRING_MISSINGS:
                    if u_cand in {"1", "1.0", "rural", "r"}:
                        urban_str = "Rural"
                    elif u_cand in {"2", "2.0", "urban", "u"}:
                        urban_str = "Urban"
                    else:
                        urban_str = str(raw_urban).strip()

            # 2. Demographics with variable-specific missing policy
            raw_age, _ = self.missing_policy.clean_age(
                get_val(row, "r1agey", "age", "age_years", "age_yrs"),
                raw_col_name="age",
            )
            if raw_age is None:
                missingness["age"] += 1
                excluded_count += 1
                continue
            if raw_age < MIN_AGE or raw_age > MAX_AGE:
                out_of_range["age"] += 1
                excluded_count += 1
                continue

            raw_gender = get_val(row, "ragender", "gender", "sex")
            if raw_gender is None or str(raw_gender).strip().lower() in UNIVERSAL_STRING_MISSINGS:
                missingness["gender"] += 1
                excluded_count += 1
                continue

            g_str = str(raw_gender).strip().lower()
            if g_str in {"1", "1.0", "male", "m"}:
                gender = "Male"
            elif g_str in {"2", "2.0", "female", "f"}:
                gender = "Female"
            else:
                missingness["gender"] += 1
                excluded_count += 1
                continue

            # 3. Blood pressure readings with variable-specific policy (preserving 99.0 mmHg)
            s1, _ = self.missing_policy.clean_blood_pressure(get_val(row, "r1bpsys1", "bpsys1", "sbp1", "sbp_1"), "sbp1", is_systolic=True)
            s2, _ = self.missing_policy.clean_blood_pressure(get_val(row, "r1bpsys2", "bpsys2", "sbp2", "sbp_2"), "sbp2", is_systolic=True)
            s3, _ = self.missing_policy.clean_blood_pressure(get_val(row, "r1bpsys3", "bpsys3", "sbp3", "sbp_3"), "sbp3", is_systolic=True)

            d1, _ = self.missing_policy.clean_blood_pressure(get_val(row, "r1bpdia1", "bpdia1", "dbp1", "dbp_1"), "dbp1", is_systolic=False)
            d2, _ = self.missing_policy.clean_blood_pressure(get_val(row, "r1bpdia2", "bpdia2", "dbp2", "dbp_2"), "dbp2", is_systolic=False)
            d3, _ = self.missing_policy.clean_blood_pressure(get_val(row, "r1bpdia3", "bpdia3", "dbp3", "dbp_3"), "dbp3", is_systolic=False)

            sbp_mean, s_code = self._calculate_average_bp(s1, s2, s3)
            dbp_mean, d_code = self._calculate_average_bp(d1, d2, d3)

            if s_code == "MEAN_2_3" and d_code == "MEAN_2_3":
                derivation_method = "PROTOCOL_MEAN_READINGS_2_AND_3"
            elif s_code == "READING_2_ONLY" or d_code == "READING_2_ONLY":
                derivation_method = "FALLBACK_READING_2_ONLY"
            elif s_code == "READING_3_ONLY" or d_code == "READING_3_ONLY":
                derivation_method = "FALLBACK_READING_3_ONLY"
            elif s_code == "FALLBACK_READING_1" or d_code == "FALLBACK_READING_1":
                derivation_method = "FALLBACK_READING_1_ONLY"
            else:
                derivation_method = "NO_VALID_READING"

            bp_derivation_counts[derivation_method] = bp_derivation_counts.get(derivation_method, 0) + 1

            if sbp_mean is None:
                missingness["sbp_mean"] += 1
            if dbp_mean is None:
                missingness["dbp_mean"] += 1

            if self.strict_protocol_bp:
                is_valid_bp = (derivation_method == "PROTOCOL_MEAN_READINGS_2_AND_3" and sbp_mean is not None and dbp_mean is not None)
            else:
                is_valid_bp = (sbp_mean is not None and dbp_mean is not None)

            # 4. HbA1c
            raw_hba1c, _ = self.missing_policy.clean_hba1c(get_val(row, "r1hba1c", "hba1c", "dbs_hba1c"), "hba1c")
            hba1c_dbs = raw_hba1c
            if hba1c_dbs is None:
                missingness["hba1c"] += 1

            hba1c = hba1c_dbs
            hba1c_venous = PopulationComparabilityLayer.adjust_dbs_hba1c_to_venous(hba1c_dbs, enabled=self.enable_venous_hba1c)
            is_valid_hba1c = (hba1c is not None)

            # 5. Chronic conditions & medications
            htn_diag, _ = self.missing_policy.clean_boolean_indicator(
                get_val(row, "r1hypere", "hypere", "hypertension", "htn"), "hypere", "diagnosed_hypertension"
            )
            if htn_diag is None:
                missingness["diagnosed_hypertension"] += 1

            t2d_diag, _ = self.missing_policy.clean_boolean_indicator(
                get_val(row, "r1diabe", "diabe", "diabetes", "t2d"), "diabe", "diagnosed_diabetes"
            )
            if t2d_diag is None:
                missingness["diagnosed_diabetes"] += 1

            ckd_diag, _ = self.missing_policy.clean_boolean_indicator(
                get_val(row, "r1kidneye", "kidneye", "ckd", "kidney_disease"), "kidneye", "diagnosed_ckd"
            )
            med_bp, _ = self.missing_policy.clean_boolean_indicator(
                get_val(row, "r1med_bp", "r1rx_htn", "med_bp", "taking_bp_meds"), "med_bp", "taking_bp_medication"
            )
            med_diab, _ = self.missing_policy.clean_boolean_indicator(
                get_val(row, "r1med_diab", "r1rx_t2d", "med_diab", "taking_diab_meds"), "med_diab", "taking_diabetes_medication"
            )

            # 6. Complex Survey Design
            raw_wt, has_valid_weight, _ = self.missing_policy.clean_survey_weight(
                get_val(row, "r1wtresp", "weight", "survey_weight", "wtresp"), "survey_weight"
            )
            if not has_valid_weight:
                missingness["survey_weight"] += 1
                survey_weight = 1.0
            else:
                survey_weight = raw_wt

            raw_strata = get_val(row, "r1strata", "strata", "stratum")
            strata_str = str(raw_strata).strip() if raw_strata is not None and str(raw_strata).strip().lower() not in UNIVERSAL_STRING_MISSINGS else None
            if strata_str and strata_str.endswith(".0"):
                strata_str = strata_str[:-2]

            raw_psu = get_val(row, "r1psu", "psu", "cluster")
            psu_str = str(raw_psu).strip() if raw_psu is not None and str(raw_psu).strip().lower() not in UNIVERSAL_STRING_MISSINGS else None
            if psu_str and psu_str.endswith(".0"):
                psu_str = psu_str[:-2]

            # Module participation & measurement indicators
            in_bio = bool(row.get("__in_biomarker_module"))
            bp_part = (s1 is not None or s2 is not None or s3 is not None or d1 is not None or d2 is not None or d3 is not None)
            hba1c_part = (hba1c_dbs is not None)
            bio_part = in_bio or bp_part or hba1c_part
            module_membership = {"individual": True, "biomarker": bio_part}

            rec = LasiCleanedRecord(
                participant_id=surrogate_id,
                household_id=surrogate_hhid,
                age=raw_age,
                gender=gender,
                state=state_str,
                urban_rural=urban_str,
                sbp_reading1=s1,
                sbp_reading2=s2,
                sbp_reading3=s3,
                sbp_mean=sbp_mean,
                dbp_reading1=d1,
                dbp_reading2=d2,
                dbp_reading3=d3,
                dbp_mean=dbp_mean,
                bp_derivation_method=derivation_method,
                hba1c=hba1c,
                hba1c_dbs=hba1c_dbs,
                hba1c_venous=hba1c_venous,
                diagnosed_hypertension=htn_diag,
                diagnosed_diabetes=t2d_diag,
                diagnosed_ckd=ckd_diag,
                taking_bp_medication=med_bp,
                taking_diabetes_medication=med_diab,
                survey_weight=survey_weight,
                strata=strata_str,
                psu=psu_str,
                biomarker_participated=bio_part,
                bp_participated=bp_part,
                hba1c_participated=hba1c_part,
                has_valid_survey_weight=has_valid_weight,
                module_membership=module_membership,
                is_valid_for_bp=is_valid_bp,
                is_valid_for_hba1c=is_valid_hba1c,
            )
            cleaned_records.append(rec)

        valid_records_count = len(cleaned_records)
        if valid_records_count == 0:
            quality_flags.append("NO_VALID_RECORDS_RETAINED")

        ages = [r.age for r in cleaned_records]
        age_summary = {
            "mean": round(sum(ages) / len(ages), 1) if ages else 0.0,
            "min": min(ages) if ages else 0.0,
            "max": max(ages) if ages else 0.0,
        }

        sbps = [r.sbp_mean for r in cleaned_records if r.sbp_mean is not None]
        sbp_summary = {
            "mean": round(sum(sbps) / len(sbps), 1) if sbps else 0.0,
            "min": min(sbps) if sbps else 0.0,
            "max": max(sbps) if sbps else 0.0,
            "valid_count": len(sbps),
        }

        dbps = [r.dbp_mean for r in cleaned_records if r.dbp_mean is not None]
        dbp_summary = {
            "mean": round(sum(dbps) / len(dbps), 1) if dbps else 0.0,
            "min": min(dbps) if dbps else 0.0,
            "max": max(dbps) if dbps else 0.0,
            "valid_count": len(dbps),
        }

        hba1cs = [r.hba1c for r in cleaned_records if r.hba1c is not None]
        hba1c_summary = {
            "mean": round(sum(hba1cs) / len(hba1cs), 2) if hba1cs else 0.0,
            "min": min(hba1cs) if hba1cs else 0.0,
            "max": max(hba1cs) if hba1cs else 0.0,
            "valid_count": len(hba1cs),
        }

        weights_coverage = 100.0 * (1.0 - (missingness["survey_weight"] / max(1, total_rows)))
        weights_list = [r.survey_weight for r in cleaned_records if r.survey_weight is not None]
        n_eff = effective_sample_size(weights_list)
        deff_w = survey_design_effect_weighting(weights_list)

        strata_present = any(r.strata is not None for r in cleaned_records)
        psu_present = any(r.psu is not None for r in cleaned_records)

        if duplicate_count > 0:
            quality_flags.append(f"DUPLICATES_REMOVED: {duplicate_count}")
        if missingness["survey_weight"] > 0:
            quality_flags.append(f"MISSING_SURVEY_WEIGHTS: {missingness['survey_weight']}")
        if bp_derivation_counts.get("FALLBACK_READING_1_ONLY", 0) > 0:
            quality_flags.append(f"BP_FALLBACK_READING_1_USED: {bp_derivation_counts['FALLBACK_READING_1_ONLY']}")

        # Survey Design Diagnostics Engine execution
        diagnostics_engine = LasiSurveyDesignDiagnostics(
            records=cleaned_records,
            source_label=source_file_label,
            join_telemetry=self.join_telemetry,
        )
        self.diagnostics_report = diagnostics_engine.run_diagnostics()

        report = LasiDataQualityReport(
            source_file=source_file_label,
            file_sha256=file_sha256,
            data_source_type=self.data_source_type,
            total_records_ingested=total_rows,
            duplicate_records_detected=duplicate_count,
            valid_records=valid_records_count,
            excluded_records=excluded_count,
            missingness_counts=missingness,
            out_of_range_counts=out_of_range,
            survey_weights_present=(weights_coverage > 50.0),
            survey_weights_coverage_pct=round(weights_coverage, 2),
            effective_sample_size=n_eff,
            design_effect_weighting=deff_w,
            strata_present=strata_present,
            psu_present=psu_present,
            bp_derivation_counts=bp_derivation_counts,
            age_summary=age_summary,
            sbp_summary=sbp_summary,
            dbp_summary=dbp_summary,
            hba1c_summary=hba1c_summary,
            quality_flags=quality_flags,
            survey_design_diagnostics=self.diagnostics_report.model_dump(),
        )

        self.cleaned_records = cleaned_records
        self.quality_report = report

        return cleaned_records, report

    def _generate_manifest(
        self,
        source_files: Dict[str, LasiSourceFileMetadata],
        join_telemetry: Optional[LasiJoinTelemetry],
        row_counts: Dict[str, int],
    ) -> LasiIngestionManifest:
        """Construct the immutable cryptographic audit manifest."""
        now_iso = datetime.now().isoformat()
        primary_hash = self.file_sha256[:8] if self.file_sha256 else "00000000"
        manifest_id = f"lasi-ingest-{now_iso[:10]}-{primary_hash}"

        parser_versions = {
            "pyreadstat": getattr(pyreadstat, "__version__", "unknown"),
            "pandas": getattr(pd, "__version__", "unknown"),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

        schema_mappings = {
            "age": "r1agey / age",
            "gender": "ragender / gender",
            "sbp_reading1": "r1bpsys1 / sbp1",
            "sbp_reading2": "r1bpsys2 / sbp2",
            "sbp_reading3": "r1bpsys3 / sbp3",
            "dbp_reading1": "r1bpdia1 / dbp1",
            "dbp_reading2": "r1bpdia2 / dbp2",
            "dbp_reading3": "r1bpdia3 / dbp3",
            "hba1c": "r1hba1c / hba1c",
            "diagnosed_hypertension": "r1hypere / hypere",
            "diagnosed_diabetes": "r1diabe / diabe",
            "taking_bp_medication": "r1med_bp / r1rx_htn",
            "survey_weight": "r1wtresp / weight",
            "strata": "r1strata / strata",
            "psu": "r1psu / psu",
            "household_id": "household_id / hhid / prim_key",
            "state": "state / r1state",
            "urban_rural": "urban_rural / sector",
        }

        diag_summary = None
        if self.diagnostics_report:
            diag_summary = {
                "total_participants": self.diagnostics_report.total_participants,
                "total_households": self.diagnostics_report.total_households,
                "total_strata": self.diagnostics_report.total_strata,
                "total_psus": self.diagnostics_report.total_psus,
                "singleton_strata_count": self.diagnostics_report.singleton_strata_count,
                "singleton_strata_pct": self.diagnostics_report.singleton_strata_pct,
                "weight_cv": self.diagnostics_report.weight_diagnostics.cv_weight,
                "deff_w": self.diagnostics_report.weight_diagnostics.deff_w,
                "kish_eff_n": self.diagnostics_report.weight_diagnostics.kish_eff_n,
                "biomarker_non_response_pct": self.diagnostics_report.module_participation.get("biomarker_non_response_pct", 0.0),
                "eligible_estimands": [
                    eid for eid, el in self.diagnostics_report.estimand_eligibilities.items() if el.is_eligible
                ],
                "diagnostic_warnings": self.diagnostics_report.diagnostic_warnings,
            }

        missing_value_mappings = {
            "policy": "Preserve explicit NaN/None. Never replace missing measurements with zero or normal values.",
            "variable_specific_provenance": self.missing_policy.get_provenance_report(),
        }

        conversion_options = {
            "strict_protocol_bp": self.strict_protocol_bp,
            "enable_venous_hba1c": self.enable_venous_hba1c,
            "pseudonymization": self.pseudonymizer.get_security_metadata(),
        }

        return LasiIngestionManifest(
            manifest_id=manifest_id,
            manifest_timestamp=now_iso,
            pipeline_version="2.4.0",
            data_source_type=self.data_source_type,
            source_files=source_files,
            join_telemetry=join_telemetry,
            schema_mappings=schema_mappings,
            missing_value_mappings=missing_value_mappings,
            row_counts=row_counts,
            parser_versions=parser_versions,
            conversion_options=conversion_options,
            survey_design_diagnostics_summary=diag_summary,
        )

    def _write_derived_csv(self) -> Path:
        """Export cleaned derived reference dataset with no sensitive identifiers."""
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.derived_dir / "lasi_cleaned_records.csv"

        fieldnames = [
            "participant_id", "household_id", "age", "gender", "state", "urban_rural",
            "sbp_reading1", "sbp_reading2", "sbp_reading3", "sbp_mean",
            "dbp_reading1", "dbp_reading2", "dbp_reading3", "dbp_mean",
            "bp_derivation_method",
            "hba1c", "hba1c_dbs", "hba1c_venous",
            "diagnosed_hypertension", "diagnosed_diabetes", "diagnosed_ckd",
            "taking_bp_medication", "taking_diabetes_medication",
            "survey_weight", "strata", "psu",
            "biomarker_participated", "bp_participated", "hba1c_participated", "has_valid_survey_weight",
            "is_valid_for_bp", "is_valid_for_hba1c",
        ]

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.cleaned_records:
                data = r.model_dump()
                # Remove nested dict or partition metadata for simple flat CSV export
                data.pop("module_membership", None)
                data.pop("partition_label", None)
                writer.writerow(data)

        return out_path

    def _write_manifest(self, manifest: LasiIngestionManifest) -> Path:
        """Export cryptographic ingestion manifest JSON."""
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.derived_dir / "LASI_INGESTION_MANIFEST.json"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        return out_path


class LasiMultiModuleIngestor:
    """Dedicated multi-module ingestion pipeline for joining LASI individual and biomarker files."""

    def __init__(
        self,
        individual_path: Union[str, Path],
        biomarker_path: Union[str, Path],
        derived_dir: Optional[Union[str, Path]] = None,
        data_source_type: LasiDataSourceType = LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
        join_key: str = "respid",
        expected_cardinality: LasiJoinCardinality = LasiJoinCardinality.ONE_TO_ZERO_OR_ONE,
        strict_protocol_bp: bool = False,
        enable_venous_hba1c: bool = False,
        pseudonymization_key: Optional[Union[str, bytes]] = None,
        variable_missing_policy: Optional[VariableMissingValuePolicy] = None,
    ):
        self.individual_path = Path(individual_path)
        self.biomarker_path = Path(biomarker_path)
        self.derived_dir = Path(derived_dir) if derived_dir else self.individual_path.parent / "derived"
        self.data_source_type = data_source_type
        self.join_key = join_key
        self.expected_cardinality = expected_cardinality
        self.strict_protocol_bp = strict_protocol_bp
        self.enable_venous_hba1c = enable_venous_hba1c

        self.underlying_ingestor = LasiDataIngestor(
            derived_dir=self.derived_dir,
            data_source_type=self.data_source_type,
            strict_protocol_bp=self.strict_protocol_bp,
            enable_venous_hba1c=self.enable_venous_hba1c,
            individual_module_path=self.individual_path,
            biomarker_module_path=self.biomarker_path,
            join_key=self.join_key,
            expected_cardinality=self.expected_cardinality,
            pseudonymization_key=pseudonymization_key,
            variable_missing_policy=variable_missing_policy,
        )

    def ingest(self) -> Tuple[List[LasiCleanedRecord], LasiDataQualityReport, LasiIngestionManifest]:
        """Execute multi-module ingestion, join validation, and manifest generation."""
        return self.underlying_ingestor.ingest_modules(
            individual_path=self.individual_path,
            biomarker_path=self.biomarker_path,
            join_key=self.join_key,
            expected_cardinality=self.expected_cardinality,
        )
