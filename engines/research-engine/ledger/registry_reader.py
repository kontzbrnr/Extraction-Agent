"""
ledger/registry_reader.py

Read-only canonical object registry reader.

Governing contract: ORCHESTRATOR-EXECUTION-CONTRACT.md Section IX:
  "Canonical registry cardinality SHALL be derived from registry contents only.
   No procedural canonical counters are permitted."

INV-1 enforcement: every function reads from disk unconditionally.
INV-3 enforcement: this module imports NO write primitives. It never opens
  any file for writing, never creates temp files, never calls os.replace.
INV-4 enforcement: lane counts are derived independently per lane key.

The five valid lane keys are the same set established in registry_writer.py.
This module does not import from registry_writer to avoid coupling;
it re-declares the constant locally as the single source of truth
for the reader domain.
"""

from __future__ import annotations

import json

VALID_LANES = frozenset({"CPS", "CME", "CSN", "StructuralEnvironment", "MediaContext"})
CANONICAL_REGISTRY_SCHEMA_VERSION = "CANONICAL_REGISTRY-1.0"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class RegistryReadError(Exception):
    """Raised when the registry file cannot be loaded or fails validation."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.path = path


# ---------------------------------------------------------------------------
# Core loader — single disk read, used by all cardinality functions
# ---------------------------------------------------------------------------


def read_registry(registry_path: str) -> dict:
    """Load and validate canonical_objects.json from disk.

    Reads from disk unconditionally on every call (INV-1).
    Never writes, renames, or mutates the file (INV-3).

    Args:
        registry_path: Absolute or relative path to canonical_objects.json.

    Returns:
        The parsed registry dict.

    Raises:
        RegistryReadError: file missing, invalid JSON, wrong schemaVersion,
                           or any required lane key absent from the file.
    """
    try:
        with open(registry_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise RegistryReadError(
            f"canonical_objects.json not found: {registry_path}",
            path=registry_path,
        )
    except json.JSONDecodeError as exc:
        raise RegistryReadError(
            f"canonical_objects.json is not valid JSON: {exc}",
            path=registry_path,
        )

    actual_version = data.get("schemaVersion")
    if actual_version != CANONICAL_REGISTRY_SCHEMA_VERSION:
        raise RegistryReadError(
            f"schemaVersion mismatch: expected '{CANONICAL_REGISTRY_SCHEMA_VERSION}', "
            f"got '{actual_version}'",
            path=registry_path,
        )

    # All five lane keys must be present — absence is a schema violation,
    # not silently defaulted to an empty list.
    for lane in VALID_LANES:
        if lane not in data:
            raise RegistryReadError(
                f"required lane key '{lane}' missing from registry",
                path=registry_path,
            )
        if not isinstance(data[lane], list):
            raise RegistryReadError(
                f"lane '{lane}' must be an array, got {type(data[lane]).__name__}",
                path=registry_path,
            )

    return data


# ---------------------------------------------------------------------------
# Cardinality functions
# ---------------------------------------------------------------------------


def lane_cardinality(registry_path: str, lane: str) -> int:
    """Return the number of canonical objects in a single lane.

    Derives count from len(registry[lane]) on a fresh disk read (INV-1).
    Never uses or increments a counter field (contract rule).

    Args:
        registry_path: Path to canonical_objects.json.
        lane:          One of the five valid lane keys.

    Returns:
        Integer count >= 0.

    Raises:
        RegistryReadError: invalid lane key (pre-read) or file unreadable.
    """
    if lane not in VALID_LANES:
        raise RegistryReadError(
            f"invalid lane key: '{lane}'. Valid lanes: {sorted(VALID_LANES)}"
        )

    registry = read_registry(registry_path)
    return len(registry[lane])


def all_lane_cardinalities(registry_path: str) -> dict[str, int]:
    """Return a dict of lane → count for all five lanes.

    All five counts are derived from a SINGLE disk read to ensure
    the snapshot is consistent (INV-4 — no cross-lane contamination,
    INV-1 — fresh read).

    Args:
        registry_path: Path to canonical_objects.json.

    Returns:
        Dict with keys: CPS, CME, CSN, StructuralEnvironment, MediaContext.
        Each value is the count of objects in that lane (>= 0).

    Raises:
        RegistryReadError: file unreadable or schema invalid.
    """
    registry = read_registry(registry_path)
    return {lane: len(registry[lane]) for lane in sorted(VALID_LANES)}


def total_registry_cardinality(registry_path: str) -> int:
    """Return the sum of all canonical objects across all five lanes.

    Derived from a SINGLE disk read — not the sum of five independent reads.
    This ensures the total is consistent with a single point-in-time snapshot.

    Args:
        registry_path: Path to canonical_objects.json.

    Returns:
        Total integer count across all lanes (>= 0).

    Raises:
        RegistryReadError: file unreadable or schema invalid.
    """
    registry = read_registry(registry_path)
    return sum(len(registry[lane]) for lane in VALID_LANES)
