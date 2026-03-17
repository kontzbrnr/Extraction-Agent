"""
tests/orchestrator/test_orchestrator_preflight.py

Preflight Ledger Read Enforcement tests — Phase 13.2.

Verifies:
    INV-1: State read unconditionally from disk. No cross-invocation cache.
    §II:   "Before every action: Read GlobalState, Read SeasonRunState.
            Never trust prior invocation memory."
    §IV Step 1: Preflight protocol — systemStatus + terminationStatus gates.
    §VI:   incompleteBatchFlag=True → handle_crash_recovery() invoked.
    INV-3: Crash recovery never touches canonical_objects.json.

Fixture pattern: tmp_path (pytest built-in). Real files written to disk.
No mocking. All ledger writes go through the module API.
"""

import json

import pytest
from pathlib import Path

from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import (
    GLOBAL_STATE_SCHEMA_VERSION,
    GlobalStateReadError,
    SeasonStateReadError,
)
from engines.research_engine.ledger.season_state_manager import create_season_run
from infra.orchestration.runtime.orchestrator import ORCHESTRATOR_VERSION, orchestrator_run


# ── Constants ─────────────────────────────────────────────────────────────────

_SEASON       = "2024_REG"
_RUN_PATH     = "runs/2024_REG"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_global_state(tmp_path: Path, system_status: str = "operational") -> None:
    """Write a schema-valid global_state.json."""
    atomic_write_json(
        str(tmp_path / "global_state.json"),
        {
            "schemaVersion": GLOBAL_STATE_SCHEMA_VERSION,
            "enumVersion": "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
            "activeSeason":  _SEASON,
            "activeRunPath": _RUN_PATH,
            "systemStatus":  system_status,
        },
    )


def _write_season_state(tmp_path: Path, **overrides) -> None:
    """Create season state via API, then apply raw overrides for test fixture setup."""
    create_season_run(str(tmp_path), _SEASON, _RUN_PATH)
    if overrides:
        state_path = tmp_path / _RUN_PATH / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(overrides)
        atomic_write_json(str(state_path), state)


def _setup(tmp_path: Path, system_status: str = "operational", **season_overrides) -> None:
    """Write both state files. Standard entry point for all tests."""
    _write_global_state(tmp_path, system_status=system_status)
    _write_season_state(tmp_path, **season_overrides)


# ── Preflight — system halted ─────────────────────────────────────────────────

def test_system_halted_returns_halted_action(tmp_path):
    _setup(tmp_path, system_status="halted")
    result = orchestrator_run(str(tmp_path))
    assert result["action"] == "halted"


def test_system_halted_reason_code(tmp_path):
    _setup(tmp_path, system_status="halted")
    result = orchestrator_run(str(tmp_path))
    assert result["reasonCode"] == "SYSTEM_HALTED"


def test_system_halted_returns_orchestrator_version(tmp_path):
    _setup(tmp_path, system_status="halted")
    result = orchestrator_run(str(tmp_path))
    assert result["orchestratorVersion"] == ORCHESTRATOR_VERSION


def test_system_halted_zero_counts(tmp_path):
    _setup(tmp_path, system_status="halted")
    result = orchestrator_run(str(tmp_path))
    assert result["canonicalizedCount"] == 0
    assert result["rejectedCount"] == 0


def test_system_halted_no_state_mutation(tmp_path):
    """INV-1: system halt must produce zero disk side effects on season state."""
    _setup(tmp_path, system_status="halted")
    state_path = tmp_path / _RUN_PATH / "state.json"
    mtime_before = state_path.stat().st_mtime
    orchestrator_run(str(tmp_path))
    assert state_path.stat().st_mtime == mtime_before


# ── Preflight — termination blocked ──────────────────────────────────────────

@pytest.mark.parametrize("term_status", ["sealed", "exhausted", "system_failure"])
def test_termination_blocked_returns_halted_action(tmp_path, term_status):
    _setup(tmp_path, terminationStatus=term_status)
    result = orchestrator_run(str(tmp_path))
    assert result["action"] == "halted"


@pytest.mark.parametrize("term_status", ["sealed", "exhausted", "system_failure"])
def test_termination_blocked_reason_code(tmp_path, term_status):
    _setup(tmp_path, terminationStatus=term_status)
    result = orchestrator_run(str(tmp_path))
    assert result["reasonCode"] == "TERMINATION_BLOCKED"


@pytest.mark.parametrize("term_status", ["sealed", "exhausted", "system_failure"])
def test_termination_blocked_zero_counts(tmp_path, term_status):
    _setup(tmp_path, terminationStatus=term_status)
    result = orchestrator_run(str(tmp_path))
    assert result["canonicalizedCount"] == 0
    assert result["rejectedCount"] == 0


