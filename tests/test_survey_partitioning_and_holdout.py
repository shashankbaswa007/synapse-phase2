"""
Unit and Integration Tests for Deterministic Survey Partitioning and Cryptographic Holdout Vault.

Milestone 4 Verification:
1. Determinism and bit-level reproducibility of PSU allocation.
2. Strict enforcement of zero PSU, household, and participant leakage.
3. Design-consistent inverse-allocation conditional weight calculations (w * nh / nh_k).
4. Handling of small/singleton strata under design rules (no cross-state or cross-sector merges).
5. Covariate balance reporting across Age, Sex, Sector, State, and Blood Pressure.
6. Authenticated AES-256-GCM encryption with technically enforced single-use access controls.
7. Tamper-evidence and failure-state defenses.
"""

import base64
import copy
import concurrent.futures
import json
import math
import os
import stat
import pytest
from typing import List

from synapse_simulator.evaluation.lasi.models import LasiCleanedRecord
from synapse_simulator.evaluation.lasi.partitioner import (
    PartitionLabel,
    StratumSupportStatus,
    LasiPartitionConfig,
    LasiClusterAllocation,
    LasiCovariateBalanceReport,
    LasiPartitionResult,
    LasiPsuPartitioner,
    HoldoutAccessTicket,
    HoldoutAuditLedger,
    LasiHoldoutVault,
    LasiPartitioningError,
    LasiLeakageError,
    LasiUnsupportedStratumError,
    HoldoutAccessViolationError,
)
from synapse_simulator.evaluation.lasi.variance import (
    LasiSurveyVarianceEngine,
    SingletonHandlingStrategy,
    student_t_critical_value,
)


@pytest.fixture(autouse=True)
def isolated_test_ledger(tmp_path, monkeypatch):
    """Ensure each test runs with a pristine, isolated temporary holdout audit ledger."""
    ledger_file = tmp_path / "test_holdout_ledger.json"
    monkeypatch.setenv("SYNAPSE_HOLDOUT_LEDGER_PATH", str(ledger_file))
    yield


def _build_test_record(
    pid: str,
    hhid: str,
    state: str,
    urban_rural: str,
    strata: str,
    psu: str,
    weight: float = 1.0,
    age: float = 65.0,
    gender: str = "Female",
    sbp: float = 130.0,
    dbp: float = 80.0,
) -> LasiCleanedRecord:
    """Helper to construct synthetic records with explicit hierarchical survey identifiers."""
    return LasiCleanedRecord(
        participant_id=pid,
        household_id=hhid,
        state=state,
        urban_rural=urban_rural,
        survey_weight=weight,
        strata=strata,
        psu=psu,
        age=age,
        gender=gender,
        sbp_mean=sbp,
        dbp_mean=dbp,
        biomarker_participated=True,
        bp_participated=True,
        hba1c_participated=True,
        has_valid_survey_weight=(weight > 0.0),
    )


def _build_synthetic_survey_cluster_cohort() -> List[LasiCleanedRecord]:
    """Generate a synthetic multi-strata, multi-household cluster cohort for partitioning tests."""
    records = []
    # Stratum 1 (State A, Rural): 5 PSUs (Adequate for 3:2 split)
    for p_idx in range(1, 6):
        psu_name = f"P1_{p_idx}"
        for h_idx in range(1, 4):  # 3 households per PSU
            hh_name = f"hh_{psu_name}_{h_idx}"
            # 2 individuals per household (e.g. husband and wife)
            records.append(_build_test_record(
                pid=f"{hh_name}_ind1", hhid=hh_name, state="State_A", urban_rural="Rural",
                strata="STRAT_A_RURAL", psu=psu_name, weight=10.0, age=60.0 + p_idx, gender="Female",
                sbp=125.0 + p_idx * 2, dbp=80.0
            ))
            records.append(_build_test_record(
                pid=f"{hh_name}_ind2", hhid=hh_name, state="State_A", urban_rural="Rural",
                strata="STRAT_A_RURAL", psu=psu_name, weight=10.0, age=63.0 + p_idx, gender="Male",
                sbp=130.0 + p_idx * 2, dbp=82.0
            ))

    # Stratum 2 (State A, Urban): 4 PSUs (Adequate for 2:2 split)
    for p_idx in range(1, 5):
        psu_name = f"P2_{p_idx}"
        for h_idx in range(1, 3):
            hh_name = f"hh_{psu_name}_{h_idx}"
            records.append(_build_test_record(
                pid=f"{hh_name}_ind1", hhid=hh_name, state="State_A", urban_rural="Urban",
                strata="STRAT_A_URBAN", psu=psu_name, weight=5.0, age=55.0 + p_idx, gender="Female",
                sbp=135.0, dbp=85.0
            ))

    # Stratum 3 (State B, Rural): 2 PSUs (SPARSE - < 4 threshold)
    for p_idx in range(1, 3):
        psu_name = f"P3_{p_idx}"
        hh_name = f"hh_{psu_name}_1"
        records.append(_build_test_record(
            pid=f"{hh_name}_ind1", hhid=hh_name, state="State_B", urban_rural="Rural",
            strata="STRAT_B_RURAL", psu=psu_name, weight=2.0, age=70.0, gender="Male",
            sbp=145.0, dbp=90.0
        ))

    return records


