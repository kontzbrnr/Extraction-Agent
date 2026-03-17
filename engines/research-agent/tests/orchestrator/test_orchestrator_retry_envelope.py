import json
from unittest.mock import patch

import pytest

from infra.orchestration.runtime.orchestrator import orchestrator_run
from engines.research_engine.ledger.season_state_manager import create_season_run, read_season_state, write_season_state
from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION


def _setup(tmp_path, retry_failure_count=0):
    """Write minimal operational ledger.

    active_run_path = "runs/S2024/run_001"
    season = "S2024"
    systemStatus = "operational"
    terminationStatus = "running"
    retryFailureCount = retry_failure_count
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
    if retry_failure_count:
        state = read_season_state(ledger_root, active_run_path)
        state["retryFailureCount"] = retry_failure_count
        write_season_state(ledger_root, active_run_path, state)

    return ledger_root, active_run_path


# ---------------------------------------------------------------------------
# GROUP A — No exception (clean run unaffected)
# ---------------------------------------------------------------------------


def test_no_exception_clean_run_normal_status(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline", return_value=None):
        result = orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert result["action"] == "new_batch"
    assert result["terminationStatus"] == "running"
    assert state["terminationStatus"] == "running"


def test_no_exception_retry_count_unchanged(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline", return_value=None):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 0


# ---------------------------------------------------------------------------
# GROUP B — First failure only (retry succeeds)
# ---------------------------------------------------------------------------


def test_first_failure_retry_succeeds_status_running(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=[RuntimeError("agent failure"), None],
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "running"


def test_first_failure_retry_succeeds_retry_count_not_incremented(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=[RuntimeError("agent failure"), None],
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 0


def test_first_failure_retry_succeeds_boundary_runs(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=[RuntimeError("agent failure"), None],
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["microBatchCount"] == 1


# ---------------------------------------------------------------------------
# GROUP C — Both failures, retryFailureCount reaches 2
# ---------------------------------------------------------------------------


def test_both_failures_threshold_reached_sets_system_failure(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=1)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "system_failure"


def test_both_failures_threshold_reached_retry_count_two(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=1)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 2


def test_both_failures_threshold_reached_return_counts_zero(tmp_path):
    ledger_root, _ = _setup(tmp_path, retry_failure_count=1)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        result = orchestrator_run(ledger_root)

    assert result["canonicalizedCount"] == 0
    assert result["rejectedCount"] == 0


def test_both_failures_threshold_reached_flag_remains_true(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=1)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["incompleteBatchFlag"] is True


# ---------------------------------------------------------------------------
# GROUP D — Both failures, retryFailureCount below threshold
# ---------------------------------------------------------------------------


def test_both_failures_below_threshold_increments_to_one(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["retryFailureCount"] == 1


def test_both_failures_below_threshold_status_running(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "running"


def test_both_failures_below_threshold_flag_remains_true(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=RuntimeError("agent failure"),
    ):
        orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["incompleteBatchFlag"] is True


# ---------------------------------------------------------------------------
# GROUP E — Retry uses fresh collector
# ---------------------------------------------------------------------------


def test_retry_attempt_calls_pipeline_twice(tmp_path):
    ledger_root, _ = _setup(tmp_path, retry_failure_count=0)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=[RuntimeError("agent failure"), None],
    ) as mock_pipeline:
        orchestrator_run(ledger_root)

    assert mock_pipeline.call_count == 2
