"""
Diagnostic Generator for SYNAPSE Phase 2.
Generates context-aware laboratory test results and radiology imaging reports
driven by MedicalKnowledgeBase reference ranges and findings templates.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from synapse_simulator.datagen.models import GeneratedLabResult, GeneratedRadiologyReport


class DiagnosticGenerator:
    """Generates synthetic lab results and radiology reports aligned with domain knowledge."""

    def __init__(self, rng: random.Random, knowledge_base: Optional[Any] = None):
        self.rng = rng
        self.kb = knowledge_base

    def generate_lab_result(
        self,
        context: Any = None,
        test_type: Optional[str] = None,
        simulated_time: Optional[datetime] = None,
    ) -> GeneratedLabResult:
        """Generate a structured lab result record with test components."""
        # Determine test type
        chosen_type = test_type
        if not chosen_type and context:
            if isinstance(context, dict):
                chosen_type = context.get("test_type") or context.get("test_name")
            elif hasattr(context, "test_type"):
                chosen_type = getattr(context, "test_type")

        if not chosen_type:
            chosen_type = "CBC"

        components: List[Dict[str, Any]] = []
        is_abnormal = False

        # Look up ranges in MedicalKnowledgeBase if available
        test_range_obj = None
        if self.kb and hasattr(self.kb, "lab_test_ranges"):
            test_range_obj = self.kb.lab_test_ranges.get(chosen_type)

        if test_range_obj and hasattr(test_range_obj, "components"):
            # Decide if entire test has an abnormal finding (15% probability)
            force_abnormal = self.rng.random() < 0.15

            for comp in test_range_obj.components:
                low, high = comp.normal_range
                unit = comp.unit
                flag = "Normal"

                if force_abnormal and not is_abnormal:
                    # Make this component abnormal
                    is_abnormal = True
                    if self.rng.random() < 0.5:
                        val = round(low * self.rng.uniform(0.7, 0.95), 2)
                        flag = "Low"
                    else:
                        val = round(high * self.rng.uniform(1.05, 1.3), 2)
                        flag = "High"
                else:
                    val = round(self.rng.uniform(low, high), 2)

                # Integer display for counts like platelets or ESR
                if low >= 10 and high >= 20:
                    val = int(round(val))

                components.append({
                    "name": comp.name,
                    "value": val,
                    "unit": unit,
                    "range": f"{low} - {high}",
                    "flag": flag,
                })
        else:
            # Fallback default CBC panel
            is_abnormal = self.rng.random() < 0.1
            wbc_val = round(self.rng.uniform(4.5, 11.0), 1) if not is_abnormal else round(self.rng.uniform(11.5, 14.5), 1)
            hb_val = round(self.rng.uniform(12.0, 17.5), 1)
            plt_val = self.rng.randint(150, 400)
            components = [
                {"name": "WBC", "value": wbc_val, "unit": "x10^3/uL", "range": "4.5 - 11.0", "flag": "High" if is_abnormal else "Normal"},
                {"name": "Hemoglobin", "value": hb_val, "unit": "g/dL", "range": "12.0 - 17.5", "flag": "Normal"},
                {"name": "Platelets", "value": plt_val, "unit": "x10^3/uL", "range": "150 - 400", "flag": "Normal"},
            ]

        display_name = {
            "CBC": "Complete Blood Count",
            "CRP": "C-Reactive Protein",
            "ESR": "Erythrocyte Sedimentation Rate",
            "Lipid_Panel": "Lipid Profile Panel",
            "FBS": "Fasting Blood Sugar",
            "HbA1c": "Glycated Hemoglobin (HbA1c)",
            "Renal_Function": "Renal Function Panel",
            "Liver_Function": "Liver Function Panel",
            "Urinalysis": "Routine Urinalysis",
            "Urine_Culture": "Urine Culture & Sensitivity",
        }.get(chosen_type, chosen_type)

        return GeneratedLabResult(
            test_name=display_name,
            components=components,
            is_abnormal=is_abnormal,
            ordered_at=simulated_time,
            resulted_at=simulated_time,
        )

    def generate_radiology_report(
        self,
        context: Any = None,
        modality: Optional[str] = None,
        simulated_time: Optional[datetime] = None,
    ) -> GeneratedRadiologyReport:
        """Generate a structured radiology imaging report with findings and impressions."""
        chosen_mod = modality
        if not chosen_mod and context:
            if isinstance(context, dict):
                chosen_mod = context.get("modality") or context.get("imaging_type")
            elif hasattr(context, "modality"):
                chosen_mod = getattr(context, "modality")

        if not chosen_mod:
            chosen_mod = "Chest X-Ray"

        # Standardize key for lookup in MedicalKnowledgeBase
        lookup_key = {
            "Chest X-Ray": "X-Ray_Chest",
            "X-Ray_Chest": "X-Ray_Chest",
            "Lumbar Spine X-Ray": "X-Ray_Lumbar_Spine",
            "X-Ray_Lumbar_Spine": "X-Ray_Lumbar_Spine",
            "CT Head": "CT_Head",
            "CT_Head": "CT_Head",
            "CT Abdomen": "CT_Abdomen",
            "CT_Abdomen": "CT_Abdomen",
        }.get(chosen_mod, chosen_mod)

        is_abnormal = False
        findings = "Normal study with clear lung fields and normal cardiac silhouette."
        impression = "No acute cardiopulmonary disease."

        if self.kb and hasattr(self.kb, "radiology_findings"):
            rf_obj = self.kb.radiology_findings.get(lookup_key)
            if rf_obj:
                if self.rng.random() < 0.15 and rf_obj.abnormal:
                    is_abnormal = True
                    findings = self.rng.choice(rf_obj.abnormal)
                    impression = f"Findings suggestive of {findings.lower().rstrip('.')}"
                else:
                    findings = rf_obj.normal
                    impression = "Unremarkable examination. Normal study."

        canonical_display = {
            "X-Ray_Chest": "Chest X-Ray",
            "X-Ray_Lumbar_Spine": "Lumbar Spine X-Ray",
            "CT_Head": "CT Head",
            "CT_Abdomen": "CT Abdomen",
        }.get(lookup_key, chosen_mod)

        return GeneratedRadiologyReport(
            imaging_type=canonical_display,
            findings=findings,
            impression=impression,
            is_abnormal=is_abnormal,
            ordered_at=simulated_time,
            reported_at=simulated_time,
        )
