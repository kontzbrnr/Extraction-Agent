import copy

import pytest

from engines.research_agent.agents.classification.seed_typing_router import SEED_TYPING_ROUTER_VERSION, route


def _au(text: str) -> dict:
    return {
        "id": "AU_" + "a" * 64,
        "text": text,
        "parentSourceID": "REC_" + "b" * 64,
        "sourceReference": "source_001",
        "splitIndex": 0,
        "schemaVersion": "AU-1.0",
    }


# ── CONSTANT ──────────────────────────────────────────────────────────────────

def test_router_version_constant():
    assert SEED_TYPING_ROUTER_VERSION == "1.0"


# ── SINGLE-SIGNAL ROUTING ─────────────────────────────────────────────────────

def test_routes_narrative_event_verb():
    assert route(_au("The head coach was fired.")) == "narrative_event"


def test_routes_narrative_announced():
    assert route(_au("The franchise announced a quarterback change.")) == "narrative_event"


def test_routes_media_described_as():
    assert route(_au("Analysts described the defense as undisciplined.")) == "media_context"


def test_routes_media_labeled():
    assert route(_au("The roster was labeled a rebuilding project.")) == "media_context"


def test_routes_pressure_tension():
    assert (
        route(_au("There is tension between the offensive coordinator and the head coach."))
        == "pressure_capable"
    )


def test_routes_pressure_volatility():
    assert (
        route(_au("Performance volatility continues at the quarterback position."))
        == "pressure_capable"
    )


def test_routes_structural_default():
    assert (
        route(_au("The offensive coordinator retains play-calling authority."))
        == "structural_environment"
    )


def test_routes_structural_no_markers():
    assert (
        route(_au("The franchise operates with a two-quarterback depth chart."))
        == "structural_environment"
    )


# ── PRIORITY — event verb beats framing ───────────────────────────────────────

def test_priority_event_verb_over_framing():
    assert (
        route(_au("The coach announced the player, described as a leader, was released."))
        == "narrative_event"
    )


# ── PRIORITY — event verb beats asymmetry ─────────────────────────────────────

def test_priority_event_verb_over_asymmetry():
    assert (
        route(_au("Despite the tension, the franchise signed the quarterback."))
        == "narrative_event"
    )


# ── PRIORITY — framing beats asymmetry ────────────────────────────────────────

def test_priority_framing_over_asymmetry():
    assert (
        route(_au("Media described the ongoing conflict as inevitable."))
        == "media_context"
    )


# ── RETURN VALUE CONTRACT ─────────────────────────────────────────────────────

def test_return_is_string():
    assert isinstance(route(_au("The coach was fired.")), str)


def test_return_in_valid_seed_types():
    from engines.research_agent.agents.classification.classification_ruleset import VALID_SEED_TYPES

    assert route(_au("The coach was fired.")) in VALID_SEED_TYPES
    assert route(_au("Analysts described the team as broken.")) in VALID_SEED_TYPES
    assert route(_au("Ongoing tension exists in the locker room.")) in VALID_SEED_TYPES
    assert route(_au("The coordinator retains authority.")) in VALID_SEED_TYPES


# ── INPUT VALIDATION ──────────────────────────────────────────────────────────

def test_missing_text_key_raises():
    with pytest.raises(ValueError):
        route({"id": "AU_" + "a" * 64})


def test_non_string_text_raises():
    with pytest.raises(ValueError):
        route({"text": 42})


# ── INPUT IMMUTABILITY (INV-1) ────────────────────────────────────────────────

def test_au_not_mutated():
    au = _au("The coach was fired.")
    original = copy.deepcopy(au)
    route(au)
    assert au == original


# ── DETERMINISM (INV-5) ───────────────────────────────────────────────────────

def test_determinism_narrative():
    r1 = route(_au("The player was traded."))
    r2 = route(_au("The player was traded."))
    assert r1 == r2


def test_determinism_structural():
    r1 = route(_au("The coordinator retains authority."))
    r2 = route(_au("The coordinator retains authority."))
    assert r1 == r2


def test_determinism_five_calls():
    results = [route(_au("There is tension at the position.")) for _ in range(5)]
    assert len(set(results)) == 1
