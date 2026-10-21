"""
Print all summaries from LONGITUDINAL_TRAJECTORY_AUDIT.json for accurate tabular reporting.
"""
import json
from pathlib import Path

MANIFEST = Path("/Users/shashi/synapse/synapse-phase2/data/experiments/longitudinal_trajectories/LONGITUDINAL_TRAJECTORY_AUDIT.json")
with open(MANIFEST, "r", encoding="utf-8") as f:
    data = json.load(f)

for n_key in ["n100", "n250", "n500"]:
    n_data = data[n_key]
    n = n_data["cohort_size"]
    print(f"\n==================== Cohort Size N={n} ====================")
    print("Runs:")
    for r in n_data["runs"]:
        s = r["seed"]
        m = r["metrics"]
        d = r["diagnostics"]
        print(f"Seed {s:3d} | Pt-Yrs: {m['long_censored_pt_years']:6.2f} (lost {d['person_years_lost_to_death']:5.2f}) | "
              f"Deaths: {m['long_deaths_count']:2d} (CMR {m['long_crude_mortality_rate']:.5f}) | "
              f"Intens: {m['long_treatment_intensification_rate']*100:5.2f}% | "
              f"Comp: {m['long_chronic_complication_rate']*100:4.2f}% | "
              f"HTN Base: {m['prev_htn_baseline']:5.2f}%, Period: {m['prev_htn_period']:5.2f}% | "
              f"T2D: {m['prev_t2d_adults']:5.2f}%")
    print("Summary:")
    for k, v in n_data["summary"].items():
        print(f"  {k:35s}: mean={v['mean']}, std={v['std']}, min={v['min']}, max={v['max']}")
