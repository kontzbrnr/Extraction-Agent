"""
santa/santa_agent.py
SANTA Agent — enforce_santa() for CSN canonical object construction.
"""

from __future__ import annotations

from engines.research_agent.agents.santa.santa_ontology import (
    REJECT_SANTA_IDENTITY_CONTAMINATION,
    REJECT_SANTA_INVALID_INPUT,
    REJECT_SANTA_INVALID_SUBCLASS,
    REJECT_SANTA_NON_CSN_INPUT,
    REJECT_SANTA_SCHEMA_INVALID,
    SANTA_LANE_TYPE,
    SANTA_VERSION,
)
from engines.research_agent.agents.santa.santa_ruleset import InvalidCSNSubclassError, derive_csn_fingerprint, validate_csn_subclass
from engines.research_agent.schemas.narrative.validator import (
    NarrativeCSNSchemaValidationError,
    validate_narrative_csn_object,
)


def _build_rejection(event: dict, reason_code: str) -> dict:
    return {
        "reasonCode": reason_code,
        "input": dict(event) if isinstance(event, dict) else {},
        "schemaVersion": "SANTA_REJECTION-1.0",
    }


def _validate_required_fields(event: dict) -> str | None:
    if "eventDescription" not in event:
        return REJECT_SANTA_INVALID_INPUT
    if not isinstance(event.get("eventDescription"), str) or event["eventDescription"].strip() == "":
        return REJECT_SANTA_INVALID_INPUT

    if "sourceReference" not in event:
        return REJECT_SANTA_INVALID_INPUT

    if "timestampContext" not in event:
        return REJECT_SANTA_INVALID_INPUT
    if not isinstance(event.get("timestampContext"), str) or event["timestampContext"].strip() == "":
        return REJECT_SANTA_INVALID_INPUT

    return None


def _identity_spot_check(event: dict) -> str | None:
    for key in ("eventDescription", "sourceReference", "timestampContext"):
        value = event.get(key)
        if not isinstance(value, str):
            return REJECT_SANTA_IDENTITY_CONTAMINATION
        if key != "sourceReference" and value.strip() == "":
            return REJECT_SANTA_IDENTITY_CONTAMINATION

    for key in ("actorRole", "action", "objectRole", "contextRole"):
        value = event.get(key)
        if value is not None and not isinstance(value, str):
            return REJECT_SANTA_IDENTITY_CONTAMINATION

    return None


def enforce_santa(event: dict) -> tuple[bool, dict | None, dict | None]:
    """Canonicalize CSN-classified events into schema-valid CSN objects."""
    if not isinstance(event, dict):
        return (False, _build_rejection({}, REJECT_SANTA_INVALID_INPUT), None)

    if event.get("classification") == "CME":
        return (False, _build_rejection(event, REJECT_SANTA_NON_CSN_INPUT), None)
    if event.get("classification") != "CSN":
        return (False, _build_rejection(event, REJECT_SANTA_NON_CSN_INPUT), None)
    if "standaloneSubclass" not in event or event.get("standaloneSubclass") is None:
        return (False, _build_rejection(event, REJECT_SANTA_INVALID_INPUT), None)

    try:
        validate_csn_subclass(event.get("standaloneSubclass"))
    except InvalidCSNSubclassError:
        return (False, _build_rejection(event, REJECT_SANTA_INVALID_SUBCLASS), None)

    required_error = _validate_required_fields(event)
    if required_error is not None:
        return (False, _build_rejection(event, required_error), None)

    identity_error = _identity_spot_check(event)
    if identity_error is not None:
        return (False, _build_rejection(event, identity_error), None)

    canonical_id = derive_csn_fingerprint(
        {
            "actorRole": event.get("actorRole"),
            "action": event.get("action"),
            "objectRole": event.get("objectRole"),
            "contextRole": event.get("contextRole"),
            "subclass": event.get("standaloneSubclass"),
            "sourceReference": event.get("sourceReference"),
        }
    )

    canonical = {
        "laneType": SANTA_LANE_TYPE,
        "id": canonical_id,
        "eventType": "CSN",
        "actorRole": event.get("actorRole"),
        "action": event.get("action"),
        "objectRole": event.get("objectRole"),
        "contextRole": event.get("contextRole"),
        "subclass": event.get("standaloneSubclass"),
        "eventDescription": event.get("eventDescription"),
        "timestampContext": event.get("timestampContext"),
        "sourceReference": event.get("sourceReference"),
        "contractVersion": SANTA_VERSION,
    }

    assert canonical["eventType"] == "CSN"
    assert canonical["laneType"] == "NARRATIVE"

    try:
        validate_narrative_csn_object(canonical)
    except NarrativeCSNSchemaValidationError:
        return (False, _build_rejection(event, REJECT_SANTA_SCHEMA_INVALID), None)

    return (
        True,
        None,
        {
            "canonicalObject": canonical,
            "deduplicationStatus": "new",
            "logEntry": f"SANTA canonicalized {canonical_id} subclass={canonical['subclass']}",
        },
    )
