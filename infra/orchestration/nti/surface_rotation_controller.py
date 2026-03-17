"""
nti/surface_rotation_controller.py

Deterministic NTI surface rotation controller.

Governing contracts:
  NTI-CYCLE-EXECUTION.md:
    Section III: Time Surface is a coverage categorization dimension.
    Section VII: Sealed surfaces are removed from future extraction rotation.
    Section XI:  NTI is rotation-driven and surface-balanced.
  ORCHESTRATOR-EXECUTION-CONTRACT.md:
    Section II:  "Before every action: Read GlobalState, Read SeasonRunState."

Schema gap (documented):
  season_state.json does not contain currentSurface or sealedSurfaces fields.
  The roadmap references these as NTI cycle state fields (currentSurface,
  surfaceSealStatus) absent from current schemas. Until a dedicated NTI cycle
  state schema is introduced, current_surface and sealed_surfaces are
  caller-managed inputs. This is a known gap pending Phase 2.x schema extension.

INV-1 enforcement:
  preflight_read() is called unconditionally on every invocation.
  Ledger state is never cached between calls.

INV-5 enforcement:
  Selection is a pure function of current_surface + sealed_surfaces +
  SURFACE_ROTATION_ORDER. Identical inputs always produce identical output.
  No timestamps, counters, or runtime variation in the selection path.

Read-only:
  This module does not write to any ledger file.
  Quota floor enforcement is a separate component (SurfaceQuotaFloor enforcer)
  and is NOT implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.research_engine.ledger.global_state_manager import preflight_read
from infra.orchestration.nti.surface_rotation_index import (
    SURFACE_ROTATION_ORDER,
    SurfaceRotationError,
    next_surface,
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SurfaceSelection:
    """Immutable result of a surface selection invocation.

    Attributes:
        selected_surface: The next surface to use, or None if all are sealed.
        current_surface:  The surface that was active at selection time
                          (echo of caller input — for audit/logging).
        active_count:     Number of surfaces available for rotation
                          (total surfaces minus sealed count).
        sealed_count:     Number of surfaces in the sealed set at selection time.
    """

    selected_surface: str | None
    current_surface: str
    active_count: int
    sealed_count: int


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------


def select_next_surface(
    ledger_root: str,
    active_run_path: str,
    current_surface: str,
    sealed_surfaces: frozenset[str] | set[str] = frozenset(),
) -> SurfaceSelection:
    """Select the next NTI rotation surface deterministically.

    Performs preflight_read before any selection to enforce:
      - systemStatus == "operational"
      - terminationStatus == "running"
    If either check fails, PreflightError propagates — no surface is selected.

    Selection algorithm (INV-5 — deterministic):
      next_surface(current_surface, sealed_surfaces) from SurfaceRotationIndex.
      Identical inputs always produce identical output.

    Schema gap note:
      current_surface and sealed_surfaces are caller-provided because
      season_state.json does not persist these fields (documented gap).
      The caller (NTI orchestrator) is responsible for tracking surface state
      until a dedicated NTI cycle state schema is introduced.

    Args:
        ledger_root:      Path to the ledger root directory.
        active_run_path:  Relative path to the active run directory.
        current_surface:  The surface currently active. Must be a valid
                          surface name from SURFACE_ROTATION_ORDER.
        sealed_surfaces:  Set of surface names removed from rotation by NTI
                          sealing logic. Unknown names are ignored.

    Returns:
        SurfaceSelection with the next surface (or None if all sealed).

    Raises:
        PreflightError:       system halted or terminationStatus != "running".
        GlobalStateReadError: global_state.json unreadable.
        SeasonStateReadError: season state.json unreadable.
        SurfaceRotationError: current_surface is not a valid surface name.
    """
    # --- Preflight (INV-1: re-read ledger on every call) --------------------
    # Raises PreflightError if system is not operational or not running.
    # Result is not used for selection — validation only.
    preflight_read(ledger_root)

    # --- Deterministic surface selection (INV-5) ----------------------------
    sealed = frozenset(sealed_surfaces)
    selected = next_surface(current_surface, sealed)

    total = len(SURFACE_ROTATION_ORDER)
    # Count only valid sealed surfaces for reporting accuracy
    valid_sealed_count = sum(
        1 for s in sealed if s in frozenset(SURFACE_ROTATION_ORDER)
    )

    return SurfaceSelection(
        selected_surface=selected,
        current_surface=current_surface,
        active_count=total - valid_sealed_count,
        sealed_count=valid_sealed_count,
    )
