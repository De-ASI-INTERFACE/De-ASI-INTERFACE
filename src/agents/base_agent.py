"""Base AI Agent Execution Adapter.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all De-ASI execution adapters."""

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self._running = False
        logger.info("Agent %s initialized.", self.agent_id)

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def __repr__(self):
        return f"<BaseAgent id={self.agent_id} running={self._running}>"
