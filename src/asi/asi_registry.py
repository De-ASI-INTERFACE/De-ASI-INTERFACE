"""ASI Ecosystem Registry.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ASIRegistry:
    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}

    def register(self, agent_id: str, capabilities: List[str],
                 metadata: Optional[Dict] = None) -> bool:
        self._agents[agent_id] = {
            "capabilities": capabilities,
            "metadata": metadata or {},
            "active": True,
        }
        return True

    def deregister(self, agent_id: str) -> bool:
        if agent_id not in self._agents:
            return False
        del self._agents[agent_id]
        return True

    def lookup(self, capability: str) -> List[str]:
        return [aid for aid, d in self._agents.items()
                if capability in d["capabilities"] and d["active"]]

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def list_all(self) -> List[str]:
        return list(self._agents.keys())

    def count(self) -> int:
        return len(self._agents)

    def health_check(self) -> bool:
        return isinstance(self._agents, dict)
