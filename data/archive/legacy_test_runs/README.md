# Legacy Test Runs Archive

> [!NOTE]
> **ARCHIVAL RECORD**  
> This directory archives historical scale test runs and validation gate artifacts generated during earlier development milestones (October 2026).
> 
> **Authoritative Release Dataset:** The active, published Phase 2 canonical dataset resides in [`data/synthetic/`](../../synthetic/) ($N=10,000$ patients, seed 42, 720 days).

---

## Directory Catalog

| Directory | Patient Count | Paradigm | Purpose / Description |
| :--- | :---: | :--- | :--- |
| **`test_stage_b/`** | 10 | Hospital Operational (`--mode hospital`) | Initial integration test of cross-departmental patient journeys. |
| **`test_stage_c/`** | 100 | Hospital Operational (`--mode hospital`) | Mid-scale stress test of discrete-event queue dispatcher. |
| **`test_stage_d/`** | 1,000 | Hospital Operational (`--mode hospital`) | High-scale operational verification of hospital inventory & billing. |
| **`test_gate_100/`** | 100 | Hospital Operational (`--mode hospital`) | Automated verification of `DatasetValidationGate` promotion. |
| **`test_gate_1000/`** | 1,000 | Hospital Operational (`--mode hospital`) | Scale verification of validation gate invariants under 1,000 patients. |
| **`failed_run_20261013_165957_7a91b4/`** | — | Negative Test Artifact | Preserved failure report verifying fail-fast gate rejection behavior. |
| **`1000/`** | 1,000 | Hospital Operational (`--mode hospital`) | Legacy 1,000-cohort output previously nested in `data/synthetic/`. |

---

These datasets are preserved strictly for historical auditability and backward-compatibility verification. They do not constitute active release datasets.
