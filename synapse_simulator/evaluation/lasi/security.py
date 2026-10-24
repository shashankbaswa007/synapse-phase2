"""
Security, Cryptographic Pseudonymization, and Enclave Confidentiality Layer.

Implements Milestone 3 Requirement 6:
1. Keyed HMAC-SHA256 pseudonymization for participant and household linkage.
2. Separate surrogate spaces for participant IDs and household IDs.
3. Environment-based or configuration-based key injection without storing keys in manifests.
4. Formal legal and ethical notice: Pseudonymization does NOT constitute anonymization.
"""

import hmac
import hashlib
import os
from typing import Optional, Any, Union


# Default deterministic application-wide salt used ONLY when no external key is configured.
DEFAULT_SURROGATE_SALT = "SYNAPSE_PHASE2_LASI_SURROGATE_SALT_v1"

CONFIDENTIALITY_NOTICE = (
    "CONFIDENTIALITY AND LEGAL NOTICE: Cryptographic pseudonymization replaces direct identifiers "
    "with deterministic HMAC-SHA256 digests to prevent inadvertent exposure in operational artifacts. "
    "Pseudonymization does NOT constitute full statistical disclosure limitation or anonymization under "
    "Indian Digital Personal Data Protection (DPDP) Act or IIPS / Gateway to Global Aging Data Use Agreements. "
    "Microdata contains quasi-identifiers (demographic profiles, geographic strata, clinical measurements) "
    "that may permit re-identification if combined with external auxiliary datasets. "
    "Genuine reference microdata must remain confined to encrypted, access-controlled enclaves and "
    "must NEVER be exported, committed to version control, or transmitted outside authorized environments."
)


class KeyedPseudonymizer:
    """Keyed cryptographic pseudonymizer using HMAC-SHA256."""

    def __init__(self, secret_key: Optional[Union[str, bytes]] = None):
        """Initialize pseudonymizer with an explicit key, environment key, or default salt.

        Args:
            secret_key: Optional secret key. If None, checks SYNAPSE_PSEUDONYMIZATION_KEY env var.
        """
        if secret_key is not None:
            self._key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
            self.is_custom_key = True
        else:
            env_key = os.environ.get("SYNAPSE_PSEUDONYMIZATION_KEY")
            if env_key:
                self._key = env_key.encode("utf-8")
                self.is_custom_key = True
            else:
                self._key = DEFAULT_SURROGATE_SALT.encode("utf-8")
                self.is_custom_key = False

    def _normalize_raw_id(self, raw_id: Any) -> Optional[str]:
        """Normalize raw identifier, stripping trailing float suffixes."""
        if raw_id is None:
            return None
        raw_str = str(raw_id).strip()
        if not raw_str or raw_str.lower() in {"", ".", "na", "nan", "null", "none", "-999", "-998", "-99"}:
            return None
        if raw_str.endswith(".0"):
            raw_str = raw_str[:-2]
        return raw_str

    def _compute_hmac_prefix(self, normalized_id: str, prefix_len: int = 12) -> str:
        """Compute truncated hex HMAC-SHA256 digest."""
        h = hmac.new(self._key, normalized_id.encode("utf-8"), hashlib.sha256)
        return h.hexdigest()[:prefix_len]

    def pseudonymize_participant(self, raw_id: Any, fallback_index: Optional[int] = None) -> str:
        """Generate deterministic, keyed pseudonym for a human participant."""
        norm = self._normalize_raw_id(raw_id)
        if norm is None:
            idx = fallback_index if fallback_index is not None else 0
            return f"lasi_syn_p_{idx:06d}"
        digest = self._compute_hmac_prefix(f"PARTICIPANT:{norm}", prefix_len=12)
        return f"lasi_p_{digest}"

    def pseudonymize_household(self, raw_hhid: Any, fallback_index: Optional[int] = None) -> Optional[str]:
        """Generate deterministic, keyed pseudonym for a household sampling unit."""
        norm = self._normalize_raw_id(raw_hhid)
        if norm is None:
            if fallback_index is not None:
                return f"lasi_syn_hh_{fallback_index:06d}"
            return None
        digest = self._compute_hmac_prefix(f"HOUSEHOLD:{norm}", prefix_len=12)
        return f"lasi_hh_{digest}"

    def get_security_metadata(self) -> dict:
        """Return non-sensitive metadata for ingestion manifests (never reveals secret key)."""
        return {
            "algorithm": "HMAC-SHA256",
            "key_source": "ENVIRONMENT_OR_CONFIG" if self.is_custom_key else "PROJECT_DEFAULT_SALT",
            "digest_prefix_length": 12,
            "confidentiality_notice": CONFIDENTIALITY_NOTICE,
        }
