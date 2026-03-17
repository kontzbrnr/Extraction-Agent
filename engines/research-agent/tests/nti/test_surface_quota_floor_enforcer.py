"""
tests/nti/test_surface_quota_floor_enforcer.py

Tests for nti/surface_quota_floor_enforcer.py.

Key invariants under test:
  INV-1: preflight_read and read_season_state called unconditionally; no caching.
  INV-5: identical inputs always produce identical FloorCheckResult output.
  Read-only: no ledger files are written by the enforcer.

Schema gap documented:
  floor_threshold is caller-provided. No stored floor threshold exists in any
  contract or schema (subcategoryQuotaFloors has zero contract definition).
  Enforcer reads season_state.subcategoryCounts — NOT nti_state.exhaustionCounters.
"""

import json
import os
from unittest.mock import patch

import pytest

from infra.orchestration.nti.surface_quota_floor_enforcer import FloorCheckResult, check_surface_floors
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER
from engines.research_engine.ledger.global_state_manager import PreflightError, write_global_state
from engines.research_engine.ledger.season_state_manager import create_season_run


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

RUN_PATH = "runs/2024_REG"

VALID_GLOBAL = {
    "schemaVersion": "GLOBAL_STATE-1.0",
    "activeSeason": "2024_REG",
    "activeRunPath": RUN_PATH,
    "systemStatus": "operational",
}


def _setup_ledger(tmp_path, subcategory_counts=None):
    """Create minimal valid ledger: operational + running + given subcategoryCounts."""
    write_global_state(str(tmp_path), VALID_GLOBAL)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    if subcategory_counts is not None:
        _write_subcategory_counts(tmp_path, subcategory_counts)


def _state_path(tmp_path):
    return tmp_path / RUN_PATH / "state.json"


def _read_state(tmp_path):
    with open(_state_path(tmp_path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_subcategory_counts(tmp_path, counts: dict):
    """Patch subcategoryCounts into an existing state.json."""
    state = _read_state(tmp_path)
    state["subcategoryCounts"] = counts
    path = _state_path(tmp_path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def _make_halted_ledger(tmp_path):
    """Create ledger where systemStatus == 'halted'."""
    halted = dict(VALID_GLOBAL)
    halted["systemStatus"] = "halted"
    write_global_state(str(tmp_path), halted)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)


def _make_sealed_ledger(tmp_path):
    """Create ledger where terminationStatus == 'sealed'."""
    write_global_state(str(tmp_path), VALID_GLOBAL)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    state = _read_state(tmp_path)
    state["terminationStatus"] = "sealed"
    with open(_state_path(tmp_path), "w", encoding="utf-8") as fh:
        json.dump(state, fh)


ALL_SURFACES = frozenset(SURFACE_ROTATION_ORDER)


# ---------------------------------------------------------------------------
# Returns FloorCheckResult
# ---------------------------------------------------------------------------


def test_returns_floor_check_result(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    assert isinstance(result, FloorCheckResult)


def test_result_is_frozen(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    with pytest.raises((AttributeError, TypeError)):
        result.floor_threshold = 99  # type: ignore[misc]


def test_floor_threshold_echoed_in_result(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=5)
    assert result.floor_threshold == 5


# ---------------------------------------------------------------------------
# Partition correctness
# ---------------------------------------------------------------------------


def test_surface_above_floor_in_met_floor(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={"offseason": 3})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3,
        surfaces=frozenset(["offseason"])
    )
    assert "offseason" in result.met_floor
    assert "offseason" not in result.below_floor


def test_surface_below_floor_in_below_floor(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={"offseason": 2})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3,
        surfaces=frozenset(["offseason"])
    )
    assert "offseason" in result.below_floor
    assert "offseason" not in result.met_floor


def test_surface_exactly_at_floor_is_met(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={"training_camp": 5})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=5,
        surfaces=frozenset(["training_camp"])
    )
    assert "training_camp" in result.met_floor


def test_surface_one_below_floor_is_below(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={"training_camp": 4})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=5,
        surfaces=frozenset(["training_camp"])
    )
    assert "training_camp" in result.below_floor


