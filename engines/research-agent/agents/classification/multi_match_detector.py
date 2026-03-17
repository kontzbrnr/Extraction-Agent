"""
classification/multi_match_detector.py

Multi-Match Detector — Phase 6.4

Evaluates all three Phase 6.1 classification signals simultaneously
and returns the set of active signal names as an immutable frozenset.

Signals:
    SIGNAL_EVENT_VERB  — contains_event_verb() fired
    SIGNAL_FRAMING     — contains_framing_language() fired
    SIGNAL_ASYMMETRY   — contains_asymmetry_language() fired

Multi-match = two or more signals active simultaneously.

Relationship to Phase 6.3 (Ambiguity Handler):
    is_ambiguous_classification() detects the specific unresolvable
    case (framing + asymmetry, no event verb).
    is_multi_match() detects ANY multi-signal case regardless of
    whether the combination is resolvable by the priority tree.
    These are complementary utilities, not overlapping.

Contract authority:
    CREATIVE-LIBRARY-EXTRACTION-AGENT.md  §X (single seed type per AU)
    classification/classification_ruleset.py (6.1) — sole pattern authority

Invariant compliance:
    INV-1: No module-level mutable state. get_active_signals() returns
           frozenset — never a mutable set.
    INV-5: Both functions are pure. Identical input produces identical
           output. No randomness, no inference, no state.
"""

from __future__ import annotations

from engines.research_agent.agents.classification.classification_ruleset import (
    contains_asymmetry_language,
    contains_event_verb,
    contains_framing_language,
)

# ── Version constant ──────────────────────────────────────────────────────────

MULTI_MATCH_DETECTOR_VERSION: str = "1.0"

# ── Signal name constants ─────────────────────────────────────────────────────

SIGNAL_EVENT_VERB: str = "event_verb"
SIGNAL_FRAMING: str = "framing"
SIGNAL_ASYMMETRY: str = "asymmetry"

# Closed set of all valid signal names.
ALL_SIGNALS: frozenset = frozenset({
    SIGNAL_EVENT_VERB,
    SIGNAL_FRAMING,
    SIGNAL_ASYMMETRY,
})


# ── Detection functions ───────────────────────────────────────────────────────

def get_active_signals(text: str) -> frozenset:
    """Return the frozenset of signal names active in text.

    Evaluates all three Phase 6.1 detection functions and collects
    the name constant of each that returns True.

    Args:
        text: The text string to evaluate (typically au["text"]).

    Returns:
        A frozenset containing zero or more of:
            SIGNAL_EVENT_VERB, SIGNAL_FRAMING, SIGNAL_ASYMMETRY.
        frozenset() if no signal is active.
        Return value is always a subset of ALL_SIGNALS.

    INV-1: Returns frozenset — never mutable set.
    INV-5: Deterministic. Identical input produces identical output.
    """
    active = set()
    if contains_event_verb(text):
        active.add(SIGNAL_EVENT_VERB)
    if contains_framing_language(text):
        active.add(SIGNAL_FRAMING)
    if contains_asymmetry_language(text):
        active.add(SIGNAL_ASYMMETRY)
    return frozenset(active)


def is_multi_match(text: str) -> bool:
    """Return True if two or more classification signals are active in text.

    Delegates to get_active_signals(). Does not re-implement detection.

    Args:
        text: The text string to evaluate (typically au["text"]).

    Returns:
        True if len(get_active_signals(text)) > 1.
        False for zero-signal or single-signal text.

    INV-5: Deterministic. Identical input produces identical output.
    """
    return len(get_active_signals(text)) > 1