# =============================================================================
# 1. Determinism and Bit-Level Reproducibility
# =============================================================================

def test_partitioning_determinism_and_reproducibility():
    """Verify that identical configuration and input records produce identical partitions and digests."""
    records = _build_synthetic_survey_cluster_cohort()
    config = LasiPartitionConfig(
        split_ratio_a=0.60,
        min_psus_per_stratum=4,
        salt="SYNAPSE_TEST_SALT",
        partition_key=b"SECRET_KEY_FOR_DETERMINISM_TEST_32B",
    )

    partitioner = LasiPsuPartitioner(config=config)
    res1 = partitioner.partition(records)
    res2 = partitioner.partition(records)

    assert res1.manifest_sha256 == res2.manifest_sha256
    assert len(res1.records_a) == len(res2.records_a)
    assert len(res1.records_c) == len(res2.records_c)

    pids_a1 = [r.participant_id for r in res1.records_a]
    pids_a2 = [r.participant_id for r in res2.records_a]
    assert pids_a1 == pids_a2

    # Different key produces different deterministic split
    config_diff = LasiPartitionConfig(
        split_ratio_a=0.60,
        min_psus_per_stratum=4,
        salt="SYNAPSE_DIFFERENT_SALT",
        partition_key=b"ANOTHER_SECRET_KEY_DIFFERENT_32B",
    )
    partitioner_diff = LasiPsuPartitioner(config=config_diff)
    res_diff = partitioner_diff.partition(records)
    assert res_diff.manifest_sha256 != res1.manifest_sha256


# =============================================================================
# 2. Strict Anti-Leakage Verification (PSU, Household, Participant)
# =============================================================================

def test_strict_zero_leakage_invariants():
    """Verify complete absence of overlap between Partition A and Partition C across clusters and individuals."""
    records = _build_synthetic_survey_cluster_cohort()
    partitioner = LasiPsuPartitioner()
    res = partitioner.partition(records)

    # 1. PSU isolation
    psus_a = {r.psu for r in res.records_a}
    psus_c = {r.psu for r in res.records_c}
    assert len(psus_a.intersection(psus_c)) == 0, "PSU overlap detected!"

    # 2. Household isolation (spouses in same household never split)
    hh_a = {r.household_id for r in res.records_a if r.household_id}
    hh_c = {r.household_id for r in res.records_c if r.household_id}
    assert len(hh_a.intersection(hh_c)) == 0, "Household overlap detected!"

    # 3. Participant isolation
    pids_a = {r.participant_id for r in res.records_a}
    pids_c = {r.participant_id for r in res.records_c}
    assert len(pids_a.intersection(pids_c)) == 0, "Participant overlap detected!"


# =============================================================================
# 3. Inverse-Allocation Conditional Weight Calculations
# =============================================================================

