"""
Pydantic Data Models for PubMed Biomedical Knowledge Integration.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PubMedArticle(BaseModel):
    """Structured record for a PubMed article."""
    pmid: str
    title: str
    abstract: str = ""
    publication_year: Optional[int] = None
    journal: str = ""
    authors: List[str] = Field(default_factory=list)
    mesh_terms: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    query_topic: str = ""


class BiomedicalEntity(BaseModel):
    """Extracted biomedical concept entity (Disease, Drug, Class, Adverse Effect, etc.)."""
    entity_id: str
    name: str
    canonical_name: str
    entity_type: str  # DISEASE, MEDICINE, DRUG_CLASS, ADVERSE_EFFECT, CONTRAINDICATION
    synonyms: List[str] = Field(default_factory=list)
    mesh_id: Optional[str] = None
    synapse_catalog_id: Optional[str] = None  # FK to Synapse medicine identity if matched


class KnowledgeRelation(BaseModel):
    """Evidence-backed relationship between biomedical entities."""
    relation_id: str
    subject_entity: str        # e.g., "Type 2 Diabetes" or "Amoxicillin"
    subject_type: str          # e.g., "DISEASE" or "MEDICINE"
    predicate: str             # e.g., "TREATED_BY", "HAS_ADVERSE_EFFECT", "HAS_CLASS", "CONTRAINDICATED_IN"
    object_entity: str         # e.g., "Metformin" or "Nausea"
    object_type: str           # e.g., "MEDICINE" or "ADVERSE_EFFECT"
    pmid: str
    evidence_title: str = ""
    confidence: float = 0.85
    extraction_method: str = "PATTERN_MATCHING"  # PATTERN_MATCHING, MESH_ANNOTATION, CO_OCCURRENCE
    source_snippet: str = ""
    is_validated: bool = False
    validation_status: str = "CANDIDATE"  # CANDIDATE, VALIDATED, REJECTED


class TargetQueryConfig(BaseModel):
    """Configuration for a specific PubMed search query."""
    id: str
    topic: str
    disease_code: str
    disease_name: str
    search_term: str
    category: str = "general"


class PubMedIntegrationConfig(BaseModel):
    """Global configuration for PubMed knowledge integration."""
    enabled: bool = True
    offline_mode: bool = False
    cache_dir: str = "data/knowledge/pubmed/cache"
    store_dir: str = "data/knowledge/pubmed"
    max_results_per_query: int = 5
    publication_year_min: int = 2015
    publication_year_max: int = 2026
    rate_limit_delay_seconds: float = 0.35
    target_queries: List[TargetQueryConfig] = Field(default_factory=list)
