"""
Deterministic PSU-Level Survey Data Partitioner and Cryptographic Holdout Vault.

Implements Milestone 4 Partitioning Architecture:
1. Configurable, deterministic 60/40 PSU-level partitioning (Calibration A / Holdout C).
2. Strict enforcement of zero PSU, household, and participant overlap.
3. Statistically defensible inverse-allocation conditional weight adjustments.
4. Design-consistent small-stratum governance rejecting arbitrary geographic merges.
5. Comprehensive covariate balance diagnostics (Age, Sex, Sector, State, SBP, DBP)
   reporting true observed balance without repeated seed-fishing.
6. Authenticated AES-256-GCM holdout encryption with key separation and technically
   enforced single-use access controls.
"""

import contextlib
from datetime import datetime, timezone
from enum import Enum
import fcntl
import hashlib
import hmac
import json
import math
import os
import base64
import threading
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
from pydantic import BaseModel, Field

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from synapse_simulator.evaluation.lasi.models import LasiCleanedRecord


# =============================================================================
# Exceptions
# =============================================================================

class LasiPartitioningError(Exception):
    """Base exception for survey partitioning failures."""
    pass


class LasiLeakageError(LasiPartitioningError):
    """Raised when PSU, household, or participant leakage across partitions is detected."""
    pass


class LasiUnsupportedStratumError(LasiPartitioningError):
    """Raised when an unsupported sparse stratum cannot be defensibly partitioned."""
    pass


class HoldoutAccessViolationError(Exception):
    """Raised when holdout decryption fails, ticket is re-used, or tampering is detected."""
    pass


# =============================================================================
# Enums and Models
# =============================================================================

class PartitionLabel(str, Enum):
    """Target partition destination for a cluster or respondent."""
    PARTITION_A = "PARTITION_A"  # Calibration and Internal Cluster Cross-Validation
    PARTITION_C = "PARTITION_C"  # Single-Use Independent Holdout External Validation


class StratumSupportStatus(str, Enum):
    """Stratum suitability for intra-stratum cluster partitioning."""
    ADEQUATE = "ADEQUATE"                                    # nh >= threshold (supports >= 2 PSUs in A and C)
    UNSUPPORTED_SPARSE_PSUS = "UNSUPPORTED_SPARSE_PSUS"      # 2 <= nh < threshold (cannot allocate 2 to both)
    UNSUPPORTED_SINGLETON = "UNSUPPORTED_SINGLETON"          # nh == 1 (indivisible)


class LasiPartitionConfig(BaseModel):
    """Configuration for deterministic survey cluster partitioning."""
    split_ratio_a: float = 0.60
    min_psus_per_stratum: int = 4
    salt: str = "SYNAPSE_PHASE2D_PARTITION_SALT_V1"
    partition_key: bytes = Field(default_factory=lambda: b"SYNAPSE_DEFAULT_SECRET_KEY_PARTITIONING_2026")
    handle_unsupported_strata: str = "EXCLUDE"  # "EXCLUDE" or "ALLOCATE_WHOLE_TO_A"

    def model_post_init(self, __context: Any) -> None:
        if self.split_ratio_a <= 0.0 or self.split_ratio_a >= 1.0:
            raise ValueError(f"split_ratio_a must be strictly in (0, 1), got {self.split_ratio_a}")
        if self.min_psus_per_stratum < 2:
            raise ValueError(f"min_psus_per_stratum must be >= 2, got {self.min_psus_per_stratum}")


class LasiClusterAllocation(BaseModel):
    """Detailed allocation outcome for a single Primary Sampling Unit."""
    stratum_id: str
    psu_id: str
    assigned_partition: Optional[PartitionLabel]
    support_status: StratumSupportStatus
    stratum_total_psus: int
    stratum_allocated_psus: int
    conditional_weight_factor: float
    allocation_hash: str


class LasiCovariateBalanceReport(BaseModel):
    """Diagnostic assessment of compositional balance between Partition A and Partition C."""
    n_records_a: int
    n_records_c: int
    n_psus_a: int
    n_psus_c: int
    age_mean_a: float
    age_sd_a: float
    age_mean_c: float
    age_sd_c: float
    age_smd: float
    female_pct_a: float
    female_pct_c: float
    female_smd: float
    urban_pct_a: float
    urban_pct_c: float
    urban_smd: float
    state_tvd: float
    sbp_mean_a: Optional[float] = None
    sbp_mean_c: Optional[float] = None
    sbp_smd: Optional[float] = None
    dbp_mean_a: Optional[float] = None
    dbp_mean_c: Optional[float] = None
    dbp_smd: Optional[float] = None
    has_covariate_imbalance: bool
    balance_warnings: List[str] = Field(default_factory=list)


