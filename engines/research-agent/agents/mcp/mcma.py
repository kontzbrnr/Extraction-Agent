"""
mcp/mcma.py

Media Context Mint Authority (MCMA) — Phase 10.5

Stateless canonical identity mint for Media Context Records.

Receives a validated MCR dict (post-MCP, post-MCG). Derives the
MCR_FINGERPRINT_V1 canonical ID, enforces within-call dedup,
assembles the frozen canonical MCR object.

Pipeline position:
    MCG → MCMA (this agent) → CIV → MediaContext registry lane

Does NOT:
    * Read from or write to the registry
    * Perform cross-run dedup (see mcr_dedup.py)
    * Assign framingType (must be present in MCR input)
    * Mutate any input dict

Contract authority: MEDIA-LANE IDENTITY PHILOSOPHY — GOVERNING RULING v1
                    Rulings 10.4-A through 10.4-D

Invariants:
    INV-1: No module-level mutable state. seen_ids set is local per call.
    INV-2: Sole canonical ID mint authority: derive_mcr_fingerprint.
    INV-3: Input MCR never mutated.
    INV-4: Scope-lock on laneType == "MEDIA".
    INV-5: Identical MCR input always produces identical output.
"""

from __future__ import annotations

from engines.research_agent.agents.mcp.mcma_schema import (
    MCMA_AUDIT_SCHEMA_VERSION,
    MCMA_DEFAULT_ENUM_REGISTRY_VERSION,
    MCMA_REQUIRED_MCR_FIELDS,
    MCMA_VERSION,
    REJECT_MCMA_INVALID_FRAMING_TYPE,
    REJECT_MCMA_INVALID_INPUT,
    REJECT_MCMA_MISSING_FIELD,
    REJECT_MCMA_SCHEMA_INVALID,
    REJECT_MCMA_WRONG_LANE,
    STATUS_DUPLICATE,
    STATUS_NEW_CANONICAL,
    VALID_MCR_FRAMING_TYPES,
)
from engines.research_agent.agents.mcp.mcr_constructor import build_mcr_canonical_object
from engines.research_agent.agents.mcp.mcr_fingerprint import MCR_FINGERPRINT_VERSION, derive_mcr_fingerprint
from engines.research_agent.schemas.media.validator import MCRCanonicalValidationError

_MEDIA_LANE_TYPE: str = "MEDIA"


def _build_rejection(mcr: object, reason_code: str) -> dict:
    seed_ref = mcr.get("sourceSeedID") if isinstance(mcr, dict) else None
    return {
        "status": reason_code,
        "sourceSeedID": seed_ref,
        "schemaVersion": MCMA_AUDIT_SCHEMA_VERSION,
    }


