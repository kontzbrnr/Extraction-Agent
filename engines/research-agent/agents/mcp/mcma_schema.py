"""
mcp/mcma_schema.py

Media Context Mint Authority (MCMA) version constants and rejection codes.

Contract authority: MEDIA-LANE IDENTITY PHILOSOPHY — GOVERNING RULING v1
                    Rulings 10.4-A through 10.4-D
Invariants: INV-1 (no mutable state), INV-5 (all constants pinned)
"""

from __future__ import annotations

from engines.research_agent.enums.role_token_registry import MEDIA_ENUM_REGISTRY_VERSION
from engines.research_agent.agents.mcp.mcr_fingerprint import MCR_FINGERPRINT_VERSION

MCMA_VERSION: str = "MCMA-1.0"
MCMA_MCR_SCHEMA_VERSION: str = "MCR-1.0"
MCMA_LANE_TYPE: str = "MEDIA"
MCMA_AUDIT_SCHEMA_VERSION: str = "MCMA_AUDIT-1.0"

STATUS_NEW_CANONICAL: str = "NEW_CANONICAL"
STATUS_DUPLICATE: str = "DUPLICATE"

REJECT_MCMA_INVALID_INPUT: str = "REJECT_MCMA_INVALID_INPUT"
REJECT_MCMA_MISSING_FIELD: str = "REJECT_MCMA_MISSING_FIELD"
REJECT_MCMA_WRONG_LANE: str = "REJECT_MCMA_WRONG_LANE"
REJECT_MCMA_INVALID_FRAMING_TYPE: str = "REJECT_MCMA_INVALID_FRAMING_TYPE"
REJECT_MCMA_SCHEMA_INVALID: str = "REJECT_MCMA_SCHEMA_INVALID"

# Default enum registry version — pinned to ENUM_v1.1 which introduced framingType.
MCMA_DEFAULT_ENUM_REGISTRY_VERSION: str = "ENUM_v1.1"

# Valid framingType tokens — sourced from ENUM_v1.1 registry.
# Must stay in sync with enums/media/registry.json framingType.values.
# Any registry change requires a corresponding update here and a version bump.
VALID_MCR_FRAMING_TYPES: frozenset[str] = frozenset({
    "label",
    "reputation",
    "destiny",
    "skepticism",
    "speculation",
    "moralizing",
    "other",
})

# Required fields in an MCR dict passed to enforce_mcma.
MCMA_REQUIRED_MCR_FIELDS: frozenset[str] = frozenset({
    "mcrSchemaVersion",
    "laneType",
    "contractVersion",
    "sourceSeedID",
    "contextDescription",
    "framingType",
})

assert MCMA_VERSION == "MCMA-1.0"
assert MCMA_MCR_SCHEMA_VERSION == "MCR-1.0"
assert MCMA_LANE_TYPE == "MEDIA"
assert MCMA_DEFAULT_ENUM_REGISTRY_VERSION == "ENUM_v1.1", (
    f"MCMA_DEFAULT_ENUM_REGISTRY_VERSION must equal 'ENUM_v1.1' "
    f"(framingType was introduced in that version). Got: "
    f"{MCMA_DEFAULT_ENUM_REGISTRY_VERSION!r}"
)
assert len(VALID_MCR_FRAMING_TYPES) == 7
assert len(MCMA_REQUIRED_MCR_FIELDS) == 6
