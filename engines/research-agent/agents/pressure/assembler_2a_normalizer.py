"""
pressure/assembler_2a_normalizer.py

2A PSAR Assembly Normalization Functions — Phase 7.2

Deterministic normalization functions for 2A.
All functions are pure — identical input → identical output.
No side effects. No state.

Contract authority:
    Structural Assembler Contract v1.1 §IV.2 (enum normalization ownership)
    Investigation Report 2026-03-07 (normalization strategies)

Invariant compliance:
    INV-1: All functions are pure. No module-level mutable state.
    INV-5: Deterministic string transformations. No randomness.
"""

from __future__ import annotations
import re
from engines.research_agent.agents.pressure.assembler_2a_schema import (
    ACTOR_GROUP_NORMALIZATION_TABLE,
    DOMAIN_NORMALIZATION_TABLE,
)
from engines.research_agent.enums.role_token_registry import PRESSURE_TOKEN_REGISTRY


def normalize_actor_group(raw: str) -> str | None:
    """
        Normalize actorGroup_raw → cast_requirement enum token via lookup table.
        Post-validates result against live PRESSURE_TOKEN_REGISTRY["cast_requirement"].

        Returns None if:
            - raw span is not in the lookup table, OR
            - table result is not in the registry (defense in depth; should never
                occur if import-time assertion in assembler_2a_schema passed)

        Lookup is case-insensitive.
    
    Args:
        raw: NLP-extracted subject span from SSI (e.g., "Coaching Staff")
    
    Returns:
        cast_requirement enum token or None
    
    Example:
        normalize_actor_group("Coaching Staff") → "coach"
        normalize_actor_group("unknown actor") → None
    """
    result = ACTOR_GROUP_NORMALIZATION_TABLE.get(raw.strip().lower())
    if result is None:
        return None
    if result not in PRESSURE_TOKEN_REGISTRY["cast_requirement"]:
        return None
    return result


def normalize_action_type(raw: str) -> str | None:
    """
    Normalize action_raw → actionType via snake_case conversion.
    
    Returns None if result is empty (actionTypeResolved = False).
    No registry check — actionType is a PSAR-intermediate free-form field.
    
    Args:
        raw: NLP-extracted verb lemma from SSI (e.g., "retained control")
    
    Returns:
        snake_case actionType or None
    
    Example:
        normalize_action_type("retained control") → "retained_control"
        normalize_action_type("") → None
    """
    result = _to_snake_case(raw)
    return result if result else None


def normalize_object_role(raw: str) -> str | None:
    """
    Normalize objectRole_raw → objectRole via snake_case conversion.
    
    Returns None if result is empty (objectRoleResolved = False).
    No registry check — objectRole is a PSAR-intermediate free-form field.
    
    Args:
        raw: NLP-extracted object span from SSI (e.g., "play calling")
    
    Returns:
        snake_case objectRole or None
    
    Example:
        normalize_object_role("play calling") → "play_calling"
        normalize_object_role("") → None
    """
    result = _to_snake_case(raw)
    return result if result else None


def normalize_domain(raw: str) -> str | None:
    """
        Normalize PLO-E domain label → pressure_signal_domain enum value.
        Post-validates result against live PRESSURE_TOKEN_REGISTRY["pressure_signal_domain"].

        Returns None if:
            - label is not in the domain normalization table, OR
            - table result is not in the registry (defense in depth; should never
                occur if import-time assertion in assembler_2a_schema passed)
    
    Args:
        raw: PLO-E v2 prose domain label (e.g., "Authority Distribution")
    
    Returns:
        pressure_signal_domain enum value or None
    
    Example:
        normalize_domain("Authority Distribution") → "authority_distribution"
        normalize_domain("Unknown Domain") → None
    """
    result = DOMAIN_NORMALIZATION_TABLE.get(raw)
    if result is None:
        return None
    if result not in PRESSURE_TOKEN_REGISTRY["pressure_signal_domain"]:
        return None
    return result


def _to_snake_case(text: str) -> str:
    """
    Convert arbitrary text to snake_case.
    
    Steps: strip → lowercase → replace non-alphanumeric with underscore
           → collapse consecutive underscores → strip leading/trailing underscores.
    
    Args:
        text: Raw text string
    
    Returns:
        snake_case string (may be empty if input contains no alphanumeric chars)
    
    Example:
        _to_snake_case("Retained Control") → "retained_control"
        _to_snake_case("Play-Calling!") → "play_calling"
    """
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")
