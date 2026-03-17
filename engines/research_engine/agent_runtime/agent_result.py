from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AgentResult:
    agent_name: str
    run_id: str
    output: Dict[str, Any]
    metadata: Dict[str, Any]