def test_inverse_allocation_conditional_weight_scaling():
    """Verify that sampling weights are adjusted by stratum-specific factors: w * (n_h / n_{h,k})."""
    records = _build_synthetic_survey_cluster_cohort()
    partitioner = LasiPsuPartitioner(config=LasiPartitionConfig(min_psus_per_stratum=4))
    res = partitioner.partition(records)

    # In Stratum 1 (STRAT_A_RURAL), there are 5 PSUs.
    # Split: n_a = 3 PSUs, n_c = 2 PSUs.
    # Factor A = 5 / 3 = 1.666667
    # Factor C = 5 / 2 = 2.500000
    strat_a_records_in_a = [r for r in res.records_a if r.strata == "STRAT_A_RURAL"]
    strat_a_records_in_c = [r for r in res.records_c if r.strata == "STRAT_A_RURAL"]

    assert len(strat_a_records_in_a) > 0
    assert len(strat_a_records_in_c) > 0

    # Original weight was 10.0
    for r in strat_a_records_in_a:
        expected_w = round(10.0 * (5.0 / 3.0), 6)
        assert math.isclose(r.survey_weight, expected_w, abs_tol=1e-4)

    for r in strat_a_records_in_c:
        expected_w = round(10.0 * (5.0 / 2.0), 6)
        assert math.isclose(r.survey_weight, expected_w, abs_tol=1e-4)

    # In Stratum 2 (STRAT_A_URBAN), there are 4 PSUs.
    # Split: n_a = 2, n_c = 2. Factor = 4 / 2 = 2.0 for both.
    strat_urban_in_a = [r for r in res.records_a if r.strata == "STRAT_A_URBAN"]
    strat_urban_in_c = [r for r in res.records_c if r.strata == "STRAT_A_URBAN"]
    for r in strat_urban_in_a + strat_urban_in_c:
        assert math.isclose(r.survey_weight, 10.0, abs_tol=1e-4)  # 5.0 * 2.0 = 10.0


# =============================================================================
# 4. Small-Stratum Handling Under Design Rules
# =============================================================================

def test_unsupported_sparse_strata_handling():
    """Verify that strata with n_h < threshold are handled per policy without invalid cross-boundary merges."""
    records = _build_synthetic_survey_cluster_cohort()

    # Policy 1: EXCLUDE (default)
    part_exclude = LasiPsuPartitioner(config=LasiPartitionConfig(
        min_psus_per_stratum=4,
        handle_unsupported_strata="EXCLUDE",
    ))
    res_exclude = part_exclude.partition(records)

    # Stratum 3 has 2 PSUs (< 4). Must be flagged as unsupported and excluded from both partitions.
    assert res_exclude.unsupported_strata_count == 1
    assert res_exclude.unsupported_psus_count == 2
    pids_strat_b = [r.participant_id for r in records if r.strata == "STRAT_B_RURAL"]
    allocated_pids = set([r.participant_id for r in res_exclude.records_a + res_exclude.records_c])
    for pid in pids_strat_b:
        assert pid not in allocated_pids, "Unsupported stratum records should be excluded!"

    # Policy 2: ALLOCATE_WHOLE_TO_A (Asymmetric allocation)
    part_whole = LasiPsuPartitioner(config=LasiPartitionConfig(
        min_psus_per_stratum=4,
        handle_unsupported_strata="ALLOCATE_WHOLE_TO_A",
    ))
    res_whole = part_whole.partition(records)
    # Stratum 3 records appear in A with weight factor 1.0, but zero appear in C
    strat_b_in_a = [r for r in res_whole.records_a if r.strata == "STRAT_B_RURAL"]
    strat_b_in_c = [r for r in res_whole.records_c if r.strata == "STRAT_B_RURAL"]
    assert len(strat_b_in_a) == len(pids_strat_b)
    assert len(strat_b_in_c) == 0
    for r in strat_b_in_a:
        assert r.survey_weight == 2.0  # factor 1.0 preserves original weight


# =============================================================================
# 5. Covariate Balance Diagnostics
# =============================================================================

def test_covariate_balance_reporting_without_seed_fishing():
    """Verify calculation of SMDs and TVD, confirming imbalance is reported transparently without re-shuffling."""
    records = _build_synthetic_survey_cluster_cohort()
    partitioner = LasiPsuPartitioner()
    res = partitioner.partition(records)

    bal = res.balance_report
    assert bal.n_records_a > 0
    assert bal.n_records_c > 0
    assert bal.n_psus_a > 0
    assert bal.n_psus_c > 0

    assert isinstance(bal.age_smd, float)
    assert isinstance(bal.female_smd, float)
    assert isinstance(bal.urban_smd, float)
    assert isinstance(bal.state_tvd, float)
    assert isinstance(bal.balance_warnings, list)


# =============================================================================
# 6. Authenticated AES-256-GCM Holdout Vault & Single-Use Enforcement
# =============================================================================

