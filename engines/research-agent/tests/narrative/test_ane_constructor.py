from copy import deepcopy

import pytest

from engines.research_agent.agents.narrative.ane_constructor import build_ane_object
from engines.research_agent.agents.narrative.ane_fingerprint import derive_aneseed_fingerprint


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


def _event_seed_id(fields: dict) -> str:
    return derive_aneseed_fingerprint(
        {
            "actorRole": fields.get("actorRole"),
            "action": fields.get("action"),
            "objectRole": fields.get("objectRole"),
            "contextRole": fields.get("contextRole"),
            "timestampContext": fields.get("timestampContext"),
            "sourceReference": fields.get("sourceReference"),
        }
    )


def test_valid_full_fields_returns_ane_object():
    fields = _fields()
    obj = build_ane_object(fields, _event_seed_id(fields))
    assert obj["schemaVersion"] == "ANE-1.0"


def test_field_order_matches_contract():
    fields = _fields()
    obj = build_ane_object(fields, _event_seed_id(fields))
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
    fields = _fields(objectRole=None)
    obj = build_ane_object(fields, _event_seed_id(fields))
    assert obj["objectRole"] is None


def test_null_context_role_allowed():
    fields = _fields(contextRole=None)
    obj = build_ane_object(fields, _event_seed_id(fields))
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
    _ = build_ane_object(f, _event_seed_id(f))
    assert f == before


def test_mismatched_seed_id_is_rejected():
    with pytest.raises(ValueError, match="KP1/KP2/KP3"):
        build_ane_object(_fields(actorRole="different_value"), "ANESEED_" + "1" * 64)


def test_missing_kp_field_is_rejected():
    fields = _fields()
    fields.pop("objectRole")
    with pytest.raises(ValueError, match="missing keypoints"):
        build_ane_object(fields, "ANESEED_" + "2" * 64)
