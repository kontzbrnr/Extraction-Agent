"""
santa/santa_ontology.py
SANTA constants and CSN identity format validation.
"""

from __future__ import annotations

import re

SANTA_VERSION: str = "SANTA-1.0"
SANTA_CSN_FINGERPRINT_VERSION: str = "CSN_FINGERPRINT_V1"
SANTA_CSN_FINGERPRINT_PREFIX: str = "CSN-1.0"

CSN_ID_PREFIX: str = "CSN_"
CSN_ID_HEX_LENGTH: int = 64
CSN_ID_TOTAL_LENGTH: int = 68
CSN_ID_PATTERN: re.Pattern = re.compile(r"^CSN_[a-f0-9]{64}$")

SANTA_PERMANENCE_NORM: str = ""
SANTA_LANE_TYPE: str = "NARRATIVE"

REJECT_SANTA_INVALID_INPUT: str = "REJECT_SANTA_INVALID_INPUT"
REJECT_SANTA_NON_CSN_INPUT: str = "REJECT_SANTA_NON_CSN_INPUT"
REJECT_SANTA_INVALID_SUBCLASS: str = "REJECT_SANTA_INVALID_SUBCLASS"
REJECT_SANTA_SCHEMA_INVALID: str = "REJECT_SANTA_SCHEMA_INVALID"
REJECT_SANTA_IDENTITY_CONTAMINATION: str = "REJECT_SANTA_IDENTITY_CONTAMINATION"


def validate_csn_id(canonical_id: str) -> None:
    """Validate CSN id format."""
    if not isinstance(canonical_id, str):
        raise ValueError("canonical_id must be a string")
    if canonical_id == "":
        raise ValueError("canonical_id cannot be empty")
    if not CSN_ID_PATTERN.match(canonical_id):
        raise ValueError("canonical_id must match ^CSN_[a-f0-9]{64}$")


assert len(CSN_ID_PREFIX) + CSN_ID_HEX_LENGTH == CSN_ID_TOTAL_LENGTH
assert SANTA_PERMANENCE_NORM == ""
assert SANTA_LANE_TYPE == "NARRATIVE"
assert SANTA_VERSION == "SANTA-1.0"
assert re.match(r"^[A-Z0-9_]+$", REJECT_SANTA_INVALID_INPUT)
assert re.match(r"^[A-Z0-9_]+$", REJECT_SANTA_NON_CSN_INPUT)
assert re.match(r"^[A-Z0-9_]+$", REJECT_SANTA_INVALID_SUBCLASS)
assert re.match(r"^[A-Z0-9_]+$", REJECT_SANTA_SCHEMA_INVALID)
assert re.match(r"^[A-Z0-9_]+$", REJECT_SANTA_IDENTITY_CONTAMINATION)
