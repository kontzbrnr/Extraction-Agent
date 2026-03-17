"""
schemas/cme_validator.py

Canonical CME (Canonical Media Event) object schema validator.

Loads cme.schema.json at import time.
Validates canonical CME dicts before registry commit.

Contract authority: MEDIA-EVENT-TRANSFORMER-AGENT.md (META v1.0).
Schema: schemas/cme.schema.json

Invariants:
    INV-1: Schema dict loaded once at import; never mutated.
    INV-5: jsonschema.validate is deterministic given fixed schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

_SCHEMA_PATH = Path(__file__).parent / "cme.schema.json"
_CME_CANONICAL_SCHEMA: dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


class CMECanonicalValidationError(Exception):
    """Raised when a canonical CME object fails JSON schema validation."""


def validate_cme_canonical_object(obj: dict) -> None:
    """Validate a canonical CME object against the canonical schema.

    Validates all constraints defined in cme.schema.json:
        - All required fields present (id, eventType, actorRole, action,
          objectRole, contextRole, eventDescription, subtype, permanence,
          sourceReference, timestampContext)
        - No unknown fields (additionalProperties: false)
        - Enum values valid (subtype, permanence, eventType)
        - ID pattern match (CME_[a-f0-9]{64})

    Args:
        obj: Assembled canonical CME dict as emitted by META.

    Raises:
        CMECanonicalValidationError: obj fails schema validation.
            Message contains jsonschema ValidationError message.
    """
    try:
        jsonschema.validate(instance=obj, schema=_CME_CANONICAL_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise CMECanonicalValidationError(str(exc.message)) from exc
