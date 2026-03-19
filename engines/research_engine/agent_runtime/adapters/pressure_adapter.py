from engines.research_engine.agent_runtime.agent_interface import AgentInterface
from engines.research_engine.agent_runtime.agent_result import AgentResult


class PressureAgentAdapter(AgentInterface):
    def run(self, packet) -> AgentResult:
        payload = packet.payload

        if packet.stage == "cps_dedup":
            from engines.research_agent.agents.pressure.cps_dedup import detect_cps_duplicate

            status, existing_obj = detect_cps_duplicate(
                payload["canonical_id"],
                payload["registry_path"],
            )
            return AgentResult(
                agent_name=packet.agent_name,
                run_id=packet.run_id,
                output={
                    "status": status,
                    "existing_obj": existing_obj,
                },
                metadata=dict(packet.metadata),
            )

        from engines.research_agent.agents.pressure.pressure_pipeline_gate import _run_pressure_pipeline_impl

        passed_psars, all_rejections, composite_audit = _run_pressure_pipeline_impl(
            payload["plo"],
            payload["cycle_metadata"],
        )
        return AgentResult(
            agent_name=packet.agent_name,
            run_id=packet.run_id,
            output={
                "passed_psars": passed_psars,
                "all_rejections": all_rejections,
                "composite_audit": composite_audit,
            },
            metadata=dict(packet.metadata),
        )
