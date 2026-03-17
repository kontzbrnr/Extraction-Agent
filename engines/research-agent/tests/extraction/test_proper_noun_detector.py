"""
tests/extraction/test_proper_noun_detector.py

Tests for extraction/proper_noun_detector.py — Phase 5.1.

Validates:
  - PROPER_NOUN_DETECTOR_VERSION constant
  - REJECT_IDENTITY_CONTAMINATION constant
  - Pattern compiled at module level (INV-1)
  - contains_proper_noun() detection logic
  - Sentence-initial exclusion (no false positives)
  - Acronym exclusion (ALL-CAPS not flagged)
  - Punctuation-attached token handling
  - Edge cases: empty, single token, all lowercase
  - Replay determinism (INV-5)
"""

import inspect

import pytest

from engines.research_agent.agents.extraction.proper_noun_detector import (
    PROPER_NOUN_DETECTOR_VERSION,
    REJECT_IDENTITY_CONTAMINATION,
    contains_proper_noun,
)


# ── Constants ─────────────────────────────────────────────────────────────────

def test_proper_noun_detector_version_is_string():
    assert isinstance(PROPER_NOUN_DETECTOR_VERSION, str)


def test_proper_noun_detector_version_pinned():
    """INV-5: version must be a pinned literal."""
    assert PROPER_NOUN_DETECTOR_VERSION == "1.0"


def test_reject_identity_contamination_is_string():
    assert isinstance(REJECT_IDENTITY_CONTAMINATION, str)


def test_reject_identity_contamination_value():
    """Contract: REJECT_IDENTITY_CONTAMINATION matches contract-specified code."""
    assert REJECT_IDENTITY_CONTAMINATION == "REJECT_IDENTITY_CONTAMINATION"


# ── Module-level pattern (INV-1) ──────────────────────────────────────────────

def test_pattern_compiled_at_module_level():
    """INV-1: _PROPER_NOUN_PATTERN must be assigned at module level."""
    import extraction.proper_noun_detector as m
    src = inspect.getsource(m)
    assert "_PROPER_NOUN_PATTERN" in src
    assert "def contains_proper_noun" in src
    pattern_pos = src.index("_PROPER_NOUN_PATTERN")
    func_pos = src.index("def contains_proper_noun")
    assert pattern_pos < func_pos


# ── True positives — proper noun detected ────────────────────────────────────

def test_named_individual_detected():
    """Named individual in non-initial position is detected."""
    assert contains_proper_noun("The coach fired Brady.") is True


def test_named_franchise_detected():
    """Named franchise in non-initial position is detected."""
    assert contains_proper_noun("The coach joined Dallas.") is True


def test_multi_word_name_detected():
    """First word of a multi-word proper name in non-initial position is detected."""
    assert contains_proper_noun("GM signed Tom Brady to an extension.") is True


def test_proper_noun_mid_sentence():
    """Proper noun mid-sentence is detected."""
    assert contains_proper_noun("Owner promoted Nick to head coach.") is True


def test_proper_noun_with_trailing_punctuation():
    """Proper noun with attached punctuation is still detected."""
    assert contains_proper_noun("The coach fired Brady, citing performance.") is True


def test_proper_noun_second_clause():
    """Proper noun appearing in second clause is detected."""
    assert contains_proper_noun("Coach resigned and Brady retired.") is True


# ── True negatives — no proper noun ──────────────────────────────────────────

def test_fully_lowercase_text():
    """Fully lowercase text contains no proper nouns."""
    assert contains_proper_noun("the coach announced a change at quarterback.") is False


def test_sentence_initial_capital_only():
    """Sentence-initial capital word is not flagged (documented exclusion)."""
    assert contains_proper_noun("Head coach announced a quarterback change.") is False


def test_all_caps_acronym_not_flagged():
    """All-caps acronyms (NFL, OC, GM) do not match [A-Z][a-z]+ pattern."""
    assert contains_proper_noun("The NFL announced OC changes.") is False


def test_role_based_abstract_text():
    """Fully abstracted, role-based text produces no detection."""
    assert contains_proper_noun("The head coach fired the offensive coordinator.") is False


def test_empty_string():
    """Empty string returns False."""
    assert contains_proper_noun("") is False


def test_single_token():
    """Single token text (only first word) returns False."""
    assert contains_proper_noun("Brady") is False


def test_single_lowercase_token():
    """Single lowercase token returns False."""
    assert contains_proper_noun("coach") is False


def test_two_tokens_both_lowercase():
    """Two lowercase tokens returns False."""
    assert contains_proper_noun("head coach") is False


# ── Return type ───────────────────────────────────────────────────────────────

def test_returns_bool_true():
    assert isinstance(contains_proper_noun("The coach fired Brady."), bool)


def test_returns_bool_false():
    assert isinstance(contains_proper_noun("Head coach announced a change."), bool)


# ── Replay determinism (INV-5) ────────────────────────────────────────────────

_RUNS = 5

def test_determinism_positive():
    """INV-5: identical input producing True is stable across runs."""
    text = "The coach fired Brady."
    results = [contains_proper_noun(text) for _ in range(_RUNS)]
    assert all(r == results[0] for r in results)


def test_determinism_negative():
    """INV-5: identical input producing False is stable across runs."""
    text = "Head coach announced a quarterback change."
    results = [contains_proper_noun(text) for _ in range(_RUNS)]
    assert all(r == results[0] for r in results)


def test_version_constant_stability():
    """INV-5: version constant is identical across repeated reads."""
    results = [PROPER_NOUN_DETECTOR_VERSION for _ in range(_RUNS)]
    assert all(r == results[0] for r in results)
