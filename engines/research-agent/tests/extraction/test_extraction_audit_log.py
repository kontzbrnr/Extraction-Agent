"""
Unit tests for extraction.extraction_audit_log module.
"""

from engines.research_agent.agents.extraction.extraction_audit_log import make_extraction_audit_log
from engines.research_agent.agents.extraction.rule_version import EXTRACTION_RULE_VERSION


def test_returns_dict():
    """Result is a dict."""
    result = make_extraction_audit_log(rec_count=5, source_reference="test_ref")
    assert isinstance(result, dict)


def test_rec_count_field():
    """recCount equals the passed value."""
    result = make_extraction_audit_log(rec_count=42, source_reference="test_ref")
    assert result["recCount"] == 42


def test_source_reference_field():
    """sourceReference equals the passed value."""
    ref = "source_material_123"
    result = make_extraction_audit_log(rec_count=5, source_reference=ref)
    assert result["sourceReference"] == ref


def test_rule_version_defaults_to_constant():
    """Calling with 2 args gives ruleVersion == EXTRACTION_RULE_VERSION."""
    result = make_extraction_audit_log(rec_count=5, source_reference="test_ref")
    assert result["ruleVersion"] == EXTRACTION_RULE_VERSION


def test_rule_version_override():
    """Passing explicit rule_version='2.0' gives ruleVersion == '2.0'."""
    result = make_extraction_audit_log(
        rec_count=5,
        source_reference="test_ref",
        rule_version="2.0",
    )
    assert result["ruleVersion"] == "2.0"


def test_exact_keys():
    """set(result.keys()) == {'recCount','sourceReference','ruleVersion'}."""
    result = make_extraction_audit_log(rec_count=5, source_reference="test_ref")
    assert set(result.keys()) == {"recCount", "sourceReference", "ruleVersion"}


def test_rec_count_zero_valid():
    """rec_count=0 does not raise."""
    result = make_extraction_audit_log(rec_count=0, source_reference="test_ref")
    assert result["recCount"] == 0


def test_negative_rec_count_raises():
    """rec_count=-1 raises ValueError."""
    try:
        make_extraction_audit_log(rec_count=-1, source_reference="test_ref")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_empty_source_reference_raises():
    """source_reference='' raises ValueError."""
    try:
        make_extraction_audit_log(rec_count=5, source_reference="")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_non_string_source_reference_raises():
    """source_reference=None raises ValueError."""
    try:
        make_extraction_audit_log(rec_count=5, source_reference=None)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_empty_rule_version_raises():
    """rule_version='' raises ValueError."""
    try:
        make_extraction_audit_log(
            rec_count=5,
            source_reference="test_ref",
            rule_version="",
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_determinism():
    """Two calls with identical args return equal dicts."""
    result1 = make_extraction_audit_log(
        rec_count=10,
        source_reference="test_ref",
        rule_version="1.0",
    )
    result2 = make_extraction_audit_log(
        rec_count=10,
        source_reference="test_ref",
        rule_version="1.0",
    )
    assert result1 == result2
