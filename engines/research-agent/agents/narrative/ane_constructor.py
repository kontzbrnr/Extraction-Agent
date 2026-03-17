"""
narrative/ane_constructor.py
Canonical ANE object constructor.
"""

from __future__ import annotations

from narrative.ane_id_format import validate_aneseed_id

ANE_CONSTRUCTOR_VERSION: str = "ANE_CONSTRUCTOR-1.0"


def build_ane_object(ane_fields: dict, event_seed_id: str) -> dict:
    """Build deterministic ANE-1.0 object from validated fields and id."""
    validate_aneseed_id(event_seed_id)

    required_non_nullable = (
        "actorRole",
        "action",
        "eventDescription",
        "timestampContext",
        "timestampBucket",
        "sourceReference",
    )

    for key in required_non_nullable:
        value = ane_fields[key]
        if not isinstance(value, str) or value == "":
            raise ValueError(f"{key} must be a non-empty string")

    return {
        "schemaVersion": "ANE-1.0",
        "eventSeedId": event_seed_id,
        "actorRole": ane_fields["actorRole"],
        "action": ane_fields["action"],
        "objectRole": ane_fields.get("objectRole"),
        "contextRole": ane_fields.get("contextRole"),
        "eventDescription": ane_fields["eventDescription"],
        "timestampContext": ane_fields["timestampContext"],
        "timestampBucket": ane_fields["timestampBucket"],
        "sourceReference": ane_fields["sourceReference"],
    }
