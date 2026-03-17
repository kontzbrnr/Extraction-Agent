"""
Phase A Step 6 — Invocation logging tests.

Verifies:
    - compute_ledger_state_hash returns sha256: prefixed hex string
    - compute_ledger_state_hash reads bytes only, not parsed JSON
    - write_invocation_log appends JSONL entries
    - make_success_entry and make_failure_entry produce correct structure
    - run_research_agent writes log on success
    - run_research_agent writes log on orchestrator failure
    - log write failure does not suppress orchestrator result
    - batchId present in orchestrator result dict
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.orchestration.openclaw.invocation_logger import (
    LOG_FILENAME,
    compute_ledger_state_hash,
    make_failure_entry,
    make_success_entry,
    write_invocation_log,
)
from infra.orchestration.openclaw.entrypoint import run_research_agent


# ── Group A: compute_ledger_state_hash ────────────────────────────────────────

class TestComputeLedgerStateHash:

    def test_returns_sha256_prefixed_string(self, tmp_path):
        (tmp_path / "global_state.json").write_text('{"key": "value"}')
        result = compute_ledger_state_hash(str(tmp_path))
        assert result.startswith("sha256:")
        assert len(result) == len("sha256:") + 64

    def test_identical_content_produces_identical_hash(self, tmp_path):
        content = '{"schemaVersion": "GLOBAL_STATE-1.0"}'
        (tmp_path / "global_state.json").write_text(content)
        h1 = compute_ledger_state_hash(str(tmp_path))
        h2 = compute_ledger_state_hash(str(tmp_path))
        assert h1 == h2

    def test_different_content_produces_different_hash(self, tmp_path):
        (tmp_path / "global_state.json").write_text('{"a": 1}')
        h1 = compute_ledger_state_hash(str(tmp_path))
        (tmp_path / "global_state.json").write_text('{"a": 2}')
        h2 = compute_ledger_state_hash(str(tmp_path))
        assert h1 != h2

    def test_reads_bytes_not_parsed_json(self, tmp_path):
        """Invalid JSON must not cause an error — bytes only."""
        (tmp_path / "global_state.json").write_bytes(b"NOT VALID JSON {{{{")
        result = compute_ledger_state_hash(str(tmp_path))
        assert result.startswith("sha256:")

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(OSError):
            compute_ledger_state_hash(str(tmp_path))


# ── Group B: write_invocation_log ─────────────────────────────────────────────

class TestWriteInvocationLog:

    def test_creates_log_file_if_absent(self, tmp_path):
        entry = {"timestamp": "2024-01-01T00:00:00Z", "action": "new_batch"}
        write_invocation_log(str(tmp_path), entry)
        assert (tmp_path / LOG_FILENAME).exists()

    def test_appends_valid_json_line(self, tmp_path):
        entry = {"timestamp": "2024-01-01T00:00:00Z", "action": "new_batch"}
        write_invocation_log(str(tmp_path), entry)
        lines = (tmp_path / LOG_FILENAME).read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["action"] == "new_batch"

    def test_appends_multiple_entries(self, tmp_path):
        for i in range(3):
            write_invocation_log(str(tmp_path), {"i": i})
        lines = (tmp_path / LOG_FILENAME).read_text().strip().splitlines()
        assert len(lines) == 3

    def test_each_line_is_independent_json_object(self, tmp_path):
        write_invocation_log(str(tmp_path), {"a": 1})
        write_invocation_log(str(tmp_path), {"b": 2})
        lines = (tmp_path / LOG_FILENAME).read_text().strip().splitlines()
        assert json.loads(lines[0]) == {"a": 1}
        assert json.loads(lines[1]) == {"b": 2}


# ── Group C: make_success_entry / make_failure_entry ─────────────────────────

class TestLogEntryBuilders:

    def test_success_entry_required_keys(self):
        summary = {
            "action": "new_batch",
            "batchId": "BATCH_S1_0001",
            "terminationStatus": "running",
            "microBatchCount": 1,
            "canonicalizedCount": 2,
            "rejectedCount": 0,
            "ntiEvaluationSkipped": False,
        }
        entry = make_success_entry("2024-01-01T00:00:00Z", "sha256:abc", summary)
        assert entry["timestamp"] == "2024-01-01T00:00:00Z"
        assert entry["ledgerStateHash"] == "sha256:abc"
        assert entry["actionSelected"] == "new_batch"
        assert entry["batchId"] == "BATCH_S1_0001"
        assert entry["invocationSuccess"] is True
        assert entry["errorCode"] is None
        assert "resultSummary" in entry

    def test_success_entry_halted_action_marks_not_success(self):
        summary = {"action": "halted", "reasonCode": "TERMINATION_BLOCKED"}
        entry = make_success_entry("2024-01-01T00:00:00Z", "sha256:abc", summary)
        assert entry["invocationSuccess"] is False
        assert entry["errorCode"] == "TERMINATION_BLOCKED"

    def test_failure_entry_required_keys(self):
        exc = RuntimeError("ledger read failure")
        entry = make_failure_entry("2024-01-01T00:00:00Z", "sha256:abc", exc)
        assert entry["timestamp"] == "2024-01-01T00:00:00Z"
        assert entry["ledgerStateHash"] == "sha256:abc"
        assert entry["invocationSuccess"] is False
        assert entry["errorCode"] == "RuntimeError"
        assert entry["actionSelected"] is None
        assert entry["batchId"] is None
        assert entry["resultSummary"] is None


# ── Group D: run_research_agent integration ───────────────────────────────────

class TestRunResearchAgentLogging:

    def _make_ledger(self, tmp_path) -> str:
        (tmp_path / "global_state.json").write_text(
            '{"schemaVersion":"GLOBAL_STATE-1.0"}'
        )
        return str(tmp_path)

    def test_log_written_on_success(self, tmp_path):
        ledger = self._make_ledger(tmp_path)
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                   return_value={"action": "new_batch", "batchId": "BATCH_S1_0001",
                                 "terminationStatus": "running", "microBatchCount": 1,
                                 "canonicalizedCount": 0, "rejectedCount": 0,
                                 "ntiEvaluationSkipped": False}):
            run_research_agent(ledger_root=ledger, env_path="/env")
        log_path = tmp_path / LOG_FILENAME
        assert log_path.exists()
        entry = json.loads(log_path.read_text().strip())
        assert entry["actionSelected"] == "new_batch"
        assert entry["invocationSuccess"] is True

    def test_log_written_on_orchestrator_failure(self, tmp_path):
        ledger = self._make_ledger(tmp_path)
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                   side_effect=RuntimeError("pipeline crash")):
            with pytest.raises(RuntimeError):
                run_research_agent(ledger_root=ledger, env_path="/env")
        log_path = tmp_path / LOG_FILENAME
        assert log_path.exists()
        entry = json.loads(log_path.read_text().strip())
        assert entry["invocationSuccess"] is False
        assert entry["errorCode"] == "RuntimeError"

    def test_orchestrator_exception_re_raised_after_log(self, tmp_path):
        ledger = self._make_ledger(tmp_path)
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                   side_effect=ValueError("bad state")):
            with pytest.raises(ValueError, match="bad state"):
                run_research_agent(ledger_root=ledger, env_path="/env")

    def test_log_write_failure_does_not_suppress_result(self, tmp_path):
        ledger = self._make_ledger(tmp_path)
        result_dict = {"action": "new_batch", "batchId": None,
                       "terminationStatus": "running", "microBatchCount": 0,
                       "canonicalizedCount": 0, "rejectedCount": 0,
                       "ntiEvaluationSkipped": False}
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run", return_value=result_dict), \
             patch("infra.orchestration.openclaw.entrypoint.write_invocation_log",
                   side_effect=OSError("disk full")):
            result = run_research_agent(ledger_root=ledger, env_path="/env")
        assert result["action"] == "new_batch"
        assert "logWriteError" in result

    def test_batch_id_in_orchestrator_result(self, tmp_path):
        """batchId must be present in orchestrator result dict."""
        ledger = self._make_ledger(tmp_path)
        result_dict = {"action": "new_batch", "batchId": "BATCH_S1_0002",
                       "terminationStatus": "running", "microBatchCount": 2,
                       "canonicalizedCount": 0, "rejectedCount": 0,
                       "ntiEvaluationSkipped": False}
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run", return_value=result_dict):
            result = run_research_agent(ledger_root=ledger, env_path="/env")
        assert result["batchId"] == "BATCH_S1_0002"
