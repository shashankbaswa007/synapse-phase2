import pytest
from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
from synapse_simulator.datagen.master_data import MasterDataGenerator
from synapse_simulator.datagen.clinical_generator import ClinicalEntityGenerator
from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
import random

@pytest.fixture
def kb():
    knowledge_base = MedicalKnowledgeBase()
    knowledge_base.load()
    return knowledge_base

@pytest.fixture
def rng():
    return random.Random(42)

def test_patient_generator(kb, rng):
    gen = PatientProfileGenerator(kb, rng)
    patient = gen.generate_patient()
    assert patient.name is not None
    assert 0 <= patient.age <= 100
    assert patient.gender in ["Male", "Female"]

def test_master_data_generator(kb, rng):
    gen = MasterDataGenerator(kb, rng)
    snapshot = gen.generate()
    assert len(snapshot.departments) > 0
    assert len(snapshot.staff) > 0
    assert len(snapshot.rooms) > 0

def test_clinical_generator(kb, rng):
    master_gen = MasterDataGenerator(kb, rng)
    snapshot = master_gen.generate()
    
    pat_gen = PatientProfileGenerator(kb, rng)
    patient = pat_gen.generate_patient()
    
    clin_gen = ClinicalEntityGenerator(kb, snapshot, rng)
    diagnosis = clin_gen.select_diagnosis(patient)
    assert diagnosis is not None
    
    treatment, conflict = clin_gen.select_medication(patient, diagnosis)
    assert treatment is not None
    
    vitals = clin_gen.generate_vitals(patient, diagnosis)
    assert vitals.temperature_c > 0
