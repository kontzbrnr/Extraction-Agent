"""
Phase 4.1 — AtomicityEnforcer skeleton tests.
Validates interface contract before full implementation.
"""

import pytest
from gsd.atomicity_enforcer import AtomicityEnforcer


def test_instantiation_succeeds():
    """AtomicityEnforcer can be instantiated."""
    enforcer = AtomicityEnforcer()
    assert enforcer is not None


def test_init_stores_no_state():
    """AtomicityEnforcer.__init__ stores no instance state."""
    enforcer = AtomicityEnforcer()
    assert vars(enforcer) == {}


def test_enforce_raises_not_implemented():
    """enforce() raises NotImplementedError with empty input."""
    enforcer = AtomicityEnforcer()
    with pytest.raises(NotImplementedError):
        enforcer.enforce([], "cluster:week1:doc1")


def test_enforce_raises_with_recs():
    """enforce() raises NotImplementedError even with valid REC input."""
    enforcer = AtomicityEnforcer()
    rec = {
        "id": "REC_" + "a" * 64,
        "text": "Head coach announced a quarterback change.",
        "isComposite": False,
        "schemaVersion": "REC-1.0",
    }
    with pytest.raises(NotImplementedError):
        enforcer.enforce([rec], "cluster:week1:doc1")


def test_enforce_not_implemented_message_contains_phase_4():
    """NotImplementedError message references Phase 4."""
    enforcer = AtomicityEnforcer()
    try:
        enforcer.enforce([], "ref")
    except NotImplementedError as e:
        assert "Phase 4" in str(e)


def test_enforce_signature_accepts_recs_and_source_reference():
    """Verify the method accepts the expected parameter names."""
    import inspect
    sig = inspect.signature(AtomicityEnforcer.enforce)
    params = list(sig.parameters.keys())
    assert "recs" in params
    assert "source_reference" in params
