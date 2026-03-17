"""
nti/extraction_fingerprint_registry.py

Extraction-level structural fingerprint registry.

Governing contract:
  NTI-CYCLE-EXECUTION.md:
    Section VI: "Fingerprint registry used in NTI is: Extraction-level
                duplication control. It must not: Encode season, Encode
                Time Surface, Encode cycle ID. Duplication is structural,
                not temporal."

This registry is DISTINCT from the canonical fingerprint registry
(CPS_FINGERPRINT_V1 defined exclusively in PSTA v4). This registry
operates pre-canonicalization at the NTI extraction layer to prevent
re-processing structurally identical material.

Fingerprint format:
  Opaque non-empty string. Caller is responsible for computing the
  fingerprint from structural content only (no time/surface/season fields).
  SHA-256 hex strings are the system convention but are not enforced here.
  The registry stores and looks up fingerprints — it does not compute them.

No time encoding (INV-5 / contract guarantee):
  Registry schema contains ZERO time fields: only schemaVersion and
  fingerprints. The registry has no awareness of season, surface, cycle,
  batch_id, or any temporal context. Identical structural content produces
  an identical fingerprint string that is a duplicate in this registry
  regardless of when or under which surface it was registered.

Storage:
  {ledger_root}/{active_run_path}/extraction_fingerprints.json
  Parallel to state.json and nti_state.json in the active run directory.
  Scope: per-season-run.

INV-5 enforcement:
  Fingerprints are stored as a sorted list (ascending). This ensures
  atomic_write_json produces byte-identical output for identical fingerprint
  sets regardless of registration order. atomic_write_json uses sort_keys=True
  for dict keys only — list element ordering is this module's responsibility.

Write pattern:
  Append-only. atomic_write_json with read-back verification (via
  ledger.atomic_write). No fingerprint may be removed once registered.

No preflight:
  This is a data store (like raw_material/store.py). No preflight_read
  call. Caller is responsible for system state validation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from engines.research_engine.ledger.atomic_write import atomic_write_json

EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION = "EXTRACTION_FINGERPRINT_REGISTRY-1.0"

EMPTY_REGISTRY: dict = {
    "schemaVersion": EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION,
    "fingerprints": [],
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class FingerprintRegistryError(Exception):
    """Base class for extraction fingerprint registry errors."""


class FingerprintRegistryExistsError(FingerprintRegistryError):
    """Raised by create_registry when the registry file already exists."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Extraction fingerprint registry already exists: {path}")
        self.path = path


class FingerprintRegistryReadError(FingerprintRegistryError):
    """Raised when the registry file is missing, invalid JSON, or wrong schema."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.path = path


# ---------------------------------------------------------------------------
# Path helper
# ---------------------------------------------------------------------------


def _registry_path(ledger_root: str, active_run_path: str) -> str:
    normalized = active_run_path.rstrip("/").rstrip("\\")
    return os.path.join(ledger_root, normalized, "extraction_fingerprints.json")


# ---------------------------------------------------------------------------
# Internal read
# ---------------------------------------------------------------------------


def _read_registry(ledger_root: str, active_run_path: str) -> dict:
    path = _registry_path(ledger_root, active_run_path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise FingerprintRegistryReadError(
            f"Extraction fingerprint registry not found: {path}", path=path
        ) from exc
    except json.JSONDecodeError as exc:
        raise FingerprintRegistryReadError(
            f"Extraction fingerprint registry is not valid JSON: {exc}", path=path
        ) from exc

    actual = data.get("schemaVersion")
    if actual != EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION:
        raise FingerprintRegistryReadError(
            f"schemaVersion mismatch: expected "
            f"'{EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION}', got '{actual}'",
            path=path,
        )
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_registry(ledger_root: str, active_run_path: str) -> dict:
    """Create a new empty extraction fingerprint registry.

    Raises:
        FingerprintRegistryExistsError: file already exists (pre-IO check).
    """
    path = _registry_path(ledger_root, active_run_path)
    if os.path.exists(path):
        raise FingerprintRegistryExistsError(path)

    state = {
        "schemaVersion": EXTRACTION_FINGERPRINT_REGISTRY_SCHEMA_VERSION,
        "fingerprints": [],
    }
    atomic_write_json(path, state)
    return state


def register_fingerprint(
    ledger_root: str,
    active_run_path: str,
    fingerprint: str,
) -> bool:
    """Register a structural fingerprint.

    Idempotent: if the fingerprint already exists, returns False with no
    disk write. Fingerprints are stored sorted (ascending) for INV-5.

    Args:
        fingerprint: Non-empty opaque string. Caller must ensure it encodes
                     structural content only — no season, surface, or cycle
                     fields (NTI-CYCLE-EXECUTION.md Section VI).

    Returns:
        True if fingerprint was new and registered.
        False if fingerprint already existed (no write performed).

    Raises:
        ValueError:                  fingerprint is empty or not a string
                                     (raised pre-IO).
        FingerprintRegistryReadError: registry file unreadable.
    """
    # Pre-IO validation
    if not isinstance(fingerprint, str):
        raise ValueError(
            f"fingerprint must be a non-empty string, got {type(fingerprint).__name__!r}"
        )
    if not fingerprint:
        raise ValueError("fingerprint must not be an empty string")

    registry = _read_registry(ledger_root, active_run_path)
    existing: set[str] = set(registry["fingerprints"])

    if fingerprint in existing:
        return False  # Already registered — idempotent, no write.

    existing.add(fingerprint)
    registry["fingerprints"] = sorted(existing)  # INV-5: sorted list
    path = _registry_path(ledger_root, active_run_path)
    atomic_write_json(path, registry)
    return True


def is_registered(
    ledger_root: str,
    active_run_path: str,
    fingerprint: str,
) -> bool:
    """Check whether a fingerprint is already registered.

    Read-only. No disk writes.

    Returns:
        True if fingerprint exists in registry, False otherwise.

    Raises:
        FingerprintRegistryReadError: registry file unreadable.
    """
    registry = _read_registry(ledger_root, active_run_path)
    return fingerprint in set(registry["fingerprints"])


def registry_size(ledger_root: str, active_run_path: str) -> int:
    """Return the number of registered fingerprints.

    Raises:
        FingerprintRegistryReadError: registry file unreadable.
    """
    registry = _read_registry(ledger_root, active_run_path)
    return len(registry["fingerprints"])


def all_fingerprints(ledger_root: str, active_run_path: str) -> frozenset[str]:
    """Return all registered fingerprints as a frozenset.

    Order-independent. Fresh disk read on every call (no caching).

    Raises:
        FingerprintRegistryReadError: registry file unreadable.
    """
    registry = _read_registry(ledger_root, active_run_path)
    return frozenset(registry["fingerprints"])
