import json

import pytest

from narrative.ane_dedup import (
    STATUS_DUPLICATE,
    STATUS_NEW_CANONICAL,
    detect_ane_duplicate,
)


def _registry_base():
    return {
        "schemaVersion": "CANONICAL_REGISTRY-1.0",
        "CPS": [],
        "CME": [],
        "CSN": [],
        "StructuralEnvironment": [],
        "MediaContext": [],
    }


def test_id_not_in_registry_returns_new(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry_base()), encoding="utf-8")
    status, obj = detect_ane_duplicate("ANESEED_" + "a" * 64, str(path))
    assert status == STATUS_NEW_CANONICAL
    assert obj is None


def test_id_present_in_registry_returns_duplicate_copy(tmp_path):
    path = tmp_path / "registry.json"
    registry = _registry_base()
    registry["ANE"] = [{"eventSeedId": "ANESEED_" + "a" * 64, "payload": "x"}]
    path.write_text(json.dumps(registry), encoding="utf-8")
    status, obj = detect_ane_duplicate("ANESEED_" + "a" * 64, str(path))
    assert status == STATUS_DUPLICATE
    assert obj == {"eventSeedId": "ANESEED_" + "a" * 64, "payload": "x"}
    assert obj is not registry["ANE"][0]


def test_empty_registry_returns_new(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry_base()), encoding="utf-8")
    status, obj = detect_ane_duplicate("ANESEED_" + "b" * 64, str(path))
    assert status == STATUS_NEW_CANONICAL
    assert obj is None


def test_bad_event_seed_id_raises_value_error(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry_base()), encoding="utf-8")
    with pytest.raises(ValueError):
        detect_ane_duplicate("BAD_ID", str(path))


def test_reads_from_disk_every_call(tmp_path):
    path = tmp_path / "registry.json"
    first = _registry_base()
    path.write_text(json.dumps(first), encoding="utf-8")

    status1, obj1 = detect_ane_duplicate("ANESEED_" + "c" * 64, str(path))
    assert status1 == STATUS_NEW_CANONICAL
    assert obj1 is None

    second = _registry_base()
    second["ANE"] = [{"eventSeedId": "ANESEED_" + "c" * 64}]
    path.write_text(json.dumps(second), encoding="utf-8")

    status2, obj2 = detect_ane_duplicate("ANESEED_" + "c" * 64, str(path))
    assert status2 == STATUS_DUPLICATE
    assert obj2 == {"eventSeedId": "ANESEED_" + "c" * 64}


def test_never_mutates_registry_file(tmp_path):
    path = tmp_path / "registry.json"
    registry = _registry_base()
    registry["ANE"] = [{"eventSeedId": "ANESEED_" + "d" * 64}]
    original = json.dumps(registry, sort_keys=True)
    path.write_text(original, encoding="utf-8")

    _ = detect_ane_duplicate("ANESEED_" + "d" * 64, str(path))

    after = json.dumps(json.loads(path.read_text(encoding="utf-8")), sort_keys=True)
    assert after == original


def test_status_literals_match_spec():
    assert STATUS_NEW_CANONICAL == "NEW_CANONICAL"
    assert STATUS_DUPLICATE == "DUPLICATE"
