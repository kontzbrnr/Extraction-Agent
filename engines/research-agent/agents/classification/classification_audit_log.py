"""
classification/classification_audit_log.py

Classification Audit Log — Phase 6.5

Produces a deterministic, in-memory audit record for a single AU's
seed typing classification decision.

No schema file. Record is in-memory only.
Caller is responsible for any persistence.

Contract authority:
    CREATIVE-LIBRARY-EXTRACTION-AGENT.md   §X  (single seed type per AU)
    PIPELINE-QUALITY-GOVERNOR.md           §III (Critic Verdict Logs)
    classification_ruleset.py / 6.1        (VALID_SEED_TYPES, rule version)
    seed_typing_router.py  / 6.2           (router version)

Invariant compliance:
    INV-1: No module-level mutable state. No runtime-derived values.
    INV-5: active_signals serialized via sorted() for deterministic list.
           Identical inputs always produce identical output.
           No timestamps. No UUIDs.
"""

from __future__ import annotations

from engines.research_agent.agents.classification.classification_ruleset import (
    CLASSIFICATION_RULE_VERSION,
    VALID_SEED_TYPES,
)
from engines.research_agent.agents.classification.seed_typing_router import SEED_TYPING_ROUTER_VERSION

# ── Schema version ────────────────────────────────────────────────────────────

CLASSIFICATION_AUDIT_SCHEMA_VERSION: str = "CLASSIFICATION_AUDIT-1.0"

# ── Valid decisions ───────────────────────────────────────────────────────────

_VALID_DECISIONS: frozenset = frozenset({"PASS", "REJECT"})


# ── Record builder ────────────────────────────────────────────────────────────

def make_classification_audit_log(
    au_id: str,
    source_reference: str,
    active_signals: frozenset,
    assigned_seed_type: str | None,
    decision: str,
    reason_code: str | None = None,
    rule_version: str = CLASSIFICATION_RULE_VERSION,
    router_version: str = SEED_TYPING_ROUTER_VERSION,
) -> dict:
    """Return a structured classification audit record for one AU.

    Args:
        au_id:              ID of the Atomic Unit classified.
        source_reference:   Reference to source material.
        active_signals:     frozenset of signal names that fired
                            (from get_active_signals()). Must be
                            exactly frozenset — not list or set.
        assigned_seed_type: Seed type assigned on PASS (must be in
                            VALID_SEED_TYPES). Must be None on REJECT.
        decision:           "PASS" or "REJECT".
        reason_code:        Rejection reason code. Required (non-empty
                            string) when decision is "REJECT". Must be
                            None when decision is "PASS".
        rule_version:       Classification rule version. Defaults to
                            CLASSIFICATION_RULE_VERSION.
        router_version:     Seed typing router version. Defaults to
                            SEED_TYPING_ROUTER_VERSION.

    Returns:
        Dict with keys: auId, sourceReference, activeSignals,
        assignedSeedType, decision, reasonCode, ruleVersion,
        routerVersion, schemaVersion.

        activeSignals is stored as sorted(active_signals) — a
        deterministic list (INV-5).

    Raises:
        ValueError: On any invalid argument.

    INV-1: No mutable state. No timestamps. No UUIDs.
    INV-5: Deterministic. Identical inputs produce identical output.
    """
    if not isinstance(au_id, str) or not au_id.strip():
        raise ValueError(
            f"au_id must be a non-empty string, got {au_id!r}"
        )
    if not isinstance(source_reference, str) or not source_reference.strip():
        raise ValueError(
            f"source_reference must be a non-empty string, got {source_reference!r}"
        )
    if not isinstance(active_signals, frozenset):
        raise ValueError(
            f"active_signals must be a frozenset, got {type(active_signals).__name__}"
        )
    if decision not in _VALID_DECISIONS:
        raise ValueError(
            f"decision must be one of {sorted(_VALID_DECISIONS)}, got {decision!r}"
        )
    if decision == "PASS":
        if assigned_seed_type not in VALID_SEED_TYPES:
            raise ValueError(
                f"assigned_seed_type must be in VALID_SEED_TYPES when decision "
                f"is 'PASS', got {assigned_seed_type!r}"
            )
        if reason_code is not None:
            raise ValueError(
                f"reason_code must be None when decision is 'PASS', "
                f"got {reason_code!r}"
            )
    if decision == "REJECT":
        if assigned_seed_type is not None:
            raise ValueError(
                f"assigned_seed_type must be None when decision is 'REJECT', "
                f"got {assigned_seed_type!r}"
            )
        if not isinstance(reason_code, str) or not reason_code.strip():
            raise ValueError(
                "reason_code must be a non-empty string when decision is 'REJECT'"
            )
    if not isinstance(rule_version, str) or not rule_version.strip():
        raise ValueError(
            f"rule_version must be a non-empty string, got {rule_version!r}"
        )
    if not isinstance(router_version, str) or not router_version.strip():
        raise ValueError(
            f"router_version must be a non-empty string, got {router_version!r}"
        )

    return {
        "auId": au_id,
        "sourceReference": source_reference,
        "activeSignals": sorted(active_signals),
        "assignedSeedType": assigned_seed_type,
        "decision": decision,
        "reasonCode": reason_code,
        "ruleVersion": rule_version,
        "routerVersion": router_version,
        "schemaVersion": CLASSIFICATION_AUDIT_SCHEMA_VERSION,
    }
