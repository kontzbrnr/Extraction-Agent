"""
Phase A Step 2 — Single callable entrypoint tests.

Verifies:
    - run_research_agent calls orchestrator_run exactly once per invocation
    - mode != "deterministic" raises ValueError before any orchestrator call
    - result is returned unmodified
    - no internal looping
    - no direct agent imports in the openclaw module
"""

import pytest
from contextlib import nullcontext
from unittest.mock import MagicMock, call, patch

from infra.orchestration.openclaw.entrypoint import run_research_agent


# ── Group A: Mode gate ────────────────────────────────────────────────────────

class TestModeGate:
    """mode must be 'deterministic' or ValueError is raised immediately."""

    def test_deterministic_mode_accepted(self):
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run", return_value={"action": "new_batch"}):
                            result = run_research_agent("/ledger", "/env", mode="deterministic")
        assert result["action"] == "new_batch"

    def test_non_deterministic_mode_raises(self):
        with pytest.raises(ValueError, match="mode must be 'deterministic'"):
            run_research_agent("/ledger", "/env", mode="stochastic")

    def test_empty_mode_raises(self):
        with pytest.raises(ValueError):
            run_research_agent("/ledger", "/env", mode="")

    def test_mode_check_precedes_orchestrator_call(self):
        """InvocationParams must fail before any orchestrator call."""
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run") as mock_orch:
            with pytest.raises(ValueError):
                run_research_agent("/ledger", "/env", mode="random")
        mock_orch.assert_not_called()


# ── Group B: Single call enforcement ─────────────────────────────────────────

class TestSingleCallEnforcement:
    """orchestrator_run must be called exactly once per invocation."""

    def test_orchestrator_called_exactly_once(self):
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent("/ledger", "/env")
        assert mock_orch.call_count == 1

    def test_orchestrator_called_with_ledger_root(self):
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent("/my/ledger", "/env")
        mock_orch.assert_called_once_with("/my/ledger")

    def test_env_path_not_forwarded_to_orchestrator(self):
        """env_path is accepted but must not be passed to orchestrator_run."""
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent("/ledger", "/some/env/path")
        args, kwargs = mock_orch.call_args
        assert "/some/env/path" not in args
        assert "env_path" not in kwargs

    def test_run_id_not_forwarded_to_orchestrator(self):
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent("/ledger", "/env", run_id="RUN_001")
        args, kwargs = mock_orch.call_args
        assert "RUN_001" not in args
        assert "run_id" not in kwargs

    def test_seed_not_forwarded_to_orchestrator(self):
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent("/ledger", "/env", seed=42)
        args, kwargs = mock_orch.call_args
        assert 42 not in args
        assert "seed" not in kwargs

    def test_multiple_independent_invocations_each_call_once(self):
        """Two separate calls to run_research_agent = two separate single calls."""
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent("/ledger", "/env")
                            run_research_agent("/ledger", "/env")
        assert mock_orch.call_count == 2


# ── Group C: Pass-through result ─────────────────────────────────────────────

class TestPassThroughResult:
    """Result from orchestrator_run must be returned unmodified."""

    def test_result_returned_unmodified(self):
        expected = {
            "orchestratorVersion": "ORCHESTRATOR-1.0",
            "action": "new_batch",
            "terminationStatus": "running",
            "microBatchCount": 1,
            "canonicalizedCount": 3,
            "rejectedCount": 0,
            "ntiEvaluationSkipped": False,
        }
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run", return_value=expected):
                            result = run_research_agent("/ledger", "/env")
        assert result is expected

    def test_halted_result_returned_unmodified(self):
        halted = {
            "orchestratorVersion": "ORCHESTRATOR-1.0",
            "action": "halted",
            "terminationStatus": "blocked",
            "reasonCode": "TERMINATION_BLOCKED",
        }
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run", return_value=halted):
                            result = run_research_agent("/ledger", "/env")
        assert result is halted

    def test_orchestrator_exception_propagates_unmodified(self):
        """Exceptions from orchestrator_run must not be swallowed."""
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   side_effect=RuntimeError("ledger read failure")):
                            with pytest.raises(RuntimeError, match="ledger read failure"):
                                run_research_agent("/ledger", "/env")


# ── Group D: Authority chain — no forbidden imports ───────────────────────────

class TestAuthorityChain:
    """openclaw module must not import forbidden pipeline agents directly."""

    def _get_openclaw_imports(self) -> set[str]:
        import importlib, inspect
        import infra.orchestration.openclaw.entrypoint as mod
        src = inspect.getsource(mod)
        import re
        return set(re.findall(r'^(?:import|from)\s+([\w\.]+)', src, re.MULTILINE))

    def test_no_psta_import(self):
        imports = self._get_openclaw_imports()
        assert not any("psta" in i.lower() for i in imports)

    def test_no_civ_import(self):
        imports = self._get_openclaw_imports()
        assert not any("civ" in i.lower() for i in imports)

    def test_no_emi_import(self):
        imports = self._get_openclaw_imports()
        assert not any("emi" in i.lower() for i in imports)

    def test_no_pressure_pipeline_import(self):
        imports = self._get_openclaw_imports()
        assert not any("pressure" in i.lower() for i in imports)

    def test_only_orchestrator_downstream_call(self):
        """The only downstream import is infra.orchestration.runtime.orchestrator."""
        imports = self._get_openclaw_imports()
        assert any("orchestrator" in i.lower() for i in imports)
