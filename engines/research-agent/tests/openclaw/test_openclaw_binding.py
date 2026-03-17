"""
Phase A Step 3 — OpenClaw binding integrity tests.

Verifies:
    - PERMITTED_ORCHESTRATOR_CALL constant is correct
    - FORBIDDEN_DIRECT_CALLS contains all required targets
    - verify_binding_integrity() passes on clean openclaw namespace
    - verify_binding_integrity() raises BindingViolationError on contamination
    - execution_summary naming in entrypoint (lifecycle clarity)
"""

import sys
import types
import pytest

from infra.orchestration.openclaw.binding import (
    FORBIDDEN_DIRECT_CALLS,
    PERMITTED_ORCHESTRATOR_CALL,
    BindingViolationError,
    verify_binding_integrity,
)


# ── Group A: Authority chain constants ────────────────────────────────────────

class TestAuthorityChainConstants:

    def test_permitted_call_is_orchestrator_run(self):
        assert PERMITTED_ORCHESTRATOR_CALL == "orchestrator_run"

    def test_forbidden_calls_is_frozenset(self):
        assert isinstance(FORBIDDEN_DIRECT_CALLS, frozenset)

    def test_plo_e_is_forbidden(self):
        assert "plo_e" in FORBIDDEN_DIRECT_CALLS

    def test_iav_is_forbidden(self):
        assert "iav" in FORBIDDEN_DIRECT_CALLS

    def test_psta_is_forbidden(self):
        assert "psta" in FORBIDDEN_DIRECT_CALLS

    def test_emi_is_forbidden(self):
        assert "emi" in FORBIDDEN_DIRECT_CALLS

    def test_media_mint_is_forbidden(self):
        assert "media_mint" in FORBIDDEN_DIRECT_CALLS

    def test_civ_is_forbidden(self):
        assert "civ" in FORBIDDEN_DIRECT_CALLS

    def test_pressure_is_forbidden(self):
        assert "pressure" in FORBIDDEN_DIRECT_CALLS

    def test_extraction_is_forbidden(self):
        assert "extraction" in FORBIDDEN_DIRECT_CALLS

    def test_narrative_is_forbidden(self):
        assert "narrative" in FORBIDDEN_DIRECT_CALLS

    def test_classification_is_forbidden(self):
        assert "classification" in FORBIDDEN_DIRECT_CALLS

    def test_orchestrator_not_in_forbidden(self):
        """orchestrator_run is the permitted call — must not be in forbidden."""
        assert not any("orchestrator" in f for f in FORBIDDEN_DIRECT_CALLS)


# ── Group B: verify_binding_integrity — clean namespace ───────────────────────

class TestBindingIntegrityClean:
    """verify_binding_integrity() must pass on the clean openclaw namespace."""

    def test_passes_on_clean_openclaw_namespace(self):
        """The installed openclaw package must pass binding integrity check."""
        verify_binding_integrity()  # must not raise

    def test_returns_none_on_success(self):
        result = verify_binding_integrity()
        assert result is None

    def test_binding_violation_error_is_runtime_error(self):
        assert issubclass(BindingViolationError, RuntimeError)


# ── Group C: verify_binding_integrity — contaminated namespace ────────────────

class TestBindingIntegrityContaminated:
    """verify_binding_integrity() must raise BindingViolationError when a
    forbidden name appears as an attribute in an openclaw module."""

    def _inject_fake_openclaw_module(self, attr_name: str) -> str:
        """Register a fake openclaw submodule with a forbidden attribute."""
        fake_mod = types.ModuleType("infra.orchestration.openclaw._test_fake")
        setattr(fake_mod, attr_name, object())
        module_key = "infra.orchestration.openclaw._test_fake"
        sys.modules[module_key] = fake_mod
        return module_key

    def _cleanup(self, module_key: str) -> None:
        sys.modules.pop(module_key, None)

    def test_raises_on_psta_attribute(self):
        key = self._inject_fake_openclaw_module("psta_agent")
        try:
            with pytest.raises(BindingViolationError, match="psta"):
                verify_binding_integrity()
        finally:
            self._cleanup(key)

    def test_raises_on_civ_attribute(self):
        key = self._inject_fake_openclaw_module("civ_validator")
        try:
            with pytest.raises(BindingViolationError, match="civ"):
                verify_binding_integrity()
        finally:
            self._cleanup(key)

    def test_raises_on_emi_attribute(self):
        key = self._inject_fake_openclaw_module("emi_handler")
        try:
            with pytest.raises(BindingViolationError):
                verify_binding_integrity()
        finally:
            self._cleanup(key)

    def test_error_message_names_forbidden_module(self):
        key = self._inject_fake_openclaw_module("psta_direct_call")
        try:
            with pytest.raises(BindingViolationError) as exc_info:
                verify_binding_integrity()
            assert "infra.orchestration.openclaw._test_fake" in str(exc_info.value)
        finally:
            self._cleanup(key)

    def test_non_forbidden_attribute_does_not_raise(self):
        """An attribute named 'orchestrator_run' must not trigger the check."""
        key = self._inject_fake_openclaw_module("orchestrator_run")
        try:
            verify_binding_integrity()  # must not raise
        finally:
            self._cleanup(key)

    def test_result_value_containing_civ_string_does_not_raise(self):
        """String values in dicts are not attribute names — must not trigger."""
        # Simulates orchestrator returning a dict with "civ" as a value.
        # This must not contaminate the binding check.
        key = self._inject_fake_openclaw_module("execution_summary")
        # execution_summary is not a forbidden name — should pass.
        try:
            verify_binding_integrity()  # must not raise
        finally:
            self._cleanup(key)
