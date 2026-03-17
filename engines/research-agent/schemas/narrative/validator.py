"""
Narrative CSN canonical object validator.
Validates objects against canonical_narrative_csn_object.schema.json.
"""

import json
from pathlib import Path
from jsonschema import validate, ValidationError


class NarrativeCSNSchemaValidationError(Exception):
    """Exception raised when narrative CSN object validation fails."""
    pass


# Load schema from file
_schema_path = Path(__file__).parent / "canonical_narrative_csn_object.schema.json"
with open(_schema_path, 'r') as f:
    _SCHEMA = json.load(f)


def validate_narrative_csn_object(obj: dict) -> None:
    """
    Validates obj against canonical_narrative_csn_object.schema.json.
    Raises NarrativeCSNSchemaValidationError with the original
    jsonschema message on any failure.
    Returns None on success.
    
    Args:
        obj: Dictionary to validate
        
    Raises:
        NarrativeCSNSchemaValidationError: If validation fails
    """
    try:
        validate(instance=obj, schema=_SCHEMA)
    except ValidationError as e:
        raise NarrativeCSNSchemaValidationError(str(e))
