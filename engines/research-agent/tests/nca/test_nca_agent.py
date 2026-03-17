from engines.research_agent.agents.nca.nca_agent import enforce_nca
from engines.research_agent.agents.nca.nca_ontology import (
    NCA_RULE_LOGIC_VERSION,
    NCA_SUBCLASS_TAXONOMY_VERSION,
    REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION,
)


def _make_event(**overrides) -> dict:
    event = {
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "unusualProcedural": False,
    }
    event.update(overrides)
    return event


def test_enforce_nca_clean_event_passes():
    passed, rejection, result = enforce_nca(_make_event())
    assert passed is True
    assert rejection is None
    assert isinstance(result, dict)


def test_enforce_nca_clean_event_classification_csn():
    passed, _rejection, result = enforce_nca(_make_event())
    assert passed is True
    assert result is not None
    assert result["classification"] == "CSN"


def test_enforce_nca_clean_event_subclass_anecdotal_beat():
    passed, _rejection, result = enforce_nca(_make_event())
    assert passed is True
    assert result is not None
    assert result["standaloneSubclass"] == "anecdotal_beat"


def test_enforce_nca_taxonomy_version_field():
    passed, _rejection, result = enforce_nca(_make_event())
    assert passed is True
    assert result is not None
    assert result["subclassTaxonomyVersion"] == NCA_SUBCLASS_TAXONOMY_VERSION


def test_enforce_nca_rule_logic_version_field():
    passed, _rejection, result = enforce_nca(_make_event())
    assert passed is True
    assert result is not None
    assert result["subclassRuleLogicVersion"] == NCA_RULE_LOGIC_VERSION


def test_enforce_nca_fan_base_maps_to_crowd_event():
    passed, _rejection, result = enforce_nca(_make_event(actorRole="fan_base"))
    assert passed is True
    assert result is not None
    assert result["standaloneSubclass"] == "crowd_event"


def test_enforce_nca_challenged_authority_maps_to_conflict_flashpoint():
    passed, _rejection, result = enforce_nca(_make_event(action="challenged_authority"))
    assert passed is True
    assert result is not None
    assert result["standaloneSubclass"] == "conflict_flashpoint"


def test_enforce_nca_unusual_true_maps_to_procedural_curiosity():
    passed, _rejection, result = enforce_nca(_make_event(unusualProcedural=True))
    assert passed is True
    assert result is not None
    assert result["standaloneSubclass"] == "procedural_curiosity"


def test_enforce_nca_ritual_object_role_maps_to_ritual_moment():
    passed, _rejection, result = enforce_nca(_make_event(objectRole="ritual_sequence"))
    assert passed is True
    assert result is not None
    assert result["standaloneSubclass"] == "ritual_moment"


def test_enforce_nca_ambiguous_event_rejects():
    passed, rejection, result = enforce_nca(
        _make_event(actorRole="fan_base", unusualProcedural=True)
    )
    assert passed is False
    assert result is None
    assert isinstance(rejection, dict)


def test_enforce_nca_ambiguous_rejection_reason_code():
    passed, rejection, result = enforce_nca(
        _make_event(actorRole="fan_base", unusualProcedural=True)
    )
    assert passed is False
    assert result is None
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION


def test_enforce_nca_does_not_mutate_input():
    event = _make_event(actorRole="fan_base")
    before = dict(event)
    _ = enforce_nca(event)
    assert event == before


def test_enforce_nca_input_not_dict_rejects():
    passed, rejection, result = enforce_nca("not-a-dict")
    assert passed is False
    assert result is None
    assert isinstance(rejection, dict)


def test_enforce_nca_never_returns_narrative_singularity():
    events = [
        _make_event(),
        _make_event(actorRole="fan_base"),
        _make_event(action="challenged_authority"),
        _make_event(unusualProcedural=True),
        _make_event(objectRole="award_ceremony"),
    ]
    for event in events:
        passed, _rejection, result = enforce_nca(event)
        if passed:
            assert result is not None
            assert result["standaloneSubclass"] != "narrative_singularity"
