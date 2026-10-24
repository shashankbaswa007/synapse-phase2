"""
Complex Survey Design and Missingness Diagnostics Component for LASI Reference Microdata.

Implements Milestone 3 Requirements 3 and 4:
1. Reusable survey-design diagnostics auditing presence and missingness of design fields.
2. Participant, household, stratum, and PSU structural counts and cluster sizes.
3. Stratum-level PSU topology and detection of singleton strata (nh == 1) and low-support strata.
4. Comprehensive weight diagnostics: distribution, dispersion, CV(w), DEFF_w, Kish n_eff,
   and extreme-weight screening (ratios, top-share, trimming recommendations).
5. Variable-specific clinical missingness rates for calibration targets.
6. Module participation, join attrition, and biomarker non-response auditing.
7. Demographic (age-sex) and geographic domain support with sparse-cell flags.
8. Estimand eligibility classification (Observed, Weighted, Adjusted, Unsupported) with
   explicit blocking and ineligibility reasons.
9. Privacy-preserving aggregate reporting: Zero participant-level identifiers exposed.
"""

import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import json

from synapse_simulator.evaluation.lasi.models import (
    LasiCleanedRecord,
    LasiJoinTelemetry,
    LasiEstimandSupportType,
    LasiSurveyDesignFieldStatus,
    LasiStratumPsuTopology,
    LasiWeightDiagnostics,
    LasiDomainSupport,
    LasiEstimandEligibility,
    LasiSurveyDesignDiagnosticsReport,
)
from synapse_simulator.evaluation.metrics import (
    effective_sample_size,
    survey_design_effect_weighting,
)


