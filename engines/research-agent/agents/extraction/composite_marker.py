"""
extraction/composite_marker.py

Composite detection for Raw Extraction Candidates (RECs).

Contract authority:
  - GLOBAL-SPLIT-DOCTRINE.md (GSD) Section II: Composite REC definition
  - GLOBAL-SPLIT-DOCTRINE.md (GSD) Section X: Determinism Lock
  - EVENT-MATERIAL-IDENTIFIER.md (EMI) Section IV: Granularity Rule
  - CREATIVE-LIBRARY-EXTRACTION-AGENT.md Section XII: Determinism Lock

DESIGN DECISION — Structural Proxy Rule:
  Contracts define composite semantically: "more than one completed, separable
  ledger mutation" (EMI Granularity Rule, Section IV). No syntactic detection
  algorithm is specified in any contract (RULE_VERSION: 0 matches in contracts_md/).

  This module implements the minimum deterministic structural proxy consistent
  with all contract-provided examples:

    Composite:
      "Coach fired OC and promoted QB coach."        (two ledger mutations)
      "Team fired OC and promoted QB coach."          (two ledger mutations)
      "Coach fired OC and retained play-calling duties."
      "Player argued with coach and later skipped media availability."

    Non-composite:
      "Head coach announced a quarterback change."   (one action)
      "Coach announced he will bench QB next week."  (one completed + future clause)
      "Coach announced a firing and a promotion."    (one action + noun phrase, not clause)

  Proxy: coordinating conjunction ("and"/"but") separating two or more
  independent action clauses, where each clause contains >= _MIN_CLAUSE_WORDS
  words. A noun phrase like "a promotion" (< 3 words) is not an independent
  action clause.

  Deterministic: same input → same output (INV-5 / EMI Section IX).
  Stateless: no module-level mutable state (INV-1 / EMI Section IX).
  Binary: True or False, no confidence scoring (EMI Section IX).
  No identity computation: no fingerprints or canonical IDs (INV-2).
"""

import re

# ── Public Constants ──────────────────────────────────────────────────────────

# Rule version for GSD Section X Determinism Lock.
# Increment when the structural proxy detection rule changes.
COMPOSITE_DETECTION_RULE_VERSION: str = "1.0"

# Rejection reason code per CREATIVE-LIBRARY-EXTRACTION-AGENT.md Section XII.
# Raised when a REC is composite but cannot be deterministically separated.
ERR_COMPOSITE_BOUNDARY_UNCLEAR: str = "ERR_COMPOSITE_BOUNDARY_UNCLEAR"

# ── Private Constants ─────────────────────────────────────────────────────────

# Coordinating conjunctions that may join independent ledger mutation clauses.
# Whitespace-bounded to avoid matching mid-word (e.g. "handed", "standard").
_CLAUSE_SPLIT_PATTERN = re.compile(r'\s+(?:and|but)\s+', re.IGNORECASE)

# Minimum word count for a clause to qualify as an independent action predicate.
# Derived from: minimum viable independent clause = subject + verb + argument (3 words).
# Design decision: value 3 is the smallest count that correctly separates all
# contract-provided composite examples from all contract-provided non-composite examples.
_MIN_CLAUSE_WORDS: int = 3


# ── Public API ────────────────────────────────────────────────────────────────

def is_composite(text: str) -> bool:
    """
    Return True if ``text`` contains more than one completed, separable
    ledger mutation per the EMI Granularity Rule and GSD composite definition.

    Structural proxy: coordinating conjunction ("and"/"but") separating two or
    more independent action clauses, each containing at least
    ``_MIN_CLAUSE_WORDS`` words.

    Returns False for empty strings, whitespace-only input, or non-string input.

    Deterministic. Stateless. Binary. No inference. No randomness.

    Invariant compliance:
      INV-1: No module-level mutable state.
      INV-2: No fingerprint or canonical ID computation.
      INV-5: Identical input always produces identical output.
    """
    if not text or not isinstance(text, str):
        return False

    parts = _CLAUSE_SPLIT_PATTERN.split(text.strip())
    non_trivial = [
        p.strip()
        for p in parts
        if len(p.strip().split()) >= _MIN_CLAUSE_WORDS
    ]
    return len(non_trivial) > 1
