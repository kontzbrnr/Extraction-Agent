import json

import pytest

from infra.orchestration.runtime.orchestrator import orchestrator_run
from infra.orchestration.nti.cycle_state_manager import create_nti_state, seal_surface
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER
from engines.research_engine.ledger.season_state_manager import (
    create_season_run,
    read_season_state,
    write_season_state,
)
from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION


def _setup(tmp_path, with_nti_state=True, seal_all=False):
    """Write minimal operational ledger.

    active_run_path = "runs/S2024/run_001"
    season = "S2024"
    systemStatus = "operational"
    terminationStatus = "running"
    Creates global_state.json and state.json.
    Optionally creates nti_state.json and optionally seals all surfaces.
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

    if with_nti_state:
        create_nti_state(ledger_root, active_run_path)
        if seal_all:
            for surface in SURFACE_ROTATION_ORDER:
                seal_surface(ledger_root, active_run_path, surface)

    return ledger_root, active_run_path


# ---------------------------------------------------------------------------
# GROUP A — NTI sealed path (3 tests)
# ---------------------------------------------------------------------------


def test_nti_all_surfaces_sealed_sets_termination_sealed(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=True, seal_all=True)

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "sealed"


def test_nti_zero_surfaces_sealed_stays_running(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=True, seal_all=False)

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "running"


def test_nti_seven_of_eight_surfaces_sealed_stays_running(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=True, seal_all=False)
    for surface in SURFACE_ROTATION_ORDER[:7]:
        seal_surface(ledger_root, active_run_path, surface)

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "running"


# ---------------------------------------------------------------------------
# GROUP B — NTI state absent stub (2 tests)
# ---------------------------------------------------------------------------


def test_no_nti_state_orchestrator_completes_and_stays_running(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=False)

    orchestrator_run(ledger_root)

    state = read_season_state(ledger_root, active_run_path)
    assert state["terminationStatus"] == "running"


def test_no_nti_state_returns_new_batch_action(tmp_path):
    ledger_root, _ = _setup(tmp_path, with_nti_state=False)

    result = orchestrator_run(ledger_root)

    assert result["action"] == "new_batch"


# ---------------------------------------------------------------------------
# GROUP C — retry failure gate (3 tests)
# ---------------------------------------------------------------------------


def test_retry_failure_count_two_sets_system_failure(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=True, seal_all=False)

    state = read_season_state(ledger_root, active_run_path)
    state["retryFailureCount"] = 2
    write_season_state(ledger_root, active_run_path, state)

    orchestrator_run(ledger_root)

    state_after = read_season_state(ledger_root, active_run_path)
    assert state_after["terminationStatus"] == "system_failure"


def test_retry_failure_count_two_no_nti_state_no_crash(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=False)

    state = read_season_state(ledger_root, active_run_path)
    state["retryFailureCount"] = 2
    write_season_state(ledger_root, active_run_path, state)

    result = orchestrator_run(ledger_root)

    state_after = read_season_state(ledger_root, active_run_path)
    assert result["action"] == "new_batch"
    assert state_after["terminationStatus"] == "system_failure"


def test_retry_failure_count_one_stays_running(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=True, seal_all=False)

    state = read_season_state(ledger_root, active_run_path)
    state["retryFailureCount"] = 1
    write_season_state(ledger_root, active_run_path, state)

    orchestrator_run(ledger_root)

    state_after = read_season_state(ledger_root, active_run_path)
    assert state_after["terminationStatus"] == "running"


# ---------------------------------------------------------------------------
# GROUP D — ordering invariant (1 test)
# ---------------------------------------------------------------------------


def test_retry_gate_precedes_nti_sealed_path(tmp_path):
    ledger_root, active_run_path = _setup(tmp_path, with_nti_state=True, seal_all=True)

    state = read_season_state(ledger_root, active_run_path)
    state["retryFailureCount"] = 2
    write_season_state(ledger_root, active_run_path, state)

    orchestrator_run(ledger_root)

    state_after = read_season_state(ledger_root, active_run_path)
    assert state_after["terminationStatus"] == "system_failure"
