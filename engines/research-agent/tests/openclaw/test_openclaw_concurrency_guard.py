"""
tests/openclaw/test_openclaw_concurrency_guard.py

Tests for openclaw.concurrency_guard.

Groups:
    A — Lock acquisition basics
    B — Concurrency violation detection
    C — Release on exception
    D — Lock file lifecycle
"""

from __future__ import annotations

import fcntl
import os
import threading
from pathlib import Path

import pytest

from infra.orchestration.openclaw.concurrency_guard import (
    LOCK_FILENAME,
    ConcurrencyViolationError,
    acquire_run_lock,
)


# ── Group A — Lock acquisition basics ────────────────────────────────

class TestLockAcquisitionBasics:
    def test_lock_acquired_and_released_clean_run(self, tmp_path):
        """Lock context manager completes without error."""
        with acquire_run_lock(str(tmp_path)):
            pass  # no exception expected

    def test_lock_file_exists_inside_context(self, tmp_path):
        """Lock file is present while the context is held."""
        with acquire_run_lock(str(tmp_path)):
            lock_path = tmp_path / LOCK_FILENAME
            assert lock_path.exists()

    def test_sequential_acquisitions_succeed(self, tmp_path):
        """Two sequential (non-overlapping) lock acquisitions both succeed."""
        with acquire_run_lock(str(tmp_path)):
            pass
        with acquire_run_lock(str(tmp_path)):
            pass


# ── Group B — Concurrency violation detection ─────────────────────────

class TestConcurrencyViolationDetection:
    def test_second_call_raises_concurrency_violation(self, tmp_path):
        """A second acquire_run_lock while first is held raises immediately."""
        lock_path = tmp_path / LOCK_FILENAME

        # Hold an exclusive lock manually to simulate a concurrent process.
        competing_fd = open(lock_path, "w")
        try:
            fcntl.flock(competing_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(ConcurrencyViolationError):
                with acquire_run_lock(str(tmp_path)):
                    pass
        finally:
            fcntl.flock(competing_fd, fcntl.LOCK_UN)
            competing_fd.close()

    def test_concurrency_violation_is_runtime_error(self, tmp_path):
        """ConcurrencyViolationError is a RuntimeError subclass."""
        assert issubclass(ConcurrencyViolationError, RuntimeError)

    def test_violation_error_message_contains_lock_path(self, tmp_path):
        """ConcurrencyViolationError message references the lock file path."""
        lock_path = tmp_path / LOCK_FILENAME
        competing_fd = open(lock_path, "w")
        try:
            fcntl.flock(competing_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(ConcurrencyViolationError, match=str(lock_path)):
                with acquire_run_lock(str(tmp_path)):
                    pass
        finally:
            fcntl.flock(competing_fd, fcntl.LOCK_UN)
            competing_fd.close()

    def test_no_blocking_wait_on_contention(self, tmp_path):
        """Second call returns (raises) immediately — does not block."""
        import time

        lock_path = tmp_path / LOCK_FILENAME
        competing_fd = open(lock_path, "w")
        fcntl.flock(competing_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        start = time.monotonic()
        try:
            with pytest.raises(ConcurrencyViolationError):
                with acquire_run_lock(str(tmp_path)):
                    pass
        finally:
            fcntl.flock(competing_fd, fcntl.LOCK_UN)
            competing_fd.close()

        elapsed = time.monotonic() - start
        # Must return in well under 1 second — non-blocking
        assert elapsed < 1.0


# ── Group C — Release on exception ────────────────────────────────────

class TestReleaseOnException:
    def test_lock_released_after_body_raises(self, tmp_path):
        """Lock is released even when the with-block body raises."""
        with pytest.raises(ValueError):
            with acquire_run_lock(str(tmp_path)):
                raise ValueError("body error")

        # Subsequent acquisition must succeed (lock was released)
        with acquire_run_lock(str(tmp_path)):
            pass

    def test_original_exception_propagates_unmodified(self, tmp_path):
        """Exception from body is not wrapped or suppressed."""
        original = ValueError("original")
        with pytest.raises(ValueError) as exc_info:
            with acquire_run_lock(str(tmp_path)):
                raise original
        assert exc_info.value is original


# ── Group D — Lock file lifecycle ─────────────────────────────────────

class TestLockFileLifecycle:
    def test_lock_file_removed_after_clean_exit(self, tmp_path):
        """Lock file is removed after a clean context exit."""
        with acquire_run_lock(str(tmp_path)):
            pass
        lock_path = tmp_path / LOCK_FILENAME
        assert not lock_path.exists()

    def test_lock_file_removed_after_exception(self, tmp_path):
        """Lock file is removed even when body raises."""
        with pytest.raises(RuntimeError):
            with acquire_run_lock(str(tmp_path)):
                raise RuntimeError("body")
        lock_path = tmp_path / LOCK_FILENAME
        assert not lock_path.exists()

    def test_lock_filename_constant(self):
        """LOCK_FILENAME has expected value."""
        assert LOCK_FILENAME == ".openclaw.lock"