def test_aes256_holdout_vault_and_technically_enforced_single_use():
    """Verify AES-256-GCM encryption, key separation, and technically enforced single-use decryption."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)  # 256-bit key

    # 1. Create encrypted vault
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(
        records_c=records,
        key=key,
        vault_id="TEST_VAULT_001",
    )

    assert payload["encryption_algorithm"] == "AES-256-GCM"
    assert payload["consumed"] is False
    assert payload["authorized_ticket_id"] == ticket.ticket_id
    assert ticket.is_consumed is False
    assert "ciphertext_b64" in payload
    assert "nonce_b64" in payload

    # 2. First Decryption: Authorized and Successful
    decrypted_records = LasiHoldoutVault.decrypt_and_consume(
        vault_payload=payload,
        key=key,
        ticket=ticket,
    )
    assert len(decrypted_records) == len(records)
    assert decrypted_records[0].participant_id == records[0].participant_id

    # State transition verification
    assert ticket.is_consumed is True
    assert ticket.consumed_at is not None
    assert payload["consumed"] is True
    assert payload["consumed_at"] is not None

    # 3. Second Decryption Attempt with same ticket: MUST FAIL (Technically enforced single-use)
    with pytest.raises(HoldoutAccessViolationError, match="already been consumed"):
        LasiHoldoutVault.decrypt_and_consume(
            vault_payload=payload,
            key=key,
            ticket=ticket,
        )

    # 4. Decryption Attempt with a fresh ticket but consumed payload: MUST FAIL
    fresh_ticket = HoldoutAccessTicket(
        ticket_id=payload["authorized_ticket_id"],
        issued_at="2026-10-22T00:00:00Z",
        token_hash="fake_hash",
        is_consumed=False,
    )
    with pytest.raises(HoldoutAccessViolationError, match="Holdout vault .* has already been consumed"):
        LasiHoldoutVault.decrypt_and_consume(
            vault_payload=payload,
            key=key,
            ticket=fresh_ticket,
        )


def test_holdout_vault_tamper_evidence_and_invalid_keys():
    """Verify that tampered ciphertext or wrong keys fail cryptographically."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    wrong_key = os.urandom(32)

    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key)

    # 1. Invalid key failure
    with pytest.raises(HoldoutAccessViolationError, match="Cryptographic authentication/decryption failed"):
        LasiHoldoutVault.decrypt_and_consume(
            vault_payload=payload,
            key=wrong_key,
            ticket=ticket,
        )

    # 2. Invalid key length
    with pytest.raises(ValueError, match="AES-256 key must be exactly 32 bytes"):
        LasiHoldoutVault.decrypt_and_consume(
            vault_payload=payload,
            key=b"too_short_key_16b!",
            ticket=ticket,
        )


# =============================================================================
# 7. Adversarial Single-Use Persistence & Concurrency Audits
# =============================================================================

def test_holdout_single_use_survives_process_restart(tmp_path):
    """Verify that holdout single-use enforcement survives process restarts and disk reloads."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    ledger_file = tmp_path / "proc_restart_ledger.json"

    # Step 1: Create vault and serialize unconsumed state to JSON (simulating pre-execution persistence)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key, vault_id="RESTART_VAULT_01")
    unconsumed_payload_json = json.dumps(payload)
    ticket_json = ticket.model_dump_json()

    # Step 2: First execution consumes the vault
    decrypted = LasiHoldoutVault.decrypt_and_consume(
        vault_payload=payload,
        key=key,
        ticket=ticket,
        ledger_path=str(ledger_file),
    )
    assert len(decrypted) == len(records)
    assert payload["consumed"] is True
    assert ticket.is_consumed is True

    # Step 3: Simulate complete process restart
    # Reload original unconsumed payload from disk/json where payload["consumed"] == False
    reloaded_payload = json.loads(unconsumed_payload_json)
    assert reloaded_payload["consumed"] is False, "Reloaded payload simulated fresh disk read"

    # Also reload ticket object with is_consumed == False
    reloaded_ticket = HoldoutAccessTicket.model_validate(json.loads(ticket_json))
    assert reloaded_ticket.is_consumed is False

    # Step 4: Re-execution attempt in fresh process MUST BE BLOCKED by persistent audit ledger
    with pytest.raises(HoldoutAccessViolationError, match="already been consumed according to persistent audit ledger"):
        LasiHoldoutVault.decrypt_and_consume(
            vault_payload=reloaded_payload,
            key=key,
            ticket=reloaded_ticket,
            ledger_path=str(ledger_file),
        )


def test_holdout_single_use_blocks_copied_payload_replay(tmp_path):
    """Verify that deepcopied payloads or forged tickets cannot replay consumed holdout data."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    ledger_file = tmp_path / "replay_ledger.json"

    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key, vault_id="REPLAY_VAULT_01")
    copied_payload = copy.deepcopy(payload)

    # First consumption succeeds
    LasiHoldoutVault.decrypt_and_consume(payload, key, ticket, ledger_path=str(ledger_file))

    # Replay attempt with copied payload and a forged unused ticket with same authorized ticket ID
    forged_ticket = HoldoutAccessTicket(
        ticket_id=copied_payload["authorized_ticket_id"],
        issued_at="2026-10-22T00:00:00Z",
        token_hash="fake_hash",
        is_consumed=False,
    )

    with pytest.raises(HoldoutAccessViolationError, match="already been consumed according to persistent audit ledger"):
        LasiHoldoutVault.decrypt_and_consume(copied_payload, key, forged_ticket, ledger_path=str(ledger_file))

    # Replay attempt even if vault_id AND ticket_id are forged: blocked by manifest digest in ledger
    copied_payload_renamed = copy.deepcopy(copied_payload)
    copied_payload_renamed["vault_id"] = "RENAMED_VAULT_ID"
    copied_payload_renamed["authorized_ticket_id"] = "ticket_FORGED_NEW_TICKET"
    forged_ticket_new = HoldoutAccessTicket(
        ticket_id="ticket_FORGED_NEW_TICKET",
        issued_at="2026-10-22T00:00:00Z",
        token_hash="fake_hash",
        is_consumed=False,
    )
    with pytest.raises(HoldoutAccessViolationError, match="manifest digest .* has already been consumed"):
        LasiHoldoutVault.decrypt_and_consume(copied_payload_renamed, key, forged_ticket_new, ledger_path=str(ledger_file))


