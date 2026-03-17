"""
tests/pressure/test_cps_constructor.py

Unit tests for pressure.cps_constructor — Phase 8.4.

Coverage plan:
  - Return type and shape
  - All 16 required fields present, no extras
  - Field values correctly sourced from cps_fields and arguments
  - fingerprintVersion sourced from CPS_FINGERPRINT_V1 import (not literal)
  - contractVersion sourced from PSTA_CONTRACT_VERSION
  - laneType and schemaVersion are fixed constants
  - canonicalId in returned object equals canonical_id argument
  - Returned object passes validate_pressure_object
  - INV-3: cps_fields not mutated
  - INV-5: identical inputs → identical output
  - Pre-assembly validation: empty string, wrong type, bad prefix,
    uppercase hex, correct prefix wrong length
  - ValueError raised before assembly (missing cps_fields key not masked)
  - PressureSchemaValidationError raised for schema-invalid assembly
  - None tier: assembles and validates correctly
  - Version constant reachable
  - psta.py integration: enforce_psta still passes its existing tests
    (verified by importing and calling enforce_psta with a valid PLO)
"""

import pytest
from copy import deepcopy

from engines.research_agent.agents.pressure.cps_constructor import CPS_CONSTRUCTOR_VERSION, build_cps_object
from engines.research_agent.agents.pressure.cps_fingerprint import CPS_FINGERPRINT_V1
from engines.research_agent.agents.pressure.psta_schema import PSTA_CONTRACT_VERSION, PSTA_CPS_SCHEMA_VERSION, PSTA_LANE_TYPE
from engines.research_agent.schemas.pressure.validator import PressureSchemaValidationError, validate_pressure_object


# ── Fixtures ───────────────────────────────────────────────────────────────────

_VALID_ID = "CPS_" + "a" * 64
_ENUM_VERSION = "ENUM_v1.0"

_VALID_FIELDS = {
    "signalClass":          "structural_tension",
    "environment":          "organizational",
    "pressureSignalDomain": "authority_distribution",
    "pressureVector":       "competing_influences",
    "signalPolarity":       "negative",
    "observationSource":    "internal_audit",
    "castRequirement":      "executive_decision_required",
    "tier":                 2,
    "observation":          "Coach retains play-calling authority despite board scrutiny.",
    "sourceSeed":           "Competing Authority Over Play-Calling",
}

_REQUIRED_KEYS = {
    "laneType", "schemaVersion", "signalClass", "environment",
    "pressureSignalDomain", "pressureVector", "signalPolarity",
    "observationSource", "castRequirement", "tier", "observation",
    "sourceSeed", "canonicalId", "enumRegistryVersion",
    "fingerprintVersion", "contractVersion",
}


# ── Return type ────────────────────────────────────────────────────────────────

def test_returns_dict():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert isinstance(result, dict)


# ── Field completeness and exclusivity ────────────────────────────────────────

def test_all_required_fields_present():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert set(result.keys()) == _REQUIRED_KEYS


def test_no_extra_fields():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert not (set(result.keys()) - _REQUIRED_KEYS)


# ── Field sourcing ─────────────────────────────────────────────────────────────

def test_canonical_id_field_equals_argument():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["canonicalId"] == _VALID_ID


def test_enum_registry_version_field_equals_argument():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, "ENUM_v2.0")
    assert result["enumRegistryVersion"] == "ENUM_v2.0"


def test_signal_class_sourced_from_cps_fields():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["signalClass"] == _VALID_FIELDS["signalClass"]


def test_tier_sourced_from_cps_fields():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["tier"] == _VALID_FIELDS["tier"]


def test_observation_sourced_from_cps_fields():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["observation"] == _VALID_FIELDS["observation"]


def test_source_seed_sourced_from_cps_fields():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["sourceSeed"] == _VALID_FIELDS["sourceSeed"]


# ── Fixed constants ────────────────────────────────────────────────────────────

def test_lane_type_is_pressure():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["laneType"] == PSTA_LANE_TYPE


def test_schema_version_is_cps_1_0():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["schemaVersion"] == PSTA_CPS_SCHEMA_VERSION


def test_fingerprint_version_equals_imported_constant():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["fingerprintVersion"] == CPS_FINGERPRINT_V1


def test_contract_version_equals_imported_constant():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    assert result["contractVersion"] == PSTA_CONTRACT_VERSION


# ── Schema validation ──────────────────────────────────────────────────────────

def test_returned_object_passes_schema_validation():
    result = build_cps_object(_VALID_FIELDS, _VALID_ID, _ENUM_VERSION)
    validate_pressure_object(result)


# ── Null tier ──────────────────────────────────────────────────────────────────

