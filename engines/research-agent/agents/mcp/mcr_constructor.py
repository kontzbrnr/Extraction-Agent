"""
mcp/mcr_constructor.py

Canonical MCR Object Constructor — Phase 10.5

Assembles and validates a single frozen canonical MCR object from a
validated MCR dict and a pre-minted canonical ID.

Does NOT derive canonical IDs. Derivation authority: mcp/mcr_fingerprint.py.
Does NOT mutate input dicts.

Invariants: INV-2 (no ID derivation), INV-3 (no input mutation),
            INV-5 (deterministic assembly)
"""

from __future__ import annotations

from engines.research_agent.agents.mcp.mcma_schema import MCMA_LANE_TYPE, MCMA_MCR_SCHEMA_VERSION, MCMA_VERSION
from engines.research_agent.agents.mcp.mcr_fingerprint import MCR_FINGERPRINT_VERSION, normalize_framing_type
from engines.research_agent.agents.mcp.mcr_id_format import validate_mcr_id
from engines.research_agent.schemas.media.validator import MCRCanonicalValidationError, validate_mcr_canonical_object

MCR_CONSTRUCTOR_VERSION: str = "MCR_CONSTRUCTOR-1.0"

assert MCR_CONSTRUCTOR_VERSION == "MCR_CONSTRUCTOR-1.0"


def build_mcr_canonical_object(
    mcr: dict,
    canonical_id: str,
    enum_registry_version: str,
) -> dict:
    """Assemble and validate a frozen canonical MCR object.

    Args:
        mcr:                   Validated MCR dict from enforce_mcp/MCG.
                               Must contain all MCMA_REQUIRED_MCR_FIELDS.
                               Never mutated (INV-3).
        canonical_id:          Pre-minted MCR canonical ID. Must match
                               ^MCR_[a-f0-9]{64}$.
        enum_registry_version: Enum registry version to embed.

    Returns:
        Validated canonical MCR dict. Passes validate_mcr_canonical_object.

    Raises:
        ValueError:                  canonical_id format invalid (pre-assembly).
        KeyError:                    Required key absent from mcr.
        MCRCanonicalValidationError: Assembled object fails schema validation.

    INV-2: Does not derive canonical IDs.
    INV-3: mcr is never mutated; returned dict is a fresh object.
    INV-5: Identical inputs → identical output.
    """
    validate_mcr_id(canonical_id)

    # Store post-normalized framingType in canonical object to ensure
    # future re-derivation from stored fields produces identical fingerprint.
    framing_type_norm = normalize_framing_type(mcr["framingType"])

    canonical: dict = {
        "id":                  canonical_id,
        "laneType":            MCMA_LANE_TYPE,
        "schemaVersion":       MCMA_MCR_SCHEMA_VERSION,
        "contextDescription":  mcr["contextDescription"],
        "framingType":         framing_type_norm,
        "sourceType":          mcr.get("sourceType"),
        "timeMarker":          mcr.get("timeMarker"),
        "sourceSeedID":        mcr["sourceSeedID"],
        "fingerprintVersion":  MCR_FINGERPRINT_VERSION,
        "contractVersion":     MCMA_VERSION,
        "enumRegistryVersion": enum_registry_version,
    }

    # Scope-lock assertions before schema validation (INV-4).
    assert canonical["laneType"] == MCMA_LANE_TYPE
    assert canonical["contractVersion"] == MCMA_VERSION

    validate_mcr_canonical_object(canonical)  # raises MCRCanonicalValidationError

    return canonical