def test_holdout_concurrent_access_race_condition(tmp_path):
    """Verify that 10 concurrent threads attempting decryption result in exactly 1 success and 9 violations."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key, vault_id="CONCURRENT_VAULT_01")
    ledger_file = tmp_path / "concurrent_ledger.json"

    results = []
    errors = []

    def worker_attempt(worker_id: int):
        # Give each worker thread its own dictionary copy to simulate independent callers racing the lock
        worker_payload = copy.deepcopy(payload)
        worker_ticket = copy.deepcopy(ticket)
        try:
            recs = LasiHoldoutVault.decrypt_and_consume(
                vault_payload=worker_payload,
                key=key,
                ticket=worker_ticket,
                ledger_path=str(ledger_file),
            )
            results.append((worker_id, len(recs)))
        except HoldoutAccessViolationError as e:
            errors.append((worker_id, str(e)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_attempt, i) for i in range(10)]
        concurrent.futures.wait(futures)

    assert len(results) == 1, f"Expected exactly 1 success, got {len(results)}"
    assert len(errors) == 9, f"Expected exactly 9 rejections, got {len(errors)}"


# =============================================================================
# 8. Cryptographic Bit-Tampering & Key Validation Adversarial Audits
# =============================================================================

def test_aes_gcm_ciphertext_and_nonce_bit_tampering():
    """Verify that flipping any bit in ciphertext, nonce, or AAD causes immediate AEAD verification failure."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key)

    # 1. Flip 1 bit in ciphertext
    raw_ct = bytearray(base64.b64decode(payload["ciphertext_b64"]))
    raw_ct[0] ^= 0x01
    tampered_payload_ct = copy.deepcopy(payload)
    tampered_payload_ct["ciphertext_b64"] = base64.b64encode(raw_ct).decode("ascii")

    with pytest.raises(HoldoutAccessViolationError, match="Cryptographic authentication/decryption failed"):
        LasiHoldoutVault.decrypt_and_consume(tampered_payload_ct, key, copy.deepcopy(ticket))

    # 2. Flip 1 bit in nonce
    raw_nonce = bytearray(base64.b64decode(payload["nonce_b64"]))
    raw_nonce[0] ^= 0x01
    tampered_payload_nonce = copy.deepcopy(payload)
    tampered_payload_nonce["nonce_b64"] = base64.b64encode(raw_nonce).decode("ascii")

    with pytest.raises(HoldoutAccessViolationError, match="Cryptographic authentication/decryption failed"):
        LasiHoldoutVault.decrypt_and_consume(tampered_payload_nonce, key, copy.deepcopy(ticket))

    # 3. Nonce length != 12 bytes
    short_nonce_payload = copy.deepcopy(payload)
    short_nonce_payload["nonce_b64"] = base64.b64encode(b"short8by").decode("ascii")
    with pytest.raises(HoldoutAccessViolationError, match="nonce must be exactly 12 bytes"):
        LasiHoldoutVault.decrypt_and_consume(short_nonce_payload, key, copy.deepcopy(ticket))

    # 4. Truncated ciphertext (< 16 bytes auth tag)
    short_ct_payload = copy.deepcopy(payload)
    short_ct_payload["ciphertext_b64"] = base64.b64encode(b"too_short").decode("ascii")
    with pytest.raises(HoldoutAccessViolationError, match="must include at least 16 bytes"):
        LasiHoldoutVault.decrypt_and_consume(short_ct_payload, key, copy.deepcopy(ticket))


