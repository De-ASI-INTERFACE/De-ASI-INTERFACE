"""Base AI Agent Execution Adapter.

Provides the abstract interface all De-ASI agents must implement.
Designed for Solana-native agentic finance workflows.
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
        logger.info(f"Agent {self.agent_id} initialized.")

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic with a given payload. Must return result dict."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if agent is healthy and ready to execute."""

    def start(self):
        self._running = True
        logger.info(f"Agent {self.agent_id} started.")

    def stop(self):
        self._running = False
        logger.info(f"Agent {self.agent_id} stopped.")

    @property
    def is_running(self) -> bool:
        return self._running

    def __repr__(self):
        return f"<BaseAgent id={self.agent_id} running={self._running}>"
