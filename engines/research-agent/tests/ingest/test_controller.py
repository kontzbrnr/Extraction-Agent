"""
tests/ingest/test_controller.py

Tests for ingest/controller.py.

Key invariants under test:
  INV-1: IngestController is memoryless — no ledger state reads, no
         batch_id derivation from season state.
  INV-3: Duplicate batch_id propagates RawMaterialWriteError (not caught).
"""

import json
import pytest

from infra.ingestion.ingest.controller import IngestReceipt, submit
from infra.ingestion.raw_material.store import (
    EMPTY_STORE,
    RawMaterialWriteError,
    all_batch_ids,
    read_batch,
)
from engines.research_engine.ledger.atomic_write import atomic_write_json


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

BATCH_A = "BATCH_2024_REG_0001"
BATCH_B = "BATCH_2024_REG_0002"

MATERIAL_A = {"source": "article_001", "body": "Raw content A"}
MATERIAL_B = {"source": "article_002", "body": "Raw content B"}


def _make_store(tmp_path) -> str:
    path = str(tmp_path / "raw_material_store.json")
    atomic_write_json(path, EMPTY_STORE)
    return path


# ---------------------------------------------------------------------------
# submit — happy path
# ---------------------------------------------------------------------------


def test_submit_returns_ingest_receipt(tmp_path):
    path = _make_store(tmp_path)
    receipt = submit(path, BATCH_A, MATERIAL_A)
    assert isinstance(receipt, IngestReceipt)


def test_submit_receipt_carries_batch_id(tmp_path):
    path = _make_store(tmp_path)
    receipt = submit(path, BATCH_A, MATERIAL_A)
    assert receipt.batch_id == BATCH_A


def test_submit_receipt_has_ingested_at_timestamp(tmp_path):
    path = _make_store(tmp_path)
    receipt = submit(path, BATCH_A, MATERIAL_A)
    assert receipt.ingested_at
    # Must be ISO-8601 parseable
    from datetime import datetime
    datetime.fromisoformat(receipt.ingested_at)


def test_submit_receipt_is_frozen(tmp_path):
    path = _make_store(tmp_path)
    receipt = submit(path, BATCH_A, MATERIAL_A)
    with pytest.raises((AttributeError, TypeError)):
        receipt.batch_id = "mutated"  # type: ignore[misc]


def test_submit_persists_to_store(tmp_path):
    path = _make_store(tmp_path)
    submit(path, BATCH_A, MATERIAL_A)
    entry = read_batch(path, BATCH_A)
    assert entry["content"] == MATERIAL_A


def test_submit_content_preserved_exactly(tmp_path):
    path = _make_store(tmp_path)
    material = {"nested": {"key": [1, 2, 3]}, "flag": True, "count": 42}
    submit(path, BATCH_A, material)
    assert read_batch(path, BATCH_A)["content"] == material


def test_submit_multiple_batches(tmp_path):
    path = _make_store(tmp_path)
    submit(path, BATCH_A, MATERIAL_A)
    submit(path, BATCH_B, MATERIAL_B)
    assert all_batch_ids(path) == [BATCH_A, BATCH_B]


def test_submit_empty_dict_material_accepted(tmp_path):
    """Empty dict is a valid (if unusual) source_material."""
    path = _make_store(tmp_path)
    receipt = submit(path, BATCH_A, {})
    assert receipt.batch_id == BATCH_A
    assert read_batch(path, BATCH_A)["content"] == {}


# ---------------------------------------------------------------------------
# submit — input validation (pre-I/O, INV-1)
# ---------------------------------------------------------------------------


def test_submit_empty_batch_id_raises_before_io(tmp_path):
    """ValueError must raise before any store file is accessed."""
    # No store file created — if I/O were attempted first, a different error
    # would occur. ValueError confirms pre-I/O enforcement.
    with pytest.raises(ValueError) as exc_info:
        submit(str(tmp_path / "nonexistent.json"), "", MATERIAL_A)
    assert "batch_id" in str(exc_info.value).lower()


