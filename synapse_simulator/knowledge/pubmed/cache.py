"""
Local File-Based Caching Layer for PubMed API Responses.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from synapse_simulator.knowledge.pubmed.models import PubMedArticle


class PubMedCache:
    """Manages local JSON disk cache for PubMed PMIDs and search query results."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/knowledge/pubmed/cache")
        self.article_dir = self.cache_dir / "articles"
        self.query_dir = self.cache_dir / "queries"
        
        self.article_dir.mkdir(parents=True, exist_ok=True)
        self.query_dir.mkdir(parents=True, exist_ok=True)

    def get_article(self, pmid: str) -> Optional[PubMedArticle]:
        """Retrieve cached article by PMID."""
        file_path = self.article_dir / f"{pmid}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PubMedArticle.model_validate(data)
        except Exception:
            return None

    def save_article(self, article: PubMedArticle) -> None:
        """Save article to local JSON cache."""
        file_path = self.article_dir / f"{article.pmid}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(article.model_dump_json(indent=2))

    def get_query_pmids(self, query_id: str) -> Optional[List[str]]:
        """Retrieve cached list of PMIDs for a query ID."""
        file_path = self.query_dir / f"{query_id}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("pmids", [])
        except Exception:
            return None

    def save_query_pmids(self, query_id: str, pmids: List[str]) -> None:
        """Save query PMIDs to cache."""
        file_path = self.query_dir / f"{query_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"query_id": query_id, "pmids": pmids}, f, indent=2)

    def clear(self) -> None:
        """Clear cache files."""
        for p in self.article_dir.glob("*.json"):
            p.unlink()
        for p in self.query_dir.glob("*.json"):
            p.unlink()
