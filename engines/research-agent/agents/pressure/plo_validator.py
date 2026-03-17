"""
pressure/plo_validator.py

PLO Validator — Phase 7.1

Validates a Pressure-Legible Observation dict against:
  1. JSON schema (schemas/pressure/plo.schema.json) — structural shape,
     required fields, observation count bounds (4–10), non-empty strings.
  2. Domain membership — each domain must be a member of VALID_DOMAINS.
     (Cannot be expressed as a JSON Schema enum on a nested property
     without hardcoding domain values in the schema file, which would
     create a version-drift risk between schema and plo_schema.py.)
  3. Domain uniqueness — all domain values within a single PLO must be
     distinct. (JSON Schema draft-07 cannot enforce uniqueness on a
     property value within an object array.)

Contract authority:
    PLO-E v2 PDF §III (domain set), §II (count bounds)
    PRESSURE-LEGIBLE-OBSERVATION-EXPANSION-AGENT.md v2.0 §V

Invariant compliance:
    INV-1: Schema loaded at module level. No mutable state.
    INV-5: Deterministic. Identical input always produces identical result.
           No randomness. No runtime-derived values.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError, validate

from engines.research_agent.agents.pressure.plo_schema import VALID_DOMAINS

# ── Version constant ───────────────────────────────────────────────────────────

PLO_VALIDATOR_VERSION: str = "1.0"

# ── Schema (loaded at module level — INV-1) ────────────────────────────────────

_SCHEMA_PATH: Path = (
    Path(__file__).resolve().parents[2] / "schemas" / "pressure" / "plo.schema.json"
)
_PLO_SCHEMA: dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


# ── Exception ─────────────────────────────────────────────────────────────────

class PLOSchemaValidationError(Exception):
    """Raised when PLO validation fails. Message contains the specific reason."""
    pass


# ── Validator ─────────────────────────────────────────────────────────────────

def validate_plo(plo: dict) -> None:
    """Validate a PLO dict against PLO-1.0 schema and domain rules.

    Three-stage validation:
      1. JSON schema — shape, required fields, count bounds, minLength.
      2. Domain membership — each observation domain in VALID_DOMAINS.
      3. Domain uniqueness — no two observations share a domain.

    Args:
        plo: A dict to validate as a Pressure-Legible Observation.

    Returns:
        None on success.

    Raises:
        PLOSchemaValidationError: If any validation stage fails.
            The message identifies the specific failure.

    INV-5: Deterministic. Identical input produces identical outcome.
    """
    # Stage 1 — JSON schema
    try:
        validate(instance=plo, schema=_PLO_SCHEMA)
    except ValidationError as exc:
        raise PLOSchemaValidationError(str(exc)) from exc

    observations: list = plo.get("observations", [])

    # Stage 2 — Domain membership
    for obs in observations:
        domain: str = obs.get("domain", "")
        if domain not in VALID_DOMAINS:
            raise PLOSchemaValidationError(
                f"Invalid domain {domain!r}. "
                f"Must be one of: {sorted(VALID_DOMAINS)}."
            )

    # Stage 3 — Domain uniqueness
    seen: set = set()
    for obs in observations:
        domain = obs.get("domain", "")
        if domain in seen:
            raise PLOSchemaValidationError(
                f"Duplicate domain {domain!r}. "
                f"Each observation must occupy a distinct perceptual domain."
            )
        seen.add(domain)
