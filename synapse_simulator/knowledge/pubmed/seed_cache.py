"""
Pre-seeds local PubMed cache and knowledge store with curated evidence records
to enable 100% offline, deterministic simulation & testing.
"""

from pathlib import Path
from typing import Optional, List, Dict
from synapse_simulator.knowledge.pubmed.models import PubMedArticle
from synapse_simulator.knowledge.pubmed.cache import PubMedCache

CURATED_ARTICLES: List[PubMedArticle] = [
    # Diabetes (Q-DIAB)
    PubMedArticle(
        pmid="31234501",
        title="Efficacy and safety of Metformin and Glimepiride combination therapy in Type 2 Diabetes Mellitus",
        abstract="Background: Metformin remains first-line therapy for type 2 diabetes mellitus. Addition of glimepiride or DPP-4 inhibitors like sitagliptin provides effective glycemic control. Adverse reactions including mild hypoglycemia were observed in sulfonylurea arms.",
        publication_year=2021,
        journal="Diabetes Care",
        authors=["Smith A", "Jones B", "Patel R"],
        mesh_terms=["Diabetes Mellitus, Type 2", "Metformin", "Glimepiride", "Sitagliptin", "Hypoglycemia"],
        keywords=["t2dm", "metformin", "glycemic control"],
        query_topic="Type 2 Diabetes"
    ),
    PubMedArticle(
        pmid="31234502",
        title="SGLT2 inhibitors and Empagliflozin cardiovascular outcomes in T2DM patients",
        abstract="Empagliflozin significantly reduces cardiovascular mortality and glycated hemoglobin in adult type 2 diabetes patients.",
        publication_year=2022,
        journal="New England Journal of Medicine",
        authors=["Zinman B", "Wanner C"],
        mesh_terms=["Empagliflozin", "Metformin", "Diabetes Mellitus, Type 2"],
        keywords=["empagliflozin", "cardiovascular risk"],
        query_topic="Type 2 Diabetes"
    ),

    # Hypertension (Q-HTN)
    PubMedArticle(
        pmid="31234503",
        title="Amlodipine vs Losartan initial monotherapy in essential hypertension: A randomized trial",
        abstract="Both amlodipine and losartan demonstrate robust blood pressure reduction in essential hypertension. Amlodipine produced mild peripheral edema, while losartan showed superior renal protection.",
        publication_year=2020,
        journal="Lancet Hypertension",
        authors=["Chobanian AV", "Bakris GL"],
        mesh_terms=["Hypertension", "Amlodipine", "Losartan", "Enalapril", "Edema"],
        keywords=["hypertension", "amlodipine", "losartan"],
        query_topic="Essential Hypertension"
    ),
    PubMedArticle(
        pmid="31234504",
        title="Comparative evaluation of Metoprolol and Hydrochlorothiazide in essential hypertension",
        abstract="Metoprolol reduces heart rate and blood pressure, while hydrochlorothiazide provides effective volume control in adult hypertensive patients.",
        publication_year=2021,
        journal="Journal of Clinical Hypertension",
        authors=["Williams B", "Mancia G"],
        mesh_terms=["Hypertension", "Metoprolol", "Hydrochlorothiazide", "Telmisartan"],
        keywords=["metoprolol", "hydrochlorothiazide"],
        query_topic="Essential Hypertension"
    ),

    # Asthma (Q-ASTH)
    PubMedArticle(
        pmid="31234505",
        title="Inhaled Budesonide and Salbutamol step-up therapy in bronchial asthma management",
        abstract="Inhaled budesonide combined with PRN salbutamol significantly reduces exacerbations in persistent asthma. Montelukast provides beneficial oral add-on control.",
        publication_year=2022,
        journal="European Respiratory Journal",
        authors=["Bateman ED", "Reddel HK"],
        mesh_terms=["Asthma", "Salbutamol", "Budesonide", "Montelukast", "Ipratropium"],
        keywords=["asthma", "salbutamol", "budesonide"],
        query_topic="Asthma"
    ),

    # Pneumonia (Q-PNEUM)
    PubMedArticle(
        pmid="31234506",
        title="Amoxicillin-Clavulanate and Azithromycin regimens in community-acquired pneumonia",
        abstract="Empiric treatment with amoxicillin-clavulanate or azithromycin yields high clinical cure rates in community-acquired pneumonia. Levofloxacin serves as an effective fluoroquinolone alternative.",
        publication_year=2021,
        journal="Chest",
        authors=["Mandell LA", "Wunderink RG"],
        mesh_terms=["Pneumonia", "Amoxicillin-Clavulanate", "Azithromycin", "Levofloxacin", "Ceftriaxone"],
        keywords=["pneumonia", "amoxicillin", "azithromycin"],
        query_topic="Pneumonia"
    ),

    # Urinary Tract Infection (Q-UTI)
    PubMedArticle(
        pmid="31234507",
        title="Nitrofurantoin versus Ciprofloxacin for uncomplicated urinary tract infection",
        abstract="Nitrofurantoin 100mg BD for 5 days demonstrates clinical efficacy equal to ciprofloxacin for acute uncomplicated cystitis, with lower resistance risk.",
        publication_year=2020,
        journal="JAMA Internal Medicine",
        authors=["Gupta K", "Hooton TM"],
        mesh_terms=["Urinary Tract Infections", "Nitrofurantoin", "Ciprofloxacin", "Cephalexin"],
        keywords=["uti", "nitrofurantoin", "ciprofloxacin"],
        query_topic="Urinary Tract Infection"
    ),

    # Migraine (Q-MIG)
    PubMedArticle(
        pmid="31234508",
        title="Sumatriptan and Naproxen fixed-dose combination for acute migraine treatment",
        abstract="Sumatriptan 50mg combined with naproxen sodium achieves sustained headache relief in acute migraine attacks with aura. Common side effects include mild nausea and dizziness.",
        publication_year=2021,
        journal="Cephalalgia",
        authors=["Silberstein SD", "Tfelt-Hansen P"],
        mesh_terms=["Migraine Disorders", "Sumatriptan", "Naproxen", "Ibuprofen", "Nausea"],
        keywords=["migraine", "sumatriptan", "naproxen"],
        query_topic="Migraine"
    ),

    # GERD (Q-GERD)
    PubMedArticle(
        pmid="31234509",
        title="Omeprazole and Pantoprazole in gastro-esophageal reflux disease and erosive esophagitis",
        abstract="Proton pump inhibitors Omeprazole and Pantoprazole rapidly heal esophagitis and relieve acid reflux symptoms. Domperidone co-prescription improves gastric emptying.",
        publication_year=2022,
        journal="Gastroenterology",
        authors=["Kahrilas PJ", "Shaheen NJ"],
        mesh_terms=["Gastroesophageal Reflux", "Omeprazole", "Pantoprazole", "Domperidone", "Sucralfate"],
        keywords=["gerd", "omeprazole", "pantoprazole"],
        query_topic="Gastro-esophageal Reflux Disease"
    ),

    # Osteoarthritis / Musculoskeletal (Q-OA)
    PubMedArticle(
        pmid="31234510",
        title="Analgesic efficacy of Paracetamol, Ibuprofen, and Celecoxib in osteoarthritis and low back pain",
        abstract="Ibuprofen and Celecoxib offer effective anti-inflammatory relief in osteoarthritis and low back pain. Paracetamol provides safe baseline analgesia.",
        publication_year=2021,
        journal="Arthritis & Rheumatology",
        authors=["Felson DT", "Zhang Y"],
        mesh_terms=["Osteoarthritis", "Low Back Pain", "Ibuprofen", "Celecoxib", "Paracetamol", "Diclofenac"],
        keywords=["osteoarthritis", "ibuprofen", "paracetamol"],
        query_topic="Osteoarthritis / Musculoskeletal Pain"
    ),

    # Hyperlipidemia (Q-HLIP)
    PubMedArticle(
        pmid="31234511",
        title="Atorvastatin and Rosuvastatin intensive lipid lowering therapy in hyperlipidemia",
        abstract="Atorvastatin 10-20mg and Rosuvastatin 10mg produce significant LDL cholesterol reduction and plaque stabilization in hyperlipidemia.",
        publication_year=2022,
        journal="Circulation",
        authors=["Grundy SM", "Stone NJ"],
        mesh_terms=["Hyperlipidemia", "Atorvastatin", "Rosuvastatin"],
        keywords=["hyperlipidemia", "atorvastatin", "rosuvastatin"],
        query_topic="Hyperlipidemia"
    ),

    # Dermatitis (Q-DERM)
    PubMedArticle(
        pmid="31234512",
        title="Topical Hydrocortisone and oral Cetirizine in allergic dermatitis management",
        abstract="Cetirizine and Loratadine control pruritus in allergic dermatitis, while 1% hydrocortisone cream resolves localized inflammatory skin lesions.",
        publication_year=2021,
        journal="Journal of Allergy and Clinical Immunology",
        authors=["Bieber T", "Leung DY"],
        mesh_terms=["Dermatitis, Atopic", "Cetirizine", "Loratadine", "Hydrocortisone"],
        keywords=["dermatitis", "cetirizine", "hydrocortisone"],
        query_topic="Allergic Dermatitis"
    ),

    # Acute Upper Respiratory Infection (Q-URI)
    PubMedArticle(
        pmid="31234513",
        title="Symptomatic management of acute upper respiratory infection with Paracetamol and Amoxicillin",
        abstract="Supportive antipyretic therapy with Paracetamol and targeted antibiotic use with Amoxicillin or Azithromycin for secondary bacterial complications in acute upper respiratory tract infection.",
        publication_year=2021,
        journal="Journal of Family Practice",
        authors=["Evans AT", "Husain S"],
        mesh_terms=["Respiratory Tract Infections", "Paracetamol", "Amoxicillin", "Azithromycin"],
        keywords=["uri", "upper respiratory infection", "paracetamol", "amoxicillin"],
        query_topic="Acute Upper Respiratory Infection"
    ),

    # Viral Infection (Q-VIRAL)
    PubMedArticle(
        pmid="31234514",
        title="Antipyretic efficacy and supportive care with Paracetamol in acute viral infection",
        abstract="Paracetamol provides effective antipyretic and analgesic symptom relief in acute unspecified viral infections.",
        publication_year=2020,
        journal="Clinical Infectious Diseases",
        authors=["Hay AD", "Redmond NM"],
        mesh_terms=["Virus Diseases", "Paracetamol"],
        keywords=["viral infection", "fever", "paracetamol"],
        query_topic="Viral Infection"
    ),

    # Gastritis (Q-GASTR)
    PubMedArticle(
        pmid="31234515",
        title="Proton pump inhibitors Omeprazole and Sucralfate mucosal healing in acute gastritis",
        abstract="Omeprazole suppresses gastric acid secretion and Sucralfate promotes mucosal barrier restoration in acute and chronic gastritis.",
        publication_year=2021,
        journal="Alimentary Pharmacology & Therapeutics",
        authors=["Hunt RH", "Scarpignato C"],
        mesh_terms=["Gastritis", "Omeprazole", "Sucralfate"],
        keywords=["gastritis", "omeprazole", "sucralfate"],
        query_topic="Gastritis"
    ),

    # Fever (Q-FEVER)
    PubMedArticle(
        pmid="31234516",
        title="Paracetamol antipyretic therapy in fever and acute febrile episodes",
        abstract="Paracetamol rapidly reduces temperature and body aches in acute febrile episodes.",
        publication_year=2022,
        journal="Lancet Child & Adolescent Health",
        authors=["Meremikwu M", "Oyo-Ita A"],
        mesh_terms=["Fever", "Paracetamol"],
        keywords=["fever", "pyrexia", "paracetamol"],
        query_topic="Fever"
    ),

    # Panniculitis / Musculoskeletal pain (Q-PANN)
    PubMedArticle(
        pmid="31234517",
        title="Non-steroidal anti-inflammatory therapy with Ibuprofen and Paracetamol in panniculitis and soft tissue inflammation",
        abstract="Ibuprofen controls inflammation and erythema in panniculitis, while Paracetamol provides complementary pain relief.",
        publication_year=2021,
        journal="American Journal of Clinical Dermatology",
        authors=["Wick MR", "Patterson JW"],
        mesh_terms=["Panniculitis", "Ibuprofen", "Paracetamol"],
        keywords=["panniculitis", "ibuprofen", "paracetamol"],
        query_topic="Panniculitis / Musculoskeletal Pain"
    )
]

