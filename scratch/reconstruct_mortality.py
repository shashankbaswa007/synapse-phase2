"""
Script to reconstruct exact individual-level actuarial mortality for N=500 seeds.
Computes:
- Cohort age distribution
- Individual 720-day death probabilities p_i
- Exact expected deaths E[D] = sum(p_i)
- Poisson-binomial variance Var(D) = sum(p_i * (1 - p_i))
- 95% Predictive Interval
- Observed deaths and cause breakdown
- Total person-time and CMR
"""

import csv
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path("/Users/shashi/synapse/synapse-phase2")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from synapse_simulator.population.loader import load_population_profile

PROFILE_PATH = PROJECT_ROOT / "config" / "population" / "india_default_v1.yaml"
profile = load_population_profile(PROFILE_PATH)

MORTALITY_BANDS = profile.mortality.bands if profile.mortality else []

def get_qx(age: int) -> float:
    for b in MORTALITY_BANDS:
        if b.min_age <= age <= b.max_age:
            return b.qx_annual
    return 0.0

TAU_YEARS = 720.0 / 365.25  # 1.9712525667

SEEDS = [42, 101, 202, 303, 404]
BASE_DIR = PROJECT_ROOT / "data" / "experiments" / "longitudinal_trajectories"

print("=========================================================================================")
print(f"ACTUARIAL MORTALITY RECONSTRUCTION (N=500, Window=720 days = {TAU_YEARS:.5f} years)")
print("=========================================================================================")

results = []

for seed in SEEDS:
    seed_dir = BASE_DIR / f"n500_s{seed}"
    patients_file = seed_dir / "patients.csv"
    deaths_file = seed_dir / "deaths.csv"

    # Read patients
    patients = []
    with open(patients_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            patients.append(r)

    # Read deaths
    deaths = []
    with open(deaths_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            deaths.append(r)

    n_patients = len(patients)
    ages = [int(p["age"]) for p in patients]

    # Age distribution
    age_0_14 = sum(1 for a in ages if a < 15)
    age_15_24 = sum(1 for a in ages if 15 <= a <= 24)
    age_25_44 = sum(1 for a in ages if 25 <= a <= 44)
    age_45_64 = sum(1 for a in ages if 45 <= a <= 64)
    age_65_plus = sum(1 for a in ages if a >= 65)
    age_75_plus = sum(1 for a in ages if a >= 75)
    mean_age = sum(ages) / n_patients

    # Individual mortality probabilities
    p_i_list = []
    for a in ages:
        qx = get_qx(a)
        # 2-year cumulative survival = (1 - qx)^tau -> p_i = 1 - (1 - qx)^tau
        p_i = 1.0 - (1.0 - qx) ** TAU_YEARS
        p_i_list.append(p_i)

    e_d = sum(p_i_list)
    var_d = sum(p * (1.0 - p) for p in p_i_list)
    sd_d = math.sqrt(var_d)
    pi_low = max(0.0, e_d - 1.96 * sd_d)
    pi_high = e_d + 1.96 * sd_d

    # Observed deaths
    obs_deaths = len(deaths)
    causes = {}
    for d in deaths:
        c = d.get("cause_code", "UNKNOWN")
        causes[c] = causes.get(c, 0) + 1

    # Read evaluation report for exact person-time
    import json
    rep_file = seed_dir / "EVALUATION_REPORT.json"
    with open(rep_file, "r", encoding="utf-8") as f:
        rep_json = json.load(f)
    
    mort_m = next(m for m in rep_json["metrics"] if m["metric_id"] == "long_crude_mortality_rate")
    pt_years = mort_m["acceptance_threshold"]["patient_years"]
    cmr = mort_m["synthetic_estimate"]

    # In PI check
    within_pi = (pi_low <= obs_deaths <= pi_high)

    results.append({
        "seed": seed,
        "n": n_patients,
        "mean_age": round(mean_age, 2),
        "age_dist": {
            "0-14": age_0_14,
            "15-24": age_15_24,
            "25-44": age_25_44,
            "45-64": age_45_64,
            "65+": age_65_plus,
            "75+": age_75_plus,
        },
        "e_d": round(e_d, 2),
        "sd_d": round(sd_d, 2),
        "pi_95": (round(pi_low, 2), round(pi_high, 2)),
        "obs_deaths": obs_deaths,
        "causes": causes,
        "pt_years": pt_years,
        "cmr": cmr,
        "within_pi": within_pi,
    })

    print(f"\n--- Seed {seed} ---")
    print(f"Age: mean={mean_age:.1f}, 0-14={age_0_14}, 15-24={age_15_24}, 25-44={age_25_44}, 45-64={age_45_64}, 65+={age_65_plus} (75+={age_75_plus})")
    print(f"Expected Deaths E[D] = {e_d:.2f}, SD = {sd_d:.2f}, 95% PI = [{pi_low:.2f}, {pi_high:.2f}]")
    print(f"Observed Deaths = {obs_deaths} (Causes: {causes}) -> Within 95% PI: {within_pi}")
    print(f"Person-Time = {pt_years:.2f} pt-yrs, Crude Mortality Rate = {cmr:.5f}")

# Cross-seed meta-analysis
mean_obs = sum(r["obs_deaths"] for r in results) / len(results)
mean_exp = sum(r["e_d"] for r in results) / len(results)
mean_pt = sum(r["pt_years"] for r in results) / len(results)
mean_cmr = sum(r["cmr"] for r in results) / len(results)
sd_obs = math.sqrt(sum((r["obs_deaths"] - mean_obs)**2 for r in results) / (len(results) - 1))
se_mc = sd_obs / math.sqrt(len(results))

print("\n=========================================================================================")
print(f"5-SEED POOLED SUMMARY (N=500):")
print(f"Mean Expected Deaths: {mean_exp:.2f}")
print(f"Mean Observed Deaths: {mean_obs:.2f} (SD across runs = {sd_obs:.2f}, MC SE = {se_mc:.2f})")
print(f"Mean Person-Time: {mean_pt:.2f} pt-yrs (Max Bound = 985.63)")
print(f"Mean Crude Mortality Rate: {mean_cmr:.5f} (Benchmark = 0.00600 - 0.00700)")
print("=========================================================================================")