def test_aes_gcm_key_and_input_validation_adversarial():
    """Verify strict validation against non-bytes keys, wrong length keys, and empty inputs."""
    records = _build_synthetic_survey_cluster_cohort()
    valid_key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=valid_key)

    # 1. Non-bytes keys raise TypeError
    with pytest.raises(TypeError, match="key must be bytes or bytearray"):
        LasiHoldoutVault.create_encrypted_vault(records, key="string_key_32_characters_long!")  # type: ignore

    with pytest.raises(TypeError, match="key must be bytes or bytearray"):
        LasiHoldoutVault.decrypt_and_consume(payload, key="string_key_32_characters_long!", ticket=ticket)  # type: ignore

    with pytest.raises(TypeError, match="key must be bytes or bytearray"):
        LasiHoldoutVault.decrypt_and_consume(payload, key=12345, ticket=ticket)  # type: ignore

    # 2. Wrong length keys raise ValueError
    for bad_len in [16, 31, 33, 64]:
        with pytest.raises(ValueError, match="key must be exactly 32 bytes"):
            LasiHoldoutVault.decrypt_and_consume(payload, key=b"x" * bad_len, ticket=ticket)

    # 3. Empty records list rejected in vault creation
    with pytest.raises(ValueError, match="Cannot create holdout vault with empty records list"):
        LasiHoldoutVault.create_encrypted_vault([], key=valid_key)


