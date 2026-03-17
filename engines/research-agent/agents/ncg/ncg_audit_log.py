"""
ncg/ncg_audit_log.py
Deterministic NCG audit log constructor.
"""

from __future__ import annotations

from ncg.ncg_schema import NCG_AUDIT_SCHEMA_VERSION, NCG_VERSION


def make_ncg_audit_log(
    verdict: str,
    reason_code: str,
    failure_stage: str | None,
    event_ref: str | None,
) -> dict:
    """Build deterministic NCG verdict audit log record."""
    return {
        "ncgAuditSchemaVersion": NCG_AUDIT_SCHEMA_VERSION,
        "ncgVersion": NCG_VERSION,
        "eventRef": event_ref,
        "verdict": verdict,
        "reasonCode": reason_code,
        "failureStage": failure_stage,
    }
