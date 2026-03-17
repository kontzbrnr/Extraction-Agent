"""
narrative/ane_id_format.py
Canonical ANESEED id format constants and validator.
"""

from __future__ import annotations

import re

ANESEED_FORMAT_VERSION: str = "ANESEED_FORMAT-1.0"
ANESEED_PREFIX: str = "ANESEED_"
ANESEED_HEX_LENGTH: int = 64
ANESEED_TOTAL_LENGTH: int = 72
ANESEED_PATTERN: re.Pattern = re.compile(r"^ANESEED_[a-f0-9]{64}$")


def validate_aneseed_id(event_seed_id: str) -> None:
    """Validate ANESEED id format."""
    if not isinstance(event_seed_id, str):
        raise ValueError("event_seed_id must be a string")
    if event_seed_id == "":
        raise ValueError("event_seed_id cannot be empty")
    if not ANESEED_PATTERN.match(event_seed_id):
        raise ValueError("event_seed_id must match ^ANESEED_[a-f0-9]{64}$")


assert len(ANESEED_PREFIX) == 8
assert len(ANESEED_PREFIX) + ANESEED_HEX_LENGTH == ANESEED_TOTAL_LENGTH
assert ANESEED_FORMAT_VERSION == "ANESEED_FORMAT-1.0"
assert ANESEED_PREFIX == "ANESEED_"
assert ANESEED_HEX_LENGTH == 64
assert ANESEED_TOTAL_LENGTH == 72
