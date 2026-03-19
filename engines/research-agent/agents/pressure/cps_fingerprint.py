"""
pressure/cps_fingerprint.py

CPS_FINGERPRINT_V1 — Canonical Pressure Signal identity hash.

Derives the canonical fingerprint for a Canonical Pressure Signal (CPS)
object. Called exclusively by PSTA at canonical mint time.

Contract authority:
    PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md (PSTA v4) — sole field
    composition, serialization order, and hash algorithm authority.
    CANONICAL-INTEGRITY-VALIDATOR.md — declares PSTA v4 sole authority.

Governance rulings applied:
    2026-03-08 — environment participates in CPS_FINGERPRINT_V1.
                 PSTA v4 governs. Phase 7 Audit comment in
                 role_token_registry.py was incorrect and is corrected
                 separately.
    2026-03-08 — Normalization rules defined here (absent from PSTA v4
                 contract). Rules: NFC → strip → collapse-ws → lower.
                 Punctuation not stripped (enum underscores must survive).

Invariant compliance:
    INV-1: Pure function. No module-level mutable state.
    INV-2: This module IS the canonical identity derivation for the
           pressure lane. It produces canonical IDs; it does not consume
           them.
    INV-3: Input dict is never mutated.
    INV-4: No cross-lane fields consumed. All inputs are pressure-lane
           fields per PSTA v4 field list.
    INV-5: Deterministic. All normalization rules pinned. No runtime
           state, timestamps, or UUIDs introduced.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from engines.research_agent.agents.pressure.cps_id_format import CPS_ID_PATTERN, CPS_ID_PREFIX


# ── Version constants ──────────────────────────────────────────────────────────

CPS_FINGERPRINT_V1: str = "CPS_FINGERPRINT_V1"

_CPS_SCHEMA_PREFIX: str = "CPS-1.0"


# ── Field participation — PSTA v4 exact order ─────────────────────────────────
# Tuple: both membership and serialization order are contractual.
# Governed by PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md (PSTA v4).
#
# environment is field index 1 (per 2026-03-08 governance ruling).
# enumRegistryVersion does NOT participate (confirmed: absent from PSTA v4
# field list).

CPS_FINGERPRINT_FIELDS: tuple[str, ...] = (
    "signalClass",
    "environment",
    "pressureSignalDomain",
    "pressureVector",
    "signalPolarity",
    "observationSource",
    "castRequirement",
    "tier",
    "observation",
    "sourceSeed",
)


# ── Normalization ──────────────────────────────────────────────────────────────
# Rules defined Phase 8.1 (2026-03-08) — absent from PSTA v4 contract text.
#
# Applied to every field value before serialization:
#   1. str()                    — coerce (handles tier: int → "1"/"2"/"3")
#   2. unicodedata.normalize    — NFC; pin Unicode form for cross-platform
#                                 determinism
#   3. .strip()                 — remove leading/trailing whitespace
#   4. collapse [ \t\r\n]+      — normalize internal whitespace to single space
#                                 (uses explicit char class, not \s, to avoid
#                                 locale-dependent matching of non-breaking spaces)
#   5. .lower()                 — case-insensitive identity
#
# Punctuation is NOT stripped: enum tokens use underscores as structural
# separators (e.g. "structural_condition"); stripping would corrupt them.
# Free-text fields (observation, sourceSeed) preserve meaningful hyphens.

def _normalize(value: object) -> str:
    """
    Apply CPS_FINGERPRINT_V1 canonical normalization to a single field value.

    Args:
        value: Raw field value. Must not be None.

    Returns:
        Normalized string ready for "|"-delimited serialization.
    """
    s = str(value)
    s = unicodedata.normalize("NFC", s)
    s = s.strip()
    s = re.sub(r"[ \t\r\n]+", " ", s)
    s = s.lower()
    return s


# ── Fingerprint derivation ─────────────────────────────────────────────────────

def derive_cps_fingerprint(cps_fields: dict) -> str:
    """
    Derive the CPS_FINGERPRINT_V1 canonical identity hash.

    Implements PSTA v4 canonical concatenation:
        canonical_string = "CPS-1.0|{f0_norm}|{f1_norm}|...|{f9_norm}"
        digest           = SHA-256(canonical_string.encode("utf-8")).hexdigest()
        canonical_id     = "CPS_" + digest

    Field order follows CPS_FINGERPRINT_FIELDS exactly (PSTA v4 §II).

    Caller contract:
        - All 10 keys in CPS_FINGERPRINT_FIELDS must be present.
          Missing key → KeyError (fail-fast; silent identity corruption
          is worse than a hard failure).
        - tier must be int (1, 2, or 3). Float inputs produce wrong str().
        - Input dict is not mutated (INV-3).

    Args:
        cps_fields: Dict containing all CPS_FINGERPRINT_FIELDS keys.
                    Additional keys are ignored and never hashed.

    Returns:
        "CPS_" + 64 lowercase hex chars  (68 chars total).

    Raises:
        KeyError: If any required field is absent from cps_fields.
    """
    parts: list[str] = [_CPS_SCHEMA_PREFIX] + [
        _normalize(cps_fields[field]) for field in CPS_FINGERPRINT_FIELDS
    ]
    canonical_string = "|".join(parts)
    digest = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()
    canonical_id = CPS_ID_PREFIX + digest
    assert CPS_ID_PATTERN.match(canonical_id), (
        f"derive_cps_fingerprint produced a non-conformant ID: {canonical_id!r}. "
        f"This is an internal invariant violation."
    )
    return canonical_id


def verify_cps_fingerprint(cps_fields: dict, canonical_id: str) -> bool:
    """Return True when canonical_id matches CPS_FINGERPRINT_V1 derivation."""
    parts: list[str] = [_CPS_SCHEMA_PREFIX] + [
        _normalize(cps_fields[field]) for field in CPS_FINGERPRINT_FIELDS
    ]
    canonical_string = "|".join(parts)
    digest = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()
    expected = CPS_ID_PREFIX + digest
    return expected == canonical_id
