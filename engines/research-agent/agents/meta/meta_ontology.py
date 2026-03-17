"""
meta/meta_ontology.py
META ontology and identity constants for CME canonicalization.
"""

from __future__ import annotations

import re

META_VERSION: str = "META-1.0"
META_CME_FINGERPRINT_VERSION: str = "CME_FINGERPRINT_V1"
META_CME_FINGERPRINT_PREFIX: str = "CME-1.0"

CME_ID_PREFIX: str = "CME_"
CME_ID_HEX_LENGTH: int = 64
CME_ID_TOTAL_LENGTH: int = 68
CME_ID_PATTERN = re.compile(r"^CME_[a-f0-9]{64}$")

CME_PERMANENCE_TOKEN: str = "permanent"

META_SUBTYPE_VALUES: frozenset[str] = frozenset(
    {
        "structural",
        "transactional",
        "disciplinary",
        "award",
        "record",
        "administrative",
        "contractual",
        "medical",
        "competitive_result",
        "retirement",
        "reinstatement",
        "other",
    }
)
META_SUBTYPE_OTHER: str = "other"

REJECT_META_INVALID_INPUT: str = "REJECT_META_INVALID_INPUT"
REJECT_META_NON_CME_INPUT: str = "REJECT_META_NON_CME_INPUT"
REJECT_META_SUBTYPE_AMBIGUOUS: str = "REJECT_META_SUBTYPE_AMBIGUOUS"
REJECT_META_PERMANENCE_VIOLATION: str = "REJECT_META_PERMANENCE_VIOLATION"
REJECT_META_IDENTITY_CONTAMINATION: str = "REJECT_META_IDENTITY_CONTAMINATION"
REJECT_META_SCHEMA_INVALID: str = "REJECT_META_SCHEMA_INVALID"


def validate_cme_id(canonical_id: str) -> None:
    """Validate CME canonical ID format."""
    if not isinstance(canonical_id, str):
        raise ValueError("canonical_id must be a string")
    if canonical_id == "":
        raise ValueError("canonical_id cannot be empty")
    if not CME_ID_PATTERN.match(canonical_id):
        raise ValueError(
            f"Invalid CME id format; expected {CME_ID_PREFIX}<64 lowercase hex chars>"
        )


assert META_VERSION == "META-1.0"
assert META_CME_FINGERPRINT_VERSION == "CME_FINGERPRINT_V1"
assert META_CME_FINGERPRINT_PREFIX == "CME-1.0"
assert CME_ID_PREFIX == "CME_"
assert CME_ID_HEX_LENGTH == 64
assert CME_ID_TOTAL_LENGTH == 68
assert len(CME_ID_PREFIX) + CME_ID_HEX_LENGTH == CME_ID_TOTAL_LENGTH
assert CME_PERMANENCE_TOKEN == "permanent"
assert len(META_SUBTYPE_VALUES) == 12
assert META_SUBTYPE_OTHER in META_SUBTYPE_VALUES