def test_submit_none_material_raises_before_io(tmp_path):
    with pytest.raises(ValueError) as exc_info:
        submit(str(tmp_path / "nonexistent.json"), BATCH_A, None)  # type: ignore
    assert "source_material" in str(exc_info.value).lower()


def test_submit_non_dict_material_raises_before_io(tmp_path):
    with pytest.raises(ValueError) as exc_info:
        submit(str(tmp_path / "nonexistent.json"), BATCH_A, ["not", "a", "dict"])  # type: ignore
    assert "dict" in str(exc_info.value).lower()


def test_submit_int_material_raises(tmp_path):
    with pytest.raises(ValueError):
        submit(str(tmp_path / "nonexistent.json"), BATCH_A, 42)  # type: ignore


# ---------------------------------------------------------------------------
# submit — immutability propagation (INV-3)
# ---------------------------------------------------------------------------


def test_submit_duplicate_propagates_raw_material_write_error(tmp_path):
    path = _make_store(tmp_path)
    submit(path, BATCH_A, MATERIAL_A)
    with pytest.raises(RawMaterialWriteError) as exc_info:
        submit(path, BATCH_A, MATERIAL_B)
    assert exc_info.value.batch_id == BATCH_A


def test_submit_duplicate_does_not_overwrite_content(tmp_path):
    path = _make_store(tmp_path)
    submit(path, BATCH_A, MATERIAL_A)
    try:
        submit(path, BATCH_A, MATERIAL_B)
    except RawMaterialWriteError:
        pass
    assert read_batch(path, BATCH_A)["content"] == MATERIAL_A


# ---------------------------------------------------------------------------
# INV-1 — memoryless: no ledger state reads
# ---------------------------------------------------------------------------


def test_submit_does_not_read_global_state(tmp_path, monkeypatch):
    """IngestController must never open global_state.json."""
    path = _make_store(tmp_path)
    opened_paths = []

    original_open = open

    def tracking_open(file, *args, **kwargs):
        opened_paths.append(str(file))
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", tracking_open)
    submit(path, BATCH_A, MATERIAL_A)

    for p in opened_paths:
        assert "global_state" not in p, (
            f"IngestController must not read global_state.json, but opened: {p}"
        )


def test_submit_does_not_read_season_state(tmp_path, monkeypatch):
    """IngestController must never open season state.json (ledger state)."""
    path = _make_store(tmp_path)
    opened_paths = []

    original_open = open

    def tracking_open(file, *args, **kwargs):
        opened_paths.append(str(file))
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", tracking_open)
    submit(path, BATCH_A, MATERIAL_A)

    for p in opened_paths:
        # state.json in a run directory = season state
        assert "state.json" not in p or "raw_material" in p, (
            f"IngestController must not read ledger state.json, but opened: {p}"
        )


def test_submit_does_not_call_mark_batch_start(tmp_path, monkeypatch):
    """IngestController must not set the incompleteBatchFlag."""
    path = _make_store(tmp_path)
    call_log = []

    def mock_mark(*args, **kwargs):
        call_log.append(("mark_batch_start", args))

    monkeypatch.setattr(
        "ledger.season_state_manager.mark_batch_start",
        mock_mark,
        raising=False,
    )

    submit(path, BATCH_A, MATERIAL_A)
    assert call_log == [], (
        "IngestController must not call mark_batch_start — "
        "that is MicroBatchScaffold's responsibility"
    )


# ---------------------------------------------------------------------------
# receipt ingested_at is independent from store ingestedAt
# ---------------------------------------------------------------------------


def test_receipt_ingested_at_is_independent_of_store(tmp_path):
    """IngestReceipt.ingested_at is the controller's timestamp,
    not the store's ingestedAt — they are separate fields."""
    path = _make_store(tmp_path)
    receipt = submit(path, BATCH_A, MATERIAL_A)
    store_entry = read_batch(path, BATCH_A)
    # Both timestamps exist independently
    assert receipt.ingested_at is not None
    assert store_entry["ingestedAt"] is not None
    # They record the same moment but are different strings from different calls
    # (no assertion on equality — they may differ by microseconds)
    assert isinstance(receipt.ingested_at, str)
    assert isinstance(store_entry["ingestedAt"], str)
