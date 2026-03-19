from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engines.research_agent.agents.civ.civ import enforce_civ
from engines.research_agent.agents.civ.civ_schema import (
    REJECT_LANE_FIELD_CONTAMINATION,
    REJECT_SCHEMA_INCOMPLETE,
    REJECT_VERSION_MISMATCH,
    STAGE_6_VERSION_SNAPSHOT,
)
from engines.research_agent.agents.mcp.mcr_fingerprint import derive_mcr_fingerprint
from engines.research_agent.agents.pressure.cps_fingerprint import derive_cps_fingerprint
from engines.research_agent.agents.meta.meta_ruleset import derive_cme_fingerprint
from engines.research_agent.agents.santa.santa_ruleset import derive_csn_fingerprint
from engines.research_agent.enums.role_token_registry import (
    MEDIA_ENUM_REGISTRY_VERSION,
    MEDIA_TOKEN_REGISTRY,
    NARRATIVE_TOKEN_REGISTRY,
    PRESSURE_ENUM_REGISTRY_VERSION,
)
from engines.research_engine.ledger.registry_writer import RegistryAppendError, append_canonical_object

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _valid_cps_obj() -> dict:
    fields = {
        "signalClass": "structural_condition",
        "environment": "organization",
        "pressureSignalDomain": "authority_distribution",
        "pressureVector": "authority",
        "signalPolarity": "negative",
        "observationSource": "internal_observer",
        "castRequirement": "coach",
        "tier": 2,
        "observation": "authority allocation remains unresolved.",
        "sourceSeed": "competing authority over play-calling",
    }
    return {
        "laneType": "PRESSURE",
        "schemaVersion": "CPS-1.0",
        "canonicalId": derive_cps_fingerprint(fields),
        **fields,
        "enumRegistryVersion": PRESSURE_ENUM_REGISTRY_VERSION,
        "fingerprintVersion": "CPS_FINGERPRINT_V1",
        "contractVersion": "CIV-1.0",
    }


def _valid_csn_obj() -> dict:
    actor = sorted(NARRATIVE_TOKEN_REGISTRY["actorRole"])[0]
    action = sorted(NARRATIVE_TOKEN_REGISTRY["action"])[0]
    obj_role = sorted(NARRATIVE_TOKEN_REGISTRY["objectRole"])[0]
    ctx_role = sorted(NARRATIVE_TOKEN_REGISTRY["contextRole"])[0]
    fields = {
        "actorRole": actor,
        "action": action,
        "objectRole": obj_role,
        "contextRole": ctx_role,
        "subclass": "anecdotal_beat",
        "sourceReference": "doc:abc123#p4l22",
        "timestampContext": "2024_offseason",
    }
    return {
        "laneType": "NARRATIVE",
        "id": derive_csn_fingerprint(fields),
        "eventType": "CSN",
        **fields,
        "eventDescription": "a neutral declarative narrative event.",
        "contractVersion": "CIV-1.0",
    }


def _valid_cme_obj() -> dict:
    fields = {
        "actorRole": "league_body",
        "action": "issued",
        "objectRole": None,
        "contextRole": "regular_season",
        "subtype": "administrative",
        "sourceReference": "doc:league_update_001",
    }
    return {
        "id": derive_cme_fingerprint(fields),
        "eventType": "CME",
        **fields,
        "eventDescription": "league issued an administrative update.",
        "permanence": "permanent",
        "timestampContext": "2024_offseason",
        "fingerprintVersion": "CME_FINGERPRINT_V1",
    }


def _valid_media_context_obj() -> dict:
    framing = sorted(MEDIA_TOKEN_REGISTRY["framingType"])[0]
    context = "discussion frames the roster decision as strategic planning"
    return {
        "id": derive_mcr_fingerprint(
            {"contextDescription": context, "framingType": framing}
        ),
        "laneType": "MEDIA",
        "schemaVersion": "MCR-1.0",
        "contextDescription": context,
        "framingType": framing,
        "sourceSeedID": "AU_" + "a" * 64,
        "fingerprintVersion": "MCR_FINGERPRINT_V1",
        "contractVersion": "MCMA-1.0",
        "enumRegistryVersion": MEDIA_ENUM_REGISTRY_VERSION,
    }


def _snapshot(obj: dict) -> dict:
    return {
        "schemaVersion": obj.get("schemaVersion", ""),
        "enumVersion": obj.get("enumRegistryVersion", "ENUM_v1.0"),
        "contractVersion": obj.get("contractVersion", "CIV-1.0"),
    }


