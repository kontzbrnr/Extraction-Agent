"""
Unit tests for pressure.cps_id_format — Phase 8.5.

Coverage plan:
  - Module exports are importable
  - Constant values (prefix, hex length, total length, version)
  - Total length consistency: len(CPS_ID_PREFIX) + CPS_ID_HEX_LENGTH == CPS_ID_TOTAL_LENGTH
  - CPS_ID_PATTERN: valid IDs match; known-invalid IDs do not
  - validate_cps_id: valid ID returns None
  - validate_cps_id: non-string raises ValueError
  - validate_cps_id: empty string raises ValueError
  - validate_cps_id: wrong prefix raises ValueError
  - validate_cps_id: uppercase hex raises ValueError
  - validate_cps_id: correct prefix, 63 hex chars raises ValueError
  - validate_cps_id: correct prefix, 65 hex chars raises ValueError
  - validate_cps_id: non-hex chars raises ValueError
  - Regression: derive_cps_fingerprint output still matches CPS_ID_PATTERN
  - Regression: cps_dedup.detect_cps_duplicate still raises ValueError on bad ID
  - Regression: cps_constructor.build_cps_object still raises ValueError on bad ID
"""

import pytest

from engines.research_agent.agents.pressure.cps_id_format import (
    CPS_ID_FORMAT_VERSION,
    CPS_ID_HEX_LENGTH,
    CPS_ID_PATTERN,
    CPS_ID_PREFIX,
    CPS_ID_TOTAL_LENGTH,
    validate_cps_id,
)

_VALID_ID = "CPS_" + "a" * 64


# ── Constants ──────────────────────────────────────────────────────────────────

def test_cps_id_prefix_value():
    assert CPS_ID_PREFIX == "CPS_"


def test_cps_id_prefix_length():
    assert len(CPS_ID_PREFIX) == 4


def test_cps_id_hex_length_value():
    assert CPS_ID_HEX_LENGTH == 64


def test_cps_id_total_length_value():
    assert CPS_ID_TOTAL_LENGTH == 68


def test_cps_id_total_length_consistency():
    assert CPS_ID_TOTAL_LENGTH == len(CPS_ID_PREFIX) + CPS_ID_HEX_LENGTH


def test_version_constant():
    assert CPS_ID_FORMAT_VERSION == "CPS_ID_FORMAT-1.0"


# ── Pattern: valid IDs ─────────────────────────────────────────────────────────

def test_pattern_matches_all_lowercase_hex_a():
    assert CPS_ID_PATTERN.match("CPS_" + "a" * 64)


def test_pattern_matches_all_lowercase_hex_f():
    assert CPS_ID_PATTERN.match("CPS_" + "f" * 64)


def test_pattern_matches_mixed_hex():
    assert CPS_ID_PATTERN.match("CPS_" + "0123456789abcdef" * 4)


def test_pattern_total_length_matches_constant():
    assert len(_VALID_ID) == CPS_ID_TOTAL_LENGTH


# ── Pattern: invalid IDs ───────────────────────────────────────────────────────

def test_pattern_rejects_uppercase_hex():
    assert not CPS_ID_PATTERN.match("CPS_" + "A" * 64)


def test_pattern_rejects_lowercase_prefix():
    assert not CPS_ID_PATTERN.match("cps_" + "a" * 64)


def test_pattern_rejects_63_hex_chars():
    assert not CPS_ID_PATTERN.match("CPS_" + "a" * 63)


def test_pattern_rejects_65_hex_chars():
    assert not CPS_ID_PATTERN.match("CPS_" + "a" * 65)


def test_pattern_rejects_empty_string():
    assert not CPS_ID_PATTERN.match("")


def test_pattern_rejects_prefix_only():
    assert not CPS_ID_PATTERN.match("CPS_")


def test_pattern_rejects_g_char():
    assert not CPS_ID_PATTERN.match("CPS_" + "g" * 64)


# ── validate_cps_id: valid ─────────────────────────────────────────────────────

def test_validate_returns_none_for_valid_id():
    result = validate_cps_id(_VALID_ID)
    assert result is None


def test_validate_accepts_all_hex_digits():
    validate_cps_id("CPS_" + "0123456789abcdef" * 4)


# ── validate_cps_id: invalid ───────────────────────────────────────────────────

def test_validate_raises_for_empty_string():
    with pytest.raises(ValueError):
        validate_cps_id("")


def test_validate_raises_for_none():
    with pytest.raises(ValueError):
        validate_cps_id(None)   # type: ignore


def test_validate_raises_for_int():
    with pytest.raises(ValueError):
        validate_cps_id(42)   # type: ignore


def test_validate_raises_for_wrong_prefix():
    with pytest.raises(ValueError):
        validate_cps_id("cps_" + "a" * 64)


def test_validate_raises_for_uppercase_hex():
    with pytest.raises(ValueError):
        validate_cps_id("CPS_" + "A" * 64)


def test_validate_raises_for_63_hex_chars():
    with pytest.raises(ValueError):
        validate_cps_id("CPS_" + "a" * 63)


def test_validate_raises_for_65_hex_chars():
    with pytest.raises(ValueError):
        validate_cps_id("CPS_" + "a" * 65)


def test_validate_raises_for_non_hex_chars():
    with pytest.raises(ValueError):
        validate_cps_id("CPS_" + "g" * 64)


# ── Regression: derive_cps_fingerprint output matches CPS_ID_PATTERN ──────────

def test_fingerprint_output_matches_cps_id_pattern():
    from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_FIELDS, derive_cps_fingerprint
    fields = {f: "test" for f in CPS_FINGERPRINT_FIELDS}
    result = derive_cps_fingerprint(fields)
    assert CPS_ID_PATTERN.match(result), (
        f"derive_cps_fingerprint output {result!r} does not match CPS_ID_PATTERN"
    )


def test_fingerprint_output_passes_validate_cps_id():
    from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_FIELDS, derive_cps_fingerprint
    fields = {f: "test" for f in CPS_FINGERPRINT_FIELDS}
    result = derive_cps_fingerprint(fields)
    validate_cps_id(result)   # must not raise


# ── Regression: consumers still raise ValueError on bad ID ────────────────────

def test_cps_dedup_still_raises_value_error_on_bad_id(tmp_path):
    from engines.research_agent.agents.pressure.cps_dedup import detect_cps_duplicate
    with pytest.raises(ValueError):
        detect_cps_duplicate("bad_id", str(tmp_path / "registry.json"))


def test_cps_constructor_still_raises_value_error_on_bad_id():
    from engines.research_agent.agents.pressure.cps_constructor import build_cps_object
    with pytest.raises(ValueError):
        build_cps_object({}, "bad_id", "ENUM_v1.0") 
