"""
openclaw — outer execution shell for the research agent runtime.

Contract authority: contracts_md/OPENCLAW-RUNTIME-CONTRACT.md v1.0

Role (§I):
    Trigger-only shell. Does not interpret. Does not make ontology
    decisions. Only triggers orchestrator actions.

Invocation rule (§II):
    One invocation = one orchestrator action. No internal loops.

Authority chain (§III):
    Sole downstream call: orchestrator_run().
    No direct calls to PLO-E, IAV, PSTA, EMI, media mint, or CIV.
"""

from infra.orchestration.openclaw.binding import BindingViolationError, verify_binding_integrity
from infra.orchestration.openclaw.concurrency_guard import ConcurrencyViolationError
from infra.orchestration.openclaw.entrypoint import run_research_agent
from infra.orchestration.openclaw.invocation_logger import (
    compute_ledger_state_hash,
    write_invocation_log,
)
from infra.orchestration.openclaw.ledger_gate import LedgerNotReachableError, assert_ledger_reachable
from infra.orchestration.openclaw.params import InvocationParams

__all__ = [
    "run_research_agent",
    "InvocationParams",
    "assert_ledger_reachable",
    "LedgerNotReachableError",
    "compute_ledger_state_hash",
    "write_invocation_log",
    "verify_binding_integrity",
    "BindingViolationError",
    "ConcurrencyViolationError",
]
