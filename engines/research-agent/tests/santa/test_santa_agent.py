from engines.research_agent.agents.santa.santa_agent import enforce_santa
from engines.research_agent.agents.santa.santa_ontology import (
    REJECT_SANTA_INVALID_INPUT,
    REJECT_SANTA_INVALID_SUBCLASS,
    REJECT_SANTA_NON_CSN_INPUT,
)
from engines.research_agent.schemas.narrative.validator import validate_narrative_csn_object


def _event(**overrides):
    base = {
        "classification": "CSN",
        "standaloneSubclass": "anecdotal_beat",
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "eventDescription": "Player appeared in a one-off event.",
        "sourceReference": "ref_001",
        "timestampContext": "2025_W10",
    }
    base.update(overrides)
    return base


def test_valid_csn_event_success_and_schema_valid():
    passed, rejection, output = enforce_santa(_event())
    assert passed is True
    assert rejection is None
    assert output is not None
    validate_narrative_csn_object(output["canonicalObject"])


def test_scope_lock_event_type_and_lane_type():
    passed, _rejection, output = enforce_santa(_event())
    assert passed is True
    assert output is not None
    canonical = output["canonicalObject"]
    assert canonical["eventType"] == "CSN"
    assert canonical["laneType"] == "NARRATIVE"


def test_contract_version_set_to_santa_version():
    passed, _rejection, output = enforce_santa(_event())
    assert passed is True
    assert output is not None
    assert output["canonicalObject"]["contractVersion"] == "SANTA-1.0"


def test_no_permanence_field_present_on_canonical_output():
    passed, _rejection, output = enforce_santa(_event())
    assert passed is True
    assert output is not None
    assert "permanence" not in output["canonicalObject"]


def test_reject_classification_cme():
    passed, rejection, output = enforce_santa(_event(classification="CME"))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_SANTA_NON_CSN_INPUT


def test_reject_missing_or_none_standalone_subclass():
    passed, rejection, output = enforce_santa(_event(standaloneSubclass=None))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_SANTA_INVALID_INPUT


def test_reject_narrative_singularity_subclass():
    passed, rejection, output = enforce_santa(_event(standaloneSubclass="narrative_singularity"))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_SANTA_INVALID_SUBCLASS


def test_reject_missing_event_description():
    event = _event()
    event.pop("eventDescription")
    passed, rejection, output = enforce_santa(event)
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_SANTA_INVALID_INPUT


def test_determinism_identical_calls_identical_id():
    event = _event()
    result_a = enforce_santa(event)
    result_b = enforce_santa(event)
    assert result_a[0] is True
    assert result_b[0] is True
    assert result_a[2] is not None
    assert result_b[2] is not None
    assert result_a[2]["canonicalObject"]["id"] == result_b[2]["canonicalObject"]["id"]


def test_enforce_santa_does_not_mutate_input_dict():
    event = _event()
    before = dict(event)
    _ = enforce_santa(event)
    assert event == before


def test_deduplication_status_new_on_success():
    passed, _rejection, output = enforce_santa(_event())
    assert passed is True
    assert output is not None
    assert output["deduplicationStatus"] == "new"


def test_rejection_schema_version_present():
    passed, rejection, output = enforce_santa(_event(classification="CME"))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["schemaVersion"] == "SANTA_REJECTION-1.0"
