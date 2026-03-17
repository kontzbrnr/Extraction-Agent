from copy import deepcopy

import pytest

from narrative.ane_constructor import build_ane_object


def _fields(**overrides):
    fields = {
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": "media_audience",
        "contextRole": "regular_season",
        "eventDescription": "A neutral declarative event.",
        "timestampContext": "2025_W10",
        "timestampBucket": "2025_W10",
        "sourceReference": "ref_001",
    }
    fields.update(overrides)
    return fields


def test_valid_full_fields_returns_ane_object():
    obj = build_ane_object(_fields(), "ANESEED_" + "a" * 64)
    assert obj["schemaVersion"] == "ANE-1.0"


def test_field_order_matches_contract():
    obj = build_ane_object(_fields(), "ANESEED_" + "a" * 64)
    assert list(obj.keys()) == [
        "schemaVersion",
        "eventSeedId",
        "actorRole",
        "action",
        "objectRole",
        "contextRole",
        "eventDescription",
        "timestampContext",
        "timestampBucket",
        "sourceReference",
    ]


def test_null_object_role_allowed():
    obj = build_ane_object(_fields(objectRole=None), "ANESEED_" + "b" * 64)
    assert obj["objectRole"] is None


def test_null_context_role_allowed():
    obj = build_ane_object(_fields(contextRole=None), "ANESEED_" + "c" * 64)
    assert obj["contextRole"] is None


@pytest.mark.parametrize(
    "missing",
    [
        "actorRole",
        "action",
        "eventDescription",
        "timestampContext",
        "timestampBucket",
        "sourceReference",
    ],
)
def test_missing_required_field_raises_key_error(missing: str):
    f = _fields()
    f.pop(missing)
    with pytest.raises(KeyError):
        build_ane_object(f, "ANESEED_" + "d" * 64)


@pytest.mark.parametrize(
    "field",
    [
        "actorRole",
        "action",
        "eventDescription",
        "timestampContext",
        "timestampBucket",
        "sourceReference",
    ],
)
def test_empty_required_field_raises_value_error(field: str):
    f = _fields(**{field: ""})
    with pytest.raises(ValueError):
        build_ane_object(f, "ANESEED_" + "e" * 64)


def test_bad_event_seed_id_raises_value_error():
    with pytest.raises(ValueError):
        build_ane_object(_fields(), "BAD_ID")


def test_input_fields_not_mutated():
    f = _fields()
    before = deepcopy(f)
    _ = build_ane_object(f, "ANESEED_" + "f" * 64)
    assert f == before


def test_constructor_accepts_provided_id_without_deriving():
    manual_id = "ANESEED_" + "1" * 64
    obj = build_ane_object(_fields(actorRole="different_value"), manual_id)
    assert obj["eventSeedId"] == manual_id
