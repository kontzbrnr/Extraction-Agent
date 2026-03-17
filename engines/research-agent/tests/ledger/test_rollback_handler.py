"""
tests/ledger/test_rollback_handler.py

Tests for ledger/rollback_handler.py.

Key invariant under test: canonical_objects.json is never touched during
crash recovery (INV-3). Verified by byte-identity check before and after.
"""

import json
import os
import pytest

from engines.research_engine.ledger.rollback_handler import CrashRecoveryResult, handle_crash_recovery
from engines.research_engine.ledger.season_state_manager import (
    create_season_run,
    mark_batch_start,
)
from engines.research_engine.ledger.global_state_manager import read_season_state


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

RUN_PATH = "runs/2024_REG"
BATCH_ID = "BATCH_2024_REG_0001"


def _state_path(tmp_path):
    return tmp_path / RUN_PATH / "state.json"


def _read_raw(tmp_path):
    return json.loads(_state_path(tmp_path).read_text(encoding="utf-8"))


def _write_fake_registry(tmp_path):
    """Write a sentinel canonical_objects.json and return its byte content."""
    registry_path = tmp_path / RUN_PATH / "canonical_objects.json"
    content = json.dumps({"schemaVersion": "CANONICAL_REGISTRY-1.0", "CPS": []})
    registry_path.write_text(content, encoding="utf-8")
    return registry_path.read_bytes()


# ---------------------------------------------------------------------------
# No crash detected — no-op path
# ---------------------------------------------------------------------------


def test_no_crash_returns_rollback_false(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    result = handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert isinstance(result, CrashRecoveryResult)
    assert result.rollback_performed is False
    assert result.recovered_batch_id is None


def test_no_crash_zero_disk_mutations(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    before = _read_raw(tmp_path)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    after = _read_raw(tmp_path)
    # lastUpdated may differ only if a write occurred — it must not
    assert before == after


def test_no_crash_double_call_no_mutation(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    before = _read_raw(tmp_path)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    after = _read_raw(tmp_path)
    assert before == after


# ---------------------------------------------------------------------------
# Crash detected — rollback path
# ---------------------------------------------------------------------------


def test_crash_detected_returns_rollback_true(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    result = handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert result.rollback_performed is True


def test_crash_detected_returns_correct_batch_id(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    result = handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert result.recovered_batch_id == BATCH_ID


def test_rollback_clears_incomplete_flag(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["incompleteBatchFlag"] is False


def test_rollback_clears_active_batch_id(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["activeBatchId"] is None


def test_rollback_resets_commit_state_to_idle(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    # Simulate commitState left as "in_progress" from a crash
    state = _read_raw(tmp_path)
    state["commitState"] = "in_progress"
    _state_path(tmp_path).write_text(json.dumps(state), encoding="utf-8")
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["commitState"] == "idle"


def test_rollback_resets_commit_state_failed_to_idle(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    state = _read_raw(tmp_path)
    state["commitState"] = "failed"
    _state_path(tmp_path).write_text(json.dumps(state), encoding="utf-8")
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["commitState"] == "idle"


# ---------------------------------------------------------------------------
# Field preservation — other fields must be unchanged
# ---------------------------------------------------------------------------


def test_rollback_preserves_termination_status(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["terminationStatus"] == "running"


def test_rollback_preserves_micro_batch_count(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # Simulate 3 completed batches before the crash
    state = _read_raw(tmp_path)
    state["microBatchCount"] = 3
    state["incompleteBatchFlag"] = True
    state["activeBatchId"] = BATCH_ID
    _state_path(tmp_path).write_text(json.dumps(state), encoding="utf-8")
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["microBatchCount"] == 3


def test_rollback_preserves_audit_cycle_count(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    state = _read_raw(tmp_path)
    state["auditCycleCount"] = 2
    state["incompleteBatchFlag"] = True
    state["activeBatchId"] = BATCH_ID
    _state_path(tmp_path).write_text(json.dumps(state), encoding="utf-8")
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["auditCycleCount"] == 2


def test_rollback_preserves_retry_failure_count(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    state = _read_raw(tmp_path)
    state["retryFailureCount"] = 1
    state["incompleteBatchFlag"] = True
    state["activeBatchId"] = BATCH_ID
    _state_path(tmp_path).write_text(json.dumps(state), encoding="utf-8")
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["retryFailureCount"] == 1


def test_rollback_preserves_subcategory_counts(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    state = _read_raw(tmp_path)
    state["subcategoryCounts"] = {"surface_A": 4, "surface_B": 2}
    state["incompleteBatchFlag"] = True
    state["activeBatchId"] = BATCH_ID
    _state_path(tmp_path).write_text(json.dumps(state), encoding="utf-8")
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert _read_raw(tmp_path)["subcategoryCounts"] == {"surface_A": 4, "surface_B": 2}


# ---------------------------------------------------------------------------
# INV-3 — canonical_objects.json must never be touched
# ---------------------------------------------------------------------------


def test_canonical_registry_not_touched_on_no_crash(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    before_bytes = _write_fake_registry(tmp_path)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    after_bytes = (tmp_path / RUN_PATH / "canonical_objects.json").read_bytes()
    assert before_bytes == after_bytes


def test_canonical_registry_not_touched_on_rollback(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    before_bytes = _write_fake_registry(tmp_path)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    after_bytes = (tmp_path / RUN_PATH / "canonical_objects.json").read_bytes()
    assert before_bytes == after_bytes


def test_canonical_registry_not_created_if_absent(tmp_path):
    """Handler must not create canonical_objects.json if it didn't exist."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    registry_path = tmp_path / RUN_PATH / "canonical_objects.json"
    assert not registry_path.exists()
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    assert not registry_path.exists()


# ---------------------------------------------------------------------------
# Recovery enables clean batch start
# ---------------------------------------------------------------------------


def test_recovery_enables_new_batch_start(tmp_path):
    """After rollback, mark_batch_start must succeed for the next batch."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    # Should not raise BatchAlreadyInProgressError
    mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0002")
    assert _read_raw(tmp_path)["activeBatchId"] == "BATCH_2024_REG_0002"


def test_state_readable_by_read_season_state_after_rollback(tmp_path):
    """Rolled-back state must pass schema validation on re-read."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
    handle_crash_recovery(str(tmp_path), RUN_PATH)
    result = read_season_state(str(tmp_path), RUN_PATH)
    assert result["schemaVersion"] == "SEASON_STATE-1.0"
    assert result["incompleteBatchFlag"] is False
