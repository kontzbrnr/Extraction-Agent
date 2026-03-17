"""
pressure/cps_constructor.py

Canonical Pressure Signal Object Constructor — Phase 8.4

Assembles and validates a single canonical pressure signal object
from pre-computed CPS fields and a pre-minted canonical ID.

This module is the sole authoritative assembly point for CPS objects.
It is imported by PSTA (Phase 8.2) and is available to any downstream
consumer (e.g. CIV) that needs to construct or reconstruct a CPS object.

Responsibilities:
  * Validate canonical_id format pre-assembly
  * Assemble complete 16-field CPS object dict
  * Validate assembled object against canonical_pressure_object.schema.json
  * Return the validated object, or raise on invalid input

This module does NOT:
  * Derive canonical IDs (sole authority: pressure.cps_fingerprint)
  * Apply fallback tokens (sole authority: pressure.psta)
  * Mutate any input dict

Contract authority: PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md v4 §IV
Schema authority:   schemas/pressure/canonical_pressure_object.schema.json
Invariants: INV-2 (no ID derivation), INV-3 (no input mutation),
            INV-5 (deterministic assembly)
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_V1
from engines.research_agent.agents.pressure.cps_id_format import validate_cps_id
from engines.research_agent.agents.pressure.psta_schema import (
    PSTA_CONTRACT_VERSION,
    PSTA_CPS_SCHEMA_VERSION,
    PSTA_LANE_TYPE,
)
from engines.research_agent.schemas.pressure.validator import PressureSchemaValidationError, validate_pressure_object

# ── Version ─────────────────────────────────────────────────────────────────────

CPS_CONSTRUCTOR_VERSION: str = "CPS_CONSTRUCTOR-1.0"

_EXPECTED_CPS_CONSTRUCTOR_VERSION: str = "CPS_CONSTRUCTOR-1.0"
assert CPS_CONSTRUCTOR_VERSION == _EXPECTED_CPS_CONSTRUCTOR_VERSION, (
    f"CPS_CONSTRUCTOR_VERSION drift: expected "
    f"{_EXPECTED_CPS_CONSTRUCTOR_VERSION!r}, got {CPS_CONSTRUCTOR_VERSION!r}"
)


# ── Public constructor ──────────────────────────────────────────────────────────

def build_cps_object(
    cps_fields: dict,
    canonical_id: str,
    enum_registry_version: str,
) -> dict:
    """
    Assemble and validate a canonical pressure signal object.

    Takes pre-computed, post-fallback CPS fields and a pre-minted
    canonical ID. Assembles the complete 16-field CPS object and
    validates it against canonical_pressure_object.schema.json before
    returning.

    This function does NOT derive canonical IDs. The caller (PSTA) is
    responsible for computing canonical_id via derive_cps_fingerprint
    before calling this function.

    Args:
        cps_fields:
            Dict with the 10 CPS fingerprint field names as keys.
            Required keys: signalClass, environment, pressureSignalDomain,
            pressureVector, signalPolarity, observationSource,
            castRequirement, tier, observation, sourceSeed.
            Values must be post-fallback (PSTA applies fallbacks before
            calling this function). None is permitted for tier.
        canonical_id:
            Pre-minted canonical ID. Must match ^CPS_[a-f0-9]{64}$.
        enum_registry_version:
            Enum registry version string to embed in the object.

    Returns:
        A validated canonical pressure signal dict with exactly 16 fields.
        Passes validate_pressure_object without exception.

    Raises:
        ValueError:
            canonical_id is empty, wrong type, or does not match the
            CPS_FINGERPRINT_V1 ID format. Raised pre-assembly.
        KeyError:
            A required key is absent from cps_fields. Caller must
            supply complete fields; constructor does not apply fallbacks.
        PressureSchemaValidationError:
            Assembled object fails schema validation.

    Invariants:
        INV-2 — Does not derive canonical IDs.
        INV-3 — cps_fields is never mutated; returned dict is a fresh object.
        INV-5 — Identical inputs → identical output, bitwise.
    """
    validate_cps_id(canonical_id)

    cps_obj: dict = {
        "laneType":             PSTA_LANE_TYPE,
        "schemaVersion":        PSTA_CPS_SCHEMA_VERSION,
        "signalClass":          cps_fields["signalClass"],
        "environment":          cps_fields["environment"],
        "pressureSignalDomain": cps_fields["pressureSignalDomain"],
        "pressureVector":       cps_fields["pressureVector"],
        "signalPolarity":       cps_fields["signalPolarity"],
        "observationSource":    cps_fields["observationSource"],
        "castRequirement":      cps_fields["castRequirement"],
        "tier":                 cps_fields["tier"],
        "observation":          cps_fields["observation"],
        "sourceSeed":           cps_fields["sourceSeed"],
        "canonicalId":          canonical_id,
        "enumRegistryVersion":  enum_registry_version,
        "fingerprintVersion":   CPS_FINGERPRINT_V1,
        "contractVersion":      PSTA_CONTRACT_VERSION,
    }

    validate_pressure_object(cps_obj)   # raises PressureSchemaValidationError if invalid

    return cps_obj
