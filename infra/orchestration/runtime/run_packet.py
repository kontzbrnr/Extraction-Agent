from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class RunPacket:
    run_id: str
    stage: str
    agent_name: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "stage": self.stage,
            "agent_name": self.agent_name,
            "payload": self.payload,
            "metadata": self.metadata,
            "context": self.context,
        }

    @staticmethod
    def from_dict(data):
        return RunPacket(
            run_id=data["run_id"],
            stage=data["stage"],
            agent_name=data["agent_name"],
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            context=data.get("context", {}),
        )
