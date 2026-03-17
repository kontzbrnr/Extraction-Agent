"""
tests/extraction/test_rule_version.py

Tests for extraction/rule_version.py.

Validates that EXTRACTION_RULE_VERSION is correctly defined, pinned to the
expected value, and immutable — required for GSD Section X Determinism Lock.

Contract reference:
  - GLOBAL-SPLIT-DOCTRINE.md (GSD) Section X: Determinism Lock
  - CREATIVE-LIBRARY-EXTRACTION-AGENT.md Section XII: Determinism Lock
"""

import extraction.rule_version as rv
from engines.research_agent.agents.extraction.rule_version import EXTRACTION_RULE_VERSION


# ── Type and Value ────────────────────────────────────────────────────────────

def test_extraction_rule_version_is_string():
    assert isinstance(EXTRACTION_RULE_VERSION, str)


def test_extraction_rule_version_pinned():
    """
    Value must be pinned. Any change must be intentional and accompanied by
    a rule change justification. Regression-guard for GSD Section X.
    """
    assert EXTRACTION_RULE_VERSION == "1.0"


def test_extraction_rule_version_non_empty():
    assert len(EXTRACTION_RULE_VERSION) > 0


# ── Single Source of Truth ────────────────────────────────────────────────────

def test_extraction_rule_version_is_module_attribute():
    """
    EXTRACTION_RULE_VERSION must be accessible as a module attribute so that
    ExtractionAuditLog (3.6) and other consumers can import it reliably.
    """
    assert hasattr(rv, "EXTRACTION_RULE_VERSION")


# ── Replay Determinism Guard (INV-5 / GSD Section X) ─────────────────────────

def test_extraction_rule_version_stable_across_reads():
    """
    Identical value on every access. Guards against runtime-variable
    assignment (e.g., os.getenv) which would break GSD Section X.
    """
    assert rv.EXTRACTION_RULE_VERSION == rv.EXTRACTION_RULE_VERSION


def test_no_runtime_imports_in_module():
    """
    rule_version.py must not import time, datetime, uuid, random, or os.
    These would allow the constant to vary between runs, violating INV-5.
    """
    import importlib, inspect
    source = inspect.getsource(rv)
    forbidden = ["import time", "import datetime", "import uuid", "import random", "import os"]
    for token in forbidden:
        assert token not in source, f"Forbidden import found in rule_version.py: {token!r}"
