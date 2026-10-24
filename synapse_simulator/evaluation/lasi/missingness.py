"""
Variable-Specific Missing-Value Policy and Survey Codebook Engine.

Implements Milestone 3 Requirement 2:
1. Replaces blanket universal sentinel replacements with variable-specific policies.
2. Differentiates variables where values like 99 are valid (e.g., Age 99, SBP 99, DBP 99)
   from variables where 99 or 999 are documented missing sentinels.
3. Integrates pyreadstat user-missing ranges and value labels when available from source codebooks.
4. Detects and flags ambiguous mappings for investigator audit rather than guessing.
5. Inviolable safeguards: Never converts missing clinical measurements to zero or normal BP;
   never converts missing diagnoses to False.
"""

import math
from typing import Dict, Any, Optional, Tuple, Set, List
import pandas as pd


# Universal string representations of missingness across Stata/SPSS/ASCII formats
UNIVERSAL_STRING_MISSINGS: Set[str] = {
    "", ".", "na", "nan", "null", "none", "missing", "refused", "dont_know", "don't know",
    ".a", ".b", ".c", ".d", ".e", ".f", ".g", ".h", ".i", ".j", ".k", ".l", ".m",
    ".n", ".o", ".p", ".q", ".r", ".s", ".t", ".u", ".v", ".w", ".x", ".y", ".z",
}


