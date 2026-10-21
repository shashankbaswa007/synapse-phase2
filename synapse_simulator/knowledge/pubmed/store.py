"""
Local Knowledge Store for PubMed Articles, Biomedical Entities, and Provenance-Backed Relationships.
Persists structured records into JSONL and JSON format.
Graph-compatible node & edge representation.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from synapse_simulator.knowledge.pubmed.models import (
    PubMedArticle,
    BiomedicalEntity,
    KnowledgeRelation,
)


class PubMedKnowledgeStore:
    """Manages persistent disk storage of retrieved PubMed evidence, entities, and relations."""

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = store_dir or Path("data/knowledge/pubmed")
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.articles_file = self.store_dir / "articles.jsonl"
        self.entities_file = self.store_dir / "entities.jsonl"
        self.relations_file = self.store_dir / "relationships.jsonl"
        self.manifest_file = self.store_dir / "manifest.json"

    def save_articles(self, articles: List[PubMedArticle]) -> None:
        """Write articles to articles.jsonl."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        existing_pmids = set()
        if self.articles_file.exists():
            with open(self.articles_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        existing_pmids.add(data.get("pmid"))

        with open(self.articles_file, "a", encoding="utf-8") as f:
            for art in articles:
                if art.pmid not in existing_pmids:
                    f.write(art.model_dump_json() + "\n")
                    existing_pmids.add(art.pmid)

    def save_relationships(self, relations: List[KnowledgeRelation]) -> None:
        """Write relationships to relationships.jsonl."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        existing_rel_ids = set()
        if self.relations_file.exists():
            with open(self.relations_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        existing_rel_ids.add(data.get("relation_id"))

        with open(self.relations_file, "a", encoding="utf-8") as f:
            for rel in relations:
                if rel.relation_id not in existing_rel_ids:
                    f.write(rel.model_dump_json() + "\n")
                    existing_rel_ids.add(rel.relation_id)


    def save_manifest(self, metrics: Dict[str, Any]) -> None:
        """Save storage manifest with counts and execution metadata."""
        manifest_data = {
            "last_updated": datetime.now().isoformat(),
            "metrics": metrics,
        }
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

    def load_articles(self) -> List[PubMedArticle]:
        """Load all articles from articles.jsonl."""
        articles = []
        if not self.articles_file.exists():
            return articles
        with open(self.articles_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    articles.append(PubMedArticle.model_validate(json.loads(line)))
        return articles

    def load_relationships(self) -> List[KnowledgeRelation]:
        """Load all relationships from relationships.jsonl."""
        relations = []
        if not self.relations_file.exists():
            return relations
        with open(self.relations_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    relations.append(KnowledgeRelation.model_validate(json.loads(line)))
        return relations

    def get_relationships_for_condition(self, condition_name: str) -> List[KnowledgeRelation]:
        """Load stored relationships matching condition name."""
        all_rels = self.load_relationships()
        if not condition_name:
            return []
        
        target = condition_name.lower()
        matched = []
        for rel in all_rels:
            subj = rel.subject_entity.lower()
            if target in subj or subj in target:
                matched.append(rel)
        return matched

