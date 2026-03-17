"""
ledger/rollback_handler.py

Crash recovery handler for incomplete micro-batch detection.

Governing contract: ORCHESTRATOR-EXECUTION-CONTRACT.md Section VI:
  "If crash occurs mid-micro-batch:
   Upon next invocation:
     Detect incomplete batch flag
     Discard entire batch
     Do NOT mutate canonical registry
     Resume by initiating new micro-batch
   No partial resume. No cluster-level resume. No seed-level resume."

INV-3 enforcement: canonical_objects.json is NEVER opened, read, or written
by this module under any circumstances.

INV-1 enforcement: state.json is read from disk unconditionally on every call.
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.research_engine.ledger.global_state_manager import (
    read_season_state,
    write_season_state,
    SeasonStateReadError,
)
from engines.research_engine.ledger.season_state_manager import _now_iso


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CrashRecoveryResult:
    """Outcome of a handle_crash_recovery call.

    Attributes:
        rollback_performed:  True if incompleteBatchFlag was True and reset was
                             performed. False if no crash was detected (no-op).
        recovered_batch_id:  The activeBatchId value that was cleared.
                             None if no rollback was performed.
    """

    rollback_performed: bool
    recovered_batch_id: str | None


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

# Fields reset to their idle values during crash recovery.
# Only these fields are mutated — all others are preserved exactly.
_CRASH_RESET_FIELDS: dict = {
    "incompleteBatchFlag": False,
    "activeBatchId": None,
    "commitState": "idle",
}


def handle_crash_recovery(
    ledger_root: str,
    active_run_path: str,
) -> CrashRecoveryResult:
    """Detect and recover from a crashed micro-batch invocation.

    Reads season state from disk unconditionally (INV-1).

    If incompleteBatchFlag is False:
        No crash detected. Returns CrashRecoveryResult(rollback_performed=False).
        Zero disk mutations.

    If incompleteBatchFlag is True:
        Crash detected. Resets incompleteBatchFlag, activeBatchId, and commitState
        to their idle values in a single atomic write. Returns
        CrashRecoveryResult(rollback_performed=True, recovered_batch_id=<id>).

    GUARANTEE (INV-3): canonical_objects.json is never opened, read, or written
    by this function. Canonical objects committed before the crash are valid
    minted objects and remain untouched in the registry.

    Args:
        ledger_root:     Path to ledger root directory.
        active_run_path: Relative path to the active run directory.

    Returns:
        CrashRecoveryResult describing whether a rollback was performed.

    Raises:
        SeasonStateReadError:      state.json missing or wrong schemaVersion.
        LedgerWriteMismatchError:  read-back verification failed after reset write.
    """
    state = read_season_state(ledger_root, active_run_path)

    if not state["incompleteBatchFlag"]:
        # No crash detected — do not mutate disk.
        return CrashRecoveryResult(rollback_performed=False, recovered_batch_id=None)

    # Capture the batch id that was in progress before clearing it.
    recovered_batch_id: str | None = state.get("activeBatchId")

    # Reset only the crash-dirty fields. All other fields are preserved.
    for field, idle_value in _CRASH_RESET_FIELDS.items():
        state[field] = idle_value
    state["lastUpdated"] = _now_iso()

    # Single atomic write — canonical_objects.json is never touched.
    write_season_state(ledger_root, active_run_path, state)

    return CrashRecoveryResult(
        rollback_performed=True,
        recovered_batch_id=recovered_batch_id,
    )
