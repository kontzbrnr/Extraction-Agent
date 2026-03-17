"""
tests/pressure/test_psta.py

Unit tests for pressure.psta — Phase 8.2.

Coverage plan:
  - Return signature
  - INV-1: no mutable module-level state (import-safe)
  - INV-2: sole mint authority — canonicalId format and determinism
  - INV-3: plo_record never mutated
  - INV-5: identical input → identical output; no timestamp in audit
  - Field sourcing: PLO-1.0 "domain" → pressureSignalDomain
  - Field sourcing: "pressureSignalDomain" key preferred over "domain"
  - Field sourcing: sourceSeedText → sourceSeed
  - Fallback tokens: missing/null fields
  - Null tier: None preserved in CPS object; "" used for fingerprint
  - Fingerprint determinism: same fields → same canonicalId
  - Full CPS object shape: required fields, no extras
  - Schema validation: each CPS object passes validate_pressure_object
  - Within-call dedup: duplicate observation → STATUS_DUPLICATE rejection
  - Multi-observation PLO: one CPS object per distinct observation
  - Empty observations list: empty canonical list
  - Audit fields: counts consistent with output lists; no timestamp
  - Version constants reachable
"""

import pytest
from copy import deepcopy

from engines.research_agent.agents.pressure.psta import enforce_psta
from engines.research_agent.agents.pressure.psta_schema import (
    PSTA_AUDIT_SCHEMA_VERSION,
    PSTA_CONTRACT_VERSION,
    PSTA_CPS_SCHEMA_VERSION,
    PSTA_DEFAULT_ENUM_REGISTRY_VERSION,
    PSTA_LANE_TYPE,
    PSTA_VERSION,
    REJECT_PSTA_SCHEMA_INVALID,
    STATUS_DUPLICATE,
    STATUS_NEW_CANONICAL,
)
from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_V1, derive_cps_fingerprint
from engines.research_agent.schemas.pressure.validator import validate_pressure_object


# ── Fixtures ───────────────────────────────────────────────────────────────────

_SOURCE_SEED_TEXT = "Competing Authority Over Play-Calling"

_OBS_FULL = {
    "signalClass":          "structural_tension",
    "environment":          "organizational",
    "pressureSignalDomain": "authority_distribution",
    "pressureVector":       "competing_influences",
    "signalPolarity":       "negative",
    "observationSource":    "internal_audit",
    "castRequirement":      "executive_decision_required",
    "tier":                 2,
    "observation":          "Coach retains play-calling authority despite board scrutiny.",
}

_OBS_PLO1_FORMAT = {
    # PLO-1.0 style: uses "domain" key instead of "pressureSignalDomain"
    "domain":      "Authority Distribution",
    "observation": "Coach retains play-calling authority despite board scrutiny.",
    # other 7 fields absent → will use fallback tokens
}

_PLO_FULL = {
    "sourceSeedText": _SOURCE_SEED_TEXT,
    "schemaVersion":  "PLO-1.0",
    "observations":   [deepcopy(_OBS_FULL)],
}

_PLO_PLO1 = {
    "sourceSeedText": _SOURCE_SEED_TEXT,
    "schemaVersion":  "PLO-1.0",
    "observations":   [deepcopy(_OBS_PLO1_FORMAT)],
}


# ── Return signature ───────────────────────────────────────────────────────────

def test_returns_tuple():
    result = enforce_psta(_PLO_FULL)
    assert isinstance(result, tuple)


def test_returns_three_elements():
    assert len(enforce_psta(_PLO_FULL)) == 3


def test_first_element_is_list():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert isinstance(canonical, list)


def test_second_element_is_list():
    _, rejections, _ = enforce_psta(_PLO_FULL)
    assert isinstance(rejections, list)


def test_third_element_is_dict():
    _, _, audit = enforce_psta(_PLO_FULL)
    assert isinstance(audit, dict)


# ── INV-3: plo_record not mutated ─────────────────────────────────────────────

def test_plo_record_not_mutated():
    plo = deepcopy(_PLO_FULL)
    original = deepcopy(plo)
    enforce_psta(plo)
    assert plo == original


def test_observation_dict_not_mutated():
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    original_obs = deepcopy(obs)
    enforce_psta(plo)
    assert obs == original_obs


# ── INV-5: determinism — identical input → identical output ───────────────────

