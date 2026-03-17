"""
Role token registry per lane.

Loads valid token sets from each lane's registry.json at import time.
All token sets are immutable (frozenset). All registries are immutable
(MappingProxyType). No cross-lane references.

INV-1: No mutable state.
INV-4: Lane-isolated — pressure, narrative, and media registries are separate.
           Exception: role tokens form a shared ontology layer. The fields
           narrative.actorRole, narrative.objectRole, and pressure.cast_requirement
           intentionally share abstract role vocabulary. This is governed by the
           ENUM GOVERNANCE RULING — ROLE TOKEN SHARING and is not an INV-4 violation.
INV-5: Version constants pinned to registry version for determinism.
"""

import json
import types
from pathlib import Path

ROLE_TOKEN_REGISTRY_MODULE_VERSION: str = "1.1"

_ENUMS_DIR = Path(__file__).parent

# ─── Pressure Lane ────────────────────────────────────────────────────────────

_pressure_registry = json.loads(
    (_ENUMS_DIR / "pressure" / "registry.json").read_text(encoding="utf-8")
)

PRESSURE_ENUM_REGISTRY_VERSION: str = _pressure_registry["version"]
_EXPECTED_PRESSURE_ENUM_VERSION: str = "ENUM_v1.0"
assert PRESSURE_ENUM_REGISTRY_VERSION == _EXPECTED_PRESSURE_ENUM_VERSION, (
    f"INV-5 violation: pressure registry version changed. "
    f"Expected {_EXPECTED_PRESSURE_ENUM_VERSION!r}, "
    f"got {PRESSURE_ENUM_REGISTRY_VERSION!r}. "
    f"Pin _EXPECTED_PRESSURE_ENUM_VERSION to the new value and bump "
    f"ROLE_TOKEN_REGISTRY_MODULE_VERSION."
)

PRESSURE_TOKEN_REGISTRY: types.MappingProxyType = types.MappingProxyType({
    field: frozenset(values)
    for field, values in _pressure_registry["enums"].items()
})

# ─── Narrative Lane ───────────────────────────────────────────────────────────

_narrative_registry = json.loads(
    (_ENUMS_DIR / "narrative" / "registry.json").read_text(encoding="utf-8")
)

NARRATIVE_ENUM_REGISTRY_VERSION: str = _narrative_registry["version"]
_EXPECTED_NARRATIVE_ENUM_VERSION: str = "ENUM_v1.0"
assert NARRATIVE_ENUM_REGISTRY_VERSION == _EXPECTED_NARRATIVE_ENUM_VERSION, (
    f"INV-5 violation: narrative registry version changed. "
    f"Expected {_EXPECTED_NARRATIVE_ENUM_VERSION!r}, "
    f"got {NARRATIVE_ENUM_REGISTRY_VERSION!r}. "
    f"Pin _EXPECTED_NARRATIVE_ENUM_VERSION to the new value and bump "
    f"ROLE_TOKEN_REGISTRY_MODULE_VERSION."
)

# timeBucketRegistry is excluded: non-fingerprint, ANE-staging only, does not
# persist to canonical CSN objects.
_NARRATIVE_TOKEN_FIELDS = ("actorRole", "action", "objectRole", "contextRole", "ncaSubclass")

NARRATIVE_TOKEN_REGISTRY: types.MappingProxyType = types.MappingProxyType({
    field: frozenset(_narrative_registry["enums"][field]["values"])
    for field in _NARRATIVE_TOKEN_FIELDS
})

# Informational only — derivation authority is santa.santa_ruleset.derive_csn_fingerprint.
# Uses canonical object field names (not registry key names).
# "subclass" is the canonical object field; "ncaSubclass" is the registry key — these differ.
NARRATIVE_FINGERPRINT_FIELDS: frozenset = frozenset({
    "actorRole", "action", "objectRole", "contextRole", "subclass", "sourceReference"
})

NARRATIVE_NULL_PERMITTED_FIELDS: frozenset = frozenset({
    field
    for field in _NARRATIVE_TOKEN_FIELDS
    if _narrative_registry["enums"][field].get("nullPermitted", False)
})

# ─── Media Lane ───────────────────────────────────────────────────────────────

_media_registry = json.loads(
    (_ENUMS_DIR / "media" / "registry.json").read_text(encoding="utf-8")
)

