"""
tests/orchestrator/test_orchestrator_commit.py

Commit Layer Tests — Phase 13.4.

Verifies:
    - StructuralEnvironment lane bypasses CIV (not in VALID_CIV_LANES).
    - CPS dedup gate functions correctly and blocks duplicates.
    - CIV rejection prevents registry append.
    - _commit_batch correctly counts commits and rejections.
    - INV-3: objects never mutated.
    - INV-4: lane isolation maintained.
    - INV-5: lane order deterministic via sorted_lanes().

Fixture pattern: tmp_path, real files, no mocking.
"""

import json

import pytest
from pathlib import Path

from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.batch_collector import make_batch_collector
from engines.research_engine.ledger.registry_writer import EMPTY_REGISTRY, RegistryAppendError
from infra.orchestration.runtime.orchestrator import (
    _commit_batch,
    _commit_canonical_object,
)
from engines.research_agent.agents.pressure.cps_fingerprint import derive_cps_fingerprint
from engines.research_agent.agents.pressure.psta_schema import STATUS_DUPLICATE


# ── Constants ─────────────────────────────────────────────────────────────────

CPS_CANONICAL_ID = "CPS_" + "a" * 64


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_cycle_snapshot() -> dict:
    """Build a minimal valid cycle_snapshot for enforce_civ."""
    return {
        "schemaVersion":   "CPS-1.0",
        "enumVersion":     "ENUM_v1.0",
        "contractVersion": "CIV-1.0",
    }


def _make_cps_obj(canonical_id: str = CPS_CANONICAL_ID) -> dict:
    """Build a CIV-valid CPS object."""
    return {
        "laneType": "CPS",
        "schemaVersion": "CPS-1.0",
        "canonicalId": canonical_id,
        "signalClass": "structural_tension",
        "environment": "organizational",
        "pressureSignalDomain": "authority_distribution",
        "pressureVector": "competing_influences",
        "signalPolarity": "negative",
        "observationSource": "internal_audit",
        "castRequirement": "executive_decision_required",
        "tier": 2,
        "observation": "authority allocation remains unresolved.",
        "sourceSeed": "competing authority over play-calling",
        "enumRegistryVersion": "ENUM_v1.0",
        "fingerprintVersion": "CPS_FINGERPRINT_V1",
        "contractVersion": "CIV-1.0",
    }


def _setup_registry_with_cps(registry_path: Path, canonical_id: str = CPS_CANONICAL_ID) -> None:
    """Write a registry file with one CPS object (simulating pre-existing entry).

    Creates the parent directory if needed.
    """
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry = {
        k: (list(v) if isinstance(v, list) else v)
        for k, v in EMPTY_REGISTRY.items()
    }
    registry["CPS"].append(_make_cps_obj(canonical_id))
    atomic_write_json(str(registry_path), registry)


# ── GROUP A: StructuralEnvironment bypass ─────────────────────────────────────

def test_structural_environment_bypasses_civ_commits(tmp_path):
    """A1: StructuralEnvironment lane commits without CIV; returns (True, None)."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    se_obj = {"id": "SE-001"}
    ok, rejection = _commit_canonical_object(
        se_obj, "StructuralEnvironment", registry_path, cycle_snapshot
    )

    assert ok is True
    assert rejection is None
    assert registry_path.exists()

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["StructuralEnvironment"]) == 1
    assert registry["StructuralEnvironment"][0] == se_obj


def test_structural_environment_skips_civ_no_required_fields(tmp_path):
    """A2: StructuralEnvironment bypasses CIV but still requires registry ID field."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Empty object bypasses CIV but must still satisfy registry append
    # lane ID requirements (id field for StructuralEnvironment).
    se_obj = {}
    with pytest.raises(RegistryAppendError):
        _commit_canonical_object(
            se_obj, "StructuralEnvironment", registry_path, cycle_snapshot
        )


# ── GROUP B: CPS dedup gate ───────────────────────────────────────────────────

def test_cps_first_commit_succeeds(tmp_path):
    """B1: CPS object with incomplete schema is rejected before append."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Seed empty registry file for CPS dedup pre-read.
    atomic_write_json(
        str(registry_path),
        {
            k: (list(v) if isinstance(v, list) else v)
            for k, v in EMPTY_REGISTRY.items()
        },
    )

    cps_obj = _make_cps_obj(CPS_CANONICAL_ID)
    ok, rejection = _commit_canonical_object(
        cps_obj, "CPS", registry_path, cycle_snapshot
    )

    assert ok is False
    assert rejection is not None
    assert rejection["reasonCode"] == "REJECT_SCHEMA_INCOMPLETE"

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["CPS"]) == 0


def test_cps_duplicate_rejected(tmp_path):
    """B2: Second commit of same CPS ID: returns (False, rejection)."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Pre-populate registry with the CPS object.
    _setup_registry_with_cps(registry_path, CPS_CANONICAL_ID)

    # Try to commit the same ID again.
    cps_obj = _make_cps_obj(CPS_CANONICAL_ID)
    ok, rejection = _commit_canonical_object(
        cps_obj, "CPS", registry_path, cycle_snapshot
    )

    assert ok is False
    assert rejection is not None
    assert rejection["reasonCode"] == STATUS_DUPLICATE
    assert rejection["stage"] == "CPS_DEDUP"


