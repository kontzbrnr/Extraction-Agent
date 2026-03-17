from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_result import AgentResult


class ExtractionAgentAdapter(AgentInterface):
    def run(self, packet) -> AgentResult:
        from engines.research_agent.agents.extraction.iav_pipeline_gate import enforce_iav

        payload = packet.payload
        passed, rejection, audit = enforce_iav(
            payload["au"],
            payload["source_reference"],
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