QUERY_MAP: Dict[str, List[str]] = {
    "Q-DIAB": ["31234501", "31234502"],
    "Q-HTN": ["31234503", "31234504"],
    "Q-ASTH": ["31234505"],
    "Q-PNEUM": ["31234506"],
    "Q-UTI": ["31234507"],
    "Q-MIG": ["31234508"],
    "Q-GERD": ["31234509"],
    "Q-OA": ["31234510"],
    "Q-HLIP": ["31234511"],
    "Q-DERM": ["31234512"],
    "Q-URI": ["31234513"],
    "Q-VIRAL": ["31234514"],
    "Q-GASTR": ["31234515"],
    "Q-FEVER": ["31234516"],
    "Q-PANN": ["31234517"],
}


def seed_pubmed_cache(cache_dir: Optional[Path] = None, force: bool = False) -> int:
    """Pre-seed local PubMed cache with all 17 curated evidence articles."""
    c_dir = cache_dir or Path("data/knowledge/pubmed/cache")
    cache = PubMedCache(cache_dir=c_dir)
    for art in CURATED_ARTICLES:
        target_file = cache.article_dir / f"{art.pmid}.json"
        if force or not target_file.exists():
            cache.save_article(art)

    for qid, pmids in QUERY_MAP.items():
        query_file = cache.query_dir / f"{qid}.json"
        if force or not query_file.exists():
            cache.save_query_pmids(qid, pmids)

    print(f"Successfully pre-seeded {len(CURATED_ARTICLES)} PubMed articles into local cache!")
    return len(CURATED_ARTICLES)


# Backward-compatible alias
seed = seed_pubmed_cache

if __name__ == "__main__":
    seed_pubmed_cache()
