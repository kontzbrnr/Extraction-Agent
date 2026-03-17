"""
tests/enums/test_role_token_registry.py

Tests for enums/role_token_registry.py — Micro-Project 5.2.

Validates:
  - Version constants for all three lanes
  - Token counts for each field
  - Type integrity (frozenset, MappingProxyType)
  - Immutability enforcement
  - Fingerprint metadata (narrative, media)
  - Lane isolation (no cross-lane key overlap)
  - Spot checks for known stable tokens
  - Determinism (identical import across subprocess runs)
"""

import subprocess
import types

import pytest

from engines.research_agent.enums.role_token_registry import (
    ROLE_TOKEN_REGISTRY_MODULE_VERSION,
    PRESSURE_ENUM_REGISTRY_VERSION,
    PRESSURE_TOKEN_REGISTRY,
    NARRATIVE_ENUM_REGISTRY_VERSION,
    NARRATIVE_TOKEN_REGISTRY,
    NARRATIVE_FINGERPRINT_FIELDS,
    NARRATIVE_NULL_PERMITTED_FIELDS,
    MEDIA_ENUM_REGISTRY_VERSION,
    MEDIA_TOKEN_REGISTRY,
    MEDIA_FINGERPRINT_FIELDS,
)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

def test_module_version_constant():
    assert ROLE_TOKEN_REGISTRY_MODULE_VERSION == "1.1"


def test_pressure_version():
    assert PRESSURE_ENUM_REGISTRY_VERSION == "ENUM_v1.0"


def test_narrative_version():
    assert NARRATIVE_ENUM_REGISTRY_VERSION == "ENUM_v1.0"


def test_media_version():
    assert MEDIA_ENUM_REGISTRY_VERSION == "ENUM_v1.1"


# ── TOKEN COUNTS (exact) ──────────────────────────────────────────────────────

def test_pressure_field_count():
    assert len(PRESSURE_TOKEN_REGISTRY) == 8


def test_pressure_signal_class_count():
    assert len(PRESSURE_TOKEN_REGISTRY["signal_class"]) == 6


def test_pressure_environment_count():
    assert len(PRESSURE_TOKEN_REGISTRY["environment"]) == 9


def test_pressure_domain_count():
    assert len(PRESSURE_TOKEN_REGISTRY["pressure_signal_domain"]) == 14


def test_pressure_vector_count():
    assert len(PRESSURE_TOKEN_REGISTRY["pressure_vector"]) == 10


def test_pressure_polarity_count():
    assert len(PRESSURE_TOKEN_REGISTRY["signal_polarity"]) == 6


def test_pressure_obs_source_count():
    assert len(PRESSURE_TOKEN_REGISTRY["observation_source"]) == 8


def test_pressure_cast_count():
    assert len(PRESSURE_TOKEN_REGISTRY["cast_requirement"]) == 9


def test_pressure_tier_count():
    assert len(PRESSURE_TOKEN_REGISTRY["tier"]) == 3


def test_narrative_field_count():
    assert len(NARRATIVE_TOKEN_REGISTRY) == 5


def test_narrative_actor_role_count():
    assert len(NARRATIVE_TOKEN_REGISTRY["actorRole"]) == 32


def test_narrative_action_count():
    assert len(NARRATIVE_TOKEN_REGISTRY["action"]) == 34


def test_narrative_object_role_count():
    assert len(NARRATIVE_TOKEN_REGISTRY["objectRole"]) == 22


def test_narrative_context_role_count():
    assert len(NARRATIVE_TOKEN_REGISTRY["contextRole"]) == 17


def test_narrative_subclass_count():
    assert len(NARRATIVE_TOKEN_REGISTRY["ncaSubclass"]) == 6


def test_media_field_count():
    assert len(MEDIA_TOKEN_REGISTRY) == 2


def test_media_subtype_count():
    assert len(MEDIA_TOKEN_REGISTRY["subtype"]) == 12


# ── TYPE INTEGRITY ────────────────────────────────────────────────────────────

def test_pressure_token_sets_are_frozensets():
    assert all(isinstance(v, frozenset) for v in PRESSURE_TOKEN_REGISTRY.values())


def test_narrative_token_sets_are_frozensets():
    assert all(isinstance(v, frozenset) for v in NARRATIVE_TOKEN_REGISTRY.values())


def test_media_token_sets_are_frozensets():
    assert all(isinstance(v, frozenset) for v in MEDIA_TOKEN_REGISTRY.values())


def test_pressure_tier_contains_integers():
    assert all(isinstance(v, int) for v in PRESSURE_TOKEN_REGISTRY["tier"])


def test_pressure_tier_values():
    assert PRESSURE_TOKEN_REGISTRY["tier"] == frozenset({1, 2, 3})


