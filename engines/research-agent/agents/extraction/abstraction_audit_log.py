"""
extraction/abstraction_audit_log.py

Abstraction Audit Log — Phase 5.4

Produces a deterministic, in-memory audit record for a single AU's
IAV (Identity Abstraction Validator) decision pass.

No schema file. Record is in-memory only.
Caller is responsible for any persistence.

Contract authority:
    IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md  Section V  (Violation Policy)
    CANONICAL-INTEGRITY-VALIDATOR.md              Section III (Identity Abstraction Integrity)
    PIPELINE-QUALITY-GOVERNOR.md                  Section III (Input Boundary — Critic Verdict Logs)

Invariant compliance:
    INV-1: No module-level mutable state. No runtime-derived values.
    INV-5: Identical inputs always produce identical output.
           No timestamps. No UUIDs. Version constants are pinned imports.
"""

from __future__ import annotations

from engines.research_agent.agents.extraction.abstraction_mapper import ABSTRACTION_MAPPER_VERSION
from engines.research_agent.agents.extraction.proper_noun_detector import PROPER_NOUN_DETECTOR_VERSION

# ── Schema version ────────────────────────────────────────────────────────────

ABSTRACTION_AUDIT_SCHEMA_VERSION: str = "ABSTRACTION_AUDIT-1.0"

# ── Valid decision tokens ─────────────────────────────────────────────────────

_VALID_DECISIONS: frozenset = frozenset({"PASS", "REJECT"})


# ── Record builder ────────────────────────────────────────────────────────────

def make_abstraction_audit_log(
    au_id: str,
    source_reference: str,
    proper_noun_detected: bool,
    decision: str,
    reason_code: str | None = None,
    detector_version: str = PROPER_NOUN_DETECTOR_VERSION,
    mapper_version: str = ABSTRACTION_MAPPER_VERSION,
) -> dict:
    """Return a structured IAV audit record for one AU.

    Args:
        au_id:                  ID of the Atomic Unit being audited.
        source_reference:       Reference to the source material.
        proper_noun_detected:   Result of ProperNounDetector for this AU.
                                Must be exactly bool (not just truthy).
        decision:               IAV decision. Must be "PASS" or "REJECT".
        reason_code:            Rejection reason code. Required (non-empty
                                string) when decision is "REJECT". Must be
                                None when decision is "PASS".
        detector_version:       Version of the ProperNounDetector used.
                                Defaults to PROPER_NOUN_DETECTOR_VERSION.
        mapper_version:         Version of the AbstractionMapper used.
                                Defaults to ABSTRACTION_MAPPER_VERSION.

    Returns:
        Dict with keys: auId, sourceReference, properNounDetected, decision,
        reasonCode, detectorVersion, mapperVersion, schemaVersion.

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
    if not isinstance(proper_noun_detected, bool):
        raise ValueError(
            f"proper_noun_detected must be bool, got {type(proper_noun_detected).__name__}"
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
    if not isinstance(detector_version, str) or not detector_version.strip():
        raise ValueError(
            f"detector_version must be a non-empty string, got {detector_version!r}"
        )
    if not isinstance(mapper_version, str) or not mapper_version.strip():
        raise ValueError(
            f"mapper_version must be a non-empty string, got {mapper_version!r}"
        )

    return {
        "auId": au_id,
        "sourceReference": source_reference,
        "properNounDetected": proper_noun_detected,
        "decision": decision,
        "reasonCode": reason_code,
        "detectorVersion": detector_version,
        "mapperVersion": mapper_version,
        "schemaVersion": ABSTRACTION_AUDIT_SCHEMA_VERSION,
    }
