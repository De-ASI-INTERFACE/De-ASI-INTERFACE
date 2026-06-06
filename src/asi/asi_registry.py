"""ASI Ecosystem Registry.

Maintains a registry of active ASI agents, their capabilities,
and interoperability endpoints within the De-ASI ecosystem.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ASIRegistry:
    """Central registry for ASI agent discovery and capability lookup."""

    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        logger.info("ASIRegistry initialized.")

    def register(self, agent_id: str, capabilities: List[str], metadata: Optional[Dict] = None) -> bool:
        """Register an agent with its capabilities."""
        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} already registered. Overwriting.")
        self._agents[agent_id] = {
            "capabilities": capabilities,
            "metadata": metadata or {},
            "active": True,
        }
        logger.info(f"Registered agent: {agent_id} with capabilities: {capabilities}")
        return True

    def deregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id not in self._agents:
            return False
        del self._agents[agent_id]
        logger.info(f"Deregistered agent: {agent_id}")
        return True

    def lookup(self, capability: str) -> List[str]:
        """Return all agent IDs that support a given capability."""
        return [
            aid for aid, data in self._agents.items()
            if capability in data["capabilities"] and data["active"]
        ]

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Return full agent record."""
        return self._agents.get(agent_id)

    def list_all(self) -> List[str]:
        """Return all registered agent IDs."""
        return list(self._agents.keys())

    def count(self) -> int:
        return len(self._agents)

    def health_check(self) -> bool:
        return isinstance(self._agents, dict)
