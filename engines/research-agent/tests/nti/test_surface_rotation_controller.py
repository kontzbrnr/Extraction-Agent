"""
tests/nti/test_surface_rotation_controller.py

Tests for nti/surface_rotation_controller.py.

Key invariants under test:
  INV-1: preflight_read called unconditionally on every invocation.
  INV-5: identical inputs always produce identical SurfaceSelection output.
  Read-only: no ledger files are written.
"""

import json
import pytest

from infra.orchestration.nti.surface_rotation_controller import SurfaceSelection, select_next_surface
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER, SurfaceRotationError
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


def _setup_ledger(tmp_path):
    """Create minimal valid ledger state: operational + running."""
    write_global_state(str(tmp_path), VALID_GLOBAL)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)


def _state_path(tmp_path):
    return tmp_path / RUN_PATH / "state.json"


# ---------------------------------------------------------------------------
# Happy path — selection
# ---------------------------------------------------------------------------


def test_select_next_surface_returns_selection(tmp_path):
    _setup_ledger(tmp_path)
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    assert isinstance(result, SurfaceSelection)


def test_select_next_surface_sequential(tmp_path):
    _setup_ledger(tmp_path)
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    assert result.selected_surface == "training_camp"


def test_select_next_surface_wraps_around(tmp_path):
    _setup_ledger(tmp_path)
    result = select_next_surface(str(tmp_path), RUN_PATH, "free_agency_period")
    assert result.selected_surface == "offseason"


def test_select_next_surface_echoes_current(tmp_path):
    _setup_ledger(tmp_path)
    result = select_next_surface(str(tmp_path), RUN_PATH, "preseason")
    assert result.current_surface == "preseason"


def test_select_next_surface_skips_sealed(tmp_path):
    _setup_ledger(tmp_path)
    sealed = frozenset({"training_camp"})
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason", sealed)
    assert result.selected_surface == "preseason"


def test_select_next_surface_result_is_frozen(tmp_path):
    _setup_ledger(tmp_path)
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    with pytest.raises((AttributeError, TypeError)):
        result.selected_surface = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# All surfaces sealed → selected_surface is None
# ---------------------------------------------------------------------------


def test_select_next_surface_all_sealed_returns_none(tmp_path):
    _setup_ledger(tmp_path)
    all_sealed = frozenset(SURFACE_ROTATION_ORDER)
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason", all_sealed)
    assert result.selected_surface is None


def test_select_next_surface_all_sealed_not_an_error(tmp_path):
    """All-sealed is a valid state — must not raise."""
    _setup_ledger(tmp_path)
    all_sealed = frozenset(SURFACE_ROTATION_ORDER)
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason", all_sealed)
    assert result.active_count == 0


# ---------------------------------------------------------------------------
# active_count and sealed_count
# ---------------------------------------------------------------------------


def test_counts_no_sealed(tmp_path):
    _setup_ledger(tmp_path)
    result = select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    assert result.sealed_count == 0
    assert result.active_count == len(SURFACE_ROTATION_ORDER)


def test_counts_with_sealed(tmp_path):
    _setup_ledger(tmp_path)
    sealed = frozenset({"offseason", "playoffs"})
    result = select_next_surface(str(tmp_path), RUN_PATH, "training_camp", sealed)
    assert result.sealed_count == 2
    assert result.active_count == len(SURFACE_ROTATION_ORDER) - 2


def test_counts_unknown_sealed_names_not_counted(tmp_path):
    """Unknown names in sealed set must not inflate sealed_count."""
    _setup_ledger(tmp_path)
    sealed = frozenset({"offseason", "NOT_A_SURFACE"})
    result = select_next_surface(str(tmp_path), RUN_PATH, "training_camp", sealed)
    assert result.sealed_count == 1


# ---------------------------------------------------------------------------
# INV-5 — determinism
# ---------------------------------------------------------------------------


def test_deterministic_same_inputs_same_output(tmp_path):
    _setup_ledger(tmp_path)
    sealed = frozenset({"playoffs"})
    r1 = select_next_surface(str(tmp_path), RUN_PATH, "regular_season", sealed)
    r2 = select_next_surface(str(tmp_path), RUN_PATH, "regular_season", sealed)
    assert r1 == r2


def test_deterministic_all_surfaces(tmp_path):
    """Every surface produces a deterministic next-surface result."""
    _setup_ledger(tmp_path)
    for surface in SURFACE_ROTATION_ORDER:
        r1 = select_next_surface(str(tmp_path), RUN_PATH, surface)
        r2 = select_next_surface(str(tmp_path), RUN_PATH, surface)
        assert r1.selected_surface == r2.selected_surface


# ---------------------------------------------------------------------------
# INV-1 — preflight called unconditionally
# ---------------------------------------------------------------------------


def test_preflight_called_on_every_invocation(tmp_path, monkeypatch):
    _setup_ledger(tmp_path)
    call_count = {"n": 0}
    original_preflight = __import__(
        "ledger.global_state_manager", fromlist=["preflight_read"]
    ).preflight_read

    def counting_preflight(root):
        call_count["n"] += 1
        return original_preflight(root)

    monkeypatch.setattr(
        "nti.surface_rotation_controller.preflight_read", counting_preflight
    )

    select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    assert call_count["n"] == 2


def test_system_halted_raises_preflight_error(tmp_path):
    write_global_state(str(tmp_path), {**VALID_GLOBAL, "systemStatus": "halted"})
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    with pytest.raises(PreflightError) as exc_info:
        select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    assert exc_info.value.reason_code == "SYSTEM_HALTED"


def test_termination_sealed_raises_preflight_error(tmp_path):
    _setup_ledger(tmp_path)
    state = json.loads(_state_path(tmp_path).read_text())
    state["terminationStatus"] = "sealed"
    _state_path(tmp_path).write_text(json.dumps(state))
    with pytest.raises(PreflightError) as exc_info:
        select_next_surface(str(tmp_path), RUN_PATH, "offseason")
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"


def test_termination_exhausted_raises_preflight_error(tmp_path):
    _setup_ledger(tmp_path)
    state = json.loads(_state_path(tmp_path).read_text())
    state["terminationStatus"] = "exhausted"
    _state_path(tmp_path).write_text(json.dumps(state))
    with pytest.raises(PreflightError):
        select_next_surface(str(tmp_path), RUN_PATH, "offseason")


# ---------------------------------------------------------------------------
# Error propagation — unknown surface
# ---------------------------------------------------------------------------


def test_unknown_current_surface_raises(tmp_path):
    _setup_ledger(tmp_path)
    with pytest.raises(SurfaceRotationError) as exc_info:
        select_next_surface(str(tmp_path), RUN_PATH, "invalid_surface")
    assert exc_info.value.surface == "invalid_surface"


# ---------------------------------------------------------------------------
# Read-only — no file mutation
# ---------------------------------------------------------------------------


def test_no_ledger_files_written(tmp_path):
    _setup_ledger(tmp_path)
    global_before = (tmp_path / "global_state.json").read_bytes()
    state_before = _state_path(tmp_path).read_bytes()

    select_next_surface(str(tmp_path), RUN_PATH, "offseason")

    assert (tmp_path / "global_state.json").read_bytes() == global_before
    assert _state_path(tmp_path).read_bytes() == state_before
