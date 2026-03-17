"""
nca/nca_agent.py
NCA Agent — enforce_nca()
Stateless subclass classification for CSN narrative events.
CME classification stub (Phase 9.2 scope: CSN + subclass only).
Contract authority: NARRATIVE-CLASSIFICATION-AGENT.md v1.0
Governance rulings: 2026-03-08 (9.2-A, 9.2-B)
Invariants: INV-1, INV-2, INV-4, INV-5
"""

from __future__ import annotations

from engines.research_agent.agents.nca.nca_ontology import (
    NCA_CLASSIFICATION_CSN,
    NCA_REQUIRED_INPUT_FIELDS,
    NCA_RULE_LOGIC_VERSION,
    NCA_SUBCLASS_TAXONOMY_VERSION,
    NCA_VERSION,
    REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION,
)
from engines.research_agent.agents.nca.nca_ruleset import (
    AmbiguousNarrativeClassification,
    classify_subclass,
    make_nca_ambiguity_rejection,
)

_ = NCA_VERSION
_ = REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION


def _validate_nca_input(event: dict) -> None:
    """Raise KeyError if required keys are missing; TypeError if event is not dict."""
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    missing = [key for key in NCA_REQUIRED_INPUT_FIELDS if key not in event]
    if missing:
        raise KeyError(f"Missing required NCA input fields: {missing!r}")


def _build_nca_rejection(event: dict, reason_code: str) -> dict:
    """Build a deterministic NCA rejection record for non-ambiguity failures."""
    safe_input = dict(event) if isinstance(event, dict) else {}
    return {
        "reasonCode": reason_code,
        "input": safe_input,
        "schemaVersion": "NCA_REJECTION-1.0",
    }


def enforce_nca(event: dict) -> tuple[bool, dict | None, dict | None]:
    """NCA classification gate. Stateless. Does not mutate event."""
    try:
        _validate_nca_input(event)
    except TypeError:
        return (False, _build_nca_rejection(event, "REJECT_NCA_INVALID_INPUT"), None)
    except KeyError:
        return (False, _build_nca_rejection(event, "REJECT_NCA_INVALID_INPUT"), None)

    cme_result = False

    if cme_result:
        return (
            True,
            None,
            {
                "classification": "CME",
                "standaloneSubclass": None,
                "subclassTaxonomyVersion": NCA_SUBCLASS_TAXONOMY_VERSION,
                "subclassRuleLogicVersion": NCA_RULE_LOGIC_VERSION,
            },
        )

    try:
        subclass = classify_subclass(event)
    except AmbiguousNarrativeClassification as exc:
        rejection = make_nca_ambiguity_rejection(event, exc.matched)
        return (False, rejection, None)

    return (
        True,
        None,
        {
            "classification": NCA_CLASSIFICATION_CSN,
            "standaloneSubclass": subclass,
            "subclassTaxonomyVersion": NCA_SUBCLASS_TAXONOMY_VERSION,
            "subclassRuleLogicVersion": NCA_RULE_LOGIC_VERSION,
        },
    )