def test_append_call_sites_are_gated_or_use_registry_civ_guard():
    call_sites: set[str] = set()
    for path in PROJECT_ROOT.rglob("*.py"):
        if "tests" in path.parts or "vendor" in path.parts or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "append_canonical_object":
                call_sites.add(path.relative_to(PROJECT_ROOT).as_posix())

    assert call_sites == {
        "infra/orchestration/runtime/orchestrator.py",
    }

    registry_writer_text = (
        PROJECT_ROOT / "engines/research-engine/ledger/registry_writer.py"
    ).read_text(encoding="utf-8")
    assert "_enforce_registry_civ_guard(lane, obj)" in registry_writer_text


def test_registry_rejects_civ_failure_direct_call(tmp_path: Path):
    registry_path = tmp_path / "canonical_objects.json"

    with pytest.raises(RegistryAppendError):
        append_canonical_object(registry_path, "CPS", {"invalid": True})

    if registry_path.exists():
        content = registry_path.read_text(encoding="utf-8")
        assert "invalid" not in content


def test_cps_rejects_narrative_fields():
    obj = _valid_cps_obj()
    obj["subclass"] = "anecdotal_beat"

    passed, rejection, _ = enforce_civ(obj, "CPS", _snapshot(obj))
    assert passed is False
    assert rejection is not None


def test_csn_rejects_pressure_fields():
    obj = _valid_csn_obj()
    obj["pressureVector"] = "authority"

    passed, rejection, _ = enforce_civ(obj, "CSN", _snapshot(obj))
    assert passed is False
    assert rejection is not None


def test_valid_lanes_still_pass_civ():
    cps = _valid_cps_obj()
    cme = _valid_cme_obj()
    csn = _valid_csn_obj()
    media = _valid_media_context_obj()

    cps_passed, _, _ = enforce_civ(cps, "CPS", _snapshot(cps))
    cme_passed, _, _ = enforce_civ(cme, "CME", _snapshot(cme))
    csn_passed, _, _ = enforce_civ(csn, "CSN", _snapshot(csn))
    media_passed, _, _ = enforce_civ(media, "MediaContext", _snapshot(media))

    assert cps_passed is True
    assert cme_passed is True
    assert csn_passed is True
    assert media_passed is True


@pytest.mark.parametrize(
    ("target_lane", "source_lane", "foreign_field"),
    [
        ("CPS", "CME", "subtype"),
        ("CPS", "CSN", "subclass"),
        ("CPS", "MediaContext", "contextDescription"),
        ("CME", "CPS", "pressureVector"),
        ("CME", "CSN", "subclass"),
        ("CME", "MediaContext", "contextDescription"),
        ("CSN", "CPS", "pressureVector"),
        ("CSN", "CME", "subtype"),
        ("CSN", "MediaContext", "contextDescription"),
        ("MediaContext", "CPS", "pressureVector"),
        ("MediaContext", "CME", "subtype"),
        ("MediaContext", "CSN", "subclass"),
    ],
)
def test_cross_lane_contamination_rejected_in_all_directions(
    target_lane: str,
    source_lane: str,
    foreign_field: str,
):
    valid_per_lane = {
        "CPS": _valid_cps_obj,
        "CME": _valid_cme_obj,
        "CSN": _valid_csn_obj,
        "MediaContext": _valid_media_context_obj,
    }
    obj = valid_per_lane[target_lane]()
    assert foreign_field not in obj
    obj[foreign_field] = f"contamination_from_{source_lane.lower()}"

    passed, rejection, _ = enforce_civ(obj, target_lane, _snapshot(obj))

    assert passed is False
    assert rejection is not None
    assert rejection["reasonCode"] in {
        REJECT_SCHEMA_INCOMPLETE,
        REJECT_LANE_FIELD_CONTAMINATION,
    }


def test_version_snapshot_mismatch_rejected_by_civ():
    obj = _valid_cps_obj()
    cycle_snapshot = _snapshot(obj)
    cycle_snapshot["schemaVersion"] = "CPS-9.9"

    passed, rejection, _ = enforce_civ(obj, "CPS", cycle_snapshot)

    assert passed is False
    assert rejection is not None
    assert rejection["reasonCode"] == REJECT_VERSION_MISMATCH
    assert rejection["failureStage"] == STAGE_6_VERSION_SNAPSHOT
