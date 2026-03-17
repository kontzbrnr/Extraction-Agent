import json

import pytest

from infra.orchestration.runtime.orchestrator import orchestrator_run
from engines.research_engine.ledger.season_state_manager import (
    create_season_run,
    mark_batch_start,
    read_season_state,
    write_season_state,
)
from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION


def _setup(tmp_path, incomplete_batch_flag=False, retry_failure_count=0):
    """Write minimal operational ledger.

    active_run_path = "runs/S2024/run_001"
    season = "S2024"
    systemStatus = "operational"
    terminationStatus = "running"
    incompleteBatchFlag = incomplete_batch_flag
    retryFailureCount = retry_failure_count
    activeBatchId = "BATCH_S2024_0000" if incomplete_batch_flag else None
    Creates global_state.json and state.json.
    Returns (ledger_root_str, active_run_path_str).
    """
    ledger_root = str(tmp_path)
    active_run_path = "runs/S2024/run_001"
    season = "S2024"

    atomic_write_json(
        str(tmp_path / "global_state.json"),
        {
            "schemaVersion": GLOBAL_STATE_SCHEMA_VERSION,
            "enumVersion": "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
            "activeSeason": season,
            "activeRunPath": active_run_path,
            "systemStatus": "operational",
        },
    )

    create_season_run(ledger_root, season, active_run_path)

    state = read_season_state(ledger_root, active_run_path)
    state["incompleteBatchFlag"] = incomplete_batch_flag
    state["retryFailureCount"] = retry_failure_count
    state["activeBatchId"] = "BATCH_S2024_0000" if incomplete_batch_flag else None
    write_season_state(ledger_root, active_run_path, state)

    return ledger_root, active_run_path


# ---------------------------------------------------------------------------
# GROUP A — first crash (retryFailureCount reaches 1)
# ---------------------------------------------------------------------------


def test_first_crash_increments_retry_failure_count_to_one(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=0,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 1


def test_first_crash_returns_crash_recovery_action(tmp_path):
    ledger_root, _ = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=0,
    )

    result = orchestrator_run(ledger_root)

    assert result["action"] == "crash_recovery"


def test_first_crash_stays_running_and_clears_flag(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=0,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "running"
    assert state["incompleteBatchFlag"] is False


# ---------------------------------------------------------------------------
# GROUP B — second crash (retryFailureCount reaches 2)
# ---------------------------------------------------------------------------


def test_second_crash_increments_retry_failure_count_to_two(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=1,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 2


def test_second_crash_sets_system_failure(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=1,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "system_failure"


def test_second_crash_returns_crash_recovery_action(tmp_path):
    ledger_root, _ = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=1,
    )

    result = orchestrator_run(ledger_root)

    assert result["action"] == "crash_recovery"


def test_second_crash_early_exit_zero_counts(tmp_path):
    ledger_root, _ = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=1,
    )

    result = orchestrator_run(ledger_root)

    assert result["canonicalizedCount"] == 0
    assert result["rejectedCount"] == 0


# ---------------------------------------------------------------------------
# GROUP C — clean run is unaffected
# ---------------------------------------------------------------------------


def test_clean_run_retry_count_zero_stays_zero(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=False,
        retry_failure_count=0,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 0


def test_clean_run_retry_count_one_stays_one(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=False,
        retry_failure_count=1,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 1


# ---------------------------------------------------------------------------
# GROUP D — incompleteBatchFlag cleared on early exit
# ---------------------------------------------------------------------------


def test_second_crash_early_exit_still_clears_incomplete_flag(tmp_path):
    ledger_root, active_run_path = _setup(
        tmp_path,
        incomplete_batch_flag=True,
        retry_failure_count=1,
    )

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["incompleteBatchFlag"] is False
