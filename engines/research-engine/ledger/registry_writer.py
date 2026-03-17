"""
Append-Only Registry Writer — canonical_objects.json manager.

Contract: ORCHESTRATOR-EXECUTION-CONTRACT.md
  "Canonical objects are append-only."
  "Registry cardinality may increase only through new canonical mint events."
  "Historical registry entries remain untouched."
  "Canonical registry cardinality SHALL be derived from registry contents only.
   No procedural canonical counters are permitted."
  "Orchestrator persists canonical objects exactly as emitted."
  "No batching of canonical commits. Atomic per object."

Schema: schemas/ledger/canonical_objects.schema.json
  Lane keys: CPS, CME, CSN, StructuralEnvironment, MediaContext
  schemaVersion: "CANONICAL_REGISTRY-1.0"
  Arrays sorted by canonicalId ascending (required for determinismChecksum stability).

ID field per lane:
  CPS              → "canonicalId"   (CPS schema required fields)
  CME              → "id"            (CME schema required fields)
  CSN              → "id"            (CSN schema required fields)
  StructuralEnv    → "id"            (CSE schema)
  MediaContext     → "id"            (stub — MFU deferred, Phase 0.4 Option A)
"""

import json
from pathlib import Path

from engines.research_engine.ledger.atomic_write import atomic_write_json


SCHEMA_VERSION = "CANONICAL_REGISTRY-1.0"

VALID_LANES = frozenset({"CPS", "CME", "CSN", "StructuralEnvironment", "MediaContext"})

_LANE_ID_FIELD: dict[str, str] = {
    "CPS": "canonicalId",
    "CME": "id",
    "CSN": "id",
    "StructuralEnvironment": "id",
    "MediaContext": "id",
}

_ALLOWED_LANE_TYPES: dict[str, frozenset[str]] = {
    "CPS": frozenset({"CPS", "PRESSURE"}),
    "CME": frozenset({"CME"}),
    "CSN": frozenset({"CSN", "NARRATIVE"}),
    "StructuralEnvironment": frozenset({"StructuralEnvironment"}),
    "MediaContext": frozenset({"MediaContext"}),
}

EMPTY_REGISTRY: dict = {
    "schemaVersion": SCHEMA_VERSION,
    "CPS": [],
    "CME": [],
    "CSN": [],
    "StructuralEnvironment": [],
    "MediaContext": [],
}


class RegistryAppendError(Exception):
    """
    Raised when an append operation would violate append-only semantics.
    Covers: duplicate canonical ID (in-place edit attempt), invalid lane key.
    Never silently swallowed.
    """

    def __init__(self, message: str, lane: str = "", canonical_id: str = ""):
        self.lane = lane
        self.canonical_id = canonical_id
        super().__init__(message)


class LaneMismatchError(Exception):
    """
    Raised when the lane parameter does not match the object's
    laneType field.

    Prevents cross-lane contamination (INV-4).
    Only raised when the object explicitly carries a laneType field.
    Objects without laneType are lane-untyped (e.g. RECs) and pass
    without validation.
    """
    def __init__(self, expected: str, found: str) -> None:
        super().__init__(
            f"Lane mismatch: lane parameter is '{expected}' "
            f"but object laneType is '{found}'"
        )
        self.expected = expected
        self.found = found


def _load_registry(registry_path: Path) -> dict:
    """Load registry from disk. Initialize with empty structure if absent."""
    if not registry_path.exists():
        return {k: (list(v) if isinstance(v, list) else v) for k, v in EMPTY_REGISTRY.items()}
    with open(registry_path, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _get_canonical_id(obj: dict, lane: str) -> str:
    """
    Extract the canonical ID from a canonical object using the lane-specific
    ID field. Raises RegistryAppendError if the ID field is absent or empty.
    """
    id_field = _LANE_ID_FIELD[lane]
    canonical_id = obj.get(id_field)
    if not canonical_id:
        raise RegistryAppendError(
            f"Object in lane '{lane}' missing required ID field '{id_field}': {obj}",
            lane=lane,
        )
    return canonical_id


def _lane_contains_id(lane_array: list, canonical_id: str, id_field: str) -> bool:
    """Return True if any existing object in the lane has the given canonical ID."""
    return any(existing_obj.get(id_field) == canonical_id for existing_obj in lane_array)


def append_canonical_object(registry_path, lane: str, obj: dict) -> None:
    """
    Append a single CIV-validated canonical object to the specified lane.

    Steps:
      1. Validate lane key against VALID_LANES.
      2. Load registry from disk (initialize if absent).
      3. Extract canonical ID from object using lane-specific ID field.
      4. Reject with RegistryAppendError if canonical ID already exists (INV-3).
      5. Append object to lane array exactly as received (zero mutation).
      6. Sort lane array by canonical ID ascending (determinismChecksum stability).
      7. Write registry atomically via atomic_write_json (Phase 1.1).

    Args:
        registry_path: Path to canonical_objects.json.
        lane: One of "CPS", "CME", "CSN", "StructuralEnvironment", "MediaContext".
        obj: Canonical object dict. Must contain the lane-appropriate ID field.
             Written EXACTLY as received — no field injection, mutation, or removal.

    Raises:
        RegistryAppendError: Duplicate canonical ID or invalid lane.
        LedgerWriteMismatchError: Read-back mismatch after atomic write.
        OSError: File system failure.
    """
    registry_path = Path(registry_path)

    if lane not in VALID_LANES:
        raise RegistryAppendError(
            f"Invalid lane '{lane}'. Must be one of: {sorted(VALID_LANES)}",
            lane=lane,
        )

    registry = _load_registry(registry_path)

    canonical_id = _get_canonical_id(obj, lane)

    # INV-4: Lane isolation guard
    # Only validates when object explicitly carries laneType.
    # RECs and other lane-untyped objects pass without check.
    obj_lane = obj.get("laneType")
    allowed_lane_types = _ALLOWED_LANE_TYPES[lane]
    if obj_lane is not None and obj_lane not in allowed_lane_types:
        raise LaneMismatchError(expected=lane, found=obj_lane)

    id_field = _LANE_ID_FIELD[lane]
    if _lane_contains_id(registry[lane], canonical_id, id_field):
        raise RegistryAppendError(
            f"Duplicate canonical ID '{canonical_id}' in lane '{lane}'. "
            f"In-place edits are prohibited. Registry is append-only.",
            lane=lane,
            canonical_id=canonical_id,
        )

    registry[lane].append(obj)

    registry[lane].sort(key=lambda lane_obj: lane_obj.get(id_field, ""))

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(registry_path, registry)


def registry_cardinality(registry_path, lane: str) -> int:
    """
    Return the number of canonical objects in the specified lane.
    Cardinality is ALWAYS derived from registry contents — no counters.

    Raises:
        RegistryAppendError: Invalid lane key.
        FileNotFoundError: Registry file does not exist.
    """
    if lane not in VALID_LANES:
        raise RegistryAppendError(
            f"Invalid lane '{lane}'. Must be one of: {sorted(VALID_LANES)}",
            lane=lane,
        )
    registry = _load_registry(Path(registry_path))
    return len(registry[lane])
