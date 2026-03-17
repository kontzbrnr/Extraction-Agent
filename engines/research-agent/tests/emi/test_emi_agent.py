import inspect
from unittest.mock import patch

from emi import emi_agent
from emi.emi_agent import enforce_emi
from emi.emi_schema import EMI_NAR_SCHEMA_VERSION, REJECT_EMI_INVALID_SEED


def _make_au(text: str, schema_version: str = "AU-1.0") -> dict:
    return {
        "id": "AU_" + "a" * 64,
        "text": text,
        "parentSourceID": "src_001",
        "sourceReference": "ref_001",
        "splitIndex": 0,
        "schemaVersion": schema_version,
    }


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_wrong_schema_version_rejects(_mock_iav):
    au = _make_au("The team traded the player.", schema_version="AU-2.0")
    passed, rejection, nar = enforce_emi(au)
    assert passed is False
    assert nar is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_EMI_INVALID_SEED


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_missing_required_au_field_rejects(_mock_iav):
    au = _make_au("The team traded the player.")
    au.pop("sourceReference")
    passed, rejection, nar = enforce_emi(au)
    assert passed is False
    assert nar is None
    assert rejection is not None


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_non_dict_au_rejects(_mock_iav):
    passed, rejection, nar = enforce_emi("not a dict")
    assert passed is False
    assert nar is None
    assert rejection is not None


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_does_not_mutate_input(_mock_iav):
    au = _make_au("The team traded the player.")
    before = dict(au)
    _ = enforce_emi(au)
    assert au == before


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_speculative_text_rejects(_mock_iav):
    au = _make_au("The team may trade the player.")
    passed, rejection, nar = enforce_emi(au)
    assert passed is False
    assert nar is None
    assert rejection is not None
    assert rejection["reasonCode"] == "REJECT_EMI_SPECULATIVE_FRAMING"


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_valid_text_passes(_mock_iav):
    au = _make_au("The team traded the player yesterday.")
    passed, rejection, nar = enforce_emi(au)
    assert passed is True
    assert rejection is None
    assert isinstance(nar, dict)


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_valid_text_nar_schema_version(_mock_iav):
    au = _make_au("The team traded the player yesterday.")
    passed, _rejection, nar = enforce_emi(au)
    assert passed is True
    assert nar is not None
    assert nar["narSchemaVersion"] == EMI_NAR_SCHEMA_VERSION


@patch("emi.emi_agent.enforce_iav", return_value=(True, None, {}))
def test_enforce_emi_valid_text_source_seed_id(_mock_iav):
    au = _make_au("The team traded the player yesterday.")
    passed, _rejection, nar = enforce_emi(au)
    assert passed is True
    assert nar is not None
    assert nar["sourceSeedID"] == au["id"]


@patch(
    "emi.emi_agent.enforce_iav",
    return_value=(
        False,
        {
            "reasonCode": "REJECT_IDENTITY_CONTAMINATION",
            "au": {},
            "schemaVersion": "REJECTION-1.0",
        },
        {},
    ),
)
def test_enforce_emi_iav_rejection_passthrough(_mock_iav):
    au = _make_au("The team traded the player yesterday.")
    passed, rejection, nar = enforce_emi(au)
    assert passed is False
    assert nar is None
    assert rejection is not None
    assert rejection["reasonCode"] == "REJECT_IDENTITY_CONTAMINATION"


def test_enforce_emi_does_not_import_make_identity_contamination_rejection():
    source = inspect.getsource(emi_agent)
    assert "make_identity_contamination_rejection" not in source
