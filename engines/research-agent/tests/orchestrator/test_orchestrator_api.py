from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from engines.research_agent.agents.pressure.cps_fingerprint import derive_cps_fingerprint
from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION
from engines.research_engine.ledger.registry_writer import EMPTY_REGISTRY
from engines.research_engine.ledger.season_state_manager import create_season_run
from infra.orchestration.runtime.api import RunRequest, app, run

SEASON = "2024_REG"
RUN_PATH = "runs/2024_REG"


def _build_ledger(tmp_path: Path) -> None:
    atomic_write_json(
        str(tmp_path / "global_state.json"),
        {
            "schemaVersion": GLOBAL_STATE_SCHEMA_VERSION,
            "enumVersion": "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
            "activeSeason": SEASON,
            "activeRunPath": RUN_PATH,
            "systemStatus": "operational",
        },
    )
    create_season_run(str(tmp_path), SEASON, RUN_PATH)
    atomic_write_json(
        str(tmp_path / RUN_PATH / "canonical_objects.json"),
        {k: (list(v) if isinstance(v, list) else v) for k, v in EMPTY_REGISTRY.items()},
    )


def _make_valid_cps() -> dict:
    cps_fields = {
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
        "canonicalId": derive_cps_fingerprint(cps_fields),
        "enumRegistryVersion": "ENUM_v1.0",
        "fingerprintVersion": "CPS_FINGERPRINT_V1",
        "contractVersion": "CIV-1.0",
        **cps_fields,
    }


def _inject_one_cps(
    ledger_root,
    active_run_path,
    season,
    batch_id,
    cycle_snapshot,
    collector,
) -> None:
    collector.add("CPS", _make_valid_cps())


def test_run_route_registered_for_post() -> None:
    route = next(r for r in app.routes if getattr(r, "path", None) == "/run")
    assert "POST" in route.methods


def test_run_bridge_commits_canonical_object(tmp_path: Path):
    _build_ledger(tmp_path)

    with patch(
        "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
        side_effect=_inject_one_cps,
    ):
        payload = run(RunRequest(ledgerRoot=str(tmp_path)))

    assert payload["action"] == "new_batch"
    assert payload["canonicalizedCount"] == 1

    registry_path = tmp_path / RUN_PATH / "canonical_objects.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry["CPS"]) == 1
