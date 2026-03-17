"""
narrative/ane_fingerprint.py
Deterministic ANESEED fingerprint derivation.
"""

from __future__ import annotations

import hashlib
import re

from narrative.ane_id_format import ANESEED_PATTERN, ANESEED_PREFIX

ANE_FINGERPRINT_VERSION: str = "ANE_FINGERPRINT_V1"
_ANE_FINGERPRINT_CONCAT_PREFIX: str = "ANE-1.0"

_NORMALIZE_WS_RE = re.compile(r"\s+")
_DISALLOWED_PUNCT_RE = re.compile(r"[^a-z0-9_]")


def _normalize_token(value: str | None) -> str:
    """Normalize a token using ANE norm(x) rules."""
    if value is None:
        return ""
    text = value.strip().lower()
    text = _NORMALIZE_WS_RE.sub("_", text)
    text = _DISALLOWED_PUNCT_RE.sub("", text)
    return text


def derive_aneseed_fingerprint(fields: dict[str, str | None]) -> str:
    """Derive ANESEED id using ANE_FINGERPRINT_V1 field order."""
    actor_role_norm = _normalize_token(fields.get("actorRole"))
    action_norm = _normalize_token(fields.get("action"))
    object_role_norm = _normalize_token(fields.get("objectRole"))
    context_role_norm = _normalize_token(fields.get("contextRole"))
    timestamp_context_norm = _normalize_token(fields.get("timestampContext"))
    source_reference_norm = _normalize_token(fields.get("sourceReference"))

    concatenated = "|".join(
        [
            _ANE_FINGERPRINT_CONCAT_PREFIX,
            actor_role_norm,
            action_norm,
            object_role_norm,
            context_role_norm,
            timestamp_context_norm,
            source_reference_norm,
        ]
    )
    digest = hashlib.sha256(concatenated.encode("utf-8")).hexdigest()
    event_seed_id = f"{ANESEED_PREFIX}{digest}"
    assert ANESEED_PATTERN.match(event_seed_id)
    return event_seed_id


assert ANE_FINGERPRINT_VERSION == "ANE_FINGERPRINT_V1"
