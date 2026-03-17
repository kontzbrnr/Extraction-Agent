"""
mcp/mcp_ruleset.py

MCP structural rule checks.

Contract authority: MEDIA-CONTEXT-SEED-STRUCTURAL-CONTRACT.md v2.0
    §V  — Event verb trigger rule
    §XII — Prohibited language
    §XIII — Identity abstraction
    §XIV — Failure conditions

All term sets and compiled patterns are module-level constants (INV-1).
All detection functions are pure (INV-5).

Invariant compliance:
    INV-1: No mutable state at module or instance level.
    INV-5: Identical input always produces identical output.
           No timestamps, no UUIDs, no runtime configuration.
"""

from __future__ import annotations

import re

from engines.research_agent.agents.classification.classification_ruleset import (
    contains_asymmetry_language,
    contains_event_verb,
)
from engines.research_agent.agents.extraction.proper_noun_detector import contains_proper_noun

# Re-export for call-site convenience. These are governed by
# classification_ruleset.py and pinned in mcp_schema.py.
__all__ = [
    "contains_event_verb",
    "contains_asymmetry_language",
    "contains_proper_noun",
    "contains_prohibited_language",
    "MCP_RULESET_VERSION",
]

MCP_RULESET_VERSION: str = "1.0"

# ── Prohibited language (§XII) ────────────────────────────────────────────────
# Any of these phrases present in AU text → REJECT_MCP_PROHIBITED_LANGUAGE.
# Frozen at module level (INV-1, INV-5).

_PROHIBITED_PHRASES: frozenset[str] = frozenset({
    "causing",
    "leading to",
    "resulting in",
    "therefore",
    "which created",
    "structural shift",
    "officially",
    "designated",
})


def _build_prohibited_pattern(phrases: frozenset[str]) -> re.Pattern:
    parts = []
    for phrase in sorted(phrases):
        escaped = re.escape(phrase)
        if " " in phrase:
            parts.append(escaped)
        else:
            parts.append(r"\b" + escaped + r"\b")
    return re.compile("(" + "|".join(parts) + ")", re.IGNORECASE)


_PROHIBITED_PATTERN: re.Pattern = _build_prohibited_pattern(_PROHIBITED_PHRASES)


def contains_prohibited_language(text: str) -> bool:
    """Return True if text contains any §XII prohibited phrase.

    Multi-word phrases match as substrings. Single-word entries use
    word-boundary. Case-insensitive.

    INV-5: Deterministic. Identical input produces identical output.
    """
    return bool(_PROHIBITED_PATTERN.search(text))
