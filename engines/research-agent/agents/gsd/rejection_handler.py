"""
gsd/rejection_handler.py

Rejection Handler — Phase 4.4

Defines the REJECT_ATOMICITY_UNCLEAR reason code and produces
rejection records for RECs that cannot be deterministically split.

Contract authority:
  CREATIVE-LIBRARY-EXTRACTION-AGENT.md  Section XI
  GLOBAL-SPLIT-DOCTRINE.md              Section VI
  GSD v1.0 Section X (Determinism Lock) — rejection decisions
  and reason codes are covered by the determinism guarantee.

Invariant compliance:
  INV-1: No module-level mutable state.
  INV-2: No fingerprint or canonical ID computation.
  INV-3: Input REC is never mutated; rejection record contains a
         shallow copy (all REC-1.0 fields are primitive).
  INV-5: Rejection records contain only pinned constants and a
         deterministic copy of the input. No timestamps, UUIDs,
         or runtime-derived values permitted.
"""

from engines.research_agent.agents.extraction.composite_marker import ERR_COMPOSITE_BOUNDARY_UNCLEAR

# GSD-layer reason code for atomicity rejection.
# Value is pinned to the contract-specified ERR_COMPOSITE_BOUNDARY_UNCLEAR.
# Never derive this from config, env vars, or runtime sources (INV-5).
REJECT_ATOMICITY_UNCLEAR: str = ERR_COMPOSITE_BOUNDARY_UNCLEAR

_REJECTION_SCHEMA_VERSION: str = "REJECTION-1.0"


def make_atomicity_rejection(rec: dict) -> dict:
    """Produce a deterministic rejection record for a boundary-unclear REC.

    The input REC is shallow-copied into the rejection record. The original
    rec dict is never mutated (INV-3). All REC-1.0 fields are primitive
    (str, bool), so a shallow copy is sufficient.

    Args:
        rec: A REC-1.0 conformant dict that failed atomicity enforcement.

    Returns:
        A rejection record dict with fields:
          reasonCode    — pinned to REJECT_ATOMICITY_UNCLEAR (INV-5)
          rec           — shallow copy of the input REC
          schemaVersion — "REJECTION-1.0"
    """
    return {
        "reasonCode": REJECT_ATOMICITY_UNCLEAR,
        "rec": dict(rec),
        "schemaVersion": _REJECTION_SCHEMA_VERSION,
    }
