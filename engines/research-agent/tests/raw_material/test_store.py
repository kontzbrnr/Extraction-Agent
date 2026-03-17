"""
tests/raw_material/test_store.py

Tests for raw_material/store.py.

Key invariants under test:
  INV-1: every read issues a fresh disk read (no caching)
  INV-3: immutability — duplicate batch_id raises before any disk mutation
  INV-5: all_batch_ids returns deterministically sorted output
"""

import json
import pytest

from infra.ingestion.raw_material.store import (
    EMPTY_STORE,
    SCHEMA_VERSION,
    RawMaterialNotFoundError,
    RawMaterialReadError,
    RawMaterialWriteError,
    all_batch_ids,
    batch_exists,
    ingest,
    read_batch,
)
from engines.research_engine.ledger.atomic_write import atomic_write_json


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

BATCH_A = "BATCH_2024_REG_0001"
BATCH_B = "BATCH_2024_REG_0002"
BATCH_C = "BATCH_2024_REG_0003"

CONTENT_A = {"source": "article_001", "text": "Sample raw material A"}
CONTENT_B = {"source": "article_002", "text": "Sample raw material B"}


def _make_store(tmp_path) -> str:
    path = str(tmp_path / "raw_material_store.json")
    atomic_write_json(path, EMPTY_STORE)
    return path


