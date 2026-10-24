# Historical Generated Datasets Archive

> [!WARNING]
> **HISTORICAL / EXPLORATORY RUN ARCHIVE**  
> The directories within `data/generated/` preserve early exploratory run outputs generated during the initial discrete-event hospital operational modeling phase (August–September 2026).
>
> **Canonical Active Cohort:** The official, verified release dataset for SYNAPSE Phase 2 is maintained in [`data/synthetic/`](file:///Users/shashi/synapse/synapse-phase2/data/synthetic/) ($N=10,000$ patients, seed 42, 720 days, timestep 7 days).

---

## Directory Inventory

* **[`data/generated/final_10000/`](final_10000/):** Historical 10,000-patient run from early September 2026 produced by the legacy hospital operational prototype (`HospitalSimulator`).
* **[`data/generated/production_10000/`](production_10000/):** Historical exploratory test output containing discrete-event queue artifacts.

These datasets are retained solely for backward compatibility verification of `--mode hospital` and historical auditability.
