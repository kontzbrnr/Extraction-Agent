"""
tests/nti/test_surface_rotation_index.py

Tests for nti/surface_rotation_index.py.

Key invariants under test:
  INV-5: all functions are pure — identical inputs produce identical outputs.
  Contract sync: SURFACE_ROTATION_ORDER must match enums/narrative/registry.json
                 timeBucketRegistry.tierA.values exactly.
"""

import json
import pytest

from infra.orchestration.nti.surface_rotation_index import (
    SURFACE_ROTATION_ORDER,
    SurfaceRotationError,
    _N,
    _SURFACE_SET,
    active_rotation,
    is_valid_surface,
    next_surface,
    surface_position,
)


# ---------------------------------------------------------------------------
# SURFACE_ROTATION_ORDER — constant integrity
# ---------------------------------------------------------------------------


def test_surface_rotation_order_is_tuple():
    assert isinstance(SURFACE_ROTATION_ORDER, tuple)


def test_surface_rotation_order_has_eight_surfaces():
    assert len(SURFACE_ROTATION_ORDER) == 8


def test_surface_rotation_order_exact_values():
    assert SURFACE_ROTATION_ORDER == (
        "offseason",
        "training_camp",
        "preseason",
        "regular_season",
        "playoffs",
        "championship_week",
        "draft_period",
        "free_agency_period",
    )


def test_surface_rotation_order_no_duplicates():
    assert len(SURFACE_ROTATION_ORDER) == len(set(SURFACE_ROTATION_ORDER))


def test_surface_rotation_order_immutable():
    """Tuple is immutable — no runtime modification possible."""
    with pytest.raises(TypeError):
        SURFACE_ROTATION_ORDER[0] = "mutated"  # type: ignore[index]


def test_surface_rotation_order_matches_enum_registry():
    """SURFACE_ROTATION_ORDER must mirror enums/narrative/registry.json Tier A values."""
    with open("enums/narrative/registry.json", "r", encoding="utf-8") as fh:
        registry = json.load(fh)

    tier_a = (
        registry
        .get("timeBucketRegistry", {})
        .get("tierA", {})
        .get("values", [])
    )

    assert tier_a, "timeBucketRegistry.tierA.values must be present in narrative registry"
    assert tuple(tier_a) == SURFACE_ROTATION_ORDER, (
        "SURFACE_ROTATION_ORDER must exactly match "
        "enums/narrative/registry.json timeBucketRegistry.tierA.values"
    )


# ---------------------------------------------------------------------------
# is_valid_surface
# ---------------------------------------------------------------------------


def test_is_valid_surface_true_for_all_surfaces():
    for surface in SURFACE_ROTATION_ORDER:
        assert is_valid_surface(surface) is True


def test_is_valid_surface_false_for_unknown():
    assert is_valid_surface("unknown_surface") is False
    assert is_valid_surface("") is False
    assert is_valid_surface("OFFSEASON") is False  # case-sensitive


def test_is_valid_surface_pure(monkeypatch):
    """Calling twice with same input must return same result (INV-5)."""
    r1 = is_valid_surface("offseason")
    r2 = is_valid_surface("offseason")
    assert r1 == r2 is True


# ---------------------------------------------------------------------------
# surface_position
# ---------------------------------------------------------------------------


def test_surface_position_first():
    assert surface_position("offseason") == 0


def test_surface_position_last():
    assert surface_position("free_agency_period") == 7


def test_surface_position_all_surfaces():
    for idx, surface in enumerate(SURFACE_ROTATION_ORDER):
        assert surface_position(surface) == idx


def test_surface_position_unknown_raises():
    with pytest.raises(SurfaceRotationError) as exc_info:
        surface_position("unknown")
    assert exc_info.value.surface == "unknown"


def test_surface_position_pure():
    """Same input always returns same position (INV-5)."""
    assert surface_position("regular_season") == surface_position("regular_season")


# ---------------------------------------------------------------------------
# active_rotation
# ---------------------------------------------------------------------------


