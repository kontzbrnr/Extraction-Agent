"""
nti/surface_quota_floor_enforcer.py

Surface coverage quota floor enforcer.

Governing contracts:
  NTI-CYCLE-EXECUTION.md:
    Section III:  Time Surface affects "Subcategory floor enforcement".
    Section XI:   NTI is "surface-balanced" and ensures "Coverage breadth".
    Section XII:  "Ensure: Coverage breadth, Surface floor enforcement,
                  Structural distinctness, Deterministic termination."
  ORCHESTRATOR-EXECUTION-CONTRACT.md:
    Section IV Step 4: subcategoryCounts updated at end-of-batch boundary.

Data source:
  season_state.subcategoryCounts — "NTI surface subcategory coverage counts.
  Keys are surface names. Values are integer counts. Updated at end-of-batch
  boundary." (season_state.schema.json).

  NOT nti_state.exhaustionCounters — exhaustionCounters tracks structural
  saturation detection events (novelty collapse, weakest subcategory
  stagnation, duplication saturation per NTI-CYCLE-EXECUTION.md Section VIII).
  Exhaustion is structural saturation — not chronological.
  Floor enforcement compares extraction coverage counts against a minimum —
  that is subcategoryCounts, not exhaustion events.

Schema gap (documented):
  subcategoryQuotaFloors is listed as an NTI cycle state field in the
  Execution Roadmap (Phase 2 components table) alongside currentSurface,
  surfaceSealStatus, and noveltyCollapseDetector. However:
    - subcategoryQuotaFloors has zero definition in any contract, schema,
      or code file.
    - noveltyCollapseDetector has zero hits in all contracts and code.
    - Neither field was added to nti_cycle_state.schema.json in Phase 2.5
      because no contract defines their type, structure, or storage location.

  Until a contract defines subcategoryQuotaFloors storage location and type,
  floor_threshold is a caller-provided argument. This is consistent with the
  pattern established for current_surface and sealed_surfaces in Phase 2.4.

INV-1 enforcement:
  preflight_read() is called unconditionally on every invocation.
  read_season_state() is called fresh on every invocation.
  subcategoryCounts is never cached between calls.

INV-5 enforcement:
  Floor check is a pure function of (subcategoryCounts, floor_threshold,
  surfaces). Identical inputs always produce identical output. No timestamps,
  no run-order dependence, no runtime variation in the enforcement path.

Read-only:
  This module does not write to any ledger file.
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.research_engine.ledger.global_state_manager import preflight_read, read_season_state
from infra.orchestration.nti.surface_rotation_index import SURFACE_ROTATION_ORDER

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALL_SURFACES: frozenset[str] = frozenset(SURFACE_ROTATION_ORDER)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FloorCheckResult:
    """Immutable result of a surface quota floor check.

    Partitions checked surfaces into exactly two disjoint sets:
      - met_floor:   surfaces whose coverage count >= floor_threshold
      - below_floor: surfaces whose coverage count <  floor_threshold

    A surface absent from season_state.subcategoryCounts is treated as
    count=0. If floor_threshold == 0, all checked surfaces are in met_floor
    because 0 >= 0.

    Attributes:
        below_floor:     Surfaces that have not yet met the coverage floor.
                         frozenset — ordering is not meaningful.
        met_floor:       Surfaces that have met or exceeded the coverage floor.
                         frozenset — ordering is not meaningful.
        floor_threshold: The caller-provided threshold used for this check.
                         Documented as caller-managed (schema gap — see module
                         docstring).
        surface_counts:  Raw per-surface counts read from season_state.
                         subcategoryCounts, filtered to the checked surfaces.
                         Absent surfaces are represented as 0.
                         Do not mutate.
    """

    below_floor: frozenset[str]
    met_floor: frozenset[str]
    floor_threshold: int
    surface_counts: dict[str, int]


# ---------------------------------------------------------------------------
# Enforcer
# ---------------------------------------------------------------------------


def check_surface_floors(
    ledger_root: str,
    active_run_path: str,
    floor_threshold: int,
    surfaces: frozenset[str] | set[str] | None = None,
) -> FloorCheckResult:
    """Check whether NTI time surfaces have met the minimum coverage floor.

    Reads season_state.subcategoryCounts from disk and compares each surface's
    count against floor_threshold. Returns a FloorCheckResult that partitions
    the checked surfaces into met_floor and below_floor sets.

    The caller decides what action to take based on the result. This function
    does not gate sealing, modify rotation, or write any ledger state.

    INV-1: preflight_read and read_season_state called unconditionally on
           every invocation. No caching.
    INV-5: Pure function of (subcategoryCounts, floor_threshold, surfaces).
           Identical inputs always produce identical output.

    Args:
        ledger_root:      Path to the ledger root directory.
        active_run_path:  Relative path to the active run directory
                          (e.g. "runs/2024_OFFSEASON").
        floor_threshold:  Minimum coverage count a surface must have reached
                          to be in met_floor. Must be >= 0. Caller-provided
                          (no stored contract for this value — documented
                          schema gap).
        surfaces:         Set of surface names to check. Only valid surface
                          names from SURFACE_ROTATION_ORDER are included in
                          the result; unknown names are silently excluded.
                          If None, defaults to all 8 rotation surfaces.

    Returns:
        FloorCheckResult with below_floor, met_floor, floor_threshold, and
        surface_counts for all checked surfaces.

    Raises:
        ValueError:           floor_threshold < 0 (raised pre-IO, before any
                              ledger reads).
        PreflightError:       system halted or terminationStatus != "running".
        GlobalStateReadError: global_state.json unreadable.
        SeasonStateReadError: season state.json unreadable.
    """
    # --- Pre-IO validation -------------------------------------------------
    if floor_threshold < 0:
        raise ValueError(
            f"floor_threshold must be >= 0, got {floor_threshold!r}"
        )

    # --- Preflight (INV-1: re-read ledger on every call) -------------------
    # Result not used — validation only.
    preflight_read(ledger_root)

    # --- Read coverage counts from season state (INV-1: no caching) --------
    season_state = read_season_state(ledger_root, active_run_path)
    raw_counts: dict[str, int] = season_state.get("subcategoryCounts", {})

    # --- Resolve surfaces to check -----------------------------------------
    # Unknown surface names are excluded from the result (consistent with the
    # sealed_surfaces pattern in Phase 2.4).
    if surfaces is None:
        checked: frozenset[str] = _ALL_SURFACES
    else:
        checked = frozenset(s for s in surfaces if s in _ALL_SURFACES)

    # --- Floor check (INV-5: pure function of counts + threshold) ----------
    below: set[str] = set()
    met: set[str] = set()
    surface_counts: dict[str, int] = {}

    for surface in checked:
        count = raw_counts.get(surface, 0)
        surface_counts[surface] = count
        if count >= floor_threshold:
            met.add(surface)
        else:
            below.add(surface)

    return FloorCheckResult(
        below_floor=frozenset(below),
        met_floor=frozenset(met),
        floor_threshold=floor_threshold,
        surface_counts=surface_counts,
    )
