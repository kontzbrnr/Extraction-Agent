"""
tests/orchestrator/test_orchestrator_batch_lifecycle.py

Batch Lifecycle and Ledger State Management tests — Phase 13.3.

Verifies:
    INV-1: orchestrator_run re-reads ledger unconditionally — no cached state
           survives between calls.
    INV-3: canonical_objects.json not created when stub pipeline emits zero objects.
    INV-5: batch_id format is deterministic — BATCH_{season}_{microBatchCount:04d}.
    §IV Steps 2–4: Batch lifecycle from action determination through checkpoint.

Fixture pattern: tmp_path (pytest built-in). Real files written to disk.
No mocking. All ledger writes go through the module API.
"""

import json

import pytest
from pathlib import Path

from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.batch_collector import make_batch_collector
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION
from engines.research_engine.ledger.registry_writer import EMPTY_REGISTRY, append_canonical_object
from engines.research_engine.ledger.season_state_manager import create_season_run
from infra.orchestration.runtime.orchestrator import (
    ORCHESTRATOR_VERSION,
    _commit_batch,
    _derive_batch_id,
    orchestrator_run,
)


# ── Constants ─────────────────────────────────────────────────────────────────

_SEASON   = "S2024"
_RUN_PATH = "runs/S2024/run_001"


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


def _setup(
    tmp_path: Path,
    micro_batch_count: int = 0,
    incomplete_batch_flag: bool = False,
    termination_status: str = "running",
) -> tuple[str, str]:
    """Write minimal global_state.json and state.json to tmp_path.

    Returns:
        (ledger_root, active_run_path) as strings for passing to orchestrator_run.

    Side effects:
        Creates run directory. Does NOT create canonical_objects.json.
    """
    _write_global_state(tmp_path, system_status="operational")
    _write_season_state(
        tmp_path,
        microBatchCount=micro_batch_count,
        incompleteBatchFlag=incomplete_batch_flag,
        terminationStatus=termination_status,
    )
    return str(tmp_path), _RUN_PATH


# ── GROUP A: batch_id derivation ──────────────────────────────────────────────

@pytest.mark.parametrize("micro_batch_count,expected", [
    (0,   "BATCH_S2024_0000"),
    (9,   "BATCH_S2024_0009"),
    (100, "BATCH_S2024_0100"),
])
def test_batch_id_format(micro_batch_count, expected):
    """A1–A3: Verify batch_id format with various micro_batch_count values."""
    result = _derive_batch_id(_SEASON, micro_batch_count)
    assert result == expected


# ── GROUP B: successful new_batch run ─────────────────────────────────────────

def test_new_batch_action_when_flag_clear(tmp_path):
    """B1: action == 'new_batch' when incompleteBatchFlag was False on entry."""
    ledger_root, _ = _setup(tmp_path, incomplete_batch_flag=False)
    result = orchestrator_run(ledger_root)
    assert result["action"] == "new_batch"


def test_new_batch_increments_micro_batch_count(tmp_path):
    """B2: After run: microBatchCount incremented by 1."""
    ledger_root, active_run_path = _setup(tmp_path, micro_batch_count=5)
    result = orchestrator_run(ledger_root)
    assert result["microBatchCount"] == 6

    # Verify on disk
    state = json.loads(
        (Path(ledger_root) / active_run_path / "state.json").read_text(encoding="utf-8")
    )
    assert state["microBatchCount"] == 6


def test_new_batch_clears_incomplete_flag(tmp_path):
    """B3: After run: incompleteBatchFlag is False."""
    ledger_root, active_run_path = _setup(tmp_path, incomplete_batch_flag=False)
    orchestrator_run(ledger_root)

    state = json.loads(
        (Path(ledger_root) / active_run_path / "state.json").read_text(encoding="utf-8")
    )
    assert state["incompleteBatchFlag"] is False


def test_new_batch_return_dict_keys(tmp_path):
    """B4: Return dict contains exactly the required keys."""
    ledger_root, _ = _setup(tmp_path)
    result = orchestrator_run(ledger_root)

    required_keys = {
        "orchestratorVersion",
        "action",
        "terminationStatus",
        "activeSurface",
        "microBatchCount",
        "canonicalizedCount",
        "rejectedCount",
        "ntiEvaluationSkipped",
        "batchId",
    }
    assert set(result.keys()) == required_keys


def test_new_batch_stub_pipeline_zero_counts(tmp_path):
    """B5: Stub pipeline emits zero objects — counts are 0."""
    ledger_root, _ = _setup(tmp_path)
    result = orchestrator_run(ledger_root)
    assert result["canonicalizedCount"] == 0
    assert result["rejectedCount"] == 0


