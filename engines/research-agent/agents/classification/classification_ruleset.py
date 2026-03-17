"""
classification/classification_ruleset.py

Classification Ruleset — Phase 6.1

Defines the four seed type labels and the structural pattern rules
used to distinguish them. All term sets and compiled patterns are
module-level constants — never mutated at runtime.

Contract authority:
    PRESSURE-CAPABLE-SEED-STRUCTURAL-CONTRACT.md   v2.0 §VI.A  (event verbs)
    STRUCTURAL-ENVIRONMENT-SEED-STRUCTURAL-CONTRACT.md  v2.0 §VII (prohibited content)
    MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md      v2.0 §V     (event verb trigger)
    NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md    v2.0        (seed definition)

Design note — _EVENT_VERBS list:
    Derived from the union of contract-specified event verb lists.
    Pressure §VI.A explicitly marks its list as "non-exhaustive."
    This module encodes the currently locked set only.
    Expansion requires a CLASSIFICATION_RULE_VERSION bump.

Invariant compliance:
    INV-1: All patterns compiled at module level. No mutable state.
    INV-4: Four seed type labels are distinct. No cross-lane overlap.
    INV-5: All detection functions are pure. Identical input produces
           identical output. No randomness, no inference, no state.
"""

from __future__ import annotations

import re

# ── Version constant ──────────────────────────────────────────────────────────

# Increment when any term set or detection logic changes.
# INV-5: Never derive from environment variables or config files.
CLASSIFICATION_RULE_VERSION: str = "1.0"

# ── Seed type labels ──────────────────────────────────────────────────────────

SEED_TYPE_PRESSURE: str = "pressure_capable"
SEED_TYPE_NARRATIVE: str = "narrative_event"
SEED_TYPE_STRUCTURAL: str = "structural_environment"
SEED_TYPE_MEDIA: str = "media_context"

VALID_SEED_TYPES: frozenset = frozenset({
    SEED_TYPE_PRESSURE,
    SEED_TYPE_NARRATIVE,
    SEED_TYPE_STRUCTURAL,
    SEED_TYPE_MEDIA,
})

# ── Term sets (frozenset — INV-1) ─────────────────────────────────────────────

# Event verbs: indicate a discrete change or action event.
# Source: Pressure v2.0 §VI.A, Structural v2.0 §VII.A, Media Context v2.0 §V.
# Presence disqualifies Structural Environment and Pressure-Capable seeds.
_EVENT_VERBS: frozenset = frozenset({
    "fired", "hired", "traded", "signed", "drafted", "benched",
    "promoted", "demoted", "suspended", "announced", "designated",
    "released", "reassigned", "activated", "placed",
})

# Asymmetry terms: indicate unresolved structural tension.
# Source: Structural v2.0 §VII.B (prohibited in Structural Environment Seeds).
# Presence is characteristic of Pressure-Capable Seeds.
_ASYMMETRY_TERMS: frozenset = frozenset({
    "tension", "imbalance", "instability", "conflict", "friction", "volatility",
})

# Framing phrases: indicate public discourse or rhetorical positioning.
# Source: Structural v2.0 §VII.C (prohibited in Structural Environment Seeds).
# Presence is characteristic of Media Context Seeds.
# Mixed: single-word and multi-word entries — see pattern compile note below.
_FRAMING_PHRASES: frozenset = frozenset({
    "described as", "labeled", "considered", "viewed as", "narrative",
})

# ── Compiled patterns (module level — INV-1) ──────────────────────────────────

# Event verb pattern: word-boundary match, case-insensitive.
# \b prevents "unsuspended" from matching "suspended".
_EVENT_VERB_PATTERN: re.Pattern = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in sorted(_EVENT_VERBS)) + r")\b",
    re.IGNORECASE,
)

# Asymmetry term pattern: word-boundary match, case-insensitive.
_ASYMMETRY_PATTERN: re.Pattern = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in sorted(_ASYMMETRY_TERMS)) + r")\b",
    re.IGNORECASE,
)

# Framing phrase pattern: multi-word entries match as substrings;
# single-word entries use word-boundary.
# Build alternation: wrap single words in \b...\b; leave phrases as-is.
def _build_framing_pattern(phrases: frozenset) -> re.Pattern:
    parts = []
    for phrase in sorted(phrases):
        escaped = re.escape(phrase)
        if " " in phrase:
            parts.append(escaped)
        else:
            parts.append(r"\b" + escaped + r"\b")
    return re.compile("(" + "|".join(parts) + ")", re.IGNORECASE)


_FRAMING_PATTERN: re.Pattern = _build_framing_pattern(_FRAMING_PHRASES)

# ── Loose framing pattern (version-pinned extension of _FRAMING_PHRASES) ────
#
# Detects the non-adjacent form "described [0-6 words] as" — a framing
# construction not representable as a single frozenset entry.
#
# Governance: This pattern is an explicit, pinned extension of the framing
# detection rule. It is governed by CLASSIFICATION_RULE_VERSION. Any change
# to the match window (currently 0–6 intervening words), anchors, or flags
# constitutes a rule change and requires a CLASSIFICATION_RULE_VERSION bump.
#
# Audit note: Activation of this pattern is NOT distinguishable from
# _FRAMING_PATTERN activation in downstream audit logs. Both cause
# SIGNAL_FRAMING to be recorded. This is a known audit resolution limit
# under CLASSIFICATION_RULE_VERSION "1.0".
#
# INV-5: Pattern is compiled at module level. Identical input always
# produces identical output. No runtime configuration permitted.
_FRAMING_LOOSE_PATTERN_ACTIVE: bool = True  # governed by CLASSIFICATION_RULE_VERSION
_FRAMING_DESCRIBED_AS_LOOSE_PATTERN: re.Pattern = re.compile(
    r"\bdescribed\b(?:\W+\w+){0,6}\W+as\b",
    re.IGNORECASE,
)

# ── Detection functions ───────────────────────────────────────────────────────

def contains_event_verb(text: str) -> bool:
    """Return True if text contains a contract-specified event verb.

    Word-boundary matching. Case-insensitive.
    Event verbs indicate a discrete change or action event.
    Presence disqualifies Structural Environment and
    Pressure-Capable seed classification.

    INV-5: Deterministic. Identical input produces identical output.
    """
    return bool(_EVENT_VERB_PATTERN.search(text))


def contains_asymmetry_language(text: str) -> bool:
    """Return True if text contains a contract-specified asymmetry term.

    Word-boundary matching. Case-insensitive.
    Asymmetry terms indicate unresolved structural tension.
    Presence is characteristic of Pressure-Capable Seeds.

    INV-5: Deterministic. Identical input produces identical output.
    """
    return bool(_ASYMMETRY_PATTERN.search(text))


def contains_framing_language(text: str) -> bool:
    """Return True if text contains a contract-specified framing phrase.

    Multi-word phrases match as substrings. Single-word entries use
    word-boundary. Case-insensitive.
    Framing language indicates public discourse or rhetorical positioning.
    Presence is characteristic of Media Context Seeds.

    INV-5: Deterministic. Identical input produces identical output.
    """
    return bool(
        _FRAMING_PATTERN.search(text)
        or _FRAMING_DESCRIBED_AS_LOOSE_PATTERN.search(text)
    )