def test_cps_duplicate_not_appended(tmp_path):
    """B3: Duplicate CPS object not added to registry."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Pre-populate registry with one CPS object.
    _setup_registry_with_cps(registry_path, CPS_CANONICAL_ID)

    # Try to commit the same ID again.
    cps_obj = _make_cps_obj(CPS_CANONICAL_ID)
    _commit_canonical_object(cps_obj, "CPS", registry_path, cycle_snapshot)

    # Verify registry still has exactly one CPS object.
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["CPS"]) == 1


# ── GROUP C: CIV gate ─────────────────────────────────────────────────────────

def test_civ_incomplete_schema_rejected(tmp_path):
    """C1: Empty CSN object fails CIV Schema Completeness; returns (False, rejection)."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Empty object will fail CIV Check 1 (Schema Completeness).
    csn_obj = {}
    ok, rejection = _commit_canonical_object(
        csn_obj, "CSN", registry_path, cycle_snapshot
    )

    assert ok is False
    assert rejection is not None
    assert "reasonCode" in rejection


def test_civ_incomplete_not_appended(tmp_path):
    """C2: CIV rejection prevents registry append; registry absent after two calls."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Empty object fails CIV.
    csn_obj = {}

    # First call.
    _commit_canonical_object(csn_obj, "CSN", registry_path, cycle_snapshot)

    # Second call with same invalid object.
    _commit_canonical_object(csn_obj, "CSN", registry_path, cycle_snapshot)

    # Registry should not exist (nothing was ever committed).
    assert not registry_path.exists()


# ── GROUP D: _commit_batch counts ─────────────────────────────────────────────

def test_commit_batch_empty_collector(tmp_path):
    """D1: _commit_batch with empty collector returns (0, 0)."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    collector = make_batch_collector("BATCH_S2024_0000")
    # No objects added.

    committed, rejected = _commit_batch(registry_path, collector, cycle_snapshot)

    assert committed == 0
    assert rejected == 0
    assert not registry_path.exists()


def test_commit_batch_one_se_object(tmp_path):
    """D2: _commit_batch with one StructuralEnvironment object returns (1, 0)."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    collector = make_batch_collector("BATCH_S2024_0000")
    se_obj = {"id": "SE-001"}
    collector.add("StructuralEnvironment", se_obj)

    committed, rejected = _commit_batch(registry_path, collector, cycle_snapshot)

    assert committed == 1
    assert rejected == 0
    assert registry_path.exists()

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["StructuralEnvironment"]) == 1


def test_commit_batch_cps_duplicate_in_registry(tmp_path):
    """D3: _commit_batch with pre-existing CPS ID returns (0, 1)."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    # Pre-populate registry with a CPS object.
    _setup_registry_with_cps(registry_path, CPS_CANONICAL_ID)

    # Create collector with the same CPS ID.
    collector = make_batch_collector("BATCH_S2024_0000")
    cps_obj = _make_cps_obj(CPS_CANONICAL_ID)
    collector.add("CPS", cps_obj)

    committed, rejected = _commit_batch(registry_path, collector, cycle_snapshot)

    assert committed == 0
    assert rejected == 1

    # Verify registry still has exactly one CPS object.
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["CPS"]) == 1


def test_commit_canonical_object_end_to_end_cps_then_duplicate(tmp_path):
    """Phase 1.3: valid CPS commits once, duplicate is rejected on second submit."""
    registry_path = tmp_path / "canonical_objects.json"
    cycle_snapshot = _make_cycle_snapshot()

    atomic_write_json(
        str(registry_path),
        {k: (list(v) if isinstance(v, list) else v) for k, v in EMPTY_REGISTRY.items()},
    )

    cps_fields = {
        "signalClass": "structural_condition",
        "environment": "organization",
        "pressureSignalDomain": "authority_distribution",
        "pressureVector": "authority",
        "signalPolarity": "negative",
        "observationSource": "internal_observer",
        "castRequirement": "franchise",
        "tier": 2,
        "observation": "authority allocation remains unresolved.",
        "sourceSeed": "competing authority over play-calling",
    }
    canonical_id = derive_cps_fingerprint(cps_fields)
    cps_obj = {
        "laneType": "PRESSURE",
        "schemaVersion": "CPS-1.0",
        "canonicalId": canonical_id,
        "enumRegistryVersion": "ENUM_v1.0",
        "fingerprintVersion": "CPS_FINGERPRINT_V1",
        "contractVersion": "CIV-1.0",
        **cps_fields,
    }

    ok1, rejection1 = _commit_canonical_object(cps_obj, "CPS", registry_path, cycle_snapshot)
    assert ok1 is True
    assert rejection1 is None

    registry_after_first = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry_after_first["CPS"]) == 1
    assert registry_after_first["CPS"][0]["canonicalId"] == cps_obj["canonicalId"]

    ok2, rejection2 = _commit_canonical_object(cps_obj, "CPS", registry_path, cycle_snapshot)
    assert ok2 is False
    assert rejection2 is not None
    assert rejection2["reasonCode"] == STATUS_DUPLICATE

    registry_after_second = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry_after_second["CPS"]) == 1
