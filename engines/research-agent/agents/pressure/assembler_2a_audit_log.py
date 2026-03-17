"""
pressure/assembler_2a_audit_log.py

2A PSAR Assembly Audit Log — Phase 7.2

Produce deterministic audit records for 2A gate decisions.

Contract authority:
    Structural Assembler Contract v1.1 §VI (determinism lock)
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 §VI (versioning strategy)

Invariant compliance:
    INV-1: Pure function. No module-level mutable state.
    INV-5: Deterministic audit record structure with version pinning.
"""

from __future__ import annotations
from engines.research_agent.agents.pressure.assembler_2a_schema import ASSEMBLER_2A_VERSION, PSAR_AUDIT_SCHEMA_VERSION


def make_2a_audit_log(
    input_record_count: int,
    proposed_count: int,
    rejected_cluster_count: int,
    decision: str,           # "PASS" | "PARTIAL" | "REJECT" | "EMPTY_INPUT"
    assembler_version: str = ASSEMBLER_2A_VERSION,
) -> dict:
    """
    Produce a 2A_AUDIT-1.0 audit record for 2A gate decision.
    
    Decision rules:
        EMPTY_INPUT  = input_record_count == 0
        PASS         = proposed_count > 0 and rejected_cluster_count == 0
        PARTIAL      = proposed_count > 0 and rejected_cluster_count > 0
        REJECT       = proposed_count == 0 and input_record_count > 0
    
    Args:
        input_record_count: Number of PLO-2.0 records received
        proposed_count: Number of PSAR v1.0 proposals emitted
        rejected_cluster_count: Number of clusters/records rejected
        decision: Gate outcome
        assembler_version: Agent version (defaults to ASSEMBLER_2A_VERSION)
    
    Returns:
        2A_AUDIT-1.0 dict
    
    Example:
        make_2a_audit_log(
            input_record_count=5,
            proposed_count=2,
            rejected_cluster_count=0,
            decision="PASS"
        )
    """
    return {
        "inputRecordCount": input_record_count,
        "proposedCount": proposed_count,
        "rejectedClusterCount": rejected_cluster_count,
        "decision": decision,
        "assemblerVersion": assembler_version,
        "schemaVersion": PSAR_AUDIT_SCHEMA_VERSION,
    }
