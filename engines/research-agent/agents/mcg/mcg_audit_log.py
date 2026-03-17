"""
mcg/mcg_audit_log.py

Media Critic Gate audit log builder.

Pure function — no side effects, no state, no I/O.

Invariants: INV-1 (no state), INV-5 (deterministic)
"""

from __future__ import annotations

from mcg.mcg_schema import MCG_AUDIT_SCHEMA_VERSION, MCG_VERSION


def make_mcg_audit_log(
    verdict: str,
    reason_code: str,
    failure_stage: str | None,
    source_seed_ref: str | None,
) -> dict:
    """Build a deterministic MCG audit log record.

    Args:
        verdict:         "PASS" or "FAIL".
        reason_code:     One of the MCG reason code constants.
        failure_stage:   Stage identifier string, or None on PASS.
        source_seed_ref: MCR sourceSeedID, or None if unavailable.

    Returns:
        Audit log dict. Identical inputs always produce identical output.

    INV-1: No state mutation.
    INV-5: No timestamps, UUIDs, or runtime-derived values.
    """
    return {
        "schemaVersion": MCG_AUDIT_SCHEMA_VERSION,
        "gateVersion": MCG_VERSION,
        "verdict": verdict,
        "reasonCode": reason_code,
        "failureStage": failure_stage,
        "sourceSeedRef": source_seed_ref,
    }
