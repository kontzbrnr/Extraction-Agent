import pytest

from engines.research_agent.agents.nca.nca_ontology import (
    NCA_ASSIGNABLE_SUBCLASSES,
    REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION,
)
from engines.research_agent.agents.nca.nca_ruleset import (
    AmbiguousNarrativeClassification,
    classify_subclass,
    make_nca_ambiguity_rejection,
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


def test_rule_1_crowd_event_fan_base_clean():
    assert classify_subclass(_make_event(actorRole="fan_base")) == "crowd_event"


def test_rule_1_crowd_event_explicit_clean_values():
    assert (
        classify_subclass(
            _make_event(actorRole="fan_base", action="appeared", unusualProcedural=False)
        )
        == "crowd_event"
    )


def test_rule_2_conflict_flashpoint():
    assert (
        classify_subclass(_make_event(action="challenged_authority"))
        == "conflict_flashpoint"
    )


def test_rule_3_procedural_curiosity():
    assert (
        classify_subclass(_make_event(unusualProcedural=True))
        == "procedural_curiosity"
    )


def test_rule_3_unusual_procedural_not_bool_raises_type_error():
    with pytest.raises(TypeError):
        classify_subclass(_make_event(unusualProcedural="true"))


def test_rule_4_ritual_moment_object_role_ritual_sequence():
    assert (
        classify_subclass(_make_event(objectRole="ritual_sequence")) == "ritual_moment"
    )


def test_rule_4_ritual_moment_object_role_award_ceremony():
    assert (
        classify_subclass(_make_event(objectRole="award_ceremony")) == "ritual_moment"
    )


@pytest.mark.parametrize("action", ["performed", "attended", "participated", "celebrated"])
def test_rule_4_ritual_moment_ceremonial_actions(action: str):
    assert classify_subclass(_make_event(action=action)) == "ritual_moment"


def test_fallback_anecdotal_beat_for_clean_event():
    assert classify_subclass(_make_event()) == "anecdotal_beat"


def test_ambiguity_actor_fan_base_and_unusual_true():
    with pytest.raises(AmbiguousNarrativeClassification):
        classify_subclass(_make_event(actorRole="fan_base", unusualProcedural=True))


def test_ambiguity_actor_fan_base_and_conflict_action():
    with pytest.raises(AmbiguousNarrativeClassification):
        classify_subclass(_make_event(actorRole="fan_base", action="challenged_authority"))


def test_ambiguity_exception_contains_conflicting_subclasses():
    with pytest.raises(AmbiguousNarrativeClassification) as excinfo:
        classify_subclass(_make_event(actorRole="fan_base", unusualProcedural=True))
    matched = excinfo.value.matched
    assert "crowd_event" in matched
    assert "procedural_curiosity" in matched


def test_make_ambiguity_rejection_reason_code():
    event = _make_event(actorRole="fan_base", unusualProcedural=True)
    rejection = make_nca_ambiguity_rejection(event, ["crowd_event", "procedural_curiosity"])
    assert rejection["reasonCode"] == REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION


def test_make_ambiguity_rejection_matched_rules_is_list():
    event = _make_event()
    rejection = make_nca_ambiguity_rejection(event, ["crowd_event", "procedural_curiosity"])
    assert isinstance(rejection["matchedRules"], list)


def test_make_ambiguity_rejection_does_not_mutate_input():
    event = _make_event(actorRole="fan_base")
    before = dict(event)
    _ = make_nca_ambiguity_rejection(event, ["crowd_event"])
    assert event == before


def test_narrative_singularity_never_returned_for_checked_combinations():
    combinations = [
        _make_event(),
        _make_event(actorRole="fan_base"),
        _make_event(action="challenged_authority"),
        _make_event(unusualProcedural=True),
        _make_event(objectRole="ritual_sequence"),
        _make_event(action="performed"),
    ]
    for event in combinations:
        try:
            result = classify_subclass(event)
        except AmbiguousNarrativeClassification:
            continue
        assert result != "narrative_singularity"


def test_return_value_always_in_assignable_subclasses_for_non_ambiguous_cases():
    combinations = [
        _make_event(),
        _make_event(actorRole="fan_base"),
        _make_event(action="challenged_authority"),
        _make_event(unusualProcedural=True),
        _make_event(objectRole="award_ceremony"),
        _make_event(action="celebrated"),
    ]
    for event in combinations:
        try:
            result = classify_subclass(event)
        except AmbiguousNarrativeClassification:
            continue
        assert result in NCA_ASSIGNABLE_SUBCLASSES
