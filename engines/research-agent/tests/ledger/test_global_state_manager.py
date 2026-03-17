"""
Tests for ledger/global_state_manager.py.

Invariant enforced: Every read call issues a fresh disk read.
No caching is permitted between calls.
"""

import json

import pytest

from engines.research_engine.ledger.global_state_manager import (
    GLOBAL_STATE_SCHEMA_VERSION,
    SEASON_STATE_SCHEMA_VERSION,
    GlobalStateReadError,
    LedgerState,
    PreflightError,
    SeasonStateReadError,
    preflight_read,
    read_global_state,
    read_season_state,
    write_global_state,
    write_season_state,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_global_state(tmp_path, **overrides):
    data = {
        "schemaVersion": "GLOBAL_STATE-1.0",
        "activeSeason": "2024_REG",
        "activeRunPath": "runs/2024_REG",
        "systemStatus": "operational",
    }
    data.update(overrides)
    path = tmp_path / "global_state.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def _make_season_state(tmp_path, active_run_path="runs/2024_REG", **overrides):
    data = {
        "schemaVersion": "SEASON_STATE-1.0",
        "season": "2024_REG",
        "terminationStatus": "running",
        "microBatchCount": 0,
        "auditCycleCount": 0,
        "retryFailureCount": 0,
        "incompleteBatchFlag": False,
        "activeBatchId": None,
        "commitState": "idle",
        "subcategoryCounts": {},
        "exhaustionCounters": {},
        "lastUpdated": "2024-09-01T00:00:00+00:00",
    }
    data.update(overrides)
    run_dir = tmp_path / active_run_path
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "state.json").write_text(json.dumps(data), encoding="utf-8")
    return data


# ---------------------------------------------------------------------------
# read_global_state
# ---------------------------------------------------------------------------

def test_read_global_state_valid(tmp_path):
    expected = _make_global_state(tmp_path)
    result = read_global_state(str(tmp_path))
    assert result == expected


def test_read_global_state_file_not_found(tmp_path):
    with pytest.raises(GlobalStateReadError) as exc_info:
        read_global_state(str(tmp_path))
    assert str(tmp_path) in exc_info.value.path


def test_read_global_state_wrong_schema_version(tmp_path):
    _make_global_state(tmp_path, schemaVersion="WRONG-1.0")
    with pytest.raises(GlobalStateReadError) as exc_info:
        read_global_state(str(tmp_path))
    assert "GLOBAL_STATE-1.0" in str(exc_info.value)
    assert "WRONG-1.0" in str(exc_info.value)


def test_read_global_state_invalid_json(tmp_path):
    (tmp_path / "global_state.json").write_text("{not valid json", encoding="utf-8")
    with pytest.raises(GlobalStateReadError):
        read_global_state(str(tmp_path))


def test_read_global_state_no_caching(tmp_path):
    """Every call must re-read from disk — no stale memory."""
    _make_global_state(tmp_path, activeSeason="2024_REG")
    first = read_global_state(str(tmp_path))
    assert first["activeSeason"] == "2024_REG"

    # Overwrite with different data
    _make_global_state(tmp_path, activeSeason="2025_PRE")
    second = read_global_state(str(tmp_path))
    assert second["activeSeason"] == "2025_PRE"


# ---------------------------------------------------------------------------
# read_season_state
# ---------------------------------------------------------------------------

def test_read_season_state_valid(tmp_path):
    expected = _make_season_state(tmp_path)
    result = read_season_state(str(tmp_path), "runs/2024_REG")
    assert result == expected


def test_read_season_state_file_not_found(tmp_path):
    with pytest.raises(SeasonStateReadError) as exc_info:
        read_season_state(str(tmp_path), "runs/2024_REG")
    assert exc_info.value.path != ""


def test_read_season_state_wrong_schema_version(tmp_path):
    _make_season_state(tmp_path, schemaVersion="WRONG-1.0")
    with pytest.raises(SeasonStateReadError) as exc_info:
        read_season_state(str(tmp_path), "runs/2024_REG")
    assert "SEASON_STATE-1.0" in str(exc_info.value)


def test_read_season_state_trailing_slash_normalized(tmp_path):
    """active_run_path with trailing slash must resolve correctly."""
    _make_season_state(tmp_path, active_run_path="runs/2024_REG")
    result = read_season_state(str(tmp_path), "runs/2024_REG/")
    assert result["schemaVersion"] == "SEASON_STATE-1.0"


def test_read_season_state_no_caching(tmp_path):
    """Every call must re-read from disk."""
    _make_season_state(tmp_path, microBatchCount=0)
    first = read_season_state(str(tmp_path), "runs/2024_REG")
    assert first["microBatchCount"] == 0

    _make_season_state(tmp_path, microBatchCount=5)
    second = read_season_state(str(tmp_path), "runs/2024_REG")
    assert second["microBatchCount"] == 5


