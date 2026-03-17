from abc import ABC, abstractmethod

from .agent_packet import AgentRunPacket
from .agent_result import AgentResult


class AgentInterface(ABC):
    @abstractmethod
    def run(self, packet: AgentRunPacket) -> AgentResult:
        pass
