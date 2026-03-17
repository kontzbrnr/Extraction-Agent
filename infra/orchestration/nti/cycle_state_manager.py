"""
nti/cycle_state_manager.py

Per-season-run NTI cycle state manager.

Governing behaviour contracts:
  NTI-CYCLE-EXECUTION.md:
    Section III:  Time Surface is a coverage categorization dimension.
    Section VII:  Sealed surfaces are removed from future extraction rotation.
    Section VIII: Exhaustion guard operates on structural distinctness.
  TIME-RECURRENCE-PARTITION-DOCTRINE.md:
    "Cycle metadata SHALL NEVER participate in canonical identity in any lane."

Schema authority:
  schemas/ledger/nti_cycle_state.schema.json — NTI_CYCLE_STATE-1.0.
  Authored for Phase 2.5 to fill documented gap (no contract formally defines
  these fields). Design decisions are explicit in the schema file.

Storage:
  {ledger_root}/{active_run_path}/nti_state.json
  Parallel to state.json in the active run directory.
  Per-season-run scoped — reset on new run creation.

Distinction from season_state.exhaustionCounters:
  season_state.exhaustionCounters: orchestrator end-of-batch tracking.
  This module's exhaustionCounters: NTI-audit-level tracking, incremented
  on NTI exhaustion detection events (novelty collapse, subcategory
  stagnation, duplication saturation per Section VIII).

INV-1 enforcement:
  All read operations re-read from disk unconditionally. No caching.

I/O:
  All writes delegate to ledger.atomic_write.atomic_write_json.
  No direct file I/O in this module.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from engines.research_engine.ledger.atomic_write import atomic_write_json
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER, _SURFACE_SET

NTI_CYCLE_STATE_SCHEMA_VERSION = "NTI_CYCLE_STATE-1.0"

# All 8 surfaces must be present in both status dicts.
_ALL_SURFACES: tuple[str, ...] = SURFACE_ROTATION_ORDER


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class NTIStateError(Exception):
    """Base exception for NTI cycle state operation errors."""


class NTIStateExistsError(NTIStateError):
    """Raised when create_nti_state finds nti_state.json already present."""

    def __init__(self, path: str) -> None:
        super().__init__(f"NTI cycle state already exists: {path}")
        self.path = path


class NTIStateReadError(NTIStateError):
    """Raised when nti_state.json is missing or fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.path = path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _nti_state_path(ledger_root: str, active_run_path: str) -> str:
    normalized = active_run_path.rstrip("/").rstrip("\\")
    return os.path.join(ledger_root, normalized, "nti_state.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_surface(surface: str) -> None:
    if surface not in _SURFACE_SET:
        raise NTIStateError(
            f"unknown surface: '{surface}'. "
            f"Valid surfaces: {list(_ALL_SURFACES)}"
        )


def _initial_state() -> dict:
    return {
        "schemaVersion": NTI_CYCLE_STATE_SCHEMA_VERSION,
        "currentSurface": None,
        "surfaceSealStatus": {s: False for s in _ALL_SURFACES},
        "exhaustionCounters": {s: 0 for s in _ALL_SURFACES},
        "lastUpdated": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------


def read_nti_state(ledger_root: str, active_run_path: str) -> dict:
    """Read nti_state.json from disk. No caching (INV-1).

    Raises:
        NTIStateReadError: file missing, invalid JSON, or wrong schemaVersion.
    """
    path = _nti_state_path(ledger_root, active_run_path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise NTIStateReadError(
            f"nti_state.json not found: {path}", path=path
        )
    except json.JSONDecodeError as exc:
        raise NTIStateReadError(
            f"nti_state.json is not valid JSON: {exc}", path=path
        )

    actual = data.get("schemaVersion")
    if actual != NTI_CYCLE_STATE_SCHEMA_VERSION:
        raise NTIStateReadError(
            f"schemaVersion mismatch: expected '{NTI_CYCLE_STATE_SCHEMA_VERSION}', "
            f"got '{actual}'",
            path=path,
        )

    return data


def write_nti_state(ledger_root: str, active_run_path: str, state: dict) -> None:
    """Write nti_state.json atomically.

    Validates schemaVersion before writing.

    Raises:
        NTIStateReadError:         wrong schemaVersion in state dict.
        LedgerWriteMismatchError:  read-back verification failed.
    """
    actual = state.get("schemaVersion")
    if actual != NTI_CYCLE_STATE_SCHEMA_VERSION:
        raise NTIStateReadError(
            f"Cannot write: schemaVersion must be '{NTI_CYCLE_STATE_SCHEMA_VERSION}', "
            f"got '{actual}'"
        )
    path = _nti_state_path(ledger_root, active_run_path)
    atomic_write_json(path, state)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def create_nti_state(ledger_root: str, active_run_path: str) -> dict:
    """Initialise nti_state.json for a new season run.

    Creates the file with all surfaces set to active (false) and all
    exhaustion counters at 0. currentSurface is null until first assignment.

    Raises:
        NTIStateExistsError:       nti_state.json already exists.
        LedgerWriteMismatchError:  atomic write read-back failed.
    """
    path = _nti_state_path(ledger_root, active_run_path)

    if os.path.exists(path):
        raise NTIStateExistsError(path)

    initial = _initial_state()
    atomic_write_json(path, initial)
    return initial


# ---------------------------------------------------------------------------
# Surface state operations
# ---------------------------------------------------------------------------


def set_current_surface(
    ledger_root: str,
    active_run_path: str,
    surface: str,
) -> None:
    """Set currentSurface to the given surface name.

    Reads from disk unconditionally (INV-1). Validates surface against
    SURFACE_ROTATION_ORDER before any disk read.

    Raises:
        NTIStateError:             surface is not a valid surface name.
        NTIStateReadError:         nti_state.json unreadable.
        LedgerWriteMismatchError:  atomic write read-back failed.
    """
    _validate_surface(surface)

    state = read_nti_state(ledger_root, active_run_path)
    state["currentSurface"] = surface
    state["lastUpdated"] = _now_iso()
    write_nti_state(ledger_root, active_run_path, state)


def seal_surface(
    ledger_root: str,
    active_run_path: str,
    surface: str,
) -> None:
    """Mark a surface as sealed in surfaceSealStatus.

    Idempotent — sealing an already-sealed surface is a no-op (no disk write).
    Per NTI-CYCLE-EXECUTION.md Section VII: sealed surfaces are removed from
    future extraction rotation.

    Validates surface before any disk read.

    Raises:
        NTIStateError:             surface is not a valid surface name.
        NTIStateReadError:         nti_state.json unreadable.
        LedgerWriteMismatchError:  atomic write read-back failed.
    """
    _validate_surface(surface)

    state = read_nti_state(ledger_root, active_run_path)

    if state["surfaceSealStatus"][surface] is True:
        return  # Already sealed — idempotent, no write.

    state["surfaceSealStatus"][surface] = True
    state["lastUpdated"] = _now_iso()
    write_nti_state(ledger_root, active_run_path, state)


def get_sealed_surfaces(
    ledger_root: str,
    active_run_path: str,
) -> frozenset[str]:
    """Return a frozenset of all currently sealed surface names.

    Reads from disk unconditionally (INV-1).

    Raises:
        NTIStateReadError: nti_state.json unreadable.
    """
    state = read_nti_state(ledger_root, active_run_path)
    return frozenset(
        surface
        for surface, sealed in state["surfaceSealStatus"].items()
        if sealed is True
    )


# ---------------------------------------------------------------------------
# Exhaustion counter operations
# ---------------------------------------------------------------------------


def increment_exhaustion_counter(
    ledger_root: str,
    active_run_path: str,
    surface: str,
) -> int:
    """Increment the NTI exhaustion counter for a surface by 1.

    Reads from disk unconditionally (INV-1). Validates surface before read.

    Per NTI-CYCLE-EXECUTION.md Section VIII: exhaustion operates on
    structural distinctness (novelty collapse, subcategory stagnation,
    duplication saturation). This counter is incremented by NTI audit logic
    on detection events — distinct from season_state.exhaustionCounters
    (orchestrator end-of-batch tracking).

    Returns:
        The new counter value after increment.

    Raises:
        NTIStateError:             surface is not a valid surface name.
        NTIStateReadError:         nti_state.json unreadable.
        LedgerWriteMismatchError:  atomic write read-back failed.
    """
    _validate_surface(surface)

    state = read_nti_state(ledger_root, active_run_path)
    state["exhaustionCounters"][surface] += 1
    state["lastUpdated"] = _now_iso()
    write_nti_state(ledger_root, active_run_path, state)
    return state["exhaustionCounters"][surface]


def get_exhaustion_counter(
    ledger_root: str,
    active_run_path: str,
    surface: str,
) -> int:
    """Return the current exhaustion counter value for a surface.

    Reads from disk unconditionally (INV-1). Validates surface before read.

    Raises:
        NTIStateError:    surface is not a valid surface name.
        NTIStateReadError: nti_state.json unreadable.
    """
    _validate_surface(surface)
    state = read_nti_state(ledger_root, active_run_path)
    return state["exhaustionCounters"][surface]
