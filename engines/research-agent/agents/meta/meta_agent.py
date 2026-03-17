"""
meta/meta_agent.py
META Agent — enforce_meta() for canonical CME object construction.
"""

from __future__ import annotations

from engines.research_agent.agents.meta.meta_ontology import (
    CME_PERMANENCE_TOKEN,
    META_VERSION,
    REJECT_META_IDENTITY_CONTAMINATION,
    REJECT_META_INVALID_INPUT,
    REJECT_META_NON_CME_INPUT,
    REJECT_META_PERMANENCE_VIOLATION,
    REJECT_META_SCHEMA_INVALID,
    REJECT_META_SUBTYPE_AMBIGUOUS,
)
from engines.research_agent.agents.meta.meta_ruleset import SubtypeAmbiguousError, assign_cme_subtype, derive_cme_fingerprint
from engines.research_agent.agents.meta.meta_schema import CMESchemaValidationError, validate_cme_object


def _build_rejection(event: dict, reason_code: str) -> dict:
    safe_input = dict(event) if isinstance(event, dict) else {}
    return {
        "reasonCode": reason_code,
        "input": safe_input,
        "schemaVersion": "META_REJECTION-1.0",
    }


def _is_non_cme_input(event: dict) -> bool:
    if event.get("classification") == "CSN":
        return True
    if "standaloneSubclass" in event and event.get("standaloneSubclass") is not None:
        return True
    if event.get("eventType") == "CSN":
        return True
    seed_type = event.get("seedType")
    if seed_type in {"PRESSURE", "MEDIA_CONTEXT", "STRUCTURAL"}:
        return True
    lane_type = event.get("laneType")
    if lane_type in {"PRESSURE", "MEDIA_CONTEXT", "STRUCTURAL"}:
        return True
    return False


def _validate_required_fields(event: dict) -> str | None:
    required = (
        "actorRole",
        "action",
        "eventDescription",
        "sourceReference",
        "timestampContext",
    )
    for field in required:
        if field not in event:
            return REJECT_META_INVALID_INPUT
        if not isinstance(event[field], str) or event[field].strip() == "":
            return REJECT_META_INVALID_INPUT
    return None


def _identity_spot_check(event: dict) -> str | None:
    for field in (
        "actorRole",
        "action",
        "eventDescription",
        "sourceReference",
        "timestampContext",
    ):
        value = event.get(field)
        if not isinstance(value, str) or value.strip() == "":
            return REJECT_META_IDENTITY_CONTAMINATION
    for field in ("objectRole", "contextRole"):
        value = event.get(field)
        if value is not None and not isinstance(value, str):
            return REJECT_META_IDENTITY_CONTAMINATION
    return None


def enforce_meta(event: dict) -> tuple[bool, dict | None, dict | None]:
    """Canonicalize NCA-classified CME events into schema-valid CME objects."""
    if not isinstance(event, dict):
        return (False, _build_rejection({}, REJECT_META_INVALID_INPUT), None)

    if _is_non_cme_input(event):
        return (False, _build_rejection(event, REJECT_META_NON_CME_INPUT), None)

    required_error = _validate_required_fields(event)
    if required_error is not None:
        return (False, _build_rejection(event, required_error), None)

    identity_error = _identity_spot_check(event)
    if identity_error is not None:
        return (False, _build_rejection(event, identity_error), None)

    try:
        subtype = assign_cme_subtype(event)
    except SubtypeAmbiguousError:
        return (False, _build_rejection(event, REJECT_META_SUBTYPE_AMBIGUOUS), None)

    permanence = CME_PERMANENCE_TOKEN
    if permanence != "permanent":
        return (False, _build_rejection(event, REJECT_META_PERMANENCE_VIOLATION), None)

    canonical_id = derive_cme_fingerprint(
        {
            "actorRole": event.get("actorRole"),
            "action": event.get("action"),
            "objectRole": event.get("objectRole"),
            "contextRole": event.get("contextRole"),
            "subtype": subtype,
            "permanence": permanence,
            "sourceReference": event.get("sourceReference"),
        }
    )

    canonical = {
        "id": canonical_id,
        "eventType": "CME",
        "actorRole": event["actorRole"],
        "action": event["action"],
        "objectRole": event.get("objectRole"),
        "contextRole": event.get("contextRole"),
        "eventDescription": event["eventDescription"],
        "subtype": subtype,
        "permanence": permanence,
        "sourceReference": event["sourceReference"],
        "timestampContext": event["timestampContext"],
    }

    assert canonical["eventType"] == "CME"
    assert "standaloneSubclass" not in canonical

    try:
        validate_cme_object(canonical)
    except CMESchemaValidationError:
        return (False, _build_rejection(event, REJECT_META_SCHEMA_INVALID), None)

    result = {
        "canonicalObject": canonical,
        "deduplicationStatus": "new",
        "logEntry": f"{META_VERSION}: canonicalized {canonical_id} subtype={subtype}",
    }
    return (True, None, result)
