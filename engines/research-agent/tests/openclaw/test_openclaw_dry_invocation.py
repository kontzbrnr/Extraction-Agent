"""
tests/openclaw/test_openclaw_dry_invocation.py

Phase A Step 9 — Dry invocation handshake test.

Calls run_research_agent against a real filesystem-backed minimal
ledger fixture with no mocks. Verifies that the full
OpenClaw → orchestrator path completes cleanly on a zero-object
stub pipeline run.

Fixture state:
    global_state.json  — operational, activeRunPath = "runs/2024_REG"
    season_state.json  — terminationStatus="running",
                         incompleteBatchFlag=False, microBatchCount=0
    nti_state.json     — absent (NTIStateReadError expected → skipped)
    canonical_objects  — absent before run; must remain absent after

Expected result:
    action               = "new_batch"
    canonicalizedCount   = 0
    rejectedCount        = 0
    ntiEvaluationSkipped = True
    terminationStatus    = "running"
    microBatchCount      = 1

Groups:
    A — Return value assertions
    B — Filesystem state assertions
    C — No unauthorized writes
    D — Invocation log written
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engines.research_engine.ledger.atomic_write import atomic_write_json
from engines.research_engine.ledger.global_state_manager import GLOBAL_STATE_SCHEMA_VERSION
from engines.research_engine.ledger.season_state_manager import create_season_run
from infra.orchestration.openclaw import run_research_agent

# ── Constants ─────────────────────────────────────────────────────────────────

_SEASON   = "2024_REG"
_RUN_PATH = "runs/2024_REG"
_ENV_PATH = "/fake/env"   # InvocationParams requires non-empty; orchestrator never reads it


# ── Fixture ───────────────────────────────────────────────────────────────────

def _build_ledger(tmp_path: Path) -> None:
    """Write a minimal valid ledger to tmp_path.

    Produces:
        {tmp_path}/global_state.json
        {tmp_path}/runs/2024_REG/state.json

    Does NOT create:
        nti_state.json        (expected to be absent — NTI stub)
        canonical_objects.json (expected to be absent before run)
    """
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


# ── Group A — Return value assertions ─────────────────────────────────────────

class TestDryInvocationReturnValues:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def test_action_is_new_batch(self):
        """Dry invocation returns action == 'new_batch'."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert result["action"] == "new_batch"

    def test_canonicalized_count_is_zero(self):
        """Stub pipeline produces zero canonical objects."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert result["canonicalizedCount"] == 0

    def test_rejected_count_is_zero(self):
        """Stub pipeline produces zero rejections."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert result["rejectedCount"] == 0

    def test_nti_evaluation_skipped(self):
        """nti_state.json absent → NTIStateReadError caught → ntiEvaluationSkipped True."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert result["ntiEvaluationSkipped"] is True

    def test_termination_status_running(self):
        """No termination triggered — terminationStatus remains 'running'."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert result["terminationStatus"] == "running"

    def test_micro_batch_count_incremented(self):
        """microBatchCount is 1 after first invocation."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert result["microBatchCount"] == 1

    def test_orchestrator_version_present(self):
        """Result contains orchestratorVersion field."""
        result = run_research_agent(str(self.tmp_path), _ENV_PATH)
        assert "orchestratorVersion" in result
        assert result["orchestratorVersion"].startswith("ORCHESTRATOR-")

    def test_no_exception_raised(self):
        """Dry invocation completes without raising."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)  # must not raise


# ── Group B — Filesystem state assertions ─────────────────────────────────────

class TestDryInvocationFilesystemState:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def test_state_json_incomplete_flag_false(self):
        """state.json has incompleteBatchFlag==False after clean exit."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        state_path = self.tmp_path / _RUN_PATH / "state.json"
        state = json.loads(state_path.read_text())
        assert state["incompleteBatchFlag"] is False

    def test_state_json_micro_batch_count_one(self):
        """state.json has microBatchCount==1 after first invocation."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        state_path = self.tmp_path / _RUN_PATH / "state.json"
        state = json.loads(state_path.read_text())
        assert state["microBatchCount"] == 1

    def test_lock_file_cleaned_up(self):
        """Lock file .openclaw.lock does not persist after clean invocation."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        lock_path = self.tmp_path / ".openclaw.lock"
        assert not lock_path.exists()


# ── Group C — No unauthorized writes ──────────────────────────────────────────

class TestNoUnauthorizedWrites:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def test_canonical_objects_json_not_created(self):
        """canonical_objects.json is not created when pipeline produces no objects."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        canonical_path = self.tmp_path / _RUN_PATH / "canonical_objects.json"
        assert not canonical_path.exists()

    def test_only_expected_files_written(self):
        """Only state.json and invocation log are written; no surprise files."""
        before = set(self.tmp_path.rglob("*"))
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        after = set(self.tmp_path.rglob("*"))
        new_files = {p for p in (after - before) if p.is_file()}
        expected_new = {self.tmp_path / "openclaw_invocation_log.jsonl"}
        # Only the invocation log may be a net-new file.
        # state.json was modified in-place (not new).
        unexpected = new_files - expected_new
        assert unexpected == set(), f"Unexpected new files: {unexpected}"


# ── Group D — Invocation log written ──────────────────────────────────────────

class TestInvocationLogWritten:
    @pytest.fixture(autouse=True)
    def ledger(self, tmp_path):
        _build_ledger(tmp_path)
        self.tmp_path = tmp_path

    def test_invocation_log_created(self):
        """openclaw_invocation_log.jsonl is created after first invocation."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        assert log_path.exists()

    def test_invocation_log_has_one_entry(self):
        """Exactly one log entry is written per invocation."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        lines = [l for l in log_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1

    def test_invocation_log_entry_is_valid_json(self):
        """Log entry is valid JSON."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        line = log_path.read_text().strip()
        entry = json.loads(line)  # must not raise
        assert isinstance(entry, dict)

    def test_invocation_log_entry_has_timestamp(self):
        """Log entry contains a timestamp field."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        entry = json.loads(log_path.read_text().strip())
        assert "timestamp" in entry

    def test_invocation_log_entry_status_success(self):
        """Log entry marks invocation as successful."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        entry = json.loads(log_path.read_text().strip())
        assert entry.get("status") == "success"

    def test_second_invocation_appends_second_entry(self):
        """Second run appends to the log — does not overwrite."""
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        run_research_agent(str(self.tmp_path), _ENV_PATH)
        log_path = self.tmp_path / "openclaw_invocation_log.jsonl"
        lines = [l for l in log_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 2
