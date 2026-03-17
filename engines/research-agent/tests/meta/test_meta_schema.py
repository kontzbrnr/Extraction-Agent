import pytest

from engines.research_agent.agents.meta.meta_schema import CMESchemaValidationError, validate_cme_object


def _minimal_cme() -> dict:
    return {
        "id": "CME_" + "a" * 64,
        "eventType": "CME",
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": None,
        "contextRole": None,
        "eventDescription": "Player traded to another team.",
        "subtype": "transactional",
        "permanence": "permanent",
        "sourceReference": "ref_001",
        "timestampContext": "2025_W10",
    }


def test_valid_minimal_cme_passes():
    validate_cme_object(_minimal_cme())


def test_valid_full_cme_passes():
    obj = _minimal_cme()
    obj["objectRole"] = "roster_slot"
    obj["contextRole"] = "regular_season"
    obj["fingerprintVersion"] = "CME_FINGERPRINT_V1"
    validate_cme_object(obj)


def test_missing_required_field_raises():
    obj = _minimal_cme()
    obj.pop("action")
    with pytest.raises(CMESchemaValidationError):
        validate_cme_object(obj)


@pytest.mark.parametrize(
    "bad_id",
    [
        "BAD_" + "a" * 64,
        "CME_" + "A" * 64,
        "CME_" + "a" * 63,
    ],
)
def test_invalid_id_formats_raise(bad_id: str):
    obj = _minimal_cme()
    obj["id"] = bad_id
    with pytest.raises(CMESchemaValidationError):
        validate_cme_object(obj)


def test_event_type_not_cme_raises():
    obj = _minimal_cme()
    obj["eventType"] = "CSN"
    with pytest.raises(CMESchemaValidationError):
        validate_cme_object(obj)


def test_permanence_not_permanent_raises():
    obj = _minimal_cme()
    obj["permanence"] = "temporary"
    with pytest.raises(CMESchemaValidationError):
        validate_cme_object(obj)


def test_invalid_subtype_raises():
    obj = _minimal_cme()
    obj["subtype"] = "unsupported"
    with pytest.raises(CMESchemaValidationError):
        validate_cme_object(obj)


@pytest.mark.parametrize(
    "field",
    ["actorRole", "action", "eventDescription", "sourceReference", "timestampContext"],
)
def test_required_non_empty_string_fields_reject_empty(field: str):
    obj = _minimal_cme()
    obj[field] = ""
    with pytest.raises(CMESchemaValidationError):
        validate_cme_object(obj)
