import pytest

from engines.research_agent.agents.meta.meta_ontology import CME_ID_PATTERN
from engines.research_agent.agents.meta.meta_ruleset import assign_cme_subtype, derive_cme_fingerprint


def _event(**overrides):
    base = {
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "unusualProcedural": False,
        "eventDescription": "Neutral event description.",
        "sourceReference": "ref_001",
    }
    base.update(overrides)
    return base


def test_assign_subtype_structural_tier1():
    assert assign_cme_subtype(_event(action="was_removed")) == "structural"


def test_assign_subtype_transactional_tier1():
    assert assign_cme_subtype(_event(action="was_traded")) == "transactional"


def test_assign_subtype_disciplinary_tier1():
    assert assign_cme_subtype(_event(action="was_ejected")) == "disciplinary"


def test_assign_subtype_award_tier1():
    assert assign_cme_subtype(_event(action="awarded")) == "award"


def test_assign_subtype_record_positive_case():
    assert assign_cme_subtype(_event(action="observed_record")) == "record"


def test_assign_subtype_administrative_tier4():
    assert assign_cme_subtype(_event(actorRole="league_body", action="appeared")) == "administrative"


def test_assign_subtype_contractual_tier2():
    assert assign_cme_subtype(_event(action="was_signed", contextRole="regular_season")) == "contractual"


def test_assign_subtype_medical_tier2():
    assert assign_cme_subtype(_event(action="was_designated", contextRole="injury_period")) == "medical"


def test_assign_subtype_competitive_result_tier4():
    assert assign_cme_subtype(_event(actorRole="franchise", action="performed")) == "competitive_result"


def test_assign_subtype_retirement_tier3():
    assert assign_cme_subtype(_event(action="departed", actorRole="skill_player")) == "retirement"


def test_assign_subtype_reinstatement_tier2():
    assert assign_cme_subtype(_event(action="was_signed", contextRole="suspension_period")) == "reinstatement"


def test_assign_subtype_other_fallback():
    assert assign_cme_subtype(_event(action="observed", actorRole="media_member")) == "other"


def test_tier2_context_disambiguation_signed_suspension_reinstatement():
    assert assign_cme_subtype(_event(action="was_signed", contextRole="suspension_period")) == "reinstatement"


def test_tier2_context_disambiguation_signed_other_contractual():
    assert assign_cme_subtype(_event(action="was_signed", contextRole="offseason")) == "contractual"


def test_tier2_context_disambiguation_designated_injury_medical():
    assert assign_cme_subtype(_event(action="was_designated", contextRole="injury_period")) == "medical"


def test_tier2_context_disambiguation_designated_suspension_disciplinary():
    assert assign_cme_subtype(_event(action="was_designated", contextRole="suspension_period")) == "disciplinary"


def test_tier3_actor_disambiguation_departed_head_coach_structural():
    assert assign_cme_subtype(_event(action="departed", actorRole="head_coach")) == "structural"


def test_tier3_actor_disambiguation_departed_skill_player_retirement():
    assert assign_cme_subtype(_event(action="departed", actorRole="skill_player")) == "retirement"


def test_tier4_administrative_league_body_any_action():
    assert assign_cme_subtype(_event(actorRole="league_body", action="appeared")) == "administrative"


def test_assign_subtype_issued_league_body_resolves_administrative():
    assert assign_cme_subtype(_event(actorRole="league_body", action="issued")) == "administrative"


def test_derive_fingerprint_output_matches_pattern():
    value = derive_cme_fingerprint(
        {
            "actorRole": "skill_player",
            "action": "was_traded",
            "objectRole": None,
            "contextRole": "regular_season",
            "subtype": "transactional",
            "permanence": "permanent",
            "sourceReference": "ref_001",
        }
    )
    assert CME_ID_PATTERN.match(value)


def test_derive_fingerprint_deterministic_same_fields_same_id():
    fields = {
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": None,
        "contextRole": "regular_season",
        "subtype": "transactional",
        "permanence": "permanent",
        "sourceReference": "ref_001",
    }
    assert derive_cme_fingerprint(fields) == derive_cme_fingerprint(fields)


def test_derive_fingerprint_time_neutral_timestamp_excluded():
    fields_a = {
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": None,
        "contextRole": "regular_season",
        "subtype": "transactional",
        "permanence": "permanent",
        "sourceReference": "ref_001",
        "timestampContext": "2025_W10",
    }
    fields_b = dict(fields_a)
    fields_b["timestampContext"] = "2026_W12"
    assert derive_cme_fingerprint(fields_a) == derive_cme_fingerprint(fields_b)


def test_derive_fingerprint_null_object_context_use_empty_token():
    with_none = {
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": None,
        "contextRole": None,
        "subtype": "transactional",
        "permanence": "permanent",
        "sourceReference": "ref_001",
    }
    with_empty = dict(with_none)
    with_empty["objectRole"] = ""
    with_empty["contextRole"] = ""
    assert derive_cme_fingerprint(with_none) == derive_cme_fingerprint(with_empty)


def test_derive_fingerprint_permanence_always_permanent():
    fields_bad_perm = {
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": None,
        "contextRole": None,
        "subtype": "transactional",
        "permanence": "temporary",
        "sourceReference": "ref_001",
    }
    fields_good_perm = dict(fields_bad_perm)
    fields_good_perm["permanence"] = "permanent"
    assert derive_cme_fingerprint(fields_bad_perm) == derive_cme_fingerprint(fields_good_perm)


def test_derive_fingerprint_normalization_whitespace_and_lowercase():
    a = {
        "actorRole": "  Skill Player  ",
        "action": "  Was Traded ",
        "objectRole": "",
        "contextRole": " Regular  Season ",
        "subtype": "Transactional",
        "permanence": "permanent",
        "sourceReference": " Ref 001 ",
    }
    b = {
        "actorRole": "skill_player",
        "action": "was_traded",
        "objectRole": "",
        "contextRole": "regular_season",
        "subtype": "transactional",
        "permanence": "permanent",
        "sourceReference": "ref_001",
    }
    assert derive_cme_fingerprint(a) == derive_cme_fingerprint(b)
