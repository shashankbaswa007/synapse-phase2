"""
Three-Tiered Population Validator for SYNAPSE Phase 2.
Implements:
- Tier 1: Structural Integrity (blocks publication)
- Tier 2: Clinical Plausibility (generates warnings)
- Tier 3: Statistical Realism (computes Wilson intervals, JSD, and distinguishes VERIFIED vs UNVERIFIED)
"""

import math
from pathlib import Path
import csv
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from synapse_simulator.population.models import PopulationProfile


def calculate_wilson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% Wilson Score confidence interval for a proportion.
    
    Args:
        k: Number of positive cases.
        n: Total sample size.
        confidence: Confidence level (default 0.95 for z=1.95996).
    
    Returns:
        (lower_bound, upper_bound) in [0.0, 1.0].
    """
    if n <= 0:
        return (0.0, 0.0)

    # Standard normal quantile for confidence level
    # 0.95 -> 1.95996, 0.99 -> 2.57583, 0.90 -> 1.64485
    z_map = {0.90: 1.64485, 0.95: 1.95996, 0.99: 2.57583}
    z = z_map.get(confidence, 1.95996)

    p = k / n
    denominator = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denominator
    spread = (z * math.sqrt((p * (1.0 - p)) / n + (z * z) / (4.0 * n * n))) / denominator

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (round(lower, 4), round(upper, 4))


def calculate_jensen_shannon_divergence(p: List[float], q: List[float]) -> float:
    """Calculate Jensen-Shannon Divergence (base 2) between two probability distributions.
    Bounded in [0.0, 1.0].
    """
    if len(p) != len(q) or len(p) == 0:
        raise ValueError("Distributions must have identical non-zero length")

    # Normalize to ensure valid probability distributions
    sum_p = sum(p) or 1.0
    sum_q = sum(q) or 1.0
    p_norm = [x / sum_p for x in p]
    q_norm = [y / sum_q for y in q]

    # Midpoint distribution M
    m = [0.5 * (p_norm[i] + q_norm[i]) for i in range(len(p))]

    def kl_divergence(a: List[float], b: List[float]) -> float:
        kl = 0.0
        for i in range(len(a)):
            if a[i] > 0.0 and b[i] > 0.0:
                kl += a[i] * math.log2(a[i] / b[i])
        return kl

    jsd = 0.5 * kl_divergence(p_norm, m) + 0.5 * kl_divergence(q_norm, m)
    return max(0.0, min(1.0, round(jsd, 5)))


def calculate_chi_square_stat(observed: List[float], expected: List[float]) -> float:
    """Calculate Chi-square statistic sum((O - E)^2 / E)."""
    chi2 = 0.0
    for o, e in zip(observed, expected):
        if e > 0:
            chi2 += ((o - e) ** 2) / e
    return round(chi2, 4)


class PopulationValidator:
    """Three-tiered validator for generated synthetic datasets."""

    def __init__(self, dataset_dir: Path, population_profile: Optional[PopulationProfile] = None):
        self.dataset_dir = dataset_dir
        self.profile = population_profile

    def _read_csv(self, filename: str) -> List[Dict[str, str]]:
        filepath = self.dataset_dir / filename
        if not filepath.exists():
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def validate_tier1_structural(self) -> Dict[str, Any]:
        """Tier 1: Structural Integrity (BLOCKS PUBLICATION on failure)."""
        errors = []
        patients = self._read_csv("patients.csv")
        encounters = self._read_csv("encounters.csv")
        conditions = self._read_csv("conditions.csv")
        medications = self._read_csv("medications.csv")

        if not patients:
            errors.append("patients.csv is missing or empty")

        patient_ids = {r["patient_id"] for r in patients if "patient_id" in r}
        if len(patient_ids) != len(patients):
            errors.append("Duplicate patient_id found in patients.csv")

        enc_ids = {r["encounter_id"] for r in encounters if "encounter_id" in r}
        for enc in encounters:
            if enc.get("patient_id") not in patient_ids:
                errors.append(f"Encounter {enc.get('encounter_id')} references missing patient {enc.get('patient_id')}")

        cond_ids = {r["condition_id"] for r in conditions if "condition_id" in r}
        for cond in conditions:
            if cond.get("patient_id") not in patient_ids:
                errors.append(f"Condition {cond.get('condition_id')} references missing patient")
            if cond.get("encounter_id") and cond.get("encounter_id") not in enc_ids:
                errors.append(f"Condition {cond.get('condition_id')} references missing encounter {cond.get('encounter_id')}")

        for med in medications:
            if med.get("patient_id") not in patient_ids:
                errors.append(f"Medication {med.get('medication_id')} references missing patient")
            if med.get("condition_id") not in cond_ids:
                errors.append(f"Medication {med.get('medication_id')} references missing condition {med.get('condition_id')}")

        status = "PASS" if not errors else "BLOCK"
        return {
            "tier": 1,
            "tier_name": "Structural Integrity",
            "status": status,
            "blocks_publication": status == "BLOCK",
            "error_count": len(errors),
            "errors": errors,
        }

    def validate_tier2_plausibility(self) -> Dict[str, Any]:
        """Tier 2: Clinical Plausibility (Generates WARNINGS)."""
        warnings = []
        patients = self._read_csv("patients.csv")
        encounters = self._read_csv("encounters.csv")
        deaths = self._read_csv("deaths.csv")
        observations = self._read_csv("observations.csv")

        # 1. Age bounds
        for p in patients:
            try:
                age = int(p.get("age", 0))
                if age < 0 or age > 115:
                    warnings.append(f"Patient {p.get('patient_id')} has implausible age {age}")
            except ValueError:
                warnings.append(f"Patient {p.get('patient_id')} has non-integer age")

        # 2. Deceased patient event temporal check (no post-mortem activity)
        death_map = {}
        for d in deaths:
            try:
                death_map[d["patient_id"]] = datetime.fromisoformat(d["death_date"])
            except Exception:
                pass

        for enc in encounters:
            pid = enc.get("patient_id")
            if pid in death_map:
                try:
                    enc_time = datetime.fromisoformat(enc.get("start_time"))
                    if enc_time > death_map[pid]:
                        warnings.append(f"Post-mortem encounter for patient {pid}: {enc_time} > {death_map[pid]}")
                except Exception:
                    pass

        # 3. Observation value physiological ranges
        for obs in observations:
            code = obs.get("observation_code")
            try:
                val = float(obs.get("value", 0))
                if code == "SBP" and (val < 50.0 or val > 260.0):
                    warnings.append(f"Physiologically implausible SBP: {val} mmHg")
                elif code == "HbA1c" and (val < 3.0 or val > 22.0):
                    warnings.append(f"Physiologically implausible HbA1c: {val}%")
            except ValueError:
                pass

        status = "PASS" if not warnings else "WARNING"
        return {
            "tier": 2,
            "tier_name": "Clinical Plausibility",
            "status": status,
            "blocks_publication": False,
            "warning_count": len(warnings),
            "warnings": warnings[:50],  # cap display
        }

    def validate_tier3_statistical(self) -> Dict[str, Any]:
        """Tier 3: Statistical Realism (Distinguishes VERIFIED vs UNVERIFIED_ESTIMATE)."""
        metrics = []
        patients = self._read_csv("patients.csv")
        conditions = self._read_csv("conditions.csv")
        n_patients = len(patients)

        if n_patients == 0:
            return {"tier": 3, "tier_name": "Statistical Realism", "metrics": []}

        # 1. Sex ratio
        males = sum(1 for p in patients if p.get("gender") == "Male")
        females = n_patients - males
        obs_male_ratio = round(males / n_patients, 4)
        male_ci = calculate_wilson_interval(males, n_patients)

        ref_male_ratio = self.profile.demographics.male_ratio if self.profile else None
        prov_sex = self.profile.demographics.sex_provenance_id if self.profile else None

        # Determine verification status
        if ref_male_ratio is not None and prov_sex and prov_sex in self.profile.provenance_catalog:
            prov_rec = self.profile.provenance_catalog[prov_sex]
            ver_status = "UNVERIFIED_ESTIMATE" if prov_rec.is_assumption else "VERIFIED"
        else:
            ver_status = "UNVERIFIED_ESTIMATE"

        metrics.append({
            "metric_name": "Demographic: Male Sex Proportion",
            "observed_value": obs_male_ratio,
            "reference_value": ref_male_ratio,
            "confidence_interval_95": male_ci,
            "provenance_id": prov_sex,
            "verification_status": ver_status,
        })

        # 2. Age distribution JSD
        if self.profile and len(self.profile.demographics.age_bands) > 0:
            bands = self.profile.demographics.age_bands
            expected_weights = [b.weight for b in bands]
            observed_counts = [0] * len(bands)
            for p in patients:
                age = int(p.get("age", 0))
                for idx, b in enumerate(bands):
                    if b.min_age <= age <= b.max_age:
                        observed_counts[idx] += 1
                        break
            observed_weights = [round(c / n_patients, 4) for c in observed_counts]
            jsd = calculate_jensen_shannon_divergence(observed_weights, expected_weights)
            chi2 = calculate_chi_square_stat(
                [float(c) for c in observed_counts],
                [w * n_patients for w in expected_weights]
            )

            prov_age = self.profile.demographics.age_provenance_id
            prov_rec = self.profile.provenance_catalog.get(prov_age)
            ver_status = "UNVERIFIED_ESTIMATE" if (not prov_rec or prov_rec.is_assumption) else "VERIFIED"

            metrics.append({
                "metric_name": "Demographic: Age Pyramid Jensen-Shannon Divergence",
                "observed_value": jsd,
                "reference_value": 0.0,
                "chi_square_stat": chi2,
                "confidence_interval_95": None,
                "provenance_id": prov_age,
                "verification_status": ver_status,
                "fidelity_interpretation": "HIGH_SIMILARITY" if jsd < 0.05 else "MODERATE_DIVERGENCE",
            })

        # 3. Disease prevalences (Wilson CI)
        cond_codes = {r.get("condition_code") for r in conditions if r.get("condition_code")}
        for code in cond_codes:
            # Count distinct patients diagnosed with this condition
            p_with_cond = {r["patient_id"] for r in conditions if r.get("condition_code") == code}
            k = len(p_with_cond)
            obs_prev = round((k / n_patients) * 100.0, 2)
            ci = calculate_wilson_interval(k, n_patients)
            ci_percent = (round(ci[0] * 100, 2), round(ci[1] * 100, 2))

            ref_prev = None
            prov_id = None
            ver_status = "UNVERIFIED_ESTIMATE"

            if self.profile:
                for p_cfg in self.profile.prevalences:
                    if p_cfg.condition_code == code:
                        ref_prev = p_cfg.prevalence_percent
                        prov_id = p_cfg.provenance_id
                        prov_rec = self.profile.provenance_catalog.get(prov_id)
                        if prov_rec and not prov_rec.is_assumption:
                            ver_status = "VERIFIED"
                        break

            metrics.append({
                "metric_name": f"Prevalence: {code}",
                "observed_value_percent": obs_prev,
                "reference_value_percent": ref_prev,
                "confidence_interval_95": ci_percent,
                "provenance_id": prov_id,
                "verification_status": ver_status,
            })

        return {
            "tier": 3,
            "tier_name": "Statistical Realism",
            "status": "PASS",
            "metrics": metrics,
        }

    def run_full_validation(self) -> Dict[str, Any]:
        """Execute all three validation tiers."""
        t1 = self.validate_tier1_structural()
        t2 = self.validate_tier2_plausibility()
        t3 = self.validate_tier3_statistical()

        overall_status = "FAIL" if t1["status"] == "BLOCK" else "PASS"

        return {
            "overall_status": overall_status,
            "tier1_structural": t1,
            "tier2_plausibility": t2,
            "tier3_statistical": t3,
            "timestamp": datetime.now().isoformat(),
        }
