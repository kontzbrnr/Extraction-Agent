from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_packet import AgentRunPacket
from engines.research_engine.agent_runtime.agent_registry import (
    AGENT_REGISTRY,
    get_agent,
    register_agent,
)
from engines.research_engine.agent_runtime.agent_result import AgentResult


class DummyAgent(AgentInterface):
    def run(self, packet: AgentRunPacket) -> AgentResult:
        packet.validate()
        return AgentResult(
            agent_name=packet.agent_name,
            run_id=packet.run_id,
            output={"ok": True},
            metadata={"source": "dummy"},
        )


def test_agent_interface_flow():
    packet = AgentRunPacket(
        run_id="run-001",
        stage="stage-5b",
        agent_name="dummy_agent",
        payload={"x": 1},
        metadata={"m": "v"},
    )

    packet.validate()

    register_agent("dummy_agent", DummyAgent())
    try:
        agent = get_agent("dummy_agent")
        result = agent.run(packet)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "dummy_agent"
        assert result.run_id == "run-001"
        assert result.output["ok"] is True
    finally:
        AGENT_REGISTRY.pop("dummy_agent", None)
