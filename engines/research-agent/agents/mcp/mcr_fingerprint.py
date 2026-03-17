"""
mcp/mcr_fingerprint.py

MCR_FINGERPRINT_V1 derivation — Phase 10.4

Canonical fingerprint authority for Media Context Records.

Governing rulings:
    Ruling 10.4-A — Canonical prefix: MCR_
    Ruling 10.4-B — Fingerprint version string: MCR-1.0
    Ruling 10.4-C — Fields: contextDescription, framingType (in this order)
    Ruling 10.4-D — Normalization algorithm (see below)
    MEDIA-LANE IDENTITY PHILOSOPHY — GOVERNING RULING v1

Fingerprint input format (pipe-delimited):
    MCR-1.0 | <contextDescription_norm> | <framingType_norm>

Normalization — contextDescription (Ruling 10.4-D):
    1. Unicode NFC normalization
    2. Strip leading/trailing whitespace
    3. Collapse multiple spaces to single space
    4. Convert to lowercase
    5. Remove all characters outside [a-z0-9 ]
    6. Re-strip leading/trailing whitespace

Normalization — framingType (Ruling 10.4-D):
    1. Strip leading/trailing whitespace
    2. Convert to lowercase

Convergence guarantee (MEDIA-LANE IDENTITY PHILOSOPHY v1):
    Multiple articles expressing equivalent framing converge to the same
    canonical identity. Punctuation differences, spacing differences, and
    capitalisation differences in contextDescription all normalize to the
    same fingerprint. This is by design — it encodes framing signal
    identity, not article identity.

Invariant compliance:
    INV-2: Sole authority for MCR canonical ID derivation. No other module
           may call hashlib.sha256 to produce MCR_ prefixed identifiers.
    INV-5: All normalization steps applied in fixed order via module-level
           compiled patterns. No timestamps, counters, UUIDs, or runtime
           configuration. Identical inputs always produce identical output.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from engines.research_agent.agents.mcp.mcr_id_format import MCR_ID_PATTERN, MCR_ID_PREFIX

# ── Version constants ─────────────────────────────────────────────────────────

MCR_FINGERPRINT_VERSION: str = "MCR_FINGERPRINT_V1"
MCR_FINGERPRINT_PREFIX: str = "MCR-1.0"

# ── Import-time assertions ────────────────────────────────────────────────────

assert MCR_FINGERPRINT_VERSION == "MCR_FINGERPRINT_V1", (
    f"MCR_FINGERPRINT_VERSION drift: {MCR_FINGERPRINT_VERSION!r}"
)
assert MCR_FINGERPRINT_PREFIX == "MCR-1.0", (
    f"MCR_FINGERPRINT_PREFIX drift: {MCR_FINGERPRINT_PREFIX!r}"
)

# ── Compiled patterns (module level — INV-5) ──────────────────────────────────

# Collapses runs of whitespace to a single space.
_MULTI_SPACE_PATTERN: re.Pattern = re.compile(r" +")

# Removes all characters outside the permitted set [a-z0-9 ].
# Applied after lowercasing — safe to assume only lowercase alpha at this point.
_DISALLOWED_CHARS_PATTERN: re.Pattern = re.compile(r"[^a-z0-9 ]")


# ── Normalisation functions ───────────────────────────────────────────────────

def normalize_context_description(text: str) -> str:
    """Normalize a contextDescription value for MCR_FINGERPRINT_V1.

    Applies Ruling 10.4-D normalization in exact fixed order:
        1. Unicode NFC normalization
        2. Strip leading/trailing whitespace
        3. Collapse multiple spaces to single space
        4. Convert to lowercase
        5. Remove characters outside [a-z0-9 ]
        6. Re-strip leading/trailing whitespace

    Convergence: punctuation, capitalisation, and spacing differences
    in equivalent framing sentences produce identical normalized output.

    INV-5: Deterministic. Identical input produces identical output.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.strip()
    text = _MULTI_SPACE_PATTERN.sub(" ", text)
    text = text.lower()
    text = _DISALLOWED_CHARS_PATTERN.sub("", text)
    text = text.strip()
    return text


def normalize_framing_type(framing_type: str) -> str:
    """Normalize a framingType value for MCR_FINGERPRINT_V1.

    Applies Ruling 10.4-D normalization:
        1. Strip leading/trailing whitespace
        2. Convert to lowercase

    INV-5: Deterministic. Identical input produces identical output.
    """
    return framing_type.strip().lower()


# ── Input error ───────────────────────────────────────────────────────────────

class MCRFingerprintInputError(ValueError):
    """Raised when derive_mcr_fingerprint receives invalid or missing fields."""


# ── Derivation ────────────────────────────────────────────────────────────────

def derive_mcr_fingerprint(fields: dict[str, str]) -> str:
    """Derive the MCR_FINGERPRINT_V1 canonical ID for a Media Context Record.

    Applies normalization, assembles the pipe-delimited hash input, and
    returns the canonical MCR_ prefixed identifier.

    Args:
        fields: Dict containing at minimum:
            "contextDescription" — the framing sentence (str, non-empty after norm)
            "framingType"        — the framing classification token (str, non-empty)

    Returns:
        Canonical MCR ID: "MCR_" + 64-char lowercase SHA-256 hex string.
        Always matches ^MCR_[a-f0-9]{64}$.

    Raises:
        MCRFingerprintInputError: If either required field is absent,
            not a string, or normalizes to an empty string.

    INV-2: Sole authority for MCR_ canonical ID derivation.
    INV-5: Deterministic. Identical fields produce identical output.
    """
    # ── Field extraction and type validation ──────────────────────────────────
    context_raw = fields.get("contextDescription")
    framing_raw = fields.get("framingType")

    if not isinstance(context_raw, str):
        raise MCRFingerprintInputError(
            f"'contextDescription' must be a str, "
            f"got {type(context_raw).__name__!r}."
        )
    if not isinstance(framing_raw, str):
        raise MCRFingerprintInputError(
            f"'framingType' must be a str, "
            f"got {type(framing_raw).__name__!r}."
        )

    # ── Normalization (Ruling 10.4-D) ─────────────────────────────────────────
    context_norm = normalize_context_description(context_raw)
    framing_norm = normalize_framing_type(framing_raw)

    if not context_norm:
        raise MCRFingerprintInputError(
            "'contextDescription' normalized to an empty string. "
            "Fingerprint cannot be derived from empty framing signal."
        )
    if not framing_norm:
        raise MCRFingerprintInputError(
            "'framingType' normalized to an empty string. "
            "Fingerprint cannot be derived from empty framing type."
        )

    # ── Hash input assembly (Ruling 10.4-B / 10.4-C) ─────────────────────────
    fingerprint_input = "|".join([
        MCR_FINGERPRINT_PREFIX,
        context_norm,
        framing_norm,
    ])

    # ── SHA-256 derivation ────────────────────────────────────────────────────
    digest = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
    canonical_id = f"{MCR_ID_PREFIX}{digest}"

    # ── Format assertion (INV-2 guard) ────────────────────────────────────────
    assert MCR_ID_PATTERN.match(canonical_id), (
        f"derive_mcr_fingerprint produced a non-conformant ID: {canonical_id!r}. "
        f"This is an internal invariant violation."
    )

    return canonical_id
