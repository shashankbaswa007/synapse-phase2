"""
Medical Knowledge Base Loader: Loads and indexes curated medical domain knowledge from YAML.
Single access point for all diagnosis-treatment-drug-allergy-lab knowledge.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml

from synapse_simulator.knowledge.models import (
    DiagnosisEntry,
    DrugTreatment,
    AllergyEntry,
    ChronicCondition,
    AllergyPrevalence,
    LabTestRange,
    RadiologyFindings,
    VitalsRange,
    ServicePricing,
    MasterDataConfig,
)


class MedicalKnowledgeBase:
    """Loads, validates, and provides lookup access to curated medical domain knowledge."""

    DRUG_METADATA_DEFAULTS: Dict[str, Tuple[str, str, str, int]] = {
        "sitagliptin": ("DPP4_Inhibitor", "100mg", "OD", 30),
        "empagliflozin": ("SGLT2_Inhibitor", "10mg", "OD", 30),
        "glimepiride": ("Sulfonylurea", "1mg", "OD", 30),
        "metformin": ("Biguanide", "500mg", "BD", 30),
        "amlodipine": ("Calcium_Channel_Blocker", "5mg", "OD", 30),
        "losartan": ("ARB", "50mg", "OD", 30),
        "metoprolol": ("Beta_Blocker", "50mg", "BD", 30),
        "hydrochlorothiazide": ("Thiazide_Diuretic", "12.5mg", "OD", 30),
        "budesonide": ("Inhaled_Corticosteroid", "200mcg", "BD", 30),
        "salbutamol": ("Beta2_Agonist", "100mcg", "PRN", 30),
        "montelukast": ("Leukotriene_Antagonist", "10mg", "OD", 30),
        "amoxicillin": ("Beta-Lactam", "500mg", "TDS", 7),
        "azithromycin": ("Macrolide", "500mg", "OD", 5),
        "levofloxacin": ("Fluoroquinolone", "500mg", "OD", 7),
        "nitrofurantoin": ("Nitrofuran", "100mg", "BD", 5),
        "ciprofloxacin": ("Fluoroquinolone", "500mg", "BD", 3),
        "cephalexin": ("Beta-Lactam", "500mg", "QDS", 7),
        "sumatriptan": ("Triptan", "50mg", "PRN", 1),
        "naproxen": ("NSAID", "500mg", "BD", 5),
        "ibuprofen": ("NSAID", "400mg", "TDS", 5),
        "diclofenac": ("NSAID", "50mg", "BD", 5),
        "omeprazole": ("PPI", "20mg", "OD", 14),
        "pantoprazole": ("PPI", "40mg", "OD", 14),
        "domperidone": ("Prokinetic", "10mg", "TDS", 14),
        "sucralfate": ("Mucosal_Protectant", "1g", "BD", 14),
        "paracetamol": ("Analgesic", "500mg", "TDS", 5),
        "celecoxib": ("NSAID", "200mg", "BD", 7),
        "atorvastatin": ("Statin", "10mg", "OD", 30),
        "rosuvastatin": ("Statin", "10mg", "OD", 30),
        "cetirizine": ("Antihistamine", "10mg", "OD", 7),
        "loratadine": ("Antihistamine", "10mg", "OD", 7),
        "hydrocortisone": ("Topical_Corticosteroid", "1%", "BD", 7),
        "hydrocortisone_cream": ("Topical_Corticosteroid", "1%", "BD", 7),
    }

    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or Path(__file__).parent.parent.parent / "config" / "knowledge"

        # Indexed knowledge stores
        self.diagnoses: List[DiagnosisEntry] = []
        self._diagnoses_by_code: Dict[str, DiagnosisEntry] = {}
        self._diagnoses_by_category: Dict[str, List[DiagnosisEntry]] = {}
        self.drug_allergy_matrix: Dict[str, AllergyEntry] = {}
        self.chronic_conditions: List[ChronicCondition] = []
        self.allergy_prevalence: List[AllergyPrevalence] = []
        self.lab_test_ranges: Dict[str, LabTestRange] = {}
        self.radiology_findings: Dict[str, RadiologyFindings] = {}
        self.vitals_ranges: Dict[str, VitalsRange] = {}
        self.service_pricing: ServicePricing = ServicePricing()
        self.master_data_config: MasterDataConfig = MasterDataConfig()
        self.pubmed_manager: Optional[Any] = None

    def load(
        self,
        enable_pubmed: bool = True,
        pubmed_store_dir: Optional[Path] = None,
        offline_mode: bool = True,
    ) -> None:
        """Load all knowledge YAML files and build indexes, optionally enriching with PubMed evidence."""
        self._load_medical_knowledge()
        self._load_master_data_config()
        if enable_pubmed:
            self.load_pubmed_evidence(store_dir=pubmed_store_dir, offline_mode=offline_mode)

    def load_pubmed_evidence(
        self,
        store_dir: Optional[Path] = None,
        offline_mode: bool = True,
    ) -> None:
        """Populate medical knowledge diagnoses with validated PubMed treatment relationships via PubMedKnowledgeManager."""
        try:
            from synapse_simulator.knowledge.pubmed.retriever import PubMedKnowledgeManager
            s_dir = store_dir or Path("data/knowledge/pubmed")
            mgr = PubMedKnowledgeManager(knowledge_base=self, config_path=Path("config/knowledge/pubmed.yaml"), offline_mode=offline_mode)
            mgr.store.store_dir = s_dir
            mgr.store.relations_file = s_dir / "relationships.jsonl"
            mgr.store.articles_file = s_dir / "articles.jsonl"
            self.pubmed_manager = mgr

            # Resolve medical treatment knowledge per unique diagnosis
            for diag in self.diagnoses:
                self._enrich_single_diagnosis_from_pubmed(diag, offline_mode=offline_mode)
        except Exception as e:
            print(f"Warning: PubMed evidence loading encountered an exception: {e}")

    def _enrich_single_diagnosis_from_pubmed(self, diag: DiagnosisEntry, offline_mode: bool = True) -> None:
        """Retrieve and attach validated PubMed treatment evidence to a diagnosis."""
        if not self.pubmed_manager:
            return

        relations = self.pubmed_manager.get_evidence_for_condition(
            condition_name=diag.name,
            disease_code=diag.code,
            offline_mode=offline_mode,
        )

        for rel in relations:
            if not rel.is_validated or rel.predicate != "TREATED_BY":
                continue

            drug_name = rel.object_entity
            drug_lower = drug_name.lower()

            # Check if drug is already present in diagnosis treatments
            existing_treatment = None
            for t in diag.treatments:
                if t.drug.lower() == drug_lower:
                    existing_treatment = t
                    break

            if existing_treatment:
                if rel.pmid and rel.pmid not in existing_treatment.evidence_ids:
                    existing_treatment.evidence_ids.append(rel.pmid)
            else:
                d_class, d_dose, d_freq, d_dur = self.DRUG_METADATA_DEFAULTS.get(
                    drug_lower, ("Therapeutic_Agent", "1 unit", "OD", 7)
                )
                new_treatment = DrugTreatment(
                    drug=drug_name,
                    drug_class=d_class,
                    dosage=d_dose,
                    frequency=d_freq,
                    duration_days=d_dur,
                    source="pubmed_evidence",
                    evidence_ids=[rel.pmid] if rel.pmid else [],
                )
                diag.treatments.append(new_treatment)


    def _load_medical_knowledge(self) -> None:
        """Load medical_knowledge.yaml."""
        path = self.knowledge_dir / "medical_knowledge.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Medical knowledge file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Diagnoses
        for d in data.get("diagnoses", []):
            entry = DiagnosisEntry.model_validate(d)
            self.diagnoses.append(entry)
            self._diagnoses_by_code[entry.code] = entry
            cat = entry.category
            if cat not in self._diagnoses_by_category:
                self._diagnoses_by_category[cat] = []
            self._diagnoses_by_category[cat].append(entry)

        # Drug-Allergy Matrix
        for allergy_name, allergy_data in data.get("drug_allergy_matrix", {}).items():
            # Convert safe_alternatives list of dicts to DrugTreatment objects
            safe_alts = []
            for alt in allergy_data.get("safe_alternatives", []):
                safe_alts.append(DrugTreatment(
                    drug=alt["drug"],
                    drug_class=alt["drug_class"],
                    dosage="",
                    frequency="",
                    duration_days=0,
                ))
            self.drug_allergy_matrix[allergy_name] = AllergyEntry(
                cross_reactive_classes=allergy_data.get("cross_reactive_classes", []),
                cross_reactive_drugs=allergy_data.get("cross_reactive_drugs", []),
                safe_alternatives=safe_alts,
            )

        # Chronic Conditions
        for c in data.get("chronic_conditions", []):
            self.chronic_conditions.append(ChronicCondition.model_validate(c))

        # Allergy Prevalence
        for a in data.get("allergy_prevalence", []):
            self.allergy_prevalence.append(AllergyPrevalence.model_validate(a))

        # Lab Test Ranges
        for test_name, test_data in data.get("lab_test_ranges", {}).items():
            self.lab_test_ranges[test_name] = LabTestRange.model_validate(test_data)

        # Radiology Findings
        for img_type, findings_data in data.get("radiology_findings", {}).items():
            self.radiology_findings[img_type] = RadiologyFindings.model_validate(findings_data)

        # Vitals Ranges
        for group_name, vitals_data in data.get("vitals_ranges", {}).items():
            self.vitals_ranges[group_name] = VitalsRange.model_validate(vitals_data)

        # Service Pricing
        pricing_data = data.get("service_pricing", {})
        if pricing_data:
            self.service_pricing = ServicePricing.model_validate(pricing_data)

    def _load_master_data_config(self) -> None:
        """Load master_data_config.yaml."""
        path = self.knowledge_dir / "master_data_config.yaml"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data:
            self.master_data_config = MasterDataConfig.model_validate(data)

    # --- Lookup Methods ---

    def get_diagnosis_by_code(self, code: str) -> Optional[DiagnosisEntry]:
        """Retrieve a diagnosis by ICD-10 code."""
        return self._diagnoses_by_code.get(code)

    def get_diagnoses_by_category(self, category: str) -> List[DiagnosisEntry]:
        """Retrieve all diagnoses in a category."""
        return self._diagnoses_by_category.get(category, [])

    def get_diagnoses_for_age(self, age: int) -> List[DiagnosisEntry]:
        """Filter diagnoses valid for a patient's age."""
        return [d for d in self.diagnoses if d.age_range[0] <= age <= d.age_range[1]]

    def get_treatments_for_diagnosis(self, code: str) -> List[DrugTreatment]:
        """Get treatment options for a diagnosis code.
        Dynamically enriches from PubMed if not already populated.
        """
        diag = self._diagnoses_by_code.get(code)
        if not diag:
            return []
        if not diag.treatments and self.pubmed_manager:
            self._enrich_single_diagnosis_from_pubmed(diag)
        return diag.treatments

    def get_allergy_conflicts(self, patient_allergies: List[str], drug_class: str) -> List[str]:
        """Check if a drug class conflicts with any of the patient's allergies.
        Returns list of conflicting allergy names."""
        conflicts = []
        for allergy in patient_allergies:
            entry = self.drug_allergy_matrix.get(allergy)
            if entry and drug_class in entry.cross_reactive_classes:
                conflicts.append(allergy)
        return conflicts

    def is_drug_safe_for_patient(self, drug_name: str, drug_class: str, patient_allergies: List[str]) -> bool:
        """Check if a specific drug is safe given patient allergies."""
        for allergy in patient_allergies:
            entry = self.drug_allergy_matrix.get(allergy)
            if not entry:
                continue
            if drug_class in entry.cross_reactive_classes:
                return False
            if drug_name in entry.cross_reactive_drugs:
                return False
        return True

    def get_safe_alternatives(self, allergy_name: str) -> List[DrugTreatment]:
        """Get safe drug alternatives for a specific allergy."""
        entry = self.drug_allergy_matrix.get(allergy_name)
        return entry.safe_alternatives if entry else []

    def get_compatible_drugs_for_patient(
        self, diagnosis_code: str, patient_allergies: List[str]
    ) -> List[DrugTreatment]:
        """Get treatments for a diagnosis that are safe for the patient's allergy profile."""
        treatments = self.get_treatments_for_diagnosis(diagnosis_code)
        safe_treatments = [
            t for t in treatments
            if self.is_drug_safe_for_patient(t.drug, t.drug_class, patient_allergies)
        ]
        return safe_treatments

    def get_lab_test_range(self, test_name: str) -> Optional[LabTestRange]:
        """Get reference range for a lab test."""
        return self.lab_test_ranges.get(test_name)

    def get_service_price(self, service_type: str, service_name: str = "") -> float:
        """Get price for a hospital service."""
        if service_type == "consultation":
            return self.service_pricing.consultation_fee
        elif service_type == "follow_up":
            return self.service_pricing.follow_up_fee
        elif service_type == "lab_test":
            return self.service_pricing.lab_test_fees.get(service_name, 300.0)
        elif service_type == "imaging":
            return self.service_pricing.imaging_fees.get(service_name, 1000.0)
        return 0.0

    def get_vitals_range_for_age(self, age: int) -> VitalsRange:
        """Get appropriate vitals range for a patient's age."""
        if age < 18:
            return self.vitals_ranges.get("pediatric", VitalsRange())
        elif age >= 65:
            return self.vitals_ranges.get("elderly", VitalsRange())
        return self.vitals_ranges.get("adult", VitalsRange())

    def get_radiology_findings(self, imaging_type: str) -> Optional[RadiologyFindings]:
        """Get template findings for an imaging type."""
        return self.radiology_findings.get(imaging_type)
