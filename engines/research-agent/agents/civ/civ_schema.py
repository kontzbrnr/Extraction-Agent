"""
civ/civ_schema.py

Canonical Integrity Validator — version constants, verdict codes,
rejection codes, check stage identifiers, and lane registry.

Contract authority: CANONICAL-INTEGRITY-VALIDATOR.md v1.0
Rejection codes: enums/shared/rejection_codes.json (CIV namespace)

Invariants: INV-1 (no mutable state), INV-5 (all constants pinned)
"""

from __future__ import annotations

import re

# ── Agent version ─────────────────────────────────────────────────────────────

CIV_VERSION: str = "CIV-1.0"
CIV_VERDICT_SCHEMA_VERSION: str = "CIV_VERDICT-1.0"

# ── Verdict codes ─────────────────────────────────────────────────────────────

VERDICT_PASS: str = "CIV_PASS"
VERDICT_FAIL: str = "CIV_FAIL"

# ── Rejection codes (CIV namespace — source: rejection_codes.json) ─────────────
# Exact names as registered in enums/shared/rejection_codes.json §namespaces.CIV.
# Any rename requires a corresponding update to the shared rejection code registry.

REJECT_SCHEMA_INCOMPLETE: str        = "REJECT_SCHEMA_INCOMPLETE"
REJECT_ENUM_INVALID: str             = "REJECT_ENUM_INVALID"
REJECT_IDENTITY_CONTAMINATION: str   = "REJECT_IDENTITY_CONTAMINATION"
REJECT_TIME_SHAPE_INVALID: str       = "REJECT_TIME_SHAPE_INVALID"
REJECT_ID_HASH_MISMATCH: str         = "REJECT_ID_HASH_MISMATCH"
REJECT_VERSION_MISMATCH: str         = "REJECT_VERSION_MISMATCH"
REJECT_LANE_FIELD_CONTAMINATION: str = "REJECT_LANE_FIELD_CONTAMINATION"

# ── Check stage identifiers (fixed order, INV-5) ──────────────────────────────
# Used in verdict and audit records. Order mirrors CIV contract §III check order.

STAGE_1_SCHEMA_COMPLETENESS: str    = "1_SCHEMA_COMPLETENESS"
STAGE_2_ENUM_COMPLIANCE: str        = "2_ENUM_REGISTRY_COMPLIANCE"
STAGE_3_IDENTITY_ABSTRACTION: str   = "3_IDENTITY_ABSTRACTION_INTEGRITY"
STAGE_4_TIME_BINDING: str           = "4_TIME_BINDING_COMPLIANCE"
STAGE_5_ID_INTEGRITY: str           = "5_ID_INTEGRITY_CHECK"
STAGE_6_VERSION_SNAPSHOT: str       = "6_VERSION_SNAPSHOT_INTEGRITY"
STAGE_7_LANE_CONTAMINATION: str     = "7_CROSS_FAMILY_FIELD_CONTAMINATION"

# ── Valid lane keys ───────────────────────────────────────────────────────────
# Must match VALID_LANES in ledger/registry_writer.py and registry_reader.py.
# CIV validates objects from all four canonical lanes.

VALID_CIV_LANES: frozenset[str] = frozenset({
    "CPS",
    "CME",
    "CSN",
    "MediaContext",
})

# ── Lanes that carry timestampContext (CIV §III.4) ────────────────────────────
# ── Version snapshot field maps (CIV §III.6) ──────────────────────────────────
#
# Maps: cycle_snapshot key → canonical object field name, per lane.
# Only fields present in the lane's schema are included.
# An empty map means the check is a no-op for that lane (CME).
#
# Name translation required: cycle_snapshot["enumVersion"] maps to
# obj["enumRegistryVersion"] — these are the same semantic version
# expressed with different key names in the two contexts.

CPS_VERSION_FIELD_MAP: dict[str, str] = {
    "schemaVersion":   "schemaVersion",
    "enumVersion":     "enumRegistryVersion",
    "contractVersion": "contractVersion",
}

# CME canonical schema carries no version tracking fields.
# The check is a structural no-op for this lane by design.
CME_VERSION_FIELD_MAP: dict[str, str] = {}

# CSN canonical schema carries contractVersion only.
CSN_VERSION_FIELD_MAP: dict[str, str] = {
    "contractVersion": "contractVersion",
}

MEDIA_CONTEXT_VERSION_FIELD_MAP: dict[str, str] = {
    "schemaVersion":   "schemaVersion",
    "enumVersion":     "enumRegistryVersion",
    "contractVersion": "contractVersion",
}
# Time binding check applies only to lanes whose canonical schema includes
# timestampContext. Pressure lane (CPS) does not carry timestampContext.

TIME_BINDING_LANES: frozenset[str] = frozenset({
    "CME",
    "CSN",
})

# ── Required cycle_snapshot keys (CIV §III.6) ────────────────────────────────

REQUIRED_CYCLE_SNAPSHOT_KEYS: frozenset[str] = frozenset({
    "schemaVersion",
    "enumVersion",
    "contractVersion",
})

# ── Enum compliance field maps (CIV §III.2) ───────────────────────────────────
#
# CPS: canonical object fields are camelCase; PRESSURE_TOKEN_REGISTRY keys are
# snake_case. Map: obj field name → registry key.
CPS_ENUM_FIELD_MAP: dict[str, str] = {
    "signalClass":          "signal_class",
    "environment":          "environment",
    "pressureSignalDomain": "pressure_signal_domain",
    "pressureVector":       "pressure_vector",
    "signalPolarity":       "signal_polarity",
    "observationSource":    "observation_source",
    "castRequirement":      "cast_requirement",
    "tier":                 "tier",
}