def test_null_tier_assembles_to_none():
    fields = {**_VALID_FIELDS, "tier": None}
    result = build_cps_object(fields, _VALID_ID, _ENUM_VERSION)
    assert result["tier"] is None


def test_null_tier_passes_schema_validation():
    fields = {**_VALID_FIELDS, "tier": None}
    result = build_cps_object(fields, _VALID_ID, _ENUM_VERSION)
    validate_pressure_object(result)


# ── INV-3: cps_fields not mutated ─────────────────────────────────────────────

def test_cps_fields_not_mutated():
    fields = deepcopy(_VALID_FIELDS)
    original = deepcopy(fields)
    build_cps_object(fields, _VALID_ID, _ENUM_VERSION)
    assert fields == original


# ── INV-5: determinism ────────────────────────────────────────────────────────

def test_identical_inputs_produce_identical_output():
    result_a = build_cps_object(deepcopy(_VALID_FIELDS), _VALID_ID, _ENUM_VERSION)
    result_b = build_cps_object(deepcopy(_VALID_FIELDS), _VALID_ID, _ENUM_VERSION)
    assert result_a == result_b


def test_different_canonical_ids_produce_different_objects():
    id_a = "CPS_" + "a" * 64
    id_b = "CPS_" + "b" * 64
    result_a = build_cps_object(_VALID_FIELDS, id_a, _ENUM_VERSION)
    result_b = build_cps_object(_VALID_FIELDS, id_b, _ENUM_VERSION)
    assert result_a != result_b


# ── Pre-assembly validation: canonical_id ─────────────────────────────────────

def test_empty_canonical_id_raises_value_error():
    with pytest.raises(ValueError):
        build_cps_object(_VALID_FIELDS, "", _ENUM_VERSION)


def test_none_canonical_id_raises_value_error():
    with pytest.raises(ValueError):
        build_cps_object(_VALID_FIELDS, None, _ENUM_VERSION)


def test_lowercase_prefix_raises_value_error():
    with pytest.raises(ValueError):
        build_cps_object(_VALID_FIELDS, "cps_" + "a" * 64, _ENUM_VERSION)


def test_uppercase_hex_raises_value_error():
    with pytest.raises(ValueError):
        build_cps_object(_VALID_FIELDS, "CPS_" + "A" * 64, _ENUM_VERSION)


def test_correct_prefix_wrong_length_raises_value_error():
    with pytest.raises(ValueError):
        build_cps_object(_VALID_FIELDS, "CPS_" + "a" * 63, _ENUM_VERSION)


def test_value_error_raised_before_assembly_for_bad_id():
    """ValueError from bad ID must fire even if cps_fields is incomplete."""
    with pytest.raises(ValueError):
        build_cps_object({}, "bad_id", _ENUM_VERSION)


# ── Missing cps_fields key propagates as KeyError ─────────────────────────────

def test_missing_cps_field_raises_key_error():
    fields = {k: v for k, v in _VALID_FIELDS.items() if k != "signalClass"}
    with pytest.raises(KeyError):
        build_cps_object(fields, _VALID_ID, _ENUM_VERSION)


# ── Schema validation failure raises PressureSchemaValidationError ────────────

def test_invalid_tier_type_raises_schema_error():
    """tier must be integer or null; string raises PressureSchemaValidationError."""
    fields = {**_VALID_FIELDS, "tier": "two"}
    with pytest.raises(PressureSchemaValidationError):
        build_cps_object(fields, _VALID_ID, _ENUM_VERSION)


# ── psta.py integration: enforce_psta still works after refactor ──────────────

def test_enforce_psta_returns_valid_cps_objects_after_refactor():
    """
    Smoke test: enforce_psta (which now calls build_cps_object) still
    produces valid CPS objects. Regression guard for the psta.py patch.
    """
    from engines.research_agent.agents.pressure.psta import enforce_psta

    plo = {
        "sourceSeedText": "Competing Authority Over Play-Calling",
        "observations": [{
            "signalClass":          "structural_tension",
            "environment":          "organizational",
            "pressureSignalDomain": "authority_distribution",
            "pressureVector":       "competing_influences",
            "signalPolarity":       "negative",
            "observationSource":    "internal_audit",
            "castRequirement":      "executive_decision_required",
            "tier":                 2,
            "observation":          "Coach retains play-calling authority despite board scrutiny.",
        }],
    }
    canonical, rejections, audit = enforce_psta(plo)
    assert len(canonical) == 1
    assert len(rejections) == 0
    validate_pressure_object(canonical[0])


# ── Version constant ───────────────────────────────────────────────────────────

def test_cps_constructor_version_constant():
    assert CPS_CONSTRUCTOR_VERSION == "CPS_CONSTRUCTOR-1.0"
