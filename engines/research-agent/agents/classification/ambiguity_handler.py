"""
classification/ambiguity_handler.py

Ambiguity Handler — Phase 6.3

Defines REJECT_AMBIGUOUS_CLASSIFICATION, detects the structural
conflict case where classification cannot be deterministically
resolved, and produces a rejection record for the AU.

Ambiguous classification condition (all three must hold):
    1. No event verb present         (event verb resolves to Narrative)
    2. Framing language present      (routes toward Media Context)
    3. Asymmetry language present    (routes toward Pressure-Capable)

    Media Context §III prohibits asymmetry language.
    Pressure-Capable §VI prohibits framing language.
    When both signals are present without an event verb, neither lane
    is valid. No priority resolution is permitted — inference is
    prohibited per the determinism lock on all seed contracts.

Structural mirror of:
    gsd/rejection_handler.py         (Phase 4.4 — REJECT_ATOMICITY_UNCLEAR)
    extraction/iav_rejection_handler.py (Phase 5.5 — REJECT_IDENTITY_CONTAMINATION)

Contract authority:
    MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md      v2.0 §III
    PRESSURE-CAPABLE-SEED-STRUCTURAL-CONTRACT.md   v2.0 §VI
    CREATIVE-LIBRARY-EXTRACTION-AGENT.md           §XII (Determinism Lock)

Invariant compliance:
    INV-1: No module-level mutable state.
    INV-2: No fingerprint or canonical ID computation.
    INV-3: Input AU is never mutated. Rejection record contains a
           shallow copy. All AU-1.0 fields are primitive (str, int).
    INV-5: is_ambiguous_classification() is deterministic and pure.
           make_ambiguity_rejection() contains no timestamps or UUIDs.
"""

from __future__ import annotations

from engines.research_agent.agents.classification.classification_ruleset import (
    contains_asymmetry_language,
    contains_event_verb,
    contains_framing_language,
)

# ── Reason code ───────────────────────────────────────────────────────────────

REJECT_AMBIGUOUS_CLASSIFICATION: str = "REJECT_AMBIGUOUS_CLASSIFICATION"

# ── Shared rejection schema version ──────────────────────────────────────────

_REJECTION_SCHEMA_VERSION: str = "REJECTION-1.0"


# ── Ambiguity detection ───────────────────────────────────────────────────────

def is_ambiguous_classification(text: str) -> bool:
    """Return True if text triggers mutually disqualifying classification signals.

    The ambiguous case is: framing language AND asymmetry language are both
    present, AND no event verb is present.

        - Event verb presence resolves classification to SEED_TYPE_NARRATIVE
          (event verb disqualifies all other lanes) — NOT ambiguous.
        - Framing language alone (no asymmetry) → SEED_TYPE_MEDIA — NOT ambiguous.
        - Asymmetry language alone (no framing) → SEED_TYPE_PRESSURE — NOT ambiguous.
        - Both framing AND asymmetry (no event verb):
            Media Context §III prohibits asymmetry language.
            Pressure-Capable §VI prohibits framing language.
            Neither lane is valid. No inference permitted. → AMBIGUOUS.

    Args:
        text: The AU text field to evaluate.

    Returns:
        True if and only if: no event verb AND framing language AND asymmetry
        language are all simultaneously detected.
        False in all other cases.

    INV-5: Deterministic. Identical input produces identical output.
    """
    if contains_event_verb(text):
        return False
    return contains_framing_language(text) and contains_asymmetry_language(text)


# ── Rejection record builder ──────────────────────────────────────────────────

def make_ambiguity_rejection(au: dict) -> dict:
    """Produce a deterministic rejection record for an ambiguously classified AU.

    The input AU is shallow-copied into the rejection record. The original
    au dict is never mutated (INV-3). All AU-1.0 fields are primitive
    (str, int), so a shallow copy is sufficient.

    Args:
        au: An AU-1.0 conformant dict that triggered ambiguous classification.

    Returns:
        A rejection record dict with fields:
          reasonCode    — REJECT_AMBIGUOUS_CLASSIFICATION (INV-5)
          au            — shallow copy of the input AU
          schemaVersion — "REJECTION-1.0"

    INV-1: No state mutation.
    INV-2: No fingerprint computation.
    INV-3: Input au is not mutated. Returned au is a copy.
    INV-5: Deterministic. No timestamps, no UUIDs.
    """
    return {
        "reasonCode": REJECT_AMBIGUOUS_CLASSIFICATION,
        "au": dict(au),
        "schemaVersion": _REJECTION_SCHEMA_VERSION,
    }
