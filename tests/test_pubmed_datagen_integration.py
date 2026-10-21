"""
End-to-End Integration Tests for PubMed Evidence Enrichment,
Cache HIT / MISS Semantics, API Deduplication, Safety Checks, and Simplified CSV Export.
"""

import os
import shutil
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock

from synapse_simulator.knowledge.pubmed.seed_cache import seed_pubmed_cache
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.knowledge.pubmed.retriever import PubMedKnowledgeManager
from synapse_simulator.knowledge.pubmed.models import PubMedArticle, KnowledgeRelation
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.exporter.csv_exporter import CSVExporter
from generate_synthetic_data import run_data_generation


@pytest.fixture(scope="module", autouse=True)
def ensure_pubmed_cache_seeded():
    """Ensure local PubMed cache is pre-seeded before tests run."""
    seed_pubmed_cache()


def test_cache_hit_avoids_pubmed_api_call():
    """TEST 1 — Cache HIT: Requesting cached condition must NOT call PubMed API."""
    mgr = PubMedKnowledgeManager(offline_mode=True)
    mgr.client.search_pmids = MagicMock(return_value=[])
    mgr.client.fetch_articles_by_pmids = MagicMock(return_value=[])

    rels = mgr.get_evidence_for_condition("Type 2 Diabetes")

    assert len(rels) > 0, "Cache HIT failed to return cached evidence"
    mgr.client.search_pmids.assert_not_called()
    mgr.client.fetch_articles_by_pmids.assert_not_called()


def test_cache_miss_triggers_pubmed_api_call_in_online_mode(tmp_path):
    """TEST 2 — Cache MISS: Requesting uncached condition in online mode calls PubMed API."""
    mgr = PubMedKnowledgeManager(offline_mode=False)
    mgr.store.store_dir = tmp_path / "store"
    mgr.store.relations_file = tmp_path / "store" / "relationships.jsonl"
    mgr.cache.cache_dir = tmp_path / "cache"
    mgr.cache.query_dir = tmp_path / "cache" / "queries"
    mgr.cache.article_dir = tmp_path / "cache" / "articles"
    mgr.cache.query_dir.mkdir(parents=True, exist_ok=True)
    mgr.cache.article_dir.mkdir(parents=True, exist_ok=True)

    mock_article = PubMedArticle(
        pmid="39999001",
        title="Empagliflozin and Metformin in Type 2 Diabetes",
        abstract="Metformin and Empagliflozin combination therapy in Type 2 Diabetes.",
        publication_year=2023,
        journal="Test Journal",
        authors=["Author A"],
        mesh_terms=["Diabetes Mellitus, Type 2", "Empagliflozin", "Metformin"],
        keywords=["t2dm", "empagliflozin"],
        query_topic="Type 2 Diabetes",
    )

    mgr.client.search_pmids = MagicMock(return_value=["39999001"])
    mgr.client.fetch_articles_by_pmids = MagicMock(return_value=[mock_article])

    rels = mgr.get_evidence_for_condition("Type 2 Diabetes", offline_mode=False)

    mgr.client.search_pmids.assert_called_once()
    assert len(rels) > 0, "Cache MISS failed to process and return evidence"
    assert mgr.store.relations_file.exists(), "Processed evidence was not cached to store"


def test_second_request_hits_cache_and_deduplicates_api_calls(tmp_path):
    """TEST 3 — SECOND REQUEST: First call triggers API, second call hits cache (API called only once)."""
    mgr = PubMedKnowledgeManager(offline_mode=False)
    mgr.store.store_dir = tmp_path / "store2"
    mgr.store.relations_file = tmp_path / "store2" / "relationships.jsonl"
    mgr.cache.cache_dir = tmp_path / "cache2"
    mgr.cache.query_dir = tmp_path / "cache2" / "queries"
    mgr.cache.article_dir = tmp_path / "cache2" / "articles"
    mgr.cache.query_dir.mkdir(parents=True, exist_ok=True)
    mgr.cache.article_dir.mkdir(parents=True, exist_ok=True)

    mock_article = PubMedArticle(
        pmid="39999002",
        title="Losartan in Essential Hypertension",
        abstract="Losartan monotherapy reduces blood pressure in essential hypertension.",
        publication_year=2023,
        journal="Hypertension Journal",
        authors=["Author B"],
        mesh_terms=["Hypertension", "Losartan"],
        keywords=["hypertension", "losartan"],
        query_topic="Essential Hypertension",
    )

    mgr.client.search_pmids = MagicMock(return_value=["39999002"])
    mgr.client.fetch_articles_by_pmids = MagicMock(return_value=[mock_article])

    # 1. First request (Cache MISS)
    rels1 = mgr.get_evidence_for_condition("Essential Hypertension", offline_mode=False)
    assert mgr.client.search_pmids.call_count == 1

    # 2. Second request (Cache HIT)
    rels2 = mgr.get_evidence_for_condition("Essential Hypertension", offline_mode=False)
    assert mgr.client.search_pmids.call_count == 1, "Second request should hit cache and NOT call API"
    assert len(rels2) == len(rels1)


