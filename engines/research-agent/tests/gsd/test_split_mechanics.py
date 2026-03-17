"""
tests/gsd/test_split_mechanics.py

Tests for gsd/split_mechanics.py — Phase 4.3.

Validates:
  - Non-composite path (1 AU, 0 PCRs)
  - Composite path (N AUs, 1 PCR)
  - 3-clause multi-conjunction handling
  - AU id determinism (INV-5)
  - AU id lane isolation (INV-4)
  - sourceReference pass-through (INV-2)
  - Input REC immutability (INV-3)
  - AU_ID_VERSION is pinned literal
  - Schema fields present and correct
  - ERR_COMPOSITE_BOUNDARY_UNCLEAR raise path
"""

import copy
import pytest

from engines.research_agent.agents.extraction.composite_marker import ERR_COMPOSITE_BOUNDARY_UNCLEAR
from gsd.split_mechanics import AU_ID_VERSION, _au_id, split_rec

# ── Fixtures ──────────────────────────────────────────────────────────────────

_NON_COMPOSITE_REC = {
    "id": "REC_" + "a" * 64,
    "text": "Head coach announced a quarterback change.",
    "isComposite": False,
    "schemaVersion": "REC-1.0",
}

_COMPOSITE_REC = {
    "id": "REC_" + "b" * 64,
    "text": "Coach fired OC and promoted QB coach.",
    "isComposite": True,
    "schemaVersion": "REC-1.0",
}

_TRIPLE_COMPOSITE_REC = {
    "id": "REC_" + "c" * 64,
    "text": "Team won Monday and lost Tuesday and benched the starter.",
    "isComposite": True,
    "schemaVersion": "REC-1.0",
}

_SOURCE_REF = "article://test/source-001"


# ── AU_ID_VERSION ─────────────────────────────────────────────────────────────

def test_au_id_version_is_string():
    assert isinstance(AU_ID_VERSION, str)


def test_au_id_version_pinned():
    """INV-5: must be a pinned literal, never derived from env."""
    assert AU_ID_VERSION == "1.0"


# ── Non-composite path ────────────────────────────────────────────────────────

def test_non_composite_produces_one_au():
    aus, pcrs, rejections = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert len(aus) == 1


def test_non_composite_produces_zero_pcrs():
    aus, pcrs, rejections = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert len(pcrs) == 0


def test_non_composite_au_split_index_zero():
    aus, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert aus[0]["splitIndex"] == 0


def test_non_composite_au_schema_version():
    aus, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert aus[0]["schemaVersion"] == "AU-1.0"


def test_non_composite_au_parent_source_id():
    aus, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert aus[0]["parentSourceID"] == _NON_COMPOSITE_REC["id"]


def test_non_composite_au_source_reference():
    """INV-2: sourceReference must be the caller-supplied value."""
    aus, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert aus[0]["sourceReference"] == _SOURCE_REF


def test_non_composite_au_text_matches_rec():
    aus, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert aus[0]["text"] == _NON_COMPOSITE_REC["text"]


# ── Composite path ────────────────────────────────────────────────────────────

def test_composite_produces_two_aus():
    aus, pcrs, rejections = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert len(aus) == 2


def test_composite_produces_one_pcr():
    aus, pcrs, rejections = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert len(pcrs) == 1


def test_composite_split_indexes_ascending():
    aus, _, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert [au["splitIndex"] for au in aus] == list(range(len(aus)))


def test_composite_au_schema_version():
    aus, _, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    for au in aus:
        assert au["schemaVersion"] == "AU-1.0"


def test_composite_au_parent_source_id():
    aus, _, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    for au in aus:
        assert au["parentSourceID"] == _COMPOSITE_REC["id"]


def test_composite_au_source_reference():
    """INV-2: sourceReference never derived from REC content."""
    aus, _, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    for au in aus:
        assert au["sourceReference"] == _SOURCE_REF


def test_composite_pcr_schema_version():
    _, pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert pcrs[0]["schemaVersion"] == "PCR-1.0"


def test_composite_pcr_parent_source_id():
    _, pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert pcrs[0]["parentSourceId"] == _COMPOSITE_REC["id"]


def test_composite_pcr_original_text():
    _, pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert pcrs[0]["originalText"] == _COMPOSITE_REC["text"]


def test_composite_pcr_split_count():
    aus, pcrs, rejections = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert pcrs[0]["splitCount"] == len(aus)


def test_composite_pcr_split_count_minimum_two():
    _, pcrs, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    assert pcrs[0]["splitCount"] >= 2


