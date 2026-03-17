"""
nti/surface_rotation_index.py

Frozen, deterministic NTI surface rotation index.

Governing contracts:
  NTI-CYCLE-EXECUTION.md:
    Section III:  Time Surface is a coverage categorization dimension.
    Section VII:  Sealed surfaces are removed from future extraction rotation.
    Section XI:   NTI is rotation-driven and surface-balanced.
    Section XII:  Deterministic termination; coverage breadth enforced.
  TIME-RECURRENCE-PARTITION-DOCTRINE.md:
    Surfaces affect scheduling only — never canonical identity.
    "Cycle metadata SHALL NEVER participate in canonical identity in any lane."

Surface source:
  enums/narrative/registry.json → timeBucketRegistry.tierA.values
  Tier A tokens define the NTI time surfaces.
  Their list order is the canonical rotation order.

INV-5 enforcement:
  SURFACE_ROTATION_ORDER is a module-level frozen tuple constant.
  All functions are pure: identical inputs → identical outputs, always.
  No disk I/O. No state reads. No side effects.

Sealing semantics (NTI Section VII):
  A sealed surface is removed from future extraction rotation.
  Sealed surfaces are supplied by the caller — this module does not
  track sealing state. It computes rotation given a sealed set.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Frozen rotation order (source: enums/narrative/registry.json Tier A)
# ---------------------------------------------------------------------------

SURFACE_ROTATION_ORDER: tuple[str, ...] = (
    "offseason",
    "training_camp",
    "preseason",
    "regular_season",
    "playoffs",
    "championship_week",
    "draft_period",
    "free_agency_period",
)

# Derived lookup structures — computed once at module import, never mutated.
_SURFACE_SET: frozenset[str] = frozenset(SURFACE_ROTATION_ORDER)
_SURFACE_POSITION: dict[str, int] = {
    surface: idx for idx, surface in enumerate(SURFACE_ROTATION_ORDER)
}

# Total number of surfaces — used in modular arithmetic for wrap-around.
_N: int = len(SURFACE_ROTATION_ORDER)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class SurfaceRotationError(Exception):
    """Raised when an unrecognised surface name is passed to a query function."""

    def __init__(self, surface: str) -> None:
        super().__init__(
            f"unknown surface: '{surface}'. "
            f"Valid surfaces: {list(SURFACE_ROTATION_ORDER)}"
        )
        self.surface = surface


# ---------------------------------------------------------------------------
# Query functions (all pure — INV-5)
# ---------------------------------------------------------------------------


def is_valid_surface(surface: str) -> bool:
    """Return True if surface is a member of SURFACE_ROTATION_ORDER.

    Pure function. No I/O. No side effects.
    """
    return surface in _SURFACE_SET


def surface_position(surface: str) -> int:
    """Return the 0-based index of surface in SURFACE_ROTATION_ORDER.

    Args:
        surface: Surface name to look up.

    Returns:
        Integer in range [0, 7].

    Raises:
        SurfaceRotationError: surface is not in SURFACE_ROTATION_ORDER.
    """
    if surface not in _SURFACE_SET:
        raise SurfaceRotationError(surface)
    return _SURFACE_POSITION[surface]


def active_rotation(sealed: frozenset[str] | set[str]) -> tuple[str, ...]:
    """Return all non-sealed surfaces in canonical rotation order.

    Preserves SURFACE_ROTATION_ORDER sequence — only sealed surfaces
    are removed. Returns an empty tuple if all surfaces are sealed.

    Args:
        sealed: Set of sealed surface names. Unknown names are ignored.
                Caller is responsible for supplying valid names.

    Returns:
        Ordered tuple of active (non-sealed) surface names.

    Pure function — same sealed input always produces same output (INV-5).
    """
    return tuple(s for s in SURFACE_ROTATION_ORDER if s not in sealed)


def next_surface(
    current: str,
    sealed: frozenset[str] | set[str] = frozenset(),
) -> str | None:
    """Return the next active surface after current in rotation order.

    Traverses SURFACE_ROTATION_ORDER from current+1, wrapping around.
    Skips sealed surfaces. current itself may be sealed — its position
    is used as the start of the search regardless.

    If only one non-sealed surface exists and it is current, returns
    current (rotation stays on the only available surface).

    Args:
        current: The surface currently active. Must be a valid surface name.
        sealed:  Set of sealed surface names. Unknown names are ignored.

    Returns:
        The next non-sealed surface name, or None if all surfaces are sealed.

    Raises:
        SurfaceRotationError: current is not in SURFACE_ROTATION_ORDER.

    Pure function — same inputs always produce same output (INV-5).
    """
    if current not in _SURFACE_SET:
        raise SurfaceRotationError(current)

    start: int = _SURFACE_POSITION[current]

    for offset in range(1, _N + 1):
        candidate = SURFACE_ROTATION_ORDER[(start + offset) % _N]
        if candidate not in sealed:
            return candidate

    # All surfaces sealed — no valid next surface.
    return None