@pytest.mark.parametrize("term_status", ["sealed", "exhausted", "system_failure"])
def test_termination_blocked_no_state_mutation(tmp_path, term_status):
    """INV-1: termination block must produce zero disk side effects on season state."""
    _setup(tmp_path, terminationStatus=term_status)
    state_path = tmp_path / _RUN_PATH / "state.json"
    mtime_before = state_path.stat().st_mtime
    orchestrator_run(str(tmp_path))
    assert state_path.stat().st_mtime == mtime_before


# ── Preflight — missing ledger files ─────────────────────────────────────────

def test_missing_global_state_propagates_error(tmp_path):
    """global_state.json absent → GlobalStateReadError must propagate uncaught."""
    with pytest.raises(GlobalStateReadError):
        orchestrator_run(str(tmp_path))


def test_missing_season_state_propagates_error(tmp_path):
    """season state.json absent → SeasonStateReadError must propagate uncaught."""
    _write_global_state(tmp_path, system_status="operational")
    # season state intentionally not created
    with pytest.raises(SeasonStateReadError):
        orchestrator_run(str(tmp_path))


# ── Crash recovery ────────────────────────────────────────────────────────────

def test_crash_recovery_action_when_flag_set(tmp_path):
    _setup(tmp_path, incompleteBatchFlag=True, activeBatchId="BATCH_2024_REG_0000")
    result = orchestrator_run(str(tmp_path))
    assert result["action"] == "crash_recovery"


def test_crash_recovery_clears_incomplete_flag(tmp_path):
    _setup(tmp_path, incompleteBatchFlag=True, activeBatchId="BATCH_2024_REG_0000")
    orchestrator_run(str(tmp_path))
    state = json.loads(
        (tmp_path / _RUN_PATH / "state.json").read_text(encoding="utf-8")
    )
    assert state["incompleteBatchFlag"] is False


def test_crash_recovery_clears_active_batch_id(tmp_path):
    _setup(tmp_path, incompleteBatchFlag=True, activeBatchId="BATCH_2024_REG_0000")
    orchestrator_run(str(tmp_path))
    state = json.loads(
        (tmp_path / _RUN_PATH / "state.json").read_text(encoding="utf-8")
    )
    assert state["activeBatchId"] is None


def test_crash_recovery_does_not_touch_registry(tmp_path):
    """INV-3: handle_crash_recovery must never open canonical_objects.json."""
    _setup(tmp_path, incompleteBatchFlag=True, activeBatchId="BATCH_2024_REG_0000")

    # Pre-create a registry file with known mtime.
    registry_path = tmp_path / _RUN_PATH / "canonical_objects.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        str(registry_path),
        {
            "schemaVersion": "CANONICAL_REGISTRY-1.0",
            "CPS": [], "CME": [], "CSN": [],
            "StructuralEnvironment": [], "MediaContext": [],
        },
    )
    mtime_before = registry_path.stat().st_mtime

    orchestrator_run(str(tmp_path))

    # Crash recovery must not have mutated the file.
    # (Empty pipeline stub adds no objects, so commit step is also a no-op.)
    assert registry_path.stat().st_mtime == mtime_before


# ── Normal path ───────────────────────────────────────────────────────────────

def test_normal_run_action_is_new_batch(tmp_path):
    _setup(tmp_path)
    result = orchestrator_run(str(tmp_path))
    assert result["action"] == "new_batch"


def test_normal_run_increments_micro_batch_count(tmp_path):
    _setup(tmp_path)
    result = orchestrator_run(str(tmp_path))
    assert result["microBatchCount"] == 1


def test_normal_run_clears_batch_flag(tmp_path):
    _setup(tmp_path)
    orchestrator_run(str(tmp_path))
    state = json.loads(
        (tmp_path / _RUN_PATH / "state.json").read_text(encoding="utf-8")
    )
    assert state["incompleteBatchFlag"] is False


def test_normal_run_termination_status_unchanged(tmp_path):
    """No failures → terminationStatus remains 'running'."""
    _setup(tmp_path)
    result = orchestrator_run(str(tmp_path))
    assert result["terminationStatus"] == "running"


def test_normal_run_returns_orchestrator_version(tmp_path):
    _setup(tmp_path)
    result = orchestrator_run(str(tmp_path))
    assert result["orchestratorVersion"] == ORCHESTRATOR_VERSION


def test_normal_run_zero_counts_with_stub_pipeline(tmp_path):
    """Stub pipeline returns (0, 0) — no canonical objects, no rejects."""
    _setup(tmp_path)
    result = orchestrator_run(str(tmp_path))
    assert result["canonicalizedCount"] == 0
    assert result["rejectedCount"] == 0
