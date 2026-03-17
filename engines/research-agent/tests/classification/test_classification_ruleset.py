import classification.classification_ruleset as rules
from engines.research_agent.agents.classification.classification_ruleset import (
    CLASSIFICATION_RULE_VERSION,
    SEED_TYPE_MEDIA,
    SEED_TYPE_NARRATIVE,
    SEED_TYPE_PRESSURE,
    SEED_TYPE_STRUCTURAL,
    VALID_SEED_TYPES,
    contains_asymmetry_language,
    contains_event_verb,
    contains_framing_language,
)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

def test_classification_rule_version():
    assert CLASSIFICATION_RULE_VERSION == "1.0"


def test_seed_type_pressure():
    assert SEED_TYPE_PRESSURE == "pressure_capable"


def test_seed_type_narrative():
    assert SEED_TYPE_NARRATIVE == "narrative_event"


def test_seed_type_structural():
    assert SEED_TYPE_STRUCTURAL == "structural_environment"


def test_seed_type_media():
    assert SEED_TYPE_MEDIA == "media_context"


def test_valid_seed_types_is_frozenset():
    assert isinstance(VALID_SEED_TYPES, frozenset)


def test_valid_seed_types_count():
    assert len(VALID_SEED_TYPES) == 4


def test_valid_seed_types_contains_all():
    assert SEED_TYPE_PRESSURE in VALID_SEED_TYPES
    assert SEED_TYPE_NARRATIVE in VALID_SEED_TYPES
    assert SEED_TYPE_STRUCTURAL in VALID_SEED_TYPES
    assert SEED_TYPE_MEDIA in VALID_SEED_TYPES


# ── TERM SET INTEGRITY ────────────────────────────────────────────────────────

def test_event_verbs_is_frozenset():
    assert isinstance(rules._EVENT_VERBS, frozenset)


def test_asymmetry_terms_is_frozenset():
    assert isinstance(rules._ASYMMETRY_TERMS, frozenset)


def test_framing_phrases_is_frozenset():
    assert isinstance(rules._FRAMING_PHRASES, frozenset)


def test_event_verbs_count():
    assert len(rules._EVENT_VERBS) == 15


def test_asymmetry_terms_count():
    assert len(rules._ASYMMETRY_TERMS) == 6


def test_framing_phrases_count():
    assert len(rules._FRAMING_PHRASES) == 5


def test_event_verbs_spot_check():
    assert "fired" in rules._EVENT_VERBS and "hired" in rules._EVENT_VERBS


def test_asymmetry_terms_spot_check():
    assert "tension" in rules._ASYMMETRY_TERMS and "volatility" in rules._ASYMMETRY_TERMS


def test_framing_phrases_spot_check():
    assert "described as" in rules._FRAMING_PHRASES and "labeled" in rules._FRAMING_PHRASES


# ── contains_event_verb — TRUE cases ──────────────────────────────────────────

def test_event_verb_fired():
    assert contains_event_verb("The head coach was fired.") is True


def test_event_verb_hired():
    assert contains_event_verb("A new coordinator was hired.") is True


def test_event_verb_announced():
    assert contains_event_verb("The franchise announced a change.") is True


def test_event_verb_suspended():
    assert contains_event_verb("The player was suspended for conduct.") is True


def test_event_verb_case_insensitive():
    assert contains_event_verb("The player was FIRED.") is True


# ── contains_event_verb — FALSE cases ─────────────────────────────────────────

def test_event_verb_absent():
    assert contains_event_verb("The coordinator retains play-calling authority.") is False


def test_event_verb_asymmetry_only():
    assert contains_event_verb("There is tension between the units.") is False


def test_event_verb_word_boundary():
    assert contains_event_verb("The player is unsuspended now.") is False


# ── contains_asymmetry_language — TRUE cases ──────────────────────────────────

def test_asymmetry_tension():
    assert contains_asymmetry_language("There is tension in the locker room.") is True


def test_asymmetry_volatility():
    assert contains_asymmetry_language("Performance volatility continues.") is True


def test_asymmetry_conflict():
    assert contains_asymmetry_language("A conflict between staff is unresolved.") is True


def test_asymmetry_case_insensitive():
    assert contains_asymmetry_language("Ongoing INSTABILITY in the depth chart.") is True


# ── contains_asymmetry_language — FALSE cases ─────────────────────────────────

def test_asymmetry_absent():
    assert contains_asymmetry_language("The quarterback attended practice.") is False


def test_asymmetry_event_verb_only():
    assert contains_asymmetry_language("The coach was fired.") is False


# ── contains_framing_language — TRUE cases ────────────────────────────────────

def test_framing_described_as():
    assert contains_framing_language("Media described the team as struggling.") is True


def test_framing_labeled():
    assert contains_framing_language("The defense was labeled undisciplined.") is True


def test_framing_viewed_as():
    assert contains_framing_language("The move was viewed as punitive.") is True


def test_framing_considered():
    assert contains_framing_language("The coach is considered unstable.") is True


def test_framing_narrative():
    assert contains_framing_language("The narrative around the team shifted.") is True


def test_framing_case_insensitive():
    assert contains_framing_language("Analysts DESCRIBED AS unreliable.") is True


# ── contains_framing_language — FALSE cases ───────────────────────────────────

def test_framing_absent():
    assert contains_framing_language("The coordinator retains authority.") is False


def test_framing_event_verb_only():
    assert contains_framing_language("The coach was fired.") is False


# ── RETURN TYPES ──────────────────────────────────────────────────────────────

def test_contains_event_verb_returns_bool():
    assert isinstance(contains_event_verb("text"), bool)


def test_contains_asymmetry_returns_bool():
    assert isinstance(contains_asymmetry_language("text"), bool)


def test_contains_framing_returns_bool():
    assert isinstance(contains_framing_language("text"), bool)


# ── DETERMINISM (INV-5) ───────────────────────────────────────────────────────

def test_determinism_event_verb():
    results = [contains_event_verb("fired") for _ in range(5)]
    assert all(result is True for result in results)


def test_determinism_asymmetry():
    results = [contains_asymmetry_language("tension") for _ in range(5)]
    assert all(result is True for result in results)


def test_determinism_framing():
    results = [contains_framing_language("described as") for _ in range(5)]
    assert all(result is True for result in results)
