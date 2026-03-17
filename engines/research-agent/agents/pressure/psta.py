"""
pressure/psta.py

Pressure Signal Transformation Agent — Phase 8.2
(Post-PLO-E / Deterministic / Stateless / Content-Derived Identity)

Receives one PLO record (PLO-1.0 format or Phase 8 enriched format).
For each observation in the record, derives the canonical CPS
fingerprint, mints the canonical ID, and returns a validated canonical
pressure signal object.

Pipeline position (Phase 8, RULING 1 — clustering deferred):
    PLO-E → PSTA → CPS objects

PSTA is purely transformational and identity-minting. It does NOT:
  * Evaluate pressure strength
  * Reclassify signals
  * Perform cross-run deduplication
  * Access global state or registries
  * Generate sequential identifiers

Contract authority: PRESSURE-SIGNAL-TRANSFORMATION-AGENT.md v4
Governance rulings: 2026-03-08 (Rulings 1–4)
Invariants: INV-1 (memoryless), INV-2 (sole mint authority),
            INV-3 (immutability), INV-5 (replay determinism)
"""

from __future__ import annotations

from engines.research_agent.agents.pressure.cps_constructor import build_cps_object
from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_V1, derive_cps_fingerprint
from engines.research_agent.agents.pressure.psta_schema import (
    PSTA_AUDIT_SCHEMA_VERSION,
    PSTA_DEFAULT_ENUM_REGISTRY_VERSION,
    PSTA_VERSION,
    REJECT_PSTA_SCHEMA_INVALID,
    STATUS_DUPLICATE,
    STATUS_NEW_CANONICAL,
)
from engines.research_agent.schemas.pressure.fallback_tokens import PRESSURE_FALLBACK_TOKENS
from engines.research_agent.schemas.pressure.validator import PressureSchemaValidationError

# ── Field sourcing ──────────────────────────────────────────────────────────────
# PLO-1.0 uses "domain"; Phase 8 enriched PLO may use "pressureSignalDomain".
# PSTA accepts either, preferring the canonical CPS key name.
_PLO_DOMAIN_FALLBACK_KEY: str = "domain"


def _apply_fallback(key: str, raw_value: object) -> object:
    """
    Return raw_value if not None; otherwise return the
    PRESSURE_FALLBACK_TOKENS value for key.
    Preserves non-string types (e.g. int for tier).
    """
    if raw_value is not None:
        return raw_value
    return PRESSURE_FALLBACK_TOKENS.get(key)


def _null_to_empty(value: object) -> object:
    """
    Convert None to "" for fingerprint computation only.
    PSTA v4 §V: null → empty token.
    Phase 8.1's _normalize(None) yields "none", not "".
    PSTA normalises nulls here, before handing off to derive_cps_fingerprint.
    """
    return "" if value is None else value


def _extract_cps_fields(obs: dict, source_seed: str) -> dict:
    """
    Extract and coerce CPS fingerprint fields from one PLO observation dict.

    Field sourcing (RULING 2, PSTA v4 §III):
        pressureSignalDomain  ← obs["pressureSignalDomain"] ?? obs["domain"] ?? fallback
        observation           ← obs["observation"] ?? fallback
        sourceSeed            ← plo_record["sourceSeedText"]
        remaining 7 fields    ← obs[field] ?? PRESSURE_FALLBACK_TOKENS[field]

    Returns a dict with exactly the 10 CPS fingerprint field names.
    Values are post-fallback but may still be None (e.g. tier).
    """
    domain_raw = obs.get("pressureSignalDomain") or obs.get(_PLO_DOMAIN_FALLBACK_KEY)

    return {
        "signalClass":          _apply_fallback("signalClass",          obs.get("signalClass")),
        "environment":          _apply_fallback("environment",          obs.get("environment")),
        "pressureSignalDomain": _apply_fallback("pressureSignalDomain", domain_raw),
        "pressureVector":       _apply_fallback("pressureVector",       obs.get("pressureVector")),
        "signalPolarity":       _apply_fallback("signalPolarity",       obs.get("signalPolarity")),
        "observationSource":    _apply_fallback("observationSource",    obs.get("observationSource")),
        "castRequirement":      _apply_fallback("castRequirement",      obs.get("castRequirement")),
        "tier":                 _apply_fallback("tier",                 obs.get("tier")),
        "observation":          _apply_fallback("observation",          obs.get("observation")),
        "sourceSeed":           source_seed if source_seed else PRESSURE_FALLBACK_TOKENS["sourceSeed"],
    }


