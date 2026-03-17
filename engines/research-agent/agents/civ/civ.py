"""
civ/civ.py

Canonical Integrity Validator (CIV)

Stateless structural firewall. Validates canonical objects post-mint,
pre-registry-commit. Runs 7 ordered checks. First failure returns
immediately. Input is never mutated.

Pipeline positions:
    PSTA   → CIV → Registry Commit  (Pressure lane)
    META   → CIV → Registry Commit  (CME)
    SANTA  → CIV → Registry Commit  (CSN)
    MCMA   → CIV → Registry Commit  (MediaContext)

Contract authority: CANONICAL-INTEGRITY-VALIDATOR.md v1.0

Implementation status:
    Check 1 (Schema Completeness)   — Phase 11.2 ✓
    Check 2 (Enum Compliance)       — Phase 11.3 stub
    Check 3 (Identity Abstraction)  — Phase 11.4 stub
    Check 4 (Time Binding)          — Phase 11.5 stub
    Check 5 (ID Integrity)          — Phase 11.6 stub
    Check 6 (Version Snapshot)      — Phase 11.7 stub
    Check 7 (Lane Contamination)    — Phase 11.8 stub

Invariant compliance:
    INV-1: No module-level mutable state. No cross-call memory.
    INV-3: Input canonical object never mutated.
    INV-4: Lane-aware dispatch — TIME_BINDING_LANES gates check 4.
    INV-5: Checks execute in fixed order 1→7. Identical input always
           produces identical verdict.
"""

from __future__ import annotations

from engines.research_agent.agents.mcp.lane_isolation_audit import (
    MEDIA_SEMANTIC_FIELDS,
    NARRATIVE_SEMANTIC_FIELDS,
    PRESSURE_SEMANTIC_FIELDS,
)

from engines.research_agent.enums.role_token_registry import (
    MEDIA_ENUM_REGISTRY_VERSION,
    MEDIA_TOKEN_REGISTRY,
    NARRATIVE_ENUM_REGISTRY_VERSION,
    NARRATIVE_TOKEN_REGISTRY,
    PRESSURE_ENUM_REGISTRY_VERSION,
    PRESSURE_TOKEN_REGISTRY,
)
from engines.research_agent.agents.extraction.proper_noun_detector import contains_proper_noun
from engines.research_agent.agents.mcp.mcr_fingerprint import MCRFingerprintInputError, derive_mcr_fingerprint
from engines.research_agent.agents.meta.meta_ruleset import derive_cme_fingerprint
from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_FIELDS, derive_cps_fingerprint
from engines.research_agent.agents.santa.santa_ruleset import derive_csn_fingerprint
from engines.research_agent.schemas.cme_validator import (
    CMECanonicalValidationError,
    validate_cme_canonical_object,
)
from engines.research_agent.schemas.media.validator import (
    MCRCanonicalValidationError,
    validate_mcr_canonical_object,
)
from engines.research_agent.schemas.narrative.validator import (
    NarrativeCSNSchemaValidationError,
    validate_narrative_csn_object,
)
from engines.research_agent.schemas.pressure.validator import (
    PressureSchemaValidationError,
    validate_pressure_object,
)