def test_partition_is_complete(tmp_path):
    """below_floor ∪ met_floor == all checked surfaces."""
    counts = {"offseason": 0, "training_camp": 3, "preseason": 1}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    surfaces = frozenset(["offseason", "training_camp", "preseason"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=2, surfaces=surfaces
    )
    assert result.below_floor | result.met_floor == surfaces


def test_partition_is_exclusive(tmp_path):
    """below_floor ∩ met_floor == ∅."""
    counts = {"offseason": 0, "training_camp": 5}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    surfaces = frozenset(["offseason", "training_camp"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3, surfaces=surfaces
    )
    assert result.below_floor & result.met_floor == frozenset()


def test_surface_counts_covers_all_checked_surfaces(tmp_path):
    """surface_counts has an entry for every checked surface."""
    counts = {"offseason": 2}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    surfaces = frozenset(["offseason", "training_camp"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1, surfaces=surfaces
    )
    for surface in surfaces:
        assert surface in result.surface_counts


# ---------------------------------------------------------------------------
# Absent surfaces treated as count=0
# ---------------------------------------------------------------------------


def test_absent_surface_treated_as_zero(tmp_path):
    """Surface not in subcategoryCounts has count=0."""
    _setup_ledger(tmp_path, subcategory_counts={})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1,
        surfaces=frozenset(["offseason"])
    )
    assert result.surface_counts["offseason"] == 0
    assert "offseason" in result.below_floor


def test_absent_surface_meets_zero_floor(tmp_path):
    """Absent surface (count=0) meets floor when threshold=0."""
    _setup_ledger(tmp_path, subcategory_counts={})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=0,
        surfaces=frozenset(["offseason"])
    )
    assert "offseason" in result.met_floor


def test_absent_surface_count_is_zero_in_surface_counts(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1,
        surfaces=frozenset(["playoffs"])
    )
    assert result.surface_counts["playoffs"] == 0


# ---------------------------------------------------------------------------
# floor_threshold=0: all surfaces met
# ---------------------------------------------------------------------------


def test_zero_threshold_all_surfaces_met(tmp_path):
    """floor_threshold=0 means 0 >= 0 is always true — all surfaces in met_floor."""
    _setup_ledger(tmp_path, subcategory_counts={})
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=0)
    assert result.met_floor == ALL_SURFACES
    assert result.below_floor == frozenset()


def test_zero_threshold_with_nonzero_counts_all_met(tmp_path):
    counts = {s: 5 for s in SURFACE_ROTATION_ORDER}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=0)
    assert result.below_floor == frozenset()


# ---------------------------------------------------------------------------
# Default surfaces = all 8 rotation surfaces
# ---------------------------------------------------------------------------


def test_default_surfaces_is_all_eight(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=0)
    checked = result.met_floor | result.below_floor
    assert checked == ALL_SURFACES


def test_default_surfaces_surface_counts_has_all_eight(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=0)
    assert set(result.surface_counts.keys()) == set(SURFACE_ROTATION_ORDER)


# ---------------------------------------------------------------------------
# Unknown surfaces excluded
# ---------------------------------------------------------------------------


def test_unknown_surface_excluded_from_result(tmp_path):
    _setup_ledger(tmp_path)
    surfaces = frozenset(["offseason", "NOT_A_SURFACE"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1, surfaces=surfaces
    )
    assert "NOT_A_SURFACE" not in result.met_floor
    assert "NOT_A_SURFACE" not in result.below_floor
    assert "NOT_A_SURFACE" not in result.surface_counts


def test_all_unknown_surfaces_result_empty(tmp_path):
    _setup_ledger(tmp_path)
    surfaces = frozenset(["FAKE_A", "FAKE_B"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1, surfaces=surfaces
    )
    assert result.below_floor == frozenset()
    assert result.met_floor == frozenset()
    assert result.surface_counts == {}


def test_known_unknown_mixed_only_known_in_result(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={"offseason": 5})
    surfaces = frozenset(["offseason", "FAKE"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3, surfaces=surfaces
    )
    assert set(result.surface_counts.keys()) == {"offseason"}
    assert "offseason" in result.met_floor


# ---------------------------------------------------------------------------
# surface_counts reflects disk
# ---------------------------------------------------------------------------


def test_surface_counts_matches_written_counts(tmp_path):
    counts = {"offseason": 7, "playoffs": 2}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    surfaces = frozenset(["offseason", "playoffs"])
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1, surfaces=surfaces
    )
    assert result.surface_counts["offseason"] == 7
    assert result.surface_counts["playoffs"] == 2


# ---------------------------------------------------------------------------
# Pre-IO validation — floor_threshold < 0
# ---------------------------------------------------------------------------


def test_negative_threshold_raises_value_error(tmp_path):
    _setup_ledger(tmp_path)
    with pytest.raises(ValueError):
        check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=-1)


def test_negative_threshold_no_preflight_called(tmp_path):
    """ValueError is raised before any IO — preflight_read must not be called."""
    _setup_ledger(tmp_path)
    with patch("nti.surface_quota_floor_enforcer.preflight_read") as mock_pf:
        with pytest.raises(ValueError):
            check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=-1)
        mock_pf.assert_not_called()