def test_identical_input_identical_canonical_id():
    canonical_a, _, _ = enforce_psta(deepcopy(_PLO_FULL))
    canonical_b, _, _ = enforce_psta(deepcopy(_PLO_FULL))
    assert canonical_a[0]["canonicalId"] == canonical_b[0]["canonicalId"]


def test_identical_input_identical_cps_object():
    canonical_a, _, _ = enforce_psta(deepcopy(_PLO_FULL))
    canonical_b, _, _ = enforce_psta(deepcopy(_PLO_FULL))
    assert canonical_a[0] == canonical_b[0]


# ── INV-5: no timestamp in audit ──────────────────────────────────────────────

def test_no_timestamp_in_audit():
    _, _, audit = enforce_psta(_PLO_FULL)
    assert "timestamp" not in audit


def test_no_execution_timestamp_in_audit():
    _, _, audit = enforce_psta(_PLO_FULL)
    assert "executionTimestamp" not in audit


# ── INV-2: canonical ID format and mint authority ─────────────────────────────

def test_canonical_id_has_cps_prefix():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["canonicalId"].startswith("CPS_")


def test_canonical_id_is_64_hex_chars():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    hex_part = canonical[0]["canonicalId"][4:]
    assert len(hex_part) == 64
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_canonical_id_matches_derive_cps_fingerprint():
    """canonicalId must equal derive_cps_fingerprint applied to the CPS fields."""
    canonical, _, _ = enforce_psta(_PLO_FULL)
    cps = canonical[0]
    expected_fields = {
        "signalClass":          cps["signalClass"],
        "environment":          cps["environment"],
        "pressureSignalDomain": cps["pressureSignalDomain"],
        "pressureVector":       cps["pressureVector"],
        "signalPolarity":       cps["signalPolarity"],
        "observationSource":    cps["observationSource"],
        "castRequirement":      cps["castRequirement"],
        "tier":                 "" if cps["tier"] is None else cps["tier"],
        "observation":          cps["observation"],
        "sourceSeed":           cps["sourceSeed"],
    }
    assert cps["canonicalId"] == derive_cps_fingerprint(expected_fields)


# ── CPS object shape ───────────────────────────────────────────────────────────

_REQUIRED_CPS_KEYS = {
    "laneType", "schemaVersion", "signalClass", "environment",
    "pressureSignalDomain", "pressureVector", "signalPolarity",
    "observationSource", "castRequirement", "tier", "observation",
    "sourceSeed", "canonicalId", "enumRegistryVersion",
    "fingerprintVersion", "contractVersion",
}

def test_cps_object_has_all_required_keys():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert set(canonical[0].keys()) == _REQUIRED_CPS_KEYS


def test_cps_object_has_no_extra_keys():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert not (set(canonical[0].keys()) - _REQUIRED_CPS_KEYS)


def test_cps_lane_type():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["laneType"] == PSTA_LANE_TYPE


def test_cps_schema_version():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["schemaVersion"] == PSTA_CPS_SCHEMA_VERSION


def test_cps_fingerprint_version():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["fingerprintVersion"] == CPS_FINGERPRINT_V1


def test_cps_contract_version():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["contractVersion"] == PSTA_CONTRACT_VERSION


def test_cps_enum_registry_version_default():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["enumRegistryVersion"] == PSTA_DEFAULT_ENUM_REGISTRY_VERSION


def test_cps_enum_registry_version_custom():
    canonical, _, _ = enforce_psta(_PLO_FULL, enum_registry_version="ENUM_v2.0")
    assert canonical[0]["enumRegistryVersion"] == "ENUM_v2.0"


# ── Schema validation ──────────────────────────────────────────────────────────

def test_cps_object_passes_schema_validation():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    # raises PressureSchemaValidationError on failure; no assertion needed
    validate_pressure_object(canonical[0])


# ── Field sourcing: PLO-1.0 "domain" → pressureSignalDomain ──────────────────

def test_plo1_domain_maps_to_pressure_signal_domain():
    canonical, _, _ = enforce_psta(_PLO_PLO1)
    # "Authority Distribution" from PLO-1.0 observation "domain" key
    assert canonical[0]["pressureSignalDomain"] == "Authority Distribution"


