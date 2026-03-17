"""
tests/extraction/test_abstraction_mapper.py

Tests for extraction/abstraction_mapper.py — Micro-Project 5.3.

Validates:
  - Version constant
  - Exact match lookups (narrative, pressure, media)
  - Normalization (case, whitespace, space-to-underscore)
  - Proper noun rejection (no match)
  - Lane isolation (no cross-lane matches)
  - Integer token exclusion (pressure tier)
  - Invalid lane error handling
  - Return type correctness
  - Determinism (INV-5)
"""

import pytest

from engines.research_agent.agents.extraction.abstraction_mapper import (
    ABSTRACTION_MAPPER_VERSION,
    map_noun_to_role_token,
)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

def test_version_constant():
    assert ABSTRACTION_MAPPER_VERSION == "1.0"


# ── EXACT MATCH — NARRATIVE LANE ──────────────────────────────────────────────

def test_quarterback_narrative():
    assert map_noun_to_role_token("quarterback", "narrative") == "quarterback"


def test_head_coach_narrative():
    assert map_noun_to_role_token("head_coach", "narrative") == "head_coach"


def test_franchise_narrative():
    assert map_noun_to_role_token("franchise", "narrative") == "franchise"


def test_unspecified_actor_narrative():
    assert map_noun_to_role_token("unspecified_actor", "narrative") == "unspecified_actor"


def test_appeared_action_narrative():
    assert map_noun_to_role_token("appeared", "narrative") == "appeared"


def test_media_audience_narrative():
    assert map_noun_to_role_token("media_audience", "narrative") == "media_audience"


def test_regular_season_narrative():
    assert map_noun_to_role_token("regular_season", "narrative") == "regular_season"


# ── EXACT MATCH — PRESSURE LANE ───────────────────────────────────────────────

def test_ambient_framing_pressure():
    assert map_noun_to_role_token("ambient_framing", "pressure") == "ambient_framing"


def test_organization_pressure():
    assert map_noun_to_role_token("organization", "pressure") == "organization"


def test_coach_pressure():
    assert map_noun_to_role_token("coach", "pressure") == "coach"


def test_visibility_pressure():
    assert map_noun_to_role_token("visibility", "pressure") == "visibility"


# ── EXACT MATCH — MEDIA LANE ──────────────────────────────────────────────────

def test_structural_media():
    assert map_noun_to_role_token("structural", "media") == "structural"


def test_other_media():
    assert map_noun_to_role_token("other", "media") == "other"


def test_retirement_media():
    assert map_noun_to_role_token("retirement", "media") == "retirement"


# ── NORMALIZATION (case + space) ──────────────────────────────────────────────

def test_case_normalization_quarterback():
    assert map_noun_to_role_token("Quarterback", "narrative") == "quarterback"


def test_case_normalization_head_coach():
    assert map_noun_to_role_token("HEAD_COACH", "narrative") == "head_coach"


def test_space_normalization():
    assert map_noun_to_role_token("head coach", "narrative") == "head_coach"


def test_mixed_normalization():
    assert map_noun_to_role_token("Head Coach", "narrative") == "head_coach"


def test_whitespace_strip():
    assert map_noun_to_role_token("  quarterback  ", "narrative") == "quarterback"


# ── NO MATCH — PROPER NOUNS ───────────────────────────────────────────────────

def test_proper_noun_returns_none():
    assert map_noun_to_role_token("Tom Brady", "narrative") is None


def test_proper_noun_underscore_returns_none():
    assert map_noun_to_role_token("tom_brady", "narrative") is None


def test_unknown_token_returns_none():
    assert map_noun_to_role_token("xyzzy_unknown", "narrative") is None


# ── LANE ISOLATION ────────────────────────────────────────────────────────────

def test_quarterback_wrong_lane():
    assert map_noun_to_role_token("quarterback", "pressure") is None


def test_ambient_framing_wrong_lane():
    assert map_noun_to_role_token("ambient_framing", "narrative") is None


def test_structural_wrong_lane():
    assert map_noun_to_role_token("structural", "narrative") is None


# ── INTEGER TOKEN EXCLUSION ───────────────────────────────────────────────────

def test_tier_integer_string_returns_none():
    assert map_noun_to_role_token("1", "pressure") is None


def test_tier_integer_two_returns_none():
    assert map_noun_to_role_token("2", "pressure") is None


# ── INVALID LANE ──────────────────────────────────────────────────────────────

def test_invalid_lane_raises():
    with pytest.raises(ValueError):
        map_noun_to_role_token("quarterback", "unknown_lane")


def test_empty_lane_raises():
    with pytest.raises(ValueError):
        map_noun_to_role_token("quarterback", "")


# ── RETURN TYPE ───────────────────────────────────────────────────────────────

def test_return_type_is_str_on_match():
    result = map_noun_to_role_token("quarterback", "narrative")
    assert isinstance(result, str)


def test_return_type_is_none_on_miss():
    result = map_noun_to_role_token("xyz_not_real", "narrative")
    assert result is None


# ── DETERMINISM ───────────────────────────────────────────────────────────────

def test_determinism():
    """INV-5: identical (noun, lane) always produces identical output."""
    results = [
        map_noun_to_role_token("quarterback", "narrative")
        for _ in range(5)
    ]
    assert all(r == results[0] for r in results)
    assert results[0] == "quarterback"
