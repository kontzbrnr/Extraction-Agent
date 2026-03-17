"""
pressure/plo_audit_log.py

PLO Audit Log — Phase 7.1

Produces a deterministic, in-memory audit record for a single AU's
PLO-E gate decision.

No schema file. Record is in-memory only.
Caller is responsible for any persistence.

Contract authority:
    PRESSURE-LEGIBLE-OBSERVATION-EXPANSION-AGENT.md v2.0 §VIII (Determinism)

Invariant compliance:
    INV-1: No module-level mutable state. No runtime-derived values.
    INV-5: Identical inputs always produce identical output.
           No timestamps. No UUIDs. Version constants are pinned imports.
           domains serialised as sorted list for deterministic ordering.
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.plo_schema import PLO_E_VERSION

# ── Schema version ─────────────────────────────────────────────────────────────

PLO_AUDIT_SCHEMA_VERSION: str = "PLO_AUDIT-1.0"

# ── Valid decision tokens ──────────────────────────────────────────────────────

_VALID_DECISIONS: frozenset = frozenset({"PASS", "REJECT"})


# ── Record builder ─────────────────────────────────────────────────────────────

def make_plo_audit_log(
    au_id: str,
    source_reference: str,
    observation_count: int | None,
    domains: list[str] | None,
    decision: str,
    reason_code: str | None = None,
    plo_e_version: str = PLO_E_VERSION,
) -> dict:
    """Return a structured PLO-E audit record for one AU.

    Args:
        au_id:             ID of the Atomic Unit being processed.
        source_reference:  Reference to the source material. Must be non-empty.
        observation_count: Number of observations provided. None if unavailable.
        domains:           List of domain strings from observations.
                           On PASS: list of domain strings (sorted for determinism).
                           On REJECT: None.
        decision:          Gate decision. Must be "PASS" or "REJECT".
        reason_code:       Rejection reason code. Required (non-empty string) when
                           decision is "REJECT". Must be None when decision is "PASS".
        plo_e_version:     Version of the PLO-E agent. Defaults to PLO_E_VERSION.

    Returns:
        Dict with keys: auId, sourceReference, observationCount, domains,
        decision, reasonCode, ploEVersion, schemaVersion.

    Raises:
        ValueError: On invalid argument.

    INV-1: No mutable state. No timestamps. No UUIDs.
    INV-5: Deterministic. Identical inputs produce identical output.
           domains stored as sorted list.
    """
    if not isinstance(au_id, str) or not au_id.strip():
        raise ValueError(f"au_id must be a non-empty string, got {au_id!r}")
    if not isinstance(source_reference, str) or not source_reference.strip():
        raise ValueError(
            f"source_reference must be a non-empty string, got {source_reference!r}"
        )
    if decision not in _VALID_DECISIONS:
        raise ValueError(
            f"decision must be one of {sorted(_VALID_DECISIONS)}, got {decision!r}"
        )
    if decision == "REJECT":
        if not isinstance(reason_code, str) or not reason_code.strip():
            raise ValueError(
                "reason_code must be a non-empty string when decision is 'REJECT'"
            )
    if decision == "PASS":
        if reason_code is not None:
            raise ValueError(
                f"reason_code must be None when decision is 'PASS', got {reason_code!r}"
            )

    return {
        "auId": au_id,
        "sourceReference": source_reference,
        "observationCount": observation_count,
        "domains": sorted(domains) if domains is not None else None,
        "decision": decision,
        "reasonCode": reason_code,
        "ploEVersion": plo_e_version,
        "schemaVersion": PLO_AUDIT_SCHEMA_VERSION,
    }
