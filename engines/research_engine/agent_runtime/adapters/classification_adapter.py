from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_result import AgentResult


class ClassificationAgentAdapter(AgentInterface):
    def run(self, packet) -> AgentResult:
        from engines.research_agent.agents.classification.routing_gate import enforce_routing_gate

        payload = packet.payload
        passed, seed_type, rejection, audit = enforce_routing_gate(
            payload["au"],
            payload["source_reference"],
        )
        return AgentResult(
            agent_name=packet.agent_name,
            run_id=packet.run_id,
            output={
                "passed": passed,
                "seed_type": seed_type,
                "rejection": rejection,
                "audit": audit,
            },
            metadata=dict(packet.metadata),
        )
