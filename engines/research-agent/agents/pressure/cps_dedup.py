"""
pressure/cps_dedup.py

CPS Canonical Dedup Detector — Phase 8.3

Read-only pre-commit query: determines whether a given canonical
pressure signal ID is NEW_CANONICAL or DUPLICATE relative to the
current canonical registry.

Pipeline position (ORCHESTRATOR-EXECUTION-CONTRACT.md §XIV):
    PSTA (ID minted) → CPS Dedup Detector → CIV → Registry Commit

This module does NOT write to the registry.
Registry commit is handled by ledger.registry_writer.append_canonical_object.

Invariant compliance:
    INV-1: No module-level state. Registry path is a parameter.
           Every call reads from disk unconditionally via registry_reader.
    INV-3: Registry is never mutated. Returned matching object is a copy.
    INV-4: Only the CPS lane is accessed. Other lanes are ignored.

Contract authority:
    PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md v4 (§XIII-6, collision policy)
    ORCHESTRATOR-EXECUTION-CONTRACT.md §XIV-3
    Phase 8.3 rulings 2026-03-08
"""

from __future__ import annotations

from engines.research_engine.ledger.registry_reader import read_registry
from engines.research_agent.agents.pressure.cps_id_format import validate_cps_id
from engines.research_agent.agents.pressure.psta_schema import STATUS_DUPLICATE, STATUS_NEW_CANONICAL

# ── Constants ───────────────────────────────────────────────────────────────────

CPS_DEDUP_VERSION: str = "CPS_DEDUP-1.0"

_CPS_LANE_KEY: str = "CPS"
_CPS_ID_FIELD: str = "canonicalId"


# ── Public API ──────────────────────────────────────────────────────────────────

def detect_cps_duplicate(
    canonical_id: str,
    registry_path: str,
) -> tuple[str, dict | None]:
    """
    Determine whether canonical_id already exists in the CPS lane of the
    canonical registry.

    Read-only. Never writes to or modifies the registry file.
    Reads from disk on every call (INV-1 — no caching).

    Args:
        canonical_id:  CPS canonical ID to check. Must match
                       ^CPS_[a-f0-9]{64}$.
        registry_path: Path to canonical_objects.json.

    Returns:
        (STATUS_NEW_CANONICAL, None)
            — canonical_id is absent from the CPS lane.
        (STATUS_DUPLICATE, matching_object)
            — canonical_id already exists; matching_object is a shallow
              copy of the existing registry entry (INV-3: registry not
              exposed directly).

    Raises:
        ValueError:        canonical_id is empty, wrong type, or wrong format
                           (raised pre-IO).
        RegistryReadError: registry file is missing, invalid JSON, wrong
                           schemaVersion, or CPS lane key absent.
    """
    validate_cps_id(canonical_id)

    registry = read_registry(registry_path)
    cps_lane: list[dict] = registry[_CPS_LANE_KEY]

    for obj in cps_lane:
        if obj.get(_CPS_ID_FIELD) == canonical_id:
            return STATUS_DUPLICATE, dict(obj)   # INV-3: shallow copy

    return STATUS_NEW_CANONICAL, None
