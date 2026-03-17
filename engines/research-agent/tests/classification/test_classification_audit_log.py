"""
tests/classification/test_classification_audit_log.py

Comprehensive test suite for Phase 6.5 Classification Audit Log.
38 tests covering constants, exact keys, field values, active signals
serialization, default versions, validation, and determinism (INV-5).
"""

import pytest

from engines.research_agent.agents.classification.classification_audit_log import (
    CLASSIFICATION_AUDIT_SCHEMA_VERSION,
    make_classification_audit_log,
)
from engines.research_agent.agents.classification.classification_ruleset import (
    CLASSIFICATION_RULE_VERSION,
    SEED_TYPE_NARRATIVE,
    SEED_TYPE_PRESSURE,
    SEED_TYPE_STRUCTURAL,
    SEED_TYPE_MEDIA,
)
from engines.research_agent.agents.classification.multi_match_detector import (
    SIGNAL_ASYMMETRY,
    SIGNAL_EVENT_VERB,
    SIGNAL_FRAMING,
)
from engines.research_agent.agents.classification.seed_typing_router import SEED_TYPING_ROUTER_VERSION


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

def test_schema_version_constant():
    assert CLASSIFICATION_AUDIT_SCHEMA_VERSION == "CLASSIFICATION_AUDIT-1.0"


# ── EXACT KEYS ────────────────────────────────────────────────────────────────

def test_exact_keys_pass():
    result = make_classification_audit_log(
        au_id="AU_" + "a" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert set(result.keys()) == {
        "auId", "sourceReference", "activeSignals", "assignedSeedType",
        "decision", "reasonCode", "ruleVersion", "routerVersion", "schemaVersion"
    }


def test_exact_keys_reject():
    result = make_classification_audit_log(
        au_id="AU_" + "a" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=None,
        decision="REJECT",
        reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
    )
    assert set(result.keys()) == {
        "auId", "sourceReference", "activeSignals", "assignedSeedType",
        "decision", "reasonCode", "ruleVersion", "routerVersion", "schemaVersion"
    }


# ── FIELD VALUES — PASS ───────────────────────────────────────────────────────

def test_au_id_field():
    au_id_val = "AU_" + "b" * 64
    result = make_classification_audit_log(
        au_id=au_id_val,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["auId"] == au_id_val


def test_source_reference_field():
    source_ref = "source_xyz_123"
    result = make_classification_audit_log(
        au_id="AU_" + "c" * 64,
        source_reference=source_ref,
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["sourceReference"] == source_ref


def test_decision_pass():
    result = make_classification_audit_log(
        au_id="AU_" + "d" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["decision"] == "PASS"


def test_reason_code_none_on_pass():
    result = make_classification_audit_log(
        au_id="AU_" + "e" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["reasonCode"] is None


def test_assigned_seed_type_narrative():
    result = make_classification_audit_log(
        au_id="AU_" + "f" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["assignedSeedType"] == SEED_TYPE_NARRATIVE


def test_schema_version_field():
    result = make_classification_audit_log(
        au_id="AU_" + "g" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["schemaVersion"] == "CLASSIFICATION_AUDIT-1.0"


# ── FIELD VALUES — REJECT ─────────────────────────────────────────────────────

def test_decision_reject():
    result = make_classification_audit_log(
        au_id="AU_" + "h" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=None,
        decision="REJECT",
        reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
    )
    assert result["decision"] == "REJECT"


def test_assigned_seed_type_none_on_reject():
    result = make_classification_audit_log(
        au_id="AU_" + "i" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=None,
        decision="REJECT",
        reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
    )
    assert result["assignedSeedType"] is None


def test_reason_code_on_reject():
    result = make_classification_audit_log(
        au_id="AU_" + "j" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=None,
        decision="REJECT",
        reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
    )
    assert result["reasonCode"] == "REJECT_AMBIGUOUS_CLASSIFICATION"


# ── ACTIVE SIGNALS SERIALIZATION ──────────────────────────────────────────────

def test_active_signals_stored_as_list():
    result = make_classification_audit_log(
        au_id="AU_" + "k" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert isinstance(result["activeSignals"], list)


def test_active_signals_sorted_deterministic():
    r1 = make_classification_audit_log(
        au_id="AU_" + "l" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=SEED_TYPE_MEDIA,
        decision="PASS",
    )
    r2 = make_classification_audit_log(
        au_id="AU_" + "l" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_ASYMMETRY, SIGNAL_FRAMING}),
        assigned_seed_type=SEED_TYPE_MEDIA,
        decision="PASS",
    )
    assert r1["activeSignals"] == r2["activeSignals"]


def test_empty_active_signals():
    result = make_classification_audit_log(
        au_id="AU_" + "m" * 64,
        source_reference="ref",
        active_signals=frozenset(),
        assigned_seed_type=SEED_TYPE_STRUCTURAL,
        decision="PASS",
    )
    assert result["activeSignals"] == []


def test_single_signal():
    result = make_classification_audit_log(
        au_id="AU_" + "n" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["activeSignals"] == [SIGNAL_EVENT_VERB]


# ── DEFAULT VERSIONS ──────────────────────────────────────────────────────────

def test_rule_version_default():
    result = make_classification_audit_log(
        au_id="AU_" + "o" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["ruleVersion"] == CLASSIFICATION_RULE_VERSION


def test_router_version_default():
    result = make_classification_audit_log(
        au_id="AU_" + "p" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert result["routerVersion"] == SEED_TYPING_ROUTER_VERSION


def test_rule_version_override():
    result = make_classification_audit_log(
        au_id="AU_" + "q" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
        rule_version="9.9",
    )
    assert result["ruleVersion"] == "9.9"


def test_router_version_override():
    result = make_classification_audit_log(
        au_id="AU_" + "r" * 64,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
        router_version="9.9",
    )
    assert result["routerVersion"] == "9.9"


# ── VALIDATION — au_id ────────────────────────────────────────────────────────

def test_empty_au_id_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="",
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


def test_whitespace_au_id_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="   ",
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


def test_non_string_au_id_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id=None,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


# ── VALIDATION — source_reference ─────────────────────────────────────────────

def test_empty_source_reference_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "s" * 64,
            source_reference="",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


def test_non_string_source_reference_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "t" * 64,
            source_reference=42,
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


# ── VALIDATION — active_signals ───────────────────────────────────────────────

def test_list_active_signals_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "u" * 64,
            source_reference="ref",
            active_signals=["event_verb"],
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


def test_set_active_signals_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "v" * 64,
            source_reference="ref",
            active_signals={"event_verb"},
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
        )


# ── VALIDATION — decision ─────────────────────────────────────────────────────

def test_invalid_decision_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "w" * 64,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="UNKNOWN",
        )


# ── VALIDATION — PASS cross-checks ────────────────────────────────────────────

def test_pass_invalid_seed_type_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "x" * 64,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type="unknown_lane",
            decision="PASS",
        )


def test_pass_none_seed_type_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "y" * 64,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=None,
            decision="PASS",
        )


def test_pass_with_reason_code_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "z" * 64,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
            reason_code="some_code",
        )


# ── VALIDATION — REJECT cross-checks ──────────────────────────────────────────

def test_reject_without_reason_code_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "aa" * 32,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
            assigned_seed_type=None,
            decision="REJECT",
            reason_code=None,
        )


def test_reject_with_empty_reason_code_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "bb" * 32,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
            assigned_seed_type=None,
            decision="REJECT",
            reason_code="",
        )


def test_reject_with_seed_type_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "cc" * 32,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="REJECT",
            reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
        )


# ── VALIDATION — versions ─────────────────────────────────────────────────────

def test_empty_rule_version_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "dd" * 32,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
            rule_version="",
        )


