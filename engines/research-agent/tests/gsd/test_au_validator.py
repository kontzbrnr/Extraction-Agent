"""
tests/gsd/test_au_validator.py

Tests for gsd/au_validator.py — Phase 4.5.

Mirrors the test pattern of tests/extraction/test_rec_validator.py.

Validates:
  - Valid AU passes without exception
  - All 6 required fields enforced
  - id pattern: prefix, length, case, format
  - schemaVersion const enforced
  - text and sourceReference minLength enforced
  - splitIndex type and minimum enforced
  - additionalProperties: false enforced
  - Error message contains jsonschema detail
  - validate_au returns None on success
  - _SCHEMA loaded at module level (not inside function)
"""

import inspect

import pytest

from gsd.au_validator import AUSchemaValidationError, validate_au

# ── Valid AU fixture ──────────────────────────────────────────────────────────

VALID_AU = {
    "schemaVersion": "AU-1.0",
    "id": "AU_" + "a" * 64,
    "text": "Coach fired the offensive coordinator.",
    "parentSourceID": "REC_" + "b" * 64,
    "sourceReference": "article://test/source-001",
    "splitIndex": 0,
}


# ── Valid AU passes ───────────────────────────────────────────────────────────

def test_valid_au_passes():
    """A fully valid AU passes validation without exception."""
    validate_au(VALID_AU)


def test_valid_au_split_index_nonzero_passes():
    """splitIndex > 0 is valid."""
    obj = {**VALID_AU, "splitIndex": 3}
    validate_au(obj)


# ── Required fields ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "field_name",
    ["id", "text", "parentSourceID", "sourceReference", "splitIndex", "schemaVersion"],
)
def test_missing_required_field_fails(field_name):
    """Removing any required field causes validation to fail."""
    obj = VALID_AU.copy()
    del obj[field_name]
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── id field ─────────────────────────────────────────────────────────────────

def test_id_wrong_prefix_fails():
    """id with REC_ prefix instead of AU_ fails validation."""
    obj = {**VALID_AU, "id": "REC_" + "a" * 64}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


def test_id_wrong_length_fails():
    """id with 63 hex characters (not 64) fails validation."""
    obj = {**VALID_AU, "id": "AU_" + "a" * 63}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


def test_id_uppercase_hex_fails():
    """id with uppercase hex characters fails (pattern requires lowercase)."""
    obj = {**VALID_AU, "id": "AU_" + "A" * 64}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


def test_id_bad_format_fails():
    """id with arbitrary bad format fails validation."""
    obj = {**VALID_AU, "id": "not_a_valid_id"}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── schemaVersion ─────────────────────────────────────────────────────────────

def test_schema_version_wrong_value_fails():
    """schemaVersion must be exactly 'AU-1.0'."""
    obj = {**VALID_AU, "schemaVersion": "AU-2.0"}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


def test_schema_version_rec_value_fails():
    """schemaVersion 'REC-1.0' is not a valid AU schema version."""
    obj = {**VALID_AU, "schemaVersion": "REC-1.0"}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── text ──────────────────────────────────────────────────────────────────────

def test_text_empty_string_fails():
    """text with empty string fails (minLength: 1)."""
    obj = {**VALID_AU, "text": ""}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── sourceReference ───────────────────────────────────────────────────────────

def test_source_reference_empty_string_fails():
    """sourceReference with empty string fails (minLength: 1)."""
    obj = {**VALID_AU, "sourceReference": ""}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── splitIndex ────────────────────────────────────────────────────────────────

def test_split_index_negative_fails():
    """splitIndex below minimum 0 fails validation."""
    obj = {**VALID_AU, "splitIndex": -1}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


def test_split_index_string_fails():
    """splitIndex as string fails (must be integer)."""
    obj = {**VALID_AU, "splitIndex": "0"}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── additionalProperties: false ───────────────────────────────────────────────

@pytest.mark.parametrize(
    "extra_field",
    ["laneType", "seed_type", "canonical_id", "lane", "seedType", "canonicalId"],
)
def test_extra_field_fails(extra_field):
    """Adding any extra field fails validation (additionalProperties: false)."""
    obj = {**VALID_AU, extra_field: "value"}
    with pytest.raises(AUSchemaValidationError):
        validate_au(obj)


# ── Error message ─────────────────────────────────────────────────────────────

def test_error_message_contains_jsonschema_detail():
    """AUSchemaValidationError message must contain jsonschema detail."""
    obj = {**VALID_AU, "id": "bad_id"}
    with pytest.raises(AUSchemaValidationError) as exc_info:
        validate_au(obj)
    assert len(str(exc_info.value)) > 0


# ── Return value ──────────────────────────────────────────────────────────────

def test_validate_au_returns_none_on_success():
    """validate_au returns None on success."""
    result = validate_au(VALID_AU)
    assert result is None


# ── Module-level schema loading ───────────────────────────────────────────────

def test_schema_loaded_at_module_level():
    """_SCHEMA must be assigned outside any function (module-level load)."""
    import gsd.au_validator as m

    src = inspect.getsource(m)
    assert "_SCHEMA" in src
    assert "def validate_au" in src
    # _SCHEMA assignment must appear before def validate_au in source
    schema_pos = src.index("_SCHEMA")
    func_pos = src.index("def validate_au")
    assert schema_pos < func_pos