def test_negative_threshold_no_season_state_read(tmp_path):
    """read_season_state must not be called when threshold < 0."""
    _setup_ledger(tmp_path)
    with patch("nti.surface_quota_floor_enforcer.read_season_state") as mock_rs:
        with pytest.raises(ValueError):
            check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=-5)
        mock_rs.assert_not_called()


# ---------------------------------------------------------------------------
# INV-1 — preflight called unconditionally on every invocation
# ---------------------------------------------------------------------------


def test_preflight_called_once_per_invocation(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.surface_quota_floor_enforcer.preflight_read") as mock_pf:
        mock_pf.return_value = None  # preflight result unused
        with patch("nti.surface_quota_floor_enforcer.read_season_state") as mock_rs:
            mock_rs.return_value = {
                "schemaVersion": "SEASON_STATE-1.0",
                "subcategoryCounts": {},
            }
            check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
        mock_pf.assert_called_once()


def test_two_calls_two_preflight_reads(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.surface_quota_floor_enforcer.preflight_read") as mock_pf:
        mock_pf.return_value = None
        with patch("nti.surface_quota_floor_enforcer.read_season_state") as mock_rs:
            mock_rs.return_value = {
                "schemaVersion": "SEASON_STATE-1.0",
                "subcategoryCounts": {},
            }
            check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
            check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
        assert mock_pf.call_count == 2


def test_reflects_disk_change_between_calls(tmp_path):
    """INV-1: second call sees updated subcategoryCounts — no caching."""
    _setup_ledger(tmp_path, subcategory_counts={"offseason": 0})
    surfaces = frozenset(["offseason"])

    result1 = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3, surfaces=surfaces
    )
    assert "offseason" in result1.below_floor

    # Update disk between calls
    _write_subcategory_counts(tmp_path, {"offseason": 5})

    result2 = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3, surfaces=surfaces
    )
    assert "offseason" in result2.met_floor


def test_halted_system_raises_preflight_error(tmp_path):
    _make_halted_ledger(tmp_path)
    with pytest.raises(PreflightError) as exc_info:
        check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    assert exc_info.value.reason_code == "SYSTEM_HALTED"


def test_sealed_system_raises_preflight_error(tmp_path):
    _make_sealed_ledger(tmp_path)
    with pytest.raises(PreflightError) as exc_info:
        check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"


def test_exhausted_system_raises_preflight_error(tmp_path):
    write_global_state(str(tmp_path), VALID_GLOBAL)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    state = _read_state(tmp_path)
    state["terminationStatus"] = "exhausted"
    with open(_state_path(tmp_path), "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    with pytest.raises(PreflightError) as exc_info:
        check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"


# ---------------------------------------------------------------------------
# INV-5 — replay determinism
# ---------------------------------------------------------------------------


def test_identical_inputs_identical_result(tmp_path):
    counts = {"offseason": 3, "training_camp": 1}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    surfaces = frozenset(["offseason", "training_camp"])

    r1 = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=2, surfaces=surfaces
    )
    r2 = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=2, surfaces=surfaces
    )
    assert r1.below_floor == r2.below_floor
    assert r1.met_floor == r2.met_floor
    assert r1.floor_threshold == r2.floor_threshold
    assert r1.surface_counts == r2.surface_counts


