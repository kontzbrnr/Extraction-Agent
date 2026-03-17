"""
Run-scoped SeasonRunState lifecycle manager.

Governing contract: ORCHESTRATOR-EXECUTION-CONTRACT.md
  Section IV Step 4: microBatchCount increment at end-of-batch boundary.
  Section V:         terminationStatus transitions (sealed / exhausted).
  Section VII:       retryFailureCount → system_failure transition.
  Section VI:        incompleteBatchFlag — crash recovery flag.

I/O layer: delegates all disk reads and writes to
  ledger.global_state_manager.read_season_state / write_season_state,
  which delegate writes to ledger.atomic_write.atomic_write_json.

INV-1 enforcement: every read-modify-write re-reads from disk unconditionally.
No module-level caching. No snapshot reuse across call frames.

terminationStatus irreversibility rule:
  "running" is the initial state only — not a valid transition target.
  Terminal statuses (sealed, exhausted, system_failure) are one-way.
  No transition out of a terminal status is permitted.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from engines.research_engine.ledger.global_state_manager import (
    SEASON_STATE_SCHEMA_VERSION,
    read_season_state,
    write_season_state,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_TERMINATION_STATUSES = frozenset(
    {"running", "sealed", "exhausted", "system_failure"}
)
_TERMINAL_STATUSES = frozenset({"sealed", "exhausted", "system_failure"})
# "running" is the initial state only — never a valid *target* of set_termination_status
_VALID_TRANSITION_TARGETS = frozenset({"sealed", "exhausted", "system_failure"})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SeasonStateError(Exception):
    """Base exception for season state operation errors."""


class SeasonRunExistsError(SeasonStateError):
    """Raised when create_season_run finds state.json already present."""

    def __init__(self, path: str) -> None:
        super().__init__(f"season run state already exists: {path}")
        self.path = path


class InvalidTerminationTransitionError(SeasonStateError):
    """Raised when a terminationStatus transition is not permitted.

    Cases:
      - current status is already terminal (one-way lock)
      - attempted target is 'running' (initial state, not a valid target)
    """

    def __init__(self, current: str, attempted: str) -> None:
        super().__init__(
            f"invalid terminationStatus transition: '{current}' → '{attempted}'"
        )
        self.current = current
        self.attempted = attempted


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _season_state_path(ledger_root: str, active_run_path: str) -> str:
    normalized = active_run_path.rstrip("/").rstrip("\\")
    return os.path.join(ledger_root, normalized, "state.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_season_run(
    ledger_root: str,
    season: str,
    active_run_path: str,
) -> dict:
    """Initialize a new run-scoped state.json for a season.

    Creates the run directory if it does not exist.
    Writes state.json with all required schema fields at initial values.

    Args:
        ledger_root:     Path to ledger root directory.
        season:          Season identifier (e.g. "2024_REG").
        active_run_path: Relative path to the run directory
                         (e.g. "runs/2024_REG"). Must match the value
                         that will be stored in global_state.activeRunPath.

    Returns:
        The initial state dict written to disk.

    Raises:
        SeasonRunExistsError: state.json already exists at the computed path.
        LedgerWriteMismatchError: read-back verification failed.
    """
    path = _season_state_path(ledger_root, active_run_path)

    if os.path.exists(path):
        raise SeasonRunExistsError(path)

    run_dir = os.path.dirname(path)
    os.makedirs(run_dir, exist_ok=True)

    initial_state: dict = {
        "schemaVersion": SEASON_STATE_SCHEMA_VERSION,
        "season": season,
        "terminationStatus": "running",
        "microBatchCount": 0,
        "auditCycleCount": 0,
        "retryFailureCount": 0,
        "incompleteBatchFlag": False,
        "activeBatchId": None,
        "commitState": "idle",
        "subcategoryCounts": {},
        "exhaustionCounters": {},
        "lastUpdated": _now_iso(),
    }

    write_season_state(ledger_root, active_run_path, initial_state)
    return initial_state


def increment_micro_batch_count(ledger_root: str, active_run_path: str) -> int:
    """Increment microBatchCount by 1 via read-modify-write.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV Step 4:
    "Increment microBatchCount" at end-of-batch boundary.

    Reads from disk unconditionally on every call (INV-1).

    Returns:
        The new microBatchCount value after increment.

    Raises:
        SeasonStateReadError:      state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError:  read-back verification failed.
    """
    state = read_season_state(ledger_root, active_run_path)
    state["microBatchCount"] = state["microBatchCount"] + 1
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)
    return state["microBatchCount"]


def set_termination_status(
    ledger_root: str,
    active_run_path: str,
    status: str,
) -> None:
    """Transition terminationStatus to a terminal value.

    Valid targets: "sealed", "exhausted", "system_failure".
    "running" is NOT a valid target (initial state only — irreversible rule).

    Reads from disk unconditionally before mutating (INV-1).

    Raises:
        SeasonStateError:                   status is not a recognized enum value.
        InvalidTerminationTransitionError:  target is "running", or current status
                                            is already terminal.
        SeasonStateReadError:               state.json unreadable.
        LedgerWriteMismatchError:           read-back verification failed.
    """
    if status not in _VALID_TERMINATION_STATUSES:
        raise SeasonStateError(
            f"unrecognized terminationStatus value: '{status}'. "
            f"Valid values: {sorted(_VALID_TERMINATION_STATUSES)}"
        )

    if status not in _VALID_TRANSITION_TARGETS:
        raise InvalidTerminationTransitionError(current="(any)", attempted=status)

    state = read_season_state(ledger_root, active_run_path)
    current = state["terminationStatus"]

    if current in _TERMINAL_STATUSES:
        raise InvalidTerminationTransitionError(current=current, attempted=status)

    state["terminationStatus"] = status
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)


# ---------------------------------------------------------------------------
# Phase 1.5 — Incomplete Batch Flag System
# ---------------------------------------------------------------------------


class BatchAlreadyInProgressError(SeasonStateError):
    """Raised when mark_batch_start is called while incompleteBatchFlag is True.

    Indicates crash recovery was not performed before starting a new batch.
    The caller must call clear_incomplete_batch_flag first.
    """

    def __init__(self, current_batch_id: str) -> None:
        super().__init__(
            f"incompleteBatchFlag is already True; "
            f"active batch: '{current_batch_id}'. "
            f"Run crash recovery (clear_incomplete_batch_flag) before starting a new batch."
        )
        self.current_batch_id = current_batch_id


def mark_batch_start(
    ledger_root: str,
    active_run_path: str,
    batch_id: str,
) -> None:
    """Set incompleteBatchFlag=True and activeBatchId=batch_id at micro-batch start.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV:
    The flag must be written BEFORE any cluster processing begins so that a
    crash mid-batch is detectable on the next invocation.

    Reads from disk unconditionally (INV-1) before mutating.

    Args:
        ledger_root:     Path to ledger root directory.
        active_run_path: Relative path to the active run directory.
        batch_id:        Batch identifier to record. Format per schema comment:
                         BATCH_{season}_{microBatchCount:04d}.
                         Must be non-empty.

    Raises:
        ValueError:                  batch_id is empty.
        BatchAlreadyInProgressError: incompleteBatchFlag is already True on disk.
        SeasonStateReadError:        state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError:    read-back verification failed.
    """
    if not batch_id:
        raise ValueError("batch_id must be a non-empty string")

    state = read_season_state(ledger_root, active_run_path)

    if state["incompleteBatchFlag"] is True:
        raise BatchAlreadyInProgressError(
            current_batch_id=state.get("activeBatchId") or "(unknown)"
        )

    state["incompleteBatchFlag"] = True
    state["activeBatchId"] = batch_id
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)


def clear_incomplete_batch_flag(
    ledger_root: str,
    active_run_path: str,
) -> None:
    """Clear incompleteBatchFlag and activeBatchId after successful commit or crash recovery.

    Idempotent — safe to call when flag is already False.

    Used in two contexts per ORCHESTRATOR-EXECUTION-CONTRACT.md:
      1. Successful checkpoint (Section IV Step 4): after all clusters processed
         and SeasonRunState fully persisted.
      2. Crash recovery (Section VI): discard incomplete batch, reset flag
         before initiating a new micro-batch.

    Reads from disk unconditionally (INV-1) before mutating.

    Raises:
        SeasonStateReadError:      state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError:  read-back verification failed.
    """
    state = read_season_state(ledger_root, active_run_path)

    # Idempotent: if already clear, write is still performed to update lastUpdated
    # but only if a change is needed — avoid spurious writes
    if state["incompleteBatchFlag"] is False and state["activeBatchId"] is None:
        return

    state["incompleteBatchFlag"] = False
    state["activeBatchId"] = None
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)


def increment_audit_cycle_count(ledger_root: str, active_run_path: str) -> int:
    """Increment auditCycleCount by 1 via read-modify-write.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV Step 4:
    "If audit interval reached → increment auditCycleCount."

    Reads from disk unconditionally on every call (INV-1).

    Returns:
        The new auditCycleCount value after increment.

    Raises:
        SeasonStateReadError:     state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError: read-back verification failed.
    """
    state = read_season_state(ledger_root, active_run_path)
    state["auditCycleCount"] = state["auditCycleCount"] + 1
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)
    return state["auditCycleCount"]


def update_subcategory_counts(
    ledger_root: str,
    active_run_path: str,
    delta: dict,
) -> None:
    """Merge delta into season_state.subcategoryCounts by addition.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV Step 4:
    "Update subcategoryCounts" at end-of-batch boundary.

    delta keys are surface names. Each key's integer value is ADDED to
    the existing count for that surface. Keys absent from existing state
    are treated as 0 (new surface coverage begins at delta value).
    Empty delta causes no disk write.

    Contract distinction (cycle_state_manager.py):
        season_state.subcategoryCounts — orchestrator end-of-batch coverage
        tracking (this function).
        nti_state.exhaustionCounters   — NTI-audit-level structural saturation
        detection (separate module).

    Reads from disk unconditionally before writing (INV-1).

    Args:
        delta: Dict mapping surface name → integer coverage increment for
               this batch. May be empty. Values must be non-negative integers.
               Not validated against SURFACE_ROTATION_ORDER — caller
               responsibility.

    Raises:
        SeasonStateReadError:     state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError: read-back verification failed.
    """
    if not delta:
        return  # No-op — avoid spurious writes.

    state = read_season_state(ledger_root, active_run_path)
    existing: dict = state.get("subcategoryCounts") or {}
    merged: dict = dict(existing)
    for surface, count in delta.items():
        merged[surface] = merged.get(surface, 0) + count
    state["subcategoryCounts"] = merged
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)


def update_exhaustion_counters(
    ledger_root: str,
    active_run_path: str,
    delta: dict,
) -> None:
    """Merge delta into season_state.exhaustionCounters by addition.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV Step 4:
    "Update exhaustion counters" at end-of-batch boundary.

    Contract distinction:
        season_state.exhaustionCounters — orchestrator end-of-batch
        tracking. Updated here from NTI audit output.
        nti_state.exhaustionCounters    — NTI-audit-level detection
        events. Written by nti.cycle_state_manager.
        These are SEPARATE fields in SEPARATE files.

    Same merge-by-addition semantics as update_subcategory_counts.
    Empty delta causes no disk write.

    Reads from disk unconditionally before writing (INV-1).

    Raises:
        SeasonStateReadError:     state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError: read-back verification failed.
    """
    if not delta:
        return  # No-op — avoid spurious writes.

    state = read_season_state(ledger_root, active_run_path)
    existing: dict = state.get("exhaustionCounters") or {}
    merged: dict = dict(existing)
    for surface, count in delta.items():
        merged[surface] = merged.get(surface, 0) + count
    state["exhaustionCounters"] = merged
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)


def increment_retry_failure_count(ledger_root: str, active_run_path: str) -> int:
    """Increment retryFailureCount by 1 via read-modify-write.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section VII (Retry Envelope):
    "If second failure: Increment retryFailureCount. If retryFailureCount >= 2
    → terminationStatus = 'system_failure' → Persist state → Exit."

    Called by the orchestrator crash recovery hook (Phase 13.7) immediately
    after handle_crash_recovery detects an incomplete batch flag.

    Reads from disk unconditionally on every call (INV-1).

    Returns:
        The new retryFailureCount value after increment.

    Raises:
        SeasonStateReadError:     state.json unreadable or wrong schemaVersion.
        LedgerWriteMismatchError: read-back verification failed.
    """
    state = read_season_state(ledger_root, active_run_path)
    state["retryFailureCount"] = state["retryFailureCount"] + 1
    state["lastUpdated"] = _now_iso()
    write_season_state(ledger_root, active_run_path, state)
    return state["retryFailureCount"]
