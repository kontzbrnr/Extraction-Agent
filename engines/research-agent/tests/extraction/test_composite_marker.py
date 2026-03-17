"""
tests/extraction/test_composite_marker.py

Tests for extraction/composite_marker.py.

Validates the composite detection rule against all contract-provided examples
and boundary conditions.

Contract reference:
  - EVENT-MATERIAL-IDENTIFIER.md (EMI) Section IV: Granularity Rule
  - GLOBAL-SPLIT-DOCTRINE.md (GSD) Section II: Composite REC definition
  - GLOBAL-SPLIT-DOCTRINE.md (GSD) Section X: Determinism Lock
  - NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md Section VII: Single-Occurrence Rule
"""

from engines.research_agent.agents.extraction.composite_marker import (
    ERR_COMPOSITE_BOUNDARY_UNCLEAR,
    COMPOSITE_DETECTION_RULE_VERSION,
    is_composite,
)


# ── Module Constants ──────────────────────────────────────────────────────────

def test_composite_detection_rule_version_is_string():
    assert isinstance(COMPOSITE_DETECTION_RULE_VERSION, str)


def test_composite_detection_rule_version_value():
    """Rule version must be pinned for GSD Section X Determinism Lock."""
    assert COMPOSITE_DETECTION_RULE_VERSION == "1.0"


def test_err_composite_boundary_unclear_value():
    """Rejection code must match CREATIVE-LIBRARY-EXTRACTION-AGENT.md Section XII."""
    assert ERR_COMPOSITE_BOUNDARY_UNCLEAR == "ERR_COMPOSITE_BOUNDARY_UNCLEAR"


# ── Contract-Provided Composite Examples (isComposite=True) ──────────────────

def test_composite_coach_fired_oc_and_promoted_qb_coach():
    """
    GSD Section VII Cross-Lane Output example.
    EMI Section IV Granularity Rule example.
    Two distinct ledger mutations: fire + promote.
    """
    assert is_composite("Coach fired OC and promoted QB coach.") is True


def test_composite_team_fired_oc_and_promoted_qb_coach():
    """
    EMI Section IV Granularity Rule canonical example.
    Two distinct ledger mutations: fire + promote.
    """
    assert is_composite("Team fired OC and promoted QB coach.") is True


def test_composite_coach_fired_oc_and_retained_duties():
    """
    GSD Section VII Cross-Lane Output example.
    Yields Narrative Event Seed + Structural Environment Seed.
    """
    assert is_composite("Coach fired OC and retained play-calling duties.") is True


def test_composite_player_argued_and_skipped_media():
    """
    NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md Section VII 'Incorrect' example.
    Marked as requiring two separate Narrative Event Seeds.
    """
    assert is_composite(
        "Player argued with coach and later skipped media availability."
    ) is True


# ── Contract-Provided Non-Composite Examples (isComposite=False) ─────────────

def test_non_composite_head_coach_announced_qb_change():
    """
    NARRATIVE-EVENT-SEED-STRUCTURAL-CONTRACT.md Section VIII Allowed example.
    Single ledger mutation: announcement.
    """
    assert is_composite("Head coach announced a quarterback change.") is False


def test_non_composite_coach_announced_future_bench():
    """
    EMI Section IV Nested Action Clause Rule example.
    Completed event (announcement) + future clause (will bench).
    Only the completed mutation qualifies; future clause is not a ledger mutation.
    """
    assert is_composite("Coach announced he will bench QB next week.") is False


def test_non_composite_noun_phrase_and():
    """
    Coordinating conjunction joining noun phrases, not independent clauses.
    "a promotion." is 2 words — below _MIN_CLAUSE_WORDS threshold.
    Single ledger mutation: announcement.
    """
    assert is_composite("Coach announced a firing and a promotion.") is False


# ── Boundary Conditions ───────────────────────────────────────────────────────

def test_empty_string_returns_false():
    assert is_composite("") is False


def test_whitespace_only_returns_false():
    assert is_composite("   ") is False


def test_none_returns_false():
    # Non-string input must not raise; must return False.
    assert is_composite(None) is False  # type: ignore[arg-type]


def test_single_word_returns_false():
    assert is_composite("fired") is False


def test_single_clause_no_conjunction_returns_false():
    assert is_composite("The coach benched the starter.") is False


def test_single_action_with_object_returns_false():
    assert is_composite("League suspended the head coach.") is False


# ── Determinism Lock (INV-5 / EMI Section IX / GSD Section X) ────────────────

def test_determinism_composite_input():
    """Identical input must always produce identical output — GSD X Determinism Lock."""
    text = "Coach fired OC and promoted QB coach."
    result_a = is_composite(text)
    result_b = is_composite(text)
    assert result_a == result_b


def test_determinism_non_composite_input():
    """Identical input must always produce identical output — GSD X Determinism Lock."""
    text = "Head coach announced a quarterback change."
    result_a = is_composite(text)
    result_b = is_composite(text)
    assert result_a == result_b


def test_output_is_bool_for_composite():
    """EMI Section IX: Binary output only. No confidence scoring."""
    result = is_composite("Coach fired OC and promoted QB coach.")
    assert isinstance(result, bool)


def test_output_is_bool_for_non_composite():
    """EMI Section IX: Binary output only. No confidence scoring."""
    result = is_composite("Head coach announced a quarterback change.")
    assert isinstance(result, bool)
