AGENT_REGISTRY = {}


def register_agent(name, agent_callable):
    if name in AGENT_REGISTRY:
        raise ValueError(f"Agent already registered: {name}")
    AGENT_REGISTRY[name] = agent_callable


def get_agent(name):
    if name not in AGENT_REGISTRY:
        raise Exception(f"Unknown agent: {name}")
    return AGENT_REGISTRY[name]


def register_default_agents():
    from engines.research_engine.agent_runtime.adapters import (
        CIVAgentAdapter,
        ClassificationAgentAdapter,
        EMIAgentAdapter,
        ExtractionAgentAdapter,
        NarrativeAgentAdapter,
        PressureAgentAdapter,
    )

    if "extraction" not in AGENT_REGISTRY:
        register_agent("extraction", ExtractionAgentAdapter())
    if "classification" not in AGENT_REGISTRY:
        register_agent("classification", ClassificationAgentAdapter())
    if "narrative" not in AGENT_REGISTRY:
        register_agent("narrative", NarrativeAgentAdapter())
    if "pressure" not in AGENT_REGISTRY:
        register_agent("pressure", PressureAgentAdapter())
    if "emi" not in AGENT_REGISTRY:
        register_agent("emi", EMIAgentAdapter())
    if "civ" not in AGENT_REGISTRY:
        register_agent("civ", CIVAgentAdapter())
