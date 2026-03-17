"""
Test suite for extraction/rec_producer.py — Phase 3.2

REC production tests only. AU production deferred to Phase 4 (GSD).
"""

import ast
import pytest
import re

from engines.research_agent.agents.extraction.rec_producer import _norm, _rec_id, produce_rec


# --- _norm tests ---

def test_norm_none_returns_empty():
    assert _norm(None) == ""


def test_norm_empty_returns_empty():
    assert _norm("") == ""


def test_norm_whitespace_only_returns_empty():
    assert _norm("   ") == ""


def test_norm_trim_lowercase_collapse():
    assert _norm("  Hello World  ") == "hello_world"


def test_norm_removes_punctuation():
    assert _norm("Hello, World!") == "hello_world"


def test_norm_collapses_multiple_spaces():
    assert _norm("foo   bar") == "foo_bar"


def test_norm_removes_colon_hash():
    assert _norm("doc:abc123#p4l22") == "docabc123p4l22"


def test_norm_preserves_underscore():
    assert _norm("REC_abc123") == "rec_abc123"


def test_norm_tab_becomes_underscore():
    assert _norm("foo\tbar") == "foo_bar"


# --- REC id determinism ---

def test_rec_id_deterministic():
    assert _rec_id("same text") == _rec_id("same text")


def test_rec_id_different_text_differs():
    assert _rec_id("text A") != _rec_id("text B")


def test_rec_id_format():
    assert re.match(r'^REC_[a-f0-9]{64}$', _rec_id("any text"))


# --- produce_rec ---

def test_produce_rec_schema_version():
    assert produce_rec("text")["schemaVersion"] == "REC-1.0"


def test_produce_rec_text_verbatim():
    # text stored verbatim — no mutation
    t = "  Hello World  "
    assert produce_rec(t)["text"] == t


def test_produce_rec_is_composite_default_false():
    assert produce_rec("text")["isComposite"] is False


def test_produce_rec_is_composite_override():
    assert produce_rec("text", is_composite=True)["isComposite"] is True


def test_produce_rec_id_matches_formula():
    t = "Coach fired OC and promoted QB coach."
    rec = produce_rec(t)
    expected = _rec_id(t)
    assert rec["id"] == expected


def test_produce_rec_exact_keys():
    assert set(produce_rec("t").keys()) == {"schemaVersion", "id", "text", "isComposite"}


def test_produce_rec_raises_on_empty():
    with pytest.raises(ValueError):
        produce_rec("")


def test_produce_rec_raises_on_whitespace_only():
    with pytest.raises(ValueError):
        produce_rec("   ")


def test_produce_rec_raises_on_non_str():
    with pytest.raises(TypeError):
        produce_rec(123)


def test_no_forbidden_imports():
    """Verify no forbidden modules (time, datetime, uuid, random) are imported."""
    src = open("extraction/rec_producer.py").read()
    tree = ast.parse(src)
    forbidden = {"time", "datetime", "uuid", "random"}
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in getattr(node, "names", [])
    }
    assert imports & forbidden == set()
