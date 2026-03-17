"""
pressure/assembler_2a_schema.py

2A PSAR Assembly Schema Constants — Phase 7.2

Module-level constants and normalization tables only. No logic.

Defines the ASSEMBLER_2A_VERSION, PSAR schema version, normalization tables
for actorGroup → cast_requirement and domain → pressure_signal_domain mappings.

Contract authority:
    Structural Assembler Contract v1.1 (enum normalization ownership)
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 (PSAR schema)
    Investigation Report 2026-03-07 (domain mapping rulings)

Invariant compliance:
    INV-1: All constants are module-level immutable literals, frozensets, or
           types.MappingProxyType (immutable dict view).
    INV-5: Version pinning with import-time assertion ensures determinism.
"""

from __future__ import annotations
import types
from engines.research_agent.enums.role_token_registry import PRESSURE_TOKEN_REGISTRY

# ── Schema versions ────────────────────────────────────────────────────────────

ASSEMBLER_2A_VERSION: str = "2A-1.0"
PSAR_SCHEMA_VERSION: str = "PSAR_v1.0"
PSAR_AUDIT_SCHEMA_VERSION: str = "2A_AUDIT-1.0"

# ── Version pinning assertion (INV-5) ─────────────────────────────────────────

_EXPECTED_ASSEMBLER_2A_VERSION: str = "2A-1.0"
assert ASSEMBLER_2A_VERSION == _EXPECTED_ASSEMBLER_2A_VERSION, (
    f"ASSEMBLER_2A_VERSION drift: expected {_EXPECTED_ASSEMBLER_2A_VERSION!r}, "
    f"got {ASSEMBLER_2A_VERSION!r}"
)

# ── Rejection reason codes ────────────────────────────────────────────────────

REJECT_2A_ENUM_RESOLUTION_FAILED: str = "REJECT_2A_ENUM_RESOLUTION_FAILED"
REJECT_2A_INVALID_INPUT: str = "REJECT_2A_INVALID_INPUT"

# ── actorGroup normalization table (Ruling 1 — Option B) ──────────────────────
# Maps lowercased NLP-extracted subject spans → cast_requirement enum tokens.
# Version is tied to ASSEMBLER_2A_VERSION. Any addition requires a version bump.
# Lookup is case-insensitive (keys are lowercase).

ACTOR_GROUP_NORMALIZATION_TABLE: types.MappingProxyType = types.MappingProxyType({
    # Direct cast_requirement self-mappings
    "individual_player": "individual_player",
    "position_group":    "position_group",
    "coach":             "coach",
    "front_office":      "front_office",
    "ownership":         "ownership",
    "franchise":         "franchise",
    "league":            "league",
    "group":             "group",
    "unspecified":       "unspecified",
    # Expanded span mappings (from Ruling 1 examples)
    "coaching staff":    "coach",
    "head coach":        "coach",
    "offensive coordinator": "coach",
    "defensive coordinator": "coach",
    "position coach":    "coach",
    "general manager":   "front_office",
    "gm":                "front_office",
    "front office":      "front_office",
    "qb room":           "position_group",
    "quarterback room":  "position_group",
    "offensive line":    "position_group",
    "defensive line":    "position_group",
    "wide receivers":    "position_group",
    "secondary":         "position_group",
    "ownership group":   "ownership",
    "owner":             "ownership",
    "team":              "franchise",
    "organization":      "franchise",
    "club":              "franchise",
    "league office":     "league",
})

# ── Domain normalization table (Ruling 2 + 9 direct mappings) ─────────────────
# Maps PLO-E v2 prose domain labels → pressure_signal_domain enum values.
# All 10 PLO-E domains are mapped. "Absence / Omission" → availability_status
# per Ruling 2 (Option A).

DOMAIN_NORMALIZATION_TABLE: types.MappingProxyType = types.MappingProxyType({
    "Structural Configuration":   "structural_configuration",
    "Authority Distribution":     "authority_distribution",
    "Timing & Horizon":           "timing_horizon",
    "Preparation & Installation": "preparation_installation",
    "Access & Information":       "access_information",
    "Absence / Omission":         "availability_status",
    "Environmental Constraints":  "environmental_constraint",
    "Public Legibility":          "public_legibility",
    "Resource Allocation":        "resource_allocation",
    "Redundancy / Fragility":     "redundancy_fragility",
})

# ── Normalization table registry integrity validation (INV-4) ──────────────
# Asserts at import time that every value in each normalization table is a
# valid token in the corresponding pressure-lane registry set.
# Fails loudly with specific violation info — never silently.
# Any table addition that maps to an invalid token will abort the import.

def _validate_normalization_tables() -> None:
    cast_requirement_tokens: frozenset = PRESSURE_TOKEN_REGISTRY["cast_requirement"]
    domain_tokens: frozenset = PRESSURE_TOKEN_REGISTRY["pressure_signal_domain"]

    actor_violations = {
        k: v
        for k, v in ACTOR_GROUP_NORMALIZATION_TABLE.items()
        if v not in cast_requirement_tokens
    }
    assert not actor_violations, (
        f"ACTOR_GROUP_NORMALIZATION_TABLE contains values not in "
        f"PRESSURE_TOKEN_REGISTRY['cast_requirement']: {actor_violations}. "
        f"All table values must be valid cast_requirement tokens. "
        f"Update the table or bump the registry."
    )

    domain_violations = {
        k: v
        for k, v in DOMAIN_NORMALIZATION_TABLE.items()
        if v not in domain_tokens
    }
    assert not domain_violations, (
        f"DOMAIN_NORMALIZATION_TABLE contains values not in "
        f"PRESSURE_TOKEN_REGISTRY['pressure_signal_domain']: {domain_violations}. "
        f"All table values must be valid pressure_signal_domain tokens. "
        f"Update the table or bump the registry."
    )


_validate_normalization_tables()
