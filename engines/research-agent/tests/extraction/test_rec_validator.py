import pytest
from engines.research_agent.agents.extraction.rec_validator import validate_rec, RECSchemaValidationError


# Valid REC fixture — produced by produce_rec() from Phase 3.2
VALID_REC = {
    "schemaVersion": "REC-1.0",
    "id": "REC_" + "a" * 64,
    "text": "Coach fired OC and promoted QB coach.",
    "isComposite": False,
}


def test_valid_rec_passes():
    """Test that a fully valid REC passes validation."""
    validate_rec(VALID_REC)


def test_valid_rec_composite_true_passes():
    """Test that isComposite=True is valid."""
    obj = {**VALID_REC, "isComposite": True}
    validate_rec(obj)


@pytest.mark.parametrize("field_name", ["id", "text", "isComposite", "schemaVersion"])
def test_missing_required_field_fails(field_name):
    """Test that removing any required field causes validation to fail."""
    obj = VALID_REC.copy()
    del obj[field_name]
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_id_wrong_prefix_fails():
    """Test that id with wrong prefix fails validation."""
    obj = {**VALID_REC, "id": "AU_" + "a" * 64}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_id_wrong_length_fails():
    """Test that id with wrong hex length fails validation."""
    obj = {**VALID_REC, "id": "REC_" + "a" * 63}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_id_uppercase_hex_fails():
    """Test that id with uppercase hex fails validation (pattern requires lowercase)."""
    obj = {**VALID_REC, "id": "REC_" + "A" * 64}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_id_bad_format_fails():
    """Test that id with bad format fails validation."""
    obj = {**VALID_REC, "id": "not_a_valid_id"}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_schema_version_wrong_value_fails():
    """Test that schemaVersion with wrong value fails validation."""
    obj = {**VALID_REC, "schemaVersion": "REC-2.0"}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_text_empty_string_fails():
    """Test that text with empty string fails validation."""
    obj = {**VALID_REC, "text": ""}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_is_composite_string_fails():
    """Test that isComposite with string value fails validation."""
    obj = {**VALID_REC, "isComposite": "false"}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_is_composite_int_fails():
    """Test that isComposite with int value fails validation."""
    obj = {**VALID_REC, "isComposite": 0}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


@pytest.mark.parametrize("extra_field", [
    "laneType", "seed_type", "canonical_id",
    "lane", "seedType", "canonicalId",
])
def test_extra_field_fails(extra_field):
    """Test that adding extra field fails validation (additionalProperties: false)."""
    obj = {**VALID_REC, extra_field: "value"}
    with pytest.raises(RECSchemaValidationError):
        validate_rec(obj)


def test_error_message_contains_jsonschema_detail():
    """Test that error message contains jsonschema validation detail."""
    obj = {**VALID_REC, "id": "bad_id"}
    with pytest.raises(RECSchemaValidationError) as exc_info:
        validate_rec(obj)
    assert len(str(exc_info.value)) > 0


def test_validate_rec_returns_none_on_success():
    """Test that validate_rec returns None on success."""
    result = validate_rec(VALID_REC)
    assert result is None


def test_schema_loaded_at_module_level():
    """Test that _SCHEMA is loaded at module level, not inside a function."""
    import extraction.rec_validator as m
    import inspect
    src = inspect.getsource(m)
    # _SCHEMA must be assigned outside any function
    assert "_SCHEMA" in src
    assert "def validate_rec" in src
    # Confirm _SCHEMA assignment is not inside validate_rec
    # (Simple structural check — _SCHEMA appears before def validate_rec)
    schema_pos = src.index("_SCHEMA")
    func_pos = src.index("def validate_rec")
    assert schema_pos < func_pos
