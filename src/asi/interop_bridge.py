"""ASI Interoperability Bridge.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


class InteropBridge:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._log: List[Dict[str, Any]] = []

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, message: Dict[str, Any]) -> int:
        handlers = self._handlers.get(topic, [])
        self._log.append({"topic": topic, "message": message,
                           "delivered_to": len(handlers)})
        for h in handlers:
            try:
                h(message)
            except Exception as exc:
                logger.error("Handler error on topic %s: %s", topic, exc)
        return len(handlers)

    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._log)

    def clear_log(self) -> None:
        self._log.clear()

    def health_check(self) -> bool:
        return isinstance(self._handlers, dict)
