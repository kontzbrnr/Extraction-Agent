"""
santa/santa_ruleset.py
SANTA deterministic fingerprint and subclass validation rules.
"""

from __future__ import annotations

import hashlib
import re

from engines.research_agent.agents.nca.nca_ontology import NCA_ASSIGNABLE_SUBCLASSES
from engines.research_agent.agents.santa.santa_ontology import (
    CSN_ID_PATTERN,
    CSN_ID_PREFIX,
    SANTA_CSN_FINGERPRINT_PREFIX,
    SANTA_PERMANENCE_NORM,
)
from engines.research_agent.schemas.narrative.fallback_tokens import NARRATIVE_CSN_FALLBACK_TOKENS

assert all(v == "" for v in NARRATIVE_CSN_FALLBACK_TOKENS.values()), (
    "INV-5 violation: NARRATIVE_CSN_FALLBACK_TOKENS values have changed. "
    "Non-empty fallback values alter CSN fingerprints for null-field objects. "
    "Any change requires a governance ruling and a CSN fingerprint version bump."
)

_NORMALIZE_WS_RE = re.compile(r"\s+")
_DISALLOWED_PUNCT_RE = re.compile(r"[^a-z0-9_]")


class InvalidCSNSubclassError(Exception):
    """Raised for invalid CSN subclass values."""

    def __init__(self, subclass: str | None) -> None:
        self.subclass = subclass
        super().__init__(f"Invalid CSN subclass: {subclass!r}")


def _normalize_token(value: str | None, fallback_key: str | None = None) -> str:
    if value is None:
        if fallback_key is None:
            return ""
        return NARRATIVE_CSN_FALLBACK_TOKENS.get(fallback_key, "")
    text = value.strip().lower()
    text = _NORMALIZE_WS_RE.sub("_", text)
    text = _DISALLOWED_PUNCT_RE.sub("", text)
    return text


def derive_csn_fingerprint(fields: dict[str, str | None]) -> str:
    """Derive CSN_FINGERPRINT_V1 canonical id."""
    actor_role_norm = _normalize_token(fields.get("actorRole"), "actorRole")
    action_norm = _normalize_token(fields.get("action"), "action")
    object_role_norm = _normalize_token(fields.get("objectRole"), "objectRole")
    context_role_norm = _normalize_token(fields.get("contextRole"), "contextRole")
    subclass_norm = _normalize_token(fields.get("subclass"), "subclass")
    permanence_norm = SANTA_PERMANENCE_NORM
    source_reference_norm = _normalize_token(fields.get("sourceReference"), "sourceReference")

    fingerprint_input = "|".join(
        [
            SANTA_CSN_FINGERPRINT_PREFIX,
            actor_role_norm,
            action_norm,
            object_role_norm,
            context_role_norm,
            subclass_norm,
            permanence_norm,
            source_reference_norm,
        ]
    )
    digest = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
    canonical_id = f"{CSN_ID_PREFIX}{digest}"
    assert CSN_ID_PATTERN.match(canonical_id)
    return canonical_id


def validate_csn_subclass(subclass: str | None) -> None:
    """Validate subclass against assignable NCA subclasses only."""
    if subclass is None:
        raise InvalidCSNSubclassError(subclass)
    if not isinstance(subclass, str):
        raise InvalidCSNSubclassError(subclass)
    if subclass == "narrative_singularity":
        raise InvalidCSNSubclassError(subclass)
    if subclass not in NCA_ASSIGNABLE_SUBCLASSES:
        raise InvalidCSNSubclassError(subclass)


def build_dedup_key(event: dict) -> tuple:
    """Build time-bound dedup key tuple including timestampContext."""
    return (
        event.get("actorRole"),
        event.get("action"),
        event.get("objectRole"),
        event.get("contextRole"),
        event.get("standaloneSubclass"),
        event.get("timestampContext"),
    )
