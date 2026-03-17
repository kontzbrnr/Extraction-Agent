"""
mcp/mcp_agent.py

Media Context Processor (MCP) — Phase 10.1

Stateless enforcement gate for media_context-typed AUs.

Validates AU against MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md v2.0
structural criteria and emits a Media Context Record (MCR).

Performs no classification, no fingerprint derivation, no lane routing.

Pipeline position:
    Seed Typing → MCP (this gate) → Context Registry

Contract authority:
    MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md v2.0

Invariant compliance:
    INV-1: No module-level mutable state. No instance state. AU never mutated.
    INV-2: No canonical ID or fingerprint computation. sourceSeedID is a
           pass-through of au["id"] — not a derived hash.
    INV-4: Scope guard rejects any AU not typed media_context.
    INV-5: All rule checks delegate to deterministic functions.
           No timestamps, UUIDs, or runtime-derived values in any output.
"""

from __future__ import annotations

from engines.research_agent.agents.classification.classification_ruleset import SEED_TYPE_MEDIA
from engines.research_agent.agents.mcp.mcp_ruleset import (
    MCP_RULESET_VERSION,
    contains_asymmetry_language,
    contains_event_verb,
    contains_prohibited_language,
    contains_proper_noun,
)
from engines.research_agent.agents.mcp.mcp_schema import (
    MCP_LANE_TYPE,
    MCP_MCR_SCHEMA_VERSION,
    MCP_REQUIRED_AU_FIELDS,
    MCP_VERSION,
    MCRValidationError,
    REJECT_MCP_ASYMMETRY_DETECTED,
    REJECT_MCP_EVENT_VERB,
    REJECT_MCP_IDENTITY_CONTAMINATION,
    REJECT_MCP_MISSING_FIELD,
    REJECT_MCP_PROHIBITED_LANGUAGE,
    REJECT_MCP_SCHEMA_INVALID,
    REJECT_MCP_WRONG_LANE,
    validate_mcr,
)


def enforce_mcp(
    au: dict,
    seed_type: str,
) -> tuple[bool, dict | None, dict | None]:
    """Apply MCP enforcement to a single media_context AU.

    Validates structural criteria from MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md
    v2.0 and emits a Media Context Record (MCR) on success.

    Args:
        au:        AU-1.0 conformant dict. Never mutated (INV-1).
        seed_type: Seed type string as returned by seed_typing_router.route().
                   Must equal SEED_TYPE_MEDIA ("media_context") to pass scope guard.

    Returns:
        3-tuple (passed, rejection_or_None, mcr_or_None):

        On PASS:
            (True, None, mcr_dict)

        On REJECT:
            (False, rejection_dict, None)
            rejection_dict contains: rejected=True, reasonCode, sourceSeedID.

    INV-1: au is never mutated.
    INV-2: No fingerprint or canonical ID computation.
    INV-4: Scope guard — rejects if seed_type != "media_context".
    INV-5: Deterministic. Identical (au, seed_type) always produces
           identical output.
    """

    def _build_rejection(reason_code: str) -> dict:
        return {
            "rejected": True,
            "reasonCode": reason_code,
            "sourceSeedID": au.get("id", "__unknown__"),
        }

    # ── Scope guard (INV-4) ───────────────────────────────────────────────────
    if seed_type != SEED_TYPE_MEDIA:
        return (False, _build_rejection(REJECT_MCP_WRONG_LANE), None)

    # ── Required field validation ─────────────────────────────────────────────
    for field in MCP_REQUIRED_AU_FIELDS:
        if field not in au:
            return (False, _build_rejection(REJECT_MCP_MISSING_FIELD), None)

    text: str = au["text"]

    # ── Structural rule checks (§XIV failure conditions) ──────────────────────

    # §V / §XIV: Event verb present → reject.
    if contains_event_verb(text):
        return (False, _build_rejection(REJECT_MCP_EVENT_VERB), None)

    # §XIV: Asymmetry language present → reject.
    if contains_asymmetry_language(text):
        return (False, _build_rejection(REJECT_MCP_ASYMMETRY_DETECTED), None)

    # §XII: Prohibited language present → reject.
    if contains_prohibited_language(text):
        return (False, _build_rejection(REJECT_MCP_PROHIBITED_LANGUAGE), None)

    # §XIII: Proper noun present → reject (secondary defense; IAV precedes MCP).
    if contains_proper_noun(text):
        return (False, _build_rejection(REJECT_MCP_IDENTITY_CONTAMINATION), None)

    # ── MCR assembly ──────────────────────────────────────────────────────────
    canonical: dict = {
        "mcrSchemaVersion": MCP_MCR_SCHEMA_VERSION,
        "laneType": MCP_LANE_TYPE,
        "contractVersion": MCP_VERSION,
        "sourceSeedID": au["id"],
        "contextDescription": text,
        "sourceType": au.get("sourceType", None),
        "timeMarker": au.get("timeMarker", None),
    }

    # ── Scope-lock assertions (before schema validation) ─────────────────────
    assert canonical["laneType"] == MCP_LANE_TYPE
    assert canonical["contractVersion"] == MCP_VERSION

    # ── Schema validation ─────────────────────────────────────────────────────
    try:
        validate_mcr(canonical)
    except MCRValidationError:
        return (False, _build_rejection(REJECT_MCP_SCHEMA_INVALID), None)

    return (True, None, canonical)
