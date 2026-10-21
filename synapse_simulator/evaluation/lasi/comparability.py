"""
LASI Population Comparability and Direct Standardization Layer.

Defines:
1. Two distinct evaluation target populations:
   - Population A: General Adults (Age >= 20)
   - Population B: Older Adults (Age >= 45, LASI-aligned)
2. Direct age- and sex-standardization using Census SRS standard weights across 8 strata
3. Measurement protocol harmonization audit (DBS vs venous HbA1c; survey BP vs clinical vitals)
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
from pydantic import BaseModel, Field

from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiComparisonPopulation,
)

# Census of India SRS standard age-sex weights for older adults (Age >= 45)
# Exactly 8 mutually exclusive strata encompassing 45-54, 55-64, 65-74, and 75+
# Sum of weights = 1.000
CENSUS_SRS_OLDER_ADULT_WEIGHTS = {
    ("45-54", "Male"): 0.231,
    ("45-54", "Female"): 0.222,
    ("55-64", "Male"): 0.154,
    ("55-64", "Female"): 0.149,
    ("65-74", "Male"): 0.078,
    ("65-74", "Female"): 0.076,
    ("75+", "Male"): 0.043,
    ("75+", "Female"): 0.047,
}


def get_age_band_older_adult(age: float) -> str:
    """Categorize age into older adult strata."""
    if age < 45.0:
        return "<45"
    elif age < 55.0:
        return "45-54"
    elif age < 65.0:
        return "55-64"
    elif age < 75.0:
        return "65-74"
    else:
        return "75+"


class PopulationComparabilityLayer:
    """Harmonizes synthetic and reference cohorts into strictly comparable subsets."""

    @staticmethod
    def filter_population_a(records: List[Any], age_extractor: Callable[[Any], float]) -> List[Any]:
        """Filter to Population A: General Adults (Age >= 20).
        
        Note: LASI Wave 1 reference data recruited adults aged >= 45 and resident spouses.
        Directly comparing Population A to LASI without age standardization is methodologically invalid.
        """
        return [r for r in records if age_extractor(r) >= 20.0]

    @staticmethod
    def filter_population_b(records: List[Any], age_extractor: Callable[[Any], float]) -> List[Any]:
        """Filter to Population B: Older Adults (Age >= 45).
        
        Strictly aligned with the LASI Wave 1 core recruitment eligibility.
        """
        return [r for r in records if age_extractor(r) >= 45.0]

    @staticmethod
    def direct_standardize_mean(
        records: List[Any],
        value_extractor: Callable[[Any], Optional[float]],
        age_extractor: Callable[[Any], float],
        gender_extractor: Callable[[Any], str],
        standard_weights: Optional[Dict[Tuple[str, str], float]] = None,
        min_populated_strata: int = 4,
    ) -> Tuple[Optional[float], Optional[float], Dict[str, Any]]:
        """Calculate both unstandardized and directly standardized mean estimates.
        
        Standardized estimate:
            Y_std = sum_s (w_s * y_s) / sum_s w_s
        
        Handles empty strata:
            - Unobserved strata are documented.
            - Remaining observed strata weights are proportionally re-normalized.
            - If fewer than min_populated_strata (default 4 of 8) are populated,
              standardization is aborted and returns None.

        Returns:
            (unstandardized_mean, standardized_mean, strata_details)
        """
        weights = standard_weights or CENSUS_SRS_OLDER_ADULT_WEIGHTS
        valid_items = [
            (age_extractor(r), gender_extractor(r), value_extractor(r))
            for r in records
            if value_extractor(r) is not None
        ]
        
        if not valid_items:
            return None, None, {"error": "NO_VALID_DATA", "total_records": 0}

        # Unstandardized mean
        vals = [item[2] for item in valid_items if item[2] is not None]
        unstd_mean = sum(vals) / len(vals)

        # Stratified values
        strata_obs: Dict[Tuple[str, str], List[float]] = {}
        for age, gender, val in valid_items:
            if val is None:
                continue
            band = get_age_band_older_adult(age)
            if band == "<45":
                continue  # Exclude <45 from older adult standard weights
            g_norm = "Male" if str(gender).lower().startswith("m") else "Female"
            key = (band, g_norm)
            strata_obs.setdefault(key, []).append(val)

        # Count populated strata
        populated_count = sum(1 for key in weights if key in strata_obs and len(strata_obs[key]) > 0)
        
        strata_report: Dict[str, Any] = {
            "total_strata": len(weights),
            "populated_strata_count": populated_count,
            "empty_strata": [],
            "strata_breakdown": {},
        }

        if populated_count < min_populated_strata:
            strata_report["error"] = f"INSUFFICIENT_STRATA_POPULATED: {populated_count} < {min_populated_strata}"
            return round(unstd_mean, 3), None, strata_report

        # Compute weighted sum
        weighted_sum = 0.0
        used_weight_sum = 0.0

        for key, w in weights.items():
            strata_label = f"{key[0]}_{key[1]}"
            if key in strata_obs and len(strata_obs[key]) > 0:
                s_mean = sum(strata_obs[key]) / len(strata_obs[key])
                weighted_sum += w * s_mean
                used_weight_sum += w
                strata_report["strata_breakdown"][strata_label] = {
                    "count": len(strata_obs[key]),
                    "stratum_mean": round(s_mean, 3),
                    "original_weight": w,
                    "is_empty": False,
                }
            else:
                strata_report["empty_strata"].append(strata_label)
                strata_report["strata_breakdown"][strata_label] = {
                    "count": 0,
                    "stratum_mean": None,
                    "original_weight": w,
                    "is_empty": True,
                }

        strata_report["used_weight_mass"] = round(used_weight_sum, 4)
        strata_report["missing_weight_mass"] = round(1.0 - used_weight_sum, 4)

        if used_weight_sum > 0.0:
            std_mean = weighted_sum / used_weight_sum
        else:
            std_mean = unstd_mean

        return round(unstd_mean, 3), round(std_mean, 3), strata_report

    @staticmethod
    def adjust_dbs_hba1c_to_venous(
        hba1c_dbs: Optional[float],
        enabled: bool = False,
    ) -> Optional[float]:
        """Convert Dried Blood Spot (DBS) HbA1c to centralized venous HPLC equivalent.
        
        CRITICAL AUDIT NOTE:
        This linear transformation (HbA1c_venous = 0.94 * DBS + 0.45) originated from the
        US Health and Retirement Study (HRS) biomarker validation in a North American cohort.
        Official LASI Wave 1 documentation (IIPS, 2020) does NOT endorse an uncalibrated
        linear transformation to clinical venous HPLC for Indian DBS specimens.
        
        Therefore, this transformation is DISABLED BY DEFAULT (enabled=False).
        When disabled, this function returns None to indicate that direct venous equivalence
        is unverified.
        
        If explicitly enabled (enabled=True), the function computes the estimate with
        acknowledged prediction uncertainty (SE ~ 0.40% HbA1c).
        """
        if hba1c_dbs is None:
            return None
        if not enabled:
            return None
        return round(0.94 * hba1c_dbs + 0.45, 2)
