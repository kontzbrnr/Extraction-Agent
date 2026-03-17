"""
extraction/abstraction_mapper.py

Abstraction Mapper — Phase 5.3

Normalizes a noun string and returns its canonical role token from the
specified lane's token registry if an exact normalized match exists.

Normalization rule:
    noun.strip().lower().replace(" ", "_")
    No regex. No punctuation stripping. No NLP.

Contract authority:
    IDENTITY-ABSTRACTION-ENFORCEMENT-CONTRACT.md  Section IV (Required Abstraction)
    ACTOR_ROLE_TAXONOMY_CONTRACT.md               Section IV (Role Abstraction Rules)
    CANONICAL-ENUM-REGISTRY.md                   Governance Clause I (Dual Registry Architecture Lock)

Invariant compliance:
    INV-1: No mutable state. All computation at call time.
    INV-4: Lookup is scoped to caller-specified lane only.
           Cross-lane search is a contract violation.
    INV-5: map_noun_to_role_token() is deterministic.
           Identical (noun, lane) always produces identical output.

No inference permitted.
No paraphrase permitted.
No text rewriting performed.
"""

from __future__ import annotations

import types

from engines.research_agent.enums.role_token_registry import (
    MEDIA_TOKEN_REGISTRY,
    NARRATIVE_TOKEN_REGISTRY,
    PRESSURE_TOKEN_REGISTRY,
)

# ── Version constant ──────────────────────────────────────────────────────────

ABSTRACTION_MAPPER_VERSION: str = "1.0"

# ── Valid lanes ───────────────────────────────────────────────────────────────

_VALID_LANES: frozenset = frozenset({"pressure", "narrative", "media"})

# ── Lane registry map ─────────────────────────────────────────────────────────

_LANE_REGISTRY: dict[str, types.MappingProxyType] = {
    "pressure": PRESSURE_TOKEN_REGISTRY,
    "narrative": NARRATIVE_TOKEN_REGISTRY,
    "media": MEDIA_TOKEN_REGISTRY,
}

# ── Public API ────────────────────────────────────────────────────────────────

def map_noun_to_role_token(noun: str, lane: str) -> str | None:
    """Normalize noun and return its canonical role token if found.

    Normalization: noun.strip().lower().replace(" ", "_")
    Lookup: exact match against all string-valued token sets in the
            specified lane's registry.
    Integer-valued token sets (e.g., pressure tier) are excluded.

    Args:
        noun: The noun string to normalize and look up.
        lane: Lane to search. Must be one of "pressure", "narrative", "media".

    Returns:
        The canonical token string if an exact normalized match is found.
        None if no match is found.

    Raises:
        ValueError: If lane is not a recognized lane identifier.

    INV-1: No state mutation.
    INV-4: Searches only the specified lane's registry.
    INV-5: Deterministic — identical (noun, lane) always produces identical output.
    No inference. No paraphrase. Exact normalized match only.
    """
    if lane not in _VALID_LANES:
        raise ValueError(
            f"Unknown lane {lane!r}. Must be one of {sorted(_VALID_LANES)}."
        )

    normalized = noun.strip().lower().replace(" ", "_")
    registry = _LANE_REGISTRY[lane]

    for token_set in registry.values():
        # Exclude integer-valued token sets (e.g., pressure tier = {1, 2, 3}).
        # Only string token sets participate in noun abstraction lookup.
        if not token_set:
            continue
        sample = next(iter(token_set))
        if not isinstance(sample, str):
            continue
        if normalized in token_set:
            return normalized

    return None
