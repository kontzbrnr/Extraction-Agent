from engines.research_engine.agent_runtime.agent_registry import (
    AGENT_REGISTRY,
    register_agent,
    register_default_agents,
)


class _TempAgent:
    def run(self, packet):
        return packet


def test_registry_completeness_and_duplicate_guard():
    original_registry = dict(AGENT_REGISTRY)
    AGENT_REGISTRY.clear()
    try:
        register_default_agents()
        expected = {"extraction", "classification", "narrative", "pressure", "emi", "civ"}
        assert expected.issubset(set(AGENT_REGISTRY.keys()))

        try:
            register_agent("civ", _TempAgent())
            assert False, "duplicate registration should raise ValueError"
        except ValueError:
            pass
    finally:
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(original_registry)
