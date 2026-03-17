from engines.research_agent.agents.meta.meta_agent import enforce_meta
from engines.research_agent.agents.meta.meta_ontology import REJECT_META_NON_CME_INPUT
from engines.research_agent.agents.meta.meta_schema import validate_cme_object


def _event(**overrides) -> dict:
    base = {
        "classification": "CME",
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": None,
        "contextRole": "regular_season",
        "eventDescription": "Player was traded before week 3.",
        "sourceReference": "ref_001",
        "timestampContext": "2025_W03",
        "unusualProcedural": False,
    }
    base.update(overrides)
    return base


def test_valid_cme_event_success_and_schema_valid():
    passed, rejection, output = enforce_meta(_event())
    assert passed is True
    assert rejection is None
    assert output is not None
    validate_cme_object(output["canonicalObject"])


def test_non_overreach_event_type_always_cme():
    passed, _rejection, output = enforce_meta(_event())
    assert passed is True
    assert output is not None
    assert output["canonicalObject"]["eventType"] == "CME"


def test_non_overreach_no_standalone_subclass_field_in_output():
    passed, _rejection, output = enforce_meta(_event())
    assert passed is True
    assert output is not None
    assert "standaloneSubclass" not in output["canonicalObject"]


def test_deduplication_status_new_on_success():
    passed, _rejection, output = enforce_meta(_event())
    assert passed is True
    assert output is not None
    assert output["deduplicationStatus"] == "new"


def test_reject_when_input_classification_is_csn():
    passed, rejection, output = enforce_meta(_event(classification="CSN"))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_META_NON_CME_INPUT


def test_reject_when_standalone_subclass_non_null():
    passed, rejection, output = enforce_meta(_event(standaloneSubclass="crowd_event"))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_META_NON_CME_INPUT


def test_reject_when_required_field_missing():
    event = _event()
    event.pop("action")
    passed, rejection, output = enforce_meta(event)
    assert passed is False
    assert output is None
    assert rejection is not None


def test_deterministic_same_input_same_canonical_id():
    event = _event()
    result1 = enforce_meta(event)
    result2 = enforce_meta(event)
    assert result1[0] is True
    assert result2[0] is True
    assert result1[2] is not None
    assert result2[2] is not None
    assert result1[2]["canonicalObject"]["id"] == result2[2]["canonicalObject"]["id"]


def test_does_not_mutate_input_dict():
    event = _event()
    before = dict(event)
    _ = enforce_meta(event)
    assert event == before


def test_rejection_schema_version_present():
    passed, rejection, output = enforce_meta(_event(classification="CSN"))
    assert passed is False
    assert output is None
    assert rejection is not None
    assert rejection["schemaVersion"] == "META_REJECTION-1.0"
