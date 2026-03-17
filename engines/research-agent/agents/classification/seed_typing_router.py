"""
classification/seed_typing_router.py

Seed Typing Router — Phase 6.2

Stateless function that applies the Phase 6.1 Classification Ruleset
to an AU and returns exactly one seed type string.

Decision tree (strict priority order — derived from contract
prohibited-content disqualification rules):

    1. contains_event_verb     → SEED_TYPE_NARRATIVE
       (event verbs disqualify Pressure, Structural, Media)

    2. contains_framing_language → SEED_TYPE_MEDIA
       (framing disqualifies Structural, Pressure)

    3. contains_asymmetry_language → SEED_TYPE_PRESSURE
       (asymmetry disqualifies Structural, Media)

    4. default                 → SEED_TYPE_STRUCTURAL

Contract authority:
    PRESSURE-CAPABLE-SEED-STRUCTURAL-CONTRACT.md   v2.0 §VI.A
    STRUCTURAL-ENVIRONMENT-SEED-STRUCTURAL-CONTRACT.md v2.0 §VII
    MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md      v2.0 §V
    NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md    v2.0 §V
    CREATIVE-LIBRARY-EXTRACTION-AGENT.md           §X (single seed type per AU)

Invariant compliance:
    INV-1: No module-level mutable state. No instance variables.
    INV-4: Returns exactly one of the four exclusive lane labels.
           Multi-assignment is a contract violation.
    INV-5: Deterministic. Identical AU always produces identical type.
           No timestamps, no UUIDs, no runtime state.
"""

from __future__ import annotations

from engines.research_agent.agents.classification.classification_ruleset import (
    SEED_TYPE_MEDIA,
    SEED_TYPE_NARRATIVE,
    SEED_TYPE_PRESSURE,
    SEED_TYPE_STRUCTURAL,
    contains_asymmetry_language,
    contains_event_verb,
    contains_framing_language,
)

# ── Version constant ──────────────────────────────────────────────────────────

# Must be co-incremented with CLASSIFICATION_RULE_VERSION when term sets
# in classification_ruleset.py change (INV-5: routing decisions change
# with term set changes).
SEED_TYPING_ROUTER_VERSION: str = "1.0"


# ── Router ────────────────────────────────────────────────────────────────────

def route(au: dict) -> str:
    """Assign exactly one seed type to an AU.

    Applies the Classification Ruleset detection functions to au["text"]
    in strict priority order and returns the first matching seed type.
    If no pattern matches, returns SEED_TYPE_STRUCTURAL (default lane).

    Args:
        au: An AU-1.0 conformant dict. Must contain a "text" key with a
            string value. Never mutated by this function (INV-1).

    Returns:
        Exactly one seed type string — a member of VALID_SEED_TYPES:
            "narrative_event"       — event verb detected
            "media_context"         — framing language detected (no event verb)
            "pressure_capable"      — asymmetry language detected (no event verb,
                                      no framing)
            "structural_environment" — no pattern matched (default)

    Raises:
        ValueError: If au does not contain a "text" key, or if au["text"]
                    is not a string.

    INV-1: No state mutation.
    INV-4: Always returns exactly one of the four exclusive seed type labels.
    INV-5: Deterministic. Identical au["text"] always produces identical output.
    """
    if "text" not in au:
        raise ValueError("au must contain a 'text' key.")
    if not isinstance(au["text"], str):
        raise ValueError(
            f"au['text'] must be a string, got {type(au['text']).__name__}."
        )

    text: str = au["text"]

    if contains_event_verb(text):
        return SEED_TYPE_NARRATIVE

    if contains_framing_language(text):
        return SEED_TYPE_MEDIA

    if contains_asymmetry_language(text):
        return SEED_TYPE_PRESSURE

    return SEED_TYPE_STRUCTURAL