def test_offline_mode_returns_cached_without_network(tmp_path):
    """TEST 4 — OFFLINE MODE: Missing cache returns empty without making network calls."""
    mgr = PubMedKnowledgeManager(offline_mode=True)
    mgr.store.store_dir = tmp_path / "empty_store"
    mgr.store.relations_file = tmp_path / "empty_store" / "relationships.jsonl"
    mgr.cache.cache_dir = tmp_path / "empty_cache"

    mgr.client.search_pmids = MagicMock(return_value=["11111"])

    rels = mgr.get_evidence_for_condition("Unknown Condition", offline_mode=True)

    assert rels == [], "Offline mode with missing cache should return empty list"
    mgr.client.search_pmids.assert_not_called()


def test_pubmed_knowledge_base_enrichment_and_provenance():
    """TEST 5 — PROVENANCE: Verify MedicalKnowledgeBase loads PubMed evidence tags."""
    kb = MedicalKnowledgeBase()
    kb.load(enable_pubmed=True)

    diag_diab = kb.get_diagnosis_by_code("E11.9")
    assert diag_diab is not None, "Type 2 Diabetes diagnosis entry missing"

    drug_names = [t.drug.lower() for t in diag_diab.treatments]
    assert "sitagliptin" in drug_names or "empagliflozin" in drug_names, "PubMed-supported antidiabetic drugs missing"

    sources = [t.source for t in diag_diab.treatments]
    assert any("pubmed_evidence" in s for s in sources), "PubMed evidence provenance tag missing"


def test_allergy_safety_hold_preserved():
    """TEST 6 — SAFETY: Verify allergy safety rules still block conflicting PubMed drugs (SCEN-V1-03)."""
    sim = HospitalSimulator(random_seed=42, enable_pubmed=True)
    sim.spawn_patients(4)
    sim.run(max_events=500)

    blocked_count = sim.metrics.get("decisions_blocked", 0)
    assert blocked_count > 0, "Allergy safety hold failed to block conflicting medication"


def test_simplified_csv_export(tmp_path):
    """TEST 7 — SIMULATION CSV EXPORT: Verify all 8 flat CSV files exist and are non-empty."""
    sim = HospitalSimulator(random_seed=42, enable_pubmed=True)
    sim.spawn_patients(10)
    sim.run(max_events=500)

    csv_exporter = CSVExporter(
        state_manager=sim.state_manager,
        master_data=sim.master_data_snapshot,
        patient_contexts=sim.patient_contexts,
        committed_events=sim.engine.committed_events,
        journeys=sim.journeys,
        trace_log=sim.engine.trace_log,
        metrics=sim.metrics,
        output_dir=tmp_path / "phase2",
    )

    out_dir = tmp_path / "synthetic"
    exported = csv_exporter.export_simplified_dataset(target_dir=out_dir)

    expected_files = [
        "patients.csv",
        "encounters.csv",
        "conditions.csv",
        "symptoms.csv",
        "medications.csv",
        "labs.csv",
        "events.csv",
        "generation_summary.csv",
    ]

    for ef in expected_files:
        assert ef in exported, f"Missing expected simplified CSV file: {ef}"
        p = exported[ef]
        assert p.exists(), f"File does not exist: {p}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"CSV file is empty: {p}"


def test_api_call_deduplication_for_n_patients(tmp_path):
    """TEST 8 — API DEDUPLICATION: For 100 patients sharing conditions, API calls depend on unique conditions."""
    kb = MedicalKnowledgeBase()
    mgr = PubMedKnowledgeManager(knowledge_base=kb, offline_mode=False)

    mgr.client.search_pmids = MagicMock(return_value=[])

    # 100 patients map to a small set of unique conditions
    for i in range(100):
        cond = "Type 2 Diabetes" if i % 2 == 0 else "Essential Hypertension"
        mgr.get_evidence_for_condition(cond, offline_mode=False)

    # Should call search_pmids at most twice (once for Diabetes, once for Hypertension)
    assert mgr.client.search_pmids.call_count <= 2, "API was called per patient instead of per unique condition"