def _read_raw(store_path: str) -> dict:
    with open(store_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# ingest — happy path
# ---------------------------------------------------------------------------


def test_ingest_writes_entry(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    data = _read_raw(path)
    assert BATCH_A in data["entries"]


def test_ingest_entry_has_required_fields(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    entry = _read_raw(path)["entries"][BATCH_A]
    assert entry["batchId"] == BATCH_A
    assert "ingestedAt" in entry
    assert entry["content"] == CONTENT_A


def test_ingest_preserves_content_exactly(tmp_path):
    path = _make_store(tmp_path)
    content = {"nested": {"key": [1, 2, 3]}, "flag": True}
    ingest(path, BATCH_A, content)
    assert _read_raw(path)["entries"][BATCH_A]["content"] == content


def test_ingest_multiple_distinct_batches(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    ingest(path, BATCH_B, CONTENT_B)
    data = _read_raw(path)
    assert BATCH_A in data["entries"]
    assert BATCH_B in data["entries"]


def test_ingest_ten_sequential_batches(tmp_path):
    path = _make_store(tmp_path)
    for i in range(1, 11):
        batch_id = f"BATCH_2024_REG_{i:04d}"
        ingest(path, batch_id, {"index": i})
    assert len(_read_raw(path)["entries"]) == 10


def test_ingest_schema_version_preserved(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    assert _read_raw(path)["schemaVersion"] == SCHEMA_VERSION


# ---------------------------------------------------------------------------
# ingest — immutability (INV-3)
# ---------------------------------------------------------------------------


def test_ingest_duplicate_raises(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    with pytest.raises(RawMaterialWriteError) as exc_info:
        ingest(path, BATCH_A, CONTENT_B)
    assert exc_info.value.batch_id == BATCH_A


def test_ingest_duplicate_no_disk_mutation(tmp_path):
    """Immutability: store must be byte-identical after duplicate attempt."""
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    before_bytes = open(path, "rb").read()
    try:
        ingest(path, BATCH_A, CONTENT_B)
    except RawMaterialWriteError:
        pass
    assert open(path, "rb").read() == before_bytes


def test_ingest_duplicate_content_unchanged(tmp_path):
    """Original content must survive a duplicate ingest attempt."""
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    try:
        ingest(path, BATCH_A, {"overwrite": "attempt"})
    except RawMaterialWriteError:
        pass
    assert _read_raw(path)["entries"][BATCH_A]["content"] == CONTENT_A


def test_ingest_empty_batch_id_raises(tmp_path):
    path = _make_store(tmp_path)
    with pytest.raises(ValueError):
        ingest(path, "", CONTENT_A)


# ---------------------------------------------------------------------------
# ingest — file errors
# ---------------------------------------------------------------------------


def test_ingest_missing_store_raises(tmp_path):
    with pytest.raises(RawMaterialReadError):
        ingest(str(tmp_path / "nonexistent.json"), BATCH_A, CONTENT_A)


def test_ingest_wrong_schema_version_raises(tmp_path):
    path = str(tmp_path / "store.json")
    atomic_write_json(path, {**EMPTY_STORE, "schemaVersion": "WRONG-1.0"})
    with pytest.raises(RawMaterialReadError) as exc_info:
        ingest(path, BATCH_A, CONTENT_A)
    assert SCHEMA_VERSION in str(exc_info.value)


# ---------------------------------------------------------------------------
# read_batch
# ---------------------------------------------------------------------------


def test_read_batch_returns_entry(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    entry = read_batch(path, BATCH_A)
    assert entry["batchId"] == BATCH_A
    assert entry["content"] == CONTENT_A


def test_read_batch_not_found_raises(tmp_path):
    path = _make_store(tmp_path)
    with pytest.raises(RawMaterialNotFoundError) as exc_info:
        read_batch(path, BATCH_A)
    assert exc_info.value.batch_id == BATCH_A


def test_read_batch_returns_independent_copy(tmp_path):
    """Mutating the returned dict must not affect subsequent reads."""
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    entry = read_batch(path, BATCH_A)
    entry["content"]["injected"] = "mutation"
    fresh = read_batch(path, BATCH_A)
    assert "injected" not in fresh["content"]


def test_read_batch_reflects_disk_state(tmp_path):
    """INV-1: read_batch must re-read disk — no stale cache."""
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    ingest(path, BATCH_B, CONTENT_B)
    entry = read_batch(path, BATCH_B)
    assert entry["content"] == CONTENT_B


def test_read_batch_empty_batch_id_raises(tmp_path):
    path = _make_store(tmp_path)
    with pytest.raises(ValueError):
        read_batch(path, "")


# ---------------------------------------------------------------------------
# batch_exists
# ---------------------------------------------------------------------------


def test_batch_exists_true_after_ingest(tmp_path):
    path = _make_store(tmp_path)
    ingest(path, BATCH_A, CONTENT_A)
    assert batch_exists(path, BATCH_A) is True


def test_batch_exists_false_before_ingest(tmp_path):
    path = _make_store(tmp_path)
    assert batch_exists(path, BATCH_A) is False


def test_batch_exists_no_write_side_effect(tmp_path):
    """batch_exists must not mutate the store file."""
    path = _make_store(tmp_path)
    before_bytes = open(path, "rb").read()
    batch_exists(path, BATCH_A)
    assert open(path, "rb").read() == before_bytes


def test_batch_exists_reads_disk_each_call(tmp_path):
    """INV-1: second call must reflect state written between calls."""
    path = _make_store(tmp_path)
    assert batch_exists(path, BATCH_A) is False
    ingest(path, BATCH_A, CONTENT_A)
    assert batch_exists(path, BATCH_A) is True


# ---------------------------------------------------------------------------
# all_batch_ids
# ---------------------------------------------------------------------------


def test_all_batch_ids_empty_store(tmp_path):
    path = _make_store(tmp_path)
    assert all_batch_ids(path) == []


def test_all_batch_ids_sorted_ascending(tmp_path):
    """INV-5: output must be deterministically sorted."""
    path = _make_store(tmp_path)
    ingest(path, BATCH_C, CONTENT_A)
    ingest(path, BATCH_A, CONTENT_A)
    ingest(path, BATCH_B, CONTENT_A)
    result = all_batch_ids(path)
    assert result == [BATCH_A, BATCH_B, BATCH_C]


def test_all_batch_ids_reflects_disk_state(tmp_path):
    """INV-1: re-read after ingest must include new batch_id."""
    path = _make_store(tmp_path)
    assert all_batch_ids(path) == []
    ingest(path, BATCH_A, CONTENT_A)
    assert all_batch_ids(path) == [BATCH_A]


def test_all_batch_ids_count_matches_ingest_count(tmp_path):
    path = _make_store(tmp_path)
    for i in range(1, 6):
        ingest(path, f"BATCH_2024_REG_{i:04d}", {"i": i})
    assert len(all_batch_ids(path)) == 5
