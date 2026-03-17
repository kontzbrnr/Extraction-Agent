"""
mcp/mcr_dedup.py

MCR Cross-Run Dedup Detector — Phase 10.5

Read-only pre-commit query: determines whether a given MCR canonical ID
is NEW_CANONICAL or DUPLICATE relative to the current MediaContext
registry lane.

This module does NOT write to the registry.

Pipeline position:
    MCMA (ID minted) → MCR Dedup Detector → CIV → Registry Commit

Invariants:
    INV-1: No module-level state. Registry path is a parameter.
           Reads from disk unconditionally on every call.
    INV-3: Registry is never mutated. Matching object returned as shallow copy.
    INV-4: Only the MediaContext lane is accessed.
"""

from __future__ import annotations

from engines.research_engine.ledger.registry_reader import read_registry
from engines.research_agent.agents.mcp.mcma_schema import STATUS_DUPLICATE, STATUS_NEW_CANONICAL
from engines.research_agent.agents.mcp.mcr_id_format import validate_mcr_id

MCR_DEDUP_VERSION: str = "MCR_DEDUP-1.0"

_MCR_LANE_KEY: str = "MediaContext"
_MCR_ID_FIELD: str = "id"


def detect_mcr_duplicate(
    canonical_id: str,
    registry_path: str,
) -> tuple[str, dict | None]:
    """Determine whether canonical_id already exists in the MediaContext lane.

    Read-only. Never writes to or modifies the registry file.
    Reads from disk on every call (INV-1 — no caching).

    Args:
        canonical_id:  MCR canonical ID to check. Must match
                       ^MCR_[a-f0-9]{64}$.
        registry_path: Path to canonical_objects.json.

    Returns:
        (STATUS_NEW_CANONICAL, None)
            — canonical_id is absent from the MediaContext lane.
        (STATUS_DUPLICATE, matching_object)
            — canonical_id already exists; matching_object is a shallow
              copy of the existing registry entry (INV-3).

    Raises:
        ValueError:       canonical_id is empty, wrong type, or wrong format.
        RegistryReadError: registry file missing, invalid JSON, or schema invalid.
    """
    validate_mcr_id(canonical_id)

    registry = read_registry(registry_path)
    media_lane: list[dict] = registry[_MCR_LANE_KEY]

    for obj in media_lane:
        if obj.get(_MCR_ID_FIELD) == canonical_id:
            return STATUS_DUPLICATE, dict(obj)   # INV-3: shallow copy

    return STATUS_NEW_CANONICAL, None
