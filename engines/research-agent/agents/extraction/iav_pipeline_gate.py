"""
extraction/iav_pipeline_gate.py

IAV Pipeline Gate — Phase 5.6

Stateless enforcement gate that applies Identity Abstraction Validator
logic to a single AU. Blocks downstream access for any AU that contains
a proper noun. Produces a rejection record and audit log on REJECT;
produces only an audit log on PASS.

Pipeline position (per CANONICAL-INTEGRITY-VALIDATOR.md Section II):
    GSD → IAV (this gate) → Seed Typing → Lane Agents

Contract authority:
    IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md  Section V (Violation Policy)
    CANONICAL-INTEGRITY-VALIDATOR.md              Section II (Pipeline Position)
    ORCHESTRATOR-EXECUTION-CONTRACT.md            Section XIV (Global Pipeline Ordering)

Invariant compliance:
    INV-1: No module-level mutable state. No instance state.
    INV-2: No fingerprint or canonical ID computation.
    INV-3: Input AU is never mutated. Rejection record receives a shallow
           copy via make_identity_contamination_rejection (established in 5.5).
    INV-5: Gate decision is derived from contains_proper_noun(), which is
           contract-guaranteed deterministic. No timestamps, UUIDs, or
           runtime-derived values in any output.
"""

from __future__ import annotations

from engines.research_agent.agents.extraction.abstraction_audit_log import make_abstraction_audit_log
from engines.research_agent.agents.extraction.abstraction_mapper import ABSTRACTION_MAPPER_VERSION
from engines.research_agent.agents.extraction.iav_rejection_handler import (
    REJECT_IDENTITY_CONTAMINATION,
    make_identity_contamination_rejection,
)
from engines.research_agent.agents.extraction.proper_noun_detector import (
    PROPER_NOUN_DETECTOR_VERSION,
    contains_proper_noun,
)

# ── Version constant ──────────────────────────────────────────────────────────

IAV_GATE_VERSION: str = "1.0"


# ── Gate function ─────────────────────────────────────────────────────────────

def enforce_iav(
    au: dict,
    source_reference: str,
) -> tuple[bool, dict | None, dict]:
    """Apply IAV enforcement to a single AU.

    Runs ProperNounDetector on au["text"]. If a proper noun is detected,
    the AU is rejected and must not proceed downstream. If no proper noun
    is detected, the AU passes and may proceed to seed typing.

    Args:
        au:               An AU-1.0 conformant dict. Never mutated (INV-3).
        source_reference: Source material reference. Passed to audit log.

    Returns:
        A 3-tuple (passed, rejection_or_None, audit_log) where:

        On PASS (no proper noun detected):
            passed          — True
            rejection_or_None — None
            audit_log       — ABSTRACTION_AUDIT-1.0 dict,
                              decision="PASS", reasonCode=None

        On REJECT (proper noun detected):
            passed          — False
            rejection_or_None — REJECTION-1.0 dict with shallow copy of au,
                              reasonCode=REJECT_IDENTITY_CONTAMINATION
            audit_log       — ABSTRACTION_AUDIT-1.0 dict,
                              decision="REJECT",
                              reasonCode=REJECT_IDENTITY_CONTAMINATION

    INV-1: No state mutation.
    INV-2: No fingerprint computation.
    INV-3: au is never mutated.
    INV-5: Deterministic. Identical (au, source_reference) always produces
           identical output.
    """
    detected: bool = contains_proper_noun(au["text"])

    if detected:
        rejection = make_identity_contamination_rejection(au)
        audit_log = make_abstraction_audit_log(
            au_id=au["id"],
            source_reference=source_reference,
            proper_noun_detected=True,
            decision="REJECT",
            reason_code=REJECT_IDENTITY_CONTAMINATION,
            detector_version=PROPER_NOUN_DETECTOR_VERSION,
            mapper_version=ABSTRACTION_MAPPER_VERSION,
        )
        return (False, rejection, audit_log)

    audit_log = make_abstraction_audit_log(
        au_id=au["id"],
        source_reference=source_reference,
        proper_noun_detected=False,
        decision="PASS",
        reason_code=None,
        detector_version=PROPER_NOUN_DETECTOR_VERSION,
        mapper_version=ABSTRACTION_MAPPER_VERSION,
    )
    return (True, None, audit_log)
