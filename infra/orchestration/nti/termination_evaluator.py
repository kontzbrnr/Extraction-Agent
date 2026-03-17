"""
nti/termination_evaluator.py

NTI termination condition evaluator.

Governing contracts:
  ORCHESTRATOR-EXECUTION-CONTRACT.md:
    Section V:  Termination Evaluation — "If NTI reports: allSurfacesSealed
                → terminationStatus = 'sealed'; exhaustionTriggered
                → terminationStatus = 'exhausted'. Persist state. Exit."
    Section II: "Before every action: Read GlobalState, Read SeasonRunState."
  NTI-CYCLE-EXECUTION.md:
    Section VII: Surface sealing removes surfaces from future extraction rotation.
    Section VIII: Exhaustion guard operates on structural distinctness.
    Section XII: "Ensure: ... Deterministic termination."

Condition definitions:
  allSurfacesSealed:
    All 8 rotation surfaces in nti_state.surfaceSealStatus are True.
    Computed from nti_state via get_sealed_surfaces().
    Fully deterministic from ledger state.
  exhaustionTriggered:
    Determined by the NTI audit layer (novelty collapse, weakest subcategory
    stagnation, duplication saturation — per Section VIII). No numerical
    threshold is defined in any contract. The evaluator receives this as a
    caller-provided bool, consistent with the caller-managed pattern used
    for sealed_surfaces (Phase 2.4), floor_threshold (Phase 2.6).

Priority:
  allSurfacesSealed is checked first. If both conditions are True,
  new_status = "sealed". Contract lists sealed before exhausted (Section V).

Ordering requirement (caller responsibility):
  Per roadmap Phase 2 validation: "TerminationEvaluator fires only after
  checkpoint write confirmed." This ordering is enforced by the orchestrator,
  not by this module. The evaluator does not validate checkpoint state.

INV-1 enforcement:
  preflight_read() called unconditionally on every invocation.
  get_sealed_surfaces() reads nti_state from disk on every call. No caching.

INV-5 enforcement:
  Result is a pure function of (nti_state.surfaceSealStatus,
  exhaustion_triggered). Identical inputs always produce identical output
  and identical ledger state. No timestamps or counters in evaluation path.

Write behavior:
  set_termination_status() called only when new_status != "running".
  Uses atomic write with read-back verification (delegated to season_state_manager).
  No write when neither condition is met.
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.research_engine.ledger.global_state_manager import preflight_read
from engines.research_engine.ledger.season_state_manager import set_termination_status
from infra.orchestration.nti.cycle_state_manager import get_sealed_surfaces
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER

_ALL_SURFACES: frozenset[str] = frozenset(SURFACE_ROTATION_ORDER)


@dataclass(frozen=True)
class TerminationDecision:
    """Immutable result of a termination evaluation.

    Attributes:
        all_surfaces_sealed: True if all 8 rotation surfaces were sealed in
                             nti_state at evaluation time.
        exhaustion_triggered: Echo of caller input — True if the NTI audit
                              reported structural exhaustion.
        new_status:          The resulting terminationStatus: "sealed",
                             "exhausted", or "running" (no change).
        persisted:           True if set_termination_status was called and
                             the ledger was updated. False when new_status
                             is "running" (no write performed).
    """

    all_surfaces_sealed: bool
    exhaustion_triggered: bool
    new_status: str
    persisted: bool


def evaluate_termination(
    ledger_root: str,
    active_run_path: str,
    exhaustion_triggered: bool,
) -> TerminationDecision:
    """Evaluate NTI termination conditions and persist the decision.

    Checks allSurfacesSealed (from nti_state) and exhaustion_triggered
    (caller-provided). If either condition is met, writes terminationStatus
    to season_state atomically and returns the result.

    Sealed takes priority over exhausted when both conditions are True.

    This function can only run successfully when terminationStatus == "running".
    preflight_read() enforces this — any other status raises PreflightError.

    INV-1: preflight_read and get_sealed_surfaces called on every invocation.
    INV-5: Pure function of (surfaceSealStatus, exhaustion_triggered).

    Args:
        ledger_root:          Path to the ledger root directory.
        active_run_path:      Relative path to the active run directory.
        exhaustion_triggered: True if the NTI audit determined that structural
                              exhaustion has occurred. Caller-provided — no
                              numerical threshold is defined in any contract.

    Returns:
        TerminationDecision with evaluation result and persist flag.

    Raises:
        PreflightError:        system halted or terminationStatus != "running".
        GlobalStateReadError:  global_state.json unreadable.
        SeasonStateReadError:  season state.json unreadable.
        NTIStateReadError:     nti_state.json unreadable.
        InvalidTerminationTransitionError: should not occur in normal flow
                               (preflight ensures "running" state), but
                               propagates if raised by set_termination_status.
    """
    # INV-1: re-read ledger on every call; result not used — validation only.
    preflight_read(ledger_root)

    # Compute allSurfacesSealed from nti_state (INV-1: fresh disk read).
    sealed = get_sealed_surfaces(ledger_root, active_run_path)
    all_surfaces_sealed = sealed == _ALL_SURFACES

    # Evaluate — sealed takes priority over exhausted.
    if all_surfaces_sealed:
        new_status = "sealed"
    elif exhaustion_triggered:
        new_status = "exhausted"
    else:
        new_status = "running"

    # Persist only if a terminal condition was reached.
    persisted = new_status != "running"
    if persisted:
        set_termination_status(ledger_root, active_run_path, new_status)

    return TerminationDecision(
        all_surfaces_sealed=all_surfaces_sealed,
        exhaustion_triggered=exhaustion_triggered,
        new_status=new_status,
        persisted=persisted,
    )