class LasiSurveyDesignDiagnostics:
    """Audit and diagnostics engine for complex survey design features and missingness."""

    def __init__(
        self,
        records: List[LasiCleanedRecord],
        source_label: str = "LASI Wave 1",
        join_telemetry: Optional[LasiJoinTelemetry] = None,
    ):
        self.records = records
        self.source_label = source_label
        self.join_telemetry = join_telemetry

    def run_diagnostics(self) -> LasiSurveyDesignDiagnosticsReport:
        """Execute full complex survey design and missingness diagnostic audit."""
        total_p = len(self.records)
        now_iso = datetime.now().isoformat()

        # 1. Survey design fields audit
        field_statuses = self._audit_design_fields(total_p)

        # 2. Structural counts & Stratum-PSU Topology
        stratum_topologies, psu_summary, household_count = self._audit_stratum_psu_topology()

        # 3. Sampling weight diagnostics
        weight_diagnostics = self._audit_weights(total_p)

        # 4. Clinical & Demographic Missingness rates
        missingness_rates = self._audit_missingness_rates(total_p)

        # 5. Module participation & Attrition
        module_participation = self._audit_module_participation(total_p)

        # 6. Domain support (Age-Sex and Geographic)
        domain_supports = self._audit_domain_support()

        # 7. Estimand eligibility checks
        estimand_eligibilities = self._audit_estimand_eligibilities(
            total_p=total_p,
            weight_diag=weight_diagnostics,
            domain_supports=domain_supports,
            stratum_topologies=stratum_topologies,
            module_participation=module_participation,
        )

        # 8. Diagnostic Warnings
        warnings = self._generate_diagnostic_warnings(
            field_statuses=field_statuses,
            stratum_topologies=stratum_topologies,
            weight_diag=weight_diagnostics,
            domain_supports=domain_supports,
            estimand_elig=estimand_eligibilities,
            module_part=module_participation,
        )

        singleton_count = sum(1 for s in stratum_topologies if s.is_singleton)
        singleton_pct = round((singleton_count / max(1, len(stratum_topologies))) * 100.0, 2)
        low_support_count = sum(1 for s in stratum_topologies if s.is_low_support)

        return LasiSurveyDesignDiagnosticsReport(
            diagnostics_timestamp=now_iso,
            source_label=self.source_label,
            total_participants=total_p,
            total_households=household_count,
            total_strata=len(stratum_topologies),
            total_psus=psu_summary["total_psus"],
            average_psu_size=psu_summary["average_size"],
            psu_size_min=psu_summary["min_size"],
            psu_size_max=psu_summary["max_size"],
            singleton_strata_count=singleton_count,
            singleton_strata_pct=singleton_pct,
            low_support_strata_count=low_support_count,
            field_statuses=field_statuses,
            weight_diagnostics=weight_diagnostics,
            stratum_topologies=stratum_topologies,
            domain_supports=domain_supports,
            missingness_rates=missingness_rates,
            module_participation=module_participation,
            estimand_eligibilities=estimand_eligibilities,
            diagnostic_warnings=warnings,
        )

    def _audit_design_fields(self, total_p: int) -> Dict[str, LasiSurveyDesignFieldStatus]:
        """Audit presence and missingness of core design fields."""
        fields = {
            "survey_weight": [r.survey_weight for r in self.records],
            "strata": [r.strata for r in self.records],
            "psu": [r.psu for r in self.records],
            "household_id": [r.household_id for r in self.records],
            "state": [r.state for r in self.records],
            "urban_rural": [r.urban_rural for r in self.records],
        }

        statuses = {}
        for fname, vals in fields.items():
            non_null = sum(1 for v in vals if v is not None and str(v).strip() != "")
            if fname == "survey_weight":
                # For weights, must be strictly > 0
                non_null = sum(1 for v in vals if v is not None and isinstance(v, (int, float)) and v > 0.0)

            missing = total_p - non_null
            pct = round((missing / max(1, total_p)) * 100.0, 2)
            present = non_null > 0

            note = ""
            if fname == "survey_weight" and missing > 0:
                note = f"{missing} records missing valid positive sampling weights."
            elif fname in {"strata", "psu"} and not present:
                note = "Field completely missing from ingested dataset; design-based cluster variance cannot be computed."

            statuses[fname] = LasiSurveyDesignFieldStatus(
                field_name=fname,
                present=present,
                source_column=fname,
                total_records=total_p,
                non_null_count=non_null,
                missing_count=missing,
                missingness_pct=pct,
                notes=note,
            )
        return statuses

    def _audit_stratum_psu_topology(self) -> Tuple[List[LasiStratumPsuTopology], Dict[str, Any], Optional[int]]:
        """Audit primary sampling units nested within survey strata."""
        strata_psu_map: Dict[str, Set[str]] = {}
        strata_part_map: Dict[str, int] = {}
        psu_part_counts: Dict[Tuple[str, str], int] = {}
        household_ids = set()

        for r in self.records:
            if r.household_id:
                household_ids.add(r.household_id)

            s_id = r.strata or "UNKNOWN_STRATUM"
            p_id = r.psu or "UNKNOWN_PSU"

            if s_id not in strata_psu_map:
                strata_psu_map[s_id] = set()
                strata_part_map[s_id] = 0

            strata_psu_map[s_id].add(p_id)
            strata_part_map[s_id] += 1

            psu_key = (s_id, p_id)
            psu_part_counts[psu_key] = psu_part_counts.get(psu_key, 0) + 1

        topologies = []
        for s_id in sorted(strata_psu_map.keys()):
            psu_count = len(strata_psu_map[s_id])
            topologies.append(LasiStratumPsuTopology(
                stratum_id=s_id,
                psu_count=psu_count,
                participant_count=strata_part_map[s_id],
                is_singleton=(psu_count == 1),
                is_low_support=(psu_count < 2),
            ))

        psu_sizes = list(psu_part_counts.values()) if psu_part_counts else [0]
        psu_summary = {
            "total_psus": len(psu_part_counts),
            "average_size": round(sum(psu_sizes) / max(1, len(psu_sizes)), 1),
            "min_size": min(psu_sizes) if psu_sizes else 0,
            "max_size": max(psu_sizes) if psu_sizes else 0,
        }

        hh_count = len(household_ids) if household_ids else None
        return topologies, psu_summary, hh_count

    def _audit_weights(self, total_p: int) -> LasiWeightDiagnostics:
        """Compute distribution, dispersion, and extreme-weight screening on sampling weights."""
        valid_weights = [
            float(r.survey_weight) for r in self.records
            if r.survey_weight is not None and float(r.survey_weight) > 0.0 and not math.isnan(float(r.survey_weight))
        ]
        missing_count = total_p - len(valid_weights)

        if not valid_weights:
            return LasiWeightDiagnostics(
                total_weights_observed=0,
                missing_or_invalid_weights_count=missing_count,
                min_weight=0.0,
                max_weight=0.0,
                mean_weight=0.0,
                median_weight=0.0,
                std_weight=0.0,
                cv_weight=0.0,
                deff_w=1.0,
                kish_eff_n=0.0,
                max_to_min_ratio=1.0,
                extreme_weight_count=0,
                extreme_weight_pct=0.0,
                top_1_pct_weight_share=0.0,
                top_5_pct_weight_share=0.0,
                has_extreme_weights=False,
                weight_trimming_recommended=False,
            )

        n_w = len(valid_weights)
        sorted_w = sorted(valid_weights)
        sum_w = sum(sorted_w)

        min_w = sorted_w[0]
        max_w = sorted_w[-1]
        mean_w = sum_w / n_w

        # Quantiles
        median_w = sorted_w[n_w // 2]
        q1_w = sorted_w[int(0.25 * n_w)]
        q3_w = sorted_w[int(0.75 * n_w)]
        iqr_w = q3_w - q1_w

        # Variance and Standard Deviation
        var_w = sum((x - mean_w) ** 2 for x in sorted_w) / max(1, n_w - 1)
        std_w = math.sqrt(var_w)
        cv_w = round(std_w / max(1e-6, mean_w), 3)

        # Kish effective sample size and DEFF_w
        deff_w = round(1.0 + (cv_w ** 2), 3)
        kish_n = effective_sample_size(sorted_w)

        ratio = round(max_w / max(1e-6, min_w), 2)

        # Extreme-weight screening thresholds:
        # Threshold A: 5x median weight
        # Threshold B: Q3 + 3 * IQR
        thresh_extreme = max(5.0 * median_w, q3_w + 3.0 * iqr_w)
        extreme_w = [w for w in sorted_w if w > thresh_extreme]
        extreme_count = len(extreme_w)
        extreme_pct = round((extreme_count / n_w) * 100.0, 2)

        # Top 1% and 5% share
        top_1_idx = int(0.99 * n_w)
        top_5_idx = int(0.95 * n_w)
        top_1_share = round((sum(sorted_w[top_1_idx:]) / max(1e-6, sum_w)) * 100.0, 2)
        top_5_share = round((sum(sorted_w[top_5_idx:]) / max(1e-6, sum_w)) * 100.0, 2)

        has_extreme = (cv_w > 1.5 or ratio > 20.0 or top_1_share > 10.0 or extreme_count > 0)
        trim_recommended = (ratio > 30.0 or cv_w > 1.8 or top_1_share > 15.0)

        return LasiWeightDiagnostics(
            total_weights_observed=n_w,
            missing_or_invalid_weights_count=missing_count,
            min_weight=round(min_w, 4),
            max_weight=round(max_w, 4),
            mean_weight=round(mean_w, 4),
            median_weight=round(median_w, 4),
            std_weight=round(std_w, 4),
            cv_weight=cv_w,
            deff_w=deff_w,
            kish_eff_n=kish_n,
            max_to_min_ratio=ratio,
            extreme_weight_count=extreme_count,
            extreme_weight_pct=extreme_pct,
            top_1_pct_weight_share=top_1_share,
            top_5_pct_weight_share=top_5_share,
            has_extreme_weights=has_extreme,
            weight_trimming_recommended=trim_recommended,
        )

    def _audit_missingness_rates(self, total_p: int) -> Dict[str, float]:
        """Compute item-level missingness rates across all clinical and survey variables."""
        if total_p == 0:
            return {}

        fields = {
            "age": sum(1 for r in self.records if r.age is None),
            "gender": sum(1 for r in self.records if r.gender is None),
            "sbp_mean": sum(1 for r in self.records if r.sbp_mean is None),
            "dbp_mean": sum(1 for r in self.records if r.dbp_mean is None),
            "sbp_reading1": sum(1 for r in self.records if r.sbp_reading1 is None),
            "sbp_reading2": sum(1 for r in self.records if r.sbp_reading2 is None),
            "sbp_reading3": sum(1 for r in self.records if r.sbp_reading3 is None),
            "dbp_reading1": sum(1 for r in self.records if r.dbp_reading1 is None),
            "dbp_reading2": sum(1 for r in self.records if r.dbp_reading2 is None),
            "dbp_reading3": sum(1 for r in self.records if r.dbp_reading3 is None),
            "hba1c": sum(1 for r in self.records if r.hba1c is None),
            "diagnosed_hypertension": sum(1 for r in self.records if r.diagnosed_hypertension is None),
            "diagnosed_diabetes": sum(1 for r in self.records if r.diagnosed_diabetes is None),
            "diagnosed_ckd": sum(1 for r in self.records if r.diagnosed_ckd is None),
            "taking_bp_medication": sum(1 for r in self.records if r.taking_bp_medication is None),
            "taking_diabetes_medication": sum(1 for r in self.records if r.taking_diabetes_medication is None),
            "survey_weight": sum(1 for r in self.records if r.survey_weight is None or r.survey_weight <= 0.0),
            "strata": sum(1 for r in self.records if r.strata is None),
            "psu": sum(1 for r in self.records if r.psu is None),
        }
        return {k: round((cnt / total_p) * 100.0, 2) for k, cnt in fields.items()}

    def _audit_module_participation(self, total_p: int) -> Dict[str, Any]:
        """Analyze multi-module participation, attrition, and biomarker non-response."""
        biomarker_part = sum(1 for r in self.records if r.biomarker_participated or r.is_valid_for_bp or r.is_valid_for_hba1c)
        bp_valid = sum(1 for r in self.records if r.is_valid_for_bp)
        hba1c_valid = sum(1 for r in self.records if r.is_valid_for_hba1c)

        non_resp_count = total_p - biomarker_part
        non_resp_pct = round((non_resp_count / max(1, total_p)) * 100.0, 2)
        bp_missing_pct = round(((total_p - bp_valid) / max(1, total_p)) * 100.0, 2)

        telemetry_info = {}
        if self.join_telemetry:
            telemetry_info = {
                "join_key": self.join_telemetry.join_key,
                "primary_rows": self.join_telemetry.primary_input_rows,
                "secondary_rows": self.join_telemetry.secondary_input_rows,
                "matched_count": self.join_telemetry.matched_key_count,
                "unmatched_primary": self.join_telemetry.unmatched_primary_count,
                "reconciliation_verified": self.join_telemetry.reconciliation_verified,
            }

        return {
            "individual_survey_participants": total_p,
            "biomarker_module_participants": biomarker_part,
            "biomarker_non_response_count": non_resp_count,
            "biomarker_non_response_pct": non_resp_pct,
            "blood_pressure_valid_count": bp_valid,
            "blood_pressure_missingness_pct": bp_missing_pct,
            "hba1c_valid_count": hba1c_valid,
            "join_telemetry": telemetry_info,
        }

    def _audit_domain_support(self) -> Dict[str, LasiDomainSupport]:
        """Compute sample size and effective sample size across demographic and geographic strata."""
        domains: Dict[str, List[LasiCleanedRecord]] = {
            "Male_45_54": [], "Male_55_64": [], "Male_65_74": [], "Male_75_plus": [],
            "Female_45_54": [], "Female_55_64": [], "Female_65_74": [], "Female_75_plus": [],
        }

        for r in self.records:
            if r.age < 45.0:
                continue

            # Age band
            if r.age < 55.0:
                band = "45_54"
            elif r.age < 65.0:
                band = "55_64"
            elif r.age < 75.0:
                band = "65_74"
            else:
                band = "75_plus"

            gender = "Male" if str(r.gender).lower() in {"male", "m"} else "Female"
            key = f"{gender}_{band}"
            if key in domains:
                domains[key].append(r)

            # Urban/Rural domain if present
            if r.urban_rural:
                ur_key = f"Sector_{r.urban_rural.title()}"
                if ur_key not in domains:
                    domains[ur_key] = []
                domains[ur_key].append(r)

        domain_results = {}
        for dname, recs in domains.items():
            n = len(recs)
            weights = [r.survey_weight or 1.0 for r in recs if r.survey_weight and r.survey_weight > 0.0]
            sum_w = sum(weights) if weights else 0.0
            n_eff = effective_sample_size(weights) if weights else 0.0

            domain_results[dname] = LasiDomainSupport(
                domain_name=dname,
                sample_size_n=n,
                weighted_n=round(sum_w, 1),
                effective_n=n_eff,
                is_sparse=(n < 30 or n_eff < 25.0),
                is_severely_sparse=(n < 15),
            )
        return domain_results

    def _audit_estimand_eligibilities(
        self,
        total_p: int,
        weight_diag: LasiWeightDiagnostics,
        domain_supports: Dict[str, LasiDomainSupport],
        stratum_topologies: List[LasiStratumPsuTopology],
        module_participation: Dict[str, Any],
    ) -> Dict[str, LasiEstimandEligibility]:
        """Evaluate whether required data and domain support exist for proposed calibration metrics."""
        has_weights = weight_diag.total_weights_observed > 0 and weight_diag.missing_or_invalid_weights_count < (0.2 * total_p)
        non_resp_pct = module_participation.get("biomarker_non_response_pct", 0.0)
        has_strata = any(s.stratum_id != "UNKNOWN_STRATUM" for s in stratum_topologies)

        candidates = [
            {
                "id": "sbp_mean_overall",
                "name": "Mean Systolic Blood Pressure (Older Adults >= 45)",
                "target": "sbp_mean",
                "req": ["age", "sbp_mean", "survey_weight"],
                "is_biomarker": True,
            },
            {
                "id": "dbp_mean_overall",
                "name": "Mean Diastolic Blood Pressure (Older Adults >= 45)",
                "target": "dbp_mean",
                "req": ["age", "dbp_mean", "survey_weight"],
                "is_biomarker": True,
            },
            {
                "id": "sbp_quantiles_age_sex",
                "name": "SBP Quantiles (25th, 50th, 75th) by Age-Sex Strata",
                "target": "sbp_mean",
                "req": ["age", "gender", "sbp_mean", "survey_weight"],
                "is_biomarker": True,
                "needs_domains": True,
            },
            {
                "id": "hypertension_prevalence",
                "name": "Hypertension Prevalence (Composite: BP >= 140/90 or Rx or Dx)",
                "target": "hypertension_composite",
                "req": ["age", "sbp_mean", "dbp_mean", "diagnosed_hypertension", "taking_bp_medication"],
                "is_biomarker": True,
            },
            {
                "id": "hypertension_awareness",
                "name": "Hypertension Awareness Rate (Self-reported Dx among Hypertensives)",
                "target": "diagnosed_hypertension",
                "req": ["age", "sbp_mean", "dbp_mean", "diagnosed_hypertension"],
                "is_biomarker": True,
            },
            {
                "id": "hypertension_treatment",
                "name": "Hypertension Treatment Rate (Medication among Diagnosed/Hypertensives)",
                "target": "taking_bp_medication",
                "req": ["age", "taking_bp_medication", "diagnosed_hypertension"],
                "is_biomarker": False,
            },
            {
                "id": "hypertension_control",
                "name": "Hypertension Control Rate (BP < 140/90 among Treated)",
                "target": "sbp_mean,dbp_mean",
                "req": ["age", "sbp_mean", "dbp_mean", "taking_bp_medication"],
                "is_biomarker": True,
            },
            {
                "id": "hba1c_mean_overall",
                "name": "Mean HbA1c Laboratory Assay (%)",
                "target": "hba1c",
                "req": ["age", "hba1c", "survey_weight"],
                "is_biomarker": True,
            },
        ]

        results = {}
        for c in candidates:
            eid = c["id"]
            reasons = []
            notes = []

            # Check available valid observations
            if c["is_biomarker"]:
                avail_n = sum(1 for r in self.records if r.age >= 45.0 and (r.is_valid_for_bp if "sbp_mean" in c["target"] or "dbp_mean" in c["target"] else r.is_valid_for_hba1c))
            else:
                avail_n = sum(1 for r in self.records if r.age >= 45.0 and r.diagnosed_hypertension is not None)

            missing_pct = round(100.0 * (total_p - avail_n) / max(1, total_p), 2)
            eff_n = effective_sample_size([r.survey_weight or 1.0 for r in self.records if r.age >= 45.0])

            # Domain checks
            if c.get("needs_domains"):
                severely_sparse = [d for d, s in domain_supports.items() if s.is_severely_sparse and "Sector" not in d]
                if severely_sparse:
                    reasons.append(f"Severely sparse age-sex domains (n < 15): {', '.join(severely_sparse)}.")

            if avail_n < 30:
                reasons.append(f"Inadequate sample size (n = {avail_n} < 30).")

            # Determine Support Type
            if not reasons:
                if has_weights and has_strata:
                    if non_resp_pct > 20.0 and c["is_biomarker"]:
                        support_type = LasiEstimandSupportType.DESIGN_WEIGHTED_OBSERVED
                        notes.append(
                            f"CAUTION: Biomarker non-response is {non_resp_pct}%. Design weights reflect respondent selection, "
                            "but do not automatically eliminate potential non-response bias without an explicit reweighting model."
                        )
                    else:
                        support_type = LasiEstimandSupportType.DESIGN_WEIGHTED_OBSERVED
                        notes.append("Supported with full complex survey design weights.")
                else:
                    support_type = LasiEstimandSupportType.OBSERVED_DATA_UNWEIGHTED
                    notes.append("Calculable only as unweighted observed complete-case sample statistic.")
                is_eligible = True
            else:
                support_type = LasiEstimandSupportType.UNSUPPORTED
                is_eligible = False

            results[eid] = LasiEstimandEligibility(
                estimand_id=eid,
                estimand_name=c["name"],
                target_variable=c["target"],
                required_fields=c["req"],
                support_type=support_type,
                is_eligible=is_eligible,
                missingness_pct=missing_pct,
                sample_size_available=avail_n,
                effective_sample_size=eff_n,
                ineligibility_reasons=reasons,
                methodological_notes=" ".join(notes),
            )

        return results

    def _generate_diagnostic_warnings(
        self,
        field_statuses: Dict[str, LasiSurveyDesignFieldStatus],
        stratum_topologies: List[LasiStratumPsuTopology],
        weight_diag: LasiWeightDiagnostics,
        domain_supports: Dict[str, LasiDomainSupport],
        estimand_elig: Dict[str, LasiEstimandEligibility],
        module_part: Dict[str, Any],
    ) -> List[str]:
        """Aggregate actionable methodological and statistical warnings."""
        warnings = []

        # Survey weights
        if not field_statuses["survey_weight"].present:
            warnings.append("CRITICAL: Survey weights missing. Design-weighted calibration cannot be performed.")
        elif weight_diag.has_extreme_weights:
            warnings.append(
                f"SURVEY WEIGHT DISPERSION: High coefficient of variation CV(w) = {weight_diag.cv_weight} "
                f"(max/min ratio = {weight_diag.max_to_min_ratio}). Kish DEFF_w = {weight_diag.deff_w}."
            )

        # Singletons
        singletons = [s.stratum_id for s in stratum_topologies if s.is_singleton]
        if singletons:
            warnings.append(
                f"SINGLETON PSUs: {len(singletons)} strata contain exactly 1 PSU (e.g. {singletons[:3]}). "
                "Design variance estimation requires explicit singleton handling (certainty, centering, or collapsing)."
            )

        # Non-response
        non_resp_pct = module_part.get("biomarker_non_response_pct", 0.0)
        if non_resp_pct > 15.0:
            warnings.append(
                f"BIOMARKER ATTRITION: {non_resp_pct}% of participants did not participate in physical/biomarker assessment. "
                "Do not assume dropping missing records and reweighting eliminates non-response bias."
            )

        # Sparse domains
        sparse_domains = [d for d, s in domain_supports.items() if s.is_sparse and "Sector" not in d]
        if sparse_domains:
            warnings.append(f"SPARSE DOMAINS: Sample size n < 30 or n_eff < 25 in domains: {', '.join(sparse_domains)}.")

        return warnings

    def export_report_artifacts(self, output_dir: Path) -> Tuple[Path, Path]:
        """Export JSON and Markdown audit reports to derived directory (zero participant-level identifiers)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.run_diagnostics()

        # 1. JSON Export
        json_path = output_dir / "SURVEY_DESIGN_DIAGNOSTICS.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        # 2. Markdown Summary Export
        md_path = output_dir / "SURVEY_DESIGN_DIAGNOSTICS.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._format_markdown_report(report))

        return json_path, md_path

    def _format_markdown_report(self, report: LasiSurveyDesignDiagnosticsReport) -> str:
        """Format a comprehensive, de-identified markdown diagnostic report."""
        lines = [
            f"# LASI Survey Design & Missingness Diagnostics Report",
            f"",
            f"**Source Data Label:** `{report.source_label}`  ",
            f"**Audit Timestamp:** `{report.diagnostics_timestamp}`  ",
            f"**Total Ingested Participants:** {report.total_participants:,}  ",
            f"**Total Survey Strata:** {report.total_strata}  ",
            f"**Total Primary Sampling Units (PSUs):** {report.total_psus}  ",
            f"**Singleton Strata ($n_h = 1$):** {report.singleton_strata_count} ({report.singleton_strata_pct}%)  ",
            f"",
            f"---",
            f"",
            f"## 1. Survey Design Fields & Missingness",
            f"",
            f"| Design Field | Present | Non-Null Count | Missing Count | Missingness % | Audit Note |",
            f"| :--- | :---: | :---: | :---: | :---: | :--- |",
        ]
        for f in report.field_statuses.values():
            lines.append(f"| **`{f.field_name}`** | {'Yes' if f.present else 'No'} | {f.non_null_count:,} | {f.missing_count:,} | {f.missingness_pct}% | {f.notes} |")

        w = report.weight_diagnostics
        lines.extend([
            f"",
            f"---",
            f"",
            f"## 2. Sampling Weight Diagnostics",
            f"",
            f"- **Weights Range:** [{w.min_weight}, {w.max_weight}]",
            f"- **Mean Weight:** {w.mean_weight} (Median: {w.median_weight}, SD: {w.std_weight})",
            f"- **Coefficient of Variation $\\text{{CV}}(w)$:** {w.cv_weight}",
            f"- **Kish Design Effect $\\text{{DEFF}}_w$:** {w.deff_w}",
            f"- **Kish Effective Sample Size $n_{{\\text{{eff}}}}$:** {w.kish_eff_n:,}",
            f"- **Max-to-Min Weight Ratio:** {w.max_to_min_ratio}",
            f"- **Extreme Weights Count:** {w.extreme_weight_count} ({w.extreme_weight_pct}%)",
            f"- **Top 1% Weight Share:** {w.top_1_pct_weight_share}% (Top 5%: {w.top_5_pct_weight_share}%)",
            f"- **Weight Trimming Indicated:** {'Yes (Recommended)' if w.weight_trimming_recommended else 'No'}",
            f"",
            f"---",
            f"",
            f"## 3. Stratum-PSU Topology & Singleton Audit",
            f"",
            f"- **Average PSU Size:** {report.average_psu_size} participants (Range: [{report.psu_size_min}, {report.psu_size_max}])",
            f"- **Singleton Strata Count:** {report.singleton_strata_count} of {report.total_strata} strata have $n_h = 1$.",
            f"- **Methodological Requirement:** Singleton strata require collapsing with adjacent design strata or grand-mean centering before Taylor series variance estimation.",
            f"",
            f"---",
            f"",
            f"## 4. Module Participation & Biomarker Non-Response",
            f"",
        ])
        for k, v in report.module_participation.items():
            if k != "join_telemetry":
                lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 5. Estimand Eligibility Framework",
            f"",
            f"| Estimand ID | Name | Available N | Support Classification | Ineligibility / Methodological Notes |",
            f"| :--- | :--- | :---: | :---: | :--- |",
        ])
        for e in report.estimand_eligibilities.values():
            reasons_str = "; ".join(e.ineligibility_reasons) if e.ineligibility_reasons else e.methodological_notes
            lines.append(f"| **`{e.estimand_id}`** | {e.estimand_name} | {e.sample_size_available:,} | `{e.support_type.value}` | {reasons_str} |")

        if report.diagnostic_warnings:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 6. Actionable Diagnostic Warnings",
                f"",
            ])
            for warn in report.diagnostic_warnings:
                lines.append(f"> [!WARNING]\n> {warn}\n")

        lines.extend([
            f"",
            f"---",
            f"",
            f"*CONFIDENTIALITY ASSURANCE: This report contains strictly aggregate statistical summaries. Zero participant-level identifiers, respondent keys, or protected health information are present in this document.*",
        ])

        return "\n".join(lines)
