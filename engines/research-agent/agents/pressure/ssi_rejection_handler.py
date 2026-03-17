"""
pressure/ssi_rejection_handler.py

SSI Rejection Handler — Phase 7.2

Produces rejection records for observations that fail extraction.

Contract authority:
    STRUCTURAL-SIGNAL-INTERPRETER.md

Invariant compliance:
    INV-1: No module-level mutable state.
    INV-5: No timestamps, UUIDs, or runtime-derived values.
"""

from __future__ import annotations


def make_ssi_rejection(
    reason_code: str,
    reason: str,
    source_seed_id: str,
    domain: str | None = None,
) -> dict:
    """Produce a deterministic rejection record for SSI extraction failure.

    Args:
        reason_code:    Rejection reason code constant.
        reason:         Human-readable failure reason.
        source_seed_id: ID of the originating AU.
        domain:         Perceptual domain of the failed observation (optional).

    Returns:
        A rejection record dict with REJECTION-1.0 schema.

    INV-1: No state mutation.
    INV-5: Deterministic. No timestamps, no UUIDs.
    """
    return {
        "reasonCode": reason_code,
        "reason": reason,
        "sourceSeedId": source_seed_id,
        "domain": domain,
        "schemaVersion": "REJECTION-1.0",
    }
