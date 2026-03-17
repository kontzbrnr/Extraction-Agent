"""
tests/ledger/test_batch_collector.py

Unit and integration tests for ledger/batch_collector.py.

Test coverage:
  1. Factory pattern — new instances always created
  2. Lane creation on first access
  3. Per-lane object order preservation
  4. Lane isolation (no cross-contamination)
  5. sorted_lanes() key ordering (INV-5)
  6. Integration with mark_batch_start flag
  7. Crash recovery (BatchAlreadyInProgressError on duplicate flag)
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from engines.research_engine.ledger.batch_collector import BatchCollector, make_batch_collector
from engines.research_engine.ledger.global_state_manager import read_season_state
from engines.research_engine.ledger.season_state_manager import (
    mark_batch_start,
    BatchAlreadyInProgressError,
    create_season_run,
)


# ---------------------------------------------------------------------------
# Unit Tests: Factory and Collector Behavior
# ---------------------------------------------------------------------------


def test_make_batch_collector_returns_new_instance() -> None:
    """Each call to make_batch_collector() returns a distinct instance."""
    collector_1 = make_batch_collector("B1")
    collector_2 = make_batch_collector("B1")

    assert collector_1 is not collector_2
    assert collector_1.batch_id == collector_2.batch_id == "B1"


def test_add_creates_lane_on_first_access() -> None:
    """First add() to a new lane creates the lane list."""
    collector = make_batch_collector("BATCH_2024_REG_0001")
    obj = {"test": "object"}

    collector.add("CPS", obj)

    assert "CPS" in collector.lanes
    assert collector.lanes["CPS"] == [obj]


def test_add_appends_in_order() -> None:
    """Multiple add() calls to the same lane preserve order."""
    collector = make_batch_collector("BATCH_2024_REG_0001")
    obj1 = {"id": 1}
    obj2 = {"id": 2}

    collector.add("CPS", obj1)
    collector.add("CPS", obj2)

    assert collector.lanes["CPS"] == [obj1, obj2]


def test_add_isolates_lanes() -> None:
    """add() to different lanes does not cross-contaminate."""
    collector = make_batch_collector("BATCH_2024_REG_0001")
    obj_cps = {"lane": "CPS"}
    obj_csn = {"lane": "CSN"}

    collector.add("CPS", obj_cps)
    collector.add("CSN", obj_csn)

    assert collector.lanes["CPS"] == [obj_cps]
    assert collector.lanes["CSN"] == [obj_csn]


def test_sorted_lanes_key_order() -> None:
    """sorted_lanes() returns dict with keys in sorted (ascending) order."""
    collector = make_batch_collector("BATCH_2024_REG_0001")
    obj_csn = {"lane": "CSN"}
    obj_cps = {"lane": "CPS"}
    obj_cme = {"lane": "CME"}

    # Add in non-alphabetical order
    collector.add("CSN", obj_csn)
    collector.add("CPS", obj_cps)
    collector.add("CME", obj_cme)

    sorted_result = collector.sorted_lanes()
    actual_keys = list(sorted_result.keys())

    assert actual_keys == ["CME", "CPS", "CSN"]


def test_sorted_lanes_preserves_per_lane_order() -> None:
    """sorted_lanes() preserves order within each lane."""
    collector = make_batch_collector("BATCH_2024_REG_0001")
    obj1 = {"id": 1}
    obj2 = {"id": 2}
    obj3 = {"id": 3}

    collector.add("CPS", obj1)
    collector.add("CPS", obj2)
    collector.add("CSN", obj3)

    sorted_result = collector.sorted_lanes()

    # Lane order should be sorted, but within each lane, insertion order preserved
    assert sorted_result["CPS"] == [obj1, obj2]
    assert sorted_result["CSN"] == [obj3]


# ---------------------------------------------------------------------------
# Integration Tests: Batch Start Flag and Crash Recovery
# ---------------------------------------------------------------------------


def test_mark_batch_start_sets_flag(tmp_path: Path) -> None:
    """mark_batch_start() sets incompleteBatchFlag and activeBatchId."""
    RUN_PATH = "runs/2024/REG"
    BATCH_ID = "BATCH_2024_REG_0001"

    # Initialize state
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)

    # Mark batch start
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)

    # Read and verify
    state = read_season_state(str(tmp_path), RUN_PATH)
    assert state["incompleteBatchFlag"] is True
    assert state["activeBatchId"] == BATCH_ID


def test_mark_batch_start_raises_on_duplicate(tmp_path: Path) -> None:
    """Calling mark_batch_start() twice raises BatchAlreadyInProgressError."""
    RUN_PATH = "runs/2024/REG"
    BATCH_ID = "BATCH_2024_REG_0001"

    # Initialize state
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)

    # First call succeeds
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)

    # Second call should raise
    with pytest.raises(BatchAlreadyInProgressError) as exc_info:
        mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)

    assert BATCH_ID in str(exc_info.value)


def test_collector_with_batch_start_integration(tmp_path: Path) -> None:
    """Collector instance independent of batch start flag lifecycle."""
    RUN_PATH = "runs/2024/REG"
    BATCH_ID = "BATCH_2024_REG_0001"

    # Initialize state
    create_season_run(str(tmp_path), "2024_REG", RUN_PATH)

    # Mark batch start (sets flag)
    mark_batch_start(str(tmp_path), RUN_PATH, BATCH_ID)

    # Create collector (in-memory, independent of flag)
    collector = make_batch_collector(BATCH_ID)
    collector.add("CPS", {"test": "object"})

    # Collector state is independent
    assert collector.batch_id == BATCH_ID
    assert len(collector.lanes["CPS"]) == 1

    # Flag remains set in ledger
    state = read_season_state(str(tmp_path), RUN_PATH)
    assert state["incompleteBatchFlag"] is True
