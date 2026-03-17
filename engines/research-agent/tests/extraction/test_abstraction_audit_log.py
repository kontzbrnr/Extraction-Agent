"""
tests/extraction/test_abstraction_audit_log.py

Tests for extraction/abstraction_audit_log.py — Micro-Project 5.4.
"""

import pytest

from engines.research_agent.agents.extraction.abstraction_audit_log import (
    ABSTRACTION_AUDIT_SCHEMA_VERSION,
    make_abstraction_audit_log,
)
from engines.research_agent.agents.extraction.abstraction_mapper import ABSTRACTION_MAPPER_VERSION
from engines.research_agent.agents.extraction.proper_noun_detector import PROPER_NOUN_DETECTOR_VERSION


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

def test_schema_version_constant():
    assert ABSTRACTION_AUDIT_SCHEMA_VERSION == "ABSTRACTION_AUDIT-1.0"


# ── RETURN TYPE AND EXACT KEYS ────────────────────────────────────────────────

def test_returns_dict():
    result = make_abstraction_audit_log(
        au_id="AU_123",
        source_reference="src://item",
        proper_noun_detected=False,
        decision="PASS",
    )
    assert isinstance(result, dict)


def test_exact_keys_pass():
    result = make_abstraction_audit_log(
        au_id="AU_123",
        source_reference="src://item",
        proper_noun_detected=False,
        decision="PASS",
    )
    assert set(result.keys()) == {
        "auId",
        "sourceReference",
        "properNounDetected",
        "decision",
        "reasonCode",
        "detectorVersion",
        "mapperVersion",
        "schemaVersion",
    }


def test_exact_keys_reject():
    result = make_abstraction_audit_log(
        au_id="AU_123",
        source_reference="src://item",
        proper_noun_detected=True,
        decision="REJECT",
        reason_code="REJECT_IDENTITY_CONTAMINATION",
    )
    assert set(result.keys()) == {
        "auId",
        "sourceReference",
        "properNounDetected",
        "decision",
        "reasonCode",
        "detectorVersion",
        "mapperVersion",
        "schemaVersion",
    }


# ── FIELD VALUES — PASS RECORD ────────────────────────────────────────────────

def test_au_id_field():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["auId"] == "AU_ABC"


def test_source_reference_field():
    result = make_abstraction_audit_log("AU_ABC", "src://ref", False, "PASS")
    assert result["sourceReference"] == "src://ref"


def test_proper_noun_detected_false():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["properNounDetected"] is False


def test_decision_pass():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["decision"] == "PASS"


def test_reason_code_none_on_pass():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["reasonCode"] is None


def test_schema_version_field():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["schemaVersion"] == "ABSTRACTION_AUDIT-1.0"


# ── FIELD VALUES — REJECT RECORD ──────────────────────────────────────────────

def test_decision_reject():
    result = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        True,
        "REJECT",
        reason_code="REJECT_IDENTITY_CONTAMINATION",
    )
    assert result["decision"] == "REJECT"


def test_reason_code_on_reject():
    result = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        True,
        "REJECT",
        reason_code="REJECT_IDENTITY_CONTAMINATION",
    )
    assert result["reasonCode"] == "REJECT_IDENTITY_CONTAMINATION"


def test_proper_noun_detected_true_on_reject():
    result = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        True,
        "REJECT",
        reason_code="REJECT_IDENTITY_CONTAMINATION",
    )
    assert result["properNounDetected"] is True


# ── DEFAULT VERSIONS ──────────────────────────────────────────────────────────

def test_detector_version_default():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["detectorVersion"] == PROPER_NOUN_DETECTOR_VERSION


def test_mapper_version_default():
    result = make_abstraction_audit_log("AU_ABC", "src://x", False, "PASS")
    assert result["mapperVersion"] == ABSTRACTION_MAPPER_VERSION


def test_detector_version_override():
    result = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        False,
        "PASS",
        detector_version="9.9",
    )
    assert result["detectorVersion"] == "9.9"


def test_mapper_version_override():
    result = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        False,
        "PASS",
        mapper_version="9.9",
    )
    assert result["mapperVersion"] == "9.9"


# ── VALIDATION — au_id ────────────────────────────────────────────────────────

def test_empty_au_id_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("", "src://x", False, "PASS")


def test_whitespace_au_id_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("   ", "src://x", False, "PASS")


def test_non_string_au_id_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log(None, "src://x", False, "PASS")


# ── VALIDATION — source_reference ─────────────────────────────────────────────

def test_empty_source_reference_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "", False, "PASS")


def test_non_string_source_reference_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", 42, False, "PASS")


# ── VALIDATION — proper_noun_detected ─────────────────────────────────────────

def test_non_bool_proper_noun_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "src://x", 1, "PASS")


def test_non_bool_proper_noun_string_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "src://x", "true", "PASS")


# ── VALIDATION — decision ─────────────────────────────────────────────────────

def test_invalid_decision_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "src://x", False, "UNKNOWN")


def test_empty_decision_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "src://x", False, "")


# ── VALIDATION — reason_code / decision cross-check ───────────────────────────

def test_reject_without_reason_code_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "src://x", True, "REJECT", reason_code=None)


def test_reject_with_empty_reason_code_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log("AU_ABC", "src://x", True, "REJECT", reason_code="")


def test_pass_with_reason_code_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log(
            "AU_ABC",
            "src://x",
            False,
            "PASS",
            reason_code="REJECT_IDENTITY_CONTAMINATION",
        )


# ── VALIDATION — version strings ──────────────────────────────────────────────

def test_empty_detector_version_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log(
            "AU_ABC",
            "src://x",
            False,
            "PASS",
            detector_version="",
        )


def test_empty_mapper_version_raises():
    with pytest.raises(ValueError):
        make_abstraction_audit_log(
            "AU_ABC",
            "src://x",
            False,
            "PASS",
            mapper_version="",
        )


# ── DETERMINISM ───────────────────────────────────────────────────────────────

def test_determinism():
    first = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        True,
        "REJECT",
        reason_code="REJECT_IDENTITY_CONTAMINATION",
    )
    second = make_abstraction_audit_log(
        "AU_ABC",
        "src://x",
        True,
        "REJECT",
        reason_code="REJECT_IDENTITY_CONTAMINATION",
    )
    assert first == second
