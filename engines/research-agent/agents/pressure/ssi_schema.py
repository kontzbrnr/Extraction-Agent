"""
pressure/ssi_schema.py

SSI Schema Constants — Phase 7.2

Module-level constants only. No logic.

Contract authority:
    STRUCTURAL-SIGNAL-INTERPRETER.md (SSI contract)

Invariant compliance:
    INV-1: All constants are module-level immutable literals.
    INV-5: No runtime-derived values. Identical across all replays.
"""

from __future__ import annotations

# ── Schema versions ────────────────────────────────────────────────────────────

SSI_SCHEMA_VERSION: str = "SSI-1.0"
PLO2_SCHEMA_VERSION: str = "PLO2-1.0"

# ── Agent version ──────────────────────────────────────────────────────────────

SSI_VERSION: str = "1.0"

# ── spaCy model configuration (INV-5) ─────────────────────────────────────────

SPACY_MODEL_NAME: str = "en_core_web_sm"
SPACY_MODEL_VERSION_PREFIX: str = "3.7"   # pinned major.minor

# ── Reason codes ───────────────────────────────────────────────────────────────

REJECT_PLO2_INVALID_INPUT: str = "REJECT_PLO2_INVALID_INPUT"
REJECT_PLO2_EXTRACTION_FAILED: str = "REJECT_PLO2_EXTRACTION_FAILED"

# ── Version assertion (INV-5) ─────────────────────────────────────────────────

_EXPECTED_SSI_VERSION: str = "1.0"
assert SSI_VERSION == _EXPECTED_SSI_VERSION, (
    f"SSI_VERSION drift: expected {_EXPECTED_SSI_VERSION!r}, got {SSI_VERSION!r}"
)
