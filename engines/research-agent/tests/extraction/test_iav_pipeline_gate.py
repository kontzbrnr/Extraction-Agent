"""Tests for extraction.iav_pipeline_gate."""

from copy import deepcopy

from engines.research_agent.agents.extraction.iav_pipeline_gate import IAV_GATE_VERSION, enforce_iav


_CLEAN_AU = {
    "id": "AU_" + "a" * 64,
    "text": "The quarterback addressed the media audience.",
    "parentSourceID": "REC_" + "b" * 64,
    "sourceReference": "source_001",
    "splitIndex": 0,
    "schemaVersion": "AU-1.0",
}

_CONTAMINATED_AU = {
    "id": "AU_" + "c" * 64,
    "text": "The quarterback addressed Tom Brady directly.",
    "parentSourceID": "REC_" + "d" * 64,
    "sourceReference": "source_001",
    "splitIndex": 0,
    "schemaVersion": "AU-1.0",
}

_SOURCE_REF = "batch_001"


# ── CONSTANT ──────────────────────────────────────────────────────────────────

def test_iav_gate_version_constant():
    assert IAV_GATE_VERSION == "1.0"


# ── RETURN TYPE ───────────────────────────────────────────────────────────────

def test_enforce_iav_returns_tuple():
    assert isinstance(enforce_iav(_CLEAN_AU, _SOURCE_REF), tuple)


def test_enforce_iav_tuple_length():
    assert len(enforce_iav(_CLEAN_AU, _SOURCE_REF)) == 3


# ── PASS PATH (clean AU) ──────────────────────────────────────────────────────

def test_pass_first_element_true():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[0] is True


def test_pass_second_element_none():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[1] is None


def test_pass_audit_log_is_dict():
    assert isinstance(enforce_iav(_CLEAN_AU, _SOURCE_REF)[2], dict)


def test_pass_audit_decision():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[2]["decision"] == "PASS"


def test_pass_audit_reason_code_none():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[2]["reasonCode"] is None


def test_pass_audit_proper_noun_detected_false():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[2]["properNounDetected"] is False


def test_pass_audit_au_id():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[2]["auId"] == _CLEAN_AU["id"]


def test_pass_audit_source_reference():
    assert enforce_iav(_CLEAN_AU, _SOURCE_REF)[2]["sourceReference"] == _SOURCE_REF


# ── REJECT PATH (contaminated AU) ─────────────────────────────────────────────

def test_reject_first_element_false():
    assert enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[0] is False


def test_reject_second_element_is_dict():
    assert isinstance(enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[1], dict)


def test_reject_rejection_reason_code():
    assert (
        enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[1]["reasonCode"]
        == "REJECT_IDENTITY_CONTAMINATION"
    )


def test_reject_rejection_au_id_matches():
    assert (
        enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[1]["au"]["id"]
        == _CONTAMINATED_AU["id"]
    )


def test_reject_rejection_schema_version():
    assert enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[1]["schemaVersion"] == "REJECTION-1.0"


def test_reject_audit_decision():
    assert enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[2]["decision"] == "REJECT"


def test_reject_audit_reason_code():
    assert (
        enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[2]["reasonCode"]
        == "REJECT_IDENTITY_CONTAMINATION"
    )


def test_reject_audit_proper_noun_detected_true():
    assert enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[2]["properNounDetected"] is True


def test_reject_audit_au_id():
    assert enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[2]["auId"] == _CONTAMINATED_AU["id"]


# ── INPUT IMMUTABILITY (INV-3) ────────────────────────────────────────────────

def test_clean_au_not_mutated():
    au = deepcopy(_CLEAN_AU)
    original = deepcopy(au)
    _ = enforce_iav(au, _SOURCE_REF)
    assert au == original


def test_contaminated_au_not_mutated():
    au = deepcopy(_CONTAMINATED_AU)
    original = deepcopy(au)
    _ = enforce_iav(au, _SOURCE_REF)
    assert au == original


def test_rejection_au_is_copy():
    result = enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)
    assert result[1]["au"] is not _CONTAMINATED_AU


# ── NO RUNTIME FIELDS (INV-5) ─────────────────────────────────────────────────

def test_pass_audit_no_timestamp():
    audit_log = enforce_iav(_CLEAN_AU, _SOURCE_REF)[2]
    assert "timestamp" not in audit_log


def test_reject_audit_no_timestamp():
    audit_log = enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[2]
    assert "timestamp" not in audit_log


def test_reject_rejection_no_timestamp():
    rejection = enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)[1]
    assert "timestamp" not in rejection


# ── DETERMINISM (INV-5) ───────────────────────────────────────────────────────

def test_determinism_pass():
    result1 = enforce_iav(_CLEAN_AU, _SOURCE_REF)
    result2 = enforce_iav(_CLEAN_AU, _SOURCE_REF)
    assert result1 == result2


def test_determinism_reject():
    result1 = enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)
    result2 = enforce_iav(_CONTAMINATED_AU, _SOURCE_REF)
    assert result1 == result2
