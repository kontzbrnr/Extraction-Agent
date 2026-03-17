import copy

from engines.research_agent.agents.classification.ambiguity_handler import (
    REJECT_AMBIGUOUS_CLASSIFICATION,
    is_ambiguous_classification,
    make_ambiguity_rejection,
)


_SAMPLE_AU = {
    "id": "AU_" + "a" * 64,
    "text": "Media described the conflict as inevitable.",
    "parentSourceID": "REC_" + "b" * 64,
    "sourceReference": "source_001",
    "splitIndex": 0,
    "schemaVersion": "AU-1.0",
}


# ── CONSTANT ──────────────────────────────────────────────────────────────────

def test_reject_code_is_string():
    assert isinstance(REJECT_AMBIGUOUS_CLASSIFICATION, str)


def test_reject_code_literal_value():
    assert REJECT_AMBIGUOUS_CLASSIFICATION == "REJECT_AMBIGUOUS_CLASSIFICATION"


# ── is_ambiguous_classification — TRUE ───────────────────────────────────────

def test_ambiguous_framing_and_asymmetry():
    assert is_ambiguous_classification("Media described the conflict as systemic.") is True


def test_ambiguous_viewed_as_tension():
    assert (
        is_ambiguous_classification("The situation was viewed as one of ongoing tension.")
        is True
    )


def test_ambiguous_labeled_volatility():
    assert is_ambiguous_classification("The unit was labeled prone to volatility.") is True


# ── is_ambiguous_classification — FALSE (event verb present) ─────────────────

def test_not_ambiguous_event_verb_present():
    assert is_ambiguous_classification("The player was fired amid the described conflict.") is False


def test_not_ambiguous_all_three_signals():
    assert (
        is_ambiguous_classification("The coach announced changes described as tension-reducing.")
        is False
    )


# ── is_ambiguous_classification — FALSE (single signal only) ─────────────────

def test_not_ambiguous_framing_only():
    assert is_ambiguous_classification("Analysts described the roster as promising.") is False


def test_not_ambiguous_asymmetry_only():
    assert (
        is_ambiguous_classification("There is ongoing tension at the quarterback position.")
        is False
    )


def test_not_ambiguous_event_verb_only():
    assert is_ambiguous_classification("The head coach was fired.") is False


def test_not_ambiguous_no_signals():
    assert is_ambiguous_classification("The coordinator retains play-calling authority.") is False


# ── is_ambiguous_classification — RETURN TYPE ────────────────────────────────

def test_returns_bool_true_case():
    assert isinstance(is_ambiguous_classification("Media described the conflict."), bool)


def test_returns_bool_false_case():
    assert isinstance(
        is_ambiguous_classification("The coordinator retains authority."),
        bool,
    )


# ── REJECTION RECORD STRUCTURE ────────────────────────────────────────────────

def test_rejection_has_reason_code():
    assert "reasonCode" in make_ambiguity_rejection(_SAMPLE_AU)


def test_rejection_reason_code_value():
    assert (
        make_ambiguity_rejection(_SAMPLE_AU)["reasonCode"]
        == "REJECT_AMBIGUOUS_CLASSIFICATION"
    )


def test_rejection_has_au_field():
    assert "au" in make_ambiguity_rejection(_SAMPLE_AU)


def test_rejection_au_id_matches():
    assert make_ambiguity_rejection(_SAMPLE_AU)["au"]["id"] == _SAMPLE_AU["id"]


def test_rejection_au_text_matches():
    assert make_ambiguity_rejection(_SAMPLE_AU)["au"]["text"] == _SAMPLE_AU["text"]


def test_rejection_schema_version():
    assert make_ambiguity_rejection(_SAMPLE_AU)["schemaVersion"] == "REJECTION-1.0"


def test_rejection_exact_keys():
    assert set(make_ambiguity_rejection(_SAMPLE_AU).keys()) == {
        "reasonCode",
        "au",
        "schemaVersion",
    }


# ── INPUT IMMUTABILITY (INV-3) ────────────────────────────────────────────────

def test_input_au_not_mutated():
    au = copy.deepcopy(_SAMPLE_AU)
    original = copy.deepcopy(au)
    make_ambiguity_rejection(au)
    assert au == original


def test_rejection_au_is_copy_not_same_object():
    result = make_ambiguity_rejection(_SAMPLE_AU)
    assert result["au"] is not _SAMPLE_AU


def test_rejection_au_mutation_does_not_affect_original():
    result = make_ambiguity_rejection(_SAMPLE_AU)
    result["au"]["text"] = "MUTATED"
    assert _SAMPLE_AU["text"] != "MUTATED"


# ── REPLAY DETERMINISM (INV-5) ────────────────────────────────────────────────

def test_detection_deterministic():
    r1 = is_ambiguous_classification("Media described the conflict.")
    r2 = is_ambiguous_classification("Media described the conflict.")
    assert r1 == r2


def test_rejection_record_deterministic():
    r1 = make_ambiguity_rejection(_SAMPLE_AU)
    r2 = make_ambiguity_rejection(_SAMPLE_AU)
    assert r1 == r2


def test_no_runtime_fields():
    result = make_ambiguity_rejection(_SAMPLE_AU)
    assert "timestamp" not in result
    assert "uuid" not in result
