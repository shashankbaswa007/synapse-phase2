"""
Comprehensive Verification Tests for Refactored Medical Knowledge & Simulation Rule Architecture.

Validates:
A. PubMed treatment retrieval (Condition -> MedicalKnowledgeBase -> PubMed -> Candidates)
B. PubMed provenance (source='pubmed_evidence', genuine evidence_ids)
C. No fake evidence (No fabricated PMIDs)
D. YAML independence (Medical treatment retrieval does not depend on deleted YAML treatment blocks)
E. Simulation rules execution across all 5 departments (Clinical, Pharmacy, Lab, Rad, Finance)
F. State transitions and allergy safety check on PubMed candidates
G. Patient journeys and cross-department workflows
H. Offline PubMed cache determinism
"""

import pytest
import yaml
from pathlib import Path

from synapse_simulator.knowledge.pubmed.seed_cache import seed_pubmed_cache
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.knowledge.pubmed.retriever import PubMedKnowledgeManager
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.state.models import ActionRequest


@pytest.fixture(scope="module", autouse=True)
def setup_cache():
    seed_pubmed_cache()


def test_a_pubmed_treatment_retrieval():
    """A. Condition -> MedicalKnowledgeBase -> PubMed -> Treatment candidates."""
    kb = MedicalKnowledgeBase()
    kb.load(enable_pubmed=True, offline_mode=True)

    conditions_to_check = [
        ("E11.9", "metformin"),
        ("I10", "amlodipine"),
        ("J18.9", "amoxicillin"),
        ("J45.9", "salbutamol"),
        ("N39.0", "nitrofurantoin"),
    ]

    for code, expected_drug in conditions_to_check:
        treatments = kb.get_treatments_for_diagnosis(code)
        assert len(treatments) > 0, f"No treatments retrieved for {code}"
        drug_names = [t.drug.lower() for t in treatments]
        assert any(expected_drug in d for d in drug_names), (
            f"Expected {expected_drug} for {code}, got {drug_names}"
        )


def test_b_pubmed_provenance_and_evidence_ids():
    """B. PubMed-derived treatments must have source='pubmed_evidence' and valid evidence_ids."""
    kb = MedicalKnowledgeBase()
    kb.load(enable_pubmed=True, offline_mode=True)

    diag = kb.get_diagnosis_by_code("E11.9")
    assert diag is not None
    treatments = kb.get_treatments_for_diagnosis("E11.9")

    for t in treatments:
        assert t.source == "pubmed_evidence", f"Expected source 'pubmed_evidence', got {t.source}"
        assert len(t.evidence_ids) > 0, f"Treatment {t.drug} has empty evidence_ids"
        for pmid in t.evidence_ids:
            assert pmid.isdigit(), f"Invalid PMID format: {pmid}"
            assert len(pmid) >= 7, f"PMID appears too short: {pmid}"


def test_c_no_fabricated_evidence_or_fake_pmids():
    """C. No fake evidence or fabricated PMIDs for unevidenced conditions."""
    kb = MedicalKnowledgeBase()
    kb.load(enable_pubmed=True, offline_mode=True)

    # An unknown code not in PubMed cache
    treatments = kb.get_treatments_for_diagnosis("Z99.99")
    assert treatments == [], "Unknown diagnosis should return empty treatments list"

    # Fallback treatment verification in ClinicalEntityGenerator
    from synapse_simulator.datagen.clinical_generator import ClinicalEntityGenerator
    from synapse_simulator.datagen.master_data import MasterDataGenerator
    from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
    import random

    rng = random.Random(42)
    master_gen = MasterDataGenerator(kb, rng)
    snapshot = master_gen.generate()
    clin_gen = ClinicalEntityGenerator(kb, snapshot, rng)
    pat_gen = PatientProfileGenerator(kb, rng)
    patient = pat_gen.generate_patient()

    from synapse_simulator.knowledge.models import DiagnosisEntry
    dummy_diag = DiagnosisEntry(
        code="UNKNOWN-99",
        name="Unknown Rare Condition",
        category="general",
        symptoms=["unspecified_symptom"],
        treatments=[],
    )

    med, is_conflict = clin_gen.select_medication(patient, dummy_diag)
    assert med.source == "internal_yaml"
    assert med.evidence_ids == [], f"Fabricated evidence IDs found in fallback: {med.evidence_ids}"


def test_d_yaml_independence_from_static_treatment_blocks():
    """D. Medical treatment retrieval must not depend on static YAML treatment blocks."""
    yaml_path = Path("config/knowledge/medical_knowledge.yaml")
    assert yaml_path.exists()

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    diagnoses = data.get("diagnoses", [])
    assert len(diagnoses) >= 10

    for d in diagnoses:
        assert "treatments" not in d, (
            f"Diagnosis {d.get('code')} still contains static 'treatments' list in YAML!"
        )


