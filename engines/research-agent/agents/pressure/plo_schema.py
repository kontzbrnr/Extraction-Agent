"""
pressure/plo_schema.py

PLO Schema Constants — Phase 7.1

Defines the PLO-1.0 schema version, the closed set of valid
perceptual expansion domains, and observation count bounds.

Domain names are the prose labels used by PLO-E v2 (PDF §III).
These differ from the registry snake_case enum values used in PSAR/PSTA.
Mapping from PLO domain names to registry enum values is performed by
2A (PSAR Assembly + Enum Normalization), not by PLO-E.

Contract authority:
    PLO-E v2 PDF §III (valid expansion domains)
    PLO-E v2 PDF §II  (observation count bounds)
    PRESSURE-LEGIBLE-OBSERVATION-EXPANSION-AGENT.md v2.0 §V

Invariant compliance:
    INV-1: All constants are module-level immutable literals or frozensets.
    INV-5: No runtime-derived values. Identical across all replays.
"""

from __future__ import annotations

# ── Schema version ─────────────────────────────────────────────────────────────

# PLO-1.0: pre-2A, pre-PSCA, pre-canonical. No enum fields. No canonical ID.
# Increment only on structural schema change.
PLO_SCHEMA_VERSION: str = "PLO-1.0"

# ── Agent version ──────────────────────────────────────────────────────────────

PLO_E_VERSION: str = "1.0"

# ── Observation count bounds ───────────────────────────────────────────────────

# PLO-E v2 PDF §II: minimum 4, maximum 10 observations per seed.
PLO_MIN_OBSERVATIONS: int = 4
PLO_MAX_OBSERVATIONS: int = 10

# ── Valid perceptual expansion domains (INV-1) ─────────────────────────────────

# Closed set of domain labels as specified in PLO-E v2 PDF §III.
# Each PLO observation must occupy exactly one of these domains.
# No two observations within a single PLO may share a domain (INV-4 / domain isolation).
VALID_DOMAINS: frozenset = frozenset({
    "Structural Configuration",
    "Authority Distribution",
    "Timing & Horizon",
    "Preparation & Installation",
    "Access & Information",
    "Absence / Omission",
    "Environmental Constraints",
    "Public Legibility",
    "Resource Allocation",
    "Redundancy / Fragility",
})
