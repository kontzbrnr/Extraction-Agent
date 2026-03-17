"""
ncg/ncg.py
Narrative Critic Gate deterministic enforcement rules.
"""

from __future__ import annotations

from engines.research_agent.agents.nca.nca_ontology import NCA_ASSIGNABLE_SUBCLASSES
from ncg.ncg_audit_log import make_ncg_audit_log
from ncg.ncg_schema import (
    REASON_FAIL_INVALID_SUBCLASS,
    REASON_FAIL_MISSING_CLASSIFICATION,
    REASON_FAIL_MISSING_EVENT_DESCRIPTION,
    REASON_FAIL_MISSING_SOURCE_REFERENCE,
    REASON_FAIL_MISSING_TIMESTAMP_CONTEXT,
    REASON_PASS_ALL_NCG_CHECKS,
    STAGE_1_CLASSIFICATION,
    STAGE_2_SUBCLASS,
    STAGE_3_TIMESTAMP_CONTEXT,
    STAGE_4_EVENT_DESCRIPTION,
    STAGE_5_SOURCE_REFERENCE,
    VERDICT_FAIL,
    VERDICT_PASS,
)


def _make_verdict_record(
    event: dict,
    verdict: str,
    reason_code: str,
    failure_stage: str | None,
) -> dict:
    """Build deterministic NCG verdict record."""
    event_ref = event.get("eventSeedId") or event.get("id") or None
    return {
        "schemaVersion": "NCG_VERDICT-1.0",
        "eventRef": event_ref,
        "verdict": verdict,
        "reasonCode": reason_code,
        "failureStage": failure_stage,
    }


def _build_fail(event: dict, reason_code: str, stage: str) -> tuple[bool, dict, dict]:
    event_ref = event.get("eventSeedId") or event.get("id") or None
    audit_log = make_ncg_audit_log(
        verdict=VERDICT_FAIL,
        reason_code=reason_code,
        failure_stage=stage,
        event_ref=event_ref,
    )
    verdict_record = _make_verdict_record(
        event=event,
        verdict=VERDICT_FAIL,
        reason_code=reason_code,
        failure_stage=stage,
    )
    return (False, verdict_record, audit_log)


def enforce_ncg(event: dict) -> tuple[bool, dict | None, dict]:
    """Enforce deterministic NCG checks in fixed order."""
    if not isinstance(event, dict):
        safe_event = {}
        return _build_fail(
            safe_event,
            REASON_FAIL_MISSING_CLASSIFICATION,
            STAGE_1_CLASSIFICATION,
        )

    classification = event.get("classification")
    if classification not in {"CME", "CSN"}:
        return _build_fail(
            event,
            REASON_FAIL_MISSING_CLASSIFICATION,
            STAGE_1_CLASSIFICATION,
        )

    if classification == "CSN":
        subclass = event.get("standaloneSubclass")
        if subclass not in NCA_ASSIGNABLE_SUBCLASSES:
            return _build_fail(
                event,
                REASON_FAIL_INVALID_SUBCLASS,
                STAGE_2_SUBCLASS,
            )

    timestamp_context = event.get("timestampContext")
    if not isinstance(timestamp_context, str) or len(timestamp_context.strip()) == 0:
        return _build_fail(
            event,
            REASON_FAIL_MISSING_TIMESTAMP_CONTEXT,
            STAGE_3_TIMESTAMP_CONTEXT,
        )

    event_description = event.get("eventDescription")
    if not isinstance(event_description, str) or len(event_description.strip()) == 0:
        return _build_fail(
            event,
            REASON_FAIL_MISSING_EVENT_DESCRIPTION,
            STAGE_4_EVENT_DESCRIPTION,
        )

    source_reference = event.get("sourceReference")
    if not isinstance(source_reference, str) or len(source_reference.strip()) == 0:
        return _build_fail(
            event,
            REASON_FAIL_MISSING_SOURCE_REFERENCE,
            STAGE_5_SOURCE_REFERENCE,
        )

    event_ref = event.get("eventSeedId") or event.get("id") or None
    audit_log = make_ncg_audit_log(
        verdict=VERDICT_PASS,
        reason_code=REASON_PASS_ALL_NCG_CHECKS,
        failure_stage=None,
        event_ref=event_ref,
    )
    return (True, None, audit_log)
