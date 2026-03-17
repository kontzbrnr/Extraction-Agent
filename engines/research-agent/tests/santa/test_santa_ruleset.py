import pytest

from engines.research_agent.agents.nca.nca_ontology import NCA_ASSIGNABLE_SUBCLASSES
from engines.research_agent.agents.santa.santa_ontology import CSN_ID_PATTERN
from engines.research_agent.agents.santa.santa_ruleset import (
    InvalidCSNSubclassError,
    build_dedup_key,
    derive_csn_fingerprint,
    validate_csn_subclass,
)


def _fp_fields(**overrides):
    base = {
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "subclass": "anecdotal_beat",
        "sourceReference": "ref_001",
    }
    base.update(overrides)
    return base


def _event(**overrides):
    base = {
        "actorRole": "skill_player",
        "action": "appeared",
        "objectRole": None,
        "contextRole": None,
        "standaloneSubclass": "anecdotal_beat",
        "timestampContext": "2025_W10",
    }
    base.update(overrides)
    return base


def test_derive_csn_fingerprint_matches_pattern():
    value = derive_csn_fingerprint(_fp_fields())
    assert CSN_ID_PATTERN.match(value)


def test_derive_csn_fingerprint_deterministic_same_fields():
    fields = _fp_fields()
    assert derive_csn_fingerprint(fields) == derive_csn_fingerprint(fields)


def test_derive_csn_fingerprint_time_neutral_timestamp_excluded():
    a = _fp_fields(timestampContext="2025_W10")
    b = _fp_fields(timestampContext="2026_W12")
    assert derive_csn_fingerprint(a) == derive_csn_fingerprint(b)


def test_derive_csn_fingerprint_permanence_norm_always_empty():
    a = _fp_fields(permanence="permanent")
    b = _fp_fields()
    assert derive_csn_fingerprint(a) == derive_csn_fingerprint(b)


def test_derive_csn_fingerprint_null_roles_use_empty_token():
    a = _fp_fields(objectRole=None, contextRole=None)
    b = _fp_fields(objectRole="", contextRole="")
    assert derive_csn_fingerprint(a) == derive_csn_fingerprint(b)


def test_build_dedup_key_includes_timestamp_context():
    a = _event(timestampContext="2025_W10")
    b = _event(timestampContext="2025_W11")
    assert build_dedup_key(a) != build_dedup_key(b)


@pytest.mark.parametrize("subclass", sorted(NCA_ASSIGNABLE_SUBCLASSES))
def test_validate_csn_subclass_assignable_values_pass(subclass: str):
    validate_csn_subclass(subclass)


def test_validate_csn_subclass_rejects_narrative_singularity():
    with pytest.raises(InvalidCSNSubclassError):
        validate_csn_subclass("narrative_singularity")


def test_validate_csn_subclass_rejects_none():
    with pytest.raises(InvalidCSNSubclassError):
        validate_csn_subclass(None)


def test_validate_csn_subclass_rejects_unknown_string():
    with pytest.raises(InvalidCSNSubclassError):
        validate_csn_subclass("unknown_subclass")
