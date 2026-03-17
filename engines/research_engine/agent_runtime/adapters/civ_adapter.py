from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_result import AgentResult


class CIVAgentAdapter(AgentInterface):
    def run(self, packet) -> AgentResult:
        from engines.research_agent.agents.civ.civ import enforce_civ

        payload = packet.payload
        passed, rejection, audit = enforce_civ(
            payload["obj"],
            payload["lane"],
            payload["cycle_snapshot"],
        )
        return AgentResult(
            agent_name=packet.agent_name,
            run_id=packet.run_id,
            output={
                "passed": passed,
                "rejection": rejection,
                "audit": audit,
            },
            metadata=dict(packet.metadata),
        )
