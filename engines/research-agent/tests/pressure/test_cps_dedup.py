"""
tests/pressure/test_cps_dedup.py

Unit tests for pressure.cps_dedup — Phase 8.3.

Coverage plan:
  - Return signature
  - NEW_CANONICAL: empty registry
  - NEW_CANONICAL: non-empty registry, ID absent
  - DUPLICATE: exact match in registry
  - DUPLICATE: matching object is a copy (INV-3 — mutation safety)
  - INV-1: fresh disk read on every call (via two sequential calls, different state)
  - INV-3: registry file never mutated by detector
  - INV-4: only CPS lane queried (other lanes ignored even if populated)
  - Pre-IO validation: empty string, wrong type, bad prefix, uppercase hex,
    correct prefix wrong length
  - RegistryReadError: missing file, missing CPS lane
  - Version constant reachable
"""

import json
import os
import pytest
from copy import deepcopy

from engines.research_agent.agents.pressure.cps_dedup import CPS_DEDUP_VERSION, detect_cps_duplicate
from engines.research_agent.agents.pressure.psta_schema import STATUS_DUPLICATE, STATUS_NEW_CANONICAL
from engines.research_engine.ledger.registry_reader import RegistryReadError


# ── Helpers ────────────────────────────────────────────────────────────────────

_VALID_ID_A = "CPS_" + "a" * 64
_VALID_ID_B = "CPS_" + "b" * 64
_VALID_ID_C = "CPS_" + "c" * 64

_CPS_OBJ_A = {
    "laneType":             "PRESSURE",
    "schemaVersion":        "CPS-1.0",
    "canonicalId":          _VALID_ID_A,
    "signalClass":          "structural_tension",
    "environment":          "organizational",
    "pressureSignalDomain": "authority_distribution",
    "pressureVector":       "competing_influences",
    "signalPolarity":       "negative",
    "observationSource":    "internal_audit",
    "castRequirement":      "executive_decision_required",
    "tier":                 2,
    "observation":          "Coach retains play-calling authority.",
    "sourceSeed":           "Competing Authority Over Play-Calling",
    "enumRegistryVersion":  "ENUM_v1.0",
    "fingerprintVersion":   "CPS_FINGERPRINT_V1",
    "contractVersion":      "PSTA_v4",
}

_REGISTRY_SCHEMA_VERSION = "CANONICAL_REGISTRY-1.0"