def enforce_mcma(
    mcr: object,
    enum_registry_version: str = MCMA_DEFAULT_ENUM_REGISTRY_VERSION,
) -> tuple[list[dict], list[dict], dict]:
    """MCMA entry point — Phase 10.5.

    Accepts a validated MCR dict. Derives canonical ID, enforces
    within-call dedup, and emits a frozen canonical MCR object.

    Args:
        mcr:                   MCR dict as emitted by enforce_mcp, validated
                               by enforce_mcg, and enriched with framingType.
                               Never mutated (INV-3).
        enum_registry_version: Enum registry version string to embed.
                               Defaults to MCMA_DEFAULT_ENUM_REGISTRY_VERSION.

    Returns:
        canonical_objects (list[dict]):
            List of zero or one validated canonical MCR objects.
        rejections (list[dict]):
            Rejection records (invalid input, duplicate, schema failure).
        audit (dict):
            MCMA_AUDIT-1.0 record. No timestamps (INV-5).

    INV-1: seen_ids is a local set — not persisted across calls.
    INV-2: canonical ID derived exclusively via derive_mcr_fingerprint.
    INV-3: mcr is never mutated.
    INV-4: Scope-lock on laneType == "MEDIA".
    INV-5: Deterministic. Identical mcr → identical output.
    """
    canonical_objects: list[dict] = []
    rejections: list[dict] = []
    seen_ids: set[str] = set()

    # ── Input type guard ──────────────────────────────────────────────────────
    if not isinstance(mcr, dict):
        rejections.append(_build_rejection(mcr, REJECT_MCMA_INVALID_INPUT))
        return canonical_objects, rejections, _build_audit(
            MCMA_DEFAULT_ENUM_REGISTRY_VERSION, 0, 0, 0, 1
        )

    mcr_snap: dict = dict(mcr)   # INV-3: snapshot; original untouched

    # ── Required field guard ──────────────────────────────────────────────────
    for field in MCMA_REQUIRED_MCR_FIELDS:
        if field not in mcr_snap:
            rejections.append(_build_rejection(mcr_snap, REJECT_MCMA_MISSING_FIELD))
            return canonical_objects, rejections, _build_audit(
                enum_registry_version, 0, 0, 0, 1
            )

    # ── Scope-lock (INV-4) ────────────────────────────────────────────────────
    if mcr_snap.get("laneType") != _MEDIA_LANE_TYPE:
        rejections.append(_build_rejection(mcr_snap, REJECT_MCMA_WRONG_LANE))
        return canonical_objects, rejections, _build_audit(
            enum_registry_version, 0, 0, 0, 1
        )

    # ── framingType validation ────────────────────────────────────────────────
    framing_raw = mcr_snap.get("framingType")
    if (
        not isinstance(framing_raw, str)
        or framing_raw.strip().lower() not in VALID_MCR_FRAMING_TYPES
    ):
        rejections.append(_build_rejection(mcr_snap, REJECT_MCMA_INVALID_FRAMING_TYPE))
        return canonical_objects, rejections, _build_audit(
            enum_registry_version, 0, 0, 0, 1
        )

    # ── Canonical ID derivation (INV-2) ───────────────────────────────────────
    canonical_id: str = derive_mcr_fingerprint({
        "contextDescription": mcr_snap["contextDescription"],
        "framingType": framing_raw,
    })

    # ── Within-call dedup (INV-1) ─────────────────────────────────────────────
    if canonical_id in seen_ids:
        rejections.append({
            "status": STATUS_DUPLICATE,
            "canonicalId": canonical_id,
            "sourceSeedID": mcr_snap.get("sourceSeedID"),
            "schemaVersion": MCMA_AUDIT_SCHEMA_VERSION,
        })
        return canonical_objects, rejections, _build_audit(
            enum_registry_version, 1, 0, 1, 0
        )
    seen_ids.add(canonical_id)

    # ── Canonical object assembly and freeze ──────────────────────────────────
    try:
        canonical_obj = build_mcr_canonical_object(mcr_snap, canonical_id, enum_registry_version)
    except MCRCanonicalValidationError:
        rejections.append(_build_rejection(mcr_snap, REJECT_MCMA_SCHEMA_INVALID))
        return canonical_objects, rejections, _build_audit(
            enum_registry_version, 1, 0, 0, 1
        )

    canonical_objects.append(canonical_obj)

    return canonical_objects, rejections, _build_audit(
        enum_registry_version, 1, 1, 0, 0
    )


def _build_audit(
    enum_registry_version: str,
    input_count: int,
    new_canonical_count: int,
    duplicate_count: int,
    rejection_count: int,
) -> dict:
    return {
        "schemaVersion":         MCMA_AUDIT_SCHEMA_VERSION,
        "mcmaVersion":           MCMA_VERSION,
        "fingerprintVersion":    MCR_FINGERPRINT_VERSION,
        "enumRegistryVersion":   enum_registry_version,
        "inputCount":            input_count,
        "newCanonicalCount":     new_canonical_count,
        "duplicateCount":        duplicate_count,
        "rejectionCount":        rejection_count,
    }
