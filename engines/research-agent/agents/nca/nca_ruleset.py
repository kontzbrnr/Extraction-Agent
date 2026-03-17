"""
nca/nca_ruleset.py
NCA Classification Ruleset — NCA_RULE_LOGIC-1.0
Maps event fields to exactly one subclass.
No semantic inference. Rules use explicit field values only.
Contract authority: NARRATIVE-CLASSIFICATION-AGENT.md v1.0 §VII
Governance ruling: 2026-03-08 (9.2-A: subclass mapping rules)
Invariants: INV-1 (no mutable state), INV-5 (deterministic)
"""

from engines.research_agent.agents.nca.nca_ontology import (
    NCA_ASSIGNABLE_SUBCLASSES,
    NCA_RULE_LOGIC_VERSION,
    NCA_SUBCLASS_ANECDOTAL_BEAT,
    NCA_SUBCLASS_CONFLICT_FLASHPOINT,
    NCA_SUBCLASS_CROWD_EVENT,
    NCA_SUBCLASS_PROCEDURAL_CURIOSITY,
    NCA_SUBCLASS_RITUAL_MOMENT,
    REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION,
)

_ = NCA_RULE_LOGIC_VERSION

_CROWD_ACTOR_ROLES: frozenset[str] = frozenset({"fan_base"})

_CONFLICT_ACTIONS: frozenset[str] = frozenset({"challenged_authority"})

_CEREMONIAL_OBJECT_ROLES: frozenset[str] = frozenset(
    {
        "ritual_sequence",
        "award_ceremony",
    }
)
_CEREMONIAL_ACTIONS: frozenset[str] = frozenset(
    {
        "performed",
        "attended",
        "participated",
        "celebrated",
    }
)


def _is_crowd_event(event: dict) -> bool:
    """Rule 1: actorRole == "fan_base" (Ruling 9.2-A)."""
    return event.get("actorRole") in _CROWD_ACTOR_ROLES


def _is_conflict_flashpoint(event: dict) -> bool:
    """Rule 2: action == "challenged_authority" (Ruling 9.2-A)."""
    return event.get("action") in _CONFLICT_ACTIONS


def _is_procedural_curiosity(event: dict) -> bool:
    """Rule 3: unusualProcedural == True (Ruling 9.2-A)."""
    val = event["unusualProcedural"]
    if not isinstance(val, bool):
        raise TypeError(f"unusualProcedural must be bool, got {type(val).__name__!r}")
    return val is True


def _is_ceremonial(event: dict) -> bool:
    """Rule 4: ceremonial_flag (Ruling 9.2-A, design decision)."""
    return (
        event.get("objectRole") in _CEREMONIAL_OBJECT_ROLES
        or event.get("action") in _CEREMONIAL_ACTIONS
    )


def classify_subclass(event: dict) -> str:
    """Deterministically classify event into exactly one assignable subclass."""
    matched: list[str] = []
    if _is_crowd_event(event):
        matched.append(NCA_SUBCLASS_CROWD_EVENT)
    if _is_conflict_flashpoint(event):
        matched.append(NCA_SUBCLASS_CONFLICT_FLASHPOINT)
    if _is_procedural_curiosity(event):
        matched.append(NCA_SUBCLASS_PROCEDURAL_CURIOSITY)
    if _is_ceremonial(event):
        matched.append(NCA_SUBCLASS_RITUAL_MOMENT)

    if len(matched) == 0:
        result = NCA_SUBCLASS_ANECDOTAL_BEAT
        assert result in NCA_ASSIGNABLE_SUBCLASSES
        return result
    if len(matched) == 1:
        result = matched[0]
        assert result in NCA_ASSIGNABLE_SUBCLASSES
        return result
    raise AmbiguousNarrativeClassification(matched)


class AmbiguousNarrativeClassification(Exception):
    """Raised when 2+ subclass rules fire simultaneously."""

    def __init__(self, matched: list[str]) -> None:
        self.matched = matched
        super().__init__(
            f"Ambiguous NCA classification: "
            f"{len(matched)} rules fired simultaneously: {matched!r}"
        )


def make_nca_ambiguity_rejection(event: dict, matched_rules: list[str]) -> dict:
    """Build a deterministic NCA rejection record for ambiguous classification."""
    return {
        "reasonCode": REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION,
        "matchedRules": list(matched_rules),
        "input": dict(event),
        "schemaVersion": "NCA_REJECTION-1.0",
    }
