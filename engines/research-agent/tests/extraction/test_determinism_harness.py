"""
Phase 3.7 — Determinism Test Harness.

Validates INV-5: identical inputs always produce identical outputs
across 5 consecutive calls, for all Phase 3 extraction components.

Contract authority: GSD Section X Determinism Lock,
CREATIVE-LIBRARY-EXTRACTION-AGENT.md Section XII.
"""

from engines.research_agent.agents.extraction.rec_producer import produce_rec
from engines.research_agent.agents.extraction.composite_marker import is_composite
from engines.research_agent.agents.extraction.rec_validator import validate_rec
from engines.research_agent.agents.extraction.rule_version import EXTRACTION_RULE_VERSION


_RUNS = 5

_INPUTS = [
    "Head coach announced a quarterback change.",
    "Coach fired OC and promoted QB coach.",
    "League suspended the head coach.",
    "Team signed a veteran quarterback.",
    "Coach fired OC and retained play-calling duties.",
]


def _all_equal(results: list) -> bool:
    """Return True if all items in results are equal to the first."""
    return all(r == results[0] for r in results[1:])


def test_produce_rec_determinism_non_composite():
    """produce_rec determinism for non-composite texts."""
    for text in _INPUTS:
        results = [produce_rec(text) for _ in range(_RUNS)]
        assert _all_equal(results), f"Non-deterministic produce_rec for: {text}"
        assert len(results) == _RUNS


def test_produce_rec_determinism_composite_flag():
    """produce_rec determinism with is_composite=True."""
    text = "Coach fired OC and promoted QB coach."
    results = [produce_rec(text, is_composite=True) for _ in range(_RUNS)]
    assert _all_equal(results)
    assert len(results) == _RUNS


def test_produce_rec_determinism_composite_flag_false():
    """produce_rec determinism with is_composite=False."""
    text = "Head coach announced a quarterback change."
    results = [produce_rec(text, is_composite=False) for _ in range(_RUNS)]
    assert _all_equal(results)
    assert len(results) == _RUNS


def test_is_composite_determinism_composite_text():
    """is_composite determinism for composite text."""
    text = "Coach fired OC and promoted QB coach."
    results = [is_composite(text) for _ in range(_RUNS)]
    assert _all_equal(results)
    assert len(results) == _RUNS
    assert all(r is True for r in results)


def test_is_composite_determinism_non_composite_text():
    """is_composite determinism for non-composite text."""
    text = "Head coach announced a quarterback change."
    results = [is_composite(text) for _ in range(_RUNS)]
    assert _all_equal(results)
    assert len(results) == _RUNS
    assert all(r is False for r in results)


def test_validate_rec_determinism():
    """validate_rec determinism."""
    rec = produce_rec("Head coach announced a quarterback change.")
    for _ in range(_RUNS):
        validate_rec(rec)


def test_rule_version_stable():
    """EXTRACTION_RULE_VERSION stable across reads."""
    results = [EXTRACTION_RULE_VERSION for _ in range(_RUNS)]
    assert _all_equal(results)
    assert all(r == "1.0" for r in results)


def test_rec_id_stable_across_runs():
    """REC id field stable across runs."""
    text = "Head coach announced a quarterback change."
    results = [produce_rec(text) for _ in range(_RUNS)]
    ids = [r["id"] for r in results]
    assert _all_equal(ids), "Non-deterministic REC id"
    assert all(rec_id.startswith("REC_") for rec_id in ids)


def test_rec_schema_version_stable():
    """REC schemaVersion field stable across runs."""
    text = _INPUTS[0]
    results = [produce_rec(text) for _ in range(_RUNS)]
    versions = [r["schemaVersion"] for r in results]
    assert _all_equal(versions)
    assert all(v == "REC-1.0" for v in versions)
