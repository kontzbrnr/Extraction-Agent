"""
tests/openclaw/test_openclaw_real_invocation.py

Phase A Step 10 — One real micro-batch invocation.

Calls run_research_agent against a real filesystem-backed ledger with
_run_canonical_pipeline patched to inject one CIV-valid CPS object
into the collector. Verifies the full path:

    run_research_agent
      → acquire_run_lock
        → orchestrator_run
          → preflight_read
          → mark_batch_start
          → _run_canonical_pipeline (patched: adds one CPS object)
          → _commit_batch
            → detect_cps_duplicate (not a dup — fresh registry)
            → enforce_civ (CPS passes schema + enum checks)
            → append_canonical_object (writes to canonical_objects.json)
          → _end_of_batch_boundary (microBatchCount++, flag cleared)
          → _evaluate_termination (NTI absent → skipped)
      → write_invocation_log

Expected result:
    action              = "new_batch"
    canonicalizedCount  = 1
    rejectedCount       = 0
    canonical_objects.json["CPS"] contains exactly the injected object.

Groups:
    A — Return value assertions
    B — canonical_objects.json assertions
    C — Ledger state assertions
    D — Invocation log assertions
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION
from engines.research_engine.ledger.registry_writer import EMPTY_REGISTRY
from engines.research_engine.ledger.season_state_manager import create_season_run
from infra.orchestration.openclaw import run_research_agent
from engines.research_agent.agents.pressure.cps_fingerprint import derive_cps_fingerprint

# ── Constants ─────────────────────────────────────────────────────────────────

_SEASON   = "2024_REG"
_RUN_PATH = "runs/2024_REG"
_ENV_PATH = "/fake/env"

CPS_CANONICAL_ID = derive_cps_fingerprint({
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
})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_ledger(tmp_path: Path) -> None:
    """Write a minimal valid ledger to tmp_path."""
    atomic_write_json(
        str(tmp_path / "global_state.json"),
        {
            "schemaVersion":   GLOBAL_STATE_SCHEMA_VERSION,
            "enumVersion":     "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
            "activeSeason":    _SEASON,
            "activeRunPath":   _RUN_PATH,
            "systemStatus":    "operational",
        },
    )
    create_season_run(str(tmp_path), _SEASON, _RUN_PATH)
    atomic_write_json(
        str(tmp_path / _RUN_PATH / "canonical_objects.json"),
        {
            key: (list(value) if isinstance(value, list) else value)
            for key, value in EMPTY_REGISTRY.items()
        },
    )


def _make_cps_obj(
    canonical_id: str | None = None,
    source_seed: str = "competing authority over play-calling",
) -> dict:
    """Build a CIV-valid CPS object (same shape as test_orchestrator_commit.py)."""
    obj = {
        "laneType":             "PRESSURE",
        "schemaVersion":        "CPS-1.0",
        "signalClass":          "structural_condition",
        "environment":          "organization",
        "pressureSignalDomain": "authority_distribution",
        "pressureVector":       "authority",
        "signalPolarity":       "negative",
        "observationSource":    "internal_observer",
        "castRequirement":      "coach",
        "tier":                 2,
        "observation":          "authority allocation remains unresolved.",
        "sourceSeed":           source_seed,
        "enumRegistryVersion":  "ENUM_v1.0",
        "fingerprintVersion":   "CPS_FINGERPRINT_V1",
        "contractVersion":      "CIV-1.0",
    }
    obj["canonicalId"] = canonical_id or derive_cps_fingerprint(obj)
    return obj


def _pipeline_inject_one_cps(
    ledger_root,
    active_run_path,
    season,
    batch_id,
    cycle_snapshot,
    collector,
) -> None:
    """Replacement for _run_canonical_pipeline that injects one CPS object."""
    collector.add("CPS", _make_cps_obj())


# ── Group A — Return value assertions ─────────────────────────────────────────

class TestRealInvocationReturnValues:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def _run(self):
        with patch(
            "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
            side_effect=_pipeline_inject_one_cps,
        ):
            return run_research_agent(str(self.tmp_path), _ENV_PATH)

    def test_action_is_new_batch(self):
        """Real invocation returns action == 'new_batch'."""
        result = self._run()
        assert result["action"] == "new_batch"

    def test_canonicalized_count_is_one(self):
        """One CPS object injected → canonicalizedCount == 1."""
        result = self._run()
        assert result["canonicalizedCount"] == 1

    def test_rejected_count_is_zero(self):
        """CIV-valid object is not rejected."""
        result = self._run()
        assert result["rejectedCount"] == 0

    def test_micro_batch_count_is_one(self):
        """microBatchCount incremented to 1."""
        result = self._run()
        assert result["microBatchCount"] == 1

    def test_termination_status_running(self):
        """No termination triggered — terminationStatus remains 'running'."""
        result = self._run()
        assert result["terminationStatus"] == "running"

    def test_no_exception_raised(self):
        """Real invocation completes without raising."""
        self._run()  # must not raise


# ── Group B — canonical_objects.json assertions ───────────────────────────────

class TestRealInvocationRegistry:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def _run(self):
        with patch(
            "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
            side_effect=_pipeline_inject_one_cps,
        ):
            return run_research_agent(str(self.tmp_path), _ENV_PATH)

    def test_canonical_objects_json_created(self):
        """canonical_objects.json is created after the real invocation."""
        self._run()
        registry_path = self.tmp_path / _RUN_PATH / "canonical_objects.json"
        assert registry_path.exists()

    def test_cps_lane_has_one_entry(self):
        """CPS lane in registry contains exactly 1 object."""
        self._run()
        registry_path = self.tmp_path / _RUN_PATH / "canonical_objects.json"
        registry = json.loads(registry_path.read_text())
        assert len(registry["CPS"]) == 1

    def test_cps_object_identity(self):
        """Registry CPS entry is exactly the injected object (not mutated)."""
        self._run()
        registry_path = self.tmp_path / _RUN_PATH / "canonical_objects.json"
        registry = json.loads(registry_path.read_text())
        assert registry["CPS"][0] == _make_cps_obj()

    def test_other_lanes_remain_empty(self):
        """Non-CPS lanes in registry are empty lists."""
        self._run()
        registry_path = self.tmp_path / _RUN_PATH / "canonical_objects.json"
        registry = json.loads(registry_path.read_text())
        for lane in ("CME", "CSN", "StructuralEnvironment", "MediaContext"):
            assert registry[lane] == [], f"Lane {lane} should be empty"

    def test_second_invocation_with_new_id_appends(self):
        """Second invocation with a different canonicalId appends to registry."""
        second_obj = _make_cps_obj(source_seed="authority resolution remains contested")

        def _inject_second(*args, **kwargs):
            collector = kwargs.get("collector") if kwargs else None
            if collector is None:
                collector = args[5]
            collector.add("CPS", second_obj)

        with patch(
            "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
            side_effect=_pipeline_inject_one_cps,
        ):
            run_research_agent(str(self.tmp_path), _ENV_PATH)

        with patch(
            "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
            side_effect=_inject_second,
        ):
            run_research_agent(str(self.tmp_path), _ENV_PATH)

        registry_path = self.tmp_path / _RUN_PATH / "canonical_objects.json"
        registry = json.loads(registry_path.read_text())
        assert len(registry["CPS"]) == 2


# ── Group C — Ledger state assertions ─────────────────────────────────────────

class TestRealInvocationLedgerState:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def _run(self):
        with patch(
            "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
            side_effect=_pipeline_inject_one_cps,
        ):
            return run_research_agent(str(self.tmp_path), _ENV_PATH)

    def test_incomplete_flag_false_after_clean_commit(self):
        """incompleteBatchFlag is False after clean commit."""
        self._run()
        state_path = self.tmp_path / _RUN_PATH / "state.json"
        state = json.loads(state_path.read_text())
        assert state["incompleteBatchFlag"] is False

    def test_lock_file_cleaned_up(self):
        """Lock file does not persist after real invocation."""
        self._run()
        assert not (self.tmp_path / ".openclaw.lock").exists()


# ── Group D — Invocation log assertions ───────────────────────────────────────

class TestRealInvocationLog:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def _run(self):
        with patch(
            "infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
            side_effect=_pipeline_inject_one_cps,
        ):
            return run_research_agent(str(self.tmp_path), _ENV_PATH)

    def test_invocation_log_created(self):
        """Invocation log written after real invocation."""
        self._run()
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        assert log_path.exists()

    def test_invocation_log_entry_status_success(self):
        """Log entry status is 'success' for a clean invocation."""
        self._run()
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        entry = json.loads(log_path.read_text().strip())
        assert entry.get("status") == "success"       