class LasiPartitionResult(BaseModel):
    """Complete result package of survey dataset partitioning."""
    records_a: List[LasiCleanedRecord]
    records_c: List[LasiCleanedRecord]
    allocations: Dict[str, LasiClusterAllocation]
    balance_report: LasiCovariateBalanceReport
    unsupported_strata_count: int
    unsupported_psus_count: int
    total_input_records: int
    total_input_psus: int
    manifest_sha256: str
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    full_stratum_psu_counts: Dict[str, int] = Field(default_factory=dict)
    stratum_psu_counts_a: Dict[str, int] = Field(default_factory=dict)
    stratum_psu_counts_c: Dict[str, int] = Field(default_factory=dict)

    def get_partition_fpc(
        self,
        partition: PartitionLabel,
        full_fpc_by_stratum: Dict[str, float],
    ) -> Dict[str, float]:
        """Derive mathematically correct partition-specific FPC fractions f_{h,k} = (n_{h,k} / n_h) * f_h.

        Prevents callers from accidentally passing unadjusted full-sample FPC fractions to partitioned data,
        which would artificially deflate variance by (1 - f_h) / (1 - p_{h,k} * f_h) < 1.
        """
        partition_fpc = {}
        for s_id, full_f in full_fpc_by_stratum.items():
            n_h = self.full_stratum_psu_counts.get(s_id, 0)
            if n_h <= 0:
                partition_fpc[s_id] = 0.0
                continue
            if partition == PartitionLabel.PARTITION_A:
                n_k = self.stratum_psu_counts_a.get(s_id, 0)
            elif partition == PartitionLabel.PARTITION_C:
                n_k = self.stratum_psu_counts_c.get(s_id, 0)
            else:
                n_k = 0
            p_k = float(n_k) / float(n_h)
            partition_fpc[s_id] = round(max(0.0, min(1.0, full_f * p_k)), 8)
        return partition_fpc



# =============================================================================
# Cryptographic Single-Use Holdout Vault & Persistent Audit Ledger
# =============================================================================

_GLOBAL_LEDGER_LOCK = threading.Lock()


