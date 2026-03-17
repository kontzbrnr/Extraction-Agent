import re

import pytest

from engines.research_agent.agents.meta.meta_ontology import (
    CME_ID_HEX_LENGTH,
    CME_ID_PREFIX,
    CME_ID_TOTAL_LENGTH,
    META_CME_FINGERPRINT_PREFIX,
    META_CME_FINGERPRINT_VERSION,
    META_SUBTYPE_VALUES,
    META_VERSION,
    REJECT_META_IDENTITY_CONTAMINATION,
    REJECT_META_INVALID_INPUT,
    REJECT_META_NON_CME_INPUT,
    REJECT_META_PERMANENCE_VIOLATION,
    REJECT_META_SCHEMA_INVALID,
    REJECT_META_SUBTYPE_AMBIGUOUS,
    validate_cme_id,
)


def test_constant_values():
    assert META_VERSION == "META-1.0"
    assert META_CME_FINGERPRINT_VERSION == "CME_FINGERPRINT_V1"
    assert META_CME_FINGERPRINT_PREFIX == "CME-1.0"
    assert CME_ID_PREFIX == "CME_"
    assert CME_ID_HEX_LENGTH == 64
    assert CME_ID_TOTAL_LENGTH == 68


def test_total_length_consistency():
    assert len(CME_ID_PREFIX) + CME_ID_HEX_LENGTH == CME_ID_TOTAL_LENGTH


def test_subtype_values_count_and_other_presence():
    assert len(META_SUBTYPE_VALUES) == 12
    assert "other" in META_SUBTYPE_VALUES


def test_validate_cme_id_valid_returns_none():
    assert validate_cme_id("CME_" + "a" * 64) is None


@pytest.mark.parametrize(
    "bad_id",
    [
        None,
        123,
        "",
        "cme_" + "a" * 64,
        "CME_" + "A" * 64,
        "CME_" + "a" * 63,
        "CME_" + "a" * 65,
    ],
)
def test_validate_cme_id_invalid_cases_raise_value_error(bad_id):
    with pytest.raises(ValueError):
        validate_cme_id(bad_id)  # type: ignore[arg-type]


def test_rejection_code_constants_are_screaming_snake_case_strings():
    values = [
        REJECT_META_INVALID_INPUT,
        REJECT_META_NON_CME_INPUT,
        REJECT_META_SUBTYPE_AMBIGUOUS,
        REJECT_META_PERMANENCE_VIOLATION,
        REJECT_META_IDENTITY_CONTAMINATION,
        REJECT_META_SCHEMA_INVALID,
    ]
    pattern = re.compile(r"^[A-Z0-9_]+$")
    for value in values:
        assert isinstance(value, str)
        assert value
        assert pattern.match(value)
