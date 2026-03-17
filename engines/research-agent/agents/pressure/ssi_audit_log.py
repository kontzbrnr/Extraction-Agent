"""
pressure/ssi_audit_log.py

SSI Audit Log — Phase 7.2

Produces a deterministic, in-memory audit record for SSI gate decision.

No schema file. Record is in-memory only.
Caller is responsible for any persistence.

Contract authority:
    STRUCTURAL-SIGNAL-INTERPRETER.md

Invariant compliance:
    INV-1: No module-level mutable state. No runtime-derived values.
    INV-5: Identical inputs always produce identical output.
           No timestamps. No UUIDs. Version constants are pinned imports.
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.ssi_schema import SSI_VERSION

# ── Schema version ─────────────────────────────────────────────────────────────

SSI_AUDIT_SCHEMA_VERSION: str = "SSI_AUDIT-1.0"


# ── Record builder ─────────────────────────────────────────────────────────────

def make_ssi_audit_log(
    source_seed_id: str,
    total_observations: int,
    extracted_count: int,
    rejected_count: int,
    decision: str,           # "PASS" | "PARTIAL" | "REJECT"
    ssi_version: str = SSI_VERSION,
) -> dict:
    """Return a structured SSI audit record for one PLO processing event.

    Decision rules:
      PASS    = extracted_count == total_observations and rejected_count == 0
      PARTIAL = extracted_count > 0 and rejected_count > 0
      REJECT  = extracted_count == 0

    Args:
        source_seed_id:     ID of the originating Atomic Unit.
        total_observations: Total number of observations in the PLO.
        extracted_count:    Number of successfully extracted PLO-2.0 records.
        rejected_count:     Number of observations that failed extraction.
        decision:           Gate decision. Must be "PASS", "PARTIAL", or "REJECT".
        ssi_version:        Version of the SSI agent. Defaults to SSI_VERSION.

    Returns:
        Dict with keys: sourceSeedId, totalObservations, extractedCount,
        rejectedCount, decision, ssiVersion, schemaVersion.

    INV-1: No mutable state. No timestamps. No UUIDs.
    INV-5: Deterministic. Identical inputs produce identical output.
    """
    return {
        "sourceSeedId": source_seed_id,
        "totalObservations": total_observations,
        "extractedCount": extracted_count,
        "rejectedCount": rejected_count,
        "decision": decision,
        "ssiVersion": ssi_version,
        "schemaVersion": SSI_AUDIT_SCHEMA_VERSION,
    }
