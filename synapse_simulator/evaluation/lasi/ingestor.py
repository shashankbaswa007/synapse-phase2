"""
LASI Wave 1 Data Ingestor and Quality Auditor.

Implements:
1. Multi-format tabular loading (CSV/TSV)
2. Participant pseudonymization / de-identification
3. Variable normalization (units, missing sentinels, categorical encodings)
4. Range validation and outlier detection
5. Protocol-compliant blood pressure averaging (2nd & 3rd reading average, with explicit fallback auditing)
6. Complex survey design extraction (weights, strata, PSU, Kish effective sample size)
7. Audit report generation (missingness, bounds, exclusions, BP derivation breakdown)
8. Export of cleaned derived evaluation tables
"""

import csv
import hashlib
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

from synapse_simulator.evaluation.metrics import (
    effective_sample_size,
    survey_design_effect_weighting,
)
from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiDataQualityReport,
    LasiDataSourceType,
)
from synapse_simulator.evaluation.lasi.comparability import (
    PopulationComparabilityLayer,
)


# Known missing value sentinel representations in LASI / survey microdata
NUMERIC_MISSING_CODES = {-999, -998, -997, -99, 9999, 999, 999.0, 9999.0}
STRING_MISSING_VALUES = {"", ".", "na", "nan", "null", "none", "-999", "-998", "-997", "-99", "999", "9999"}

# Plausible physiological validation ranges
MIN_AGE, MAX_AGE = 18.0, 120.0
MIN_SBP, MAX_SBP = 60.0, 280.0
MIN_DBP, MAX_DBP = 40.0, 160.0
MIN_HBA1C, MAX_HBA1C = 3.5, 20.0


