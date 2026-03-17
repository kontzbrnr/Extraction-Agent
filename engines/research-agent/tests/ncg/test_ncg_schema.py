import re

from ncg.ncg_schema import (
    NCG_AUDIT_SCHEMA_VERSION,
    NCG_VERSION,
    REASON_FAIL_INVALID_SUBCLASS,
    REASON_FAIL_MISSING_CLASSIFICATION,
    REASON_FAIL_MISSING_EVENT_DESCRIPTION,
    REASON_FAIL_MISSING_SOURCE_REFERENCE,
    REASON_FAIL_MISSING_TIMESTAMP_CONTEXT,
    REASON_PASS_ALL_NCG_CHECKS,
    STAGE_1_CLASSIFICATION,
    STAGE_2_SUBCLASS,
    STAGE_3_TIMESTAMP_CONTEXT,
    STAGE_4_EVENT_DESCRIPTION,
    STAGE_5_SOURCE_REFERENCE,
    VERDICT_FAIL,
    VERDICT_PASS,
)


def test_constants_match_expected_values():
    assert NCG_VERSION == "NCG-1.0"
    assert NCG_AUDIT_SCHEMA_VERSION == "NCG_AUDIT-1.0"
    assert VERDICT_PASS == "PASS"
    assert VERDICT_FAIL == "FAIL"


def test_reason_codes_non_empty_screaming_snake_case():
    pattern = re.compile(r"^[A-Z0-9_]+$")
    values = [
        REASON_PASS_ALL_NCG_CHECKS,
        REASON_FAIL_MISSING_CLASSIFICATION,
        REASON_FAIL_INVALID_SUBCLASS,
        REASON_FAIL_MISSING_TIMESTAMP_CONTEXT,
        REASON_FAIL_MISSING_EVENT_DESCRIPTION,
        REASON_FAIL_MISSING_SOURCE_REFERENCE,
    ]
    for value in values:
        assert isinstance(value, str)
        assert value
        assert pattern.match(value)


def test_stage_identifiers_start_with_digit_pattern():
    values = [
        STAGE_1_CLASSIFICATION,
        STAGE_2_SUBCLASS,
        STAGE_3_TIMESTAMP_CONTEXT,
        STAGE_4_EVENT_DESCRIPTION,
        STAGE_5_SOURCE_REFERENCE,
    ]
    for value in values:
        assert isinstance(value, str)
        assert re.match(r"^[1-9]_", value)
