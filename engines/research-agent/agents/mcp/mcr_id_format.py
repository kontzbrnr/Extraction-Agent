"""
mcp/mcr_id_format.py

MCR Canonical ID Format Lock — Phase 10.4

Centralises the canonical Media Context Record ID format constants,
compiled pattern, and validation function.

Format (MCR_FINGERPRINT_V1 / Ruling 10.4-A):
    MCR_ID_PREFIX       "MCR_"           — 4 characters
    MCR_ID_HEX_LENGTH   64               — lowercase SHA-256 hex
    MCR_ID_TOTAL_LENGTH 68               — 4 + 64
    MCR_ID_PATTERN      ^MCR_[a-f0-9]{64}$

Namespace registration:
    MCR_ is registered in DETERMINISTIC-GLOBAL-IDENTITY-FRAMEWORK.md §III
    alongside CPS_, CME_, CSN_.

Invariant compliance:
    INV-2: Publishes the authoritative format. Does NOT derive canonical IDs.
           Derivation resides exclusively in mcr_fingerprint.py.
    INV-5: All constants pinned. Import-time assertions detect drift at
           process startup before any MCR ID is validated or minted.
"""

from __future__ import annotations

import re

# ── Version ───────────────────────────────────────────────────────────────────

MCR_ID_FORMAT_VERSION: str = "MCR_ID_FORMAT-1.0"

# ── Format constants ──────────────────────────────────────────────────────────

MCR_ID_PREFIX: str = "MCR_"
MCR_ID_HEX_LENGTH: int = 64
MCR_ID_TOTAL_LENGTH: int = 68      # len("MCR_") + 64

# ── Compiled pattern ──────────────────────────────────────────────────────────

MCR_ID_PATTERN: re.Pattern[str] = re.compile(r"^MCR_[a-f0-9]{64}$")

# ── Import-time assertions — format lock ──────────────────────────────────────

assert MCR_ID_FORMAT_VERSION == "MCR_ID_FORMAT-1.0", (
    f"MCR_ID_FORMAT_VERSION drift: {MCR_ID_FORMAT_VERSION!r}"
)
assert MCR_ID_PREFIX == "MCR_", (
    f"MCR_ID_PREFIX drift: {MCR_ID_PREFIX!r}"
)
assert MCR_ID_HEX_LENGTH == 64, (
    f"MCR_ID_HEX_LENGTH drift: {MCR_ID_HEX_LENGTH!r}"
)
assert MCR_ID_TOTAL_LENGTH == len(MCR_ID_PREFIX) + MCR_ID_HEX_LENGTH, (
    f"MCR_ID_TOTAL_LENGTH inconsistency: "
    f"{MCR_ID_TOTAL_LENGTH} != {len(MCR_ID_PREFIX)} + {MCR_ID_HEX_LENGTH}"
)
# Known-good: valid MCR ID must match.
assert MCR_ID_PATTERN.match("MCR_" + "a" * 64), (
    "MCR_ID_PATTERN does not match a known-good valid MCR ID."
)
# Known-bad: wrong prefix must not match.
assert not MCR_ID_PATTERN.match("mcr_" + "a" * 64), (
    "MCR_ID_PATTERN incorrectly matches a known-bad lowercase-prefix ID."
)
# Known-bad: CME prefix must not match.
assert not MCR_ID_PATTERN.match("CME_" + "a" * 64), (
    "MCR_ID_PATTERN incorrectly matches a CME-prefixed ID."
)


# ── Public validator ──────────────────────────────────────────────────────────

def validate_mcr_id(canonical_id: str) -> None:
    """
    Raise ValueError if canonical_id does not conform to MCR_FINGERPRINT_V1
    output format: "MCR_" followed by exactly 64 lowercase hex characters.

    Returns None on success.

    Args:
        canonical_id: Value to validate.

    Raises:
        ValueError: canonical_id is not a non-empty str, or does not match
                    ^MCR_[a-f0-9]{64}$.
    """
    if not isinstance(canonical_id, str) or not canonical_id:
        raise ValueError(
            f"canonical_id must be a non-empty string, "
            f"got {type(canonical_id).__name__!r}."
        )
    if not MCR_ID_PATTERN.match(canonical_id):
        raise ValueError(
            f"canonical_id does not match MCR_FINGERPRINT_V1 format "
            f"(MCR_<64 lowercase hex chars>): {canonical_id!r}"
        )
