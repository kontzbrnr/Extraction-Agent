"""
Phase 13.9 — Single-Action-Per-Invocation Guard
Tests that orchestrator_run validates the derived action against _VALID_ACTIONS
before proceeding to cycle_snapshot construction or mark_batch_start.
"""

import pytest
from unittest.mock import MagicMock, patch

from infra.orchestration.runtime.orchestrator import _VALID_ACTIONS, orchestrator_run


# ── Group A: "new_batch" passes guard ─────────────────────────────────────────

class TestNewBatchPassesGuard:
    """new_batch is in _VALID_ACTIONS — guard must not block it."""

    def _make_ledger_state(self, tmp_path):
        """Return a minimal LedgerState-like mock for a clean new_batch run."""
        gs = {"activeRunPath": "runs/S1", "schemaVersion": "CPS-1.0",
              "enumVersion": "ENUM_v1.0", "contractVersion": "CIV-1.0"}
        ss = {"season": "S1", "microBatchCount": 0, "terminationStatus": "running",
              "incompleteBatchFlag": False, "retryFailureCount": 0}
        ls = MagicMock()
        ls.global_state = gs
        ls.season_state = ss
        return ls

    def test_new_batch_not_halted(self, tmp_path):
        ledger_state = self._make_ledger_state(tmp_path)
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ledger_state), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector", return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline"), \
             patch("infra.orchestration.runtime.orchestrator._end_of_batch_boundary"), \
             patch("infra.orchestration.runtime.orchestrator._evaluate_termination"), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state", return_value=ledger_state.season_state):
            result = orchestrator_run("/fake/ledger")
        assert result["action"] == "new_batch"
        assert result.get("reasonCode") is None

    def test_new_batch_build_cycle_snapshot_called(self, tmp_path):
        ledger_state = self._make_ledger_state(tmp_path)
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ledger_state), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector", return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline"), \
             patch("infra.orchestration.runtime.orchestrator._end_of_batch_boundary"), \
             patch("infra.orchestration.runtime.orchestrator._evaluate_termination"), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state", return_value=ledger_state.season_state), \
             patch("infra.orchestration.runtime.orchestrator._build_cycle_snapshot",
                   wraps=lambda gs: {"schemaVersion": "CPS-1.0", "enumVersion": "ENUM_v1.0",
                                     "contractVersion": "CIV-1.0"}) as mock_bcs:
            orchestrator_run("/fake/ledger")
        mock_bcs.assert_called_once()


# ── Group B: "crash_recovery" passes guard ───────────────────────────────────

class TestCrashRecoveryPassesGuard:
    """crash_recovery is in _VALID_ACTIONS — guard must not block it."""

    def _make_crash_ledger_state(self):
        gs = {"activeRunPath": "runs/S1", "schemaVersion": "CPS-1.0",
              "enumVersion": "ENUM_v1.0", "contractVersion": "CIV-1.0"}
        ss_initial = {"season": "S1", "microBatchCount": 0, "terminationStatus": "running",
                      "incompleteBatchFlag": True, "retryFailureCount": 0}
        ss_after = {"season": "S1", "microBatchCount": 0, "terminationStatus": "running",
                    "incompleteBatchFlag": False, "retryFailureCount": 1}
        ls = MagicMock()
        ls.global_state = gs
        ls.season_state = ss_initial
        return ls, ss_after

    def test_crash_recovery_not_halted(self):
        ls, ss_after = self._make_crash_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.handle_crash_recovery"), \
             patch("infra.orchestration.runtime.orchestrator.increment_retry_failure_count"), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state", return_value=ss_after), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector", return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline"), \
             patch("infra.orchestration.runtime.orchestrator._end_of_batch_boundary"), \
             patch("infra.orchestration.runtime.orchestrator._evaluate_termination"):
            result = orchestrator_run("/fake/ledger")
        assert result["action"] == "crash_recovery"
        assert result.get("reasonCode") is None


# ── Group C: Unrecognized action triggers guard ───────────────────────────────

class TestInvalidActionTriggersGuard:
    """An unrecognized action value must return halted without side effects."""

    def _make_new_batch_ledger_state(self):
        gs = {"activeRunPath": "runs/S1", "schemaVersion": "CPS-1.0",
              "enumVersion": "ENUM_v1.0", "contractVersion": "CIV-1.0"}
        ss = {"season": "S1", "microBatchCount": 0, "terminationStatus": "running",
              "incompleteBatchFlag": False, "retryFailureCount": 0}
        ls = MagicMock()
        ls.global_state = gs
        ls.season_state = ss
        return ls

    def test_invalid_action_returns_halted_status(self):
        """Monkey-patch action to an unrecognized token; guard must fire."""
        ls = self._make_new_batch_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start") as mock_mbs, \
             patch("infra.orchestration.runtime.orchestrator._build_cycle_snapshot") as mock_bcs:
            # Inject invalid action by patching the else-branch indirectly:
            # Override _VALID_ACTIONS to exclude "new_batch" for this test only.
            with patch("infra.orchestration.runtime.orchestrator._VALID_ACTIONS", frozenset()):
                result = orchestrator_run("/fake/ledger")
        assert result["action"] == "halted"
        assert result["terminationStatus"] == "blocked"
        assert result["reasonCode"] == "INVALID_ACTION"

    def test_invalid_action_does_not_call_build_cycle_snapshot(self):
        ls = self._make_new_batch_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator._build_cycle_snapshot") as mock_bcs, \
             patch("infra.orchestration.runtime.orchestrator._VALID_ACTIONS", frozenset()):
            orchestrator_run("/fake/ledger")
        mock_bcs.assert_not_called()

    def test_invalid_action_does_not_call_mark_batch_start(self):
        ls = self._make_new_batch_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start") as mock_mbs, \
             patch("infra.orchestration.runtime.orchestrator._VALID_ACTIONS", frozenset()):
            orchestrator_run("/fake/ledger")
        mock_mbs.assert_not_called()

    def test_invalid_action_canonical_count_zero(self):
        ls = self._make_new_batch_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator._VALID_ACTIONS", frozenset()):
            result = orchestrator_run("/fake/ledger")
        assert result["canonicalizedCount"] == 0
        assert result["rejectedCount"] == 0


# ── Group D: _VALID_ACTIONS constant integrity ────────────────────────────────

class TestValidActionsConstant:
    """_VALID_ACTIONS must contain exactly the documented tokens."""

    def test_valid_actions_is_frozenset(self):
        assert isinstance(_VALID_ACTIONS, frozenset)

    def test_valid_actions_contains_new_batch(self):
        assert "new_batch" in _VALID_ACTIONS

    def test_valid_actions_contains_crash_recovery(self):
        assert "crash_recovery" in _VALID_ACTIONS

    def test_valid_actions_cardinality(self):
        """Exactly two tokens — no undocumented entries."""
        assert len(_VALID_ACTIONS) == 2

    def test_halted_not_in_valid_actions(self):
        """'halted' is a preflight exit code, not a valid Step-2 action."""
        assert "halted" not in _VALID_ACTIONS
