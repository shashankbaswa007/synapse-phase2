"""
Script to inspect complication incidence across N=500 seeds.
"""
import csv
from pathlib import Path

BASE_DIR = Path("/Users/shashi/synapse/synapse-phase2/data/experiments/longitudinal_trajectories")
SEEDS = [42, 101, 202, 303, 404]

for seed in SEEDS:
    seed_dir = BASE_DIR / f"n500_s{seed}"
    conds = []
    with open(seed_dir / "conditions.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            conds.append(r)
            
    htn_pids = {c["patient_id"] for c in conds if c["condition_code"] in ("I10", "I12.9")}
    t2d_pids = {c["patient_id"] for c in conds if c["condition_code"] in ("E11.9", "E11.2")}
    chronic_pids = htn_pids.union(t2d_pids)
    
    ckd_pids = {c["patient_id"] for c in conds if c["condition_code"] == "I12.9"}
    neph_pids = {c["patient_id"] for c in conds if c["condition_code"] == "E11.2"}
    comp_pids = ckd_pids.union(neph_pids)
    
    comp_rate = len(comp_pids) / len(chronic_pids) if chronic_pids else 0.0
    print(f"Seed {seed}: Chronic={len(chronic_pids)}, CKD(I12.9)={len(ckd_pids)}, Neph(E11.2)={len(neph_pids)}, Total Distinct Complications={len(comp_pids)} ({comp_rate*100:.2f}%)")
