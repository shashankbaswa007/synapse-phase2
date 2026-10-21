"""
NCBI E-utilities HTTP Client for PubMed API Integration.
"""

import time
import urllib.request
import urllib.parse
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from synapse_simulator.knowledge.pubmed.models import PubMedArticle, TargetQueryConfig
from synapse_simulator.knowledge.pubmed.cache import PubMedCache
from synapse_simulator.knowledge.pubmed.parser import PubMedParser


class PubMedClient:
    """Client for fetching PubMed metadata and abstracts via NCBI E-utilities API."""

    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(
        self,
        cache: Optional[PubMedCache] = None,
        timeout: int = 10,
        rate_limit_delay: float = 0.35,
        offline_mode: bool = False,
    ):
        self.cache = cache or PubMedCache()
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.offline_mode = offline_mode
        self._last_request_time = 0.0

    def _wait_rate_limit(self) -> None:
        """Enforce NCBI rate limit (max 3 req/sec)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def search_pmids(self, query: str, max_results: int = 5) -> List[str]:
        """Search PubMed for a query string and return list of PMIDs."""
        if self.offline_mode:
            return []

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": str(max_results),
            "retmode": "json",
        }
        url = f"{self.ESEARCH_URL}?{urllib.parse.urlencode(params)}"

        self._wait_rate_limit()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SynapseSimulator/2.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return PubMedParser.parse_esearch_json(data)
        except Exception as e:
            print(f"PubMed ESearch network call failed (query='{query}'): {e}")
            return []

    def fetch_articles_by_pmids(self, pmids: List[str], query_topic: str = "") -> List[PubMedArticle]:
        """Fetch PubMedArticle objects for a list of PMIDs, using local cache first."""
        articles: List[PubMedArticle] = []
        uncached_pmids = []

        # 1. Check local cache first
        for pmid in pmids:
            cached_art = self.cache.get_article(pmid)
            if cached_art:
                articles.append(cached_art)
            else:
                uncached_pmids.append(pmid)

        # If all were cached or we are offline, return cached articles
        if not uncached_pmids or self.offline_mode:
            return articles

        # 2. Fetch uncached PMIDs from NCBI efetch
        params = {
            "db": "pubmed",
            "id": ",".join(uncached_pmids),
            "retmode": "xml",
        }
        url = f"{self.EFETCH_URL}?{urllib.parse.urlencode(params)}"

        self._wait_rate_limit()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SynapseSimulator/2.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                xml_content = resp.read().decode("utf-8")
                fetched = PubMedParser.parse_efetch_xml(xml_content, query_topic=query_topic)

                for art in fetched:
                    self.cache.save_article(art)
                    articles.append(art)
        except Exception as e:
            print(f"PubMed EFetch network call failed for PMIDs {uncached_pmids}: {e}")

        return articles

    def execute_query(self, query_cfg: TargetQueryConfig, max_results: int = 5) -> List[PubMedArticle]:
        """Execute search for a TargetQueryConfig, with caching and fallback."""
        # 1. Check if query PMIDs are cached
        cached_pmids = self.cache.get_query_pmids(query_cfg.id)
        if cached_pmids is not None:
            return self.fetch_articles_by_pmids(cached_pmids, query_topic=query_cfg.topic)

        # 2. Search online if not offline
        if not self.offline_mode:
            pmids = self.search_pmids(query_cfg.search_term, max_results=max_results)
            if pmids:
                self.cache.save_query_pmids(query_cfg.id, pmids)
                return self.fetch_articles_by_pmids(pmids, query_topic=query_cfg.topic)

        return []
