"""
EMI event ID derivation.

EMI event IDs are local audit reference hashes. They are NOT canonical lane
identities. They do not participate in CME_FINGERPRINT_V1, CSN_FINGERPRINT_V1,
CPS_FINGERPRINT_V1, or ANE_FINGERPRINT_V1. They carry no prefix and are not
registered in any dedup registry.
"""

import hashlib

EMI_EVENT_ID_VERSION = "EMI-EVENTID-1.0"


def derive_emi_event_id(au: dict) -> str:
    """
    Derive a deterministic local audit reference hash for an AU record.
    Input: au dict with keys 'id' and 'text'.
    Returns: 64-char lowercase hex string (unprefixed).
    """
    payload = f"{au['id']}|{au['text']}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()