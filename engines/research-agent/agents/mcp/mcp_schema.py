"""
mcp/mcp_schema.py

MCP version constants, rejection codes, required AU fields,
and MCR structural validator.

Contract authority: MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md v2.0
Invariants: INV-1 (no mutable state), INV-5 (all constants pinned)
"""

from engines.research_agent.agents.classification.classification_ruleset import CLASSIFICATION_RULE_VERSION

MCP_VERSION: str = "MCP-1.0"
MCP_LANE_TYPE: str = "MEDIA"
MCP_MCR_SCHEMA_VERSION: str = "MCP_MCR-1.0"
MCP_AU_SCHEMA_VERSION: str = "AU-1.0"

MCP_STATUS_PASS: str = "PASS"
MCP_STATUS_REJECT: str = "REJECT"

# Classification rule version this module was built against (INV-5).
# If CLASSIFICATION_RULE_VERSION changes, this assert will fail at import,
# signalling that mcp_ruleset.py must be reviewed for compatibility.
_EXPECTED_CLASSIFICATION_RULE_VERSION: str = "1.0"
assert CLASSIFICATION_RULE_VERSION == _EXPECTED_CLASSIFICATION_RULE_VERSION, (
    f"MCP built against classification rule version "
    f"{_EXPECTED_CLASSIFICATION_RULE_VERSION}, "
    f"found {CLASSIFICATION_RULE_VERSION}."
)

REJECT_MCP_WRONG_LANE: str = "REJECT_MCP_WRONG_LANE"
REJECT_MCP_MISSING_FIELD: str = "REJECT_MCP_MISSING_FIELD"
REJECT_MCP_EVENT_VERB: str = "REJECT_MCP_EVENT_VERB"
REJECT_MCP_ASYMMETRY_DETECTED: str = "REJECT_MCP_ASYMMETRY_DETECTED"
REJECT_MCP_PROHIBITED_LANGUAGE: str = "REJECT_MCP_PROHIBITED_LANGUAGE"
REJECT_MCP_IDENTITY_CONTAMINATION: str = "REJECT_MCP_IDENTITY_CONTAMINATION"
REJECT_MCP_SCHEMA_INVALID: str = "REJECT_MCP_SCHEMA_INVALID"

MCP_REQUIRED_AU_FIELDS: frozenset[str] = frozenset({
    "id",
    "text",
    "parentSourceID",
    "sourceReference",
    "splitIndex",
    "schemaVersion",
})

assert MCP_VERSION == "MCP-1.0"
assert MCP_LANE_TYPE == "MEDIA"
assert MCP_MCR_SCHEMA_VERSION == "MCP_MCR-1.0"
assert len(MCP_REQUIRED_AU_FIELDS) == 6


class MCRValidationError(Exception):
    """Raised by validate_mcr when an MCR dict is structurally incomplete."""


def validate_mcr(mcr: dict) -> None:
    """Validate structural completeness and types for an MCP MCR dict."""
    if not isinstance(mcr, dict):
        raise MCRValidationError("MCR must be a dict.")

    required_str_fields = {
        "mcrSchemaVersion": str,
        "laneType": str,
        "contractVersion": str,
        "sourceSeedID": str,
        "contextDescription": str,
    }
    for field, expected_type in required_str_fields.items():
        if field not in mcr:
            raise MCRValidationError(f"Missing required MCR field: {field}")
        if not isinstance(mcr[field], expected_type):
            raise MCRValidationError(
                f"MCR field '{field}' must be {expected_type.__name__}."
            )

    nullable_str_fields = {"sourceType", "timeMarker", "framingType"}
    for field in nullable_str_fields:
        if field not in mcr:
            raise MCRValidationError(f"Missing MCR field: {field}")
        if mcr[field] is not None and not isinstance(mcr[field], str):
            raise MCRValidationError(
                f"MCR field '{field}' must be str or None."
            )

    if mcr["mcrSchemaVersion"] != MCP_MCR_SCHEMA_VERSION:
        raise MCRValidationError(
            f"mcrSchemaVersion must equal {MCP_MCR_SCHEMA_VERSION}."
        )
    if mcr["laneType"] != MCP_LANE_TYPE:
        raise MCRValidationError(
            f"laneType must equal {MCP_LANE_TYPE}."
        )
    if mcr["contractVersion"] != MCP_VERSION:
        raise MCRValidationError(
            f"contractVersion must equal {MCP_VERSION}."
        )
