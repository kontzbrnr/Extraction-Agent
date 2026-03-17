"""
pressure/psca_audit_log.py

PSCA Audit Log — Phase 7.6

Constructs a structured audit record for each PSCA gate pass.

Contract authority:
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 §IX
    PRESSURE-SIGNAL-CRITIC-AGENT.md v2.0 §VI (verdict persistence policy)

Invariant compliance:
    INV-1: Pure function. No state. No side effects.
    INV-5: Deterministic. Identical inputs → identical output.
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.psca_schema import PSCA_AUDIT_SCHEMA_VERSION, PSCA_VERSION


def make_psca_audit_log(
    input_count: int,
    malformed_count: int,
    pass_count: int,
    reject_count: int,
    decision: str,
) -> dict:
    """
    Construct a PSCA gate audit record.

    Args:
        input_count    : Total PSAR records received.
        malformed_count: Records excluded for false enumComplianceFlags (no output).
        pass_count     : Records that received criticStatus = PASS.
        reject_count   : Records that received criticStatus = REJECT.
        decision       : Gate-level summary.
            "EMPTY_INPUT"  — no input records.
            "PASS"         — all evaluable records passed.
            "PARTIAL"      — mixed pass/reject among evaluable records.
            "REJECT_ALL"   — all evaluable records rejected.

    Returns:
        Audit log dict.
    """
    return {
        "auditSchemaVersion": PSCA_AUDIT_SCHEMA_VERSION,
        "pscaVersion":        PSCA_VERSION,
        "inputCount":         input_count,
        "malformedCount":     malformed_count,
        "passCount":          pass_count,
        "rejectCount":        reject_count,
        "decision":           decision,
    }
