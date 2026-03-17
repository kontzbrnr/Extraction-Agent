"""
meta/meta_ruleset.py
META deterministic subtype assignment and CME fingerprint derivation.
"""

from __future__ import annotations

import hashlib
import re

from engines.research_agent.agents.meta.meta_ontology import (
    CME_ID_PATTERN,
    CME_ID_PREFIX,
    CME_PERMANENCE_TOKEN,
    META_CME_FINGERPRINT_PREFIX,
    META_SUBTYPE_OTHER,
)

_NORMALIZE_WS_RE = re.compile(r"\s+")
_DISALLOWED_PUNCT_RE = re.compile(r"[^a-z0-9_]")

_STRUCTURAL_DEPARTURE_ROLES: frozenset[str] = frozenset(
    {
        "head_coach",
        "offensive_coordinator",
        "defensive_coordinator",
        "special_teams_coordinator",
        "position_coach",
        "general_manager",
        "front_office_executive",
        "owner",
    }
)
_RETIREMENT_DEPARTURE_ROLES: frozenset[str] = frozenset(
    {
        "quarterback",
        "skill_player",
        "offensive_lineman",
        "defensive_lineman",
        "linebacker",
        "defensive_back",
        "specialist",
        "practice_squad_player",
        "captain",
    }
)
_ADMINISTRATIVE_ACTOR_ROLES: frozenset[str] = frozenset({"league_body", "league_official"})
_COMPETITIVE_RESULT_ACTIONS: frozenset[str] = frozenset({"performed", "participated"})


class SubtypeAmbiguousError(Exception):
    """Raised when two rules inside the same tier match simultaneously."""

    def __init__(self, matched_subtypes: list[str]) -> None:
        self.matched_subtypes = matched_subtypes
        super().__init__(
            f"Subtype ambiguous in same tier: {len(matched_subtypes)} matches {matched_subtypes!r}"
        )


def _normalize_token(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = _NORMALIZE_WS_RE.sub("_", text)
    text = _DISALLOWED_PUNCT_RE.sub("", text)
    return text


def derive_cme_fingerprint(fields: dict[str, str | None]) -> str:
    """Derive CME_FINGERPRINT_V1 canonical id."""
    actor_role_norm = _normalize_token(fields.get("actorRole"))
    action_norm = _normalize_token(fields.get("action"))
    object_role_norm = _normalize_token(fields.get("objectRole"))
    context_role_norm = _normalize_token(fields.get("contextRole"))
    subtype_norm = _normalize_token(fields.get("subtype"))
    permanence_norm = _normalize_token(CME_PERMANENCE_TOKEN)
    source_reference_norm = _normalize_token(fields.get("sourceReference"))

    fingerprint_input = "|".join(
        [
            META_CME_FINGERPRINT_PREFIX,
            actor_role_norm,
            action_norm,
            object_role_norm,
            context_role_norm,
            subtype_norm,
            permanence_norm,
            source_reference_norm,
        ]
    )
    digest = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
    canonical_id = f"{CME_ID_PREFIX}{digest}"
    assert CME_ID_PATTERN.match(canonical_id), (
        f"derive_cme_fingerprint produced a non-conformant ID: {canonical_id!r}. "
        f"This is an internal invariant violation."
    )
    return canonical_id


def _resolve_single_tier_match(matches: list[str]) -> str | None:
    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches[0]
    raise SubtypeAmbiguousError(matches)


def assign_cme_subtype(event: dict) -> str:
    """Assign subtype using the priority-ordered rule table from Ruling 9.3-A."""
    action = event.get("action")
    context_role = event.get("contextRole")
    actor_role = event.get("actorRole")

    tier1_matches: list[str] = []
    if action in {"was_traded", "was_waived", "was_released"}:
        tier1_matches.append("transactional")
    if action == "was_ejected":
        tier1_matches.append("disciplinary")
    if action == "was_removed":
        tier1_matches.append("structural")
    if action == "awarded":
        tier1_matches.append("award")
    tier1 = _resolve_single_tier_match(tier1_matches)
    if tier1 is not None:
        return tier1

    tier2_matches: list[str] = []
    if action == "was_signed":
        if context_role == "suspension_period":
            tier2_matches.append("reinstatement")
        else:
            tier2_matches.append("contractual")
    if action == "was_designated":
        if context_role == "suspension_period":
            tier2_matches.append("disciplinary")
        elif context_role == "injury_period":
            tier2_matches.append("medical")
        else:
            tier2_matches.append("transactional")
    if action == "designated":
        if context_role == "suspension_period":
            tier2_matches.append("disciplinary")
        elif context_role == "injury_period":
            tier2_matches.append("medical")
        else:
            tier2_matches.append("transactional")
    if action == "returned":
        if context_role == "suspension_period":
            tier2_matches.append("reinstatement")
        elif context_role == "injury_period":
            tier2_matches.append("medical")
    tier2 = _resolve_single_tier_match(tier2_matches)
    if tier2 is not None:
        return tier2

    tier3_matches: list[str] = []
    if action == "departed" and actor_role in _STRUCTURAL_DEPARTURE_ROLES:
        tier3_matches.append("structural")
    if action == "departed" and actor_role in _RETIREMENT_DEPARTURE_ROLES:
        tier3_matches.append("retirement")
    tier3 = _resolve_single_tier_match(tier3_matches)
    if tier3 is not None:
        return tier3

    tier4_matches: list[str] = []
    if actor_role in _ADMINISTRATIVE_ACTOR_ROLES:
        tier4_matches.append("administrative")
    if actor_role == "franchise" and action in _COMPETITIVE_RESULT_ACTIONS:
        tier4_matches.append("competitive_result")
    tier4 = _resolve_single_tier_match(tier4_matches)
    if tier4 is not None:
        return tier4

    if action == "observed_record":
        return "record"

    return META_SUBTYPE_OTHER
