"""
narrative/ane_dedup.py
Read-only ANE deduplication detector.
"""

from __future__ import annotations

from engines.research_engine.ledger.registry_reader import read_registry
from narrative.ane_id_format import validate_aneseed_id

ANE_DEDUP_VERSION: str = "ANE_DEDUP-1.0"
STATUS_NEW_CANONICAL: str = "NEW_CANONICAL"
STATUS_DUPLICATE: str = "DUPLICATE"
_ANE_LANE_KEY: str = "ANE"
_ANE_ID_FIELD: str = "eventSeedId"


def detect_ane_duplicate(event_seed_id: str, registry_path: str) -> tuple[str, dict | None]:
    """Detect whether ANE event_seed_id already exists in registry."""
    validate_aneseed_id(event_seed_id)
    registry = read_registry(registry_path)

    for obj in registry.get(_ANE_LANE_KEY, []):
        if obj.get(_ANE_ID_FIELD) == event_seed_id:
            return (STATUS_DUPLICATE, dict(obj))

    return (STATUS_NEW_CANONICAL, None)
