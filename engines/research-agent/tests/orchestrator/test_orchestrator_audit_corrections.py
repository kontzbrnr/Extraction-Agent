"""
Phase 13.10 audit corrections — regression tests.

Covers:
    Item 3: Enum namespace collision — _build_cycle_snapshot raises KeyError
            on missing version fields (no silent substitution).
    Items 4 + 6: Replay determinism + hidden inference creep —
            ntiEvaluationSkipped surfaced in returned status dict.
"""

import pytest
from unittest.mock import MagicMock, patch

from infra.orchestration.runtime.orchestrator import _build_cycle_snapshot, orchestrator_run


# ── Group A: Enum namespace collision (_build_cycle_snapshot) ─────────────────

class TestBuildCycleSnapshotNoSilentFallback:

    def test_raises_on_missing_schema_version(self):
        gs = {"enumVersion": "ENUM_v1.0", "contractVersion": "CIV-1.0"}
        with pytest.raises(KeyError):
            _build_cycle_snapshot(gs)

    def test_raises_on_missing_enum_version(self):
        gs = {"schemaVersion": "CPS-1.0", "contractVersion": "CIV-1.0"}
        with pytest.raises(KeyError):
            _build_cycle_snapshot(gs)

    def test_raises_on_missing_contract_version(self):
        gs = {"schemaVersion": "CPS-1.0", "enumVersion": "ENUM_v1.0"}
        with pytest.raises(KeyError):
            _build_cycle_snapshot(gs)

    def test_raises_on_empty_global_state(self):
        with pytest.raises(KeyError):
            _build_cycle_snapshot({})

    def test_returns_exact_values_when_present(self):
        gs = {
            "schemaVersion":   "CPS-2.0",
            "enumVersion":     "ENUM_v3.1",
            "contractVersion": "CIV-2.0",
        }
        result = _build_cycle_snapshot(gs)
        assert result["schemaVersion"]   == "CPS-2.0"
        assert result["enumVersion"]     == "ENUM_v3.1"
        assert result["contractVersion"] == "CIV-2.0"

    def test_does_not_substitute_default_enum_version(self):
        """Confirm the old "ENUM_v1.0" fallback is gone."""
        gs = {"schemaVersion": "CPS-1.0", "contractVersion": "CIV-1.0"}
        # Would have returned "ENUM_v1.0" under the old silent-fallback code.
        with pytest.raises(KeyError):
            _build_cycle_snapshot(gs)


# ── Group B: ntiEvaluationSkipped — NTI state absent ─────────────────────────