class LasiDataIngestor:
    """Loads, cleans, validates, and summarizes LASI Wave 1 reference microdata."""

    def __init__(
        self,
        source_path: Union[str, Path],
        derived_dir: Optional[Union[str, Path]] = None,
        data_source_type: LasiDataSourceType = LasiDataSourceType.SYNTHETIC_TEST_FIXTURE,
        strict_protocol_bp: bool = False,
        enable_venous_hba1c: bool = False,
    ):
        self.source_path = Path(source_path)
        self.derived_dir = Path(derived_dir) if derived_dir else self.source_path.parent / "derived"
        self.data_source_type = data_source_type
        self.strict_protocol_bp = strict_protocol_bp
        self.enable_venous_hba1c = enable_venous_hba1c
        
        self.file_sha256 = ""
        self.cleaned_records: List[LasiCleanedRecord] = []
        self.quality_report: Optional[LasiDataQualityReport] = None

    def calculate_file_sha256(self) -> str:
        """Compute SHA-256 hash of the raw input file for provenance tracking."""
        if not self.source_path.exists():
            return ""
        hasher = hashlib.sha256()
        with open(self.source_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _parse_float(self, value: Any) -> Optional[float]:
        """Safely parse float, mapping known survey missing codes to None."""
        if value is None:
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
        if value is None:
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
        - Primary measurement is the mean of reading 2 and reading 3.
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
        """Ingest raw LASI dataset, validate records, and compile quality report."""
        if not self.source_path.exists():
            raise FileNotFoundError(f"LASI reference file not found: {self.source_path}")

        self.file_sha256 = self.calculate_file_sha256()

        # Detect delimiter
        with open(self.source_path, "r", encoding="utf-8-sig", errors="replace") as f:
            first_line = f.readline()
            delimiter = "\t" if "\t" in first_line and "," not in first_line else ","

        seen_ids = set()
        duplicate_count = 0
        total_rows = 0
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

        with open(self.source_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if not reader.fieldnames:
                raise ValueError("LASI source file contains no headers or is empty.")

            # Map field names flexibly to accommodate different export dialects
            fn_lower = {fn.strip().lower(): fn for fn in reader.fieldnames}

            def get_val(row: Dict[str, str], *aliases: str) -> Optional[str]:
                for alias in aliases:
                    if alias.lower() in fn_lower:
                        return row[fn_lower[alias.lower()]]
                return None

            for row_idx, row in enumerate(reader, start=1):
                total_rows += 1

                # 1. Identifier extraction & pseudonymization
                raw_id = get_val(
                    row, "participant_id", "prim_key", "individual_id", "household_id",
                    "respid", "r1id", "subjid", "id"
                )
                if not raw_id:
                    surrogate_id = f"lasi_syn_p_{row_idx:06d}"
                else:
                    # Pseudonymize using truncated SHA-256 digest
                    surrogate_id = f"lasi_p_{hashlib.sha256(raw_id.strip().encode('utf-8')).hexdigest()[:12]}"

                if surrogate_id in seen_ids:
                    duplicate_count += 1
                    continue
                seen_ids.add(surrogate_id)

                # 2. Demographics
                raw_age = self._parse_float(get_val(row, "r1agey", "age", "age_years", "age_yrs"))
                if raw_age is None:
                    missingness["age"] += 1
                    excluded_count += 1
                    continue
                if raw_age < MIN_AGE or raw_age > MAX_AGE:
                    out_of_range["age"] += 1
                    excluded_count += 1
                    continue

                raw_gender = get_val(row, "ragender", "gender", "sex")
                if not raw_gender or str(raw_gender).strip().lower() in STRING_MISSING_VALUES:
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

                # 3. Blood pressure readings
                s1 = self._parse_float(get_val(row, "r1bpsys1", "bpsys1", "sbp1", "sbp_1"))
                s2 = self._parse_float(get_val(row, "r1bpsys2", "bpsys2", "sbp2", "sbp_2"))
                s3 = self._parse_float(get_val(row, "r1bpsys3", "bpsys3", "sbp3", "sbp_3"))
                
                d1 = self._parse_float(get_val(row, "r1bpdia1", "bpdia1", "dbp1", "dbp_1"))
                d2 = self._parse_float(get_val(row, "r1bpdia2", "bpdia2", "dbp2", "dbp_2"))
                d3 = self._parse_float(get_val(row, "r1bpdia3", "bpdia3", "dbp3", "dbp_3"))

                # Validate ranges for individual readings
                def check_bp_range(val: Optional[float], min_v: float, max_v: float, err_key: str) -> Optional[float]:
                    if val is None:
                        return None
                    if val < min_v or val > max_v:
                        out_of_range[err_key] += 1
                        return None
                    return val

                s1 = check_bp_range(s1, MIN_SBP, MAX_SBP, "sbp")
                s2 = check_bp_range(s2, MIN_SBP, MAX_SBP, "sbp")
                s3 = check_bp_range(s3, MIN_SBP, MAX_SBP, "sbp")
                d1 = check_bp_range(d1, MIN_DBP, MAX_DBP, "dbp")
                d2 = check_bp_range(d2, MIN_DBP, MAX_DBP, "dbp")
                d3 = check_bp_range(d3, MIN_DBP, MAX_DBP, "dbp")

                # Protocol blood pressure mean calculation
                sbp_mean, s_code = self._calculate_average_bp(s1, s2, s3)
                dbp_mean, d_code = self._calculate_average_bp(d1, d2, d3)

                # Determine overall derivation method
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
                raw_hba1c = self._parse_float(get_val(row, "r1hba1c", "hba1c", "dbs_hba1c"))
                if raw_hba1c is not None:
                    if raw_hba1c < MIN_HBA1C or raw_hba1c > MAX_HBA1C:
                        out_of_range["hba1c"] += 1
                        hba1c_dbs = None
                    else:
                        hba1c_dbs = round(raw_hba1c, 2)
                else:
                    missingness["hba1c"] += 1
                    hba1c_dbs = None
                
                # Preserved authentic DBS measurement
                hba1c = hba1c_dbs
                hba1c_venous = PopulationComparabilityLayer.adjust_dbs_hba1c_to_venous(hba1c_dbs, enabled=self.enable_venous_hba1c)
                is_valid_hba1c = (hba1c is not None)

                # 5. Self-reported conditions & medications
                htn_diag = self._parse_bool(get_val(row, "r1hypere", "hypere", "hypertension", "htn"))
                if htn_diag is None:
                    missingness["diagnosed_hypertension"] += 1

                t2d_diag = self._parse_bool(get_val(row, "r1diabe", "diabe", "diabetes", "t2d"))
                if t2d_diag is None:
                    missingness["diagnosed_diabetes"] += 1

                ckd_diag = self._parse_bool(get_val(row, "r1kidneye", "kidneye", "ckd", "kidney_disease"))

                med_bp = self._parse_bool(get_val(row, "r1med_bp", "r1rx_htn", "med_bp", "taking_bp_meds"))
                med_diab = self._parse_bool(get_val(row, "r1med_diab", "r1rx_t2d", "med_diab", "taking_diab_meds"))

                # 6. Complex Survey Design
                raw_wt = self._parse_float(get_val(row, "r1wtresp", "weight", "survey_weight", "wtresp"))
                if raw_wt is None or raw_wt <= 0.0 or math.isnan(raw_wt):
                    missingness["survey_weight"] += 1
                    survey_weight = 1.0
                else:
                    survey_weight = raw_wt

                strata = get_val(row, "r1strata", "strata", "stratum")
                psu = get_val(row, "r1psu", "psu", "cluster")

                rec = LasiCleanedRecord(
                    participant_id=surrogate_id,
                    age=raw_age,
                    gender=gender,
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
                    strata=strata.strip() if strata else None,
                    psu=psu.strip() if psu else None,
                    is_valid_for_bp=is_valid_bp,
                    is_valid_for_hba1c=is_valid_hba1c,
                )
                cleaned_records.append(rec)

        # Quality summaries
        valid_records_count = len(cleaned_records)
        if valid_records_count == 0:
            quality_flags.append("NO_VALID_RECORDS_RETAINED")

        # Age stats
        ages = [r.age for r in cleaned_records]
        age_summary = {
            "mean": round(sum(ages) / len(ages), 1) if ages else 0.0,
            "min": min(ages) if ages else 0.0,
            "max": max(ages) if ages else 0.0,
        }

        # SBP stats
        sbps = [r.sbp_mean for r in cleaned_records if r.sbp_mean is not None]
        sbp_summary = {
            "mean": round(sum(sbps) / len(sbps), 1) if sbps else 0.0,
            "min": min(sbps) if sbps else 0.0,
            "max": max(sbps) if sbps else 0.0,
            "valid_count": len(sbps),
        }

        # DBP stats
        dbps = [r.dbp_mean for r in cleaned_records if r.dbp_mean is not None]
        dbp_summary = {
            "mean": round(sum(dbps) / len(dbps), 1) if dbps else 0.0,
            "min": min(dbps) if dbps else 0.0,
            "max": max(dbps) if dbps else 0.0,
            "valid_count": len(dbps),
        }

        # HbA1c stats
        hba1cs = [r.hba1c for r in cleaned_records if r.hba1c is not None]
        hba1c_summary = {
            "mean": round(sum(hba1cs) / len(hba1cs), 2) if hba1cs else 0.0,
            "min": min(hba1cs) if hba1cs else 0.0,
            "max": max(hba1cs) if hba1cs else 0.0,
            "valid_count": len(hba1cs),
        }

        # Survey weights & effective sample size
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

        report = LasiDataQualityReport(
            source_file=str(self.source_path),
            file_sha256=self.file_sha256,
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
        )

        self.cleaned_records = cleaned_records
        self.quality_report = report

        # Write cleaned derived file if requested
        if self.derived_dir:
            self._write_derived_csv()

        return cleaned_records, report

    def _write_derived_csv(self) -> Path:
        """Export cleaned derived reference dataset with no sensitive identifiers."""
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.derived_dir / "lasi_cleaned_records.csv"

        fieldnames = [
            "participant_id", "age", "gender",
            "sbp_reading1", "sbp_reading2", "sbp_reading3", "sbp_mean",
            "dbp_reading1", "dbp_reading2", "dbp_reading3", "dbp_mean",
            "bp_derivation_method",
            "hba1c", "hba1c_dbs", "hba1c_venous",
            "diagnosed_hypertension", "diagnosed_diabetes", "diagnosed_ckd",
            "taking_bp_medication", "taking_diabetes_medication",
            "survey_weight", "strata", "psu",
            "is_valid_for_bp", "is_valid_for_hba1c",
        ]

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.cleaned_records:
                writer.writerow(r.model_dump())

        return out_path
