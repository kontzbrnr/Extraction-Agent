"""
pressure/pressure_pipeline_schema.py

Pressure Pipeline Gate Schema Constants — Phase 7.7

Version constant and rejection schema identifier for the pressure lane
pipeline gate. No logic.

Contract authority:
    ORCHESTRATOR-EXECUTION-CONTRACT.md §XIV (pipeline ordering)
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0 §II (pipeline position)

Invariant compliance:
    INV-1: Module-level immutable constants only.
    INV-5: Version pinning assertion at import time.
"""

from __future__ import annotations

PRESSURE_PIPELINE_GATE_VERSION: str = "1.0"

_EXPECTED_VERSION: str = "1.0"
assert PRESSURE_PIPELINE_GATE_VERSION == _EXPECTED_VERSION, (
    f"PRESSURE_PIPELINE_GATE_VERSION drift: expected {_EXPECTED_VERSION!r}, "
    f"got {PRESSURE_PIPELINE_GATE_VERSION!r}"
)

# Rejection schema identifier for PSAR validation failures caught at gate level
PSAR_GATE_VALIDATION_SCHEMA_VERSION: str = "PSAR_GATE_REJECTION-1.0"

# Reason code for PSARs that fail validate_psar before reaching PSCA
REJECT_PSAR_GATE_SCHEMA_INVALID: str = "REJECT_PSAR_GATE_SCHEMA_INVALID"
