from unittest.mock import patch

from emi.emi_ruleset import (
    EMI_RULESET_VERSION,
    _PROCEDURAL_LOCKED_LEXICON,
    _SPECULATIVE_MARKERS,
    check_actor_attribution,
    check_completed_occurrence,
    check_procedural_micro_adjustment,
    classify_eligibility,
)
from emi.emi_schema import (
    REJECT_EMI_ACTOR_ATTRIBUTION,
    REJECT_EMI_LEDGER_INCOMPLETE,
    REJECT_EMI_SPECULATIVE_FRAMING,
)


def test_emi_ruleset_version_constant():
    assert EMI_RULESET_VERSION == "EMI_RULESET-1.0"


def test_speculative_markers_is_frozenset():
    assert isinstance(_SPECULATIVE_MARKERS, frozenset)


def test_procedural_locked_lexicon_is_frozenset():
    assert isinstance(_PROCEDURAL_LOCKED_LEXICON, frozenset)


def test_check_completed_occurrence_known_good():
    assert check_completed_occurrence("The team traded the player.") is None


def test_check_completed_occurrence_known_bad_speculative():
    assert (
        check_completed_occurrence("The team may trade the player.")
        == REJECT_EMI_SPECULATIVE_FRAMING
    )


def test_check_actor_attribution_known_good():
    assert check_actor_attribution("The commissioner suspended him.") is None


def test_check_actor_attribution_known_bad():
    assert (
        check_actor_attribution("Was suspended by the league.")
        == REJECT_EMI_ACTOR_ATTRIBUTION
    )


def test_check_procedural_micro_adjustment_with_locked_term_passes():
    text = "The team made an adjustment due to hazard after the storm."
    assert check_procedural_micro_adjustment(text) is None


def test_check_procedural_micro_adjustment_without_locked_term_rejects():
    assert (
        check_procedural_micro_adjustment("The team made an adjustment.")
        == REJECT_EMI_LEDGER_INCOMPLETE
    )


def test_classify_eligibility_clean_au_passes():
    au = {"text": "The team traded the player yesterday."}
    passed, code, ploe_fork = classify_eligibility(au)
    assert passed is True
    assert code is None
    assert isinstance(ploe_fork, bool)


def test_classify_eligibility_speculative_au_rejects():
    au = {"text": "The team may trade the player."}
    assert classify_eligibility(au) == (False, REJECT_EMI_SPECULATIVE_FRAMING, False)


def test_classify_eligibility_fail_fast_stops_on_first_rule():
    au = {"text": "The team may trade the player."}
    with patch("emi.emi_ruleset.check_actor_attribution") as actor_rule:
        actor_rule.return_value = None
        result = classify_eligibility(au)
    actor_rule.assert_not_called()
    assert result == (False, REJECT_EMI_SPECULATIVE_FRAMING, False)