MEDIA_ENUM_REGISTRY_VERSION: str = _media_registry["version"]
_EXPECTED_MEDIA_ENUM_VERSION: str = "ENUM_v1.1"
assert MEDIA_ENUM_REGISTRY_VERSION == _EXPECTED_MEDIA_ENUM_VERSION, (
    f"INV-5 violation: media registry version changed. "
    f"Expected {_EXPECTED_MEDIA_ENUM_VERSION!r}, "
    f"got {MEDIA_ENUM_REGISTRY_VERSION!r}. "
    f"Pin _EXPECTED_MEDIA_ENUM_VERSION to the new value and bump "
    f"ROLE_TOKEN_REGISTRY_MODULE_VERSION."
)

MEDIA_TOKEN_REGISTRY: types.MappingProxyType = types.MappingProxyType({
    field: frozenset(entry["values"] if isinstance(entry, dict) else entry)
    for field, entry in _media_registry["enums"].items()
})

MEDIA_FINGERPRINT_FIELDS: frozenset = frozenset({"subtype"})

# ─── Cross-lane namespace uniqueness guard (INV-4) ───────────────────────────
#
# Enforces that no string token belongs to more than one lane's token sets,
# with the following governed exception:
#
# Role Token Family Exception (ENUM GOVERNANCE RULING — ROLE TOKEN SHARING):
#   The fields listed in _ROLE_TOKEN_FAMILY_FIELDS participate in a shared
#   abstract role ontology across lanes. Tokens in these fields may appear in
#   multiple lane registries. This is intentional and is not a collision.
#   Authorised shared fields:
#       pressure.cast_requirement
#       narrative.actorRole
#       narrative.objectRole
#
# All other fields are subject to strict cross-lane token uniqueness.
# Fails loudly at import time if a non-exempt collision is introduced.
# To add a new exempt field, append its name to _ROLE_TOKEN_FAMILY_FIELDS
# and document the governing contract authority in the comment above.

_ROLE_TOKEN_FAMILY_FIELDS: frozenset = frozenset({
    "cast_requirement",  # pressure lane — governed by ENUM GOVERNANCE RULING
    "actorRole",         # narrative lane — governed by ENUM GOVERNANCE RULING
    "objectRole",        # narrative lane — governed by ENUM GOVERNANCE RULING
})

# Pressure-lane fields excluded from cross-lane uniqueness check.
# These fields contain contextual/spatial classifier tokens that are not
# fingerprint-participating and may share natural-language strings with
# tokens in other lanes without introducing ontological contamination.
#
# Justified exclusions:
#   "environment" — spatial/contextual tag (e.g., "medical" = a facility type).
#                   "medical" also appears in media.subtype as an event category.
#                   These are semantically distinct uses of the same string.
#                   The token overlap is a coincidental natural-language collision,
#                   not a shared semantic identity across lanes.
#                   Note: environment DOES participate in CPS_FINGERPRINT_V1
#                   per PSTA v4 (governance ruling 2026-03-08 overrides the
#                   incorrect Phase 7 Audit comment).
#                   Governed by Phase 7 Audit corrective action 2026-03-07.
_PRESSURE_CONTEXT_FIELDS: frozenset = frozenset({
    "environment",
})
assert len(_PRESSURE_CONTEXT_FIELDS) == 1, (
    "Expanding _PRESSURE_CONTEXT_FIELDS requires an explicit governance ruling. "
    "Each new entry must document why the token collision is semantically distinct "
    "from the colliding token in the other lane's registry."
)

def _assert_cross_lane_token_uniqueness() -> None:
    def _string_tokens(
        registry: types.MappingProxyType,
        exclude_fields: frozenset = frozenset(),
    ) -> set:
        result: set = set()
        for field, token_set in registry.items():
            if field in exclude_fields:
                continue
            if not token_set:
                continue
            if isinstance(next(iter(token_set)), str):
                result.update(token_set)
        return result

    p = _string_tokens(PRESSURE_TOKEN_REGISTRY,
                       exclude_fields=_ROLE_TOKEN_FAMILY_FIELDS | _PRESSURE_CONTEXT_FIELDS)
    n = _string_tokens(NARRATIVE_TOKEN_REGISTRY, exclude_fields=_ROLE_TOKEN_FAMILY_FIELDS)
    m = _string_tokens(MEDIA_TOKEN_REGISTRY)

    violations: dict = {
        k: sorted(v) for k, v in {
            "pressure∩narrative": p & n,
            "pressure∩media":     p & m,
            "narrative∩media":    n & m,
        }.items() if v
    }
    assert not violations, (
        f"INV-4 cross-lane enum namespace collision detected: {violations}. "
        f"Each non-role-token string must belong to exactly one lane's registry. "
        f"If the token belongs to the shared role ontology, add its field name "
        f"to _ROLE_TOKEN_FAMILY_FIELDS with a governing contract reference."
    )


_assert_cross_lane_token_uniqueness()
