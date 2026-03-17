"""
Tests for ledger/registry_writer.py

Validates all Phase 1.2 acceptance criteria:
  - Registry initialization when file absent
  - Successful append to each valid lane
  - In-place edit prohibition (duplicate ID raises RegistryAppendError)
  - Invalid lane raises RegistryAppendError
  - Object written exactly as received (zero mutation)
  - Lane sorted by canonical ID ascending after append
  - Cross-lane isolation (append to CPS does not touch CSN)
  - Cardinality derived from contents
  - Multiple sequential appends produce correct sort order
"""

import json

import pytest

from engines.research_engine.ledger.registry_writer import (
    LaneMismatchError,
    RegistryAppendError,
    SCHEMA_VERSION,
    append_canonical_object,
    registry_cardinality,
)


@pytest.fixture
def registry_path(tmp_path):
    return tmp_path / "canonical_objects.json"


def make_cps(canonical_id: str) -> dict:
    return {"canonicalId": canonical_id, "laneType": "CPS", "schemaVersion": "CPS-1.0"}


def make_csn(id_: str) -> dict:
    return {"id": id_, "laneType": "CSN", "eventType": "CSN"}


def make_cme(id_: str) -> dict:
    return {"id": id_, "laneType": "CME", "eventType": "CME", "permanence": "permanent"}


def test_initializes_registry_when_absent(registry_path):
    append_canonical_object(registry_path, "CPS", make_cps("CPS_" + "a" * 64))
    registry = json.loads(registry_path.read_text())
    assert registry["schemaVersion"] == SCHEMA_VERSION
    assert set(registry.keys()) == {
        "schemaVersion",
        "CPS",
        "CME",
        "CSN",
        "StructuralEnvironment",
        "MediaContext",
    }


def test_initialized_registry_has_all_lanes_empty_except_written(registry_path):
    append_canonical_object(registry_path, "CPS", make_cps("CPS_" + "a" * 64))
    registry = json.loads(registry_path.read_text())
    assert len(registry["CME"]) == 0
    assert len(registry["CSN"]) == 0
    assert len(registry["StructuralEnvironment"]) == 0
    assert len(registry["MediaContext"]) == 0
    assert len(registry["CPS"]) == 1


def test_append_cps_object(registry_path):
    obj = make_cps("CPS_" + "b" * 64)
    append_canonical_object(registry_path, "CPS", obj)
    registry = json.loads(registry_path.read_text())
    assert len(registry["CPS"]) == 1
    assert registry["CPS"][0] == obj


def test_append_csn_object(registry_path):
    obj = make_csn("CSN_" + "c" * 64)
    append_canonical_object(registry_path, "CSN", obj)
    registry = json.loads(registry_path.read_text())
    assert registry["CSN"][0] == obj


def test_append_cme_object(registry_path):
    obj = make_cme("CME_" + "d" * 64)
    append_canonical_object(registry_path, "CME", obj)
    registry = json.loads(registry_path.read_text())
    assert registry["CME"][0] == obj


def test_append_structural_environment_object(registry_path):
    obj = {"id": "CSE_" + "e" * 64, "eventType": "CSE"}
    append_canonical_object(registry_path, "StructuralEnvironment", obj)
    registry = json.loads(registry_path.read_text())
    assert registry["StructuralEnvironment"][0] == obj


def test_append_media_context_stub(registry_path):
    obj = {"id": "MFU_" + "f" * 64}
    append_canonical_object(registry_path, "MediaContext", obj)
    registry = json.loads(registry_path.read_text())
    assert len(registry["MediaContext"]) == 1


def test_duplicate_id_raises_registry_append_error(registry_path):
    obj = make_cps("CPS_" + "a" * 64)
    append_canonical_object(registry_path, "CPS", obj)
    with pytest.raises(RegistryAppendError) as exc_info:
        append_canonical_object(registry_path, "CPS", obj)
    assert "CPS_" + "a" * 64 in str(exc_info.value)
    assert exc_info.value.lane == "CPS"
    assert exc_info.value.canonical_id == "CPS_" + "a" * 64


def test_duplicate_id_does_not_mutate_registry(registry_path):
    obj = make_cps("CPS_" + "a" * 64)
    append_canonical_object(registry_path, "CPS", obj)
    original_content = registry_path.read_bytes()
    with pytest.raises(RegistryAppendError):
        append_canonical_object(registry_path, "CPS", obj)
    assert registry_path.read_bytes() == original_content