class VariableMissingValuePolicy:
    """Variable-specific missing value evaluation and codebook enforcement."""

    def __init__(
        self,
        custom_codebook: Optional[Dict[str, Dict[str, Any]]] = None,
        source_column_labels: Optional[Dict[str, str]] = None,
        source_value_labels: Optional[Dict[str, Dict[Any, str]]] = None,
        source_missing_ranges: Optional[Dict[str, Any]] = None,
    ):
        """Initialize policy with optional file-level metadata or custom codebook.

        Args:
            custom_codebook: Optional variable-specific overrides.
            source_column_labels: Column labels from pyreadstat metadata.
            source_value_labels: Value labels from pyreadstat metadata.
            source_missing_ranges: Missing ranges from pyreadstat metadata.
        """
        self.custom_codebook = custom_codebook or {}
        self.source_column_labels = source_column_labels or {}
        self.source_value_labels = source_value_labels or {}
        self.source_missing_ranges = source_missing_ranges or {}

        # Audit logs of transformations and ambiguous sentinels
        self.ambiguous_values_encountered: List[Dict[str, Any]] = []
        self.transformation_counts: Dict[str, int] = {}

    def _is_stata_or_universal_string_missing(self, val_str: str) -> bool:
        """Check if string is an explicit missing indicator."""
        return val_str.lower() in UNIVERSAL_STRING_MISSINGS

    def _check_pyreadstat_missing_range(self, var_name: str, numeric_val: float) -> bool:
        """Check if numeric value falls inside user-missing ranges documented in SPSS/Stata metadata."""
        if not self.source_missing_ranges or var_name not in self.source_missing_ranges:
            return False
        ranges = self.source_missing_ranges[var_name]
        for r in ranges:
            # pyreadstat format: dict with 'lo', 'hi', or individual value
            if isinstance(r, dict):
                lo = r.get("lo", float("-inf"))
                hi = r.get("hi", float("inf"))
                if lo <= numeric_val <= hi:
                    return True
            elif isinstance(r, (int, float)):
                if abs(numeric_val - r) < 1e-6:
                    return True
        return False

    def clean_age(self, value: Any, raw_col_name: str = "age") -> Tuple[Optional[float], Optional[str]]:
        """Clean age variable.

        Note: Age 98 or 99 is a completely VALID older-adult age in LASI (ages 45-100+).
        Sentinels for age are strictly negative values (-999, -998, -99) or extreme codes (999, 9999).
        """
        if value is None or pd.isna(value):
            return None, "NULL_VALUE"

        val_str = str(value).strip()
        if self._is_stata_or_universal_string_missing(val_str):
            return None, f"STRING_SENTINEL:{val_str}"

        try:
            val_float = float(val_str)
        except (ValueError, TypeError):
            return None, f"NON_NUMERIC:{val_str}"

        if math.isnan(val_float) or math.isinf(val_float):
            return None, "NAN_OR_INF"

        # Check file codebook metadata if present
        if self._check_pyreadstat_missing_range(raw_col_name, val_float):
            return None, f"CODEBOOK_USER_MISSING:{val_float}"

        # Age-specific sentinels: -999, -998, -997, -99, 999, 9999
        if val_float in {-999, -998, -997, -99, 999, 9999}:
            return None, f"DOCUMENTED_AGE_SENTINEL:{val_float}"

        # Plausible older-adult range verification
        if val_float < 18.0 or val_float > 120.0:
            self.ambiguous_values_encountered.append({
                "variable": "age",
                "raw_column": raw_col_name,
                "value": val_float,
                "reason": "PHYSIOLOGICALLY_IMPLAUSIBLE_AGE",
            })
            return None, f"OUT_OF_RANGE:{val_float}"

        return round(val_float, 1), None

    def clean_blood_pressure(
        self,
        value: Any,
        raw_col_name: str,
        is_systolic: bool,
    ) -> Tuple[Optional[float], Optional[str]]:
        """Clean blood pressure measurement (SBP or DBP).

        CRITICAL CLINICAL SAFEGUARDS:
        1. A reading of 99.0 mmHg is a completely valid clinical reading (normal DBP or low SBP).
           It must NEVER be discarded as a missing sentinel!
        2. Negative values (-999, -998, -997, -99) are explicit refusal/unassessable sentinels.
        3. Values > 300 mmHg (e.g. 999, 9999) are sensor error / missing codes.
        4. NEVER coerce missing readings to 0.0, 120.0, 80.0, or population medians.
        """
        if value is None or pd.isna(value):
            return None, "NULL_VALUE"

        val_str = str(value).strip()
        if self._is_stata_or_universal_string_missing(val_str):
            return None, f"STRING_SENTINEL:{val_str}"

        try:
            val_float = float(val_str)
        except (ValueError, TypeError):
            return None, f"NON_NUMERIC:{val_str}"

        if math.isnan(val_float) or math.isinf(val_float):
            return None, "NAN_OR_INF"

        if self._check_pyreadstat_missing_range(raw_col_name, val_float):
            return None, f"CODEBOOK_USER_MISSING:{val_float}"

        # Explicit negative sentinels in health surveys
        if val_float in {-999, -998, -997, -99, -9}:
            return None, f"NEGATIVE_BP_SENTINEL:{val_float}"

        # Extreme sentinel codes (999, 9999)
        if val_float in {999, 9999}:
            return None, f"HIGH_BP_SENTINEL:{val_float}"

        # Physiological range checks
        min_p = 60.0 if is_systolic else 40.0
        max_p = 280.0 if is_systolic else 160.0

        if val_float < min_p or val_float > max_p:
            self.ambiguous_values_encountered.append({
                "variable": "sbp" if is_systolic else "dbp",
                "raw_column": raw_col_name,
                "value": val_float,
                "reason": f"BP_OUT_OF_PHYSIOLOGICAL_RANGE_[{min_p},{max_p}]",
            })
            return None, f"OUT_OF_PHYSIOLOGICAL_RANGE:{val_float}"

        return round(val_float, 1), None

    def clean_hba1c(self, value: Any, raw_col_name: str = "hba1c") -> Tuple[Optional[float], Optional[str]]:
        """Clean HbA1c assay measurement (%).

        Plausible physiological range: [3.5%, 20.0%].
        Sentinels: negative values (-999, -998, -99) or > 30 (99, 999).
        """
        if value is None or pd.isna(value):
            return None, "NULL_VALUE"

        val_str = str(value).strip()
        if self._is_stata_or_universal_string_missing(val_str):
            return None, f"STRING_SENTINEL:{val_str}"

        try:
            val_float = float(val_str)
        except (ValueError, TypeError):
            return None, f"NON_NUMERIC:{val_str}"

        if math.isnan(val_float) or math.isinf(val_float):
            return None, "NAN_OR_INF"

        if self._check_pyreadstat_missing_range(raw_col_name, val_float):
            return None, f"CODEBOOK_USER_MISSING:{val_float}"

        if val_float in {-999, -998, -997, -99, 99, 999, 9999}:
            return None, f"HBA1C_SENTINEL:{val_float}"

        if val_float < 3.5 or val_float > 20.0:
            self.ambiguous_values_encountered.append({
                "variable": "hba1c",
                "raw_column": raw_col_name,
                "value": val_float,
                "reason": "HBA1C_OUT_OF_PHYSIOLOGICAL_RANGE_[3.5,20.0]",
            })
            return None, f"OUT_OF_PHYSIOLOGICAL_RANGE:{val_float}"

        return round(val_float, 2), None

    def clean_boolean_indicator(
        self,
        value: Any,
        raw_col_name: str,
        variable_name: str,
    ) -> Tuple[Optional[bool], Optional[str]]:
        """Clean categorical survey indicators (e.g. self-reported physician diagnosis, medication).

        Survey conventions:
        - Yes: 1, 1.0, "yes", "true"
        - No: 0, 0.0, 2, 2.0, "no", "false" (SPSS/Stata often use 1=Yes, 2=No)
        - Missing / Unknown / Refused: 8 (Refused), 9 (Don't know), 98, 99, -999, -998, -99

        INVIOLABLE RULE: Missing is NEVER coerced to False!
        """
        if value is None or pd.isna(value):
            return None, "NULL_VALUE"

        val_str = str(value).strip().lower()
        if self._is_stata_or_universal_string_missing(val_str):
            return None, f"STRING_SENTINEL:{val_str}"

        if self._check_pyreadstat_missing_range(raw_col_name, float(val_str) if val_str.replace(".", "", 1).isdigit() else 0.0):
            return None, "CODEBOOK_USER_MISSING"

        # Explicit Positive
        if val_str in {"1", "1.0", "true", "yes", "y"}:
            return True, None

        # Explicit Negative
        if val_str in {"0", "0.0", "2", "2.0", "false", "no", "n"}:
            return False, None

        # Documented Survey Sentinels for "Don't know" or "Refused"
        if val_str in {"8", "8.0", "9", "9.0", "98", "98.0", "99", "99.0", "-999", "-998", "-99", "-9"}:
            return None, f"SURVEY_NON_RESPONSE_CODE:{val_str}"

        # Ambiguous code
        self.ambiguous_values_encountered.append({
            "variable": variable_name,
            "raw_column": raw_col_name,
            "value": val_str,
            "reason": f"UNMAPPED_BOOLEAN_CODE_{val_str}",
        })
        return None, f"AMBIGUOUS_CODE:{val_str}"

    def clean_survey_weight(
        self,
        value: Any,
        raw_col_name: str = "survey_weight",
    ) -> Tuple[Optional[float], bool, Optional[str]]:
        """Clean complex survey sampling weights.

        Returns:
            (weight_val, is_valid, note)
            Where weight_val is float or None.
            is_valid is strictly True ONLY if weight > 0.0 and finite.
        """
        if value is None or pd.isna(value):
            return None, False, "NULL_WEIGHT"

        val_str = str(value).strip()
        if self._is_stata_or_universal_string_missing(val_str):
            return None, False, f"STRING_SENTINEL:{val_str}"

        try:
            w_float = float(val_str)
        except (ValueError, TypeError):
            return None, False, f"NON_NUMERIC_WEIGHT:{val_str}"

        if math.isnan(w_float) or math.isinf(w_float):
            return None, False, "NAN_OR_INF_WEIGHT"

        if w_float <= 0.0:
            return None, False, f"NON_POSITIVE_WEIGHT:{w_float}"

        if w_float in {999, 9999, -999, -998, -99}:
            return None, False, f"WEIGHT_SENTINEL:{w_float}"

        return w_float, True, None

    def get_provenance_report(self) -> Dict[str, Any]:
        """Return summary of missingness policies and any flagged ambiguous mappings."""
        return {
            "policy_type": "VARIABLE_SPECIFIC_CODEBOOK_DRIVEN",
            "ambiguous_values_count": len(self.ambiguous_values_encountered),
            "ambiguous_values_summary": self.ambiguous_values_encountered[:20],  # Head 20
            "safeguards_enforced": [
                "Blood pressure 99 mmHg preserved as valid physiological reading",
                "Age 98/99 preserved as valid older adult age",
                "Missing clinical vitals never coerced to zero or normal values",
                "Missing diagnoses never coerced to False",
                "Missing weights flagged explicitly and excluded from weighted estimates",
            ],
        }
