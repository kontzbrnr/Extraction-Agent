"""
pressure/assembler_2a_rejection_handler.py

2A PSAR Assembly Rejection Handler — Phase 7.2

Produce rejection records for 2A assembly failures.

Contract authority:
    Structural Assembler Contract v1.1 §V (explicit prohibitions)
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 §VIII (diagnostic metadata)

Invariant compliance:
    INV-1: Pure function. No module-level mutable state.
    INV-5: Deterministic rejection record structure.
"""

from __future__ import annotations


def make_2a_rejection(
    reason_code: str,
    reason: str,
    cluster_key: tuple[str, str, str] | None = None,
    structural_source_ids: list[str] | None = None,
) -> dict:
    """
    Produce a REJECTION-1.0 record for 2A assembly failure.
    
    Args:
        reason_code: Deterministic reason code (e.g., REJECT_2A_ENUM_RESOLUTION_FAILED)
        reason: Human-readable explanation string
        cluster_key: Optional (actorGroup, actionType, objectRole) tuple
        structural_source_ids: Optional list of ploID values that failed
    
    Returns:
        REJECTION-1.0 dict
    
    Example:
        make_2a_rejection(
            "REJECT_2A_ENUM_RESOLUTION_FAILED",
            "Normalization failed for fields: ['actorGroup']",
            cluster_key=("unknown_actor", "retained_control", "play_calling"),
            structural_source_ids=["PLO2_abc123"]
        )
    """
    return {
        "reasonCode": reason_code,
        "reason": reason,
        "clusterKey": list(cluster_key) if cluster_key else None,
        "structuralSourceIDs": sorted(structural_source_ids) if structural_source_ids else None,
        "schemaVersion": "REJECTION-1.0",
    }