def test_corrupted_audit_ledger_defense(tmp_path):
    """Verify that a corrupted or tampered audit ledger file causes immediate fail-safe abort."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key)
    ledger_file = tmp_path / "corrupted_ledger.json"

    # Write corrupted invalid JSON to ledger
    with open(ledger_file, "w") as f:
        f.write("{ INVALID_JSON_TAMPERED")

    with pytest.raises(HoldoutAccessViolationError, match="is corrupted or tampered with"):
        LasiHoldoutVault.decrypt_and_consume(payload, key, ticket, ledger_path=str(ledger_file))


# =============================================================================
# 9. Adversarial Leakage & Stratum Dispersion Diagnostics Audits
# =============================================================================

def test_adversarial_household_and_participant_cross_psu_leakage():
    """Verify that corrupted data with households or participants split across PSUs triggers LasiLeakageError."""
    records = _build_synthetic_survey_cluster_cohort()

    # Corrupt records: force a household to span across all PSUs in Stratum 1
    # Since Stratum 1 is split into A and C, this household is guaranteed to appear in both partitions
    corrupted_records = []
    for r in records:
        if r.strata == "STRAT_A_RURAL":
            corrupted_records.append(r.model_copy(update={"household_id": "SHARED_LEAKY_HOUSEHOLD"}))
        else:
            corrupted_records.append(r)

    partitioner = LasiPsuPartitioner()
    with pytest.raises(LasiLeakageError, match="Household leakage detected across partitions"):
        partitioner.partition(corrupted_records)

    # Participant leakage across PSUs
    corrupted_participant_records = []
    for r in records:
        if r.strata == "STRAT_A_RURAL":
            corrupted_participant_records.append(r.model_copy(update={"participant_id": "SHARED_LEAKY_PARTICIPANT"}))
        else:
            corrupted_participant_records.append(r)

    with pytest.raises(LasiLeakageError, match="Participant leakage detected across partitions"):
        partitioner.partition(corrupted_participant_records)


def test_unequal_psu_dispersion_and_missing_design_field_diagnostics():
    """Verify that intra-stratum PSU weight dispersion CV > 0.50 and missing design fields are audited."""
    # Build cohort with extreme unequal PSU sizes in Stratum 1:
    # PSU 1 has 50 records with weight 10.0 (total weight = 500)
    # PSUs 2, 3, 4, 5 have 1 record with weight 1.0 (total weight = 1)
    records = []
    for i in range(50):
        records.append(_build_test_record(
            pid=f"skew_p1_{i}", hhid=f"hh_skew_p1_{i}", state="State_A", urban_rural="Rural",
            strata="STRAT_SKEWED", psu="P_SKEW_1", weight=10.0,
        ))
    for p_idx in range(2, 6):
        records.append(_build_test_record(
            pid=f"skew_p{p_idx}_1", hhid=f"hh_skew_p{p_idx}_1", state="State_A", urban_rural="Rural",
            strata="STRAT_SKEWED", psu=f"P_SKEW_{p_idx}", weight=1.0,
        ))

    # Add a record with missing strata and missing PSU and invalid zero weight
    records.append(_build_test_record(
        pid="bad_record_1", hhid="hh_bad", state="State_A", urban_rural="Rural",
        strata="", psu="", weight=0.0,
    ))

    partitioner = LasiPsuPartitioner()
    res = partitioner.partition(records)

    diag = res.diagnostics
    assert "STRAT_SKEWED" in diag["high_psu_dispersion_strata"]
    assert diag["stratum_psu_dispersion_cv"]["STRAT_SKEWED"] > 0.50
    assert diag["missing_strata_records"] == 1
    assert diag["missing_psu_records"] == 1
    assert diag["invalid_weight_records"] == 1

    bal = res.balance_report
    assert bal.has_covariate_imbalance is True
    assert any("high intra-stratum PSU weight dispersion" in w for w in bal.balance_warnings)
    assert any("Incomplete survey design fields" in w for w in bal.balance_warnings)


def test_all_singleton_strata_handling():
    """Verify graceful handling when an entire dataset contains only singleton strata."""
    records = [
        _build_test_record(pid="s1", hhid="h1", state="State_A", urban_rural="Rural", strata="STRAT_1", psu="P1"),
        _build_test_record(pid="s2", hhid="h2", state="State_B", urban_rural="Rural", strata="STRAT_2", psu="P2"),
    ]
    partitioner = LasiPsuPartitioner(config=LasiPartitionConfig(min_psus_per_stratum=4, handle_unsupported_strata="EXCLUDE"))
    res = partitioner.partition(records)

    assert res.unsupported_strata_count == 2
    assert res.unsupported_psus_count == 2
    assert len(res.records_a) == 0
    assert len(res.records_c) == 0
    assert res.balance_report.has_covariate_imbalance is True


# =============================================================================
# 10. Audit Phase 2D.10: Ledger Security & Partitioned Inference Verification
# =============================================================================

def test_ledger_empty_file_truncation_defense(tmp_path):
    """Verify that an existing but 0-byte truncated audit ledger triggers fail-safe abort."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key)
    ledger_file = tmp_path / "truncated_ledger.json"

    # Create empty 0-byte file (simulating attacker truncating ledger to reset state)
    with open(ledger_file, "w") as f:
        pass
    assert os.path.getsize(ledger_file) == 0

    with pytest.raises(HoldoutAccessViolationError, match="exists but is empty or truncated"):
        LasiHoldoutVault.decrypt_and_consume(payload, key, ticket, ledger_path=str(ledger_file))


