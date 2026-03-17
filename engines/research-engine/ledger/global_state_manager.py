"""
Read-before-every-action enforcement wrapper for orchestrator state.

Governing contract: ORCHESTRATOR-EXECUTION-CONTRACT.md
  Section II: "Before every action: Read GlobalState, Read SeasonRunState.
               Never trust prior invocation memory."
  Section IV Step 1: Preflight read protocol.
  Section IX: Ledger structure — global_state.json at root,
              season state at runs/{season}/state.json.

No caching. Every read function issues a disk read unconditionally.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from engines.research_engine.ledger.atomic_write import atomic_write_json

GLOBAL_STATE_SCHEMA_VERSION = "GLOBAL_STATE-1.0"
SEASON_STATE_SCHEMA_VERSION = "SEASON_STATE-1.0"

_TERMINAL_STATUSES = frozenset({"sealed", "exhausted", "system_failure"})


class GlobalStateReadError(Exception):
    """Raised when global_state.json is missing or fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.path = path


class SeasonStateReadError(Exception):
    """Raised when season state.json is missing or fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.path = path


class PreflightError(Exception):
    """Raised when preflight guard conditions are not met.

    reason_code values:
      SYSTEM_HALTED       — global_state.systemStatus == "halted"
      TERMINATION_BLOCKED — season_state.terminationStatus != "running"
    """

    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class LedgerState:
    """Immutable snapshot of both state files as read from disk.

    Returned by preflight_read() only when all preflight checks pass.
    Callers must not cache this object across invocations.
    """

    global_state: dict
    season_state: dict


def _global_state_path(ledger_root: str) -> str:
    return os.path.join(ledger_root, "global_state.json")


def _season_state_path(ledger_root: str, active_run_path: str) -> str:
    # active_run_path may have trailing slash, e.g. "runs/2024_OFFSEASON/"
    # strip it to normalize, then append /state.json
    normalized = active_run_path.rstrip("/").rstrip("\\")
    return os.path.join(ledger_root, normalized, "state.json")


def read_global_state(ledger_root: str) -> dict:
    """Read global_state.json from disk. No caching.

    Raises:
        GlobalStateReadError: file missing, JSON invalid, or wrong schemaVersion.
    """
    path = _global_state_path(ledger_root)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise GlobalStateReadError(
            f"global_state.json not found at: {path}", path=path
        ) from exc
    except json.JSONDecodeError as exc:
        raise GlobalStateReadError(
            f"global_state.json is not valid JSON: {exc}", path=path
        ) from exc

    actual = data.get("schemaVersion")
    if actual != GLOBAL_STATE_SCHEMA_VERSION:
        raise GlobalStateReadError(
            f"schemaVersion mismatch: expected '{GLOBAL_STATE_SCHEMA_VERSION}', "
            f"got '{actual}'",
            path=path,
        )

    return data


def read_season_state(ledger_root: str, active_run_path: str) -> dict:
    """Read season state.json from disk. No caching.

    Args:
        ledger_root:     Path to ledger root directory.
        active_run_path: Value of activeRunPath from global_state (e.g. "runs/2024_REG/").

    Raises:
        SeasonStateReadError: file missing, JSON invalid, or wrong schemaVersion.
    """
    path = _season_state_path(ledger_root, active_run_path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise SeasonStateReadError(
            f"season state.json not found at: {path}", path=path
        ) from exc
    except json.JSONDecodeError as exc:
        raise SeasonStateReadError(
            f"season state.json is not valid JSON: {exc}", path=path
        ) from exc

    actual = data.get("schemaVersion")
    if actual != SEASON_STATE_SCHEMA_VERSION:
        raise SeasonStateReadError(
            f"schemaVersion mismatch: expected '{SEASON_STATE_SCHEMA_VERSION}', "
            f"got '{actual}'",
            path=path,
        )

    return data


def preflight_read(ledger_root: str) -> LedgerState:
    """Perform the orchestrator preflight protocol.

    Implements ORCHESTRATOR-EXECUTION-CONTRACT.md Section IV Step 1:
      1. Load GlobalState
      2. Load SeasonRunState (via activeRunPath from GlobalState)
      3. Confirm systemStatus == "operational"   → raise PreflightError(SYSTEM_HALTED)
      4. Confirm terminationStatus == "running"  → raise PreflightError(TERMINATION_BLOCKED)

    Returns:
        LedgerState with both dicts when all checks pass.

    Raises:
        GlobalStateReadError:  global_state.json unreadable.
        SeasonStateReadError:  season state.json unreadable.
        PreflightError:        systemStatus or terminationStatus check fails.
    """
    global_state = read_global_state(ledger_root)

    system_status = global_state.get("systemStatus")
    if system_status == "halted":
        raise PreflightError(
            "SYSTEM_HALTED",
            detail="global_state.systemStatus is 'halted'",
        )

    active_run_path = global_state["activeRunPath"]
    season_state = read_season_state(ledger_root, active_run_path)

    termination_status = season_state.get("terminationStatus")
    if termination_status != "running":
        raise PreflightError(
            "TERMINATION_BLOCKED",
            detail=f"terminationStatus is '{termination_status}', expected 'running'",
        )

    return LedgerState(global_state=global_state, season_state=season_state)


def write_global_state(ledger_root: str, state: dict) -> None:
    """Write global_state.json atomically.

    Validates schemaVersion before writing.

    Raises:
        GlobalStateReadError:      wrong schemaVersion in state dict.
        LedgerWriteMismatchError:  read-back verification failed (from atomic_write_json).
    """
    actual = state.get("schemaVersion")
    if actual != GLOBAL_STATE_SCHEMA_VERSION:
        raise GlobalStateReadError(
            f"Cannot write: schemaVersion must be '{GLOBAL_STATE_SCHEMA_VERSION}', "
            f"got '{actual}'"
        )
    path = _global_state_path(ledger_root)
    atomic_write_json(path, state)


def write_season_state(ledger_root: str, active_run_path: str, state: dict) -> None:
    """Write season state.json atomically.

    Validates schemaVersion before writing.

    Raises:
        SeasonStateReadError:      wrong schemaVersion in state dict.
        LedgerWriteMismatchError:  read-back verification failed (from atomic_write_json).
    """
    actual = state.get("schemaVersion")
    if actual != SEASON_STATE_SCHEMA_VERSION:
        raise SeasonStateReadError(
            f"Cannot write: schemaVersion must be '{SEASON_STATE_SCHEMA_VERSION}', "
            f"got '{actual}'"
        )
    path = _season_state_path(ledger_root, active_run_path)
    atomic_write_json(path, state)
