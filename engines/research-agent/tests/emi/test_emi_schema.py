import pytest

from emi.emi_schema import (
    EMINARValidationError,
    EMI_AU_SCHEMA_VERSION,
    EMI_LANE_TYPE,
    EMI_NAR_SCHEMA_VERSION,
    EMI_REQUIRED_AU_FIELDS,
    EMI_VERSION,
    REJECT_EMI_ACTOR_ATTRIBUTION,
    REJECT_EMI_COMPOSITE_BOUNDARY,
    REJECT_EMI_DISCOURSE_INSEPARABLE,
    REJECT_EMI_EVENT_AMBIGUOUS,
    REJECT_EMI_INVALID_SEED,
    REJECT_EMI_LEDGER_INCOMPLETE,
    REJECT_EMI_NO_SEPARABLE_OCCURRENCE,
    REJECT_EMI_SPECULATIVE_FRAMING,
    validate_nar,
)


def _valid_nar() -> dict:
    return {
        "eventID": "evt_001",
        "sourceSeedID": "AU_" + "a" * 64,
        "actorGroup": "The",
        "actionVerb": "team",
        "ledgerMutation": True,
        "unusualProcedural": False,
        "narSchemaVersion": "EMI_NAR-1.0",
        "ploe_fork_required": False,
    }


def test_emi_version_constant():
    assert EMI_VERSION == "EMI-1.0"


def test_emi_lane_type_constant():
    assert EMI_LANE_TYPE == "NARRATIVE"


def test_emi_au_schema_version_constant():
    assert EMI_AU_SCHEMA_VERSION == "AU-1.0"


def test_emi_nar_schema_version_constant():
    assert EMI_NAR_SCHEMA_VERSION == "EMI_NAR-1.0"


def test_emi_required_au_fields_length():
    assert len(EMI_REQUIRED_AU_FIELDS) == 6


def test_reject_codes_non_empty_and_distinct():
    codes = {
        REJECT_EMI_INVALID_SEED,
        REJECT_EMI_EVENT_AMBIGUOUS,
        REJECT_EMI_COMPOSITE_BOUNDARY,
        REJECT_EMI_ACTOR_ATTRIBUTION,
        REJECT_EMI_SPECULATIVE_FRAMING,
        REJECT_EMI_LEDGER_INCOMPLETE,
        REJECT_EMI_NO_SEPARABLE_OCCURRENCE,
        REJECT_EMI_DISCOURSE_INSEPARABLE,
    }
    assert len(codes) == 8
    assert all(isinstance(code, str) and code for code in codes)


def test_validate_nar_passes_on_complete_nar():
    validate_nar(_valid_nar())


@pytest.mark.parametrize(
    "missing_field",
    [
        "eventID",
        "sourceSeedID",
        "actorGroup",
        "actionVerb",
        "ledgerMutation",
        "unusualProcedural",
        "narSchemaVersion",
        "ploe_fork_required",
    ],
)
def test_validate_nar_raises_on_missing_required_field(missing_field: str):
    nar = _valid_nar()
    nar.pop(missing_field)
    with pytest.raises(EMINARValidationError):
        validate_nar(nar)


def test_validate_nar_raises_on_bad_schema_version():
    nar = _valid_nar()
    nar["narSchemaVersion"] = "EMI_NAR-0.9"
    with pytest.raises(EMINARValidationError):
        validate_nar(nar)


def test_validate_nar_raises_on_non_bool_ledger_mutation():
    nar = _valid_nar()
    nar["ledgerMutation"] = "true"
    with pytest.raises(EMINARValidationError):
        validate_nar(nar)


def test_validate_nar_does_not_mutate_input_dict():
    nar = _valid_nar()
    before = dict(nar)
    validate_nar(nar)
    assert nar == before
