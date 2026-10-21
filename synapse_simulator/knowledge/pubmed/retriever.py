"""
PubMed Knowledge Retriever and Pipeline Manager.
Coordinates API fetching, parsing, extraction, normalization, validation, and storage.
Exposes evidence-backed medicine lookup API to Synapse.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from synapse_simulator.knowledge.pubmed.models import (
    PubMedArticle,
    KnowledgeRelation,
    PubMedIntegrationConfig,
    TargetQueryConfig,
)
from synapse_simulator.knowledge.pubmed.client import PubMedClient
from synapse_simulator.knowledge.pubmed.cache import PubMedCache
from synapse_simulator.knowledge.pubmed.parser import PubMedParser
from synapse_simulator.knowledge.pubmed.extractor import KnowledgeExtractor
from synapse_simulator.knowledge.pubmed.normalizer import TerminologyNormalizer
from synapse_simulator.knowledge.pubmed.validator import KnowledgeValidator
from synapse_simulator.knowledge.pubmed.store import PubMedKnowledgeStore
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase


class PubMedKnowledgeManager:
    """High-level facade for PubMed integration, evidence lookup, and ingestion pipeline."""

    def __init__(
        self,
        knowledge_base: Optional[MedicalKnowledgeBase] = None,
        config_path: Optional[Path] = None,
        offline_mode: bool = False,
    ):
        self.kb = knowledge_base or MedicalKnowledgeBase()
        if not hasattr(self.kb, 'diagnoses') or not self.kb.diagnoses:
            self.kb.load()

        self.config_path = config_path or Path("config/knowledge/pubmed.yaml")
        self.config = self._load_config()
        if offline_mode:
            self.config.offline_mode = True

        self.cache = PubMedCache(cache_dir=Path(self.config.cache_dir))
        self.client = PubMedClient(
            cache=self.cache,
            timeout=10,
            rate_limit_delay=self.config.rate_limit_delay_seconds,
            offline_mode=self.config.offline_mode,
        )
        self.extractor = KnowledgeExtractor()
        self.validator = KnowledgeValidator(self.kb)
        self.store = PubMedKnowledgeStore(store_dir=Path(self.config.store_dir))

        self.articles: List[PubMedArticle] = []
        self.relations: List[KnowledgeRelation] = []

    def _load_config(self) -> PubMedIntegrationConfig:
        """Load pubmed.yaml config file."""
        if not self.config_path.exists():
            return PubMedIntegrationConfig()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return PubMedIntegrationConfig.model_validate(data)
        except Exception:
            return PubMedIntegrationConfig()

    def run_ingestion_pipeline(self) -> Dict[str, Any]:
        """Execute full PubMed ingestion pipeline across configured target queries."""
        all_articles: List[PubMedArticle] = []
        all_relations: List[KnowledgeRelation] = []

        if not self.config.enabled:
            return {"status": "DISABLED", "articles_count": 0, "relations_count": 0}

        for q_cfg in self.config.target_queries:
            arts = self.client.execute_query(q_cfg, max_results=self.config.max_results_per_query)
            all_articles.extend(arts)

            for art in arts:
                extracted_rels = self.extractor.extract_relations_from_article(art)
                validated_rels = self.validator.validate_all(extracted_rels)
                all_relations.extend(validated_rels)

        # Save to store
        self.store.save_articles(all_articles)
        self.store.save_relationships(all_relations)

        self.articles = self.store.load_articles()
        self.relations = self.store.load_relationships()

        validated_count = sum(1 for r in self.relations if r.is_validated)
        metrics = {
            "total_articles": len(self.articles),
            "total_pmids": len({a.pmid for a in self.articles}),
            "total_relationships": len(self.relations),
            "validated_relationships": validated_count,
            "candidate_relationships": len(self.relations) - validated_count,
            "queries_executed": len(self.config.target_queries),
        }
        self.store.save_manifest(metrics)
        return metrics

    def _find_query_config(self, condition_name: str, disease_code: Optional[str] = None) -> Optional[TargetQueryConfig]:
        """Find matching TargetQueryConfig from config by code or disease name."""
        cond_lower = condition_name.lower()
        for q_cfg in self.config.target_queries:
            if disease_code and q_cfg.disease_code == disease_code:
                return q_cfg
            if q_cfg.topic.lower() in cond_lower or cond_lower in q_cfg.topic.lower():
                return q_cfg
            if q_cfg.disease_name.lower() in cond_lower or cond_lower in q_cfg.disease_name.lower():
                return q_cfg
        return None

    def get_evidence_for_condition(
        self,
        condition_name: str,
        disease_code: Optional[str] = None,
        offline_mode: Optional[bool] = None,
    ) -> List[KnowledgeRelation]:
        """Get validated treatment evidence for a condition using Cache HIT / MISS semantics.
        
        Cache HIT:
            Returns stored/cached validated relationships. PubMed API is NOT called.
            
        Cache MISS:
            If offline_mode: Returns empty list / existing cached without API call.
            If online_mode: Calls PubMedClient API (search_pmids -> fetch_articles_by_pmids),
            parses XML, extracts, normalizes, validates, stores in cache & store, and returns.
        """
        is_offline = offline_mode if offline_mode is not None else self.config.offline_mode
        q_cfg = self._find_query_config(condition_name, disease_code)

        # 1. Check Store/Cache for existing validated relationships (Cache HIT)
        existing_rels = self.store.get_relationships_for_condition(condition_name)
        if existing_rels:
            validated = [r for r in existing_rels if r.is_validated]
            if validated:
                return validated

        # Check if query PMIDs & articles exist in PubMedCache
        if q_cfg:
            cached_pmids = self.cache.get_query_pmids(q_cfg.id)
            if cached_pmids:
                cached_articles = self.client.fetch_articles_by_pmids(cached_pmids, query_topic=q_cfg.topic)
                if cached_articles:
                    rels = []
                    for art in cached_articles:
                        extracted = self.extractor.extract_relations_from_article(art)
                        valid = self.validator.validate_all(extracted)
                        rels.extend(valid)
                    if rels:
                        self.store.save_articles(cached_articles)
                        self.store.save_relationships(rels)
                        return [r for r in rels if r.is_validated]

        # 2. Cache MISS: Query PubMed API if in online mode
        if is_offline or not self.config.enabled:
            return []

        search_term = q_cfg.search_term if q_cfg else f"{condition_name} treatment drug therapy"
        topic = q_cfg.topic if q_cfg else condition_name
        q_id = q_cfg.id if q_cfg else f"Q-{condition_name[:4].upper()}"

        pmids = self.client.search_pmids(search_term, max_results=self.config.max_results_per_query)
        if not pmids:
            return []

        self.cache.save_query_pmids(q_id, pmids)
        articles = self.client.fetch_articles_by_pmids(pmids, query_topic=topic)

        all_extracted = []
        for art in articles:
            e_rels = self.extractor.extract_relations_from_article(art)
            v_rels = self.validator.validate_all(e_rels)
            all_extracted.extend(v_rels)

        self.store.save_articles(articles)
        self.store.save_relationships(all_extracted)

        return [r for r in all_extracted if r.is_validated]

    def find_candidate_medicines(self, condition_name: str) -> List[Dict[str, Any]]:
        """Look up evidence-backed candidate medicines for a disease condition."""
        if not self.relations:
            self.relations = self.store.load_relationships()

        norm_disease = TerminologyNormalizer.normalize_disease_name(condition_name)
        target_name = norm_disease[1] if norm_disease else condition_name

        candidates = []
        seen_drugs = set()

        for rel in self.relations:
            if rel.is_validated and rel.predicate == "TREATED_BY":
                if rel.subject_entity.lower() == target_name.lower() or target_name.lower() in rel.subject_entity.lower():
                    drug = rel.object_entity
                    if drug not in seen_drugs:
                        seen_drugs.add(drug)
                        candidates.append({
                            "drug_name": drug,
                            "pmid": rel.pmid,
                            "evidence_title": rel.evidence_title,
                            "confidence": rel.confidence,
                            "validation_status": rel.validation_status,
                        })

        return candidates

    def get_evidence_for_treatment(self, condition_name: str, drug_name: str) -> Optional[KnowledgeRelation]:
        """Retrieve PubMed evidence record for a specific (condition, drug) pair."""
        if not self.relations:
            self.relations = self.store.load_relationships()

        norm_drug = TerminologyNormalizer.normalize_drug_name(drug_name) or drug_name

        for rel in self.relations:
            if rel.predicate == "TREATED_BY" and rel.object_entity.lower() == norm_drug.lower():
                if condition_name.lower() in rel.subject_entity.lower() or rel.subject_entity.lower() in condition_name.lower():
                    return rel

        return None

