from engines.research_agent.agents.classification.ambiguity_handler import (
    REJECT_AMBIGUOUS_CLASSIFICATION,
    is_ambiguous_classification,
    make_ambiguity_rejection,
)
from engines.research_agent.agents.classification.seed_typing_router import route
from engines.research_agent.agents.classification.multi_match_detector import get_active_signals
from engines.research_agent.agents.classification.classification_audit_log import make_classification_audit_log

ROUTING_GATE_VERSION: str = "1.0"


def enforce_routing_gate(
    au: dict,
    source_reference: str,
) -> tuple[bool, str | None, dict | None, dict]:
    """
    Routing gate for seed type classification.

    Returns a 4-tuple:
        (passed, seed_type, rejection, audit_log)

    PASS:   (True,  seed_type: str, None,       audit_log: dict)
    REJECT: (False, None,           rejection: dict, audit_log: dict)

    Does not mutate au. Holds no state.
    """
    text: str = au["text"]
    active_signals = get_active_signals(text)

    if is_ambiguous_classification(text):
        rejection = make_ambiguity_rejection(au)
        audit_log = make_classification_audit_log(
            au_id=au["id"],
            source_reference=source_reference,
            active_signals=active_signals,
            assigned_seed_type=None,
            decision="REJECT",
            reason_code=REJECT_AMBIGUOUS_CLASSIFICATION,
        )
        return (False, None, rejection, audit_log)

    seed_type: str = route(au)
    audit_log = make_classification_audit_log(
        au_id=au["id"],
        source_reference=source_reference,
        active_signals=active_signals,
        assigned_seed_type=seed_type,
        decision="PASS",
        reason_code=None,
    )
    return (True, seed_type, None, audit_log)
