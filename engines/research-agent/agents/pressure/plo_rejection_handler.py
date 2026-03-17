"""
pressure/plo_rejection_handler.py

PLO Rejection Handler — Phase 7.1

Defines REJECT_PLO_SCHEMA_INVALID and produces rejection records for
AUs whose externally-provided observations fail PLO schema validation.

Structural mirror of:
    gsd/rejection_handler.py              (Phase 4.4)
    extraction/iav_rejection_handler.py   (Phase 5.5)
    classification/ambiguity_handler.py   (Phase 6.3)

Contract authority:
    PRESSURE-LEGIBLE-OBSERVATION-EXPANSION-AGENT.md v2.0 §X (Failure Conditions)

Invariant compliance:
    INV-1: No module-level mutable state.
    INV-2: No fingerprint or canonical ID computation.
    INV-3: Input AU is never mutated. Rejection record contains a shallow copy.
           All AU-1.0 fields are primitive (str, int) — shallow copy is sufficient.
    INV-5: No timestamps, UUIDs, or runtime-derived values.
"""

from __future__ import annotations

# ── Reason code ────────────────────────────────────────────────────────────────

REJECT_PLO_SCHEMA_INVALID: str = "REJECT_PLO_SCHEMA_INVALID"

# ── Shared rejection schema version ───────────────────────────────────────────

_REJECTION_SCHEMA_VERSION: str = "REJECTION-1.0"


# ── Rejection record builder ───────────────────────────────────────────────────

def make_plo_rejection(au: dict, reason: str) -> dict:
    """Produce a deterministic rejection record for a PLO schema failure.

    The input AU is shallow-copied. The original au dict is never mutated (INV-3).

    Args:
        au:     The AU-1.0 conformant dict whose observations failed validation.
        reason: The human-readable failure reason from PLOSchemaValidationError.

    Returns:
        A rejection record dict with fields:
          reasonCode    — REJECT_PLO_SCHEMA_INVALID (INV-5)
          reason        — specific validation failure message
          au            — shallow copy of the input AU
          schemaVersion — "REJECTION-1.0"

    INV-1: No state mutation.
    INV-2: No fingerprint computation.
    INV-3: Input au is not mutated. Returned au is a copy.
    INV-5: Deterministic. No timestamps, no UUIDs.
    """
    return {
        "reasonCode": REJECT_PLO_SCHEMA_INVALID,
        "reason": reason,
        "au": dict(au),
        "schemaVersion": _REJECTION_SCHEMA_VERSION,
    }