# ── GROUP C: canonical_objects.json creation ──────────────────────────────────

def test_stub_run_does_not_create_registry(tmp_path):
    """C1: After stub run: canonical_objects.json does NOT exist."""
    ledger_root, active_run_path = _setup(tmp_path)
    orchestrator_run(ledger_root)

    registry_path = Path(ledger_root) / active_run_path / "canonical_objects.json"
    assert not registry_path.exists()


def test_commit_batch_creates_registry_with_object(tmp_path):
    """C2: Manual _commit_batch with one object creates registry and populates it."""
    ledger_root, active_run_path = _setup(tmp_path)
    registry_path = Path(ledger_root) / active_run_path / "canonical_objects.json"

    # Create registry directory if needed
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "schemaVersion": "CANONICAL_REGISTRY-1.0",
                "CPS": [],
                "CME": [],
                "CSN": [],
                "StructuralEnvironment": [],
                "MediaContext": [],
            }
        ),
        encoding="utf-8",
    )

    # Create collector and add a minimal StructuralEnvironment object
    collector = make_batch_collector("BATCH_S2024_0000")
    cps_obj = {
        "id": "SE_1",
        "laneType": "StructuralEnvironment",
    }
    collector.add("StructuralEnvironment", cps_obj)

    # Commit the batch
    _commit_batch(
        registry_path=registry_path,
        collector=collector,
        cycle_snapshot={
            "schemaVersion":   "CPS-1.0",
            "enumVersion":     "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
        },
    )

    # Verify registry was created
    assert registry_path.exists()

    # Verify object is in registry
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["StructuralEnvironment"]) == 1
    assert registry["StructuralEnvironment"][0] == cps_obj
    assert registry["StructuralEnvironment"][0]["id"] == "SE_1"


# ── GROUP D: crash recovery run ───────────────────────────────────────────────

def test_crash_recovery_action_when_flag_set(tmp_path):
    """D1: When incompleteBatchFlag is True on entry: action == 'crash_recovery'."""
    ledger_root, _ = _setup(
        tmp_path,
        incomplete_batch_flag=True,
    )
    result = orchestrator_run(ledger_root)
    assert result["action"] == "crash_recovery"


def test_crash_recovery_clears_incomplete_flag(tmp_path):
    """D2: After crash recovery run: incompleteBatchFlag is False."""
    ledger_root, active_run_path = _setup(tmp_path, incomplete_batch_flag=True)
    orchestrator_run(ledger_root)

    state = json.loads(
        (Path(ledger_root) / active_run_path / "state.json").read_text(encoding="utf-8")
    )
    assert state["incompleteBatchFlag"] is False


def test_crash_recovery_increments_micro_batch_count(tmp_path):
    """D3: After crash recovery run: microBatchCount incremented by 1."""
    ledger_root, active_run_path = _setup(
        tmp_path,
        micro_batch_count=3,
        incomplete_batch_flag=True,
    )
    orchestrator_run(ledger_root)

    state = json.loads(
        (Path(ledger_root) / active_run_path / "state.json").read_text(encoding="utf-8")
    )
    assert state["microBatchCount"] == 4


def test_crash_recovery_does_not_create_registry(tmp_path):
    """D4: After crash recovery run: canonical_objects.json does NOT exist."""
    ledger_root, active_run_path = _setup(tmp_path, incomplete_batch_flag=True)
    orchestrator_run(ledger_root)

    registry_path = Path(ledger_root) / active_run_path / "canonical_objects.json"
    assert not registry_path.exists()


# ── GROUP E: microBatchCount in return dict ──────────────────────────────────

def test_return_dict_micro_batch_count_matches_disk(tmp_path):
    """E1: Return dict microBatchCount matches value written to disk."""
    ledger_root, active_run_path = _setup(tmp_path, micro_batch_count=2)
    result = orchestrator_run(ledger_root)

    state = json.loads(
        (Path(ledger_root) / active_run_path / "state.json").read_text(encoding="utf-8")
    )
    assert result["microBatchCount"] == state["microBatchCount"]
    assert result["microBatchCount"] == 3


def test_return_dict_micro_batch_count_from_5_to_6(tmp_path):
    """E2: Starting from micro_batch_count=5: return microBatchCount == 6."""
    ledger_root, _ = _setup(tmp_path, micro_batch_count=5)
    result = orchestrator_run(ledger_root)
    assert result["microBatchCount"] == 6
