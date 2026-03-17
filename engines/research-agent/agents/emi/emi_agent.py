"""
emi/emi_agent.py
EMI Agent — enforce_emi()
Stateless invocation contract.
Pipeline: input validation → IAV gate → eligibility classification → NAR
Contract authority: EVENT-MATERIAL-IDENTIFIER.md v1.0 (Stabilized)
Governance ruling: 2026-03-08 (9.1.4 IAV gate)
Invariants: INV-1, INV-2, INV-3, INV-4, INV-5
"""

from __future__ import annotations

from emi import emi_ruleset
from emi.emi_fingerprint import derive_emi_event_id
from emi.emi_ruleset import classify_eligibility
from emi.emi_schema import (
    EMI_AU_SCHEMA_VERSION,
    EMI_NAR_SCHEMA_VERSION,
    EMI_REQUIRED_AU_FIELDS,
    EMINARValidationError,
    REJECT_EMI_INVALID_SEED,
    validate_nar,
)
from engines.research_engine.agent_runtime.agent_packet import AgentRunPacket
from engines.research_engine.agent_runtime.agent_registry import get_agent, register_default_agents


def _validate_au_input(au: dict) -> str | None:
    """Return rejection code if AU is invalid, None if valid."""
    if not isinstance(au, dict):
        return REJECT_EMI_INVALID_SEED

    if not EMI_REQUIRED_AU_FIELDS.issubset(set(au.keys())):
        return REJECT_EMI_INVALID_SEED

    if au.get("schemaVersion") != EMI_AU_SCHEMA_VERSION:
        return REJECT_EMI_INVALID_SEED

    return None


def _build_rejection(au: dict, reason_code: str) -> dict:
    """Build a deterministic EMI rejection record."""
    return {
        "reasonCode": reason_code,
        "au": dict(au),
        "schemaVersion": "REJECTION-1.0",
    }


def _extract_nar_fields(au: dict) -> dict:
    """Extract actorGroup and actionVerb from AU text."""
    text = au.get("text", "")
    if not isinstance(text, str):
        return {"actorGroup": "", "actionVerb": ""}

    parts = text.split()
    actor_group = parts[0] if len(parts) >= 1 else ""
    action_verb = parts[1] if len(parts) >= 2 else ""
    return {
        "actorGroup": actor_group,
        "actionVerb": action_verb,
    }


def _is_unusual_procedural(text: str) -> bool:
    """Return True if text contains an unusual procedural marker."""
    text_lower = text.lower()
    return any(marker in text_lower for marker in emi_ruleset._PROCEDURAL_LOCKED_LEXICON)


def enforce_emi(au: dict) -> tuple[bool, dict | None, dict | None]:
    register_default_agents()
    packet = AgentRunPacket(
        run_id=str(au.get("id", "")) if isinstance(au, dict) else "",
        stage="emi_pipeline",
        agent_name="emi",
        payload={"au": au},
        metadata={},
    )
    packet.validate()
    result = get_agent(packet.agent_name).run(packet)
    return (
        bool(result.output.get("passed", False)),
        result.output.get("rejection"),
        result.output.get("nar"),
    )


def _run_emi_impl(au: dict) -> tuple[bool, dict | None, dict | None]:
    """EMI gate. Stateless. Does not mutate au."""
    invalid_code = _validate_au_input(au)
    if invalid_code is not None:
        safe_au = au if isinstance(au, dict) else {}
        return (False, _build_rejection(safe_au, REJECT_EMI_INVALID_SEED), None)

    extraction_packet = AgentRunPacket(
        run_id=str(au.get("id", "")),
        stage="iav_gate",
        agent_name="extraction",
        payload={
            "au": au,
            "source_reference": au["sourceReference"],
        },
        metadata={},
    )
    extraction_packet.validate()
    extraction_result = get_agent(extraction_packet.agent_name).run(extraction_packet)
    iav_passed = bool(extraction_result.output.get("passed", False))
    iav_rejection = extraction_result.output.get("rejection")
    if not iav_passed:
        return (False, iav_rejection, None)

    eligible, code, ploe_fork = classify_eligibility(au)
    if not eligible:
        return (False, _build_rejection(au, code or REJECT_EMI_INVALID_SEED), None)

    event_id = derive_emi_event_id(au)
    nar_fields = _extract_nar_fields(au)
    nar = {
        "eventID": event_id,
        "sourceSeedID": au["id"],
        "actorGroup": nar_fields["actorGroup"],
        "actionVerb": nar_fields["actionVerb"],
        "ledgerMutation": True,
        "unusualProcedural": _is_unusual_procedural(au["text"]),
        "narSchemaVersion": EMI_NAR_SCHEMA_VERSION,
        "ploe_fork_required": ploe_fork,
    }
    validate_nar(nar)
    return (True, None, nar)
