"""
tests/gsd/test_rejection_handler.py

Tests for gsd/rejection_handler.py — Phase 4.4.

Validates:
  - REJECT_ATOMICITY_UNCLEAR constant value (contract-pinned)
  - make_atomicity_rejection structure and field values
  - Input immutability (INV-3)
  - Replay determinism (INV-5)
  - No runtime-derived fields in rejection records
"""

import copy

from engines.research_agent.agents.extraction.composite_marker import ERR_COMPOSITE_BOUNDARY_UNCLEAR
from gsd.rejection_handler import (
    REJECT_ATOMICITY_UNCLEAR,
    make_atomicity_rejection,
)

_SAMPLE_REC = {
    "id": "REC_" + "a" * 64,
    "text": "Coach fired OC and promoted QB coach.",
    "isComposite": True,
    "schemaVersion": "REC-1.0",
}


# ── REJECT_ATOMICITY_UNCLEAR constant ─────────────────────────────────────────

def test_reject_atomicity_unclear_is_string():
    assert isinstance(REJECT_ATOMICITY_UNCLEAR, str)


def test_reject_atomicity_unclear_value_contract_pinned():
    """Contract: reasonCode = ERR_COMPOSITE_BOUNDARY_UNCLEAR."""
    assert REJECT_ATOMICITY_UNCLEAR == ERR_COMPOSITE_BOUNDARY_UNCLEAR


def test_reject_atomicity_unclear_value_literal():
    assert REJECT_ATOMICITY_UNCLEAR == "ERR_COMPOSITE_BOUNDARY_UNCLEAR"


# ── make_atomicity_rejection structure ────────────────────────────────────────

def test_rejection_record_has_reason_code():
    result = make_atomicity_rejection(_SAMPLE_REC)
    assert "reasonCode" in result


def test_rejection_record_reason_code_value():
    result = make_atomicity_rejection(_SAMPLE_REC)
    assert result["reasonCode"] == "ERR_COMPOSITE_BOUNDARY_UNCLEAR"


def test_rejection_record_has_rec_field():
    result = make_atomicity_rejection(_SAMPLE_REC)
    assert "rec" in result


def test_rejection_record_rec_id_matches():
    result = make_atomicity_rejection(_SAMPLE_REC)
    assert result["rec"]["id"] == _SAMPLE_REC["id"]


def test_rejection_record_rec_text_matches():
    result = make_atomicity_rejection(_SAMPLE_REC)
    assert result["rec"]["text"] == _SAMPLE_REC["text"]


def test_rejection_record_schema_version():
    result = make_atomicity_rejection(_SAMPLE_REC)
    assert result["schemaVersion"] == "REJECTION-1.0"


def test_rejection_record_no_extra_runtime_fields():
    """INV-5: rejection record must not contain timestamp or dynamic fields."""
    result = make_atomicity_rejection(_SAMPLE_REC)
    allowed_keys = {"reasonCode", "rec", "schemaVersion"}
    assert set(result.keys()) == allowed_keys


# ── Input immutability (INV-3) ────────────────────────────────────────────────

def test_input_rec_not_mutated():
    """INV-3: make_atomicity_rejection must never mutate the input."""
    rec = copy.deepcopy(_SAMPLE_REC)
    original = copy.deepcopy(rec)
    make_atomicity_rejection(rec)
    assert rec == original


def test_rejection_rec_is_copy_not_same_object():
    """INV-3: modifying rejection record rec must not affect original."""
    rec = copy.deepcopy(_SAMPLE_REC)
    result = make_atomicity_rejection(rec)
    result["rec"]["text"] = "MUTATED"
    assert rec["text"] == _SAMPLE_REC["text"]


# ── Replay determinism (INV-5) ────────────────────────────────────────────────

def test_rejection_record_deterministic():
    """INV-5: identical input must produce identical output."""
    result1 = make_atomicity_rejection(_SAMPLE_REC)
    result2 = make_atomicity_rejection(_SAMPLE_REC)
    assert result1 == result2


def test_rejection_record_reason_code_deterministic():
    result1 = make_atomicity_rejection(_SAMPLE_REC)
    result2 = make_atomicity_rejection(_SAMPLE_REC)
    assert result1["reasonCode"] == result2["reasonCode"]
