"""
gsd/au_validator.py

AU Schema Validator — Phase 4.5

Validates an AU dict against schemas/au.schema.json before
downstream handoff.

Invariants enforced by schema:
  — Required fields: id, text, parentSourceID, sourceReference,
    splitIndex, schemaVersion
  — id pattern: "AU_[a-f0-9]{64}$"
  — schemaVersion const: AU-1.0
  — text minLength: 1
  — sourceReference minLength: 1
  — splitIndex type: integer, minimum: 0
  — additionalProperties: false  (blocks laneType, seed_type,
    canonical_id, and all other extra fields — INV-4)

INV-3: validate_au() must be called before any downstream handoff.
       An AU that fails validation must never reach append_canonical_object().
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError
from jsonschema import validate

# Schema loaded once at module level — schema is a static codebase
# artifact, never mutated at runtime. Module-level load is consistent
# with extraction/rec_validator.py, schemas/pressure/validator.py,
# and schemas/narrative/validator.py.
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "au.schema.json"
with open(_SCHEMA_PATH, encoding="utf-8") as _fh:
    _SCHEMA: dict = json.load(_fh)


class AUSchemaValidationError(Exception):
    """
    Raised when an AU dict fails validation against au.schema.json.
    Message contains the original jsonschema ValidationError message.
    """


def validate_au(obj: dict) -> None:
    """
    Validate obj against au.schema.json.

    Returns None on success.
    Raises AUSchemaValidationError on any schema violation.

    Args:
        obj: AU dict to validate. Must conform to au.schema.json.

    Raises:
        AUSchemaValidationError: If validation fails.
    """
    try:
        validate(instance=obj, schema=_SCHEMA)
    except ValidationError as e:
        raise AUSchemaValidationError(str(e))
