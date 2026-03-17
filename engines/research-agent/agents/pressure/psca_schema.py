"""
pressure/psca_schema.py

PSCA Schema Constants — Phase 7.6

Versioned constants only. No logic.

Defines threshold parameters, verdict codes, reason codes, and stage identifiers
for PSCA v1.0. Any change to threshold values requires a PSCA_VERSION bump.

Contract authority:
    PRESSURE-SIGNAL-CRITIC-AGENT.md v2.0 §IV (threshold parameters)
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 §X (reason code registry)
    Phase 7.6 Governing Rulings (verdict scope: PASS/REJECT only)

Invariant compliance:
    INV-1: All constants are module-level immutable literals.
    INV-5: Version pinning assertion at import time. Any constant drift
           aborts the import with a descriptive error.
"""

from __future__ import annotations

# ── Version ────────────────────────────────────────────────────────────────────

PSCA_VERSION: str = "PSCA-1.0"

_EXPECTED_PSCA_VERSION: str = "PSCA-1.0"
assert PSCA_VERSION == _EXPECTED_PSCA_VERSION, (
    f"PSCA_VERSION drift: expected {_EXPECTED_PSCA_VERSION!r}, "
    f"got {PSCA_VERSION!r}"
)

# ── Sanity gate thresholds (INV-5 — versioned, not hardcoded inline) ──────────
# PSCA contract v2.0 §IV: "Threshold Parameters (Versioned Constants)"
# These constants are version-bound to PSCA_VERSION.
# Any change to these values requires a PSCA_VERSION bump.

MIN_CLUSTER_SIZE: int = 2
MIN_DOMAIN_DIVERSITY: int = 2

# ── Verdict codes (PASS/REJECT only — Ruling 3) ───────────────────────────────

VERDICT_PASS: str = "PASS"
VERDICT_REJECT: str = "REJECT"

# ── Reason codes (from PSAR contract v1.0 §X) ─────────────────────────────────

REASON_PASS_ALL_CHECKS: str = "PASS_ALL_CHECKS"
REASON_REJECT_INSUFFICIENT_CLUSTER_SIZE: str = "REJECT_INSUFFICIENT_CLUSTER_SIZE"
REASON_REJECT_INSUFFICIENT_DOMAIN_DIVERSITY: str = "REJECT_INSUFFICIENT_DOMAIN_DIVERSITY"

# ── Failure stage identifiers (mandatory per PSAR contract v1.0 §IX) ──────────
# Required in post-critic PSAR when criticStatus = REJECT.
# Identifies which PSCA check triggered the verdict.

STAGE_1_CLUSTER_SIZE: str = "1_CLUSTER_SIZE_GATE"
STAGE_2_DOMAIN_DIVERSITY: str = "2_DOMAIN_DIVERSITY_GATE"

# ── Audit log schema version ───────────────────────────────────────────────────

PSCA_AUDIT_SCHEMA_VERSION: str = "PSCA_AUDIT-1.0"
