"""
Phase A Step 5 — Ledger-first startup gate tests.

Verifies:
    - assert_ledger_reachable passes when ledger_root and
      global_state.json both exist
    - assert_ledger_reachable raises LedgerNotReachableError when
      ledger_root does not exist
    - assert_ledger_reachable raises LedgerNotReachableError when
      global_state.json is absent
    - assert_ledger_reachable does not read file contents
    - run_research_agent calls assert_ledger_reachable before
      orchestrator_run
    - LedgerNotReachableError propagates unswallowed
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from infra.orchestration.openclaw.ledger_gate import LedgerNotReachableError, assert_ledger_reachable
from infra.orchestration.openclaw.entrypoint import run_research_agent


# ── Group A: assert_ledger_reachable — path checks ───────────────────────────

class TestAssertLedgerReachable:

    def test_passes_when_dir_and_global_state_present(self, tmp_path):
        (tmp_path / "global_state.json").write_text("{}")
        assert_ledger_reachable(str(tmp_path))  # must not raise

    def test_raises_when_dir_does_not_exist(self, tmp_path):
        missing = str(tmp_path / "nonexistent")
        with pytest.raises(LedgerNotReachableError, match="not an existing directory"):
            assert_ledger_reachable(missing)

    def test_raises_when_path_is_a_file_not_dir(self, tmp_path):
        file_path = tmp_path / "not_a_dir.json"
        file_path.write_text("{}")
        with pytest.raises(LedgerNotReachableError):
            assert_ledger_reachable(str(file_path))

    def test_raises_when_global_state_absent(self, tmp_path):
        # Directory exists but global_state.json is missing.
        with pytest.raises(LedgerNotReachableError, match="global_state.json"):
            assert_ledger_reachable(str(tmp_path))

    def test_error_message_contains_ledger_root(self, tmp_path):
        missing = str(tmp_path / "bad_ledger")
        with pytest.raises(LedgerNotReachableError) as exc_info:
            assert_ledger_reachable(missing)
        assert missing in str(exc_info.value)

    def test_does_not_read_global_state_content(self, tmp_path):
        """gate must not open or parse global_state.json — existence only."""
        # Write intentionally invalid JSON — if the gate reads it, it would
        # either fail or silently accept garbage. It must not read at all.
        (tmp_path / "global_state.json").write_text("NOT VALID JSON {{{{")
        assert_ledger_reachable(str(tmp_path))  # must not raise

    def test_returns_none_on_success(self, tmp_path):
        (tmp_path / "global_state.json").write_text("{}")
        result = assert_ledger_reachable(str(tmp_path))
        assert result is None

    def test_ledger_not_reachable_error_is_runtime_error(self):
        assert issubclass(LedgerNotReachableError, RuntimeError)


# ── Group B: Ordering — gate fires before orchestrator_run ───────────────────

class TestLedgerGateOrdering:
    """assert_ledger_reachable must be called before orchestrator_run."""

    def test_unreachable_ledger_blocks_orchestrator_call(self, tmp_path):
        missing = str(tmp_path / "no_ledger")
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run") as mock_orch:
            with pytest.raises(LedgerNotReachableError):
                run_research_agent(
                    ledger_root=missing,
                    env_path="/env",
                    mode="deterministic",
                )
        mock_orch.assert_not_called()

    def test_missing_global_state_blocks_orchestrator_call(self, tmp_path):
        # tmp_path exists as dir but no global_state.json
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run") as mock_orch:
            with pytest.raises(LedgerNotReachableError):
                run_research_agent(
                    ledger_root=str(tmp_path),
                    env_path="/env",
                    mode="deterministic",
                )
        mock_orch.assert_not_called()

    def test_reachable_ledger_proceeds_to_orchestrator(self, tmp_path):
        (tmp_path / "global_state.json").write_text("{}")
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                   return_value={"action": "new_batch"}) as mock_orch:
            result = run_research_agent(
                ledger_root=str(tmp_path),
                env_path="/env",
                mode="deterministic",
            )
        mock_orch.assert_called_once_with(str(tmp_path))
        assert result["action"] == "new_batch"

    def test_param_validation_fires_before_ledger_gate(self):
        """Empty ledger_root raises ValueError (InvocationParams), not
        LedgerNotReachableError (ledger_gate). InvocationParams is first."""
        with pytest.raises(ValueError, match="ledger_root"):
            run_research_agent(
                ledger_root="",
                env_path="/env",
                mode="deterministic",
            )


# ── Group C: Error propagation ────────────────────────────────────────────────

class TestLedgerGateErrorPropagation:

    def test_ledger_not_reachable_error_propagates_unswallowed(self, tmp_path):
        missing = str(tmp_path / "absent")
        with pytest.raises(LedgerNotReachableError):
            run_research_agent(
                ledger_root=missing,
                env_path="/env",
                mode="deterministic",
            )

    def test_ledger_gate_error_distinct_from_value_error(self, tmp_path):
        missing = str(tmp_path / "absent")
        with pytest.raises(LedgerNotReachableError) as exc_info:
            run_research_agent(
                ledger_root=missing,
                env_path="/env",
                mode="deterministic",
            )
        assert not isinstance(exc_info.value, ValueError)
