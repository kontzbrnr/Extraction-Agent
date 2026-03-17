"""
tests/gsd/test_composite_ruleset.py

Tests for gsd/composite_ruleset.py.

Validates that the GSD composite detection façade:
  - Exports the correct constants and function
  - Re-exports the canonical is_composite (same object, not a copy)
  - Satisfies contract-provided examples
  - Maintains replay determinism (GSD Section X / INV-5)
"""

import extraction.composite_marker as _marker
import gsd.composite_ruleset as ruleset
from gsd.composite_ruleset import (
    COMPOSITE_DETECTION_RULE_VERSION,
    ERR_COMPOSITE_BOUNDARY_UNCLEAR,
    GSD_COMPOSITE_RULESET_VERSION,
    is_composite,
)


# ── Version Constants ─────────────────────────────────────────────────────────

def test_gsd_composite_ruleset_version_is_string():
    assert isinstance(GSD_COMPOSITE_RULESET_VERSION, str)


def test_gsd_composite_ruleset_version_pinned():
    """GSD-layer version must be pinned — INV-5."""
    assert GSD_COMPOSITE_RULESET_VERSION == "1.0"


def test_composite_detection_rule_version_re_exported():
    """COMPOSITE_DETECTION_RULE_VERSION must be the extraction-layer value."""
    assert COMPOSITE_DETECTION_RULE_VERSION == "1.0"


def test_err_composite_boundary_unclear_re_exported():
    assert ERR_COMPOSITE_BOUNDARY_UNCLEAR == "ERR_COMPOSITE_BOUNDARY_UNCLEAR"


# ── Re-export Identity (no logic duplication) ─────────────────────────────────

def test_is_composite_is_same_object():
    """
    gsd.composite_ruleset.is_composite must be the same function object as
    extraction.composite_marker.is_composite — not a copy or wrapper.
    Guards against silent logic duplication.
    """
    assert is_composite is _marker.is_composite


def test_is_composite_accessible_as_module_attr():
    assert hasattr(ruleset, "is_composite")


# ── Contract Examples ─────────────────────────────────────────────────────────

def test_composite_coach_fired_oc_and_promoted_qb_coach():
    """rec-au.schema.test.json canonical composite example."""
    assert is_composite("Coach fired OC and promoted QB coach.") is True


def test_non_composite_head_coach_announced_qb_change():
    """rec-au.schema.test.json canonical non-composite example."""
    assert is_composite("Head coach announced a quarterback change.") is False


# ── Replay Determinism (INV-5 / GSD Section X) ───────────────────────────────

def test_determinism_composite():
    """Identical input must always produce identical output."""
    text = "Coach fired OC and promoted QB coach."
    assert is_composite(text) == is_composite(text)


def test_determinism_non_composite():
    """Identical input must always produce identical output."""
    text = "Head coach announced a quarterback change."
    assert is_composite(text) == is_composite(text)


# ── Binary Output (EMI Section IX) ───────────────────────────────────────────

def test_output_is_bool_composite():
    assert isinstance(is_composite("Coach fired OC and promoted QB coach."), bool)


def test_output_is_bool_non_composite():
    assert isinstance(is_composite("Head coach announced a quarterback change."), bool)