class TestNTIEvaluationSkippedField:
    """When NTIStateReadError is raised, ntiEvaluationSkipped must be True."""

    def _make_ledger_state(self):
        gs = {
            "activeRunPath":   "runs/S1",
            "schemaVersion":   "CPS-1.0",
            "enumVersion":     "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
        }
        ss = {
            "season":               "S1",
            "microBatchCount":      0,
            "terminationStatus":    "running",
            "incompleteBatchFlag":  False,
            "retryFailureCount":    0,
        }
        ls = MagicMock()
        ls.global_state = gs
        ls.season_state = ss
        return ls

    def test_nti_skipped_true_when_nti_state_absent(self):
        from infra.orchestration.nti.cycle_state_manager import NTIStateReadError
        ls = self._make_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector",
                   return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline"), \
             patch("infra.orchestration.runtime.orchestrator._end_of_batch_boundary"), \
             patch("infra.orchestration.runtime.orchestrator.evaluate_termination",
                   side_effect=NTIStateReadError("nti_state.json not found")), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state",
                   return_value=ls.season_state):
            result = orchestrator_run("/fake/ledger")
        assert result["ntiEvaluationSkipped"] is True

    def test_nti_skipped_false_when_nti_evaluation_succeeds(self):
        ls = self._make_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector",
                   return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline"), \
             patch("infra.orchestration.runtime.orchestrator._end_of_batch_boundary"), \
             patch("infra.orchestration.runtime.orchestrator.evaluate_termination"), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state",
                   return_value=ls.season_state):
            result = orchestrator_run("/fake/ledger")
        assert result["ntiEvaluationSkipped"] is False

    def test_nti_skipped_field_present_on_crash_recovery_early_exit(self):
        """Early exits (crash/retry) must also include the field (default False)."""
        gs = {
            "activeRunPath":   "runs/S1",
            "schemaVersion":   "CPS-1.0",
            "enumVersion":     "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
        }
        ss_initial = {
            "season":              "S1",
            "microBatchCount":     0,
            "terminationStatus":   "running",
            "incompleteBatchFlag": True,
            "retryFailureCount":   1,
        }
        ss_after = {
            "season":              "S1",
            "microBatchCount":     0,
            "terminationStatus":   "system_failure",
            "incompleteBatchFlag": False,
            "retryFailureCount":   2,
        }
        ls = MagicMock()
        ls.global_state = gs
        ls.season_state = ss_initial
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.handle_crash_recovery"), \
             patch("infra.orchestration.runtime.orchestrator.increment_retry_failure_count"), \
             patch("infra.orchestration.runtime.orchestrator.set_termination_status"), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state", return_value=ss_after):
            result = orchestrator_run("/fake/ledger")
        assert "ntiEvaluationSkipped" in result
        assert result["ntiEvaluationSkipped"] is False

    def test_nti_skipped_field_present_on_retry_envelope_early_exit(self):
        """Retry envelope early exit must also include the field (default False)."""
        ls = self._make_ledger_state()
        ss_after = dict(ls.season_state)
        ss_after["retryFailureCount"] = 2
        ss_after["terminationStatus"] = "system_failure"
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector",
                   return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline",
                   side_effect=[Exception("fail"), Exception("fail")]), \
             patch("infra.orchestration.runtime.orchestrator.increment_retry_failure_count"), \
             patch("infra.orchestration.runtime.orchestrator.set_termination_status"), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state", return_value=ss_after):
            result = orchestrator_run("/fake/ledger")
        assert "ntiEvaluationSkipped" in result
        assert result["ntiEvaluationSkipped"] is False


# ── Group C: ntiEvaluationSkipped does not suppress termination status ────────

class TestNTISkipDoesNotMaskTermination:
    """Skipping NTI must not alter terminationStatus — it must remain 'running'."""

    def _make_ledger_state(self):
        gs = {
            "activeRunPath":   "runs/S1",
            "schemaVersion":   "CPS-1.0",
            "enumVersion":     "ENUM_v1.0",
            "contractVersion": "CIV-1.0",
        }
        ss = {
            "season":               "S1",
            "microBatchCount":      1,
            "terminationStatus":    "running",
            "incompleteBatchFlag":  False,
            "retryFailureCount":    0,
        }
        ls = MagicMock()
        ls.global_state = gs
        ls.season_state = ss
        return ls

    def test_termination_status_running_when_nti_skipped(self):
        from infra.orchestration.nti.cycle_state_manager import NTIStateReadError
        ls = self._make_ledger_state()
        with patch("infra.orchestration.runtime.orchestrator.preflight_read", return_value=ls), \
             patch("infra.orchestration.runtime.orchestrator.mark_batch_start"), \
             patch("infra.orchestration.runtime.orchestrator.make_batch_collector",
                   return_value=MagicMock(sorted_lanes=lambda: {})), \
             patch("infra.orchestration.runtime.orchestrator._run_canonical_pipeline"), \
             patch("infra.orchestration.runtime.orchestrator._end_of_batch_boundary"), \
             patch("infra.orchestration.runtime.orchestrator.evaluate_termination",
                   side_effect=NTIStateReadError("absent")), \
             patch("infra.orchestration.runtime.orchestrator.read_season_state",
                   return_value=ls.season_state):
            result = orchestrator_run("/fake/ledger")
        assert result["terminationStatus"] == "running"
        assert result["ntiEvaluationSkipped"] is True
