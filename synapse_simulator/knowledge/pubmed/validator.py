"""
Biomedical Knowledge Validator.
Validates PubMed candidate relations against Synapse Authoritative Medicine Vocabulary & Safety Rules.
"""

from typing import List, Dict, Any, Set
from synapse_simulator.knowledge.pubmed.models import KnowledgeRelation
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase


class KnowledgeValidator:
    """Validates extracted PubMed candidate relationships against Synapse Master Data & Safety Constraints."""

    def __init__(self, knowledge_base: MedicalKnowledgeBase):
        self.kb = knowledge_base
        # Build set of authoritative catalog generic drug names
        self.authoritative_drugs: Set[str] = {
            inv.drug_name for inv in knowledge_base.master_data_config.initial_inventory
        }

    def validate_relation(self, relation: KnowledgeRelation) -> KnowledgeRelation:
        """Validate a single candidate relation against Synapse authoritative catalog."""
        # 1. Disease -> Medicine relation check
        if relation.predicate == "TREATED_BY" and relation.object_type == "MEDICINE":
            if relation.object_entity in self.authoritative_drugs:
                relation.is_validated = True
                relation.validation_status = "VALIDATED"
                relation.confidence = min(1.0, relation.confidence + 0.10)
            else:
                relation.is_validated = False
                relation.validation_status = "REJECTED_UNCATALOGED_MEDICINE"

        # 2. Adverse effect relation check
        elif relation.predicate == "HAS_ADVERSE_EFFECT":
            if relation.subject_entity in self.authoritative_drugs:
                relation.is_validated = True
                relation.validation_status = "VALIDATED"
            else:
                relation.is_validated = False
                relation.validation_status = "REJECTED_UNCATALOGED_MEDICINE"

        return relation

    def validate_all(self, relations: List[KnowledgeRelation]) -> List[KnowledgeRelation]:
        """Validate a batch of candidate relations."""
        return [self.validate_relation(rel) for rel in relations]