def test_pressure_non_tier_contain_strings():
    for field, tokens in PRESSURE_TOKEN_REGISTRY.items():
        if field != "tier":
            assert all(isinstance(v, str) for v in tokens), f"Field {field} contains non-string"


def test_narrative_tokens_contain_strings():
    for field, tokens in NARRATIVE_TOKEN_REGISTRY.items():
        assert all(isinstance(v, str) for v in tokens), f"Field {field} contains non-string"


def test_media_tokens_contain_strings():
    for field, tokens in MEDIA_TOKEN_REGISTRY.items():
        assert all(isinstance(v, str) for v in tokens), f"Field {field} contains non-string"


# ── IMMUTABILITY ──────────────────────────────────────────────────────────────

def test_pressure_registry_is_mapping_proxy():
    assert isinstance(PRESSURE_TOKEN_REGISTRY, types.MappingProxyType)


def test_narrative_registry_is_mapping_proxy():
    assert isinstance(NARRATIVE_TOKEN_REGISTRY, types.MappingProxyType)


def test_media_registry_is_mapping_proxy():
    assert isinstance(MEDIA_TOKEN_REGISTRY, types.MappingProxyType)


def test_pressure_registry_mutation_raises():
    with pytest.raises(TypeError):
        PRESSURE_TOKEN_REGISTRY["new_key"] = frozenset()


def test_narrative_frozenset_mutation_raises():
    with pytest.raises(AttributeError):
        NARRATIVE_TOKEN_REGISTRY["actorRole"].add("new_token")


# ── FINGERPRINT METADATA ──────────────────────────────────────────────────────

def test_narrative_fingerprint_fields():
    assert NARRATIVE_FINGERPRINT_FIELDS == frozenset({
        "actorRole", "action", "objectRole", "contextRole",
        "subclass", "sourceReference"
    })


def test_narrative_null_permitted():
    assert NARRATIVE_NULL_PERMITTED_FIELDS == frozenset({"objectRole", "contextRole"})


def test_media_fingerprint_fields():
    assert MEDIA_FINGERPRINT_FIELDS == frozenset({"subtype"})


def test_narrative_fingerprint_fields_is_frozenset():
    assert isinstance(NARRATIVE_FINGERPRINT_FIELDS, frozenset)


# ── LANE ISOLATION ────────────────────────────────────────────────────────────

def test_cross_lane_key_isolation():
    assert set(PRESSURE_TOKEN_REGISTRY.keys()).isdisjoint(set(NARRATIVE_TOKEN_REGISTRY.keys()))


def test_narrative_excludes_time_bucket():
    assert "timeBucketTierA" not in NARRATIVE_TOKEN_REGISTRY
    assert "tierA" not in NARRATIVE_TOKEN_REGISTRY


# ── SPOT CHECKS (known stable values) ─────────────────────────────────────────

def test_pressure_signal_class_contains_ambient_framing():
    assert "ambient_framing" in PRESSURE_TOKEN_REGISTRY["signal_class"]


def test_narrative_actor_role_contains_head_coach():
    assert "head_coach" in NARRATIVE_TOKEN_REGISTRY["actorRole"]


def test_narrative_actor_role_excludes_ontological_level_keys():
    assert "PERSON" not in NARRATIVE_TOKEN_REGISTRY["actorRole"]
    assert "UNIT" not in NARRATIVE_TOKEN_REGISTRY["actorRole"]


def test_media_subtype_contains_other():
    assert "other" in MEDIA_TOKEN_REGISTRY["subtype"]


def test_narrative_action_contains_challenged_authority():
    assert "challenged_authority" in NARRATIVE_TOKEN_REGISTRY["action"]


# ── DETERMINISM ───────────────────────────────────────────────────────────────

def test_determinism():
    """INV-5: identical import across subprocess runs."""
    code = """
import json
from engines.research_agent.enums.role_token_registry import (
    PRESSURE_TOKEN_REGISTRY,
    NARRATIVE_TOKEN_REGISTRY,
    MEDIA_TOKEN_REGISTRY,
)

# Convert to JSON-serializable sorted structure for comparison
def registry_to_json(reg):
    return {k: sorted(list(v)) for k, v in reg.items()}

print(json.dumps({
    "pressure": registry_to_json(PRESSURE_TOKEN_REGISTRY),
    "narrative": registry_to_json(NARRATIVE_TOKEN_REGISTRY),
    "media": registry_to_json(MEDIA_TOKEN_REGISTRY),
}, sort_keys=True))
"""
    
    result1 = subprocess.run(
        ["python3", "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    
    result2 = subprocess.run(
        ["python3", "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    
    assert result1.stdout == result2.stdout
    assert result1.stdout.strip() != ""
