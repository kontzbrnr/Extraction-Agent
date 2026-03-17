"""
tests/classification/test_multi_match_detector.py

Comprehensive test suite for Phase 6.4 Multi-Match Detector.
31 tests covering constants, zero/single/multi-signal detection,
return types, subset constraints, and determinism (INV-5).
"""

import pytest

from engines.research_agent.agents.classification.multi_match_detector import (
    ALL_SIGNALS,
    MULTI_MATCH_DETECTOR_VERSION,
    SIGNAL_ASYMMETRY,
    SIGNAL_EVENT_VERB,
    SIGNAL_FRAMING,
    get_active_signals,
    is_multi_match,
)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

def test_version_constant():
    assert MULTI_MATCH_DETECTOR_VERSION == "1.0"


def test_signal_event_verb_value():
    assert SIGNAL_EVENT_VERB == "event_verb"


def test_signal_framing_value():
    assert SIGNAL_FRAMING == "framing"


def test_signal_asymmetry_value():
    assert SIGNAL_ASYMMETRY == "asymmetry"


def test_all_signals_is_frozenset():
    assert isinstance(ALL_SIGNALS, frozenset)


def test_all_signals_count():
    assert len(ALL_SIGNALS) == 3


def test_all_signals_contains_all_constants():
    assert SIGNAL_EVENT_VERB in ALL_SIGNALS
    assert SIGNAL_FRAMING in ALL_SIGNALS
    assert SIGNAL_ASYMMETRY in ALL_SIGNALS


# ── get_active_signals — ZERO signals ─────────────────────────────────────────

def test_zero_signals_returns_empty_frozenset():
    assert get_active_signals("The coordinator retains play-calling authority.") == frozenset()


def test_zero_signals_is_multi_match_false():
    assert is_multi_match("The coordinator retains play-calling authority.") is False


# ── get_active_signals — SINGLE signal (event verb only) ──────────────────────

def test_single_event_verb_signal():
    assert get_active_signals("The head coach was fired.") == frozenset({SIGNAL_EVENT_VERB})


def test_single_event_verb_not_multi_match():
    assert is_multi_match("The head coach was fired.") is False


# ── get_active_signals — SINGLE signal (framing only) ─────────────────────────

def test_single_framing_signal():
    assert get_active_signals("Analysts described the roster as promising.") == frozenset({SIGNAL_FRAMING})


def test_single_framing_not_multi_match():
    assert is_multi_match("Analysts described the roster as promising.") is False


# ── get_active_signals — SINGLE signal (asymmetry only) ───────────────────────

def test_single_asymmetry_signal():
    assert get_active_signals("There is ongoing tension at the position.") == frozenset({SIGNAL_ASYMMETRY})


def test_single_asymmetry_not_multi_match():
    assert is_multi_match("There is ongoing tension at the position.") is False


# ── get_active_signals — TWO signals (event verb + framing) ───────────────────

def test_two_signals_event_and_framing():
    result = get_active_signals("The player was fired, described as a distraction.")
    assert result == frozenset({SIGNAL_EVENT_VERB, SIGNAL_FRAMING})


def test_two_event_framing_is_multi_match():
    assert is_multi_match("The player was fired, described as a distraction.") is True


# ── get_active_signals — TWO signals (event verb + asymmetry) ─────────────────

def test_two_signals_event_and_asymmetry():
    result = get_active_signals("Despite the tension, the player was signed.")
    assert result == frozenset({SIGNAL_EVENT_VERB, SIGNAL_ASYMMETRY})


def test_two_event_asymmetry_is_multi_match():
    assert is_multi_match("Despite the tension, the player was signed.") is True


# ── get_active_signals — TWO signals (framing + asymmetry, no event verb) ─────

def test_two_signals_framing_and_asymmetry():
    result = get_active_signals("Media described the conflict as inevitable.")
    assert result == frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY})


def test_two_framing_asymmetry_is_multi_match():
    assert is_multi_match("Media described the conflict as inevitable.") is True


# ── get_active_signals — THREE signals ────────────────────────────────────────

def test_three_signals_all_active():
    result = get_active_signals(
        "The player was fired amid tension, described as unavoidable."
    )
    assert result == ALL_SIGNALS


def test_three_signals_is_multi_match():
    assert is_multi_match(
        "The player was fired amid tension, described as unavoidable."
    ) is True


# ── RETURN TYPE ───────────────────────────────────────────────────────────────

def test_get_active_signals_returns_frozenset():
    assert isinstance(get_active_signals("any text"), frozenset)


def test_is_multi_match_returns_bool_true():
    assert isinstance(is_multi_match("The player was fired, described as a distraction."), bool)


def test_is_multi_match_returns_bool_false():
    assert isinstance(is_multi_match("The coordinator retains authority."), bool)


# ── SUBSET CONSTRAINT ─────────────────────────────────────────────────────────

def test_active_signals_is_subset_of_all_signals():
    assert get_active_signals("The player was fired.").issubset(ALL_SIGNALS)
    assert get_active_signals("Media described the tension.").issubset(ALL_SIGNALS)
    assert get_active_signals("The coordinator retains authority.").issubset(ALL_SIGNALS)


# ── DETERMINISM (INV-5) ───────────────────────────────────────────────────────

def test_get_active_signals_deterministic():
    r1 = get_active_signals("Media described the conflict as inevitable.")
    r2 = get_active_signals("Media described the conflict as inevitable.")
    assert r1 == r2


def test_is_multi_match_deterministic():
    results = [is_multi_match("The player was fired, described as a distraction.")
               for _ in range(5)]
    assert all(r is True for r in results)
