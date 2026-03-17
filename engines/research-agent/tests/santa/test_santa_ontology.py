import re

import pytest

from engines.research_agent.agents.santa.santa_ontology import (
    CSN_ID_HEX_LENGTH,
    CSN_ID_PREFIX,
    CSN_ID_TOTAL_LENGTH,
    REJECT_SANTA_IDENTITY_CONTAMINATION,
    REJECT_SANTA_INVALID_INPUT,
    REJECT_SANTA_INVALID_SUBCLASS,
    REJECT_SANTA_NON_CSN_INPUT,
    REJECT_SANTA_SCHEMA_INVALID,
    SANTA_CSN_FINGERPRINT_PREFIX,
    SANTA_CSN_FINGERPRINT_VERSION,
    SANTA_LANE_TYPE,
    SANTA_PERMANENCE_NORM,
    SANTA_VERSION,
    validate_csn_id,
)


def test_constant_values_match_spec():
    assert SANTA_VERSION == "SANTA-1.0"
    assert SANTA_CSN_FINGERPRINT_VERSION == "CSN_FINGERPRINT_V1"
    assert SANTA_CSN_FINGERPRINT_PREFIX == "CSN-1.0"
    assert CSN_ID_PREFIX == "CSN_"
    assert CSN_ID_HEX_LENGTH == 64
    assert CSN_ID_TOTAL_LENGTH == 68
    assert SANTA_LANE_TYPE == "NARRATIVE"


def test_total_length_consistency():
    assert len(CSN_ID_PREFIX) + CSN_ID_HEX_LENGTH == CSN_ID_TOTAL_LENGTH


def test_validate_csn_id_valid_returns_none():
    assert validate_csn_id("CSN_" + "a" * 64) is None


@pytest.mark.parametrize(
    "bad_id",
    [
        None,
        123,
        "",
        "csn_" + "a" * 64,
        "CSN_" + "A" * 64,
        "CSN_" + "a" * 63,
        "CSN_" + "a" * 65,
    ],
)
def test_validate_csn_id_invalid_raises_value_error(bad_id):
    with pytest.raises(ValueError):
        validate_csn_id(bad_id)  # type: ignore[arg-type]


def test_permanence_norm_is_empty_not_permanent_not_none():
    assert SANTA_PERMANENCE_NORM == ""
    assert SANTA_PERMANENCE_NORM != "permanent"
    assert SANTA_PERMANENCE_NORM is not None


def test_rejection_codes_non_empty_screaming_snake_case():
    values = [
        REJECT_SANTA_INVALID_INPUT,
        REJECT_SANTA_NON_CSN_INPUT,
        REJECT_SANTA_INVALID_SUBCLASS,
        REJECT_SANTA_SCHEMA_INVALID,
        REJECT_SANTA_IDENTITY_CONTAMINATION,
    ]
    pattern = re.compile(r"^[A-Z0-9_]+$")
    for value in values:
        assert isinstance(value, str)
        assert value
        assert pattern.match(value)
