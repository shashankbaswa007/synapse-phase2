"""
Point-in-Time Medication Status Evaluation for SYNAPSE Phase 2.

Determines whether an eligible prescription was active at a specific reference timestamp,
eliminating temporal look-ahead bias (future prescription leakage) and historical
discontinuation misclassification.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Union

DEFAULT_ANTIHYPERTENSIVE_KEYWORDS = {
    "amlodipine", "telmisartan", "enalapril", "losartan",
    "hydrochlorothiazide", "atenolol", "metoprolol"
}


def parse_timestamp(ts: Union[str, datetime, None]) -> Optional[datetime]:
    """Parse string or datetime to datetime object safely."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        # Support ISO formats with or without timezone
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def is_prescription_active_at(
    prescription: Dict[str, Any],
    reference_time: Union[datetime, str],
    encounter: Optional[Dict[str, Any]] = None,
    target_drug_keywords: Optional[Set[str]] = None,
) -> bool:
    """Determine whether a prescription record was active at a specific point in time.

    Rules:
    1. Drug Eligibility: If target_drug_keywords is specified, drug_name must contain at least one keyword.
    2. Start Timing:
       - Checks prescription record fields: prescribed_time, start_time, timestamp.
       - Falls back to linked encounter start_time if prescription timing is absent.
       - If start time cannot be established, prescription cannot be verified as active (returns False).
    3. Start Boundary:
       - Must satisfy: start_time <= reference_time.
       - Prescriptions first issued strictly after reference_time (start_time > reference_time) return False.
       - Exactly at reference_time (start_time == reference_time) returns True (inclusive lower bound).
    4. Discontinuation / End Timing:
       - Checks end_time, discontinued_time, stop_time, cancellation_time.
       - If an end time is present and end_time < reference_time, returns False.
       - If status indicates discontinuation (Discontinued, Cancelled, Stopped, Blocked_Safety_Hold, Expired, Suspended):
         * If end_time is present and end_time >= reference_time, it was still active at reference_time.
         * If no end_time is present, explicit discontinuation status renders it inactive (returns False).
    5. Ongoing Maintenance:
       - Prescriptions with valid start_time <= reference_time and no discontinuation remain active.
    """
    ref_dt = parse_timestamp(reference_time)
    if ref_dt is None:
        return False

    if hasattr(prescription, "model_dump"):
        prescription = prescription.model_dump()
    elif hasattr(prescription, "dict"):
        prescription = prescription.dict()

    # 1. Drug Eligibility Check
    keywords = target_drug_keywords if target_drug_keywords is not None else DEFAULT_ANTIHYPERTENSIVE_KEYWORDS
    drug_name = (prescription.get("drug_name") or prescription.get("medicine_id") or "").lower()
    if keywords and not any(k in drug_name for k in keywords):
        return False

    # 2. Start Timing Determination
    start_str = (
        prescription.get("prescribed_time")
        or prescription.get("start_time")
        or prescription.get("timestamp")
    )
    if not start_str and encounter:
        start_str = encounter.get("start_time") or encounter.get("timestamp")

    start_dt = parse_timestamp(start_str)
    if start_dt is None:
        # Ambiguous / missing start time cannot be verified as active at point-in-time
        return False

    # 3. Boundary Check: Future prescriptions must not count
    if start_dt > ref_dt:
        return False

    # 4. Discontinuation / End Timing Determination
    end_str = (
        prescription.get("discontinued_time")
        or prescription.get("end_time")
        or prescription.get("stop_time")
        or prescription.get("cancellation_time")
    )
    end_dt = parse_timestamp(end_str)

    if end_dt is not None:
        if end_dt < ref_dt:
            # Discontinued prior to assessment timestamp
            return False

    status = (prescription.get("status") or "").strip().lower()
    discontinued_statuses = {"discontinued", "cancelled", "stopped", "expired", "blocked_safety_hold", "suspended"}
    if status in discontinued_statuses and end_dt is None:
        # Discontinued without explicit timestamp -> cannot assume active
        return False

    return True


def get_active_antihypertensive_patient_ids(
    prescriptions: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]],
    encounters: Optional[Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]] = None,
    reference_time: Union[datetime, str] = datetime.now(),
    target_drug_keywords: Optional[Set[str]] = None,
) -> Set[str]:
    """Extract set of patient IDs with active antihypertensive prescriptions at reference_time.

    Preserves deterministic, order-independent evaluation.
    """
    ref_dt = parse_timestamp(reference_time)
    if ref_dt is None:
        return set()

    # Build encounter map for O(1) start_time lookup
    enc_map: Dict[str, Dict[str, Any]] = {}
    if encounters:
        if isinstance(encounters, dict):
            for e_id, e in encounters.items():
                enc_map[e_id] = e
                if isinstance(e, dict) and "encounter_id" in e:
                    enc_map[e["encounter_id"]] = e
        elif isinstance(encounters, list):
            for e in encounters:
                eid = e.get("encounter_id")
                if eid:
                    enc_map[eid] = e

    rx_list: List[Dict[str, Any]] = (
        list(prescriptions.values()) if isinstance(prescriptions, dict) else list(prescriptions)
    )

    active_pids: Set[str] = set()
    for rx in rx_list:
        pid = rx.get("patient_id")
        if not pid:
            continue
        enc_id = rx.get("encounter_id")
        enc = enc_map.get(enc_id) if enc_id else None
        if is_prescription_active_at(rx, ref_dt, encounter=enc, target_drug_keywords=target_drug_keywords):
            active_pids.add(pid)

    return active_pids
