from narrative.ane_fingerprint import derive_aneseed_fingerprint
from narrative.ane_id_format import ANESEED_PATTERN


def _fields(**overrides):
    fields = {
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "timestampContext": "2025_W10",
        "sourceReference": "ref_001",
    }
    fields.update(overrides)
    return fields


def test_output_matches_aneseed_pattern():
    out = derive_aneseed_fingerprint(_fields())
    assert ANESEED_PATTERN.match(out)


def test_deterministic_identical_fields_identical_id():
    fields = _fields()
    assert derive_aneseed_fingerprint(fields) == derive_aneseed_fingerprint(fields)


def test_null_object_and_context_roles_use_empty_token():
    a = _fields(objectRole=None, contextRole=None)
    b = _fields(objectRole="", contextRole="")
    assert derive_aneseed_fingerprint(a) == derive_aneseed_fingerprint(b)


def test_event_description_excluded_from_fingerprint():
    a = _fields(eventDescription="first phrasing")
    b = _fields(eventDescription="different phrasing")
    assert derive_aneseed_fingerprint(a) == derive_aneseed_fingerprint(b)


def test_timestamp_bucket_excluded_from_fingerprint():
    a = _fields(timestampBucket="bucket_a")
    b = _fields(timestampBucket="bucket_b")
    assert derive_aneseed_fingerprint(a) == derive_aneseed_fingerprint(b)


def test_timestamp_context_included_in_fingerprint():
    a = _fields(timestampContext="2025_W10")
    b = _fields(timestampContext="2025_W11")
    assert derive_aneseed_fingerprint(a) != derive_aneseed_fingerprint(b)


def test_normalization_applied():
    a = _fields(
        actorRole="  Skill Player  ",
        action=" Appeared!!! ",
        contextRole=" Regular   Season ",
        sourceReference=" Ref 001 ",
    )
    b = _fields(
        actorRole="skill_player",
        action="appeared",
        contextRole="regular_season",
        sourceReference="ref_001",
    )
    assert derive_aneseed_fingerprint(a) == derive_aneseed_fingerprint(b)


def test_correct_aneseed_prefix():
    out = derive_aneseed_fingerprint(_fields())
    assert out.startswith("ANESEED_")
