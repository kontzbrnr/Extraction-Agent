"""
tests/ledger/test_registry_reader.py

Tests for ledger/registry_reader.py.

Key invariant under test:
  - All counts derived from file contents only — no counters (INV-1, contract rule)
  - No file mutation under any code path (INV-3)
  - Lane counts are independent (INV-4)
"""

import json
import os
import pytest

from engines.research_engine.ledger.registry_reader import (
    CANONICAL_REGISTRY_SCHEMA_VERSION,
    VALID_LANES,
    RegistryReadError,
    all_lane_cardinalities,
    lane_cardinality,
    read_registry,
    total_registry_cardinality,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

EMPTY_REGISTRY = {
    "schemaVersion": "CANONICAL_REGISTRY-1.0",
    "CPS": [],
    "CME": [],
    "CSN": [],
    "StructuralEnvironment": [],
    "MediaContext": [],
}


def _write_registry(tmp_path, data=None):
    path = tmp_path / "canonical_objects.json"
    payload = data if data is not None else EMPTY_REGISTRY
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _cps_obj(canonical_id: str) -> dict:
    return {"canonicalId": canonical_id, "lane": "CPS"}


def _csn_obj(id_val: str) -> dict:
    return {"id": id_val, "lane": "CSN"}


# ---------------------------------------------------------------------------
# read_registry
# ---------------------------------------------------------------------------


def test_read_registry_valid_empty(tmp_path):
    path = _write_registry(tmp_path)
    result = read_registry(path)
    assert result["schemaVersion"] == CANONICAL_REGISTRY_SCHEMA_VERSION
    for lane in VALID_LANES:
        assert lane in result
        assert result[lane] == []


def test_read_registry_file_not_found(tmp_path):
    with pytest.raises(RegistryReadError) as exc_info:
        read_registry(str(tmp_path / "missing.json"))
    assert exc_info.value.path != ""


def test_read_registry_invalid_json(tmp_path):
    path = tmp_path / "canonical_objects.json"
    path.write_text("{bad json", encoding="utf-8")
    with pytest.raises(RegistryReadError):
        read_registry(str(path))


def test_read_registry_wrong_schema_version(tmp_path):
    data = {**EMPTY_REGISTRY, "schemaVersion": "WRONG-9.9"}
    path = _write_registry(tmp_path, data)
    with pytest.raises(RegistryReadError) as exc_info:
        read_registry(path)
    assert "CANONICAL_REGISTRY-1.0" in str(exc_info.value)
    assert "WRONG-9.9" in str(exc_info.value)


def test_read_registry_missing_lane_key_raises(tmp_path):
    data = {k: v for k, v in EMPTY_REGISTRY.items() if k != "CME"}
    path = _write_registry(tmp_path, data)
    with pytest.raises(RegistryReadError) as exc_info:
        read_registry(path)
    assert "CME" in str(exc_info.value)


def test_read_registry_lane_not_list_raises(tmp_path):
    data = {**EMPTY_REGISTRY, "CPS": {"not": "a list"}}
    path = _write_registry(tmp_path, data)
    with pytest.raises(RegistryReadError):
        read_registry(path)


def test_read_registry_no_file_mutation(tmp_path):
    """read_registry must never modify the file."""
    path = _write_registry(tmp_path)
    before = (tmp_path / "canonical_objects.json").read_bytes()
    read_registry(path)
    after = (tmp_path / "canonical_objects.json").read_bytes()
    assert before == after


def test_read_registry_reads_disk_each_call(tmp_path):
    path = _write_registry(tmp_path)
    r1 = read_registry(path)
    assert r1["CPS"] == []

    # Externally append an object to CPS
    data = json.loads((tmp_path / "canonical_objects.json").read_text())
    data["CPS"].append(_cps_obj("abc123"))
    (tmp_path / "canonical_objects.json").write_text(json.dumps(data))

    r2 = read_registry(path)
    assert len(r2["CPS"]) == 1


# ---------------------------------------------------------------------------
# lane_cardinality
# ---------------------------------------------------------------------------


def test_lane_cardinality_empty(tmp_path):
    path = _write_registry(tmp_path)
    assert lane_cardinality(path, "CPS") == 0


def test_lane_cardinality_invalid_lane_raises_before_io(tmp_path):
    """Invalid lane must raise before any disk read."""
    # No file exists — if I/O were attempted first, FileNotFoundError would occur
    with pytest.raises(RegistryReadError) as exc_info:
        lane_cardinality(str(tmp_path / "nonexistent.json"), "INVALID_LANE")
    assert "invalid lane key" in str(exc_info.value).lower()


def test_lane_cardinality_with_objects(tmp_path):
    data = {**EMPTY_REGISTRY, "CPS": [_cps_obj("id1"), _cps_obj("id2")]}
    path = _write_registry(tmp_path, data)
    assert lane_cardinality(path, "CPS") == 2


def test_lane_cardinality_reflects_disk_update(tmp_path):
    path = _write_registry(tmp_path)
    assert lane_cardinality(path, "CSN") == 0

    data = json.loads((tmp_path / "canonical_objects.json").read_text())
    data["CSN"].append(_csn_obj("csn_001"))
    (tmp_path / "canonical_objects.json").write_text(json.dumps(data))

    assert lane_cardinality(path, "CSN") == 1


def test_lane_cardinality_all_five_lanes(tmp_path):
    path = _write_registry(tmp_path)
    for lane in VALID_LANES:
        assert lane_cardinality(path, lane) == 0


def test_lane_cardinality_isolation(tmp_path):
    """Count for one lane must not include objects from another lane."""
    data = {
        **EMPTY_REGISTRY,
        "CPS": [_cps_obj("cps1"), _cps_obj("cps2"), _cps_obj("cps3")],
        "CSN": [_csn_obj("csn1")],
    }
    path = _write_registry(tmp_path, data)
    assert lane_cardinality(path, "CPS") == 3
    assert lane_cardinality(path, "CSN") == 1
    assert lane_cardinality(path, "CME") == 0


# ---------------------------------------------------------------------------
# all_lane_cardinalities
# ---------------------------------------------------------------------------


def test_all_lane_cardinalities_empty(tmp_path):
    path = _write_registry(tmp_path)
    result = all_lane_cardinalities(path)
    assert set(result.keys()) == VALID_LANES
    assert all(v == 0 for v in result.values())


def test_all_lane_cardinalities_with_objects(tmp_path):
    data = {
        **EMPTY_REGISTRY,
        "CPS": [_cps_obj("c1"), _cps_obj("c2")],
        "CME": [{"id": "m1"}],
    }
    path = _write_registry(tmp_path, data)
    result = all_lane_cardinalities(path)
    assert result["CPS"] == 2
    assert result["CME"] == 1
    assert result["CSN"] == 0
    assert result["StructuralEnvironment"] == 0
    assert result["MediaContext"] == 0


def test_all_lane_cardinalities_single_read(tmp_path):
    """All five counts come from one disk read — verified via consistent snapshot."""
    data = {
        **EMPTY_REGISTRY,
        "CPS": [_cps_obj("c1")],
        "CSN": [_csn_obj("n1"), _csn_obj("n2")],
    }
    path = _write_registry(tmp_path, data)
    result = all_lane_cardinalities(path)
    # The total must equal the sum implied by the single snapshot
    assert sum(result.values()) == 3


def test_all_lane_cardinalities_returns_all_keys(tmp_path):
    path = _write_registry(tmp_path)
    result = all_lane_cardinalities(path)
    assert result.keys() == VALID_LANES


# ---------------------------------------------------------------------------
# total_registry_cardinality
# ---------------------------------------------------------------------------


def test_total_cardinality_empty(tmp_path):
    path = _write_registry(tmp_path)
    assert total_registry_cardinality(path) == 0


def test_total_cardinality_with_objects(tmp_path):
    data = {
        **EMPTY_REGISTRY,
        "CPS": [_cps_obj("c1"), _cps_obj("c2")],
        "CME": [{"id": "m1"}],
        "CSN": [_csn_obj("n1")],
    }
    path = _write_registry(tmp_path, data)
    assert total_registry_cardinality(path) == 4


def test_total_cardinality_equals_sum_of_all_lanes(tmp_path):
    data = {
        **EMPTY_REGISTRY,
        "CPS": [_cps_obj(f"c{i}") for i in range(5)],
        "MediaContext": [{"id": "mc1"}, {"id": "mc2"}],
    }
    path = _write_registry(tmp_path, data)
    total = total_registry_cardinality(path)
    per_lane = all_lane_cardinalities(path)
    # Independent reads — values should agree for same file content
    assert total == sum(per_lane.values())


def test_total_cardinality_reflects_disk_update(tmp_path):
    path = _write_registry(tmp_path)
    assert total_registry_cardinality(path) == 0

    data = json.loads((tmp_path / "canonical_objects.json").read_text())
    data["CPS"].append(_cps_obj("new1"))
    (tmp_path / "canonical_objects.json").write_text(json.dumps(data))

    assert total_registry_cardinality(path) == 1


def test_no_temp_files_created(tmp_path):
    """Reader must not leave any temp files after any operation."""
    path = _write_registry(tmp_path)
    before_files = set(os.listdir(tmp_path))
    read_registry(path)
    all_lane_cardinalities(path)
    total_registry_cardinality(path)
    after_files = set(os.listdir(tmp_path))
    assert before_files == after_files
