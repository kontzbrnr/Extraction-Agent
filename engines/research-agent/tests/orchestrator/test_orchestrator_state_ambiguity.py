"""
tests/orchestrator/test_orchestrator_state_ambiguity.py

Tests for Phase A Step 8 — hard fail on state ambiguity.

Verifies that orchestrator_run returns a deterministic halted status
when incompleteBatchFlag is neither True nor False, and that no
canonical writes occur on that path.

Groups:
    A — Ambiguous flag values halt without writing
    B — Valid flag values proceed normally
    C — Halted status dict structure
"""

from __future__ import annotations

import json
import os
from unittest.mock import patch, MagicMock

import pytest

from engines.research_engine.ledger.global_state_manager import LedgerState
from infra.orchestration.runtime.orchestrator import orchestrator_run

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_ledger_state(incomplete_flag):
    """Build a minimal LedgerState with the given incompleteBatchFlag value."""
    global_state = {
        "schemaVersion":   "GLOBAL_STATE-1.0",
        "systemStatus":    "operational",
        "activeRunPath":   "runs/2024_REG",
        "schemaVersion":   "GLOBAL_STATE-1.0",
        "enumVersion":     "ENUM-1.0",
        "contractVersion": "CONTRACT-1.0",
    }
    season_state = {
        "schemaVersion":       "SEASON_STATE-1.0",
        "season":              "2024_REG",
        "terminationStatus":   "running",
        "incompleteBatchFlag": incomplete_flag,
        "microBatchCount":     0,
        "retryFailureCount":   0,
    }
    return LedgerState(global_state=global_state, season_state=season_state)


# ── Group A — Ambiguous flag values halt without writing ──────────────────────

class TestAmbiguousFlagHalts:
    AMBIGUOUS_VALUES = [None, "true", "false", "True", "False", 0, 1, [], {}]

    @pytest.mark.parametrize("flag_value", AMBIGUOUS_VALUES)
    def test_ambiguous_flag_returns_halted_action(self, flag_value):
        """Any non-bool incompleteBatchFlag returns action == 'halted'."""
        ledger_state = _make_ledger_state(flag_value)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ):
            result = orchestrator_run("/fake/ledger")
        assert result["action"] == "halted"

    @pytest.mark.parametrize("flag_value", AMBIGUOUS_VALUES)
    def test_ambiguous_flag_returns_ambiguous_reason_code(self, flag_value):
        """Halted result has reasonCode == 'AMBIGUOUS_LEDGER_STATE'."""
        ledger_state = _make_ledger_state(flag_value)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ):
            result = orchestrator_run("/fake/ledger")
        assert result["reasonCode"] == "AMBIGUOUS_LEDGER_STATE"

    @pytest.mark.parametrize("flag_value", AMBIGUOUS_VALUES)
    def test_ambiguous_flag_does_not_call_mark_batch_start(self, flag_value):
        """mark_batch_start is never called on ambiguous state."""
        ledger_state = _make_ledger_state(flag_value)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ), patch(
            "infra.orchestration.runtime.orchestrator.mark_batch_start"
        ) as mock_mark:
            orchestrator_run("/fake/ledger")
        mock_mark.assert_not_called()

    @pytest.mark.parametrize("flag_value", AMBIGUOUS_VALUES)
    def test_ambiguous_flag_zero_canonical_count(self, flag_value):
        """Ambiguity halt reports canonicalizedCount == 0."""
        ledger_state = _make_ledger_state(flag_value)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ):
            result = orchestrator_run("/fake/ledger")
        assert result["canonicalizedCount"] == 0
        assert result["rejectedCount"] == 0


# ── Group B — Valid flag values proceed past ambiguity gate ──────────────────

class TestValidFlagProceeds:
    def test_false_flag_does_not_halt_at_ambiguity_gate(self):
        """incompleteBatchFlag == False proceeds to new_batch path."""
        ledger_state = _make_ledger_state(False)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ), patch(
            "infra.orchestration.runtime.orchestrator.mark_batch_start"
        ), patch(
            "infra.orchestration.runtime.orchestrator.make_batch_collector",
            return_value=MagicMock(sorted_lanes=lambda: {}),
        ), patch(
            "infra.orchestration.runtime.orchestrator.read_season_state",
            return_value=ledger_state.season_state,
        ), patch(
            "infra.orchestration.runtime.orchestrator._evaluate_termination",
            return_value=False,
        ), patch(
            "infra.orchestration.runtime.orchestrator._end_of_batch_boundary",
        ):
            result = orchestrator_run("/fake/ledger")
        # Must NOT be an ambiguity halt
        assert result.get("reasonCode") != "AMBIGUOUS_LEDGER_STATE"
        assert result["action"] == "new_batch"

    def test_true_flag_does_not_halt_at_ambiguity_gate(self):
        """incompleteBatchFlag == True proceeds to crash_recovery path."""
        ledger_state = _make_ledger_state(True)
        season_after_crash = {**ledger_state.season_state, "retryFailureCount": 0}
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ), patch(
            "infra.orchestration.runtime.orchestrator.handle_crash_recovery",
            return_value=MagicMock(),
        ), patch(
            "infra.orchestration.runtime.orchestrator.increment_retry_failure_count",
        ), patch(
            "infra.orchestration.runtime.orchestrator.read_season_state",
            return_value=season_after_crash,
        ), patch(
            "infra.orchestration.runtime.orchestrator.mark_batch_start",
        ), patch(
            "infra.orchestration.runtime.orchestrator.make_batch_collector",
            return_value=MagicMock(sorted_lanes=lambda: {}),
        ), patch(
            "infra.orchestration.runtime.orchestrator._evaluate_termination",
            return_value=False,
        ), patch(
            "infra.orchestration.runtime.orchestrator._end_of_batch_boundary",
        ):
            result = orchestrator_run("/fake/ledger")
        assert result.get("reasonCode") != "AMBIGUOUS_LEDGER_STATE"
        assert result["action"] == "crash_recovery"


# ── Group C — Halted status dict structure ────────────────────────────────────

class TestHaltedStatusStructure:
    def test_ambiguity_halt_has_required_keys(self):
        """Ambiguity halt result contains all required status dict keys."""
        ledger_state = _make_ledger_state(None)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ):
            result = orchestrator_run("/fake/ledger")
        required_keys = {
            "orchestratorVersion",
            "action",
            "terminationStatus",
            "reasonCode",
            "canonicalizedCount",
            "rejectedCount",
        }
        assert required_keys.issubset(result.keys())

    def test_ambiguity_halt_termination_status_blocked(self):
        """Ambiguity halt reports terminationStatus == 'blocked'."""
        ledger_state = _make_ledger_state(None)
        with patch(
            "infra.orchestration.runtime.orchestrator.preflight_read",
            return_value=ledger_state,
        ):
            result = orchestrator_run("/fake/ledger")
        assert result["terminationStatus"] == "blocked"
