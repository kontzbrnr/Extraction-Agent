import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


# Load the schema
schema_path = Path(__file__).parent.parent.parent / "schemas" / "canonical_envelope.schema.json"
with open(schema_path, 'r') as f:
    CANONICAL_ENVELOPE_SCHEMA = json.load(f)


def test_valid_envelope_passes():
    """Test that a valid envelope with all required fields passes validation."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0",
        "fingerprintVersion": None
    }
    validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_valid_all_lanes():
    """Test that all three lane types (PRESSURE, NARRATIVE, MEDIA) pass validation."""
    for lane_type in ["PRESSURE", "NARRATIVE", "MEDIA"]:
        envelope = {
            "laneType": lane_type,
            "schemaVersion": "1.0.0",
            "enumVersion": "1.0.0",
            "contractVersion": "1.0.0"
        }
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_missing_laneType_fails():
    """Test that an envelope missing laneType fails validation."""
    envelope = {
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0"
    }
    with pytest.raises(ValidationError):
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_missing_schemaVersion_fails():
    """Test that an envelope missing schemaVersion fails validation."""
    envelope = {
        "laneType": "PRESSURE",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0"
    }
    with pytest.raises(ValidationError):
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_missing_enumVersion_fails():
    """Test that an envelope missing enumVersion fails validation."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "contractVersion": "1.0.0"
    }
    with pytest.raises(ValidationError):
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_missing_contractVersion_fails():
    """Test that an envelope missing contractVersion fails validation."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0"
    }
    with pytest.raises(ValidationError):
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_invalid_laneType_value_fails():
    """Test that an invalid laneType value fails validation."""
    envelope = {
        "laneType": "MEDIA_PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0"
    }
    with pytest.raises(ValidationError):
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_additional_field_fails():
    """Test that additional properties are rejected due to additionalProperties: false."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0",
        "mintedAt": "2024-01-01"
    }
    with pytest.raises(ValidationError):
        validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_fingerprintVersion_null_passes():
    """Test that fingerprintVersion can be null."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0",
        "fingerprintVersion": None
    }
    validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_fingerprintVersion_string_passes():
    """Test that fingerprintVersion can be a string."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0",
        "fingerprintVersion": "v1"
    }
    validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)


def test_fingerprintVersion_absent_passes():
    """Test that fingerprintVersion is optional and can be absent."""
    envelope = {
        "laneType": "PRESSURE",
        "schemaVersion": "1.0.0",
        "enumVersion": "1.0.0",
        "contractVersion": "1.0.0"
    }
    validate(instance=envelope, schema=CANONICAL_ENVELOPE_SCHEMA)