def test_invalid_lane_raises(registry_path):
    with pytest.raises(RegistryAppendError) as exc_info:
        append_canonical_object(registry_path, "INVALID_LANE", {"id": "x"})
    assert "INVALID_LANE" in str(exc_info.value)


def test_lowercase_lane_raises(registry_path):
    with pytest.raises(RegistryAppendError):
        append_canonical_object(registry_path, "cps", make_cps("CPS_" + "a" * 64))


def test_object_written_without_mutation(registry_path):
    obj = make_cps("CPS_" + "a" * 64)
    obj_copy = dict(obj)
    append_canonical_object(registry_path, "CPS", obj)
    registry = json.loads(registry_path.read_text())
    assert registry["CPS"][0] == obj_copy


def test_lane_sorted_ascending_after_appends(registry_path):
    ids = ["CPS_" + char * 64 for char in ["z", "a", "m"]]
    for canonical_id in ids:
        append_canonical_object(registry_path, "CPS", make_cps(canonical_id))
    registry = json.loads(registry_path.read_text())
    stored_ids = [obj["canonicalId"] for obj in registry["CPS"]]
    assert stored_ids == sorted(stored_ids)


def test_csn_sorted_by_id_field(registry_path):
    ids = ["CSN_" + char * 64 for char in ["z", "a", "m"]]
    for canonical_id in ids:
        append_canonical_object(registry_path, "CSN", make_csn(canonical_id))
    registry = json.loads(registry_path.read_text())
    stored_ids = [obj["id"] for obj in registry["CSN"]]
    assert stored_ids == sorted(stored_ids)


def test_append_to_cps_does_not_touch_csn(registry_path):
    append_canonical_object(registry_path, "CSN", make_csn("CSN_" + "x" * 64))
    append_canonical_object(registry_path, "CPS", make_cps("CPS_" + "y" * 64))
    registry = json.loads(registry_path.read_text())
    assert len(registry["CSN"]) == 1
    assert registry["CSN"][0]["id"] == "CSN_" + "x" * 64


def test_cardinality_reflects_content_count(registry_path):
    assert registry_cardinality(registry_path, "CPS") == 0
    append_canonical_object(registry_path, "CPS", make_cps("CPS_" + "a" * 64))
    assert registry_cardinality(registry_path, "CPS") == 1
    append_canonical_object(registry_path, "CPS", make_cps("CPS_" + "b" * 64))
    assert registry_cardinality(registry_path, "CPS") == 2


def test_cardinality_invalid_lane_raises(registry_path):
    with pytest.raises(RegistryAppendError):
        registry_cardinality(registry_path, "BOGUS")


def test_ten_sequential_appends_all_persisted(registry_path):
    for index in range(10):
        canonical_id = f"CPS_{index:064d}"
        append_canonical_object(registry_path, "CPS", make_cps(canonical_id))
    assert registry_cardinality(registry_path, "CPS") == 10


# --- INV-4: Lane mismatch validation ---


def test_lane_mismatch_raises_when_laneType_conflicts(registry_path):
    """LaneMismatchError raised when lane parameter != object laneType."""
    obj = {"canonicalId": "CPS_x", "laneType": "CSN"}
    with pytest.raises(LaneMismatchError):
        append_canonical_object(registry_path, "CPS", obj)


def test_lane_mismatch_error_fields(registry_path):
    """LaneMismatchError carries expected and found lane values."""
    obj = {"canonicalId": "CPS_x", "laneType": "CSN"}
    try:
        append_canonical_object(registry_path, "CPS", obj)
    except LaneMismatchError as e:
        assert e.expected == "CPS"
        assert e.found == "CSN"


def test_no_lane_mismatch_when_laneType_absent(registry_path):
    """Objects without laneType field pass without lane validation."""
    obj = {
        "canonicalId": "CPS_" + "a" * 64,
        "text": "t",
        "isComposite": False,
        "schemaVersion": "REC-1.0",
    }
    # No laneType field — must not raise
    append_canonical_object(registry_path, "CPS", obj)


def test_no_lane_mismatch_when_laneType_matches(registry_path):
    """Objects with matching laneType and lane parameter pass."""
    obj = {"canonicalId": "CPS_x", "laneType": "CPS"}
    # Matching lane — must not raise
    append_canonical_object(registry_path, "CPS", obj)