def test_active_rotation_no_sealed_returns_all():
    result = active_rotation(frozenset())
    assert result == SURFACE_ROTATION_ORDER


def test_active_rotation_one_sealed():
    result = active_rotation(frozenset({"offseason"}))
    assert "offseason" not in result
    assert len(result) == 7
    assert result[0] == "training_camp"


def test_active_rotation_preserves_order():
    sealed = frozenset({"training_camp", "playoffs"})
    result = active_rotation(sealed)
    expected = tuple(s for s in SURFACE_ROTATION_ORDER if s not in sealed)
    assert result == expected


def test_active_rotation_all_sealed_returns_empty():
    result = active_rotation(frozenset(SURFACE_ROTATION_ORDER))
    assert result == ()


def test_active_rotation_unknown_sealed_names_ignored():
    """Unknown names in sealed set are silently ignored."""
    result = active_rotation(frozenset({"offseason", "NOT_A_SURFACE"}))
    assert "offseason" not in result
    assert len(result) == 7


def test_active_rotation_pure():
    """Same sealed set always produces same result (INV-5)."""
    sealed = frozenset({"preseason", "playoffs"})
    assert active_rotation(sealed) == active_rotation(sealed)


def test_active_rotation_accepts_regular_set():
    result = active_rotation({"offseason"})
    assert "offseason" not in result


# ---------------------------------------------------------------------------
# next_surface
# ---------------------------------------------------------------------------


def test_next_surface_sequential_no_sealed():
    assert next_surface("offseason") == "training_camp"
    assert next_surface("training_camp") == "preseason"
    assert next_surface("preseason") == "regular_season"
    assert next_surface("regular_season") == "playoffs"
    assert next_surface("playoffs") == "championship_week"
    assert next_surface("championship_week") == "draft_period"
    assert next_surface("draft_period") == "free_agency_period"


def test_next_surface_wraps_around():
    """Last surface wraps to first (INV-5: rotation is circular)."""
    assert next_surface("free_agency_period") == "offseason"


def test_next_surface_skips_sealed():
    """Sealed surfaces are skipped in rotation."""
    result = next_surface("offseason", sealed=frozenset({"training_camp"}))
    assert result == "preseason"


def test_next_surface_skips_multiple_sealed():
    sealed = frozenset({"training_camp", "preseason", "regular_season"})
    assert next_surface("offseason", sealed=sealed) == "playoffs"


def test_next_surface_wraps_skipping_sealed():
    """Wrap-around must also skip sealed surfaces."""
    sealed = frozenset({"offseason", "training_camp"})
    assert next_surface("free_agency_period", sealed=sealed) == "preseason"


def test_next_surface_current_is_sealed():
    """If current is sealed, still use its position as the search start."""
    sealed = frozenset({"offseason"})
    result = next_surface("offseason", sealed=sealed)
    assert result == "training_camp"


def test_next_surface_only_one_active_returns_self():
    """If only current is active (all others sealed), returns current."""
    all_except_offseason = frozenset(SURFACE_ROTATION_ORDER) - {"offseason"}
    result = next_surface("offseason", sealed=all_except_offseason)
    assert result == "offseason"


def test_next_surface_all_sealed_returns_none():
    result = next_surface("offseason", sealed=frozenset(SURFACE_ROTATION_ORDER))
    assert result is None


def test_next_surface_unknown_current_raises():
    with pytest.raises(SurfaceRotationError) as exc_info:
        next_surface("invalid_surface")
    assert exc_info.value.surface == "invalid_surface"


def test_next_surface_pure():
    """Same inputs always produce same output (INV-5)."""
    sealed = frozenset({"playoffs"})
    r1 = next_surface("regular_season", sealed)
    r2 = next_surface("regular_season", sealed)
    assert r1 == r2 == "championship_week"


def test_next_surface_full_cycle_returns_to_start():
    """Rotating through all surfaces must return to starting point."""
    start = "offseason"
    current = start
    visited = []
    for _ in range(_N):
        current = next_surface(current)
        visited.append(current)
    assert visited[-1] == start
    assert len(set(visited)) == _N
