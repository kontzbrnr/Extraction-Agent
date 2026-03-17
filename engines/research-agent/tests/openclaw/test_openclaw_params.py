"""
Phase A Step 4 — InvocationParams validation tests.

Verifies:
    - InvocationParams accepts valid minimum input surface
    - InvocationParams rejects empty ledger_root
    - InvocationParams rejects empty env_path
    - InvocationParams rejects non-deterministic mode
    - InvocationParams is frozen (immutable after construction)
    - run_research_agent delegates validation to InvocationParams
"""

import pytest
from contextlib import nullcontext
from unittest.mock import patch

from infra.orchestration.openclaw.params import InvocationParams
from infra.orchestration.openclaw.entrypoint import run_research_agent


# ── Group A: Valid construction ───────────────────────────────────────────────

class TestInvocationParamsValid:

    def test_minimal_valid_construction(self):
        params = InvocationParams(ledger_root="/ledger", env_path="/env")
        assert params.ledger_root == "/ledger"
        assert params.env_path    == "/env"
        assert params.mode        == "deterministic"
        assert params.run_id      is None
        assert params.seed        is None

    def test_all_fields_explicit(self):
        params = InvocationParams(
            ledger_root="/ledger",
            env_path="/env",
            mode="deterministic",
            run_id="RUN_001",
            seed=42,
        )
        assert params.run_id == "RUN_001"
        assert params.seed   == 42

    def test_frozen_immutable_ledger_root(self):
        params = InvocationParams(ledger_root="/ledger", env_path="/env")
        with pytest.raises((AttributeError, TypeError)):
            params.ledger_root = "/other"

    def test_frozen_immutable_mode(self):
        params = InvocationParams(ledger_root="/ledger", env_path="/env")
        with pytest.raises((AttributeError, TypeError)):
            params.mode = "stochastic"

    def test_exactly_five_fields(self):
        import dataclasses
        fields = {f.name for f in dataclasses.fields(InvocationParams)}
        # _PERMITTED_MODE is a field on the dataclass but is internal.
        public_fields = {f for f in fields if not f.startswith("_")}
        assert public_fields == {"ledger_root", "env_path", "mode", "run_id", "seed"}


# ── Group B: Validation failures ─────────────────────────────────────────────

class TestInvocationParamsValidation:

    def test_empty_ledger_root_raises(self):
        with pytest.raises(ValueError, match="ledger_root"):
            InvocationParams(ledger_root="", env_path="/env")

    def test_empty_env_path_raises(self):
        with pytest.raises(ValueError, match="env_path"):
            InvocationParams(ledger_root="/ledger", env_path="")

    def test_non_deterministic_mode_raises(self):
        with pytest.raises(ValueError, match="deterministic"):
            InvocationParams(ledger_root="/ledger", env_path="/env",
                             mode="stochastic")

    def test_empty_mode_raises(self):
        with pytest.raises(ValueError):
            InvocationParams(ledger_root="/ledger", env_path="/env", mode="")

    def test_none_ledger_root_raises(self):
        with pytest.raises((ValueError, TypeError)):
            InvocationParams(ledger_root=None, env_path="/env")

    def test_none_env_path_raises(self):
        with pytest.raises((ValueError, TypeError)):
            InvocationParams(ledger_root="/ledger", env_path=None)

    def test_validation_raises_before_orchestrator_call(self):
        """InvocationParams construction must fail before any downstream call."""
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run") as mock_orch:
            with pytest.raises(ValueError):
                run_research_agent(
                    ledger_root="",
                    env_path="/env",
                    mode="deterministic",
                )
        mock_orch.assert_not_called()


# ── Group C: Integration with run_research_agent ──────────────────────────────

class TestRunResearchAgentUsesParams:

    def test_valid_params_reaches_orchestrator(self):
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={"action": "new_batch"}) as mock_orch:
                            result = run_research_agent(
                                ledger_root="/ledger",
                                env_path="/env",
                                mode="deterministic",
                            )
        mock_orch.assert_called_once_with("/ledger")
        assert result["action"] == "new_batch"

    def test_orchestrator_called_with_validated_ledger_root(self):
        """params.ledger_root (not raw arg) is forwarded to orchestrator."""
        with patch("infra.orchestration.openclaw.entrypoint.assert_ledger_reachable", return_value=None):
            with patch("infra.orchestration.openclaw.entrypoint.acquire_run_lock", return_value=nullcontext()):
                with patch("infra.orchestration.openclaw.entrypoint.compute_ledger_state_hash", return_value="sha256:test"):
                    with patch("infra.orchestration.openclaw.entrypoint.write_invocation_log", return_value=None):
                        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run",
                                   return_value={}) as mock_orch:
                            run_research_agent(ledger_root="/my/ledger", env_path="/env")
        mock_orch.assert_called_once_with("/my/ledger")

    def test_empty_ledger_root_raises_before_orchestrator(self):
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run") as mock_orch:
            with pytest.raises(ValueError, match="ledger_root"):
                run_research_agent(ledger_root="", env_path="/env")
        mock_orch.assert_not_called()

    def test_invalid_mode_raises_before_orchestrator(self):
        with patch("infra.orchestration.openclaw.entrypoint.orchestrator_run") as mock_orch:
            with pytest.raises(ValueError, match="deterministic"):
                run_research_agent(
                    ledger_root="/ledger",
                    env_path="/env",
                    mode="random",
                )
        mock_orch.assert_not_called()
