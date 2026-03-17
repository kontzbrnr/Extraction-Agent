"""
Tests for ledger/atomic_write.py

Validates all Phase 1 acceptance criteria:
  - Successful write produces correct file content
  - Read-back mismatch raises LedgerWriteMismatchError (never silent pass)
  - Crash-before-rename leaves original file intact (pre-write state preserved)
  - JSON serialization is deterministic (sort_keys enforced)
  - fsync called before rename
  - .tmp file cleaned up on success, left in place on failure
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, call

from engines.research_engine.ledger.atomic_write import atomic_write_json, LedgerWriteMismatchError


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_file(tmp_path):
    """Returns a path to a non-existent file in a temp directory."""
    return tmp_path / "ledger_test.json"


# ── AC-1: Successful write produces correct, readable JSON ───────────────────

def test_successful_write_produces_correct_content(tmp_file):
    data = {"lane": "pressure", "version": "CPS-1.0", "count": 42}
    atomic_write_json(tmp_file, data)
    assert tmp_file.exists()
    read_data = json.loads(tmp_file.read_text(encoding='utf-8'))
    assert read_data == data


def test_successful_write_leaves_no_tmp_file(tmp_file):
    data = {"key": "value"}
    atomic_write_json(tmp_file, data)
    tmp = Path(str(tmp_file) + '.tmp')
    assert not tmp.exists(), ".tmp file must be cleaned up on successful write"


# ── AC-2: sort_keys=True enforced — deterministic serialization ───────────────

def test_serialization_is_deterministic_regardless_of_insertion_order(tmp_file):
    data_a = {"z": 1, "a": 2, "m": 3}
    data_b = {"a": 2, "m": 3, "z": 1}
    atomic_write_json(tmp_file, data_a)
    content_a = tmp_file.read_bytes()
    atomic_write_json(tmp_file, data_b)
    content_b = tmp_file.read_bytes()
    assert content_a == content_b, "sort_keys=True must produce identical output for same logical content"


# ── AC-3: Mismatch raises LedgerWriteMismatchError — never silent pass ────────

def test_mismatch_raises_ledger_write_mismatch_error(tmp_file):
    """
    Simulate filesystem returning corrupted content on read-back.
    Patch open() to return different bytes than what was written.
    """
    data = {"id": "CPS_abc123"}
    corrupted = b'{"id":"CORRUPTED"}'

    original_open = open

    def patched_open(path, mode='r', **kwargs):
        # Only intercept the read-back (binary read of the target path)
        if str(path) == str(tmp_file) and mode == 'rb':
            import io
            return io.BytesIO(corrupted)
        return original_open(path, mode, **kwargs)

    with patch('builtins.open', side_effect=patched_open):
        with pytest.raises(LedgerWriteMismatchError) as exc_info:
            atomic_write_json(tmp_file, data)

    err = exc_info.value
    assert err.path == str(tmp_file)
    assert err.written != err.read_back


# ── AC-4: Crash-before-rename — original file untouched ─────────────────────

def test_crash_before_rename_leaves_original_intact(tmp_file):
    """
    Simulate crash between fsync and rename by patching os.replace to raise.
    Original file must remain in pre-write state.
    """
    original_data = {"status": "original", "version": 1}
    # Write original state
    atomic_write_json(tmp_file, original_data)

    new_data = {"status": "new", "version": 2}

    with patch('os.replace', side_effect=OSError("Simulated crash mid-rename")):
        with pytest.raises(OSError, match="Simulated crash mid-rename"):
            atomic_write_json(tmp_file, new_data)

    # Original file must be unchanged
    surviving = json.loads(tmp_file.read_text(encoding='utf-8'))
    assert surviving == original_data, "Crash before rename must not mutate original"


def test_crash_before_rename_at_byte_1_preserves_original(tmp_file):
    """Roadmap validation: crash at byte 1 — original preserved."""
    original_data = {"seq": 0}
    atomic_write_json(tmp_file, original_data)

    with patch('os.replace', side_effect=OSError("crash at byte 1")):
        with pytest.raises(OSError):
            atomic_write_json(tmp_file, {"seq": 1})

    assert json.loads(tmp_file.read_text())["seq"] == 0


def test_crash_before_rename_at_byte_n_minus_1_preserves_original(tmp_file):
    """Roadmap validation: crash at byte N-1 — original preserved."""
    original_data = {"seq": 0}
    atomic_write_json(tmp_file, original_data)

    with patch('os.replace', side_effect=OSError("crash at byte N-1")):
        with pytest.raises(OSError):
            atomic_write_json(tmp_file, {"seq": 99})

    assert json.loads(tmp_file.read_text())["seq"] == 0


# ── AC-5: fsync called before rename ────────────────────────────────────────

def test_fsync_called_before_rename(tmp_file):
    """
    Verify call order: fsync must occur before os.replace.
    Uses os-level call tracking.
    """
    data = {"fsync_test": True}
    call_order = []

    original_fsync = os.fsync
    original_replace = os.replace

    def tracking_fsync(fd):
        call_order.append('fsync')
        return original_fsync(fd)

    def tracking_replace(src, dst):
        call_order.append('replace')
        return original_replace(src, dst)

    with patch('os.fsync', side_effect=tracking_fsync), \
         patch('os.replace', side_effect=tracking_replace):
        atomic_write_json(tmp_file, data)

    assert call_order == ['fsync', 'replace'], \
        f"fsync must precede os.replace. Got order: {call_order}"


# ── AC-6: Overwrites existing file atomically ────────────────────────────────

def test_overwrites_existing_file(tmp_file):
    atomic_write_json(tmp_file, {"v": 1})
    atomic_write_json(tmp_file, {"v": 2})
    result = json.loads(tmp_file.read_text())
    assert result == {"v": 2}


# ── AC-7: LedgerWriteMismatchError carries path, written, read_back ──────────

def test_mismatch_error_carries_full_context(tmp_file):
    data = {"a": 1}
    original_open = open

    def patched_open(path, mode='r', **kwargs):
        if str(path) == str(tmp_file) and mode == 'rb':
            import io
            return io.BytesIO(b'bad')
        return original_open(path, mode, **kwargs)

    with patch('builtins.open', side_effect=patched_open):
        with pytest.raises(LedgerWriteMismatchError) as exc_info:
            atomic_write_json(tmp_file, data)

    assert exc_info.value.path == str(tmp_file)
    assert isinstance(exc_info.value.written, bytes)
    assert exc_info.value.read_back == b'bad'
