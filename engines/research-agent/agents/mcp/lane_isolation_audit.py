"""
mcp/lane_isolation_audit.py

Lane Isolation Audit — Phase 10.6

Schema-driven import-time assertion confirming that the media lane
canonical schema contains zero semantic field overlap with the pressure
lane canonical schema and zero semantic field overlap with the narrative
lane canonical schemas (CME + CSN).

Modelled on the cross-lane token uniqueness guard in
enums/role_token_registry.py (_assert_cross_lane_token_uniqueness).

Structural envelope fields are shared across all lanes by design,
governed by schemas/canonical_envelope.schema.json. They are excluded
from semantic field comparison. Any field NOT in the structural envelope
must be unique to exactly one lane.

Schema authority:
    schemas/media/canonical_media_context_object.schema.json     (MCR)
    schemas/pressure/canonical_pressure_object.schema.json       (CPS)
    schemas/narrative/canonical_narrative_csn_object.schema.json (CSN)
    schemas/cme.schema.json                                       (CME)

Invariant compliance:
    INV-4: Confirms media lane canonical schema is semantically isolated
           from pressure and narrative canonical schemas.
    INV-5: All field sets derived from schema files at import time.
           Deterministic — identical schema files produce identical result.
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Version ───────────────────────────────────────────────────────────────────

LANE_ISOLATION_AUDIT_VERSION: str = "LANE_ISOLATION_AUDIT-1.0"

# ── Schema paths ──────────────────────────────────────────────────────────────

_SCHEMAS_ROOT = Path(__file__).resolve().parents[2] / "schemas"

_MEDIA_SCHEMA_PATH    = _SCHEMAS_ROOT / "media"    / "canonical_media_context_object.schema.json"
_PRESSURE_SCHEMA_PATH = _SCHEMAS_ROOT / "pressure" / "canonical_pressure_object.schema.json"
_CSN_SCHEMA_PATH      = _SCHEMAS_ROOT / "narrative" / "canonical_narrative_csn_object.schema.json"
_CME_SCHEMA_PATH      = _SCHEMAS_ROOT / "cme.schema.json"

# ── Structural envelope fields (shared by design — governed by
#    canonical_envelope.schema.json) ───────────────────────────────────────────
#
# These field names appear in multiple lane schemas intentionally.
# They carry different values per lane (e.g. laneType="MEDIA" vs "PRESSURE")
# but share the same key name. They are NOT semantic contamination.
#
# Any change to this set requires a corresponding update to
# canonical_envelope.schema.json and a version bump here.

_STRUCTURAL_ENVELOPE_FIELDS: frozenset[str] = frozenset({
    "id",
    "laneType",
    "schemaVersion",
    "contractVersion",
    "enumRegistryVersion",
    "fingerprintVersion",
})

# ── Schema loading ────────────────────────────────────────────────────────────

def _load_schema_properties(path: Path) -> frozenset[str]:
    """Load a JSON schema and return its top-level property names."""
    schema = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(schema.get("properties", {}).keys())


_media_all_fields    = _load_schema_properties(_MEDIA_SCHEMA_PATH)
_pressure_all_fields = _load_schema_properties(_PRESSURE_SCHEMA_PATH)
_csn_all_fields      = _load_schema_properties(_CSN_SCHEMA_PATH)
_cme_all_fields      = _load_schema_properties(_CME_SCHEMA_PATH)

# ── Semantic field extraction ─────────────────────────────────────────────────

MEDIA_SEMANTIC_FIELDS:    frozenset[str] = _media_all_fields    - _STRUCTURAL_ENVELOPE_FIELDS
PRESSURE_SEMANTIC_FIELDS: frozenset[str] = _pressure_all_fields - _STRUCTURAL_ENVELOPE_FIELDS
NARRATIVE_SEMANTIC_FIELDS: frozenset[str] = (
    (_csn_all_fields | _cme_all_fields) - _STRUCTURAL_ENVELOPE_FIELDS
)

# ── Envelope integrity guard ─────────────────────────────────────────────────-
#
# Every member of _STRUCTURAL_ENVELOPE_FIELDS must appear in at least
# one lane schema. If a field is listed here but absent from all schemas,
# the set is stale and must be corrected.

_all_schema_fields = _media_all_fields | _pressure_all_fields | _csn_all_fields | _cme_all_fields
_unrecognised_envelope = _STRUCTURAL_ENVELOPE_FIELDS - _all_schema_fields
assert not _unrecognised_envelope, (
    f"LANE_ISOLATION_AUDIT: _STRUCTURAL_ENVELOPE_FIELDS contains field(s) "
    f"absent from all canonical schemas: {sorted(_unrecognised_envelope)}. "
    f"Update _STRUCTURAL_ENVELOPE_FIELDS to match canonical_envelope.schema.json."
)

# ── Lane isolation assertions (INV-4) ─────────────────────────────────────────

_media_pressure_contamination: frozenset[str] = (
    MEDIA_SEMANTIC_FIELDS & PRESSURE_SEMANTIC_FIELDS
)
assert not _media_pressure_contamination, (
    f"INV-4 VIOLATION — Media lane canonical schema contains pressure semantic "
    f"field(s): {sorted(_media_pressure_contamination)}. "
    f"Remove these fields from canonical_media_context_object.schema.json "
    f"or reclassify them as structural envelope fields with contract authority."
)

_media_narrative_contamination: frozenset[str] = (
    MEDIA_SEMANTIC_FIELDS & NARRATIVE_SEMANTIC_FIELDS
)
assert not _media_narrative_contamination, (
    f"INV-4 VIOLATION — Media lane canonical schema contains narrative semantic "
    f"field(s): {sorted(_media_narrative_contamination)}. "
    f"Remove these fields from canonical_media_context_object.schema.json "
    f"or reclassify them as structural envelope fields with contract authority."
)

_pressure_narrative_contamination: frozenset[str] = (
    PRESSURE_SEMANTIC_FIELDS & NARRATIVE_SEMANTIC_FIELDS
)
assert not _pressure_narrative_contamination, (
    f"INV-4 VIOLATION — Pressure and narrative lane canonical schemas share "
    f"semantic field(s): {sorted(_pressure_narrative_contamination)}. "
    f"Each semantic field must belong to exactly one lane."
)

# ── Import-time version assertion ─────────────────────────────────────────────

assert LANE_ISOLATION_AUDIT_VERSION == "LANE_ISOLATION_AUDIT-1.0"

# ── Public report function ────────────────────────────────────────────────────

def get_lane_isolation_report() -> dict:
    """Return a structured lane isolation audit report.

    Callable after successful import (assertions passed).
    Returns a snapshot of the field sets and contamination results.

    Returns:
        Dict with keys:
            passed (bool)                     — True if both checks pass
            mediaSemanticFields (list[str])   — sorted media semantic fields
            pressureSemanticFields (list[str])— sorted pressure semantic fields
            narrativeSemanticFields (list[str])— sorted narrative semantic fields
            mediaPressureContamination (list[str]) — empty if clean
            mediaNarrativeContamination (list[str]) — empty if clean
            mediaFieldCount (int)
            pressureFieldCount (int)
            narrativeFieldCount (int)
            auditVersion (str)

    INV-5: Deterministic — identical schema files produce identical report.
    """
    media_pressure = sorted(MEDIA_SEMANTIC_FIELDS & PRESSURE_SEMANTIC_FIELDS)
    media_narrative = sorted(MEDIA_SEMANTIC_FIELDS & NARRATIVE_SEMANTIC_FIELDS)

    return {
        "passed":                       not media_pressure and not media_narrative,
        "mediaSemanticFields":          sorted(MEDIA_SEMANTIC_FIELDS),
        "pressureSemanticFields":       sorted(PRESSURE_SEMANTIC_FIELDS),
        "narrativeSemanticFields":      sorted(NARRATIVE_SEMANTIC_FIELDS),
        "mediaPressureContamination":   media_pressure,
        "mediaNarrativeContamination":  media_narrative,
        "mediaFieldCount":              len(MEDIA_SEMANTIC_FIELDS),
        "pressureFieldCount":           len(PRESSURE_SEMANTIC_FIELDS),
        "narrativeFieldCount":          len(NARRATIVE_SEMANTIC_FIELDS),
        "auditVersion":                 LANE_ISOLATION_AUDIT_VERSION,
    }

