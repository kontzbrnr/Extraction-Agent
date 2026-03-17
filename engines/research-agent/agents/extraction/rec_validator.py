"""
REC Schema Validator — Phase 3.3

Validates a REC dict against schemas/rec.schema.json before
downstream handoff.

Invariants enforced by schema:
  - Required fields: id, text, isComposite, schemaVersion
  - id pattern: ^REC_[a-f0-9]{64}$
  - schemaVersion const: REC-1.0
  - text minLength: 1
  - isComposite type: boolean
  - additionalProperties: false  (blocks laneType, seed_type,
    canonical_id, and all other extra fields — INV-4)

INV-3: validate_rec() must be called before any downstream handoff.
       A REC that fails validation must never reach append_canonical_object().
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError
from jsonschema import validate

# Schema loaded once at module level — schema is a static codebase
# artifact, never mutated at runtime. Module-level load is consistent
# with schemas/pressure/validator.py and schemas/narrative/validator.py.
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "rec.schema.json"
with open(_SCHEMA_PATH, encoding="utf-8") as _fh:
    _SCHEMA: dict = json.load(_fh)


class RECSchemaValidationError(Exception):
    """
    Raised when a REC dict fails validation against rec.schema.json.
    Message contains the original jsonschema ValidationError message.
    """


def validate_rec(obj: dict) -> None:
    """
    Validate obj against rec.schema.json.

    Returns None on success.
    Raises RECSchemaValidationError on any schema violation.

    Args:
        obj: REC dict to validate. Must conform to rec.schema.json.

    Raises:
        RECSchemaValidationError: If validation fails.
    """
    try:
        validate(instance=obj, schema=_SCHEMA)
    except ValidationError as e:
        raise RECSchemaValidationError(str(e))