def test_empty_router_version_raises():
    with pytest.raises(ValueError):
        make_classification_audit_log(
            au_id="AU_" + "ee" * 32,
            source_reference="ref",
            active_signals=frozenset({SIGNAL_EVENT_VERB}),
            assigned_seed_type=SEED_TYPE_NARRATIVE,
            decision="PASS",
            router_version="",
        )


# ── DETERMINISM (INV-5) ───────────────────────────────────────────────────────

def test_determinism_pass():
    r1 = make_classification_audit_log(
        au_id="AU_" + "ff" * 32,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    r2 = make_classification_audit_log(
        au_id="AU_" + "ff" * 32,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert r1 == r2


def test_determinism_reject():
    r1 = make_classification_audit_log(
        au_id="AU_" + "gg" * 32,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=None,
        decision="REJECT",
        reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
    )
    r2 = make_classification_audit_log(
        au_id="AU_" + "gg" * 32,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_FRAMING, SIGNAL_ASYMMETRY}),
        assigned_seed_type=None,
        decision="REJECT",
        reason_code="REJECT_AMBIGUOUS_CLASSIFICATION",
    )
    assert r1 == r2


def test_no_timestamp():
    result = make_classification_audit_log(
        au_id="AU_" + "hh" * 32,
        source_reference="ref",
        active_signals=frozenset({SIGNAL_EVENT_VERB}),
        assigned_seed_type=SEED_TYPE_NARRATIVE,
        decision="PASS",
    )
    assert "timestamp" not in result
