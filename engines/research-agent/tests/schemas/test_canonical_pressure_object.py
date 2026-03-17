import pytest
from engines.research_agent.schemas.pressure.validator import validate_pressure_object, PressureSchemaValidationError
from engines.research_agent.schemas.pressure.fallback_tokens import PRESSURE_FALLBACK_TOKENS


# Valid object fixture — fully populated, valid canonical pressure object
VALID_OBJECT = {
    "laneType": "PRESSURE",
    "schemaVersion": "CPS-1.0",
    "signalClass": "structural_tension",
    "environment": "organizational",
    "pressureSignalDomain": "authority_distribution",
    "pressureVector": "competing_influences",
    "signalPolarity": "negative",
    "observationSource": "internal_audit",
    "castRequirement": "executive_decision_required",
    "tier": 2,
    "observation": "Coach retains play-calling authority despite board scrutiny.",
    "sourceSeed": "Competing Authority Over Play-Calling",
    "canonicalId": "CPS_" + "a" * 64,
    "enumRegistryVersion": "ENUM_v1.0",
    "fingerprintVersion": "CPS_FINGERPRINT_V1",
    "contractVersion": "PSTA_v4",
}


def test_valid_object_passes():
    """Test that a fully valid canonical pressure object passes validation."""
    validate_pressure_object(VALID_OBJECT)


@pytest.mark.parametrize("field_name", [
    "laneType",
    "schemaVersion",
    "signalClass",
    "environment",
    "pressureSignalDomain",
    "pressureVector",
    "signalPolarity",
    "observationSource",
    "castRequirement",
    "tier",
    "observation",
    "sourceSeed",
    "canonicalId",
    "enumRegistryVersion",
    "fingerprintVersion",
    "contractVersion",
])
def test_missing_each_required_field_fails(field_name):
    """Test that removing any required field causes validation to fail."""
    obj = VALID_OBJECT.copy()
    del obj[field_name]
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_laneType_wrong_value_fails():
    """Test that laneType with value NARRATIVE fails validation."""
    obj = VALID_OBJECT.copy()
    obj["laneType"] = "NARRATIVE"
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_laneType_wrong_value_media_fails():
    """Test that laneType with value MEDIA fails validation."""
    obj = VALID_OBJECT.copy()
    obj["laneType"] = "MEDIA"
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_tier_string_fails():
    """Test that tier with string value fails validation."""
    obj = VALID_OBJECT.copy()
    obj["tier"] = "2"
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_tier_null_passes():
    """Test that tier with null value passes validation."""
    obj = VALID_OBJECT.copy()
    obj["tier"] = None
    validate_pressure_object(obj)


def test_canonicalId_bad_format_fails():
    """Test that canonicalId with bad format fails validation."""
    obj = VALID_OBJECT.copy()
    obj["canonicalId"] = "bad_format"
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_canonicalId_uppercase_hex_fails():
    """Test that canonicalId with uppercase hex fails validation (pattern requires lowercase)."""
    obj = VALID_OBJECT.copy()
    obj["canonicalId"] = "CPS_" + "A" * 64
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_additional_field_fails():
    """Test that adding extra field timestampContext fails validation."""
    obj = VALID_OBJECT.copy()
    obj["timestampContext"] = "2024-01"
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_additional_field_lifecycle_fails():
    """Test that adding extra field recurrenceCount fails validation."""
    obj = VALID_OBJECT.copy()
    obj["recurrenceCount"] = 3
    with pytest.raises(PressureSchemaValidationError):
        validate_pressure_object(obj)


def test_fingerprint_field_empty_string_passes():
    """Test that empty string is valid fallback token for fingerprint fields."""
    obj = VALID_OBJECT.copy()
    obj["signalClass"] = ""
    validate_pressure_object(obj)


def test_observation_null_passes():
    """Test that null observation passes validation."""
    obj = VALID_OBJECT.copy()
    obj["observation"] = None
    validate_pressure_object(obj)


def test_fallback_tokens_coverage():
    """Assert PRESSURE_FALLBACK_TOKENS keys match exactly the nullable fingerprint-participating fields."""
    # Expected nullable fingerprint-participating fields
    expected_fields = {
        "schemaVersion",
        "signalClass",
        "environment",
        "pressureSignalDomain",
        "pressureVector",
        "signalPolarity",
        "observationSource",
        "castRequirement",
        "tier",
        "observation",
        "sourceSeed",
    }
    
    # Assert keys match exactly
    assert set(PRESSURE_FALLBACK_TOKENS.keys()) == expected_fields, \
        f"Fallback tokens keys {set(PRESSURE_FALLBACK_TOKENS.keys())} do not match expected {expected_fields}"
