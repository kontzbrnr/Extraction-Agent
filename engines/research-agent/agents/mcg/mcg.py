"""
mcg/mcg.py

Media Critic Gate — Phase 10.3

Stateless contamination gate for MCR objects.

Inspects MCR contextDescription for pressure conversion attempts
and narrative synthesis attempts. Emits a named FAIL verdict for
each contamination vector. Passes clean MCRs to Media Mint.

Pipeline position:
    MCP → MCG (this gate) → Media Mint

Contract authority:
    MEDIA-FRAMING-AUDIT-AGENT.md §PROHIBITIONS

Invariant compliance:
    INV-1: No module-level mutable state. No instance state. MCR never mutated.
    INV-4: Scope-lock on laneType == "MEDIA" before any contamination check.
    INV-5: All contamination checks delegate to deterministic,
           module-level-compiled pattern functions. No timestamps,
           UUIDs, or runtime-derived values in any output.
"""

from __future__ import annotations

from engines.research_agent.agents.classification.classification_ruleset import (
    contains_asymmetry_language,
    contains_event_verb,
)
from mcg.mcg_audit_log import make_mcg_audit_log
from mcg.mcg_schema import (
    MCG_REQUIRED_MCR_FIELDS,
    MCG_VERDICT_SCHEMA_VERSION,
    REASON_PASS_ALL_MCG_CHECKS,
    REASON_REJECT_INVALID_INPUT,
    REASON_REJECT_MISSING_FIELD,
    REASON_REJECT_NARRATIVE_SYNTHESIS,
    REASON_REJECT_PRESSURE_CONVERSION,
    REASON_REJECT_WRONG_LANE,
    STAGE_1_INPUT_GUARD,
    STAGE_2_FIELD_GUARD,
    STAGE_3_SCOPE_LOCK,
    STAGE_4_PRESSURE_CONVERSION,
    STAGE_5_NARRATIVE_SYNTHESIS,
    VERDICT_FAIL,
    VERDICT_PASS,
)

_MEDIA_LANE_TYPE: str = "MEDIA"


def _get_seed_ref(mcr: object) -> str | None:
    if isinstance(mcr, dict):
        return mcr.get("sourceSeedID") or None
    return None


def _build_fail(
    mcr: object,
    reason_code: str,
    stage: str,
) -> tuple[bool, dict, dict]:
    seed_ref = _get_seed_ref(mcr)
    audit_log = make_mcg_audit_log(
        verdict=VERDICT_FAIL,
        reason_code=reason_code,
        failure_stage=stage,
        source_seed_ref=seed_ref,
    )
    verdict_record = {
        "schemaVersion": MCG_VERDICT_SCHEMA_VERSION,
        "sourceSeedRef": seed_ref,
        "verdict": VERDICT_FAIL,
        "reasonCode": reason_code,
        "failureStage": stage,
    }
    return (False, verdict_record, audit_log)


def enforce_mcg(mcr: object) -> tuple[bool, dict | None, dict]:
    """Apply Media Critic Gate checks to a single MCR.

    Checks execute in strict priority order. First failing check returns
    immediately — no subsequent checks run.

    Args:
        mcr: MCR dict as emitted by enforce_mcp. Never mutated (INV-1).

    Returns:
        3-tuple (passed, verdict_or_None, audit_log):

        On PASS:
            (True, None, audit_log)

        On FAIL:
            (False, verdict_record, audit_log)
            verdict_record contains: schemaVersion, sourceSeedRef,
            verdict, reasonCode, failureStage.

    INV-1: mcr is never mutated.
    INV-4: Scope-lock on laneType precedes all contamination checks.
    INV-5: Deterministic. Identical mcr always produces identical output.
    """

    # ── Check 1: Input guard ──────────────────────────────────────────────────
    if not isinstance(mcr, dict):
        return _build_fail(mcr, REASON_REJECT_INVALID_INPUT, STAGE_1_INPUT_GUARD)

    # ── Check 2: Required field guard ─────────────────────────────────────────
    for field in MCG_REQUIRED_MCR_FIELDS:
        if field not in mcr:
            return _build_fail(mcr, REASON_REJECT_MISSING_FIELD, STAGE_2_FIELD_GUARD)

    # ── Check 3: Scope-lock (INV-4) ───────────────────────────────────────────
    if mcr["laneType"] != _MEDIA_LANE_TYPE:
        return _build_fail(mcr, REASON_REJECT_WRONG_LANE, STAGE_3_SCOPE_LOCK)

    context: str = mcr["contextDescription"]

    # ── Check 4: Pressure conversion attempt ──────────────────────────────────
    # Asymmetry language in contextDescription signals that the MCR encodes
    # pressure-routable content. Prohibited by MEDIA-FRAMING-AUDIT-AGENT.md
    # §PROHIBITIONS: "route outputs into pressure signal logic".
    if contains_asymmetry_language(context):
        return _build_fail(
            mcr, REASON_REJECT_PRESSURE_CONVERSION, STAGE_4_PRESSURE_CONVERSION
        )

    # ── Check 5: Narrative synthesis attempt ──────────────────────────────────
    # Event verb presence in contextDescription signals that the MCR encodes
    # event-bearing content that would route to narrative transformation.
    # Prohibited by MEDIA-FRAMING-AUDIT-AGENT.md §PROHIBITIONS:
    # "translate framing into events", "create narrative arcs".
    if contains_event_verb(context):
        return _build_fail(
            mcr, REASON_REJECT_NARRATIVE_SYNTHESIS, STAGE_5_NARRATIVE_SYNTHESIS
        )

    # ── PASS ──────────────────────────────────────────────────────────────────
    seed_ref = mcr.get("sourceSeedID") or None
    audit_log = make_mcg_audit_log(
        verdict=VERDICT_PASS,
        reason_code=REASON_PASS_ALL_MCG_CHECKS,
        failure_stage=None,
        source_seed_ref=seed_ref,
    )
    return (True, None, audit_log)
