"""
extraction/proper_noun_detector.py

Proper Noun Detector — Phase 5.1

Pattern-based detection of proper nouns in text.
No NLP library permitted. Detection uses structural regex proxy only.

Contract authority:
  IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md  Section III (Prohibited Content)
  IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md  Section V  (Violation Policy)
  CANONICAL-INTEGRITY-VALIDATOR.md              Section III (Identity Abstraction Integrity)

Prohibited content (per contract):
  * Proper nouns
  * Named individuals
  * Named franchises (if abstractable)
  * Literal identifiers unique to specific person

Rejection code on violation: REJECT_IDENTITY_CONTAMINATION

Detection rule (design decision — contract specifies WHAT, not the syntactic HOW):
  A token is treated as a proper noun if it matches [A-Z][a-z]+ (initial
  uppercase followed by one or more lowercase letters) and appears in a
  non-sentence-initial position (i.e., not the first token of the text).

  Rationale:
    - Sentence-initial tokens are excluded to prevent false positives on
      words like "Head", "The", "Coach" that are grammatically capitalized.
    - All-caps tokens (e.g., "NFL", "OC") do NOT match [A-Z][a-z]+ and
      are not flagged — these are acronyms, not abstraction violations.
    - Punctuation is stripped from tokens before matching.

  Documented limitation:
    A proper noun appearing ONLY as the first token of the text will not
    be detected. This is an accepted constraint of pattern-based detection
    without NLP. The IAV contract does not specify a syntactic detection
    algorithm; this rule is the structural proxy.

Invariant compliance:
  INV-1: _PROPER_NOUN_PATTERN compiled at module level — never mutated.
  INV-2: No fingerprint or canonical ID computation.
  INV-5: contains_proper_noun() is purely deterministic. Identical input
         always produces identical output. No randomness, no inference.
"""

from __future__ import annotations

import re

# ── Version constant ──────────────────────────────────────────────────────────

# Pinned version for this detection rule. Increment if detection logic changes.
# INV-5: Never derive from environment variables, config files, or runtime.
PROPER_NOUN_DETECTOR_VERSION: str = "1.0"

# ── Rejection code ────────────────────────────────────────────────────────────

# GSD/IAV-layer reason code for identity contamination rejection.
# Source: IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md Section V
#         CANONICAL-INTEGRITY-VALIDATOR.md Section III
REJECT_IDENTITY_CONTAMINATION: str = "REJECT_IDENTITY_CONTAMINATION"

# ── Pattern (compiled at module level — INV-1) ────────────────────────────────

# Matches a token that begins with one uppercase letter followed by one or
# more lowercase letters. Does NOT match all-caps acronyms (e.g., "NFL", "OC").
# Module-level compile is consistent with extraction/composite_marker.py.
_PROPER_NOUN_PATTERN = re.compile(r'^[A-Z][a-z]+$')

# Minimum character length for a token to be considered a proper noun candidate.
# Prevents single-letter capitalized tokens (e.g., "I") from triggering detection.
_MIN_PROPER_NOUN_LENGTH: int = 2

# Characters stripped from token edges before pattern matching.
_STRIP_CHARS: str = '.,!?;:"\'()[]{}—-'


# ── Detection function ────────────────────────────────────────────────────────

def contains_proper_noun(text: str) -> bool:
    """Detect whether text contains a proper noun in a non-initial position.

    Uses a structural regex proxy: tokens matching [A-Z][a-z]+ that appear
    after the first token are treated as proper noun violations.

    The first token is excluded from detection to prevent false positives on
    sentence-initial words (e.g., "Head", "The", "Coach"). See module
    docstring for documented limitation.

    Args:
        text: A string to inspect (typically an AU text field or canonical
              object field).

    Returns:
        True if a proper noun is detected in non-initial position.
        False otherwise.

    INV-5: Deterministic. Identical input always produces identical output.
    INV-2: No fingerprint computation. Read-only inspection only.
    """
    tokens = text.split()
    if len(tokens) < 2:
        return False
    for token in tokens[1:]:
        cleaned = token.strip(_STRIP_CHARS)
        if (
            len(cleaned) >= _MIN_PROPER_NOUN_LENGTH
            and _PROPER_NOUN_PATTERN.match(cleaned)
        ):
            return True
    return False