class HoldoutAuditLedger:
    """Persistent, cross-process, thread-safe audit ledger enforcing single-use holdout consumption.

    Enforces single-use holdout access across:
    1. Process restarts: Ledgers are written durably to disk with atomic file replacement.
    2. Copied payloads and replayed tickets: Tracks consumed vault_id, ticket_id, and manifest_sha256.
    3. Concurrent access: Coordinates execution via intra-process thread mutex and cross-process fcntl.flock.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        if ledger_path is None:
            ledger_path = os.environ.get("SYNAPSE_HOLDOUT_LEDGER_PATH", ".synapse_holdout_audit_ledger.json")
        self.ledger_path = ledger_path
        self._is_memory = (ledger_path == ":memory:")
        self._memory_data: Dict[str, Any] = {
            "consumed_vaults": {},
            "consumed_tickets": {},
            "consumed_manifests": {},
        }

    @contextlib.contextmanager
    def lock_session(self):
        """Context manager providing intra-process thread mutex and cross-process fcntl.flock."""
        with _GLOBAL_LEDGER_LOCK:
            if self._is_memory:
                yield self._memory_data, lambda updated: self._memory_data.update(updated)
                return

            # Symlink traversal defense (CWE-59): Reject symlinks for audit ledger or lockfile
            if os.path.islink(self.ledger_path):
                raise HoldoutAccessViolationError(
                    f"Security violation: Audit ledger path '{self.ledger_path}' is a symlink. Symlinks are strictly prohibited."
                )

            dir_name = os.path.dirname(self.ledger_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            lock_file_path = f"{self.ledger_path}.lock"
            if os.path.islink(lock_file_path):
                raise HoldoutAccessViolationError(
                    f"Security violation: Lockfile path '{lock_file_path}' is a symlink. Symlinks are strictly prohibited."
                )

            # Restrict lockfile permissions to owner-only (0o600, CWE-732)
            raw_lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR, 0o600)
            lock_fd = os.fdopen(raw_lock_fd, "a+")
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
                ledger_data: Dict[str, Any] = {
                    "consumed_vaults": {},
                    "consumed_tickets": {},
                    "consumed_manifests": {},
                }
                if os.path.exists(self.ledger_path):
                    with open(self.ledger_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if not content:
                            # Truncation defense: An existing empty ledger indicates truncation/tampering
                            raise HoldoutAccessViolationError(
                                f"Audit ledger file '{self.ledger_path}' exists but is empty or truncated. "
                                "Aborting holdout access to prevent security bypass."
                            )
                        try:
                            ledger_data = json.loads(content)
                        except Exception as err:
                            raise HoldoutAccessViolationError(
                                f"Audit ledger file '{self.ledger_path}' is corrupted or tampered with: {str(err)}. "
                                "Aborting holdout access to preserve audit integrity."
                            )

                def commit(updated_data: Dict[str, Any]) -> None:
                    temp_path = f"{self.ledger_path}.tmp.{os.getpid()}.{threading.get_ident()}"
                    try:
                        # Write with owner-only permissions (0o600)
                        raw_temp_fd = os.open(temp_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
                        with open(raw_temp_fd, "w", encoding="utf-8") as tf:
                            json.dump(updated_data, tf, indent=2, sort_keys=True)
                            tf.flush()
                            os.fsync(tf.fileno())
                        os.replace(temp_path, self.ledger_path)
                        try:
                            os.chmod(self.ledger_path, 0o600)
                        except Exception:
                            pass
                    except Exception:
                        if os.path.exists(temp_path):
                            try:
                                os.unlink(temp_path)
                            except Exception:
                                pass
                        raise

                yield ledger_data, commit
            finally:
                try:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
                lock_fd.close()


class HoldoutAccessTicket(BaseModel):
    """Cryptographic authorization ticket for single-use holdout decryption."""
    ticket_id: str
    issued_at: str
    token_hash: str
    is_consumed: bool = False
    consumed_at: Optional[str] = None

    def mark_consumed(self) -> None:
        if self.is_consumed:
            raise HoldoutAccessViolationError(f"Ticket {self.ticket_id} has already been consumed.")
        self.is_consumed = True
        self.consumed_at = datetime.now(timezone.utc).isoformat()


class LasiHoldoutVault:
    """AES-256-GCM Authenticated Encryption Enclave with Technically Enforced Single-Use Access."""

    @staticmethod
    def create_encrypted_vault(
        records_c: List[LasiCleanedRecord],
        key: bytes,
        vault_id: str = "SYNAPSE_HOLDOUT_VAULT_V1",
    ) -> Tuple[Dict[str, Any], HoldoutAccessTicket]:
        """Encrypt holdout Partition C records using AES-256-GCM and issue a single-use access ticket.

        Args:
            records_c: List of holdout records to protect.
            key: 256-bit (32-byte) secret encryption key.
            vault_id: Identifier for authenticated associated data.

        Returns:
            (vault_payload, access_ticket)
        """
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError(f"AES-256 key must be bytes or bytearray, got {type(key).__name__}")
        if len(key) != 32:
            raise ValueError(f"AES-256 key must be exactly 32 bytes (256 bits), got {len(key)}")

        if not records_c:
            raise ValueError("Cannot create holdout vault with empty records list.")

        # Serialize records to canonical JSON bytes
        records_dicts = [r.model_dump() for r in records_c]
        raw_bytes = json.dumps(records_dicts, sort_keys=True).encode("utf-8")
        manifest_digest = hashlib.sha256(raw_bytes).hexdigest()

        # Generate 96-bit (12-byte) unique cryptographic nonce per NIST SP 800-38D
        nonce = os.urandom(12)
        aad = vault_id.encode("utf-8")

        aesgcm = AESGCM(key)
        # AESGCM.encrypt appends the 16-byte authentication tag to ciphertext
        ciphertext_and_tag = aesgcm.encrypt(nonce, raw_bytes, aad)

        # Issue single-use access ticket
        now_iso = datetime.now(timezone.utc).isoformat()
        ticket_seed = os.urandom(32)
        ticket_id = f"ticket_{hashlib.sha256(ticket_seed).hexdigest()[:16]}"
        token_hash = hashlib.sha256(ticket_seed + aad).hexdigest()

        ticket = HoldoutAccessTicket(
            ticket_id=ticket_id,
            issued_at=now_iso,
            token_hash=token_hash,
            is_consumed=False,
        )

        vault_payload = {
            "vault_id": vault_id,
            "encryption_algorithm": "AES-256-GCM",
            "created_at": now_iso,
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_b64": base64.b64encode(ciphertext_and_tag).decode("ascii"),
            "records_count": len(records_c),
            "manifest_sha256": manifest_digest,
            "consumed": False,
            "consumed_at": None,
            "authorized_ticket_id": ticket_id,
        }

        return vault_payload, ticket

    @staticmethod
    def decrypt_and_consume(
        vault_payload: Dict[str, Any],
        key: bytes,
        ticket: HoldoutAccessTicket,
        ledger: Optional[HoldoutAuditLedger] = None,
        ledger_path: Optional[str] = None,
    ) -> List[LasiCleanedRecord]:
        """Decrypt holdout Partition C records, enforcing strict single-use access.

        Technical Enforcement:
            1. In-memory checks: If ticket or vault payload is already marked consumed, abort immediately.
            2. Cryptographic key validation: Strictly enforce key is bytes/bytearray of length 32.
            3. Persistent ledger checks under cross-process fcntl.flock & thread lock:
               Verify ticket_id, vault_id, and manifest_sha256 have not been consumed across any process.
            4. Nonce validation: Strictly enforce 96-bit (12-byte) nonce per NIST SP 800-38D.
            5. Authenticated decryption: AES-256-GCM authenticated decryption with AAD=vault_id.
            6. Integrity digest verification: SHA-256 digest of decrypted bytes must match manifest_sha256.
            7. Atomic ledger update: Commit consumption record before releasing lock.
            8. Zeroization: Plaintext memory buffer is explicitly zeroed out after parsing.

        Returns:
            List of authenticated LasiCleanedRecord objects.
        """
        # Enforcement 1: In-memory ticket check
        if ticket.is_consumed:
            raise HoldoutAccessViolationError(
                f"Access ticket {ticket.ticket_id} has already been consumed at {ticket.consumed_at}. "
                "Single-use policy strictly violated."
            )

        # Enforcement 2: In-memory vault payload check
        if vault_payload.get("consumed", False):
            raise HoldoutAccessViolationError(
                f"Holdout vault {vault_payload.get('vault_id')} has already been consumed at "
                f"{vault_payload.get('consumed_at')}. Re-access to holdout data is strictly prohibited."
            )

        # Enforcement 3: Ticket authorization matching
        if ticket.ticket_id != vault_payload.get("authorized_ticket_id"):
            raise HoldoutAccessViolationError("Ticket ID does not match vault authorized ticket.")

        # Enforcement 4: Key validation
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError(f"AES-256 key must be bytes or bytearray, got {type(key).__name__}")
        if len(key) != 32:
            raise ValueError(f"AES-256 key must be exactly 32 bytes (256 bits), got {len(key)}")

        # Enforcement 5: Required payload fields check
        required_fields = ["nonce_b64", "ciphertext_b64", "vault_id", "manifest_sha256"]
        for field in required_fields:
            if field not in vault_payload:
                raise HoldoutAccessViolationError(f"Vault payload missing required field: {field}")

        vault_id = str(vault_payload["vault_id"])
        ticket_id = ticket.ticket_id
        manifest_sha = str(vault_payload["manifest_sha256"])

        # Resolve ledger
        if ledger is None:
            ledger = HoldoutAuditLedger(ledger_path=ledger_path)

        with ledger.lock_session() as (ledger_data, commit_ledger):
            # Check persistent ledger records
            if ticket_id in ledger_data.get("consumed_tickets", {}):
                rec = ledger_data["consumed_tickets"][ticket_id]
                raise HoldoutAccessViolationError(
                    f"Access ticket {ticket_id} has already been consumed according to persistent audit ledger "
                    f"at {rec.get('consumed_at')}. Single-use policy strictly violated."
                )

            if vault_id in ledger_data.get("consumed_vaults", {}):
                rec = ledger_data["consumed_vaults"][vault_id]
                raise HoldoutAccessViolationError(
                    f"Holdout vault {vault_id} has already been consumed according to persistent audit ledger "
                    f"at {rec.get('consumed_at')}. Re-access to holdout data is strictly prohibited."
                )

            if manifest_sha in ledger_data.get("consumed_manifests", {}):
                rec = ledger_data["consumed_manifests"][manifest_sha]
                raise HoldoutAccessViolationError(
                    f"Holdout data with manifest digest {manifest_sha} has already been consumed "
                    f"according to persistent audit ledger at {rec.get('consumed_at')}. Replay attempt blocked."
                )

            # Decode nonce and ciphertext
            try:
                nonce = base64.b64decode(vault_payload["nonce_b64"])
                ciphertext = base64.b64decode(vault_payload["ciphertext_b64"])
            except Exception as e:
                raise HoldoutAccessViolationError(f"Base64 decoding failed for vault payload: {str(e)}")

            if len(nonce) != 12:
                raise HoldoutAccessViolationError(
                    f"AES-GCM nonce must be exactly 12 bytes (96 bits) per NIST SP 800-38D, got {len(nonce)}"
                )

            if len(ciphertext) < 16:
                raise HoldoutAccessViolationError(
                    f"Ciphertext is truncated; must include at least 16 bytes for the GCM authentication tag, got {len(ciphertext)}"
                )

            aad = vault_id.encode("utf-8")

            # Decrypt with AES-256-GCM
            try:
                aesgcm = AESGCM(key)
                decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, aad)
            except Exception as e:
                raise HoldoutAccessViolationError(f"Cryptographic authentication/decryption failed: {str(e)}")

            # Verify integrity
            computed_sha = hashlib.sha256(decrypted_bytes).hexdigest()
            if computed_sha != manifest_sha:
                raise HoldoutAccessViolationError(
                    f"Integrity check failed: manifest digest mismatch (computed {computed_sha} != expected {manifest_sha})."
                )

            # Record consumption atomically in ledger
            now_iso = datetime.now(timezone.utc).isoformat()
            consumption_entry = {
                "vault_id": vault_id,
                "ticket_id": ticket_id,
                "manifest_sha256": manifest_sha,
                "consumed_at": now_iso,
                "records_count": vault_payload.get("records_count", 0),
            }
            ledger_data.setdefault("consumed_vaults", {})[vault_id] = consumption_entry
            ledger_data.setdefault("consumed_tickets", {})[ticket_id] = consumption_entry
            ledger_data.setdefault("consumed_manifests", {})[manifest_sha] = consumption_entry

            commit_ledger(ledger_data)

            # Update in-memory objects
            ticket.mark_consumed()
            vault_payload["consumed"] = True
            vault_payload["consumed_at"] = now_iso

            # Parse records and zeroize raw buffer
            decrypted_buf = bytearray(decrypted_bytes)
            try:
                records_dicts = json.loads(decrypted_buf.decode("utf-8"))
            finally:
                for i in range(len(decrypted_buf)):
                    decrypted_buf[i] = 0

            return [LasiCleanedRecord.model_validate(d) for d in records_dicts]


# =============================================================================
# Deterministic Survey Partitioner
# =============================================================================

class LasiPsuPartitioner:
    """Deterministic, cluster-level 60/40 survey partitioner with strict anti-leakage guarantees."""

    def __init__(self, config: Optional[LasiPartitionConfig] = None):
        self.config = config or LasiPartitionConfig()

    def partition(self, records: List[LasiCleanedRecord]) -> LasiPartitionResult:
        """Partition survey microdata at the Primary Sampling Unit (PSU) cluster level.

        Execution Pipeline:
            1. Discover all unique clusters: (strata, psu).
            2. Audit stratum topology and identify small/singleton strata.
            3. Apply design-consistent allocation using HMAC-SHA256 deterministic ordering.
            4. Compute stratum-specific inverse-allocation weights: w_hij * (n_h / n_{h,k}).
            5. Enforce strict anti-leakage invariants (zero PSU, HH, participant overlap).
            6. Compute covariate balance diagnostics without re-shuffling.
        """
        if not records:
            raise LasiPartitioningError("Cannot partition empty record list.")

        # Step 1: Group records by stratum and PSU
        strata_psus: Dict[str, Set[str]] = defaultdict(set)
        psu_records: Dict[Tuple[str, str], List[LasiCleanedRecord]] = defaultdict(list)
        psu_households: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        psu_participants: Dict[Tuple[str, str], Set[str]] = defaultdict(set)

        missing_strata_count = sum(
            1 for r in records
            if not r.strata or not str(r.strata).strip() or str(r.strata).strip().upper() in ("UNKNOWN_STRATUM", "NONE", "NAN")
        )
        missing_psu_count = sum(
            1 for r in records
            if not r.psu or not str(r.psu).strip() or str(r.psu).strip().upper() in ("UNKNOWN_PSU", "NONE", "NAN")
        )
        invalid_weight_count = sum(
            1 for r in records
            if r.survey_weight is None or r.survey_weight <= 0.0 or math.isnan(r.survey_weight)
        )

        for r in records:
            s_id = str(r.strata or "UNKNOWN_STRATUM").strip()
            p_id = str(r.psu or "UNKNOWN_PSU").strip()
            key = (s_id, p_id)
            strata_psus[s_id].add(p_id)
            psu_records[key].append(r)
            if r.household_id:
                psu_households[key].add(r.household_id)
            psu_participants[key].add(r.participant_id)

        total_psus = sum(len(ps) for ps in strata_psus.values())

        # Audit intra-stratum PSU aggregate weight dispersion (CV)
        stratum_psu_cvs: Dict[str, float] = {}
        high_dispersion_strata: List[str] = []

        for s_id, psus in sorted(strata_psus.items()):
            if len(psus) > 1:
                psu_weights = []
                for p_id in sorted(psus):
                    pw = sum(r.survey_weight for r in psu_records[(s_id, p_id)] if r.survey_weight and r.survey_weight > 0.0)
                    psu_weights.append(pw)
                mean_pw = sum(psu_weights) / len(psu_weights)
                if mean_pw > 0.0:
                    var_pw = sum((x - mean_pw) ** 2 for x in psu_weights) / (len(psu_weights) - 1)
                    cv_pw = math.sqrt(var_pw) / mean_pw
                else:
                    cv_pw = 0.0
                stratum_psu_cvs[s_id] = round(cv_pw, 4)
                if cv_pw > 0.50:
                    high_dispersion_strata.append(s_id)

        # Step 2: Stratum topology inspection and deterministic allocation
        allocations: Dict[str, LasiClusterAllocation] = {}
        unsupported_strata_count = 0
        unsupported_psus_count = 0

        for s_id, psus in sorted(strata_psus.items()):
            n_h = len(psus)

            # Check support threshold
            if n_h < self.config.min_psus_per_stratum:
                unsupported_strata_count += 1
                unsupported_psus_count += n_h
                support_status = (
                    StratumSupportStatus.UNSUPPORTED_SINGLETON
                    if n_h == 1
                    else StratumSupportStatus.UNSUPPORTED_SPARSE_PSUS
                )

                if self.config.handle_unsupported_strata == "EXCLUDE":
                    for p_id in sorted(psus):
                        alloc_key = f"{s_id}:{p_id}"
                        allocations[alloc_key] = LasiClusterAllocation(
                            stratum_id=s_id,
                            psu_id=p_id,
                            assigned_partition=None,
                            support_status=support_status,
                            stratum_total_psus=n_h,
                            stratum_allocated_psus=0,
                            conditional_weight_factor=0.0,
                            allocation_hash="",
                        )
                elif self.config.handle_unsupported_strata == "ALLOCATE_WHOLE_TO_A":
                    for p_id in sorted(psus):
                        alloc_key = f"{s_id}:{p_id}"
                        allocations[alloc_key] = LasiClusterAllocation(
                            stratum_id=s_id,
                            psu_id=p_id,
                            assigned_partition=PartitionLabel.PARTITION_A,
                            support_status=support_status,
                            stratum_total_psus=n_h,
                            stratum_allocated_psus=n_h,
                            conditional_weight_factor=1.0,
                            allocation_hash="WHOLE_STRATUM_A",
                        )
                else:
                    raise LasiUnsupportedStratumError(
                        f"Stratum {s_id} has {n_h} PSUs (< threshold {self.config.min_psus_per_stratum}). "
                        "Splitting within stratum is unsupported."
                    )
            else:
                # Adequate stratum: deterministic allocation
                support_status = StratumSupportStatus.ADEQUATE

                # Compute deterministic hashes for each PSU
                psu_hashes: List[Tuple[str, str]] = []
                for p_id in sorted(psus):
                    msg = f"{s_id}:{p_id}:{self.config.salt}".encode("utf-8")
                    digest = hmac.new(self.config.partition_key, msg, hashlib.sha256).hexdigest()
                    psu_hashes.append((digest, p_id))

                # Sort PSUs by cryptographic digest
                psu_hashes.sort(key=lambda x: x[0])

                # Determine target counts guaranteeing at least 2 PSUs in A and at least 2 in C
                n_a = max(2, min(n_h - 2, int(round(n_h * self.config.split_ratio_a))))
                n_c = n_h - n_a

                # Inverse-allocation conditional weight factors
                factor_a = n_h / float(n_a)
                factor_c = n_h / float(n_c)

                # Assign top n_a to Partition A
                for digest, p_id in psu_hashes[:n_a]:
                    alloc_key = f"{s_id}:{p_id}"
                    allocations[alloc_key] = LasiClusterAllocation(
                        stratum_id=s_id,
                        psu_id=p_id,
                        assigned_partition=PartitionLabel.PARTITION_A,
                        support_status=support_status,
                        stratum_total_psus=n_h,
                        stratum_allocated_psus=n_a,
                        conditional_weight_factor=round(factor_a, 6),
                        allocation_hash=digest,
                    )

                # Assign remaining n_c to Partition C
                for digest, p_id in psu_hashes[n_a:]:
                    alloc_key = f"{s_id}:{p_id}"
                    allocations[alloc_key] = LasiClusterAllocation(
                        stratum_id=s_id,
                        psu_id=p_id,
                        assigned_partition=PartitionLabel.PARTITION_C,
                        support_status=support_status,
                        stratum_total_psus=n_h,
                        stratum_allocated_psus=n_c,
                        conditional_weight_factor=round(factor_c, 6),
                        allocation_hash=digest,
                    )

        # Step 3: Record partitioning and conditional weight application
        records_a: List[LasiCleanedRecord] = []
        records_c: List[LasiCleanedRecord] = []

        for r in records:
            s_id = str(r.strata or "UNKNOWN_STRATUM").strip()
            p_id = str(r.psu or "UNKNOWN_PSU").strip()
            alloc_key = f"{s_id}:{p_id}"
            alloc = allocations.get(alloc_key)

            if alloc is None or alloc.assigned_partition is None:
                continue

            # Compute adjusted weight
            adj_weight = None
            if r.survey_weight is not None and r.survey_weight > 0.0:
                adj_weight = round(r.survey_weight * alloc.conditional_weight_factor, 6)

            updated_record = r.model_copy(update={
                "survey_weight": adj_weight,
                "has_valid_survey_weight": (adj_weight is not None and adj_weight > 0.0),
                "partition_label": alloc.assigned_partition.value,
            })

            if alloc.assigned_partition == PartitionLabel.PARTITION_A:
                records_a.append(updated_record)
            elif alloc.assigned_partition == PartitionLabel.PARTITION_C:
                records_c.append(updated_record)

        # Step 4: Strict Anti-Leakage Assertions
        psus_in_a = {alloc.psu_id for alloc in allocations.values() if alloc.assigned_partition == PartitionLabel.PARTITION_A}
        psus_in_c = {alloc.psu_id for alloc in allocations.values() if alloc.assigned_partition == PartitionLabel.PARTITION_C}
        psu_overlap = psus_in_a.intersection(psus_in_c)
        if psu_overlap:
            raise LasiLeakageError(f"PSU leakage detected across partitions: {psu_overlap}")

        hh_in_a = {r.household_id for r in records_a if r.household_id}
        hh_in_c = {r.household_id for r in records_c if r.household_id}
        hh_overlap = hh_in_a.intersection(hh_in_c)
        if hh_overlap:
            raise LasiLeakageError(f"Household leakage detected across partitions: {hh_overlap}")

        pid_in_a = {r.participant_id for r in records_a}
        pid_in_c = {r.participant_id for r in records_c}
        pid_overlap = pid_in_a.intersection(pid_in_c)
        if pid_overlap:
            raise LasiLeakageError(f"Participant leakage detected across partitions: {pid_overlap}")

        # Step 5: Covariate Balance Diagnostics
        balance_report = self._compute_covariate_balance(records_a, records_c, len(psus_in_a), len(psus_in_c))

        # Population Total Estimation & Divergence Audit
        pop_input = sum(r.survey_weight for r in records if r.survey_weight and r.survey_weight > 0.0)
        pop_a = sum(r.survey_weight for r in records_a if r.survey_weight and r.survey_weight > 0.0)
        pop_c = sum(r.survey_weight for r in records_c if r.survey_weight and r.survey_weight > 0.0)

        div_a = (abs(pop_a - pop_input) / pop_input) if pop_input > 0 else 0.0
        div_c = (abs(pop_c - pop_input) / pop_input) if pop_input > 0 else 0.0

        if missing_strata_count > 0 or missing_psu_count > 0:
            balance_report.balance_warnings.append(
                f"Incomplete survey design fields: {missing_strata_count} records missing strata, "
                f"{missing_psu_count} records missing PSU."
            )
            balance_report.has_covariate_imbalance = True

        if high_dispersion_strata:
            balance_report.balance_warnings.append(
                f"{len(high_dispersion_strata)} strata exhibit high intra-stratum PSU weight dispersion (CV > 0.50): "
                f"{high_dispersion_strata[:3]}. Unequal PSU sizes may cause partition sample total discrepancy."
            )
            balance_report.has_covariate_imbalance = True

        if div_a >= 0.10:
            balance_report.balance_warnings.append(
                f"Estimated population total in Partition A diverges by {div_a * 100.0:.2f}% from input total."
            )
            balance_report.has_covariate_imbalance = True

        if div_c >= 0.10:
            balance_report.balance_warnings.append(
                f"Estimated population total in Partition C diverges by {div_c * 100.0:.2f}% from input total."
            )
            balance_report.has_covariate_imbalance = True

        # Compute SHA-256 Manifest
        alloc_summary = {k: v.model_dump() for k, v in sorted(allocations.items())}
        manifest_digest = hashlib.sha256(json.dumps(alloc_summary, sort_keys=True).encode("utf-8")).hexdigest()

        diagnostics = {
            "total_input_records": len(records),
            "total_input_psus": total_psus,
            "allocated_records_a": len(records_a),
            "allocated_records_c": len(records_c),
            "allocated_psus_a": len(psus_in_a),
            "allocated_psus_c": len(psus_in_c),
            "unsupported_strata_count": unsupported_strata_count,
            "unsupported_psus_count": unsupported_psus_count,
            "unsupported_handling": self.config.handle_unsupported_strata,
            "missing_strata_records": missing_strata_count,
            "missing_psu_records": missing_psu_count,
            "invalid_weight_records": invalid_weight_count,
            "high_psu_dispersion_strata": high_dispersion_strata,
            "stratum_psu_dispersion_cv": stratum_psu_cvs,
            "estimated_pop_total_input": round(pop_input, 2),
            "estimated_pop_total_a": round(pop_a, 2),
            "estimated_pop_total_c": round(pop_c, 2),
            "pop_total_divergence_pct_a": round(div_a * 100.0, 2),
            "pop_total_divergence_pct_c": round(div_c * 100.0, 2),
        }

        full_psu_counts_map = {s_id: len(ps) for s_id, ps in strata_psus.items()}
        psu_counts_a_map: Dict[str, int] = defaultdict(int)
        psu_counts_c_map: Dict[str, int] = defaultdict(int)
        for alloc in allocations.values():
            if alloc.assigned_partition == PartitionLabel.PARTITION_A:
                psu_counts_a_map[alloc.stratum_id] += 1
            elif alloc.assigned_partition == PartitionLabel.PARTITION_C:
                psu_counts_c_map[alloc.stratum_id] += 1

        return LasiPartitionResult(
            records_a=records_a,
            records_c=records_c,
            allocations=allocations,
            balance_report=balance_report,
            unsupported_strata_count=unsupported_strata_count,
            unsupported_psus_count=unsupported_psus_count,
            total_input_records=len(records),
            total_input_psus=total_psus,
            manifest_sha256=manifest_digest,
            diagnostics=diagnostics,
            full_stratum_psu_counts=full_psu_counts_map,
            stratum_psu_counts_a=dict(psu_counts_a_map),
            stratum_psu_counts_c=dict(psu_counts_c_map),
        )

    def _compute_covariate_balance(
        self,
        records_a: List[LasiCleanedRecord],
        records_c: List[LasiCleanedRecord],
        n_psus_a: int,
        n_psus_c: int,
    ) -> LasiCovariateBalanceReport:
        """Compute standardized mean differences and distributional distances across covariates."""
        warnings: List[str] = []

        if not records_a or not records_c:
            return LasiCovariateBalanceReport(
                n_records_a=len(records_a),
                n_records_c=len(records_c),
                n_psus_a=n_psus_a,
                n_psus_c=n_psus_c,
                age_mean_a=0.0, age_sd_a=0.0, age_mean_c=0.0, age_sd_c=0.0, age_smd=0.0,
                female_pct_a=0.0, female_pct_c=0.0, female_smd=0.0,
                urban_pct_a=0.0, urban_pct_c=0.0, urban_smd=0.0,
                state_tvd=0.0, has_covariate_imbalance=True,
                balance_warnings=["Empty partition encountered; balance cannot be evaluated."],
            )

        # 1. Age SMD
        ages_a = [r.age for r in records_a if r.age is not None]
        ages_c = [r.age for r in records_c if r.age is not None]
        mean_age_a = sum(ages_a) / max(1, len(ages_a))
        mean_age_c = sum(ages_c) / max(1, len(ages_c))
        var_age_a = sum((x - mean_age_a) ** 2 for x in ages_a) / max(1, len(ages_a) - 1)
        var_age_c = sum((x - mean_age_c) ** 2 for x in ages_c) / max(1, len(ages_c) - 1)
        pooled_sd_age = math.sqrt(max(1e-9, (var_age_a + var_age_c) / 2.0))
        age_smd = round(abs(mean_age_a - mean_age_c) / pooled_sd_age, 4)

        if age_smd >= 0.10:
            warnings.append(f"Age imbalance: SMD = {age_smd:.4f} >= 0.10 threshold.")

        # 2. Female Proportion SMD
        females_a = sum(1 for r in records_a if str(r.gender).strip().lower() in ("female", "f", "2"))
        females_c = sum(1 for r in records_c if str(r.gender).strip().lower() in ("female", "f", "2"))
        p_fem_a = females_a / len(records_a)
        p_fem_c = females_c / len(records_c)
        var_fem = max(1e-9, (p_fem_a * (1.0 - p_fem_a) + p_fem_c * (1.0 - p_fem_c)) / 2.0)
        female_smd = round(abs(p_fem_a - p_fem_c) / math.sqrt(var_fem), 4)

        if female_smd >= 0.10:
            warnings.append(f"Sex imbalance: Female SMD = {female_smd:.4f} >= 0.10 threshold.")

        # 3. Urban Sector SMD
        urban_a = sum(1 for r in records_a if str(r.urban_rural).strip().lower() == "urban")
        urban_c = sum(1 for r in records_c if str(r.urban_rural).strip().lower() == "urban")
        p_urb_a = urban_a / len(records_a)
        p_urb_c = urban_c / len(records_c)
        var_urb = max(1e-9, (p_urb_a * (1.0 - p_urb_a) + p_urb_c * (1.0 - p_urb_c)) / 2.0)
        urban_smd = round(abs(p_urb_a - p_urb_c) / math.sqrt(var_urb), 4)

        if urban_smd >= 0.10:
            warnings.append(f"Sector imbalance: Urban SMD = {urban_smd:.4f} >= 0.10 threshold.")

        # 4. State Total Variation Distance (TVD)
        states_all = set([r.state for r in records_a if r.state] + [r.state for r in records_c if r.state])
        tvd_sum = 0.0
        for s in states_all:
            prop_a = sum(1 for r in records_a if r.state == s) / len(records_a)
            prop_c = sum(1 for r in records_c if r.state == s) / len(records_c)
            tvd_sum += abs(prop_a - prop_c)
        state_tvd = round(0.5 * tvd_sum, 4)

        if state_tvd >= 0.08:
            warnings.append(f"State distribution divergence: TVD = {state_tvd:.4f} >= 0.08 threshold.")

        # 5. SBP and DBP SMD (if valid vitals exist)
        sbp_a = [r.sbp_mean for r in records_a if r.sbp_mean is not None and not math.isnan(r.sbp_mean)]
        sbp_c = [r.sbp_mean for r in records_c if r.sbp_mean is not None and not math.isnan(r.sbp_mean)]
        sbp_smd = None
        mean_sbp_a = round(sum(sbp_a) / len(sbp_a), 2) if sbp_a else None
        mean_sbp_c = round(sum(sbp_c) / len(sbp_c), 2) if sbp_c else None
        if sbp_a and sbp_c:
            var_sbp_a = sum((x - mean_sbp_a) ** 2 for x in sbp_a) / max(1, len(sbp_a) - 1)
            var_sbp_c = sum((x - mean_sbp_c) ** 2 for x in sbp_c) / max(1, len(sbp_c) - 1)
            sbp_smd = round(abs(mean_sbp_a - mean_sbp_c) / math.sqrt(max(1e-9, (var_sbp_a + var_sbp_c) / 2.0)), 4)
            if sbp_smd >= 0.10:
                warnings.append(f"Baseline SBP imbalance: SMD = {sbp_smd:.4f} >= 0.10 threshold.")

        dbp_a = [r.dbp_mean for r in records_a if r.dbp_mean is not None and not math.isnan(r.dbp_mean)]
        dbp_c = [r.dbp_mean for r in records_c if r.dbp_mean is not None and not math.isnan(r.dbp_mean)]
        dbp_smd = None
        mean_dbp_a = round(sum(dbp_a) / len(dbp_a), 2) if dbp_a else None
        mean_dbp_c = round(sum(dbp_c) / len(dbp_c), 2) if dbp_c else None
        if dbp_a and dbp_c:
            var_dbp_a = sum((x - mean_dbp_a) ** 2 for x in dbp_a) / max(1, len(dbp_a) - 1)
            var_dbp_c = sum((x - mean_dbp_c) ** 2 for x in dbp_c) / max(1, len(dbp_c) - 1)
            dbp_smd = round(abs(mean_dbp_a - mean_dbp_c) / math.sqrt(max(1e-9, (var_dbp_a + var_dbp_c) / 2.0)), 4)
            if dbp_smd >= 0.10:
                warnings.append(f"Baseline DBP imbalance: SMD = {dbp_smd:.4f} >= 0.10 threshold.")

        return LasiCovariateBalanceReport(
            n_records_a=len(records_a),
            n_records_c=len(records_c),
            n_psus_a=n_psus_a,
            n_psus_c=n_psus_c,
            age_mean_a=round(mean_age_a, 2),
            age_sd_a=round(math.sqrt(var_age_a), 2),
            age_mean_c=round(mean_age_c, 2),
            age_sd_c=round(math.sqrt(var_age_c), 2),
            age_smd=age_smd,
            female_pct_a=round(p_fem_a * 100.0, 2),
            female_pct_c=round(p_fem_c * 100.0, 2),
            female_smd=female_smd,
            urban_pct_a=round(p_urb_a * 100.0, 2),
            urban_pct_c=round(p_urb_c * 100.0, 2),
            urban_smd=urban_smd,
            state_tvd=state_tvd,
            sbp_mean_a=mean_sbp_a,
            sbp_mean_c=mean_sbp_c,
            sbp_smd=sbp_smd,
            dbp_mean_a=mean_dbp_a,
            dbp_mean_c=mean_dbp_c,
            dbp_smd=dbp_smd,
            has_covariate_imbalance=(len(warnings) > 0),
            balance_warnings=warnings,
        )