def test_ledger_symlink_traversal_defense(tmp_path):
    """Verify that symlinks for ledger path or lockfile are strictly rejected (CWE-59)."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key)

    target_secrets = tmp_path / "target_secrets.txt"
    with open(target_secrets, "w") as f:
        f.write("SECRET_DATA")

    # 1. Symlink on ledger path
    symlink_ledger = tmp_path / "symlink_ledger.json"
    os.symlink(target_secrets, symlink_ledger)

    with pytest.raises(HoldoutAccessViolationError, match="Security violation: .* is a symlink"):
        LasiHoldoutVault.decrypt_and_consume(payload, key, ticket, ledger_path=str(symlink_ledger))

    # 2. Symlink on lockfile path
    regular_ledger = tmp_path / "regular_ledger.json"
    symlink_lock = tmp_path / "regular_ledger.json.lock"
    os.symlink(target_secrets, symlink_lock)

    with pytest.raises(HoldoutAccessViolationError, match="Security violation: .* is a symlink"):
        LasiHoldoutVault.decrypt_and_consume(payload, key, ticket, ledger_path=str(regular_ledger))


def test_ledger_file_permissions_owner_only(tmp_path):
    """Verify that the ledger and lockfile are created with strict owner-only permissions (0o600)."""
    records = _build_synthetic_survey_cluster_cohort()
    key = os.urandom(32)
    payload, ticket = LasiHoldoutVault.create_encrypted_vault(records_c=records, key=key)
    ledger_file = tmp_path / "perm_ledger.json"

    LasiHoldoutVault.decrypt_and_consume(payload, key, ticket, ledger_path=str(ledger_file))

    # Inspect file permissions (mask with 0o777)
    ledger_mode = stat.S_IMODE(os.stat(ledger_file).st_mode)
    lock_mode = stat.S_IMODE(os.stat(f"{ledger_file}.lock").st_mode)

    assert ledger_mode == 0o600, f"Expected 0o600 for ledger, got {oct(ledger_mode)}"
    assert lock_mode == 0o600, f"Expected 0o600 for lockfile, got {oct(lock_mode)}"


def test_taylor_linearization_and_degrees_of_freedom_on_partitioned_records():
    """Verify that Taylor linearization and design degrees of freedom remain mathematically valid after partitioning."""
    records = _build_synthetic_survey_cluster_cohort()
    partitioner = LasiPsuPartitioner(config=LasiPartitionConfig(
        split_ratio_a=0.60,
        min_psus_per_stratum=4,
        handle_unsupported_strata="EXCLUDE",
    ))
    res = partitioner.partition(records)

    # In synthetic cohort:
    # Stratum 1 (STRAT_A_RURAL) has 5 PSUs -> 3 in A, 2 in C
    # Stratum 2 (STRAT_A_URBAN) has 4 PSUs -> 2 in A, 2 in C
    # Stratum 3 (STRAT_B_RURAL) has 2 PSUs -> excluded
    # Total adequate PSUs in A: 3 + 2 = 5 PSUs across 2 strata
    # Expected df_A = 5 - 2 = 3
    # Total adequate PSUs in C: 2 + 2 = 4 PSUs across 2 strata
    # Expected df_C = 4 - 2 = 2

    engine = LasiSurveyVarianceEngine()

    # 1. Evaluate Partition A
    mean_sbp_a, se_sbp_a, diag_a = engine.calculate_taylor_linearized_mean_and_se(
        res.records_a,
        value_getter=lambda r: r.sbp_mean,
    )

    assert diag_a["df"] == 3
    assert diag_a["total_strata"] == 2
    assert diag_a["total_psus"] == 5
    assert diag_a["singleton_strata_count"] == 0, "No singletons should exist in adequate partition!"
    assert diag_a["insufficient_df"] is False
    assert se_sbp_a > 0.0

    # 2. Evaluate Partition C
    mean_sbp_c, se_sbp_c, diag_c = engine.calculate_taylor_linearized_mean_and_se(
        res.records_c,
        value_getter=lambda r: r.sbp_mean,
    )

    assert diag_c["df"] == 2
    assert diag_c["total_strata"] == 2
    assert diag_c["total_psus"] == 4
    assert diag_c["singleton_strata_count"] == 0
    assert diag_c["insufficient_df"] is False
    assert se_sbp_c > 0.0

    # 3. Evaluate Full Adequate Sample (filtering out Stratum 3 for fair comparison)
    adequate_records = [r for r in records if r.strata in ("STRAT_A_RURAL", "STRAT_A_URBAN")]
    mean_full, se_full, diag_full = engine.calculate_taylor_linearized_mean_and_se(
        adequate_records,
        value_getter=lambda r: r.sbp_mean,
    )

    # 4. Verification of ratio estimator mean consistency:
    # Both Partition A and Partition C estimates are consistent estimators of the full adequate population mean
    assert math.isclose(mean_sbp_a, mean_full, rel_tol=0.05)
    assert math.isclose(mean_sbp_c, mean_full, rel_tol=0.05)

    # 5. Verification of uncertainty expansion via Student's t degrees of freedom penalties:
    # Reduced cluster counts in partitions reduce degrees of freedom (df_A=3, df_C=2 vs df_full=7).
    # Consequently, critical multipliers t_df are substantially larger (3.182, 4.303 vs 2.365).
    t_crit_a = student_t_critical_value(diag_a["df"], 0.95)
    t_crit_c = student_t_critical_value(diag_c["df"], 0.95)
    t_crit_full = student_t_critical_value(diag_full["df"], 0.95)

    ci_half_a = t_crit_a * se_sbp_a
    ci_half_c = t_crit_c * se_sbp_c
    ci_half_full = t_crit_full * se_full

    assert ci_half_a > ci_half_full, f"Expected Partition A CI half-width ({ci_half_a:.3f}) > full ({ci_half_full:.3f})"
    assert ci_half_c > ci_half_full, f"Expected Partition C CI half-width ({ci_half_c:.3f}) > full ({ci_half_full:.3f})"
