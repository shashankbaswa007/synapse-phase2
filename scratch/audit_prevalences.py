"""
Inspect hypertension & diabetes prevalence metrics across N=500 seeds.
"""
import json
from pathlib import Path

BASE_DIR = Path("/Users/shashi/synapse/synapse-phase2/data/experiments/longitudinal_trajectories")
SEEDS = [42, 101, 202, 303, 404]

for seed in SEEDS:
    rep_file = BASE_DIR / f"n500_s{seed}" / "EVALUATION_REPORT.json"
    with open(rep_file, "r", encoding="utf-8") as f:
        rep = json.load(f)
        
    htn = next(m for m in rep["metrics"] if m["metric_id"] == "prev_hypertension_adults")
    t2d = next(m for m in rep["metrics"] if m["metric_id"] == "prev_diabetes_t2_adults")
    
    htn_diag = htn["acceptance_threshold"]
    print(f"\n--- Seed {seed} ---")
    print(f"HTN (Denominator Adults >= 20 = {htn['denominator']}):")
    print(f"  Baseline Point Prevalence: {htn_diag.get('baseline_point_prevalence_pct')}% ({htn_diag.get('baseline_point_cases')} cases)")
    print(f"  2-Year Period Prevalence:  {htn['synthetic_estimate']}% ({htn['numerator']} cases) [Ref: {htn['reference_estimate']}%, Diff: {htn['difference']}%]")
    print(f"  Incident Cases:            {htn_diag.get('incident_cases')} ({htn_diag.get('incident_attack_rate_pct')}%)")
    print(f"  95% CI:                    {htn['confidence_interval']}")
    print(f"T2D (Denominator Adults >= 20 = {t2d['denominator']}):")
    print(f"  Period Prevalence:         {t2d['synthetic_estimate']}% ({t2d['numerator']} cases) [Ref: {t2d['reference_estimate']}%, Diff: {t2d['difference']}%]")
    print(f"  95% CI:                    {t2d['confidence_interval']}")