# ---------------------------------------------------------------------------
# preflight_read
# ---------------------------------------------------------------------------

def test_preflight_read_passes(tmp_path):
    _make_global_state(tmp_path)
    _make_season_state(tmp_path)
    result = preflight_read(str(tmp_path))
    assert isinstance(result, LedgerState)
    assert result.global_state["systemStatus"] == "operational"
    assert result.season_state["terminationStatus"] == "running"


def test_preflight_read_halted_raises(tmp_path):
    _make_global_state(tmp_path, systemStatus="halted")
    _make_season_state(tmp_path)
    with pytest.raises(PreflightError) as exc_info:
        preflight_read(str(tmp_path))
    assert exc_info.value.reason_code == "SYSTEM_HALTED"


def test_preflight_read_sealed_raises(tmp_path):
    _make_global_state(tmp_path)
    _make_season_state(tmp_path, terminationStatus="sealed")
    with pytest.raises(PreflightError) as exc_info:
        preflight_read(str(tmp_path))
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"
    assert "sealed" in exc_info.value.detail


def test_preflight_read_exhausted_raises(tmp_path):
    _make_global_state(tmp_path)
    _make_season_state(tmp_path, terminationStatus="exhausted")
    with pytest.raises(PreflightError) as exc_info:
        preflight_read(str(tmp_path))
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"


def test_preflight_read_system_failure_raises(tmp_path):
    _make_global_state(tmp_path)
    _make_season_state(tmp_path, terminationStatus="system_failure")
    with pytest.raises(PreflightError) as exc_info:
        preflight_read(str(tmp_path))
    assert exc_info.value.reason_code == "TERMINATION_BLOCKED"


def test_preflight_halted_does_not_read_season_state(tmp_path):
    """If global state is halted, season state need not exist."""
    _make_global_state(tmp_path, systemStatus="halted")
    # No season state file created intentionally
    with pytest.raises(PreflightError) as exc_info:
        preflight_read(str(tmp_path))
    assert exc_info.value.reason_code == "SYSTEM_HALTED"


def test_preflight_read_twice_issues_four_disk_reads(tmp_path):
    """Two preflight calls with mutated disk state must return updated values."""
    _make_global_state(tmp_path)
    _make_season_state(tmp_path, microBatchCount=0)

    r1 = preflight_read(str(tmp_path))
    assert r1.season_state["microBatchCount"] == 0

    _make_season_state(tmp_path, microBatchCount=3)
    r2 = preflight_read(str(tmp_path))
    assert r2.season_state["microBatchCount"] == 3


# ---------------------------------------------------------------------------
# write_global_state
# ---------------------------------------------------------------------------

def test_write_global_state_round_trip(tmp_path):
    data = {
        "schemaVersion": "GLOBAL_STATE-1.0",
        "activeSeason": "2024_REG",
        "activeRunPath": "runs/2024_REG",
        "systemStatus": "operational",
    }
    write_global_state(str(tmp_path), data)
    result = read_global_state(str(tmp_path))
    assert result == data


def test_write_global_state_wrong_version_raises(tmp_path):
    data = {
        "schemaVersion": "WRONG-9.9",
        "activeSeason": "2024_REG",
        "activeRunPath": "runs/2024_REG",
        "systemStatus": "operational",
    }
    with pytest.raises(GlobalStateReadError):
        write_global_state(str(tmp_path), data)


# ---------------------------------------------------------------------------
# write_season_state
# ---------------------------------------------------------------------------

def test_write_season_state_round_trip(tmp_path):
    run_dir = tmp_path / "runs" / "2024_REG"
    run_dir.mkdir(parents=True)
    data = {
        "schemaVersion": "SEASON_STATE-1.0",
        "season": "2024_REG",
        "terminationStatus": "running",
        "microBatchCount": 7,
        "auditCycleCount": 1,
        "retryFailureCount": 0,
        "incompleteBatchFlag": False,
        "activeBatchId": None,
        "commitState": "idle",
        "subcategoryCounts": {},
        "exhaustionCounters": {},
        "lastUpdated": "2024-09-10T12:00:00+00:00",
    }
    write_season_state(str(tmp_path), "runs/2024_REG", data)
    result = read_season_state(str(tmp_path), "runs/2024_REG")
    assert result == data


def test_write_season_state_wrong_version_raises(tmp_path):
    run_dir = tmp_path / "runs" / "2024_REG"
    run_dir.mkdir(parents=True)
    data = {"schemaVersion": "BAD-0.0"}
    with pytest.raises(SeasonStateReadError):
        write_season_state(str(tmp_path), "runs/2024_REG", data)
