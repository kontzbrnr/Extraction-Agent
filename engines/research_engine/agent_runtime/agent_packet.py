from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AgentRunPacket:
    run_id: str
    stage: str
    agent_name: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]

    def validate(self):
        import json

        json.dumps(self.payload)
        json.dumps(self.metadata)
