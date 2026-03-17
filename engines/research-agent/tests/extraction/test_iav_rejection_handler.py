"""Tests for extraction.iav_rejection_handler."""

from copy import deepcopy

from engines.research_agent.agents.extraction.iav_rejection_handler import (
    REJECT_IDENTITY_CONTAMINATION,
    make_identity_contamination_rejection,
)


_SAMPLE_AU = {
    "id": "AU_" + "a" * 64,
    "text": "The quarterback addressed Tom Brady directly.",
    "parentSourceID": "REC_" + "b" * 64,
    "sourceReference": "source_material_001",
    "splitIndex": 0,
    "schemaVersion": "AU-1.0",
}


def test_reject_identity_contamination_is_string() -> None:
    assert isinstance(REJECT_IDENTITY_CONTAMINATION, str)


def test_reject_identity_contamination_value_contract_pinned() -> None:
    from engines.research_agent.agents.extraction.proper_noun_detector import (
        REJECT_IDENTITY_CONTAMINATION as _PND_REJECT_IDENTITY_CONTAMINATION,
    )

    assert REJECT_IDENTITY_CONTAMINATION == _PND_REJECT_IDENTITY_CONTAMINATION


def test_reject_identity_contamination_value_literal() -> None:
    assert REJECT_IDENTITY_CONTAMINATION == "REJECT_IDENTITY_CONTAMINATION"


def test_rejection_record_has_reason_code() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert "reasonCode" in result


def test_rejection_record_reason_code_value() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert result["reasonCode"] == "REJECT_IDENTITY_CONTAMINATION"


def test_rejection_record_has_au_field() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert "au" in result


def test_rejection_record_au_id_matches() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert result["au"]["id"] == _SAMPLE_AU["id"]


def test_rejection_record_au_text_matches() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert result["au"]["text"] == _SAMPLE_AU["text"]


def test_rejection_record_schema_version() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert result["schemaVersion"] == "REJECTION-1.0"


def test_rejection_record_no_extra_runtime_fields() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert set(result.keys()) == {"reasonCode", "au", "schemaVersion"}


def test_input_au_not_mutated() -> None:
    au = deepcopy(_SAMPLE_AU)
    original = deepcopy(au)
    _ = make_identity_contamination_rejection(au)
    assert au == original


def test_rejection_au_is_copy_not_same_object() -> None:
    au = deepcopy(_SAMPLE_AU)
    result = make_identity_contamination_rejection(au)
    assert result["au"] is not au


def test_rejection_au_mutation_does_not_affect_original() -> None:
    au = deepcopy(_SAMPLE_AU)
    result = make_identity_contamination_rejection(au)
    result["au"]["text"] = "MUTATED"
    assert au["text"] == _SAMPLE_AU["text"]


def test_rejection_record_deterministic() -> None:
    result1 = make_identity_contamination_rejection(_SAMPLE_AU)
    result2 = make_identity_contamination_rejection(_SAMPLE_AU)
    assert result1 == result2


def test_rejection_record_reason_code_deterministic() -> None:
    result1 = make_identity_contamination_rejection(_SAMPLE_AU)
    result2 = make_identity_contamination_rejection(_SAMPLE_AU)
    assert result1["reasonCode"] == result2["reasonCode"]


def test_no_runtime_fields() -> None:
    result = make_identity_contamination_rejection(_SAMPLE_AU)
    assert "timestamp" not in result and "uuid" not in result
