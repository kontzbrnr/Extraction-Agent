"""
raw_material/store.py

Append-only, batch_id-keyed raw material ingest store.

Governing authority: Research Agent Execution Roadmap, Phase 2.
  IngestController: assigns batch_id, writes to RawMaterialStore.
  ExtractionAgent:  reads from RawMaterialStore by batch_id.

Immutability rule (contract):
  "read-only after ingest: any write attempt raises error"
  Enforced by RawMaterialWriteError on duplicate batch_id — pre-read check,
  no disk mutation on violation.

Content policy:
  The store is content-agnostic. Entry content dicts are stored and
  returned opaquely. No validation of content structure is performed.
  Content schema is owned by IngestController (caller).

I/O:
  All writes delegate to ledger.atomic_write.atomic_write_json.
  All reads issue a fresh disk read (INV-1 — no in-memory caching).

Store file structure:
  {
    "schemaVersion": "RAW_MATERIAL_STORE-1.0",
    "entries": {
      "BATCH_2024_REG_0001": {
        "batchId":    "BATCH_2024_REG_0001",
        "ingestedAt": "2024-09-01T12:00:00+00:00",
        "content":    { ... opaque caller-supplied dict ... }
      }
    }
  }
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from engines.research_engine.ledger.atomic_write import atomic_write_json

SCHEMA_VERSION = "RAW_MATERIAL_STORE-1.0"

EMPTY_STORE: dict = {
    "schemaVersion": SCHEMA_VERSION,
    "entries": {},
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RawMaterialWriteError(Exception):
    """Raised when ingest is attempted for an already-present batch_id.

    The store is immutable after write — no entry may be overwritten.
    """

    def __init__(self, batch_id: str) -> None:
        super().__init__(
            f"batch_id '{batch_id}' already exists in store — "
            "RawMaterialStore entries are immutable after ingest"
        )
        self.batch_id = batch_id


class RawMaterialReadError(Exception):
    """Raised when the store file cannot be loaded or fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.path = path


class RawMaterialNotFoundError(Exception):
    """Raised when read_batch is called with a batch_id not present in the store."""

    def __init__(self, batch_id: str) -> None:
        super().__init__(f"batch_id '{batch_id}' not found in RawMaterialStore")
        self.batch_id = batch_id


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_batch_id(batch_id: str) -> None:
    if not batch_id:
        raise ValueError("batch_id must be a non-empty string")


def _load_store(store_path: str) -> dict:
    """Read and validate store file from disk. No caching (INV-1)."""
    try:
        with open(store_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise RawMaterialReadError(
            f"RawMaterialStore not found: {store_path}", path=store_path
        )
    except json.JSONDecodeError as exc:
        raise RawMaterialReadError(
            f"RawMaterialStore is not valid JSON: {exc}", path=store_path
        )

    actual = data.get("schemaVersion")
    if actual != SCHEMA_VERSION:
        raise RawMaterialReadError(
            f"schemaVersion mismatch: expected '{SCHEMA_VERSION}', got '{actual}'",
            path=store_path,
        )

    if "entries" not in data or not isinstance(data["entries"], dict):
        raise RawMaterialReadError(
            "RawMaterialStore missing required 'entries' dict",
            path=store_path,
        )

    return data


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ingest(store_path: str, batch_id: str, content: dict) -> None:
    """Append a new entry keyed by batch_id.

    Writes are immutable: raises RawMaterialWriteError if batch_id already
    exists. No disk mutation occurs on violation.

    Args:
        store_path: Path to the store JSON file. Must already exist and be
                    valid. Use EMPTY_STORE to initialise a new store file.
        batch_id:   Unique batch identifier (e.g. "BATCH_2024_REG_0001").
                    Must be non-empty.
        content:    Opaque dict of raw material content. Not validated by
                    the store — caller owns the schema.

    Raises:
        ValueError:               batch_id is empty.
        RawMaterialWriteError:    batch_id already exists (pre-read, no write).
        RawMaterialReadError:     store file unreadable or schema invalid.
        LedgerWriteMismatchError: atomic write read-back failed.
    """
    _validate_batch_id(batch_id)

    store = _load_store(store_path)

    if batch_id in store["entries"]:
        raise RawMaterialWriteError(batch_id)

    store["entries"][batch_id] = {
        "batchId": batch_id,
        "ingestedAt": _now_iso(),
        "content": content,
    }

    atomic_write_json(store_path, store)


def read_batch(store_path: str, batch_id: str) -> dict:
    """Retrieve the entry for a given batch_id.

    Reads from disk unconditionally (INV-1).
    Returns an independent copy — mutating the result does not affect
    subsequent reads.

    Args:
        store_path: Path to the store JSON file.
        batch_id:   Batch identifier to retrieve.

    Returns:
        The full entry dict: {batchId, ingestedAt, content}.

    Raises:
        ValueError:                batch_id is empty.
        RawMaterialReadError:      store file unreadable or schema invalid.
        RawMaterialNotFoundError:  batch_id not present in store.
    """
    _validate_batch_id(batch_id)

    store = _load_store(store_path)

    if batch_id not in store["entries"]:
        raise RawMaterialNotFoundError(batch_id)

    import copy

    return copy.deepcopy(store["entries"][batch_id])


def batch_exists(store_path: str, batch_id: str) -> bool:
    """Return True if batch_id is present in the store.

    Reads from disk on every call (INV-1). Zero write side effects.

    Raises:
        ValueError:           batch_id is empty.
        RawMaterialReadError: store file unreadable or schema invalid.
    """
    _validate_batch_id(batch_id)
    store = _load_store(store_path)
    return batch_id in store["entries"]


def all_batch_ids(store_path: str) -> list[str]:
    """Return all batch_ids in the store, sorted ascending.

    Sorted order is deterministic for identical store contents (INV-5).
    Reads from disk on every call (INV-1).

    Raises:
        RawMaterialReadError: store file unreadable or schema invalid.
    """
    store = _load_store(store_path)
    return sorted(store["entries"].keys())
