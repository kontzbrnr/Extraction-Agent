import json
from pathlib import Path

import pytest

from engines.research_agent.agents.nca.nca_ontology import (
    NCA_ASSIGNABLE_SUBCLASSES,
    NCA_RULE_LOGIC_VERSION,
    NCA_SUBCLASS_TAXONOMY_VERSION,
    NCA_SUBCLASS_VALUES,
    NCA_VERSION,
    REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION,
)


def test_nca_version_constant():
    assert NCA_VERSION == "NCA-1.0"


def test_nca_subclass_taxonomy_version_constant():
    assert NCA_SUBCLASS_TAXONOMY_VERSION == "NCA_SUBCLASS_TAXONOMY-1.0"


def test_nca_rule_logic_version_constant():
    assert NCA_RULE_LOGIC_VERSION == "NCA_RULE_LOGIC-1.0"


def test_subclass_values_length():
    assert len(NCA_SUBCLASS_VALUES) == 6


def test_assignable_subclasses_length():
    assert len(NCA_ASSIGNABLE_SUBCLASSES) == 5


def test_all_expected_values_present_in_subclass_values():
    expected = {
        "narrative_singularity",
        "crowd_event",
        "ritual_moment",
        "anecdotal_beat",
        "procedural_curiosity",
        "conflict_flashpoint",
    }
    assert NCA_SUBCLASS_VALUES == expected


def test_narrative_singularity_in_full_values():
    assert "narrative_singularity" in NCA_SUBCLASS_VALUES


def test_narrative_singularity_not_assignable():
    assert "narrative_singularity" not in NCA_ASSIGNABLE_SUBCLASSES


def test_assignable_subclasses_proper_subset():
    assert NCA_ASSIGNABLE_SUBCLASSES < NCA_SUBCLASS_VALUES


def test_subclass_values_is_frozenset_immutable():
    with pytest.raises(AttributeError):
        NCA_SUBCLASS_VALUES.add("new_value")  # type: ignore[attr-defined]


def test_assignable_subclasses_is_frozenset_immutable():
    with pytest.raises(AttributeError):
        NCA_ASSIGNABLE_SUBCLASSES.add("new_value")  # type: ignore[attr-defined]


def test_reject_ambiguous_code_non_empty_string():
    assert isinstance(REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION, str)
    assert REJECT_AMBIGUOUS_NARRATIVE_CLASSIFICATION


def test_subclass_values_match_registry_json_exactly():
    repo_root = Path(__file__).resolve().parents[2]
    registry_path = repo_root / "enums" / "narrative" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_values = set(registry["enums"]["ncaSubclass"]["values"])
    assert NCA_SUBCLASS_VALUES == registry_values
