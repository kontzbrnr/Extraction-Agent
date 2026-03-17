from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_result import AgentResult


class NarrativeAgentAdapter(AgentInterface):
    def run(self, packet) -> AgentResult:
        from engines.research_agent.agents.ncg.narrative_pipeline_gate import _run_narrative_pipeline_impl

        payload = packet.payload
        passed, rejections, audit = _run_narrative_pipeline_impl(payload["event"])
        return AgentResult(
            agent_name=packet.agent_name,
            run_id=packet.run_id,
            output={
                "passed": passed,
                "rejections": rejections,
                "audit": audit,
            },
            metadata=dict(packet.metadata),
        )