def _write_registry(path: str, cps_objects: list[dict]) -> None:
    """Write a minimal valid canonical_objects.json for test use."""
    data = {
        "schemaVersion":        _REGISTRY_SCHEMA_VERSION,
        "CPS":                  cps_objects,
        "CME":                  [],
        "CSN":                  [],
        "StructuralEnvironment": [],
        "MediaContext":         [],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


# ── Return signature ───────────────────────────────────────────────────────────

def test_returns_tuple(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    result = detect_cps_duplicate(_VALID_ID_A, reg)
    assert isinstance(result, tuple)


def test_returns_two_elements(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    assert len(detect_cps_duplicate(_VALID_ID_A, reg)) == 2


# ── NEW_CANONICAL: empty registry ─────────────────────────────────────────────

def test_new_canonical_empty_registry_status(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    status, obj = detect_cps_duplicate(_VALID_ID_A, reg)
    assert status == STATUS_NEW_CANONICAL


def test_new_canonical_empty_registry_object_is_none(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    _, obj = detect_cps_duplicate(_VALID_ID_A, reg)
    assert obj is None


# ── NEW_CANONICAL: non-empty registry, ID absent ──────────────────────────────

def test_new_canonical_id_absent_from_populated_registry(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    status, obj = detect_cps_duplicate(_VALID_ID_B, reg)
    assert status == STATUS_NEW_CANONICAL
    assert obj is None


# ── DUPLICATE: exact match ─────────────────────────────────────────────────────

def test_duplicate_status_when_id_present(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    status, _ = detect_cps_duplicate(_VALID_ID_A, reg)
    assert status == STATUS_DUPLICATE


def test_duplicate_returns_matching_object(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    _, obj = detect_cps_duplicate(_VALID_ID_A, reg)
    assert obj is not None
    assert obj["canonicalId"] == _VALID_ID_A


def test_duplicate_matching_object_equals_stored_object(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    _, obj = detect_cps_duplicate(_VALID_ID_A, reg)
    assert obj == _CPS_OBJ_A


def test_duplicate_among_multiple_objects(tmp_path):
    obj_b = {**_CPS_OBJ_A, "canonicalId": _VALID_ID_B}
    obj_c = {**_CPS_OBJ_A, "canonicalId": _VALID_ID_C}
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A), deepcopy(obj_b), deepcopy(obj_c)])
    status, obj = detect_cps_duplicate(_VALID_ID_B, reg)
    assert status == STATUS_DUPLICATE
    assert obj["canonicalId"] == _VALID_ID_B


# ── INV-3: returned object is a copy, not a reference ─────────────────────────

def test_duplicate_returned_object_is_copy(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    _, obj = detect_cps_duplicate(_VALID_ID_A, reg)
    # Mutating the returned dict must not affect a subsequent read
    obj["canonicalId"] = "CPS_" + "f" * 64
    _, obj2 = detect_cps_duplicate(_VALID_ID_A, reg)
    assert obj2["canonicalId"] == _VALID_ID_A


# ── INV-3: registry file not mutated by detector ──────────────────────────────

def test_registry_file_not_mutated_on_new_canonical(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    mtime_before = os.path.getmtime(reg)
    detect_cps_duplicate(_VALID_ID_A, reg)
    mtime_after = os.path.getmtime(reg)
    assert mtime_before == mtime_after


def test_registry_file_not_mutated_on_duplicate(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    mtime_before = os.path.getmtime(reg)
    detect_cps_duplicate(_VALID_ID_A, reg)
    mtime_after = os.path.getmtime(reg)
    assert mtime_before == mtime_after


# ── INV-1: fresh disk read reflects updated registry ──────────────────────────

def test_fresh_read_reflects_updated_registry(tmp_path):
    """Second call sees an object written after the first call."""
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    status_before, _ = detect_cps_duplicate(_VALID_ID_A, reg)
    assert status_before == STATUS_NEW_CANONICAL

    # Simulate registry commit between calls
    _write_registry(reg, [deepcopy(_CPS_OBJ_A)])
    status_after, _ = detect_cps_duplicate(_VALID_ID_A, reg)
    assert status_after == STATUS_DUPLICATE


# ── INV-4: only CPS lane queried ──────────────────────────────────────────────

def test_id_in_other_lane_not_detected_as_duplicate(tmp_path):
    """An ID present in CME lane must not be reported as CPS duplicate."""
    cme_obj = {**_CPS_OBJ_A, "laneType": "CME", "id": _VALID_ID_A}
    reg = str(tmp_path / "canonical_objects.json")
    data = {
        "schemaVersion":        _REGISTRY_SCHEMA_VERSION,
        "CPS":                  [],
        "CME":                  [cme_obj],
        "CSN":                  [],
        "StructuralEnvironment": [],
        "MediaContext":         [],
    }
    with open(reg, "w") as fh:
        json.dump(data, fh)
    status, obj = detect_cps_duplicate(_VALID_ID_A, reg)
    assert status == STATUS_NEW_CANONICAL
    assert obj is None


# ── Pre-IO validation: canonical_id ───────────────────────────────────────────

def test_empty_string_raises_value_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    with pytest.raises(ValueError):
        detect_cps_duplicate("", reg)


def test_wrong_type_raises_value_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    with pytest.raises(ValueError):
        detect_cps_duplicate(None, reg)   # type: ignore


def test_bad_prefix_raises_value_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    with pytest.raises(ValueError):
        detect_cps_duplicate("cps_" + "a" * 64, reg)   # lowercase prefix


def test_uppercase_hex_raises_value_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    with pytest.raises(ValueError):
        detect_cps_duplicate("CPS_" + "A" * 64, reg)


def test_correct_prefix_wrong_length_raises_value_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    _write_registry(reg, [])
    with pytest.raises(ValueError):
        detect_cps_duplicate("CPS_" + "a" * 63, reg)   # 63 instead of 64


def test_no_disk_read_when_validation_fails(tmp_path):
    """ValueError must be raised before any file is opened."""
    nonexistent = str(tmp_path / "does_not_exist.json")
    with pytest.raises(ValueError):
        detect_cps_duplicate("bad_id", nonexistent)   # fails pre-IO, not FileNotFoundError


# ── RegistryReadError: missing or invalid registry ────────────────────────────

def test_missing_registry_raises_registry_read_error(tmp_path):
    nonexistent = str(tmp_path / "canonical_objects.json")
    with pytest.raises(RegistryReadError):
        detect_cps_duplicate(_VALID_ID_A, nonexistent)


def test_invalid_json_raises_registry_read_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    with open(reg, "w") as fh:
        fh.write("not json {{{")
    with pytest.raises(RegistryReadError):
        detect_cps_duplicate(_VALID_ID_A, reg)


def test_wrong_schema_version_raises_registry_read_error(tmp_path):
    reg = str(tmp_path / "canonical_objects.json")
    data = {
        "schemaVersion": "WRONG-VERSION",
        "CPS": [], "CME": [], "CSN": [],
        "StructuralEnvironment": [], "MediaContext": [],
    }
    with open(reg, "w") as fh:
        json.dump(data, fh)
    with pytest.raises(RegistryReadError):
        detect_cps_duplicate(_VALID_ID_A, reg)


# ── Version constant ───────────────────────────────────────────────────────────

def test_cps_dedup_version_constant():
    assert CPS_DEDUP_VERSION == "CPS_DEDUP-1.0"
