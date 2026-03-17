"""
meta/meta_schema.py
Schema loading and validation for canonical CME objects.
"""

from __future__ import annotations

import json
from pathlib import Path

from engines.research_agent.agents.meta.meta_ontology import CME_PERMANENCE_TOKEN, META_SUBTYPE_VALUES, validate_cme_id


class CMESchemaValidationError(Exception):
    """Raised when CME object fails schema validation."""

    def __init__(self, field_errors: list[str]) -> None:
        self.field_errors = field_errors
        super().__init__("; ".join(field_errors))


try:
    _SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "cme.schema.json"
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as schema_handle:
        _CME_SCHEMA = json.load(schema_handle)
except Exception as exc:
    raise RuntimeError(f"Failed to load cme.schema.json: {exc}")


def validate_cme_object(obj: dict) -> None:
    """Validate object against cme.schema.json constraints."""
    errors: list[str] = []
    if not isinstance(obj, dict):
        raise CMESchemaValidationError(["CME object must be a dict"])

    required_fields = set(_CME_SCHEMA["required"])
    allowed_fields = set(_CME_SCHEMA["properties"].keys())

    for field in required_fields:
        if field not in obj:
            errors.append(f"Missing required field: {field}")

    extra_fields = set(obj.keys()) - allowed_fields
    if extra_fields:
        errors.append(f"Unknown fields present: {sorted(extra_fields)!r}")

    if "id" in obj:
        try:
            validate_cme_id(obj["id"])
        except ValueError as exc:
            errors.append(str(exc))

    if obj.get("eventType") != "CME":
        errors.append("eventType must equal 'CME'")

    if obj.get("permanence") != CME_PERMANENCE_TOKEN:
        errors.append("permanence must equal 'permanent'")

    subtype = obj.get("subtype")
    if subtype not in META_SUBTYPE_VALUES:
        errors.append("subtype is invalid")

    for field in (
        "actorRole",
        "action",
        "eventDescription",
        "sourceReference",
        "timestampContext",
    ):
        value = obj.get(field)
        if not isinstance(value, str) or value.strip() == "":
            errors.append(f"{field} must be a non-empty string")

    for field in ("objectRole", "contextRole"):
        value = obj.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be string or null")

    if errors:
        raise CMESchemaValidationError(errors)
