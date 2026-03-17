"""
emi/emi_ruleset.py
EMI Structural Classification Ruleset — EMI_RULESET-1.0
Inference prohibition: all rules use explicit lexical markers only.
No ML, no heuristic inference, no external calls.
All rules check the AU "text" field exclusively.
Contract authority: EVENT-MATERIAL-IDENTIFIER.md v1.0, Rules 1-8
Invariants: INV-1 (no mutable state), INV-5 (deterministic)
"""

from __future__ import annotations

from emi.emi_schema import (
    REJECT_EMI_ACTOR_ATTRIBUTION,
    REJECT_EMI_COMPOSITE_BOUNDARY,
    REJECT_EMI_DISCOURSE_INSEPARABLE,
    REJECT_EMI_LEDGER_INCOMPLETE,
    REJECT_EMI_SPECULATIVE_FRAMING,
)

EMI_RULESET_VERSION: str = "EMI_RULESET-1.0"
_EXPECTED_EMI_RULESET_VERSION = "EMI_RULESET-1.0"
assert EMI_RULESET_VERSION == _EXPECTED_EMI_RULESET_VERSION

_SPECULATIVE_MARKERS: frozenset[str] = frozenset(
    {
        "may ",
        "might ",
        "could ",
        "reportedly",
        "allegedly",
        "sources say",
        "reports suggest",
        "is expected to",
        "is likely to",
        "is rumored to",
        "it is believed",
        "hypothetically",
        "in the future",
        "will likely",
        "if ",
        "whether ",
    }
)

_PROCEDURAL_LOCKED_LEXICON: frozenset[str] = frozenset(
    {
        "first time",
        "unexpected",
        "unprecedented",
        "emergency",
        "cancellation",
        "league-mandated",
        "due to hazard",
    }
)


def _has_completed_verb_marker(text_lower: str) -> bool:
    words = text_lower.replace(";", " ").replace(",", " ").split()
    if "has" in words or "have" in words:
        return True
    return any(word.endswith("ed") for word in words)


def check_completed_occurrence(text: str) -> str | None:
    """Rule 1 (Completed Occurrence Requirement)."""
    text_lower = text.lower()
    for marker in _SPECULATIVE_MARKERS:
        if marker in text_lower:
            return REJECT_EMI_SPECULATIVE_FRAMING
    return None


def check_actor_attribution(text: str) -> str | None:
    """Rule 2 (Actor Attribution Requirement)."""
    text_lower = text.lower().strip()
    passive_markers = ("was ", "were ", "has been ", "have been ", "is being ")
    if text_lower.startswith(passive_markers):
        return REJECT_EMI_ACTOR_ATTRIBUTION

    words = text_lower.replace(";", " ").replace(",", " ").split()
    if not words:
        return REJECT_EMI_ACTOR_ATTRIBUTION

    verb_index = None
    for idx, word in enumerate(words):
        if word.endswith("ed") or word in {"has", "have", "was", "were"}:
            verb_index = idx
            break

    if verb_index is None or verb_index == 0:
        return REJECT_EMI_ACTOR_ATTRIBUTION
    return None


def check_ledger_mutation(text: str) -> str | None:
    """Rule 3 (Ledger Mutation / Atomicity Definition)."""
    text_lower = text.lower()
    if not _has_completed_verb_marker(text_lower):
        return REJECT_EMI_LEDGER_INCOMPLETE
    return None


def check_granularity(text: str) -> str | None:
    """Rule 4 (Granularity Rule)."""
    text_lower = text.lower()
    words = text_lower.replace(";", " ").replace(",", " ").split()
    completed_markers = sum(1 for word in words if word.endswith("ed"))
    if (" and " in text_lower or ";" in text_lower) and completed_markers >= 2:
        return REJECT_EMI_COMPOSITE_BOUNDARY
    return None


def check_event_structural_clause(text: str) -> bool:
    """Rule 5 (Event + Structural Clause Rule)."""
    text_lower = text.lower()
    has_event = _has_completed_verb_marker(text_lower)
    has_structural_clause = (
        " because " in text_lower
        or " due to " in text_lower
        or " if " in text_lower
        or " when " in text_lower
    )
    return has_event and has_structural_clause


def check_nested_action_clause(text: str) -> str | None:
    """Rule 6 (Nested Action Clause Rule)."""
    text_lower = text.lower()
    if ", and will " in text_lower or ", which will " in text_lower:
        return REJECT_EMI_DISCOURSE_INSEPARABLE
    return None


def check_public_speech_act(text: str) -> str | None:
    """Rule 7 (Public Speech Acts)."""
    _ = text
    return None


def check_procedural_micro_adjustment(text: str) -> str | None:
    """Rule 8 (Procedural Micro-Adjustments)."""
    text_lower = text.lower()
    procedural_markers = ("adjustment", "modification", "tweak", "update", "change")
    has_procedural_adjustment = any(marker in text_lower for marker in procedural_markers)
    if not has_procedural_adjustment:
        return None

    if any(marker in text_lower for marker in _PROCEDURAL_LOCKED_LEXICON):
        return None
    return REJECT_EMI_LEDGER_INCOMPLETE


def classify_eligibility(au: dict) -> tuple[bool, str | None, bool]:
    """Apply all 8 rules in contract order. Return (passed, code, ploe_fork)."""
    text = ""
    if isinstance(au, dict):
        value = au.get("text", "")
        text = value if isinstance(value, str) else ""

    for rule in (
        check_completed_occurrence,
        check_actor_attribution,
        check_ledger_mutation,
        check_granularity,
    ):
        code = rule(text)
        if code is not None:
            return (False, code, False)

    ploe_fork = check_event_structural_clause(text)

    for rule in (
        check_nested_action_clause,
        check_public_speech_act,
        check_procedural_micro_adjustment,
    ):
        code = rule(text)
        if code is not None:
            return (False, code, False)

    return (True, None, ploe_fork)
