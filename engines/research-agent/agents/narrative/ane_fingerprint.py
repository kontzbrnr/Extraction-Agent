"""
narrative/ane_fingerprint.py
Deterministic ANESEED fingerprint derivation.
"""

from __future__ import annotations

import hashlib
import re

from engines.research_agent.agents.narrative.ane_id_format import ANESEED_PATTERN, ANESEED_PREFIX, validate_aneseed_id

ANE_FINGERPRINT_VERSION: str = "ANE_FINGERPRINT_V1"
_ANE_FINGERPRINT_CONCAT_PREFIX: str = "ANE-1.0"

ANE_KP1_FIELDS: tuple[str, ...] = ("actorRole", "action")
ANE_KP2_FIELDS: tuple[str, ...] = ("objectRole", "contextRole", "timestampContext")
ANE_KP3_FIELDS: tuple[str, ...] = ("sourceReference",)


def _lock_fields_payload(fields: dict[str, str | None]) -> dict[str, str | None]:
    lock_fields = ANE_KP1_FIELDS + ANE_KP2_FIELDS + ANE_KP3_FIELDS
    missing = [key for key in lock_fields if key not in fields]
    if missing:
        raise ValueError(f"missing keypoints for ANE lock: {', '.join(missing)}")
    return {key: fields.get(key) for key in lock_fields}


def validate_aneseed_lock(fields: dict[str, str | None], event_seed_id: str) -> None:
    """Validate KP1/KP2/KP3 lock and ANESEED derivation integrity."""
    validate_aneseed_id(event_seed_id)
    expected = derive_aneseed_fingerprint(_lock_fields_payload(fields))
    if expected != event_seed_id:
        raise ValueError("event_seed_id does not match KP1/KP2/KP3 lock derivation")


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
