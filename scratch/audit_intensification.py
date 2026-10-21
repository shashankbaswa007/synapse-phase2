"""
Script to extract detailed treatment intensification breakdown across N=500 seeds.
"""

import csv
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("/Users/shashi/synapse/synapse-phase2")
SEEDS = [42, 101, 202, 303, 404]
BASE_DIR = PROJECT_ROOT / "data" / "experiments" / "longitudinal_trajectories"

print("=========================================================================================")
print("TREATMENT INTENSIFICATION DETAILED AUDIT (N=500)")
print("=========================================================================================")

for seed in SEEDS:
    seed_dir = BASE_DIR / f"n500_s{seed}"
    
    # Read medications
    meds = []
    with open(seed_dir / "medications.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            meds.append(r)
            
    # Read conditions
    conds = []
    with open(seed_dir / "conditions.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            conds.append(r)
            
    # Read observations
    obs = []
    with open(seed_dir / "observations.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            obs.append(r)
            
    # Read encounters
    encs = []
    with open(seed_dir / "encounters.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            encs.append(r)

    # Patient drug sets
    patient_drugs = {}
    patient_drug_counts = {}
    for m in meds:
        pid = m["patient_id"]
        d = m["drug_name"]
        patient_drugs.setdefault(pid, set()).add(d)
        patient_drug_counts.setdefault(pid, {}).setdefault(d, 0)
        patient_drug_counts[pid][d] += 1

    htn_pids = {c["patient_id"] for c in conds if c["condition_code"] in ("I10", "I12.9")}
    t2d_pids = {c["patient_id"] for c in conds if c["condition_code"] in ("E11.9", "E11.2")}
    chronic_pids = htn_pids.union(t2d_pids)
    treated_chronic = [pid for pid in chronic_pids if pid in patient_drugs]

    # Intensified
    intens_htn = [pid for pid in htn_pids if "Telmisartan" in patient_drugs.get(pid, set())]
    intens_t2d = [pid for pid in t2d_pids if "Glimepiride" in patient_drugs.get(pid, set())]
    intens_total = set(intens_htn).union(set(intens_t2d))

    # Check for redundant duplicate prescriptions
    redundant_telmi = sum(1 for pid, counts in patient_drug_counts.items() if counts.get("Telmisartan", 0) > 1)
    redundant_glim = sum(1 for pid, counts in patient_drug_counts.items() if counts.get("Glimepiride", 0) > 1)

    # Observations: SBP & HbA1c
    followup_sbp = [float(o["value"]) for o in obs if o["observation_code"] == "SBP"]
    uncontrolled_sbp = [v for v in followup_sbp if v > 140.0]

    followup_hba1c = [float(o["value"]) for o in obs if o["observation_code"] == "HbA1c"]
    uncontrolled_hba1c = [v for v in followup_hba1c if v > 7.0]

    intens_pct = (len(intens_total) / len(treated_chronic)) * 100.0 if treated_chronic else 0.0

    print(f"Seed {seed}: Chronic Treated={len(treated_chronic)}, Intensified={len(intens_total)} ({intens_pct:.2f}%)")
    print(f"   HTN: {len(intens_htn)}/{len(htn_pids)} ({len(intens_htn)/len(htn_pids)*100:.1f}%), T2D: {len(intens_t2d)}/{len(t2d_pids)} ({len(intens_t2d)/len(t2d_pids)*100:.1f}%)")
    print(f"   Redundant orders: Telmisartan={redundant_telmi}, Glimepiride={redundant_glim}")
    print(f"   SBP obs: total={len(followup_sbp)}, uncontrolled={len(uncontrolled_sbp)} ({len(uncontrolled_sbp)/len(followup_sbp)*100:.1f}%)")
    print(f"   HbA1c obs: total={len(followup_hba1c)}, uncontrolled={len(uncontrolled_hba1c)} ({len(uncontrolled_hba1c)/len(followup_hba1c)*100:.1f}%)")
