"""
Reporting Layer for SYNAPSE Phase 2 Evaluation.
Formats EvaluationReport into machine-readable JSON and human-readable Markdown.
"""

import json
from pathlib import Path
from typing import Dict, Any

from synapse_simulator.evaluation.evaluator import EvaluationReport, MetricStatus


class EvaluationReportFormatter:
    """Formats and exports EvaluationReport to JSON and Markdown artifacts."""

    @staticmethod
    def to_json(report: EvaluationReport, indent: int = 2) -> str:
        """Serialize EvaluationReport to formatted JSON."""
        return report.model_dump_json(indent=indent)

    @staticmethod
    def save_json(report: EvaluationReport, output_path: Path) -> Path:
        """Write JSON report to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(EvaluationReportFormatter.to_json(report))
        return output_path

    @staticmethod
    def to_markdown(report: EvaluationReport) -> str:
        """Format human-readable comprehensive Markdown evaluation report."""
        lines = [
            "# SYNAPSE Phase 2 — Comprehensive Synthetic Data Evaluation Report",
            "",
            f"**Evaluation Timestamp:** `{report.timestamp}`  ",
            f"**Dataset Directory:** `{report.dataset_directory}`  ",
            f"**Overall Evaluation Status:** **{report.overall_status.value}**  ",
            f"**Invariant Integrity:** **{'PASSED (0 Hard Violations)' if report.invariants_passed else 'FAILED (Hard Invariant Violations Detected)'}**  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Status Overview",
            "",
            f"- **Total Evaluated Metrics:** `{report.total_metrics}`",
            f"- **PASS:** `{report.passed_metrics}` (Meets predefined empirical acceptance thresholds)",
            f"- **WARNING:** `{report.warning_metrics}` (Observed deviation or moderate divergence requiring calibration/review)",
            f"- **FAIL:** `{report.failed_metrics}` (Violates hard invariant or practical tolerance threshold)",
            f"- **UNVERIFIED:** `{report.unverified_metrics}` (Lacks published empirical real-world benchmark; assumption documented)",
            f"- **NOT_APPLICABLE:** `{report.not_applicable_metrics}` (Cohort sample size or eligibility empty for this stratum)",
            "",
            "### Dimension Status Breakdown",
            "",
            "| Evaluation Dimension | Total | PASS | WARNING | FAIL | UNVERIFIED | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        for dim_name, summary in report.dimension_summaries.items():
            if summary["fail"] > 0:
                dim_status = "FAIL"
            elif summary["warning"] > 0:
                dim_status = "WARNING"
            elif summary["pass"] > 0:
                dim_status = "PASS"
            else:
                dim_status = "UNVERIFIED"
            lines.append(
                f"| **{dim_name}** | {summary['total']} | {summary['pass']} | {summary['warning']} | {summary['fail']} | {summary['unverified']} | **{dim_status}** |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 2. Quantitative Metric Scorecard",
            "",
            "| Metric ID | Dimension | Synthetic Estimate | Reference Benchmark | Difference | 95% Confidence Interval | Status | Verification |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ])

        for m in report.metrics:
            syn_str = f"{m.synthetic_estimate:,.2f}" if isinstance(m.synthetic_estimate, float) else str(m.synthetic_estimate)
            ref_str = f"{m.reference_estimate:,.2f}" if m.reference_estimate is not None else "—"
            diff_str = f"{m.difference:+,.2f}" if m.difference is not None else "—"
            ci_str = f"[{m.confidence_interval[0]:.2f}, {m.confidence_interval[1]:.2f}]" if m.confidence_interval else "—"
            lines.append(
                f"| `{m.metric_id}` | {m.dimension.value} | {syn_str} | {ref_str} | {diff_str} | {ci_str} | **{m.status.value}** | `{m.verification_status}` |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Invariant & Safety Evaluation",
            "",
            "Hard temporal and causal invariants protect structural and clinical correctness independently of statistical comparisons.",
            "",
        ])

        inv_metrics = [m for m in report.metrics if m.dimension.value == "INVARIANTS"]
        for m in inv_metrics:
            icon = "✅" if m.status == MetricStatus.PASS else "❌"
            lines.extend([
                f"### {icon} {m.metric_name}",
                f"- **Definition:** {m.definition}",
                f"- **Violations Observed:** `{int(m.synthetic_estimate)}` out of `{m.denominator}` records",
                f"- **Acceptance Threshold:** `0 violations permitted`",
                f"- **Status:** **{m.status.value}**",
                f"- **Known Limitations:** {m.known_limitations}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 4. Demographic Fidelity Details",
            "",
        ])

        demo_metrics = [m for m in report.metrics if m.dimension.value == "DEMOGRAPHICS"]
        for m in demo_metrics:
            lines.extend([
                f"### {m.metric_name} (`{m.metric_id}`)",
                f"- **Definition:** {m.definition}",
                f"- **Synthetic Estimate:** `{m.synthetic_estimate}` | **Reference Benchmark:** `{m.reference_estimate}`",
                f"- **Difference:** `{m.difference}`",
                f"- **Confidence Interval (95% Wilson):** `{m.confidence_interval or 'N/A'}`",
                f"- **Acceptance Policy & Diagnostics:** `{m.acceptance_threshold}`",
                f"- **Provenance:** `{m.provenance_id}` (`{m.verification_status}`)",
                f"- **Status:** **{m.status.value}**",
                f"- **Limitations:** {m.known_limitations}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 5. Disease Prevalence Details (Denominator Matched)",
            "",
        ])

        prev_metrics = [m for m in report.metrics if m.dimension.value == "PREVALENCE"]
        for m in prev_metrics:
            lines.extend([
                f"### {m.metric_name} (`{m.metric_id}`)",
                f"- **Definition:** {m.definition}",
                f"- **Eligible Cohort Denominator:** `{m.denominator}` patients | **Diagnosed Cases:** `{m.numerator}`",
                f"- **Synthetic Prevalence:** `{m.synthetic_estimate}%` (95% CI: `{m.confidence_interval[0]}% - {m.confidence_interval[1]}%`)",
                f"- **Empirical Reference:** `{m.reference_estimate}%` (Absolute Diff: `{m.difference}%`, Relative Diff: `{round((m.relative_difference or 0)*100, 2)}%`)",
                f"- **Provenance:** `{m.provenance_id}` (`{m.verification_status}`)",
                f"- **Status:** **{m.status.value}**",
                f"- **Diagnostics & Crude Values:** `{m.acceptance_threshold}`",
                f"- **Limitations:** {m.known_limitations}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 6. Comorbidity & Disease Clustering Details",
            "",
        ])

        comorb_metrics = [m for m in report.metrics if m.dimension.value == "COMORBIDITY"]
        for m in comorb_metrics:
            lines.extend([
                f"### {m.metric_name} (`{m.metric_id}`)",
                f"- **Definition:** {m.definition}",
                f"- **Synthetic Conditional Prevalence P(HTN|T2D):** `{m.synthetic_estimate}%` (Cases: `{m.numerator}` / `{m.denominator}`)",
                f"- **Reference Benchmark (ICMR-INDIAB 2023):** `{m.reference_estimate}%`",
                f"- **Association Diagnostics:** `{m.acceptance_threshold}`",
                f"- **Status:** **{m.status.value}** (`{m.verification_status}`)",
                f"- **Limitations:** {m.known_limitations}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 7. Longitudinal Dynamics & Clinical Treatments",
            "",
        ])

        other_metrics = [m for m in report.metrics if m.dimension.value in ("LONGITUDINAL", "TREATMENT")]
        for m in other_metrics:
            lines.extend([
                f"### {m.metric_name} (`{m.metric_id}`)",
                f"- **Dimension:** `{m.dimension.value}`",
                f"- **Synthetic Estimate:** `{m.synthetic_estimate}` | **Reference Benchmark:** `{m.reference_estimate or 'Unspecified'}`",
                f"- **Provenance:** `{m.provenance_id}` (`{m.verification_status}`)",
                f"- **Status:** **{m.status.value}**",
                f"- **Known Limitations & Assumptions:** {m.known_limitations}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 8. Calibration Guidance & Research Governance",
            "",
            "- **Separation of Evaluation from Generation:** Evaluator inspected exported CSV artifacts without relying on simulation memory objects.",
            "- **Denominator Compatibility:** Denominators for adult chronic non-communicable conditions (HTN, T2D) strictly filter for age >= 20, matching ICMR-INDIAB survey methodology.",
            "- **Unverified Benchmarks:** Metrics without formal peer-reviewed or census benchmarks are explicitly labeled `UNVERIFIED` and never marked `PASS`.",
            "- **Adherence Assumption:** Medication adherence is assumed to be 100% in simulation, which represents an idealized clinical trial or guideline-adherent baseline.",
            "",
        ])

        return "\n".join(lines)

    @staticmethod
    def save_markdown(report: EvaluationReport, output_path: Path) -> Path:
        """Write Markdown report to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(EvaluationReportFormatter.to_markdown(report))
        return output_path
