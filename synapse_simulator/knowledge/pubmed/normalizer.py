"""
Medicine and Clinical Terminology Normalizer.
Maps extracted terms from PubMed literature to Synapse Authoritative Vocabularies.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from synapse_simulator.knowledge.pubmed.models import BiomedicalEntity


class TerminologyNormalizer:
    """Normalizes medical terminology, generic drug names, and clinical conditions."""

    # Synonyms mapping to canonical drug generic names in Synapse Catalog
    DRUG_SYNONYMS: Dict[str, str] = {
        "acetaminophen": "Paracetamol",
        "paracetamol": "Paracetamol",
        "amoxicillin": "Amoxicillin",
        "amoxil": "Amoxicillin",
        "azithromycin": "Azithromycin",
        "zithromax": "Azithromycin",
        "ibuprofen": "Ibuprofen",
        "advil": "Ibuprofen",
        "motrin": "Ibuprofen",
        "omeprazole": "Omeprazole",
        "prilosec": "Omeprazole",
        "amlodipine": "Amlodipine",
        "norvasc": "Amlodipine",
        "metformin": "Metformin",
        "glucophage": "Metformin",
        "losartan": "Losartan",
        "cozaar": "Losartan",
        "atorvastatin": "Atorvastatin",
        "lipitor": "Atorvastatin",
        "ciprofloxacin": "Ciprofloxacin",
        "cipro": "Ciprofloxacin",
        "diclofenac": "Diclofenac",
        "voltaren": "Diclofenac",
        "levofloxacin": "Levofloxacin",
        "levaquin": "Levofloxacin",
        "cetirizine": "Cetirizine",
        "zyrtec": "Cetirizine",
        "salbutamol": "Salbutamol",
        "albuterol": "Salbutamol",
        "domperidone": "Domperidone",
        "nitrofurantoin": "Nitrofurantoin",
        "macrodantin": "Nitrofurantoin",
        "sumatriptan": "Sumatriptan",
        "imitrex": "Sumatriptan",
        "glimepiride": "Glimepiride",
        "amaryl": "Glimepiride",
        "pantoprazole": "Pantoprazole",
        "protonix": "Pantoprazole",
        "telmisartan": "Telmisartan",
        "enalapril": "Enalapril",
        "metoprolol": "Metoprolol",
        "hydrochlorothiazide": "Hydrochlorothiazide",
        "hctz": "Hydrochlorothiazide",
        "gliclazide": "Gliclazide",
        "sitagliptin": "Sitagliptin",
        "januvia": "Sitagliptin",
        "empagliflozin": "Empagliflozin",
        "jardiance": "Empagliflozin",
        "cephalexin": "Cephalexin",
        "keflex": "Cephalexin",
        "amoxicillin-clavulanate": "Amoxicillin-Clavulanate",
        "augmentin": "Amoxicillin-Clavulanate",
        "ceftriaxone": "Ceftriaxone",
        "rocephin": "Ceftriaxone",
        "doxycycline": "Doxycycline",
        "clarithromycin": "Clarithromycin",
        "biaxin": "Clarithromycin",
        "naproxen": "Naproxen",
        "aleve": "Naproxen",
        "celecoxib": "Celecoxib",
        "celebrex": "Celecoxib",
        "tramadol": "Tramadol",
        "ultram": "Tramadol",
        "rosuvastatin": "Rosuvastatin",
        "crestor": "Rosuvastatin",
        "ondansetron": "Ondansetron",
        "zofran": "Ondansetron",
        "sucralfate": "Sucralfate",
        "carafate": "Sucralfate",
        "loratadine": "Loratadine",
        "claritin": "Loratadine",
        "levocetirizine": "Levocetirizine",
        "xyz计时": "Levocetirizine",
        "budesonide": "Budesonide",
        "pulmicort": "Budesonide",
        "montelukast": "Montelukast",
        "singulair": "Montelukast",
        "ipratropium": "Ipratropium",
        "atrovent": "Ipratropium",
        "gabapentin": "Gabapentin",
        "neurontin": "Gabapentin",
        "pregabalin": "Pregabalin",
        "lyrica": "Pregabalin",
        "hydrocortisone": "Hydrocortisone_Cream",
        "clotrimazole": "Clotrimazole",
        "tamsulosin": "Tamsulosin",
        "flomax": "Tamsulosin",
        "solifenacin": "Solifenacin",
        "vesicare": "Solifenacin",
        "aspirin": "Aspirin",
        "clopidogrel": "Clopidogrel",
        "plavix": "Clopidogrel",
    }

    # Disease synonyms mapping to canonical condition names
    DISEASE_SYNONYMS: Dict[str, Tuple[str, str]] = {
        "type 2 diabetes": ("E11.9", "Type 2 diabetes mellitus"),
        "type 2 diabetes mellitus": ("E11.9", "Type 2 diabetes mellitus"),
        "t2dm": ("E11.9", "Type 2 diabetes mellitus"),
        "diabetes mellitus": ("E11.9", "Type 2 diabetes mellitus"),
        "hypertension": ("I10", "Essential hypertension"),
        "essential hypertension": ("I10", "Essential hypertension"),
        "high blood pressure": ("I10", "Essential hypertension"),
        "asthma": ("J45.9", "Asthma, unspecified"),
        "bronchial asthma": ("J45.9", "Asthma, unspecified"),
        "pneumonia": ("J18.9", "Pneumonia, unspecified organism"),
        "community-acquired pneumonia": ("J18.9", "Pneumonia, unspecified organism"),
        "urinary tract infection": ("N39.0", "Urinary tract infection, site not specified"),
        "uti": ("N39.0", "Urinary tract infection, site not specified"),
        "migraine": ("G43.9", "Migraine, unspecified"),
        "migraine headache": ("G43.9", "Migraine, unspecified"),
        "gerd": ("K21.0", "Gastro-esophageal reflux disease with esophagitis"),
        "gastroesophageal reflux disease": ("K21.0", "Gastro-esophageal reflux disease with esophagitis"),
        "low back pain": ("M54.5", "Low back pain"),
        "back pain": ("M54.5", "Low back pain"),
        "hyperlipidemia": ("E78.5", "Hyperlipidemia, unspecified"),
        "dyslipidemia": ("E78.5", "Hyperlipidemia, unspecified"),
        "dermatitis": ("L30.9", "Dermatitis, unspecified"),
        "eczema": ("L30.9", "Dermatitis, unspecified"),
        "acute upper respiratory infection": ("J06.9", "Acute upper respiratory infection"),
        "upper respiratory infection": ("J06.9", "Acute upper respiratory infection"),
        "urti": ("J06.9", "Acute upper respiratory infection"),
        "uri": ("J06.9", "Acute upper respiratory infection"),
        "viral infection": ("B34.9", "Viral infection, unspecified"),
        "viral infection, unspecified": ("B34.9", "Viral infection, unspecified"),
        "gastritis": ("K29.7", "Gastritis, unspecified"),
        "gastritis, unspecified": ("K29.7", "Gastritis, unspecified"),
        "fever": ("R50.9", "Fever, unspecified"),
        "fever, unspecified": ("R50.9", "Fever, unspecified"),
        "pyrexia": ("R50.9", "Fever, unspecified"),
        "panniculitis": ("M79.3", "Panniculitis, unspecified"),
        "panniculitis, unspecified": ("M79.3", "Panniculitis, unspecified"),
    }

    @classmethod
    def normalize_drug_name(cls, raw_term: str) -> Optional[str]:
        """Normalize a drug name string to Synapse canonical generic drug name."""
        if not raw_term:
            return None
        term_clean = raw_term.strip().lower()

        # Direct synonym lookup
        if term_clean in cls.DRUG_SYNONYMS:
            return cls.DRUG_SYNONYMS[term_clean]

        # Token match
        for syn, canonical in cls.DRUG_SYNONYMS.items():
            if re.search(r'\b' + re.escape(syn) + r'\b', term_clean):
                return canonical

        return None

    @classmethod
    def normalize_disease_name(cls, raw_term: str) -> Optional[Tuple[str, str]]:
        """Normalize a disease term string to (icd_code, canonical_name)."""
        if not raw_term:
            return None
        term_clean = raw_term.strip().lower()

        if term_clean in cls.DISEASE_SYNONYMS:
            return cls.DISEASE_SYNONYMS[term_clean]

        for syn, res in cls.DISEASE_SYNONYMS.items():
            if syn in term_clean:
                return res

        return None
