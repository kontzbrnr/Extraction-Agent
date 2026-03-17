"""
emi/emi_schema.py
EMI version constants, status codes, rejection codes, NAR schema version.
Contract authority: EVENT-MATERIAL-IDENTIFIER.md v1.0 (Stabilized)
Invariants: INV-1 (no mutable state), INV-5 (all constants pinned)
"""

EMI_VERSION: str = "EMI-1.0"
EMI_LANE_TYPE: str = "NARRATIVE"
EMI_AU_SCHEMA_VERSION: str = "AU-1.0"

EMI_STATUS_PASS: str = "PASS"
EMI_STATUS_REJECT: str = "REJECT"

EMI_NAR_SCHEMA_VERSION: str = "EMI_NAR-1.0"

REJECT_EMI_INVALID_SEED: str = "REJECT_EMI_INVALID_SEED"
REJECT_EMI_EVENT_AMBIGUOUS: str = "REJECT_EMI_EVENT_AMBIGUOUS"
REJECT_EMI_COMPOSITE_BOUNDARY: str = "REJECT_EMI_COMPOSITE_BOUNDARY"
REJECT_EMI_ACTOR_ATTRIBUTION: str = "REJECT_EMI_ACTOR_ATTRIBUTION"
REJECT_EMI_SPECULATIVE_FRAMING: str = "REJECT_EMI_SPECULATIVE_FRAMING"
REJECT_EMI_LEDGER_INCOMPLETE: str = "REJECT_EMI_LEDGER_INCOMPLETE"
REJECT_EMI_NO_SEPARABLE_OCCURRENCE: str = "REJECT_EMI_NO_SEPARABLE_OCCURRENCE"
REJECT_EMI_DISCOURSE_INSEPARABLE: str = "REJECT_EMI_DISCOURSE_INSEPARABLE"

EMI_REQUIRED_AU_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "text",
        "parentSourceID",
        "sourceReference",
        "splitIndex",
        "schemaVersion",
    }
)

assert EMI_VERSION == "EMI-1.0"
assert EMI_LANE_TYPE == "NARRATIVE"
assert EMI_AU_SCHEMA_VERSION == "AU-1.0"
assert EMI_NAR_SCHEMA_VERSION == "EMI_NAR-1.0"
assert len(EMI_REQUIRED_AU_FIELDS) == 6


class EMINARValidationError(Exception):
    """Raised by validate_nar when a NAR dict is structurally incomplete."""


def validate_nar(nar: dict) -> None:
    """Validate structural completeness and types for an EMI NAR dict."""
    if not isinstance(nar, dict):
        raise EMINARValidationError("NAR must be a dict")

    expected_fields = {
        "eventID": str,
        "sourceSeedID": str,
        "actorGroup": str,
        "actionVerb": str,
        "ledgerMutation": bool,
        "unusualProcedural": bool,
        "narSchemaVersion": str,
        "ploe_fork_required": bool,
    }

    for field_name, expected_type in expected_fields.items():
        if field_name not in nar:
            raise EMINARValidationError(f"Missing required NAR field: {field_name}")
        if not isinstance(nar[field_name], expected_type):
            raise EMINARValidationError(
                f"NAR field '{field_name}' must be of type {expected_type.__name__}"
            )

    if nar["narSchemaVersion"] != EMI_NAR_SCHEMA_VERSION:
        raise EMINARValidationError(
            f"narSchemaVersion must equal {EMI_NAR_SCHEMA_VERSION}"
        )
