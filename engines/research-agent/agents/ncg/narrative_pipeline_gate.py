"""
ncg/narrative_pipeline_gate.py
Narrative mint gate enforcement: NCA -> NCG -> Transformer.
"""

from __future__ import annotations

from engines.research_agent.agents.meta.meta_agent import enforce_meta
from engines.research_agent.agents.nca.nca_agent import enforce_nca
from ncg.ncg import enforce_ncg
from engines.research_agent.agents.santa.santa_agent import enforce_santa
from engines.research_engine.agent_runtime.agent_packet import AgentRunPacket
from engines.research_engine.agent_runtime.agent_registry import get_agent, register_default_agents

REJECT_CME_CLASSIFICATION_DEFERRED = "ERR_CME_CLASSIFICATION_DEFERRED"


def enforce_narrative_pipeline(event: dict) -> tuple[bool, list[dict], dict]:
    register_default_agents()
    packet = AgentRunPacket(
        run_id=str(event.get("id", "")) if isinstance(event, dict) else "",
        stage="narrative_pipeline",
        agent_name="narrative",
        payload={"event": event},
        metadata={},
    )
    packet.validate()
    result = get_agent(packet.agent_name).run(packet)
    return (
        bool(result.output.get("passed", False)),
        list(result.output.get("rejections", [])),
        dict(result.output.get("audit", {})),
    )


def _run_narrative_pipeline_impl(event: dict) -> tuple[bool, list[dict], dict]:
    """Run narrative pipeline with strict mint-gate control flow."""
    rejections: list[dict] = []
    composite_audit: dict = {}

    input_event = dict(event) if isinstance(event, dict) else {}

    nca_passed, nca_rejection, nca_result = enforce_nca(input_event)
    composite_audit["nca"] = nca_result if nca_passed else nca_rejection
    if not nca_passed:
        if nca_rejection is not None:
            rejections.append(nca_rejection)
        return (False, rejections, composite_audit)

    event_with_nca_result = dict(input_event)
    if isinstance(nca_result, dict):
        if "classification" in nca_result:
            event_with_nca_result["classification"] = nca_result["classification"]
        if "standaloneSubclass" in nca_result:
            event_with_nca_result["standaloneSubclass"] = nca_result["standaloneSubclass"]

    nca_classification = event_with_nca_result.get("classification")
    # Guard: CME classification is not yet implemented (NCA stub active).
    # Until enforce_nca resolves CME classification, reject any event whose
    # NCA result would route to enforce_meta. This prevents silent lane
    # contamination. Remove this guard when the CME stub is resolved.
    if nca_classification == "CME":
        return (
            False,
            {
                "rejected": True,
                "reason": REJECT_CME_CLASSIFICATION_DEFERRED,
                "note": "CME classification deferred — NCA stub not yet resolved.",
            },
            None,
        )

    ncg_passed, ncg_verdict, ncg_audit = enforce_ncg(event_with_nca_result)
    composite_audit["ncg"] = ncg_audit
    if not ncg_passed:
        if ncg_verdict is not None:
            rejections.append(ncg_verdict)
        return (False, rejections, composite_audit)

    classification = event_with_nca_result.get("classification")
    if classification == "CME":
        t_passed, t_rejection, t_result = enforce_meta(event_with_nca_result)
    elif classification == "CSN":
        t_passed, t_rejection, t_result = enforce_santa(event_with_nca_result)
    else:
        t_passed, t_rejection, t_result = (False, {"reasonCode": "REJECT_PIPELINE_INVALID_CLASSIFICATION"}, None)

    composite_audit["transformer"] = t_result if t_passed else t_rejection

    if not t_passed:
        if t_rejection is not None:
            rejections.append(t_rejection)
        return (False, rejections, composite_audit)

    return (True, [], composite_audit)
