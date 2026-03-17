from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_result import AgentResult


class EMIAgentAdapter(AgentInterface):
    def run(self, packet) -> AgentResult:
        from engines.research_agent.agents.emi.emi_agent import _run_emi_impl

        payload = packet.payload
        passed, rejection, nar = _run_emi_impl(payload["au"])
        return AgentResult(
            agent_name=packet.agent_name,
            run_id=packet.run_id,
            output={
                "passed": passed,
                "rejection": rejection,
                "nar": nar,
            },
            metadata=dict(packet.metadata),
        )
