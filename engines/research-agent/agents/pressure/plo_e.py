"""
pressure/plo_e.py

PLO-E Gate — Phase 7.1

Stateless enforcement gate that accepts a pressure-capable AU and
externally-provided observations, constructs a PLO dict, validates it
against PLO-1.0 schema, and returns a structured gate tuple.

The semantic content of observations (what is generated, which domains
are selected) is produced by the LLM orchestration layer. This module
enforces structural validity only.

Pipeline position (per PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md §XIV):
    Seed Typing → PLO-E (this gate) → 2A (PSAR Assembly) → PSCA → PSTA

Contract authority:
    PRESSURE-LEGIBLE-OBSERVATION-EXPANSION-AGENT.md v2.0
    PLO-E v2 PDF §II, §III, §V, §VIII

Invariant compliance:
    INV-1: No module-level mutable state. No instance state.
    INV-2: PLO dict contains no canonical ID. ID minting authority is PSTA only.
    INV-3: Input AU is never mutated. Observation dicts are shallow-copied
           into the PLO. All AU-1.0 fields are primitive — shallow copy is
           sufficient.
    INV-5: Gate decision is fully determined by inputs. No timestamps, UUIDs,
           or runtime-derived values in any output.
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.plo_audit_log import make_plo_audit_log
from engines.research_agent.agents.pressure.plo_rejection_handler import (
    REJECT_PLO_SCHEMA_INVALID,
    make_plo_rejection,
)
from engines.research_agent.agents.pressure.plo_schema import PLO_E_VERSION, PLO_SCHEMA_VERSION
from engines.research_agent.agents.pressure.plo_validator import PLOSchemaValidationError, validate_plo


# ── Gate function ──────────────────────────────────────────────────────────────

def enforce_plo_e(
    au: dict,
    observations: list[dict],
    source_reference: str,
) -> tuple[bool, dict | None, dict | None, dict]:
    """Apply PLO-E enforcement to a single pressure-capable AU.

    Constructs a PLO dict from the AU and caller-provided observations,
    then validates it against PLO-1.0 schema. Returns a 4-tuple gate result.

    Args:
        au:             An AU-1.0 conformant dict. Must contain "id" and "text".
                        Never mutated (INV-3).
        observations:   List of observation dicts, each containing "domain"
                        and "observation" keys. Provided by the LLM orchestration
                        layer. Each dict is shallow-copied into the PLO (INV-3).
        source_reference: Source material reference. Passed to audit log.
                          Must be non-empty.

    Returns:
        A 4-tuple (passed, plo_or_None, rejection_or_None, audit_log) where:

        On PASS (PLO passes validation):
            passed            — True
            plo_or_None       — PLO-1.0 dict
            rejection_or_None — None
            audit_log         — PLO_AUDIT-1.0 dict, decision="PASS"

        On REJECT (PLO fails validation):
            passed            — False
            plo_or_None       — None
            rejection_or_None — REJECTION-1.0 dict, reasonCode=REJECT_PLO_SCHEMA_INVALID
            audit_log         — PLO_AUDIT-1.0 dict, decision="REJECT"

    Raises:
        KeyError: If au does not contain "id" or "text". Not swallowed (INV-5).

    INV-1: No state mutation.
    INV-2: No canonical ID computation or reference.
    INV-3: au is never mutated. Observation dicts are shallow-copied.
    INV-5: Deterministic. Identical (au, observations, source_reference)
           always produces identical output.
    """
    plo: dict = {
        "sourceSeedId": au["id"],
        "sourceSeedText": au["text"],
        "schemaVersion": PLO_SCHEMA_VERSION,
        "observations": [dict(obs) for obs in observations],
    }

    try:
        validate_plo(plo)
    except PLOSchemaValidationError as exc:
        reason: str = str(exc)
        rejection = make_plo_rejection(au, reason)
        audit_log = make_plo_audit_log(
            au_id=au["id"],
            source_reference=source_reference,
            observation_count=len(observations),
            domains=None,
            decision="REJECT",
            reason_code=REJECT_PLO_SCHEMA_INVALID,
            plo_e_version=PLO_E_VERSION,
        )
        return (False, None, rejection, audit_log)

    domains: list[str] = [obs["domain"] for obs in plo["observations"]]
    audit_log = make_plo_audit_log(
        au_id=au["id"],
        source_reference=source_reference,
        observation_count=len(plo["observations"]),
        domains=domains,
        decision="PASS",
        reason_code=None,
        plo_e_version=PLO_E_VERSION,
    )
    return (True, plo, None, audit_log)
