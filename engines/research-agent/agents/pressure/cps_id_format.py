"""
pressure/cps_id_format.py

CPS Canonical ID Format Lock — Phase 8.5

Centralises the canonical pressure signal ID format constants, compiled
pattern, and validation function so that no other module carries a local
copy of the regex or format definition.

Before this module, the CPS_[a-f0-9]{64} pattern was duplicated in:
  * pressure/cps_fingerprint.py   (_CPS_ID_PREFIX)
  * pressure/cps_dedup.py         (_CPS_ID_PATTERN)
  * pressure/cps_constructor.py   (_CANONICAL_ID_PATTERN)

Phase 8.5 consolidates them here. All consumers import from this module.

Format (PSTA v4 §V / CPS_FINGERPRINT_V1 authority):
  CPS_ID_PREFIX       "CPS_"           — 4 characters
  CPS_ID_HEX_LENGTH   64               — lowercase SHA-256 hex
  CPS_ID_TOTAL_LENGTH 68               — 4 + 64
  CPS_ID_PATTERN      ^CPS_[a-f0-9]{64}$

Invariant compliance:
  INV-2: This module publishes the authoritative format; it does NOT
         derive canonical IDs. Derivation remains in cps_fingerprint.py.
  INV-3: No mutable module-level state.
  INV-5: Pattern and constants are pinned; import-time assertions detect
         accidental drift at process startup.
"""

from __future__ import annotations

import re


# ── Version ─────────────────────────────────────────────────────────────────────

CPS_ID_FORMAT_VERSION: str = "CPS_ID_FORMAT-1.0"


# ── Format constants ─────────────────────────────────────────────────────────────

CPS_ID_PREFIX: str = "CPS_"
CPS_ID_HEX_LENGTH: int = 64
CPS_ID_TOTAL_LENGTH: int = 68      # len("CPS_") + 64


# ── Compiled pattern ─────────────────────────────────────────────────────────────

CPS_ID_PATTERN: re.Pattern[str] = re.compile(r"^CPS_[a-f0-9]{64}$")


# ── Import-time assertions — format lock ─────────────────────────────────────────
# These fire at process startup and catch accidental constant drift before any
# CPS ID is validated or minted.

assert CPS_ID_FORMAT_VERSION == "CPS_ID_FORMAT-1.0", (
    f"CPS_ID_FORMAT_VERSION drift: {CPS_ID_FORMAT_VERSION!r}"
)
assert CPS_ID_PREFIX == "CPS_", (
    f"CPS_ID_PREFIX drift: {CPS_ID_PREFIX!r}"
)
assert CPS_ID_HEX_LENGTH == 64, (
    f"CPS_ID_HEX_LENGTH drift: {CPS_ID_HEX_LENGTH!r}"
)
assert CPS_ID_TOTAL_LENGTH == len(CPS_ID_PREFIX) + CPS_ID_HEX_LENGTH, (
    f"CPS_ID_TOTAL_LENGTH inconsistency: "
    f"{CPS_ID_TOTAL_LENGTH} != {len(CPS_ID_PREFIX)} + {CPS_ID_HEX_LENGTH}"
)
# Known-good: minimal valid ID must match
assert CPS_ID_PATTERN.match("CPS_" + "a" * 64), (
    "CPS_ID_PATTERN does not match a known-good valid CPS ID"
)
# Known-bad: wrong prefix must not match
assert not CPS_ID_PATTERN.match("cps_" + "a" * 64), (
    "CPS_ID_PATTERN incorrectly matches a known-bad lowercase-prefix ID"
)


# ── Public validator ─────────────────────────────────────────────────────────────

def validate_cps_id(canonical_id: str) -> None:
    """
    Raise ValueError if canonical_id does not conform to CPS_FINGERPRINT_V1
    output format: "CPS_" followed by exactly 64 lowercase hex characters.

    Returns None on success. Raised pre-IO in all consumers so no disk read
    is wasted on a malformed ID.

    Args:
        canonical_id: Value to validate.

    Raises:
        ValueError: canonical_id is not a non-empty str, or does not match
                    ^CPS_[a-f0-9]{64}$.
    """
    if not isinstance(canonical_id, str) or not canonical_id:
        raise ValueError(
            f"canonical_id must be a non-empty string, "
            f"got {type(canonical_id).__name__!r}"
        )
    if not CPS_ID_PATTERN.match(canonical_id):
        raise ValueError(
            f"canonical_id does not match CPS_FINGERPRINT_V1 format "
            f"(CPS_<64 lowercase hex chars>): {canonical_id!r}"
        )
