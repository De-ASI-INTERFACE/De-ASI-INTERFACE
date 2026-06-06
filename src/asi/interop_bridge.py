"""ASI Interoperability Bridge.

Facilitates cross-agent message passing and payload routing
between De-ASI agents and external ASI ecosystem participants.
"""
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InteropBridge:
    """Routes messages between registered ASI agents."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._message_log: List[Dict[str, Any]] = []

    def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe a handler function to a message topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)
        logger.info(f"Handler subscribed to topic '{topic}'.")

    def publish(self, topic: str, message: Dict[str, Any]) -> int:
        """Publish a message to all subscribers of a topic. Returns handler count."""
        handlers = self._handlers.get(topic, [])
        entry = {"topic": topic, "message": message, "delivered_to": len(handlers)}
        self._message_log.append(entry)
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Handler error on topic '{topic}': {e}")
        logger.info(f"Published to '{topic}': {len(handlers)} handlers notified.")
        return len(handlers)

    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._message_log)

    def clear_log(self) -> None:
        self._message_log.clear()

    def health_check(self) -> bool:
        return isinstance(self._handlers, dict)
