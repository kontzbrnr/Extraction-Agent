"""
pressure/psar_validator.py

PSAR Validator — Phase 7.5

Validates a pre-critic PSAR v1.0 dict against:
  1. JSON schema (schemas/pressure/psar.schema.json) — structural shape,
     required fields, proposalID pattern, clusterSignature pattern,
     auditSchemaVersion const, min cardinality bounds.
  2. Enum membership — actorGroup must be in cast_requirement;
     each domainSet member must be in pressure_signal_domain.
     (Cannot be expressed as JSON Schema enum without hardcoding token lists,
     which would create version-drift risk vs. registry.json.)
  3. Derived-field consistency — clusterSize == len(structuralSourceIDs);
     domainDiversityCount == len(domainSet); domainSet == sorted(domainSet).

Contract authority:
    PRESSURE-SIGNAL-AUDIT-RECORD.md v1.0
    Structural Assembler Contract v1.1
    Investigation Report 2026-03-07

Invariant compliance:
    INV-1: Schema loaded at module level. No mutable state.
    INV-4: actorGroup and domainSet membership asserted against
           PRESSURE_TOKEN_REGISTRY (pressure lane only).
    INV-5: Deterministic. Identical input always produces identical result.
           No randomness. No runtime-derived values.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError, validate

from engines.research_agent.enums.role_token_registry import PRESSURE_TOKEN_REGISTRY

# ── Version constant ───────────────────────────────────────────────────────────

PSAR_VALIDATOR_VERSION: str = "1.0"

# ── Schema (loaded at module level — INV-1) ────────────────────────────────────

_SCHEMA_PATH: Path = (
    Path(__file__).resolve().parents[2] / "schemas" / "pressure" / "psar.schema.json"
)
_PSAR_SCHEMA: dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


# ── Exception ──────────────────────────────────────────────────────────────────

class PSARSchemaValidationError(Exception):
    """Raised when PSAR validation fails. Message contains the specific reason."""
    pass


# ── Validator ──────────────────────────────────────────────────────────────────

def validate_psar(psar: dict) -> None:
    """Validate a PSAR v1.0 dict against schema, enum membership, and consistency.

    Three-stage validation:
      1. JSON schema — shape, required fields, pattern constraints, const fields.
      2. Enum membership — actorGroup in cast_requirement;
         each domainSet member in pressure_signal_domain.
      3. Derived-field consistency — clusterSize, domainDiversityCount, domainSet sort.

    Args:
        psar: A dict to validate as a pre-critic PSAR v1.0 object.

    Returns:
        None on success.

    Raises:
        PSARSchemaValidationError: If any validation stage fails.
            The message identifies the specific failure.

    INV-5: Deterministic. Identical input produces identical outcome.
    """
    # Stage 1 — JSON schema
    try:
        validate(instance=psar, schema=_PSAR_SCHEMA)
    except ValidationError as exc:
        raise PSARSchemaValidationError(str(exc)) from exc

    # Stage 2 — Enum membership (pressure lane, INV-4)
    cast_requirement_tokens: frozenset = PRESSURE_TOKEN_REGISTRY["cast_requirement"]
    domain_tokens: frozenset = PRESSURE_TOKEN_REGISTRY["pressure_signal_domain"]

    actor_group: str = psar["actorGroup"]
    if actor_group not in cast_requirement_tokens:
        raise PSARSchemaValidationError(
            f"actorGroup {actor_group!r} is not a valid cast_requirement token. "
            f"Valid tokens: {sorted(cast_requirement_tokens)}."
        )

    domain_set: list[str] = psar["domainSet"]
    for domain in domain_set:
        if domain not in domain_tokens:
            raise PSARSchemaValidationError(
                f"domainSet contains {domain!r} which is not a valid "
                f"pressure_signal_domain token. "
                f"Valid tokens: {sorted(domain_tokens)}."
            )

    # Stage 3 — Derived-field consistency (INV-5)
    structural_source_ids: list[str] = psar["structuralSourceIDs"]
    cluster_size: int = psar["clusterSize"]
    domain_diversity_count: int = psar["domainDiversityCount"]

    if cluster_size != len(structural_source_ids):
        raise PSARSchemaValidationError(
            f"clusterSize {cluster_size} does not match "
            f"len(structuralSourceIDs) {len(structural_source_ids)}. "
            f"These must be equal."
        )

    if domain_diversity_count != len(domain_set):
        raise PSARSchemaValidationError(
            f"domainDiversityCount {domain_diversity_count} does not match "
            f"len(domainSet) {len(domain_set)}. "
            f"These must be equal."
        )

    if domain_set != sorted(domain_set):
        raise PSARSchemaValidationError(
            f"domainSet is not sorted. "
            f"Expected: {sorted(domain_set)}. "
            f"Got: {domain_set}. "
            f"domainSet must be in ascending lexicographic order (INV-5)."
        )
