import pytest

from narrative.ane_id_format import (
    ANESEED_HEX_LENGTH,
    ANESEED_PREFIX,
    ANESEED_TOTAL_LENGTH,
    validate_aneseed_id,
)


def test_constants_match_spec():
    assert ANESEED_PREFIX == "ANESEED_"
    assert ANESEED_HEX_LENGTH == 64
    assert ANESEED_TOTAL_LENGTH == 72


def test_total_length_consistency():
    assert len(ANESEED_PREFIX) + ANESEED_HEX_LENGTH == ANESEED_TOTAL_LENGTH


def test_validate_valid_aneseed_id_returns_none():
    assert validate_aneseed_id("ANESEED_" + "a" * 64) is None


@pytest.mark.parametrize(
    "bad_id",
    [
        None,
        123,
        "",
        "CPS_" + "a" * 64,
        "CSN_" + "a" * 64,
        "CME_" + "a" * 64,
        "ANESEED_" + "A" * 64,
        "ANESEED_" + "a" * 63,
        "ANESEED_" + "a" * 65,
    ],
)
def test_validate_invalid_ids_raise_value_error(bad_id):
    with pytest.raises(ValueError):
        validate_aneseed_id(bad_id)  # type: ignore[arg-type]
