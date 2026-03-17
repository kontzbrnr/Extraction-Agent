"""
Atomic Write Primitive — LedgerWriter core.

Contract: ORCHESTRATOR-EXECUTION-CONTRACT.md Section IX
  "All writes must be: Atomic, Synchronous, Immediately persisted, Verified by read-back."

Guarantee: A reader of `path` will see either the complete previous content
or the complete new content — never a partial write.

Pattern: write to .tmp → fsync → os.replace (atomic rename) → read-back verify
"""

import json
import os
from pathlib import Path


class LedgerWriteMismatchError(Exception):
    """
    Raised when the read-back buffer after an atomic write does not match
    the buffer that was written. Indicates filesystem or serialization corruption.
    Never silently swallowed.
    """
    def __init__(self, path: str, written: bytes, read_back: bytes):
        self.path = path
        self.written = written
        self.read_back = read_back
        super().__init__(
            f"Ledger write mismatch at '{path}': "
            f"written {len(written)} bytes, read back {len(read_back)} bytes. "
            f"Written hash: {hash(written)}, Read-back hash: {hash(read_back)}"
        )


def atomic_write_json(path, data: dict) -> None:
    """
    Atomically write `data` as JSON to `path`.

    Steps:
      1. Serialize `data` to bytes (sort_keys=True, compact, UTF-8).
      2. Write bytes to `{path}.tmp` in the same directory.
      3. fsync the file descriptor (flush OS write buffer to storage).
      4. os.replace(tmp, path) — atomic rename on POSIX; overwrites atomically.
      5. Read back `path` and compare byte-for-byte to written buffer.
      6. Raise LedgerWriteMismatchError on any divergence.

    Constraints:
      - `path` and its .tmp sibling MUST be on the same filesystem (POSIX rename atomic).
      - On crash between step 2 and step 4, only `.tmp` exists; `path` is unchanged.
      - On crash between step 4 and step 5, `path` contains the new content (correct).
      - `.tmp` file is NOT cleaned up on failure — preserves forensic evidence.

    Args:
        path: Target file path (str or Path). Parent directory must exist.
        data: Dict to serialize as JSON. Must be JSON-serializable.

    Raises:
        LedgerWriteMismatchError: Read-back does not match written buffer.
        OSError: File I/O failure (permission error, full disk, cross-device rename, etc.)
        TypeError: `data` is not JSON-serializable.
    """
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + '.tmp')

    # Step 1 — Serialize deterministically
    # sort_keys=True: required for deterministic comparison regardless of dict insertion order
    # separators=(',', ':'): compact (no extra whitespace) — canonical form
    # ensure_ascii=False: preserve unicode characters exactly
    payload: bytes = json.dumps(
        data,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    ).encode('utf-8')

    # Step 2+3 — Write to temp file and fsync
    fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, payload)
        os.fsync(fd)  # Flush OS buffer to durable storage before rename
    finally:
        os.close(fd)

    # Step 4 — Atomic rename (os.replace is atomic on POSIX within same filesystem)
    # If crash occurs here, tmp_path exists but path is unchanged (safe).
    os.replace(str(tmp_path), str(path))

    # Step 5 — Read-back verification
    # Crash here is safe: path already contains new content.
    with open(path, 'rb') as f:
        read_back: bytes = f.read()

    # Step 6 — Byte-for-byte comparison
    if read_back != payload:
        raise LedgerWriteMismatchError(str(path), payload, read_back)