def test_plo1_observation_maps_correctly():
    canonical, _, _ = enforce_psta(_PLO_PLO1)
    assert canonical[0]["observation"] == _OBS_PLO1_FORMAT["observation"]


# ── Field sourcing: "pressureSignalDomain" preferred over "domain" ─────────────

def test_pressure_signal_domain_key_preferred_over_domain():
    obs = {
        "pressureSignalDomain": "timing_horizon",
        "domain":               "Authority Distribution",   # should be ignored
        "observation":          "Some observation.",
    }
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    canonical, _, _ = enforce_psta(plo)
    assert canonical[0]["pressureSignalDomain"] == "timing_horizon"


# ── Field sourcing: sourceSeedText → sourceSeed ────────────────────────────────

def test_source_seed_text_maps_to_source_seed():
    canonical, _, _ = enforce_psta(_PLO_FULL)
    assert canonical[0]["sourceSeed"] == _SOURCE_SEED_TEXT


def test_missing_source_seed_text_uses_fallback():
    plo = {"observations": [deepcopy(_OBS_FULL)]}   # no sourceSeedText key
    canonical, _, _ = enforce_psta(plo)
    assert canonical[0]["sourceSeed"] == ""


def test_empty_source_seed_text_uses_fallback():
    plo = {"sourceSeedText": "", "observations": [deepcopy(_OBS_FULL)]}
    canonical, _, _ = enforce_psta(plo)
    assert canonical[0]["sourceSeed"] == ""


# ── Fallback tokens: missing / null string fields ─────────────────────────────

def test_missing_signal_class_falls_back_to_empty_string():
    obs = {k: v for k, v in _OBS_FULL.items() if k != "signalClass"}
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    canonical, _, _ = enforce_psta(plo)
    assert canonical[0]["signalClass"] == ""


def test_null_signal_class_falls_back_to_empty_string():
    obs = {**_OBS_FULL, "signalClass": None}
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    canonical, _, _ = enforce_psta(plo)
    assert canonical[0]["signalClass"] == ""


# ── Null tier: None preserved in CPS object ───────────────────────────────────

def test_null_tier_preserved_as_none_in_cps():
    obs = {**_OBS_FULL, "tier": None}
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    canonical, _, _ = enforce_psta(plo)
    assert canonical[0]["tier"] is None


def test_null_tier_cps_passes_schema_validation():
    obs = {**_OBS_FULL, "tier": None}
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    canonical, _, _ = enforce_psta(plo)
    validate_pressure_object(canonical[0])   # must not raise


def test_null_tier_produces_deterministic_canonical_id():
    obs = {**_OBS_FULL, "tier": None}
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs]}
    canonical_a, _, _ = enforce_psta(deepcopy(plo))
    canonical_b, _, _ = enforce_psta(deepcopy(plo))
    assert canonical_a[0]["canonicalId"] == canonical_b[0]["canonicalId"]


def test_null_tier_and_int_tier_produce_different_canonical_ids():
    obs_null = {**_OBS_FULL, "tier": None}
    obs_int  = {**_OBS_FULL, "tier": 2}
    plo_null = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs_null]}
    plo_int  = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs_int]}
    canonical_null, _, _ = enforce_psta(plo_null)
    canonical_int,  _, _ = enforce_psta(plo_int)
    assert canonical_null[0]["canonicalId"] != canonical_int[0]["canonicalId"]


# ── Within-call dedup ─────────────────────────────────────────────────────────

def test_duplicate_observation_produces_one_canonical_object():
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs, deepcopy(obs)]}
    canonical, _, _ = enforce_psta(plo)
    assert len(canonical) == 1


def test_duplicate_observation_produces_one_rejection():
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs, deepcopy(obs)]}
    _, rejections, _ = enforce_psta(plo)
    assert len(rejections) == 1


def test_duplicate_rejection_has_status_duplicate():
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs, deepcopy(obs)]}
    _, rejections, _ = enforce_psta(plo)
    assert rejections[0]["status"] == STATUS_DUPLICATE


def test_duplicate_rejection_has_matching_canonical_id():
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs, deepcopy(obs)]}
    canonical, rejections, _ = enforce_psta(plo)
    assert rejections[0]["canonicalId"] == canonical[0]["canonicalId"]


# ── Multi-observation PLO ─────────────────────────────────────────────────────

