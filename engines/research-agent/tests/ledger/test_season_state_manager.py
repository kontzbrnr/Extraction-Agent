"""
Tests for ledger/season_state_manager.py.
"""

import json

import pytest

from engines.research_engine.ledger.global_state_manager import read_season_state
from engines.research_engine.ledger.season_state_manager import (
    InvalidTerminationTransitionError,
    SeasonRunExistsError,
    SeasonStateError,
    create_season_run,
    increment_audit_cycle_count,
    increment_micro_batch_count,
    increment_retry_failure_count,
    set_termination_status,
    update_exhaustion_counters,
    update_subcategory_counts,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

RUN_PATH = "runs/2024_REG"


def _state_path(tmp_path, run_path=RUN_PATH):
    return tmp_path / run_path / "state.json"


def _read_raw(tmp_path, run_path=RUN_PATH):
    return json.loads(_state_path(tmp_path, run_path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# create_season_run
# ---------------------------------------------------------------------------

def test_create_season_run_writes_state_json(tmp_path):
    result = create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    assert _state_path(tmp_path).exists()
    assert result["schemaVersion"] == "SEASON_STATE-1.0"
    assert result["season"] == "2024_REG"


def test_create_season_run_all_required_fields_present(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    data = _read_raw(tmp_path)
    required = [
        "schemaVersion",
        "season",
        "terminationStatus",
        "microBatchCount",
        "auditCycleCount",
        "retryFailureCount",
        "incompleteBatchFlag",
        "activeBatchId",
        "commitState",
        "subcategoryCounts",
        "exhaustionCounters",
        "lastUpdated",
    ]
    for field in required:
        assert field in data, f"Missing required field: {field}"


def test_create_season_run_initial_values(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    data = _read_raw(tmp_path)
    assert data["terminationStatus"] == "running"
    assert data["microBatchCount"] == 0
    assert data["auditCycleCount"] == 0
    assert data["retryFailureCount"] == 0
    assert data["incompleteBatchFlag"] is False
    assert data["activeBatchId"] is None
    assert data["commitState"] == "idle"
    assert data["subcategoryCounts"] == {}
    assert data["exhaustionCounters"] == {}


def test_create_season_run_creates_directory(tmp_path):
    run_path = "runs/2025_PRE"
    create_season_run(str(tmp_path), "2025_PRE", run_path)
    assert (tmp_path / run_path / "state.json").exists()


def test_create_season_run_raises_if_already_exists(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    with pytest.raises(SeasonRunExistsError) as exc_info:
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    assert str(exc_info.value.path) != ""


def test_create_season_run_readable_by_read_season_state(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    result = read_season_state(str(tmp_path), RUN_PATH)
    assert result["schemaVersion"] == "SEASON_STATE-1.0"


# ---------------------------------------------------------------------------
# increment_micro_batch_count
# ---------------------------------------------------------------------------

def test_increment_micro_batch_count_starts_at_zero(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    new_count = increment_micro_batch_count(str(tmp_path), RUN_PATH)
    assert new_count == 1


def test_increment_micro_batch_count_returns_new_count(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    assert increment_micro_batch_count(str(tmp_path), RUN_PATH) == 1
    assert increment_micro_batch_count(str(tmp_path), RUN_PATH) == 2
    assert increment_micro_batch_count(str(tmp_path), RUN_PATH) == 3


def test_increment_micro_batch_count_persisted_to_disk(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    increment_micro_batch_count(str(tmp_path), RUN_PATH)
    increment_micro_batch_count(str(tmp_path), RUN_PATH)
    data = _read_raw(tmp_path)
    assert data["microBatchCount"] == 2


def test_increment_micro_batch_count_reads_disk_each_call(tmp_path):
    """Simulate external write between calls — increment must reflect disk state."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # Externally set microBatchCount to 10 on disk
    data = _read_raw(tmp_path)
    data["microBatchCount"] = 10
    _state_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")

    new_count = increment_micro_batch_count(str(tmp_path), RUN_PATH)
    assert new_count == 11


def test_increment_micro_batch_count_ten_sequential(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    for expected in range(1, 11):
        count = increment_micro_batch_count(str(tmp_path), RUN_PATH)
        assert count == expected
    assert _read_raw(tmp_path)["microBatchCount"] == 10


# ---------------------------------------------------------------------------
# set_termination_status
# ---------------------------------------------------------------------------

def test_set_termination_status_sealed(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "sealed")
    assert _read_raw(tmp_path)["terminationStatus"] == "sealed"


def test_set_termination_status_exhausted(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "exhausted")
    assert _read_raw(tmp_path)["terminationStatus"] == "exhausted"


def test_set_termination_status_system_failure(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "system_failure")
    assert _read_raw(tmp_path)["terminationStatus"] == "system_failure"


def test_set_termination_status_running_is_invalid_target(tmp_path):
    """'running' is the initial state only — not a valid transition target."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    with pytest.raises(InvalidTerminationTransitionError) as exc_info:
        set_termination_status(str(tmp_path), RUN_PATH, "running")
    assert exc_info.value.attempted == "running"


def test_set_termination_status_unknown_value_raises_before_disk_read(tmp_path):
    """Unknown status must raise immediately — no disk mutation."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    with pytest.raises(SeasonStateError):
        set_termination_status(str(tmp_path), RUN_PATH, "INVALID_STATUS")
    assert _read_raw(tmp_path)["terminationStatus"] == "running"


def test_set_termination_status_from_sealed_is_blocked(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "sealed")
    with pytest.raises(InvalidTerminationTransitionError) as exc_info:
        set_termination_status(str(tmp_path), RUN_PATH, "exhausted")
    assert exc_info.value.current == "sealed"
    assert exc_info.value.attempted == "exhausted"


def test_set_termination_status_from_exhausted_is_blocked(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "exhausted")
    with pytest.raises(InvalidTerminationTransitionError):
        set_termination_status(str(tmp_path), RUN_PATH, "sealed")


def test_set_termination_status_from_system_failure_is_blocked(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "system_failure")
    with pytest.raises(InvalidTerminationTransitionError):
        set_termination_status(str(tmp_path), RUN_PATH, "sealed")


def test_set_termination_status_persisted_to_disk(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    set_termination_status(str(tmp_path), RUN_PATH, "sealed")
    data = read_season_state(str(tmp_path), RUN_PATH)
    assert data["terminationStatus"] == "sealed"


# ---------------------------------------------------------------------------
# Phase 1.5 — Incomplete Batch Flag System
# ---------------------------------------------------------------------------

from engines.research_engine.ledger.season_state_manager import (
    BatchAlreadyInProgressError,
    clear_incomplete_batch_flag,
    mark_batch_start,
)

BATCH_ID = "BATCH_2024_REG_0001"


class TestMarkBatchStart:

    def test_sets_flag_true(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is True

    def test_sets_active_batch_id(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        assert _read_raw(tmp_path)["activeBatchId"] == BATCH_ID

    def test_raises_if_already_in_progress(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        with pytest.raises(BatchAlreadyInProgressError) as exc_info:
            mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0002")
        assert exc_info.value.current_batch_id == BATCH_ID

    def test_raises_before_mutating_disk(self, tmp_path):
        """No disk mutation on BatchAlreadyInProgressError."""
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        try:
            mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0002")
        except BatchAlreadyInProgressError:
            pass
        # activeBatchId must remain the original
        assert _read_raw(tmp_path)["activeBatchId"] == BATCH_ID

    def test_empty_batch_id_raises_value_error(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        with pytest.raises(ValueError):
            mark_batch_start(str(tmp_path), RUN_PATH, "")

    def test_does_not_mutate_termination_status(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        assert _read_raw(tmp_path)["terminationStatus"] == "running"

    def test_does_not_mutate_micro_batch_count(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        assert _read_raw(tmp_path)["microBatchCount"] == 0

    def test_reads_disk_each_call(self, tmp_path):
        """Flag detection must reflect current disk state, not a cached snapshot."""
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        # Externally clear the flag on disk (simulating clear_incomplete_batch_flag)
        data = _read_raw(tmp_path)
        data["incompleteBatchFlag"] = False
        data["activeBatchId"] = None
        _state_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")
        # Should now succeed — flag was cleared on disk
        mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0002")
        assert _read_raw(tmp_path)["activeBatchId"] == "BATCH_2024_REG_0002"


class TestClearIncompleteBatchFlag:

    def test_clears_flag(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is False

    def test_clears_active_batch_id(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)
        assert _read_raw(tmp_path)["activeBatchId"] is None

    def test_idempotent_when_already_false(self, tmp_path):
        """Double-clear must not raise and must leave flag at False."""
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)  # already False
        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)  # second clear
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is False

    def test_does_not_mutate_other_fields(self, tmp_path):
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)
        increment_micro_batch_count(str(tmp_path), RUN_PATH)
        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)
        data = _read_raw(tmp_path)
        assert data["microBatchCount"] == 1
        assert data["terminationStatus"] == "running"

    def test_full_batch_lifecycle(self, tmp_path):
        """start → clear → start → clear round-trip."""
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)

        mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0001")
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is True

        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is False

        mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0002")
        assert _read_raw(tmp_path)["activeBatchId"] == "BATCH_2024_REG_0002"

        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is False
        assert _read_raw(tmp_path)["activeBatchId"] is None

    def test_crash_recovery_pattern(self, tmp_path):
        """Simulate crash: flag left True on disk. Recovery: clear then start new batch."""
        create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
        mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0001")

        # Crash — flag remains True on disk. New invocation detects it.
        data = _read_raw(tmp_path)
        assert data["incompleteBatchFlag"] is True

        # Crash recovery: clear flag, do NOT mutate canonical registry
        clear_incomplete_batch_flag(str(tmp_path), RUN_PATH)
        assert _read_raw(tmp_path)["incompleteBatchFlag"] is False
        assert _read_raw(tmp_path)["activeBatchId"] is None

        # Start new batch — must succeed after recovery
        mark_batch_start(str(tmp_path), RUN_PATH, "BATCH_2024_REG_0002")
        assert _read_raw(tmp_path)["activeBatchId"] == "BATCH_2024_REG_0002"


# ---------------------------------------------------------------------------
# increment_audit_cycle_count
# ---------------------------------------------------------------------------

def test_increment_audit_cycle_count_from_zero(tmp_path):
    """auditCycleCount: 0 → 1."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    result = increment_audit_cycle_count(str(tmp_path), RUN_PATH)
    assert result == 1
    assert _read_raw(tmp_path)["auditCycleCount"] == 1


def test_increment_audit_cycle_count_from_preset_value(tmp_path):
    """auditCycleCount: 5 → 6 (pre-set value)."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # Pre-set auditCycleCount
    data = _read_raw(tmp_path)
    data["auditCycleCount"] = 5
    _state_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")

    result = increment_audit_cycle_count(str(tmp_path), RUN_PATH)
    assert result == 6
    assert _read_raw(tmp_path)["auditCycleCount"] == 6


def test_increment_audit_cycle_count_inv1_unconditional_disk_read(tmp_path):
    """INV-1: increment_audit_cycle_count always reads from disk, never uses cached state."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # First increment
    result1 = increment_audit_cycle_count(str(tmp_path), RUN_PATH)
    assert result1 == 1
    # Mutate disk directly (simulating concurrent modification)
    data = _read_raw(tmp_path)
    data["auditCycleCount"] = 100
    _state_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")
    # Second increment — must read the mutated disk value
    result2 = increment_audit_cycle_count(str(tmp_path), RUN_PATH)
    assert result2 == 101
    assert _read_raw(tmp_path)["auditCycleCount"] == 101


# ---------------------------------------------------------------------------
# update_subcategory_counts
# ---------------------------------------------------------------------------

def test_update_subcategory_counts_empty_delta_no_write(tmp_path):
    """update_subcategory_counts with empty delta: no write side effect."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # Get initial timestamp
    data_before = _read_raw(tmp_path)
    ts_before = data_before["lastUpdated"]

    # Call with empty delta (should no-op)
    update_subcategory_counts(str(tmp_path), RUN_PATH, {})
    data_after = _read_raw(tmp_path)
    ts_after = data_after["lastUpdated"]

    # Timestamp unchanged (no write occurred)
    assert ts_before == ts_after
    assert data_after["subcategoryCounts"] == {}


def test_update_subcategory_counts_merge_existing_surface(tmp_path):
    """update_subcategory_counts merge: {"offseason": 1} + delta {"offseason": 2} = {"offseason": 3}."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # Pre-set subcategoryCounts
    data = _read_raw(tmp_path)
    data["subcategoryCounts"] = {"offseason": 1}
    _state_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")

    # Merge delta
    update_subcategory_counts(str(tmp_path), RUN_PATH, {"offseason": 2})
    assert _read_raw(tmp_path)["subcategoryCounts"] == {"offseason": 3}


def test_update_subcategory_counts_new_surface(tmp_path):
    """update_subcategory_counts new surface: {} + delta {"training_camp": 1} = {"training_camp": 1}."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # subcategoryCounts is {} by default
    assert _read_raw(tmp_path)["subcategoryCounts"] == {}

    # Merge delta with new surface
    update_subcategory_counts(str(tmp_path), RUN_PATH, {"training_camp": 1})
    assert _read_raw(tmp_path)["subcategoryCounts"] == {"training_camp": 1}


# ---------------------------------------------------------------------------
# update_exhaustion_counters
# ---------------------------------------------------------------------------

def test_update_exhaustion_counters_merge(tmp_path):
    """update_exhaustion_counters merge: {} + delta {"regular_season": 3} = {"regular_season": 3}."""
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    # exhaustionCounters is {} by default
    assert _read_raw(tmp_path)["exhaustionCounters"] == {}

    # Merge delta
    update_exhaustion_counters(str(tmp_path), RUN_PATH, {"regular_season": 3})
    assert _read_raw(tmp_path)["exhaustionCounters"] == {"regular_season": 3}


# ---------------------------------------------------------------------------
# increment_retry_failure_count
# ---------------------------------------------------------------------------

def test_increment_retry_failure_count_from_zero(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    result = increment_retry_failure_count(str(tmp_path), RUN_PATH)
    assert result == 1
    assert _read_raw(tmp_path)["retryFailureCount"] == 1


def test_increment_retry_failure_count_twice(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)
    first = increment_retry_failure_count(str(tmp_path), RUN_PATH)
    second = increment_retry_failure_count(str(tmp_path), RUN_PATH)
    assert first == 1
    assert second == 2
    assert _read_raw(tmp_path)["retryFailureCount"] == 2


def test_increment_retry_failure_count_inv1_unconditional_disk_read(tmp_path):
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)

    # Prior in-memory read
    _ = read_season_state(str(tmp_path), RUN_PATH)

    # External disk write after in-memory read
    data = _read_raw(tmp_path)
    data["retryFailureCount"] = 5
    _state_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")

    # Must read fresh value from disk (5) then increment to 6
    result = increment_retry_failure_count(str(tmp_path), RUN_PATH)
    assert result == 6
    assert _read_raw(tmp_path)["retryFailureCount"] == 6
