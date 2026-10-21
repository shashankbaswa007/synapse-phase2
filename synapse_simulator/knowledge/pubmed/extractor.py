"""
Biomedical Relationship Extractor.
Extracts structured candidate relationships (Disease -> Medicine, Medicine -> Adverse Effect, etc.)
from PubMed article titles, abstracts, and MeSH terms.
"""

import re
import uuid
from typing import List, Dict, Any, Optional
from synapse_simulator.knowledge.pubmed.models import (
    PubMedArticle,
    BiomedicalEntity,
    KnowledgeRelation,
)
from synapse_simulator.knowledge.pubmed.normalizer import TerminologyNormalizer


class KnowledgeExtractor:
    """Extracts candidate biomedical relations from PubMed article content."""

    ADVERSE_EFFECT_KEYWORDS = [
        "adverse effect", "adverse reaction", "side effect", "toxicity", "risk of",
        "nausea", "headache", "diarrhea", "dizziness", "rash", "fatigue", "dyspepsia",
        "hypoglycemia", "cough", "edema", "hyperkalemia", "myalgia"
    ]

    def extract_relations_from_article(self, article: PubMedArticle) -> List[KnowledgeRelation]:
        """Extract candidate KnowledgeRelation objects from a single PubMed article."""
        relations: List[KnowledgeRelation] = []
        text = f"{article.title}. {article.abstract}"

        # 1. Identify disease in article (from query_topic or text)
        disease_info = TerminologyNormalizer.normalize_disease_name(article.query_topic)
        if not disease_info:
            disease_info = TerminologyNormalizer.normalize_disease_name(text)

        disease_name = disease_info[1] if disease_info else article.query_topic

        # 2. Extract drug occurrences in title/abstract/MeSH
        found_drugs = set()

        # Check MeSH terms first
        for mesh in article.mesh_terms:
            drug = TerminologyNormalizer.normalize_drug_name(mesh)
            if drug:
                found_drugs.add(drug)

        # Check text
        for word in text.split():
            clean_word = word.strip(",.():;[]\"'")
            drug = TerminologyNormalizer.normalize_drug_name(clean_word)
            if drug:
                found_drugs.add(drug)

        # 3. Create Disease -> Medicine TREATED_BY relations
        for drug in found_drugs:
            rel_id = f"rel-treat-{article.pmid}-{drug.lower().replace(' ', '_')}"
            rel = KnowledgeRelation(
                relation_id=rel_id,
                subject_entity=disease_name,
                subject_type="DISEASE",
                predicate="TREATED_BY",
                object_entity=drug,
                object_type="MEDICINE",
                pmid=article.pmid,
                evidence_title=article.title,
                confidence=0.90 if article.mesh_terms else 0.82,
                extraction_method="CO_OCCURRENCE_NLP",
                source_snippet=article.title[:120],
                is_validated=False,
                validation_status="CANDIDATE",
            )
            relations.append(rel)

        # 4. Extract Adverse Effects if present
        for ae_kw in self.ADVERSE_EFFECT_KEYWORDS:
            if re.search(r'\b' + re.escape(ae_kw) + r'\b', text, re.IGNORECASE):
                for drug in found_drugs:
                    ae_rel_id = f"rel-ae-{article.pmid}-{drug.lower()}-{ae_kw.replace(' ', '_')}"
                    rel = KnowledgeRelation(
                        relation_id=ae_rel_id,
                        subject_entity=drug,
                        subject_type="MEDICINE",
                        predicate="HAS_ADVERSE_EFFECT",
                        object_entity=ae_kw.capitalize(),
                        object_type="ADVERSE_EFFECT",
                        pmid=article.pmid,
                        evidence_title=article.title,
                        confidence=0.75,
                        extraction_method="PATTERN_MATCHING",
                        source_snippet=f"Literature mentions '{ae_kw}' in context of {drug}",
                        is_validated=False,
                        validation_status="CANDIDATE",
                    )
                    relations.append(rel)

        return relations
