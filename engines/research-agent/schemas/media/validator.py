"""
schemas/media/validator.py

Canonical MCR object schema validator.

Loads canonical_media_context_object.schema.json at import time.
Validates canonical MCR dicts before registry commit.

Invariants: INV-1 (schema loaded once, not mutated), INV-5 (deterministic)
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

_SCHEMA_PATH = Path(__file__).parent / "canonical_media_context_object.schema.json"
_MCR_CANONICAL_SCHEMA: dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


class MCRCanonicalValidationError(Exception):
    """Raised when a canonical MCR object fails JSON schema validation."""


def validate_mcr_canonical_object(obj: dict) -> None:
    """Validate a canonical MCR object against the canonical schema.

    Args:
        obj: Assembled canonical MCR dict.

    Raises:
        MCRCanonicalValidationError: obj fails schema validation.
    """
    try:
        jsonschema.validate(instance=obj, schema=_MCR_CANONICAL_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise MCRCanonicalValidationError(str(exc.message)) from exc
