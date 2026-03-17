"""
openclaw/concurrency_guard.py

File-lock-based concurrency guard for the OpenClaw runtime.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md §VI

Single-writer enforcement: at most one OpenClaw invocation may hold
the orchestrator call at a time. Implemented via an exclusive,
non-blocking fcntl file lock at {ledger_root}/.openclaw.lock.

On POSIX systems the OS releases held locks unconditionally on process
exit, so a crashed process never deadlocks future runs.
"""

from __future__ import annotations

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

LOCK_FILENAME = ".openclaw.lock"


class ConcurrencyViolationError(RuntimeError):
    """Raised when a concurrent OpenClaw invocation is detected.

    Indicates that another process currently holds the exclusive run
    lock for the same ledger_root. The caller must not retry
    automatically — an external scheduler controls invocation cadence.
    """


@contextmanager
def acquire_run_lock(ledger_root: str):
    """Acquire an exclusive file lock for one orchestrator invocation.

    Opens (or creates) {ledger_root}/.openclaw.lock and acquires an
    exclusive, non-blocking lock via fcntl.LOCK_EX | fcntl.LOCK_NB.

    Raises ConcurrencyViolationError immediately if the lock is held.
    Releases the lock (and attempts to remove the lock file) on exit,
    whether the body returns normally or raises.

    Args:
        ledger_root: Absolute path to the ledger root directory. Must
                     exist — assert_ledger_reachable is expected to
                     have verified this before acquire_run_lock is
                     called.

    Raises:
        ConcurrencyViolationError: Another OpenClaw process holds the
            lock. Raised immediately — no blocking wait.
        OSError: Lock file cannot be opened or created (permissions,
            disk full, etc.). Propagates unmodified.

    Yields:
        Nothing. The lock is held for the duration of the with-block.
    """
    lock_path = Path(ledger_root) / LOCK_FILENAME
    lock_fd = open(lock_path, "w")  # noqa: WPS515  (open without context mgr intentional)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_fd.close()
            raise ConcurrencyViolationError(
                f"Another OpenClaw invocation is already running. "
                f"Lock file: {lock_path}"
            )
        try:
            yield
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
    finally:
        lock_fd.close()
        # Best-effort removal. Stale file is harmless on next run
        # (open + LOCK_EX succeeds). Never suppress the original exc.
        try:
            os.unlink(lock_path)
        except OSError:
            pass
