from copy import deepcopy

from ncg.ncg import enforce_ncg
from ncg.ncg_schema import (
    REASON_FAIL_INVALID_SUBCLASS,
    REASON_FAIL_MISSING_CLASSIFICATION,
    REASON_FAIL_MISSING_EVENT_DESCRIPTION,
    REASON_FAIL_MISSING_SOURCE_REFERENCE,
    REASON_FAIL_MISSING_TIMESTAMP_CONTEXT,
    STAGE_1_CLASSIFICATION,
    STAGE_3_TIMESTAMP_CONTEXT,
)


def _cme_event(**overrides):
    event = {
        "classification": "CME",
        "id": "evt_001",
        "timestampContext": "2025_W10",
        "eventDescription": "League issued a policy update.",
        "sourceReference": "ref_001",
        "actorRole": "league_body",
        "action": "issued",
    }
    event.update(overrides)
    return event


def _csn_event(**overrides):
    event = {
        "classification": "CSN",
        "standaloneSubclass": "anecdotal_beat",
        "id": "evt_002",
        "timestampContext": "2025_W10",
        "eventDescription": "A one-off event occurred.",
        "sourceReference": "ref_002",
        "actorRole": "skill_player",
        "action": "appeared",
    }
    event.update(overrides)
    return event


def test_valid_cme_event_passes():
    passed, verdict, audit = enforce_ncg(_cme_event())
    assert passed is True
    assert verdict is None
    assert audit["verdict"] == "PASS"


def test_valid_csn_event_valid_subclass_passes():
    passed, verdict, audit = enforce_ncg(_csn_event())
    assert passed is True
    assert verdict is None
    assert audit["verdict"] == "PASS"


def test_missing_classification_fails():
    event = _cme_event()
    event.pop("classification")
    passed, verdict, _audit = enforce_ncg(event)
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_CLASSIFICATION


def test_invalid_classification_other_fails():
    passed, verdict, _audit = enforce_ncg(_cme_event(classification="OTHER"))
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_CLASSIFICATION


def test_csn_narrative_singularity_fails():
    passed, verdict, _audit = enforce_ncg(_csn_event(standaloneSubclass="narrative_singularity"))
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_INVALID_SUBCLASS


def test_csn_none_subclass_fails():
    passed, verdict, _audit = enforce_ncg(_csn_event(standaloneSubclass=None))
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_INVALID_SUBCLASS


def test_cme_without_standalone_subclass_passes():
    event = _cme_event()
    event.pop("classification")
    event["classification"] = "CME"
    passed, verdict, _audit = enforce_ncg(event)
    assert passed is True
    assert verdict is None


def test_missing_timestamp_context_fails():
    event = _cme_event()
    event.pop("timestampContext")
    passed, verdict, _audit = enforce_ncg(event)
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_TIMESTAMP_CONTEXT


def test_empty_timestamp_context_fails():
    passed, verdict, _audit = enforce_ncg(_cme_event(timestampContext="   "))
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_TIMESTAMP_CONTEXT


def test_missing_event_description_fails():
    event = _cme_event()
    event.pop("eventDescription")
    passed, verdict, _audit = enforce_ncg(event)
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_EVENT_DESCRIPTION


def test_missing_source_reference_fails():
    event = _cme_event()
    event.pop("sourceReference")
    passed, verdict, _audit = enforce_ncg(event)
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_SOURCE_REFERENCE


def test_stage_ordering_reports_first_failed_stage_only():
    event = {
        "standaloneSubclass": "narrative_singularity",
        "eventDescription": "",
        "sourceReference": "",
    }
    passed, verdict, _audit = enforce_ncg(event)
    assert passed is False
    assert verdict is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_CLASSIFICATION
    assert verdict["failureStage"] == STAGE_1_CLASSIFICATION

    event2 = _csn_event(timestampContext="", eventDescription="", sourceReference="")
    passed2, verdict2, _audit2 = enforce_ncg(event2)
    assert passed2 is False
    assert verdict2 is not None
    assert verdict2["reasonCode"] == REASON_FAIL_MISSING_TIMESTAMP_CONTEXT
    assert verdict2["failureStage"] == STAGE_3_TIMESTAMP_CONTEXT


def test_enforce_ncg_does_not_mutate_input():
    event = _csn_event()
    before = deepcopy(event)
    _ = enforce_ncg(event)
    assert event == before


def test_non_dict_input_fails_not_exception():
    passed, verdict, audit = enforce_ncg("not-a-dict")
    assert passed is False
    assert verdict is not None
    assert audit is not None
    assert verdict["reasonCode"] == REASON_FAIL_MISSING_CLASSIFICATION
