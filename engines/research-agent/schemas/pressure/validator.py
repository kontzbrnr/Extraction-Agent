"""
Pressure canonical object validator.
Validates objects against canonical_pressure_object.schema.json.
"""

import json
from pathlib import Path
from jsonschema import validate, ValidationError


class PressureSchemaValidationError(Exception):
    """Exception raised when pressure object validation fails."""
    pass


# Load schema from file
_schema_path = Path(__file__).parent / "canonical_pressure_object.schema.json"
with open(_schema_path, 'r') as f:
    _SCHEMA = json.load(f)


def validate_pressure_object(obj: dict) -> None:
    """
    Validates obj against canonical_pressure_object.schema.json.
    Raises PressureSchemaValidationError with the original
    jsonschema message on any failure.
    Returns None on success.
    
    Args:
        obj: Dictionary to validate
        
    Raises:
        PressureSchemaValidationError: If validation fails
    """
    try:
        validate(instance=obj, schema=_SCHEMA)
    except ValidationError as e:
        raise PressureSchemaValidationError(str(e))