def test_determinism_all_surfaces(tmp_path):
    """Same state → same result across all 8 surfaces, multiple runs."""
    counts = {s: i for i, s in enumerate(SURFACE_ROTATION_ORDER)}
    _setup_ledger(tmp_path, subcategory_counts=counts)

    results = [
        check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=4)
        for _ in range(5)
    ]
    for r in results[1:]:
        assert r.below_floor == results[0].below_floor
        assert r.met_floor == results[0].met_floor


# ---------------------------------------------------------------------------
# Read-only — no ledger files written
# ---------------------------------------------------------------------------


def test_no_state_json_mutation(tmp_path):
    """season_state is not modified by the enforcer."""
    counts = {"offseason": 2}
    _setup_ledger(tmp_path, subcategory_counts=counts)

    state_before = _read_state(tmp_path)
    check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    state_after = _read_state(tmp_path)

    assert state_before == state_after


def test_no_extra_files_created(tmp_path):
    """Enforcer must not create any new files in the ledger."""
    _setup_ledger(tmp_path)
    files_before = set(
        os.path.relpath(os.path.join(root, f), tmp_path)
        for root, _, files in os.walk(tmp_path)
        for f in files
    )
    check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)
    files_after = set(
        os.path.relpath(os.path.join(root, f), tmp_path)
        for root, _, files in os.walk(tmp_path)
        for f in files
    )
    assert files_after == files_before


def test_global_state_not_modified(tmp_path):
    """global_state.json is not modified by the enforcer."""
    _setup_ledger(tmp_path)
    gs_path = tmp_path / "global_state.json"
    with open(gs_path, "r", encoding="utf-8") as fh:
        before = json.load(fh)

    check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=1)

    with open(gs_path, "r", encoding="utf-8") as fh:
        after = json.load(fh)
    assert before == after


# ---------------------------------------------------------------------------
# Multiple surfaces — mixed counts
# ---------------------------------------------------------------------------


def test_multiple_surfaces_mixed_result(tmp_path):
    counts = {
        "offseason": 5,
        "training_camp": 0,
        "preseason": 3,
        "regular_season": 2,
    }
    _setup_ledger(tmp_path, subcategory_counts=counts)
    surfaces = frozenset(counts.keys())
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=3, surfaces=surfaces
    )
    assert "offseason" in result.met_floor      # 5 >= 3
    assert "training_camp" in result.below_floor  # 0 < 3
    assert "preseason" in result.met_floor      # 3 >= 3
    assert "regular_season" in result.below_floor  # 2 < 3


def test_all_surfaces_below_floor(tmp_path):
    _setup_ledger(tmp_path, subcategory_counts={})
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=1
    )
    assert result.below_floor == ALL_SURFACES
    assert result.met_floor == frozenset()


def test_all_surfaces_above_floor(tmp_path):
    counts = {s: 10 for s in SURFACE_ROTATION_ORDER}
    _setup_ledger(tmp_path, subcategory_counts=counts)
    result = check_surface_floors(
        str(tmp_path), RUN_PATH, floor_threshold=5
    )
    assert result.met_floor == ALL_SURFACES
    assert result.below_floor == frozenset()


def test_all_eight_surfaces_individually(tmp_path):
    """Each rotation surface can independently appear in met_floor or below_floor."""
    _setup_ledger(tmp_path, subcategory_counts={})
    for surface in SURFACE_ROTATION_ORDER:
        result = check_surface_floors(
            str(tmp_path), RUN_PATH, floor_threshold=1,
            surfaces=frozenset([surface])
        )
        assert surface in result.below_floor
        assert surface in result.surface_counts


def test_below_floor_and_met_floor_are_frozensets(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=0)
    assert isinstance(result.below_floor, frozenset)
    assert isinstance(result.met_floor, frozenset)


def test_surface_counts_is_dict(tmp_path):
    _setup_ledger(tmp_path)
    result = check_surface_floors(str(tmp_path), RUN_PATH, floor_threshold=0)
    assert isinstance(result.surface_counts, dict)