# ── Multi-conjunction (3 clauses) ─────────────────────────────────────────────

def test_triple_composite_produces_three_aus():
    aus, _, _rejs = split_rec(_TRIPLE_COMPOSITE_REC, _SOURCE_REF)
    assert len(aus) == 3


def test_triple_composite_split_indexes_ascending():
    aus, _, _rejs = split_rec(_TRIPLE_COMPOSITE_REC, _SOURCE_REF)
    assert [au["splitIndex"] for au in aus] == [0, 1, 2]


def test_triple_composite_pcr_split_count_three():
    _, pcrs, _rejs = split_rec(_TRIPLE_COMPOSITE_REC, _SOURCE_REF)
    assert pcrs[0]["splitCount"] == 3


# ── AU id determinism (INV-5) ─────────────────────────────────────────────────

def test_au_id_deterministic_non_composite():
    aus1, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    aus2, _, _rejs = split_rec(_NON_COMPOSITE_REC, _SOURCE_REF)
    assert aus1[0]["id"] == aus2[0]["id"]


def test_au_id_deterministic_composite():
    aus1, _, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    aus2, _, _rejs = split_rec(_COMPOSITE_REC, _SOURCE_REF)
    for a1, a2 in zip(aus1, aus2):
        assert a1["id"] == a2["id"]


# ── AU id lane isolation (INV-4) ──────────────────────────────────────────────

def test_au_id_lane_isolated_different_parent():
    """Same text + same splitIndex + different parentSourceID → different id."""
    parent_a = "REC_" + "a" * 64
    parent_b = "REC_" + "b" * 64
    text = "Head coach announced a quarterback change."
    id_a = _au_id(parent_a, 0, text)
    id_b = _au_id(parent_b, 0, text)
    assert id_a != id_b


def test_au_id_lane_isolated_different_split_index():
    """Same text + same parent + different splitIndex → different id."""
    parent = "REC_" + "a" * 64
    text = "some repeated text here"
    id_0 = _au_id(parent, 0, text)
    id_1 = _au_id(parent, 1, text)
    assert id_0 != id_1


def test_au_id_starts_with_prefix():
    parent = "REC_" + "a" * 64
    result = _au_id(parent, 0, "some text here")
    assert result.startswith("AU_")


def test_au_id_hex_length():
    """AU id must be 'AU_' + 64 hex characters."""
    parent = "REC_" + "a" * 64
    result = _au_id(parent, 0, "some text here")
    hex_part = result[len("AU_"):]
    assert len(hex_part) == 64
    assert all(c in "0123456789abcdef" for c in hex_part)


# ── Input immutability (INV-3) ────────────────────────────────────────────────

def test_input_rec_not_mutated_non_composite():
    """INV-3: split_rec must never mutate the input REC."""
    rec = copy.deepcopy(_NON_COMPOSITE_REC)
    original = copy.deepcopy(rec)
    split_rec(rec, _SOURCE_REF)
    assert rec == original


def test_input_rec_not_mutated_composite():
    """INV-3: split_rec must never mutate the input REC."""
    rec = copy.deepcopy(_COMPOSITE_REC)
    original = copy.deepcopy(rec)
    split_rec(rec, _SOURCE_REF)
    assert rec == original


# ── ERR_COMPOSITE_BOUNDARY_UNCLEAR ───────────────────────────────────────────

def test_boundary_unclear_returns_rejection_dict(monkeypatch):
    """
    If is_composite returns True but splitting yields < 2 valid segments,
    split_rec must return a rejection dict — never raise (GSD Section VI).
    """
    import re
    import gsd.split_mechanics as sm

    monkeypatch.setattr(sm, "is_composite", lambda text: True)
    monkeypatch.setattr(
        sm, "_CLAUSE_SPLIT_PATTERN",
        re.compile(r"NEVER_MATCHES_ANYTHING_XYZ"),
    )

    rec = {
        "id": "REC_" + "d" * 64,
        "text": "no conjunction here at all",
        "isComposite": True,
        "schemaVersion": "REC-1.0",
    }
    aus, pcrs, rejections = split_rec(rec, _SOURCE_REF)
    assert aus == []
    assert pcrs == []
    assert len(rejections) == 1
    assert rejections[0]["reasonCode"] == "ERR_COMPOSITE_BOUNDARY_UNCLEAR"
    assert rejections[0]["schemaVersion"] == "REJECTION-1.0"
    assert rejections[0]["rec"]["id"] == rec["id"]
