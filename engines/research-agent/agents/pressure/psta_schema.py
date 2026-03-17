"""
pressure/psta_schema.py

PSTA Schema Constants — Phase 8.2

Versioned constants only. No logic.

Contract authority: PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md v4
Governance: Phase 8.2 rulings 2026-03-08

Invariant compliance:
    INV-1: All constants are module-level immutable literals.
    INV-5: Version-pinning assertion at import time. Any constant
           drift aborts the import with a descriptive error.
"""

from __future__ import annotations

# ── Agent version ───────────────────────────────────────────────────────────────
PSTA_VERSION: str = "PSTA-1.0"

_EXPECTED_PSTA_VERSION: str = "PSTA-1.0"
assert PSTA_VERSION == _EXPECTED_PSTA_VERSION, (
    f"PSTA_VERSION drift: expected {_EXPECTED_PSTA_VERSION!r}, "
    f"got {PSTA_VERSION!r}"
)

# ── Schema / contract labels ────────────────────────────────────────────────────
PSTA_CPS_SCHEMA_VERSION: str = "CPS-1.0"      # schemaVersion field in each CPS object
PSTA_CONTRACT_VERSION: str   = "PSTA_v4"      # contractVersion field in each CPS object
PSTA_LANE_TYPE: str          = "PRESSURE"     # laneType field

# ── Dedup status codes (RULING 4) ──────────────────────────────────────────────
STATUS_NEW_CANONICAL: str = "NEW_CANONICAL"
STATUS_DUPLICATE: str     = "DUPLICATE"

# ── Rejection reason codes ──────────────────────────────────────────────────────
REJECT_PSTA_SCHEMA_INVALID: str = "REJECT_PSTA_SCHEMA_INVALID"

# ── Audit ───────────────────────────────────────────────────────────────────────
PSTA_AUDIT_SCHEMA_VERSION: str = "PSTA_AUDIT-1.0"

# ── Default enum registry version ──────────────────────────────────────────────
PSTA_DEFAULT_ENUM_REGISTRY_VERSION: str = "ENUM_v1.0"