def test_four_distinct_observations_produce_four_cps_objects():
    observations = [
        {**_OBS_FULL, "pressureSignalDomain": "authority_distribution", "observation": "obs 1"},
        {**_OBS_FULL, "pressureSignalDomain": "timing_horizon",          "observation": "obs 2"},
        {**_OBS_FULL, "pressureSignalDomain": "structural_configuration","observation": "obs 3"},
        {**_OBS_FULL, "pressureSignalDomain": "access_information",      "observation": "obs 4"},
    ]
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": observations}
    canonical, rejections, _ = enforce_psta(plo)
    assert len(canonical) == 4
    assert len(rejections) == 0


def test_four_observations_all_have_unique_canonical_ids():
    observations = [
        {**_OBS_FULL, "pressureSignalDomain": "authority_distribution", "observation": "obs 1"},
        {**_OBS_FULL, "pressureSignalDomain": "timing_horizon",          "observation": "obs 2"},
        {**_OBS_FULL, "pressureSignalDomain": "structural_configuration","observation": "obs 3"},
        {**_OBS_FULL, "pressureSignalDomain": "access_information",      "observation": "obs 4"},
    ]
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": observations}
    canonical, _, _ = enforce_psta(plo)
    ids = [c["canonicalId"] for c in canonical]
    assert len(set(ids)) == 4


# ── Empty observations list ───────────────────────────────────────────────────

def test_empty_observations_returns_empty_canonical():
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": []}
    canonical, _, _ = enforce_psta(plo)
    assert canonical == []


def test_empty_observations_returns_empty_rejections():
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": []}
    _, rejections, _ = enforce_psta(plo)
    assert rejections == []


def test_empty_observations_audit_has_zero_counts():
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": []}
    _, _, audit = enforce_psta(plo)
    assert audit["inputObservationCount"] == 0
    assert audit["newCanonicalCount"] == 0
    assert audit["duplicateCount"] == 0
    assert audit["rejectionCount"] == 0


def test_missing_observations_key_returns_empty_canonical():
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT}
    canonical, _, _ = enforce_psta(plo)
    assert canonical == []


# ── Audit fields ──────────────────────────────────────────────────────────────

def test_audit_schema_version():
    _, _, audit = enforce_psta(_PLO_FULL)
    assert audit["schemaVersion"] == PSTA_AUDIT_SCHEMA_VERSION


def test_audit_psta_version():
    _, _, audit = enforce_psta(_PLO_FULL)
    assert audit["pstaVersion"] == PSTA_VERSION


def test_audit_fingerprint_version():
    _, _, audit = enforce_psta(_PLO_FULL)
    assert audit["fingerprintVersion"] == CPS_FINGERPRINT_V1


def test_audit_input_observation_count():
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [deepcopy(_OBS_FULL)] * 3}
    _, _, audit = enforce_psta(plo)
    assert audit["inputObservationCount"] == 3


def test_audit_new_canonical_count_matches_list():
    canonical, _, audit = enforce_psta(_PLO_FULL)
    assert audit["newCanonicalCount"] == len(canonical)


def test_audit_duplicate_count_matches_rejections():
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs, deepcopy(obs)]}
    canonical, rejections, audit = enforce_psta(plo)
    assert audit["duplicateCount"] == 1
    assert audit["newCanonicalCount"] == 1


def test_audit_counts_sum_to_input_count():
    """newCanonicalCount + duplicateCount + rejectionCount == inputObservationCount."""
    obs = deepcopy(_OBS_FULL)
    plo = {"sourceSeedText": _SOURCE_SEED_TEXT, "observations": [obs, deepcopy(obs)]}
    _, _, audit = enforce_psta(plo)
    total = audit["newCanonicalCount"] + audit["duplicateCount"] + audit["rejectionCount"]
    assert total == audit["inputObservationCount"]


# ── Version constants reachable ───────────────────────────────────────────────

def test_psta_version_constant():
    assert PSTA_VERSION == "PSTA-1.0"


def test_psta_audit_schema_version_constant():
    assert PSTA_AUDIT_SCHEMA_VERSION == "PSTA_AUDIT-1.0"


def test_status_new_canonical_constant():
    assert STATUS_NEW_CANONICAL == "NEW_CANONICAL"


def test_status_duplicate_constant():
    assert STATUS_DUPLICATE == "DUPLICATE"
