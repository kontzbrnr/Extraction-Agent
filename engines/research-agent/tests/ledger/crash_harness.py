"""
tests/ledger/crash_harness.py

Reusable crash injection utilities for ledger write atomicity tests.

Provides two crash injection context managers:

  crash_write_at_byte(n)
    Patches os.write to write exactly n bytes to the file descriptor,
    then raises OSError. The target file is never touched because
    os.replace is never called.

  crash_before_rename()
    Patches os.replace to raise OSError immediately.
    The temp file is fully written and fsynced but never renamed
    into the target path.

Both context managers restore the original OS functions on exit,
whether the block raised or not.

Usage in tests:
    with crash_write_at_byte(1):
        with pytest.raises(OSError):
            atomic_write_json(path, data)
    # target file is now in pre-crash state — assert here

    with crash_before_rename():
        with pytest.raises(OSError):
            atomic_write_json(path, data)
    # target file is now in pre-crash state — assert here
"""

from __future__ import annotations

import os as _os
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def crash_write_at_byte(n: int):
    """Simulate a crash during os.write after exactly `n` bytes are written.

    The patched os.write:
      1. Writes min(n, len(data)) bytes to the real file descriptor.
      2. Raises OSError unconditionally.

    This leaves the temp file with at most `n` bytes of data.
    os.replace is never called — the target file is untouched.

    Args:
        n: Number of bytes to write before crashing. 0 = crash immediately
           before writing any bytes. 1 = write 1 byte then crash.
           len(payload)-1 = write all but last byte then crash.
    """
    _real_write = _os.write

    def _patched_write(fd: int, data: bytes) -> int:
        if n > 0:
            chunk = data[:n]
            _real_write(fd, chunk)
        raise OSError(
            f"[crash_harness] os.write interrupted: {n} bytes written before crash"
        )

    with patch("os.write", side_effect=_patched_write):
        yield


@contextmanager
def crash_before_rename():
    """Simulate a crash immediately before os.replace (atomic rename).

    The temp file is fully written and fsynced. os.replace raises OSError.
    The target file is untouched — the new data is never made visible.

    This is equivalent to a crash at 'byte N' (all bytes written, rename blocked).
    """

    def _patched_replace(src: str, dst: str) -> None:
        raise OSError(
            f"[crash_harness] os.replace interrupted: crash before rename "
            f"({src!r} → {dst!r})"
        )

    with patch("os.replace", side_effect=_patched_replace):
        yield


def payload_size(data: dict) -> int:
    """Return the byte length of the canonical JSON serialization of `data`.

    Matches the serialization used by atomic_write_json exactly:
      json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)
      encoded as UTF-8.

    Use this to compute n for crash_write_at_byte(payload_size(data) - 1).
    """
    import json

    return len(
        json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
    )
