"""
mcg/mcg_schema.py

Media Critic Gate constants and schema/version metadata.

Contract authority: MEDIA-FRAMING-AUDIT-AGENT.md §PROHIBITIONS
Invariants: INV-1 (no mutable state), INV-5 (all constants pinned)
"""

from __future__ import annotations

import re

from engines.research_agent.agents.classification.classification_ruleset import CLASSIFICATION_RULE_VERSION

MCG_VERSION: str = "MCG-1.0"
MCG_AUDIT_SCHEMA_VERSION: str = "MCG_AUDIT-1.0"
MCG_VERDICT_SCHEMA_VERSION: str = "MCG_VERDICT-1.0"

VERDICT_PASS: str = "PASS"
VERDICT_FAIL: str = "FAIL"

REASON_PASS_ALL_MCG_CHECKS: str = "PASS_ALL_MCG_CHECKS"
REASON_REJECT_INVALID_INPUT: str = "REJECT_MCG_INVALID_INPUT"
REASON_REJECT_MISSING_FIELD: str = "REJECT_MCG_MISSING_FIELD"
REASON_REJECT_WRONG_LANE: str = "REJECT_MCG_WRONG_LANE"
REASON_REJECT_PRESSURE_CONVERSION: str = "REJECT_PRESSURE_CONVERSION_ATTEMPTED"
REASON_REJECT_NARRATIVE_SYNTHESIS: str = "REJECT_NARRATIVE_SYNTHESIS_ATTEMPTED"

STAGE_1_INPUT_GUARD: str = "1_INPUT_GUARD"
STAGE_2_FIELD_GUARD: str = "2_FIELD_GUARD"
STAGE_3_SCOPE_LOCK: str = "3_SCOPE_LOCK"
STAGE_4_PRESSURE_CONVERSION: str = "4_PRESSURE_CONVERSION"
STAGE_5_NARRATIVE_SYNTHESIS: str = "5_NARRATIVE_SYNTHESIS"

MCG_REQUIRED_MCR_FIELDS: frozenset[str] = frozenset({
    "mcrSchemaVersion",
    "laneType",
    "contractVersion",
    "sourceSeedID",
    "contextDescription",
})

# Classification rule version this module was built against (INV-5).
_EXPECTED_CLASSIFICATION_RULE_VERSION: str = "1.0"
assert CLASSIFICATION_RULE_VERSION == _EXPECTED_CLASSIFICATION_RULE_VERSION, (
    f"MCG built against classification rule version "
    f"{_EXPECTED_CLASSIFICATION_RULE_VERSION}, "
    f"found {CLASSIFICATION_RULE_VERSION}."
)

_REASON_CODES = (
    REASON_PASS_ALL_MCG_CHECKS,
    REASON_REJECT_INVALID_INPUT,
    REASON_REJECT_MISSING_FIELD,
    REASON_REJECT_WRONG_LANE,
    REASON_REJECT_PRESSURE_CONVERSION,
    REASON_REJECT_NARRATIVE_SYNTHESIS,
)

for _code in _REASON_CODES:
    assert isinstance(_code, str)
    assert _code != ""
    assert re.match(r"^[A-Z0-9_]+$", _code), (
        f"Reason code {_code!r} contains invalid characters."
    )

assert MCG_VERSION == "MCG-1.0"
assert MCG_AUDIT_SCHEMA_VERSION == "MCG_AUDIT-1.0"
assert MCG_VERDICT_SCHEMA_VERSION == "MCG_VERDICT-1.0"
assert len(MCG_REQUIRED_MCR_FIELDS) == 5
