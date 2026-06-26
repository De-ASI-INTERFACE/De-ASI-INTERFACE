"""ASI Interoperability Bridge — fully async, concurrent, timeout-guarded.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_HANDLER_TIMEOUT_S: float = 2.0   # per-handler coroutine timeout
MAX_LOG_ENTRIES: int = 10_000            # ring-buffer cap on in-memory log


class InteropBridge:
    """
    Pub/sub bridge between ASI agents and the Solana validator pipeline.

    Key properties:
      - publish() is fully async; all handlers are awaited concurrently
        via asyncio.gather with individual per-handler timeouts.
      - Sync handlers (plain callables) are wrapped in
        asyncio.get_event_loop().run_in_executor so they never block the
        event loop.
      - Log is capped at MAX_LOG_ENTRIES (ring-buffer eviction of oldest).
      - sync_publish() is provided as a fire-and-forget shim for callers
        that cannot be made async (e.g. legacy InteropBridge.publish() call
        sites); it schedules publish() as a task and returns immediately.
    """

    def __init__(
        self,
        handler_timeout: float = DEFAULT_HANDLER_TIMEOUT_S,
    ) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._log: List[Dict[str, Any]] = []
        self._handler_timeout = handler_timeout
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, topic: str, handler: Callable) -> None:
        """Register a handler for *topic*. Handler may be sync or async."""
        self._handlers.setdefault(topic, []).append(handler)
        logger.debug("InteropBridge: subscribed handler to topic={!r}", topic)

    def unsubscribe(self, topic: str, handler: Callable) -> bool:
        """Remove a specific handler from *topic*. Returns True if found."""
        handlers = self._handlers.get(topic, [])
        try:
            handlers.remove(handler)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> int:
        """
        Dispatch *message* to all handlers subscribed to *topic*.

        All handlers are launched concurrently with asyncio.gather.
        Each handler is individually wrapped in asyncio.wait_for with
        *timeout* (default: self._handler_timeout).

        Returns the number of handlers that completed without error.
        Handlers that timeout or raise are logged and counted as failures
        but do not abort the dispatch of remaining handlers.
        """
        timeout = timeout if timeout is not None else self._handler_timeout
        handlers = self._handlers.get(topic, [])
        loop = asyncio.get_event_loop()

        async def _dispatch_one(h: Callable) -> bool:
            try:
                if asyncio.iscoroutinefunction(h):
                    await asyncio.wait_for(h(message), timeout=timeout)
                else:
                    # Run sync handler in thread-pool; wrap in wait_for
                    await asyncio.wait_for(
                        loop.run_in_executor(None, h, message),
                        timeout=timeout,
                    )
                return True
            except asyncio.TimeoutError:
                logger.warning(
                    "InteropBridge: handler timeout on topic={!r} handler={!r}",
                    topic, getattr(h, '__name__', repr(h)),
                )
                return False
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "InteropBridge: handler error on topic={!r}: {}", topic, exc
                )
                return False

        results = await asyncio.gather(*[_dispatch_one(h) for h in handlers])
        delivered = sum(results)

        # Ring-buffer log
        entry: Dict[str, Any] = {
            "topic": topic,
            "message": message,
            "dispatched": len(handlers),
            "delivered": delivered,
            "ts_ns": time.time_ns(),
        }
        async with self._lock:
            if len(self._log) >= MAX_LOG_ENTRIES:
                self._log.pop(0)  # evict oldest
            self._log.append(entry)

        return delivered

    def sync_publish(self, topic: str, message: Dict[str, Any]) -> None:
        """
        Fire-and-forget shim for sync call-sites.

        Schedules publish() as an asyncio task. The task result is
        discarded. Use only where the caller cannot be made async.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.publish(topic, message))
            else:
                loop.run_until_complete(self.publish(topic, message))
        except RuntimeError:
            logger.error(
                "InteropBridge.sync_publish: no running event loop for topic={!r}",
                topic,
            )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    async def get_log(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        async with self._lock:
            entries = list(self._log)
        return entries[-limit:] if limit else entries

    async def clear_log(self) -> None:
        async with self._lock:
            self._log.clear()

    def health_check(self) -> bool:
        return isinstance(self._handlers, dict)

    def topic_count(self) -> int:
        return len(self._handlers)

    def handler_count(self, topic: str) -> int:
        return len(self._handlers.get(topic, []))
