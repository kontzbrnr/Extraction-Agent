"""
Tests for orchestrator.py checkpoint (_end_of_batch_boundary) implementation.

Verifies Phase 13.5 checkpoint completion:
    - microBatchCount incremented
    - auditCycleCount incremented when interval reached (AUDIT_CYCLE_INTERVAL == 1)
    - subcategoryCounts and exhaustionCounters updated (stubs: empty delta)
    - incompleteBatchFlag cleared (crash-safety sentinel)
    - All writes committed atomically to disk
"""

import json

import pytest

from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import (
    GLOBAL_STATE_SCHEMA_VERSION,
    read_season_state,
)
from engines.research_engine.ledger.season_state_manager import create_season_run
from infra.orchestration.runtime.orchestrator import AUDIT_CYCLE_INTERVAL, orchestrator_run


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_SEASON       = "2024_REG"
_RUN_PATH     = "runs/2024_REG"


def _write_global_state(tmp_path, system_status="operational"):
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


def _write_season_state(tmp_path, **overrides):
    """Create season state via API, then apply raw overrides for test fixture setup."""
    create_season_run(str(tmp_path), _SEASON, _RUN_PATH)
    if overrides:
        state_path = tmp_path / _RUN_PATH / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(overrides)
        atomic_write_json(str(state_path), state)


def _setup(tmp_path, system_status="operational", **season_overrides):
    """Write both state files. Standard entry point for all tests."""
    _write_global_state(tmp_path, system_status=system_status)
    _write_season_state(tmp_path, **season_overrides)
    # Create canonical_registry.jsonl
    registry = tmp_path / _RUN_PATH / "canonical_registry.jsonl"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text("", encoding="utf-8")


def _state_path(tmp_path, run_path=_RUN_PATH):
    return tmp_path / run_path / "state.json"


def _read_raw(tmp_path, run_path=_RUN_PATH):
    return json.loads(_state_path(tmp_path, run_path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# GROUP A: After single orchestrator_run, verify post-checkpoint state
# ---------------------------------------------------------------------------

def test_checkpoint_microBatchCount_incremented(tmp_path):
    """After orchestrator_run, microBatchCount == 1."""
    _setup(tmp_path)
    state_before = read_season_state(str(tmp_path), _RUN_PATH)
    assert state_before["microBatchCount"] == 0

    orchestrator_run(str(tmp_path))

    state_after = _read_raw(tmp_path, _RUN_PATH)
    assert state_after["microBatchCount"] == 1


def test_checkpoint_auditCycleCount_incremented_at_interval(tmp_path):
    """After orchestrator_run, auditCycleCount == 1 (AUDIT_CYCLE_INTERVAL == 1)."""
    _setup(tmp_path)
    assert AUDIT_CYCLE_INTERVAL == 1  # Governance: default 1 (every batch)
    state_before = read_season_state(str(tmp_path), _RUN_PATH)
    assert state_before["auditCycleCount"] == 0

    orchestrator_run(str(tmp_path))

    state_after = _read_raw(tmp_path, _RUN_PATH)
    assert state_after["auditCycleCount"] == 1


def test_checkpoint_subcategoryCounts_and_exhaustionCounters_unchanged(tmp_path):
    """After orchestrator_run, subcategoryCounts and exhaustionCounters unchanged (stubs: {} delta)."""
    _setup(tmp_path)
    state_before = read_season_state(str(tmp_path), _RUN_PATH)
    assert state_before["subcategoryCounts"] == {}
    assert state_before["exhaustionCounters"] == {}

    orchestrator_run(str(tmp_path))

    state_after = _read_raw(tmp_path, _RUN_PATH)
    assert state_after["subcategoryCounts"] == {}
    assert state_after["exhaustionCounters"] == {}


def test_checkpoint_incompleteBatchFlag_cleared(tmp_path):
    """After orchestrator_run, incompleteBatchFlag == False (crash-safety sentinel)."""
    _setup(tmp_path)
    # After orchestrator_run, batch is marked complete
    orchestrator_run(str(tmp_path))

    state_after = _read_raw(tmp_path, _RUN_PATH)
    assert state_after["incompleteBatchFlag"] is False


# ---------------------------------------------------------------------------
# GROUP B: Sequential runs increment counts correctly
# ---------------------------------------------------------------------------

def test_checkpoint_sequential_runs_increment_counts(tmp_path):
    """Two sequential orchestrator_run calls: microBatchCount 0 → 1 → 2, auditCycleCount 0 → 1 → 2."""
    _setup(tmp_path)

    # First run
    state1 = read_season_state(str(tmp_path), _RUN_PATH)
    assert state1["microBatchCount"] == 0
    assert state1["auditCycleCount"] == 0

    orchestrator_run(str(tmp_path))
    state1_after = _read_raw(tmp_path, _RUN_PATH)
    assert state1_after["microBatchCount"] == 1
    assert state1_after["auditCycleCount"] == 1
    assert state1_after["incompleteBatchFlag"] is False

    # Second run
    orchestrator_run(str(tmp_path))
    state2_after = _read_raw(tmp_path, _RUN_PATH)
    assert state2_after["microBatchCount"] == 2
    assert state2_after["auditCycleCount"] == 2
    assert state2_after["incompleteBatchFlag"] is False


def test_checkpoint_incompleteBatchFlag_cleared_each_run(tmp_path):
    """Each orchestrator_run clears incompleteBatchFlag (no dangling incomplete batches)."""
    _setup(tmp_path)

    for i in range(3):
        orchestrator_run(str(tmp_path))
        state = _read_raw(tmp_path, _RUN_PATH)
        assert state["incompleteBatchFlag"] is False, f"Run {i+1}: flag not cleared"


# ---------------------------------------------------------------------------
# GROUP C: AUDIT_CYCLE_INTERVAL constant validation
# ---------------------------------------------------------------------------

def test_audit_cycle_interval_constant_is_one(tmp_path):
    """Assert AUDIT_CYCLE_INTERVAL == 1 (every batch increments auditCycleCount)."""
    assert AUDIT_CYCLE_INTERVAL == 1
