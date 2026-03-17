"""
extraction/iav_rejection_handler.py

IAV Rejection Handler — Phase 5.5

Defines the REJECT_IDENTITY_CONTAMINATION reason code (re-exported from
extraction.proper_noun_detector) and produces rejection records for AUs
that failed identity abstraction enforcement.

Structural mirror of gsd/rejection_handler.py (Phase 4.4).
Subject is an AU (Atomic Unit), not a REC.

Contract authority:
    IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md  Section V  (Violation Policy)
    CANONICAL-INTEGRITY-VALIDATOR.md              Section III (Identity Abstraction Integrity)

Invariant compliance:
    INV-1: No module-level mutable state.
    INV-2: No fingerprint or canonical ID computation.
    INV-3: Input AU is never mutated. Rejection record contains a
           shallow copy. All AU-1.0 fields are primitive (str, int),
           so shallow copy is sufficient.
    INV-5: No timestamps, UUIDs, or runtime-derived values.
           Rejection records are fully determined by input.
"""

from engines.research_agent.agents.extraction.proper_noun_detector import REJECT_IDENTITY_CONTAMINATION  # noqa: F401

_REJECTION_SCHEMA_VERSION: str = "REJECTION-1.0"


def make_identity_contamination_rejection(au: dict) -> dict:
    """Produce a deterministic rejection record for an identity-contaminated AU.

    The input AU is shallow-copied into the rejection record. The original
    au dict is never mutated (INV-3). All AU-1.0 fields are primitive
    (str, int), so a shallow copy is sufficient.

    Args:
        au: An AU-1.0 conformant dict that failed identity abstraction
            enforcement (proper noun detected in text field).

    Returns:
        A rejection record dict with fields:
          reasonCode    — pinned to REJECT_IDENTITY_CONTAMINATION (INV-5)
          au            — shallow copy of the input AU
          schemaVersion — "REJECTION-1.0"

    INV-1: No state mutation.
    INV-2: No fingerprint computation.
    INV-3: Input au is not mutated. Returned au is a copy.
    INV-5: Deterministic. No timestamps, no UUIDs.
    """
    return {
        "reasonCode": REJECT_IDENTITY_CONTAMINATION,
        "au": dict(au),
        "schemaVersion": _REJECTION_SCHEMA_VERSION,
    }
