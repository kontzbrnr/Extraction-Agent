"""
tests/nti/test_termination_evaluator.py

Tests for nti/termination_evaluator.py.

Invariants under test:
  INV-1: preflight_read and get_sealed_surfaces called unconditionally; no caching.
  INV-5: identical inputs always produce identical TerminationDecision output.
  Write discipline: set_termination_status called only when new_status != "running".
"""

import json
import os
from unittest.mock import patch, call

import pytest

from infra.orchestration.nti.termination_evaluator import TerminationDecision, evaluate_termination
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER
from infra.orchestration.nti.cycle_state_manager import create_nti_state, seal_surface
from engines.research_engine.ledger.global_state_manager import PreflightError, write_global_state
from engines.research_engine.ledger.season_state_manager import create_season_run


RUN_PATH = "runs/2024_REG"

VALID_GLOBAL = {
    "schemaVersion": "GLOBAL_STATE-1.0",
    "activeSeason": "2024_REG",
    "activeRunPath": RUN_PATH,
    "systemStatus": "operational",
}


def _setup_ledger(tmp_path, seal_all=False, seal_count=0):
    """Create minimal valid ledger + nti_state. Optionally seal surfaces."""
    write_global_state(str(tmp_path), VALID_GLOBAL)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    create_nti_state(str(tmp_path), RUN_PATH)
    if seal_all:
        for surface in SURFACE_ROTATION_ORDER:
            seal_surface(str(tmp_path), RUN_PATH, surface)
    elif seal_count > 0:
        for surface in SURFACE_ROTATION_ORDER[:seal_count]:
            seal_surface(str(tmp_path), RUN_PATH, surface)


def _read_state(tmp_path):
    path = tmp_path / RUN_PATH / "state.json"
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _make_halted_ledger(tmp_path):
    halted = dict(VALID_GLOBAL, systemStatus="halted")
    write_global_state(str(tmp_path), halted)
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    create_nti_state(str(tmp_path), RUN_PATH)


# ── Returns TerminationDecision ───────────────────────────────────────────────

def test_returns_termination_decision(tmp_path):
    _setup_ledger(tmp_path)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert isinstance(result, TerminationDecision)


def test_result_is_frozen(tmp_path):
    _setup_ledger(tmp_path)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    with pytest.raises((AttributeError, TypeError)):
        result.new_status = "sealed"  # type: ignore


def test_exhaustion_triggered_echoed(tmp_path):
    _setup_ledger(tmp_path)
    r_false = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert r_false.exhaustion_triggered is False


# ── all_surfaces_sealed computation ──────────────────────────────────────────

def test_all_surfaces_sealed_false_when_none_sealed(tmp_path):
    _setup_ledger(tmp_path)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.all_surfaces_sealed is False


def test_all_surfaces_sealed_false_when_partial(tmp_path):
    _setup_ledger(tmp_path, seal_count=7)  # 7 of 8 sealed
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.all_surfaces_sealed is False


def test_all_surfaces_sealed_true_when_all_sealed(tmp_path):
    _setup_ledger(tmp_path, seal_all=True)
    # Need to reset terminationStatus to "running" for preflight to pass.
    # After sealing all surfaces via seal_surface, terminationStatus is still "running"
    # (seal_surface only touches nti_state, not season state termination).
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.all_surfaces_sealed is True


# ── Decision logic ────────────────────────────────────────────────────────────

def test_neither_condition_returns_running(tmp_path):
    _setup_ledger(tmp_path)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.new_status == "running"
    assert result.persisted is False


def test_all_sealed_returns_sealed(tmp_path):
    _setup_ledger(tmp_path, seal_all=True)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.new_status == "sealed"
    assert result.persisted is True


def test_exhaustion_triggered_returns_exhausted(tmp_path):
    _setup_ledger(tmp_path)  # no surfaces sealed
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
    assert result.new_status == "exhausted"
    assert result.persisted is True


def test_both_conditions_sealed_takes_priority(tmp_path):
    """When both allSurfacesSealed and exhaustionTriggered: sealed wins."""
    _setup_ledger(tmp_path, seal_all=True)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
    assert result.new_status == "sealed"
    assert result.all_surfaces_sealed is True
    assert result.exhaustion_triggered is True


def test_exhaustion_true_but_all_sealed_also_true_status_is_sealed(tmp_path):
    _setup_ledger(tmp_path, seal_all=True)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
    assert result.new_status == "sealed"


# ── Persist behavior ──────────────────────────────────────────────────────────

def test_sealed_persisted_to_ledger(tmp_path):
    _setup_ledger(tmp_path, seal_all=True)
    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    state = _read_state(tmp_path)
    assert state["terminationStatus"] == "sealed"


def test_exhausted_persisted_to_ledger(tmp_path):
    _setup_ledger(tmp_path)
    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
    state = _read_state(tmp_path)
    assert state["terminationStatus"] == "exhausted"


def test_running_not_persisted_to_ledger(tmp_path):
    """When new_status='running', terminationStatus must remain 'running'."""
    _setup_ledger(tmp_path)
    state_before = _read_state(tmp_path)
    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    state_after = _read_state(tmp_path)
    assert state_before == state_after