# CME: only subtype is registry-validated.
# actorRole, action, objectRole, contextRole are governance-gap fields —
# no contract assigns them to any registry (enums/media/registry.json §openItems).
# Skipping them is governed behaviour, not an omission.
CME_REGISTRY_ENUM_FIELDS: frozenset[str] = frozenset({"subtype"})

# CSN: five narrative token fields validated.
# "subclass" in the canonical object maps to "ncaSubclass" in NARRATIVE_TOKEN_REGISTRY.
# objectRole and contextRole are nullable — skip when None.
CSN_ENUM_FIELD_MAP: dict[str, str] = {
    "actorRole":   "actorRole",
    "action":      "action",
    "objectRole":  "objectRole",
    "contextRole": "contextRole",
    "subclass":    "ncaSubclass",
}
CSN_NULLABLE_ENUM_FIELDS: frozenset[str] = frozenset({"objectRole", "contextRole"})

# MediaContext: only framingType is registry-validated.
MEDIA_CONTEXT_REGISTRY_ENUM_FIELDS: frozenset[str] = frozenset({"framingType"})

# ── Identity abstraction scan fields (CIV §III.3) ─────────────────────────────
#
# Defines which fields in each canonical lane are scanned for proper nouns.
# Enum-token fields (validated by check 2) are excluded from CPS — registry
# tokens are lowercase by construction and will never trigger detection.
# CME/CSN role token fields (actorRole, action, etc.) ARE included because
# their enum governance gap means check 2 does not validate them against any
# registry; CIV §III.3 is the sole downstream identity check for those fields.
#
# Nullable fields are listed separately. When the value is None, skip the scan.

CPS_IDENTITY_SCAN_FIELDS: frozenset[str] = frozenset({
    "observation",
    "sourceSeed",
})

CME_IDENTITY_SCAN_FIELDS: frozenset[str] = frozenset({
    "actorRole",
    "action",
    "eventDescription",
    "sourceReference",
    "timestampContext",
})
CME_IDENTITY_SCAN_NULLABLE_FIELDS: frozenset[str] = frozenset({
    "objectRole",
    "contextRole",
})

CSN_IDENTITY_SCAN_FIELDS: frozenset[str] = frozenset({
    "actorRole",
    "action",
    "eventDescription",
    "sourceReference",
    "timestampContext",
})
CSN_IDENTITY_SCAN_NULLABLE_FIELDS: frozenset[str] = frozenset({
    "objectRole",
    "contextRole",
})

MEDIA_CONTEXT_IDENTITY_SCAN_FIELDS: frozenset[str] = frozenset({
    "contextDescription",
})

# ── Time binding constants (CIV §III.4) ──────────────────────────────────────
#
# Governed phase vocabulary (Ruling A — Phase 11.5).
# Source: Builder governance ruling issued 2026-03-09.
# Values represent seasonal narrative phase context within an NFL season.
# All tokens are lowercase. Optional four-digit year prefix is permitted.
# Format: ^(?:\d{4}_)?<phase_token>$
#
# Examples of valid values:
#   "playoffs", "offseason", "2025_early_season", "2025_trade_deadline_window"
#
# Old week-bucket format (e.g., "2025_W10") is NOT valid under this vocabulary.

TIMESTAMP_CONTEXT_PHASE_TOKENS: frozenset[str] = frozenset({
    "early_season",
    "late_season",
    "mid_season",
    "offseason",
    "playoffs",
    "trade_deadline_window",
})

# Compiled at import time (INV-1). Tokens sorted alphabetically in alternation
# for deterministic pattern definition.
TIMESTAMP_CONTEXT_PATTERN: re.Pattern = re.compile(
    r'^(?:\d{4}_)?'
    r'(?:early_season|late_season|mid_season|offseason|playoffs|trade_deadline_window)$'
)

# ── Import-time assertions ────────────────────────────────────────────────────

assert CIV_VERSION == "CIV-1.0"
assert CIV_VERDICT_SCHEMA_VERSION == "CIV_VERDICT-1.0"
assert VERDICT_PASS == "CIV_PASS"
assert VERDICT_FAIL == "CIV_FAIL"
assert len(VALID_CIV_LANES) == 4
assert len(TIME_BINDING_LANES) == 2
assert len(REQUIRED_CYCLE_SNAPSHOT_KEYS) == 3

_ALL_REJECTION_CODES = (
    REJECT_SCHEMA_INCOMPLETE,
    REJECT_ENUM_INVALID,
    REJECT_IDENTITY_CONTAMINATION,
    REJECT_TIME_SHAPE_INVALID,
    REJECT_ID_HASH_MISMATCH,
    REJECT_VERSION_MISMATCH,
    REJECT_LANE_FIELD_CONTAMINATION,
)
for _code in _ALL_REJECTION_CODES:
    assert isinstance(_code, str) and _code
    assert re.match(r"^[A-Z0-9_]+$", _code), (
        f"Rejection code {_code!r} contains invalid characters."
    )

_ALL_STAGES = (
    STAGE_1_SCHEMA_COMPLETENESS,
    STAGE_2_ENUM_COMPLIANCE,
    STAGE_3_IDENTITY_ABSTRACTION,
    STAGE_4_TIME_BINDING,
    STAGE_5_ID_INTEGRITY,
    STAGE_6_VERSION_SNAPSHOT,
    STAGE_7_LANE_CONTAMINATION,
)
for _stage in _ALL_STAGES:
    assert re.match(r"^\d_[A-Z_]+$", _stage), (
        f"Stage identifier {_stage!r} does not match required pattern."
    )