from engines.research_agent.agents.civ.civ_schema import (
    CIV_VERSION,
    CIV_VERDICT_SCHEMA_VERSION,
    CME_IDENTITY_SCAN_FIELDS,
    CME_IDENTITY_SCAN_NULLABLE_FIELDS,
    CME_REGISTRY_ENUM_FIELDS,
    CPS_ENUM_FIELD_MAP,
    CPS_IDENTITY_SCAN_FIELDS,
    CSN_ENUM_FIELD_MAP,
    CSN_IDENTITY_SCAN_FIELDS,
    CSN_IDENTITY_SCAN_NULLABLE_FIELDS,
    CSN_NULLABLE_ENUM_FIELDS,
    MEDIA_CONTEXT_IDENTITY_SCAN_FIELDS,
    MEDIA_CONTEXT_REGISTRY_ENUM_FIELDS,
    REJECT_ENUM_INVALID,
    REJECT_ID_HASH_MISMATCH,
    REJECT_IDENTITY_CONTAMINATION,
    REJECT_LANE_FIELD_CONTAMINATION,
    REJECT_SCHEMA_INCOMPLETE,
    REJECT_TIME_SHAPE_INVALID,
    REJECT_VERSION_MISMATCH,
    REQUIRED_CYCLE_SNAPSHOT_KEYS,
    STAGE_1_SCHEMA_COMPLETENESS,
    STAGE_2_ENUM_COMPLIANCE,
    STAGE_3_IDENTITY_ABSTRACTION,
    STAGE_4_TIME_BINDING,
    STAGE_5_ID_INTEGRITY,
    STAGE_6_VERSION_SNAPSHOT,
    STAGE_7_LANE_CONTAMINATION,
    TIMESTAMP_CONTEXT_PATTERN,
    TIMESTAMP_CONTEXT_PHASE_TOKENS,
    TIME_BINDING_LANES,
    VALID_CIV_LANES,
    VERDICT_FAIL,
    VERDICT_PASS,
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _make_verdict(
    lane: str,
    verdict: str,
    reason_code: str | None,
    failure_stage: str | None,
) -> dict:
    return {
        "schemaVersion":  CIV_VERDICT_SCHEMA_VERSION,
        "civVersion":     CIV_VERSION,
        "lane":           lane,
        "verdict":        verdict,
        "reasonCode":     reason_code,
        "failureStage":   failure_stage,
    }


def _build_fail(
    obj: dict,
    lane: str,
    reason_code: str,
    stage: str,
) -> tuple[bool, dict, dict]:
    rejection = {
        "rejected":      True,
        "reasonCode":    reason_code,
        "failureStage":  stage,
        "civVersion":    CIV_VERSION,
        "lane":          lane,
        "objectRef":     obj.get("id") or obj.get("canonicalId"),
    }
    verdict = _make_verdict(lane, VERDICT_FAIL, reason_code, stage)
    return (False, rejection, verdict)


# ── Check functions ───────────────────────────────────────────────────────────
# Signature: (obj: dict, lane: str, cycle_snapshot: dict) -> tuple[bool, str|None]
# Returns: (passed: bool, reason_code: str|None)
# On PASS: (True, None). On FAIL: (False, REJECT_* code).
# Note: enforce_civ ignores the reason_code return value — reason code is
# sourced from _ORDERED_CHECKS. The second element is for internal clarity only.
# Checks 2–7 remain stubs (phases 11.3–11.8).

def _check_schema_completeness(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """CIV §III.1: Schema Completeness.

    Delegates to the per-lane JSON Schema validator. A single jsonschema
    call covers all three sub-checks because every canonical schema uses
    ``additionalProperties: false``:

        1. All required fields present       — ``required`` array in schema
        2. No unknown/extra fields           — ``additionalProperties: false``
        3. No missing enum fields; values valid — ``enum``/``const`` constraints

    Lane → validator mapping:
        CPS          → schemas.pressure.validator.validate_pressure_object
        CME          → schemas.cme_validator.validate_cme_canonical_object
            CME_VERSION_FIELD_MAP,
            CPS_VERSION_FIELD_MAP,
            CSN_VERSION_FIELD_MAP,
            MEDIA_CONTEXT_VERSION_FIELD_MAP,
        CSN          → schemas.narrative.validator.validate_narrative_csn_object
        MediaContext → schemas.media.validator.validate_mcr_canonical_object

    Args:
        obj:           Canonical object dict. Never mutated (INV-3).
        lane:          Registry lane key. Pre-validated by enforce_civ entry
                       guard; guaranteed to be in VALID_CIV_LANES.
        cycle_snapshot: Unused in this check. Present for uniform signature.

    Returns:
        (True, None)                      on PASS.
        (False, REJECT_SCHEMA_INCOMPLETE) on any validation failure.
    """
    try:
        if lane == "CPS":
            validate_pressure_object(obj)
        elif lane == "CME":
            validate_cme_canonical_object(obj)
        elif lane == "CSN":
            validate_narrative_csn_object(obj)
        elif lane == "MediaContext":
            validate_mcr_canonical_object(obj)
    except (
        PressureSchemaValidationError,
        CMECanonicalValidationError,
        NarrativeCSNSchemaValidationError,
        MCRCanonicalValidationError,
    ):
        return (False, REJECT_SCHEMA_INCOMPLETE)
    return (True, None)


def _check_enum_compliance(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """CIV §III.2: Enum Registry Compliance.

    Verifies that all enum-typed fields in the canonical object carry
    tokens that exist in the live registry loaded by role_token_registry.py,
    and that enumRegistryVersion (where the lane schema includes it) matches
    the live pinned registry version.

    Lane-specific notes:
        CPS          — 8 enum fields; camelCase→snake_case mapping required;
                       enumRegistryVersion present in schema, compared to
                       PRESSURE_ENUM_REGISTRY_VERSION.
        CME          — subtype only; actorRole/action/objectRole/contextRole
                       are governance-gap fields (enums/media/registry.json
                       §openItems) and are explicitly skipped; no
                       enumRegistryVersion field in CME schema.
        CSN          — actorRole, action, objectRole, contextRole, subclass;
                       subclass maps to ncaSubclass in registry;
                       objectRole and contextRole are nullable (skip if None);
                       no enumRegistryVersion field in CSN schema.
        MediaContext — framingType only; enumRegistryVersion present in
                       schema, compared to MEDIA_ENUM_REGISTRY_VERSION.

    Args:
        obj:            Canonical object dict. Never mutated (INV-3).
        lane:           Registry lane key; pre-validated by enforce_civ.
        cycle_snapshot: Unused in this check. Present for uniform signature.

    Returns:
        (True, None)               on PASS.
        (False, REJECT_ENUM_INVALID) on any version mismatch or token miss.
    """
    if lane == "CPS":
        if obj.get("enumRegistryVersion") != PRESSURE_ENUM_REGISTRY_VERSION:
            return (False, REJECT_ENUM_INVALID)
        for obj_field, registry_key in CPS_ENUM_FIELD_MAP.items():
            if obj.get(obj_field) not in PRESSURE_TOKEN_REGISTRY[registry_key]:
                return (False, REJECT_ENUM_INVALID)

    elif lane == "CME":
        # No enumRegistryVersion in CME schema — version check skipped.
        for field in CME_REGISTRY_ENUM_FIELDS:
            if obj.get(field) not in MEDIA_TOKEN_REGISTRY[field]:
                return (False, REJECT_ENUM_INVALID)

    elif lane == "CSN":
        # No enumRegistryVersion in CSN schema — version check skipped.
        for obj_field, registry_key in CSN_ENUM_FIELD_MAP.items():
            value = obj.get(obj_field)
            if value is None and obj_field in CSN_NULLABLE_ENUM_FIELDS:
                continue
            if value not in NARRATIVE_TOKEN_REGISTRY[registry_key]:
                return (False, REJECT_ENUM_INVALID)

    elif lane == "MediaContext":
        if obj.get("enumRegistryVersion") != MEDIA_ENUM_REGISTRY_VERSION:
            return (False, REJECT_ENUM_INVALID)
        for field in MEDIA_CONTEXT_REGISTRY_ENUM_FIELDS:
            if obj.get(field) not in MEDIA_TOKEN_REGISTRY[field]:
                return (False, REJECT_ENUM_INVALID)

    return (True, None)


def _check_identity_abstraction(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """CIV §III.3: Identity Abstraction Integrity.

    Scans per-lane structural text fields using contains_proper_noun().
    Rejects any object where a non-initial token in a scanned field
    matches ^[A-Z][a-z]+$ (len >= 2 after punctuation strip).

    Detection is delegated entirely to extraction.proper_noun_detector.
    PROPER_NOUN_DETECTOR_VERSION = "1.0" is pinned — INV-5 guaranteed.

    Documented limitation (inherited from detector contract):
        A proper noun appearing only as the first token of a field value
        will not be detected. This is an accepted constraint of
        pattern-based detection without NLP.

    Lane → scanned fields:
        CPS          — observation, sourceSeed
        CME          — actorRole, action, eventDescription, sourceReference,
                       timestampContext; objectRole and contextRole if non-None
        CSN          — same as CME
        MediaContext — contextDescription

    Args:
        obj:            Canonical object dict. Never mutated (INV-3).
        lane:           Registry lane key; pre-validated by enforce_civ.
        cycle_snapshot: Unused in this check. Present for uniform signature.

    Returns:
        (True, None)                        on PASS.
        (False, REJECT_IDENTITY_CONTAMINATION) on any proper noun detected.
    """
    if lane == "CPS":
        scan_fields = CPS_IDENTITY_SCAN_FIELDS
        nullable_fields: frozenset[str] = frozenset()
    elif lane == "CME":
        scan_fields = CME_IDENTITY_SCAN_FIELDS
        nullable_fields = CME_IDENTITY_SCAN_NULLABLE_FIELDS
    elif lane == "CSN":
        scan_fields = CSN_IDENTITY_SCAN_FIELDS
        nullable_fields = CSN_IDENTITY_SCAN_NULLABLE_FIELDS
    else:  # MediaContext
        scan_fields = MEDIA_CONTEXT_IDENTITY_SCAN_FIELDS
        nullable_fields = frozenset()

    for field in scan_fields:
        value = obj.get(field)
        if isinstance(value, str) and contains_proper_noun(value):
            return (False, REJECT_IDENTITY_CONTAMINATION)

    for field in nullable_fields:
        value = obj.get(field)
        if value is None:
            continue
        if isinstance(value, str) and contains_proper_noun(value):
            return (False, REJECT_IDENTITY_CONTAMINATION)

    return (True, None)


def _check_time_binding(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """CIV §III.4: Time Binding Compliance.

    Applies to TIME_BINDING_LANES only (CME, CSN). The enforce_civ
    dispatcher skips this check entirely for CPS and MediaContext.

    Validates that timestampContext is a non-empty string conforming to
    the governed seasonal phase vocabulary:

        ^(?:\\d{4}_)?(?:early_season|late_season|mid_season|offseason
                        |playoffs|trade_deadline_window)$

    Bare phase tokens and year-prefixed phase tokens are both valid.
    Old week-bucket format (YYYY_WXX) is not valid.

    ID exclusion verification (timestampContext not in fingerprint) is
    the sole responsibility of Check 5 — not performed here.
    Ruling B — Phase 11.5.

    Args:
        obj:            Canonical object dict. Never mutated (INV-3).
        lane:           Registry lane key; pre-validated by enforce_civ.
                        Guaranteed to be in TIME_BINDING_LANES at call site.
        cycle_snapshot: Unused in this check. Present for uniform signature.

    Returns:
        (True, None)                  on PASS.
        (False, REJECT_TIME_SHAPE_INVALID) on missing, non-string, empty,
                                           or non-conforming value.
    """
    value = obj.get("timestampContext")
    if not isinstance(value, str) or not value.strip():
        return (False, REJECT_TIME_SHAPE_INVALID)
    if not TIMESTAMP_CONTEXT_PATTERN.match(value):
        return (False, REJECT_TIME_SHAPE_INVALID)
    return (True, None)


def _check_id_integrity(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """CIV §III.5: ID Integrity Check.

    Re-derives the canonical ID from the object's structural fields using
    the lane's authoritative fingerprint function. Rejects if the derived
    ID does not match the stored ID field.

    This check confirms:
        1. The stored ID was produced by the correct recipe.
        2. No fingerprint-participating field was mutated post-mint.
        3. timestampContext (CME/CSN) is excluded from identity — verified
           implicitly because the recipe does not include it; re-derivation
           without it produces the matching stored ID (Ruling B, Phase 11.5).

    Lane → fingerprint authority → stored ID field:
        CPS          → pressure.cps_fingerprint.derive_cps_fingerprint
                       10 fields from CPS_FINGERPRINT_FIELDS (tier as int)
                       permanence: n/a — no permanence in CPS recipe
                       stored field: "canonicalId"
        CME          → meta.meta_ruleset.derive_cme_fingerprint
                       fields: actorRole, action, objectRole, contextRole,
                               subtype, sourceReference
                       permanence: hardcoded inside function via
                                   CME_PERMANENCE_TOKEN — not extracted from obj
                       stored field: "id"
        CSN          → santa.santa_ruleset.derive_csn_fingerprint
                       fields: actorRole, action, objectRole, contextRole,
                               subclass, sourceReference
                       permanence: hardcoded inside function via
                                   SANTA_PERMANENCE_NORM — not extracted from obj
                       stored field: "id"
        MediaContext → mcp.mcr_fingerprint.derive_mcr_fingerprint
                       fields: contextDescription, framingType
                       stored field: "id"

    Args:
        obj:            Canonical object dict. Never mutated (INV-3).
        lane:           Registry lane key; pre-validated by enforce_civ.
        cycle_snapshot: Unused in this check. Present for uniform signature.

    Returns:
        (True, None)                  on PASS (derived == stored).
        (False, REJECT_ID_HASH_MISMATCH) on mismatch or re-derivation error.
    """
    try:
        if lane == "CPS":
            derived = derive_cps_fingerprint(
                {field: obj[field] for field in CPS_FINGERPRINT_FIELDS}
            )
            stored = obj.get("canonicalId")

        elif lane == "CME":
            derived = derive_cme_fingerprint({
                "actorRole":       obj.get("actorRole"),
                "action":          obj.get("action"),
                "objectRole":      obj.get("objectRole"),
                "contextRole":     obj.get("contextRole"),
                "subtype":         obj.get("subtype"),
                "sourceReference": obj.get("sourceReference"),
            })
            stored = obj.get("id")

        elif lane == "CSN":
            derived = derive_csn_fingerprint({
                "actorRole":       obj.get("actorRole"),
                "action":          obj.get("action"),
                "objectRole":      obj.get("objectRole"),
                "contextRole":     obj.get("contextRole"),
                "subclass":        obj.get("subclass"),
                "sourceReference": obj.get("sourceReference"),
            })
            stored = obj.get("id")

        else:  # MediaContext
            derived = derive_mcr_fingerprint({
                "contextDescription": obj.get("contextDescription"),
                "framingType":        obj.get("framingType"),
            })
            stored = obj.get("id")

    except (KeyError, MCRFingerprintInputError):
        return (False, REJECT_ID_HASH_MISMATCH)

    if derived != stored:
        return (False, REJECT_ID_HASH_MISMATCH)

    return (True, None)


def _check_version_snapshot(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """Stub — CIV §III.6: Version Snapshot Integrity.

    Will verify: schemaVersion, enumVersion, contractVersion in object
    match orchestrator cycle_snapshot values.
    Implementation: Phase 11.7.
    """
    return (True, None)


def _check_lane_contamination(
    obj: dict, lane: str, cycle_snapshot: dict
) -> tuple[bool, str | None]:
    """CIV §III.7: Cross-Family Field Contamination.

    Verifies that no canonical object carries field keys belonging to a
    foreign lane's semantic field set. Uses the authoritative field sets
    from engines.research_agent.agents.mcp.lane_isolation_audit, which enforces zero overlap between
    all three sets at import time via assertion.

    Forbidden key sets per lane:
        CPS          — NARRATIVE_SEMANTIC_FIELDS ∪ MEDIA_SEMANTIC_FIELDS
        CME          — PRESSURE_SEMANTIC_FIELDS  ∪ MEDIA_SEMANTIC_FIELDS
        CSN          — PRESSURE_SEMANTIC_FIELDS  ∪ MEDIA_SEMANTIC_FIELDS
        MediaContext — PRESSURE_SEMANTIC_FIELDS  ∪ NARRATIVE_SEMANTIC_FIELDS

    Under normal operation this check passes for any object that survived
    check 1 (schema completeness), because additionalProperties: false in
    all four canonical schemas prevents foreign fields from entering.
    This check is an explicit defense-in-depth layer (INV-4 runtime
    enforcement).

    Args:
        obj:            Canonical object dict. Never mutated (INV-3).
        lane:           Registry lane key; pre-validated by enforce_civ.
        cycle_snapshot: Unused in this check. Present for uniform signature.

    Returns:
        (True, None)                         on PASS (no foreign keys present).
        (False, REJECT_LANE_FIELD_CONTAMINATION) if any foreign key is found.
    """
    obj_keys = frozenset(obj.keys())

    if lane == "CPS":
        forbidden = obj_keys & (NARRATIVE_SEMANTIC_FIELDS | MEDIA_SEMANTIC_FIELDS)
    elif lane in ("CME", "CSN"):
        forbidden = obj_keys & (PRESSURE_SEMANTIC_FIELDS | MEDIA_SEMANTIC_FIELDS)
    else:  # MediaContext
        forbidden = obj_keys & (PRESSURE_SEMANTIC_FIELDS | NARRATIVE_SEMANTIC_FIELDS)

    if forbidden:
        return (False, REJECT_LANE_FIELD_CONTAMINATION)

    return (True, None)


# ── Dispatch table (fixed order — INV-5) ─────────────────────────────────────
# Ordered tuples of (stage_id, reason_code, check_fn).
# Order is final and must not change without a CIV_VERSION bump.

_ORDERED_CHECKS: tuple = (
    (STAGE_1_SCHEMA_COMPLETENESS,  REJECT_SCHEMA_INCOMPLETE,        _check_schema_completeness),
    (STAGE_2_ENUM_COMPLIANCE,      REJECT_ENUM_INVALID,             _check_enum_compliance),
    (STAGE_3_IDENTITY_ABSTRACTION, REJECT_IDENTITY_CONTAMINATION,   _check_identity_abstraction),
    (STAGE_4_TIME_BINDING,         REJECT_TIME_SHAPE_INVALID,       _check_time_binding),
    (STAGE_5_ID_INTEGRITY,         REJECT_ID_HASH_MISMATCH,         _check_id_integrity),
    (STAGE_6_VERSION_SNAPSHOT,     REJECT_VERSION_MISMATCH,         _check_version_snapshot),
    (STAGE_7_LANE_CONTAMINATION,   REJECT_LANE_FIELD_CONTAMINATION, _check_lane_contamination),
)


# ── Public entry point ────────────────────────────────────────────────────────

def enforce_civ(
    obj: object,
    lane: str,
    cycle_snapshot: dict,
) -> tuple[bool, dict | None, dict]:
    """Apply CIV structural validation to a single canonical object.

    Runs 7 checks in fixed contract order. Returns on the first failure.
    Input is never mutated (INV-3). No state persisted (INV-1).

    Args:
        obj:            Canonical object dict as emitted by PSTA / META /
                        SANTA / MCMA. Never mutated.
        lane:           Registry lane key. Must be one of VALID_CIV_LANES:
                        "CPS", "CME", "CSN", "MediaContext".
        cycle_snapshot: Orchestrator cycle version snapshot dict.
                        Must contain: schemaVersion, enumVersion,
                        contractVersion.

    Returns:
        3-tuple (passed, rejection_or_None, verdict):

        On PASS (all 7 checks pass):
            (True, None, verdict_dict)

        On FAIL (first failing check):
            (False, rejection_dict, verdict_dict)
            rejection_dict: rejected=True, reasonCode, failureStage,
                            civVersion, lane, objectRef.
            verdict_dict:   civVersion, lane, verdict, reasonCode,
                            failureStage.

    INV-1: No state mutation.
    INV-3: obj is never mutated.
    INV-4: Lane-aware — check 4 skipped for non-TIME_BINDING_LANES.
    INV-5: Deterministic. Identical (obj, lane, cycle_snapshot) always
           produces identical output.
    """
    # ── Entry guards ──────────────────────────────────────────────────────────

    if not isinstance(obj, dict):
        safe_lane = lane if isinstance(lane, str) else "__unknown__"
        rejection = {
            "rejected":     True,
            "reasonCode":   REJECT_SCHEMA_INCOMPLETE,
            "failureStage": STAGE_1_SCHEMA_COMPLETENESS,
            "civVersion":   CIV_VERSION,
            "lane":         safe_lane,
            "objectRef":    None,
        }
        return (False, rejection, _make_verdict(
            safe_lane, VERDICT_FAIL, REJECT_SCHEMA_INCOMPLETE,
            STAGE_1_SCHEMA_COMPLETENESS
        ))

    if lane not in VALID_CIV_LANES:
        return _build_fail(obj, lane if isinstance(lane, str) else "__unknown__",
                           REJECT_SCHEMA_INCOMPLETE, STAGE_1_SCHEMA_COMPLETENESS)

    if not isinstance(cycle_snapshot, dict) or not all(
        k in cycle_snapshot for k in REQUIRED_CYCLE_SNAPSHOT_KEYS
    ):
        return _build_fail(obj, lane, REJECT_VERSION_MISMATCH,
                           STAGE_6_VERSION_SNAPSHOT)

    obj_snap: dict = obj   # INV-3: obj is not mutated; snapshot reference only

    # ── Ordered check dispatch (INV-5: fixed order) ───────────────────────────
    for stage, reason_code, check_fn in _ORDERED_CHECKS:

        # Check 4 (time binding) applies only to TIME_BINDING_LANES.
        if stage == STAGE_4_TIME_BINDING and lane not in TIME_BINDING_LANES:
            continue

        passed, _ = check_fn(obj_snap, lane, cycle_snapshot)
        if not passed:
            return _build_fail(obj_snap, lane, reason_code, stage)

    # ── PASS ──────────────────────────────────────────────────────────────────
    return (True, None, _make_verdict(lane, VERDICT_PASS, None, None))
