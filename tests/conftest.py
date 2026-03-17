import json
import pytest
from infra.orchestration.runtime.orchestrator import _commit_canonical_object
from engines.research_agent.agents.pressure.psta_schema import STATUS_DUPLICATE
from engines.research_engine.ledger.registry_writer import EMPTY_REGISTRY
from pathlib import Path


class Orchestrator:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path

    def _commit_canonical_object(self, obj, lane, cycle_snapshot, batch_id, collector):
        commit_obj = dict(obj)
        if "batchId" not in commit_obj:
            commit_obj["batchId"] = batch_id

        ok, rejection = _commit_canonical_object(
            obj=commit_obj,
            lane=lane,
            registry_path=self.registry_path,
            cycle_snapshot=cycle_snapshot,
        )

        if ok:
            return {"status": "accepted", "rejection": None}

        if isinstance(rejection, dict) and rejection.get("reasonCode") == STATUS_DUPLICATE:
            return {"status": "duplicate", "rejection": rejection}

        return {"status": "rejected", "rejection": rejection}


@pytest.fixture
def orchestrator(tmp_path):
    registry_path = tmp_path / "canonical_objects.json"
    registry_path.write_text(json.dumps(EMPTY_REGISTRY), encoding="utf-8")

    o = Orchestrator(registry_path=registry_path)

    if hasattr(o, "ledger_root"):
        o.ledger_root = tmp_path

    if hasattr(o, "active_run_path"):
        o.active_run_path = tmp_path

    return o