def test_e_simulation_rules_execute_across_all_departments():
    """E. Simulation rules still execute for Clinical, Pharmacy, Laboratory, Radiology, and Finance."""
    repo = RuleRepository()
    rule_count = repo.load_rules()
    assert rule_count > 0, "No rules loaded"
    engine = RuleEngine(repo)

    department_actions = [
        ("clinical", "START_DOCTOR_CONSULTATION", {"appointment_status": "Checked-In"}),
        ("pharmacy", "VERIFY_PRESCRIPTION", {"prescription_status": "Issued", "has_allergy_conflict": False}),
        ("laboratory", "COLLECT_SAMPLE", {"order_status": "Ordered"}),
        ("radiology", "ACQUIRE_IMAGE", {"order_status": "Ordered"}),
        ("finance", "GENERATE_INVOICE", {"billable_status": "Pending"}),
    ]

    from datetime import datetime
    from synapse_simulator.state.models import InputContext, DecisionStatus
    now = datetime(2026, 1, 1, 9, 0, 0)

    for dept, action_type, payload in department_actions:
        req = ActionRequest(
            action_id=f"act-test-{dept}",
            action_type=action_type,
            target_department=dept,
            target_entity_table=f"{dept}.test_entities",
            target_entity_id="test-123",
            scenario_instance_id="scen-test-01",
            patient_journey_id="pj-test-01",
            correlation_id="corr-test-01",
            requested_timestamp=now,
            payload=payload,
        )
        ctx = InputContext(
            simulated_timestamp=now,
            scenario_id="SCEN-V1-01",
            scenario_instance_id="scen-test-01",
            patient_journey_id="pj-test-01",
            correlation_id="corr-test-01",
            department_id=dept,
            proposed_action=req,
            entity_state=payload,
        )
        res = engine.evaluate(ctx)
        assert res is not None, f"RuleEngine returned None for department {dept}"
        assert res.status in (DecisionStatus.ALLOWED, DecisionStatus.BLOCKED), f"Unexpected status: {res.status}"


def test_f_allergy_safety_hold_blocks_pubmed_candidate():
    """F. Allergy safety check still blocks conflicting PubMed candidate medication."""
    repo = RuleRepository()
    repo.load_rules()
    engine = RuleEngine(repo)

    from datetime import datetime
    from synapse_simulator.state.models import InputContext, DecisionStatus
    now = datetime(2026, 1, 1, 9, 0, 0)

    # Candidate drug from PubMed has allergy conflict
    req = ActionRequest(
        action_id="act-allergy-test",
        action_type="VERIFY_PRESCRIPTION",
        target_department="pharmacy",
        target_entity_table="pharmacy.prescriptions",
        target_entity_id="rx-test-01",
        scenario_instance_id="scen-allergy-01",
        patient_journey_id="pj-allergy-01",
        correlation_id="corr-allergy-01",
        requested_timestamp=now,
        payload={
            "prescription_status": "Issued",
            "has_allergy_conflict": True,
            "drug_name": "Amoxicillin",
            "drug_class": "Beta-Lactam",
            "patient_allergies": ["Penicillin"],
            "source": "pubmed_evidence",
            "evidence_ids": ["31234506"],
        },
    )
    ctx = InputContext(
        simulated_timestamp=now,
        scenario_id="SCEN-V1-03",
        scenario_instance_id="scen-allergy-01",
        patient_journey_id="pj-allergy-01",
        correlation_id="corr-allergy-01",
        department_id="pharmacy",
        proposed_action=req,
        patient_state={"allergies": ["Penicillin"]},
        entity_state={"status": "Issued"},
        extra_context={"drug_class": "Beta-Lactam"},
    )

    res = engine.evaluate(ctx)
    assert res.status == DecisionStatus.BLOCKED, f"Expected BLOCKED, got {res.status}"
    assert res.winning_rule_id == "RULE-CLIN-ALLERGY-001"


def test_g_patient_journeys_and_cross_department_execution():
    """G. Full patient journeys and cross-department workflows execute smoothly."""
    sim = HospitalSimulator(random_seed=42, enable_pubmed=True, offline_mode=True)
    sim.spawn_patients(8)
    metrics = sim.run(max_events=400)

    assert metrics["total_events_processed"] > 0
    assert metrics["decisions_allowed"] > 0
    assert metrics["decisions_blocked"] > 0  # From SCEN-V1-03 allergy safety hold


def test_h_offline_pubmed_cache_works_deterministically():
    """H. Offline PubMed cache works without internet and is deterministic."""
    mgr1 = PubMedKnowledgeManager(offline_mode=True)
    mgr2 = PubMedKnowledgeManager(offline_mode=True)

    rels1 = mgr1.get_evidence_for_condition("Essential Hypertension")
    rels2 = mgr2.get_evidence_for_condition("Essential Hypertension")

    assert len(rels1) > 0
    assert len(rels1) == len(rels2)
    assert [r.object_entity for r in rels1] == [r.object_entity for r in rels2]