def test_persisted_false_when_running(tmp_path):
    _setup_ledger(tmp_path)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.persisted is False


def test_persisted_true_on_sealed(tmp_path):
    _setup_ledger(tmp_path, seal_all=True)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert result.persisted is True


def test_persisted_true_on_exhausted(tmp_path):
    _setup_ledger(tmp_path)
    result = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
    assert result.persisted is True


# ── INV-1 — preflight called unconditionally ──────────────────────────────────

def test_preflight_called_once(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.preflight_read") as mock_pf:
        mock_pf.return_value = None
        with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
            mock_gs.return_value = frozenset()
            with patch("nti.termination_evaluator.set_termination_status"):
                evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
        mock_pf.assert_called_once()


def test_two_calls_two_preflight_reads(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.preflight_read") as mock_pf:
        mock_pf.return_value = None
        with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
            mock_gs.return_value = frozenset()
            evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
            evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
        assert mock_pf.call_count == 2


def test_get_sealed_surfaces_called_on_every_invocation(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.preflight_read"):
        with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
            mock_gs.return_value = frozenset()
            evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
            evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
        assert mock_gs.call_count == 2


def test_reflects_nti_state_disk_change_between_calls(tmp_path):
    """INV-1: second call sees newly sealed surfaces — no caching."""
    _setup_ledger(tmp_path, seal_count=0)
    r1 = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert r1.all_surfaces_sealed is False
    assert r1.new_status == "running"

    # Seal all surfaces on disk between calls.
    for surface in SURFACE_ROTATION_ORDER:
        seal_surface(str(tmp_path), RUN_PATH, surface)

    r2 = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert r2.all_surfaces_sealed is True
    assert r2.new_status == "sealed"


def test_halted_system_raises_preflight_error(tmp_path):
    _make_halted_ledger(tmp_path)
    with pytest.raises(PreflightError) as exc_info:
        evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert exc_info.value.reason_code == "SYSTEM_HALTED"


def test_sealed_terminationstatus_raises_termination_blocked(tmp_path):
    """If terminationStatus is already 'sealed', preflight raises TERMINATION_BLOCKED."""
    _setup_ledger(tmp_path, seal_all=True)
    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    # Now terminationStatus == "sealed"; next preflight call should raise.
    with pytest.raises(PreflightError) as exc_info:
        evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"


def test_set_termination_status_not_called_on_running(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.set_termination_status") as mock_sts:
        with patch("nti.termination_evaluator.preflight_read"):
            with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
                mock_gs.return_value = frozenset()
                evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    mock_sts.assert_not_called()


def test_set_termination_status_called_with_correct_status_on_sealed(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.set_termination_status") as mock_sts:
        with patch("nti.termination_evaluator.preflight_read"):
            with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
                mock_gs.return_value = frozenset(SURFACE_ROTATION_ORDER)  # all sealed
                evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    mock_sts.assert_called_once_with(str(tmp_path), RUN_PATH, "sealed")


def test_set_termination_status_called_with_correct_status_on_exhausted(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.set_termination_status") as mock_sts:
        with patch("nti.termination_evaluator.preflight_read"):
            with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
                mock_gs.return_value = frozenset()  # none sealed
                evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
    mock_sts.assert_called_once_with(str(tmp_path), RUN_PATH, "exhausted")


# ── INV-5 — replay determinism ────────────────────────────────────────────────

def test_identical_inputs_identical_result_running(tmp_path):
    _setup_ledger(tmp_path)
    r1 = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    r2 = evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    assert r1.all_surfaces_sealed == r2.all_surfaces_sealed
    assert r1.new_status == r2.new_status
    assert r1.persisted == r2.persisted


def test_determinism_exhaustion_path(tmp_path):
    _setup_ledger(tmp_path)
    with patch("nti.termination_evaluator.preflight_read"):
        with patch("nti.termination_evaluator.get_sealed_surfaces") as mock_gs:
            mock_gs.return_value = frozenset()
            with patch("nti.termination_evaluator.set_termination_status"):
                results = [
                    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=True)
                    for _ in range(5)
                ]
    for r in results:
        assert r.new_status == "exhausted"
        assert r.persisted is True


# ── Read-only when new_status == "running" ────────────────────────────────────

def test_no_extra_files_created_on_running(tmp_path):
    _setup_ledger(tmp_path)
    files_before = set(
        os.path.relpath(os.path.join(root, f), tmp_path)
        for root, _, files in os.walk(tmp_path)
        for f in files
    )
    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    files_after = set(
        os.path.relpath(os.path.join(root, f), tmp_path)
        for root, _, files in os.walk(tmp_path)
        for f in files
    )
    assert files_after == files_before


def test_nti_state_not_modified_by_evaluator(tmp_path):
    """evaluate_termination must not write nti_state.json."""
    _setup_ledger(tmp_path)
    nti_path = tmp_path / RUN_PATH / "nti_state.json"
    with open(nti_path, "r", encoding="utf-8") as fh:
        nti_before = json.load(fh)
    evaluate_termination(str(tmp_path), RUN_PATH, exhaustion_triggered=False)
    with open(nti_path, "r", encoding="utf-8") as fh:
        nti_after = json.load(fh)
    assert nti_before == nti_after