def _fingerprint_fields(cps_fields: dict) -> dict:
    """
    Return a copy of cps_fields with None values replaced by ""
    for fingerprint computation (PSTA v4 §V: null → empty token).
    Does NOT modify cps_fields in place (INV-3).
    """
    return {k: _null_to_empty(v) for k, v in cps_fields.items()}


def enforce_psta(
    plo_record: dict,
    enum_registry_version: str = PSTA_DEFAULT_ENUM_REGISTRY_VERSION,
) -> tuple[list[dict], list[dict], dict]:
    """
    PSTA entry point — Phase 8.2.

    Accepts a PLO record (PLO-1.0 format or Phase 8 enriched format).
    Produces one canonical CPS object per observation, skipping
    within-call duplicates and schema-invalid outputs.

    Within-call dedup (RULING 4 / PSTA v4 §XIII-6):
        If two observations in the same PLO record produce identical
        canonical IDs, the second is recorded as STATUS_DUPLICATE
        in the rejection list and is NOT emitted as a canonical object.
        Cross-run dedup is out of scope (INV-1: stateless).

    Args:
        plo_record:
            PLO record dict. Expected keys:
                "sourceSeedText" (str) — maps to CPS sourceSeed
                "observations"   (list[dict]) — one dict per observation
            Observations may carry any/all of the 10 CPS fingerprint
            field names. Missing or None values receive fallback tokens.
        enum_registry_version:
            Enum registry version string to embed in each CPS object.
            Defaults to PSTA_DEFAULT_ENUM_REGISTRY_VERSION.

    Returns:
        canonical_objects (list[dict]):
            Validated CPS objects. Empty if no observations pass.
        rejections (list[dict]):
            Dicts describing skipped observations
            (STATUS_DUPLICATE or REJECT_PSTA_SCHEMA_INVALID).
        audit (dict):
            Audit record per PSTA_AUDIT-1.0. No timestamp (INV-5).

    Invariants enforced:
        INV-1  — No mutable module-level state; no cross-call memory.
        INV-2  — Sole canonical ID mint authority: derive_cps_fingerprint.
        INV-3  — plo_record and each observation are never mutated.
        INV-5  — Identical plo_record → identical output, bitwise.
    """
    source_seed: str = plo_record.get("sourceSeedText") or ""
    observations: list[dict] = list(plo_record.get("observations") or [])

    canonical_objects: list[dict] = []
    rejections: list[dict] = []
    seen_ids: set[str] = set()          # within-call dedup; not persisted

    for obs in observations:
        obs_snap = dict(obs)            # INV-3: snapshot; original untouched

        # 1. Extract + coerce CPS fields (fallbacks applied; None preserved)
        cps_fields = _extract_cps_fields(obs_snap, source_seed)

        # 2. Derive canonical ID — null fields must be "" (PSTA v4 §V)
        fp_fields = _fingerprint_fields(cps_fields)
        canonical_id: str = derive_cps_fingerprint(fp_fields)

        # 3. Within-call dedup gate (RULING 4)
        if canonical_id in seen_ids:
            rejections.append({
                "status":           STATUS_DUPLICATE,
                "canonicalId":      canonical_id,
                "sourceObservation": obs_snap,
                "schemaVersion":    PSTA_AUDIT_SCHEMA_VERSION,
            })
            continue
        seen_ids.add(canonical_id)

        # 4. Assemble and validate CPS object (constructor validates internally)
        try:
            cps_obj = build_cps_object(cps_fields, canonical_id, enum_registry_version)
        except PressureSchemaValidationError as exc:
            rejections.append({
                "status":           REJECT_PSTA_SCHEMA_INVALID,
                "canonicalId":      canonical_id,
                "sourceObservation": obs_snap,
                "validationError":  str(exc),
                "schemaVersion":    PSTA_AUDIT_SCHEMA_VERSION,
            })
            continue

        canonical_objects.append(cps_obj)

    duplicate_count = sum(1 for r in rejections if r.get("status") == STATUS_DUPLICATE)
    rejection_count = sum(1 for r in rejections if r.get("status") != STATUS_DUPLICATE)

    audit: dict = {
        "schemaVersion":         PSTA_AUDIT_SCHEMA_VERSION,
        "pstaVersion":           PSTA_VERSION,
        "fingerprintVersion":    CPS_FINGERPRINT_V1,
        "enumRegistryVersion":   enum_registry_version,
        "inputObservationCount": len(observations),
        "newCanonicalCount":     len(canonical_objects),
        "duplicateCount":        duplicate_count,
        "rejectionCount":        rejection_count,
    }

    return canonical_objects, rejections, audit
