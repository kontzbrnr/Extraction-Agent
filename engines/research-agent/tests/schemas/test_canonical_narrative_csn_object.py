import pytest
from engines.research_agent.schemas.narrative.validator import validate_narrative_csn_object, NarrativeCSNSchemaValidationError
from engines.research_agent.schemas.narrative.fallback_tokens import NARRATIVE_CSN_FALLBACK_TOKENS


# Valid object fixture — fully populated valid CSN canonical object
VALID_OBJECT = {
    "laneType": "NARRATIVE",
    "id": "CSN_" + "a" * 64,
    "eventType": "CSN",
    "actorRole": "head_coach",
    "action": "announced",
    "objectRole": "starting_quarterback",
    "contextRole": "team_leadership",
    "subclass": "personnel_decision",
    "sourceReference": "doc:abc123#p4l22",
    "eventDescription": "A head coach announced a change to the starting quarterback.",
    "timestampContext": "season_2020_week_03",
    "contractVersion": "SANTA_v1",
}


def test_valid_object_passes():
    """Test that a fully valid CSN canonical object passes validation."""
    validate_narrative_csn_object(VALID_OBJECT)


@pytest.mark.parametrize("field_name", [
    "id",
    "eventType",
    "actorRole",
    "action",
    "subclass",
    "sourceReference",
    "eventDescription",
    "timestampContext",
    "laneType",
    "contractVersion",
])
def test_missing_required_fields_fails(field_name):
    """Test that removing any required field causes validation to fail."""
    obj = VALID_OBJECT.copy()
    del obj[field_name]
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_objectRole_absent_passes():
    """Test that objectRole can be absent (not required)."""
    obj = VALID_OBJECT.copy()
    del obj["objectRole"]
    validate_narrative_csn_object(obj)


def test_contextRole_absent_passes():
    """Test that contextRole can be absent (not required)."""
    obj = VALID_OBJECT.copy()
    del obj["contextRole"]
    validate_narrative_csn_object(obj)


def test_objectRole_null_passes():
    """Test that objectRole can be null."""
    obj = VALID_OBJECT.copy()
    obj["objectRole"] = None
    validate_narrative_csn_object(obj)


def test_contextRole_null_passes():
    """Test that contextRole can be null."""
    obj = VALID_OBJECT.copy()
    obj["contextRole"] = None
    validate_narrative_csn_object(obj)


def test_laneType_wrong_value_fails():
    """Test that laneType with value PRESSURE fails validation."""
    obj = VALID_OBJECT.copy()
    obj["laneType"] = "PRESSURE"
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_eventType_wrong_value_fails():
    """Test that eventType with value CME fails validation."""
    obj = VALID_OBJECT.copy()
    obj["eventType"] = "CME"
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_id_bad_format_fails():
    """Test that id with bad format fails validation."""
    obj = VALID_OBJECT.copy()
    obj["id"] = "bad_format"
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_id_uppercase_hex_fails():
    """Test that id with uppercase hex fails validation (pattern requires lowercase)."""
    obj = VALID_OBJECT.copy()
    obj["id"] = "CSN_" + "A" * 64
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_eventDescription_empty_string_fails():
    """Test that eventDescription with empty string fails validation (minLength: 1)."""
    obj = VALID_OBJECT.copy()
    obj["eventDescription"] = ""
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_timestampContext_empty_string_fails():
    """Test that timestampContext with empty string fails validation (minLength: 1)."""
    obj = VALID_OBJECT.copy()
    obj["timestampContext"] = ""
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_permanence_field_fails():
    """Test that permanence field fails validation (additionalProperties: false)."""
    obj = VALID_OBJECT.copy()
    obj["permanence"] = "permanent"
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


@pytest.mark.parametrize("field_name", [
    "timestampBucket",
    "eventSeedId",
    "firstSeen",
    "recurrenceCount",
    "decayScore",
])
def test_excluded_diagnostic_field_fails(field_name):
    """Test that adding any excluded diagnostic field fails validation."""
    obj = VALID_OBJECT.copy()
    obj[field_name] = "value"
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_additional_field_fails():
    """Test that adding extra field clusterMembership fails validation."""
    obj = VALID_OBJECT.copy()
    obj["clusterMembership"] = "x"
    with pytest.raises(NarrativeCSNSchemaValidationError):
        validate_narrative_csn_object(obj)


def test_fingerprint_field_empty_string_passes():
    """Test that empty string is valid fallback token for fingerprint fields."""
    obj = VALID_OBJECT.copy()
    obj["actorRole"] = ""
    validate_narrative_csn_object(obj)


def test_fallback_tokens_coverage():
    """Assert NARRATIVE_CSN_FALLBACK_TOKENS keys match exactly the fingerprint-participating fields."""
    # Expected fingerprint-participating fields
    expected_fields = {
        "actorRole",
        "action",
        "objectRole",
        "contextRole",
        "subclass",
        "sourceReference",
    }
    
    # Assert keys match exactly
    assert set(NARRATIVE_CSN_FALLBACK_TOKENS.keys()) == expected_fields, \
        f"Fallback tokens keys {set(NARRATIVE_CSN_FALLBACK_TOKENS.keys())} do not match expected {expected_fields}"
    
    # Assert permanence is NOT in fallback tokens
    assert "permanence" not in NARRATIVE_CSN_FALLBACK_TOKENS, \
        "permanence should not be in NARRATIVE_CSN_FALLBACK_TOKENS (Option B ruling)"
