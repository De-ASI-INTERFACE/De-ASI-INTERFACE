"""Base AI Agent — continuous async execution loop for blockchain-contained validators.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_TICK_INTERVAL_S: float = 0.4   # Alpenglow slot time target
MAX_BACKOFF_S: float = 30.0
INITIAL_BACKOFF_S: float = 0.5


class BaseAgent(ABC):
    """
    Abstract base for every De-ASI validator agent.

    Subclasses implement:
      - execute(payload)  — one unit of work per tick
      - health_check()    — synchronous liveness probe

    The run() coroutine drives a strict continuous cycle:

        while running:
            t0 = now()
            await execute_tick()
            sleep(max(0, tick_interval - elapsed))  # slot-aligned

    Exceptions inside execute() are caught, logged, and retried with
    exponential backoff capped at MAX_BACKOFF_S.  Clean shutdown is
    triggered by stop() or asyncio.CancelledError.
    """

    def __init__(
        self,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None,
        tick_interval: float = DEFAULT_TICK_INTERVAL_S,
    ) -> None:
        self.agent_id = agent_id
        self.config = config or {}
        self.tick_interval = tick_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None  # type: ignore[type-arg]
        self._consecutive_errors = 0
        self._last_tick_ns: int = 0
        logger.info("Agent {} initialized | tick={:.3f}s", agent_id, tick_interval)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one tick of validator work. Must be async."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Synchronous liveness probe. Must not block for >50 ms."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Schedule the continuous run() loop on the running event loop."""
        if self._running:
            logger.warning("Agent {} already running — ignoring start()", self.agent_id)
            return
        self._running = True
        self._task = asyncio.get_event_loop().create_task(
            self.run(), name=f"agent-{self.agent_id}"
        )
        logger.info("Agent {} started", self.agent_id)

    def stop(self) -> None:
        """Signal the run loop to stop; cancel the underlying task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Agent {} stop requested", self.agent_id)

    async def join(self) -> None:
        """Await clean shutdown of the run loop."""
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Agent {} joined", self.agent_id)

    # ------------------------------------------------------------------
    # Continuous cycle
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """
        Strict continuous cycle — slot-aligned, backoff-on-error.

        Tick timing:
          - Each iteration targets tick_interval seconds wall-clock.
          - execute() time is subtracted from the sleep; if execute()
            overruns the full tick_interval, the next tick fires
            immediately (no drift accumulation).

        Error handling:
          - On exception: log, increment _consecutive_errors, sleep
            backoff (exponential, capped at MAX_BACKOFF_S).
          - On successful tick: reset _consecutive_errors and backoff.
          - asyncio.CancelledError propagates cleanly.
        """
        backoff = INITIAL_BACKOFF_S
        logger.info("Agent {} run loop starting", self.agent_id)

        while self._running:
            tick_start = time.monotonic()
            self._last_tick_ns = time.time_ns()

            try:
                payload: Dict[str, Any] = self._build_tick_payload()
                await self.execute(payload)
                # Successful tick — reset error counter and backoff
                self._consecutive_errors = 0
                backoff = INITIAL_BACKOFF_S

            except asyncio.CancelledError:
                logger.info("Agent {} received CancelledError — stopping", self.agent_id)
                break

            except Exception as exc:  # noqa: BLE001
                self._consecutive_errors += 1
                backoff = min(backoff * 2, MAX_BACKOFF_S)
                logger.error(
                    "Agent {} tick error #{} ({}) — backing off {:.1f}s",
                    self.agent_id,
                    self._consecutive_errors,
                    exc,
                    backoff,
                )
                try:
                    await asyncio.sleep(backoff)
                except asyncio.CancelledError:
                    break
                continue

            # Slot-aligned sleep: remainder of tick_interval after execute() cost
            elapsed = time.monotonic() - tick_start
            sleep_for = max(0.0, self.tick_interval - elapsed)
            if sleep_for > 0:
                try:
                    await asyncio.sleep(sleep_for)
                except asyncio.CancelledError:
                    break

        self._running = False
        logger.info("Agent {} run loop exited | total_errors={}",
                    self.agent_id, self._consecutive_errors)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_tick_payload(self) -> Dict[str, Any]:
        """Construct the standard payload delivered to execute() each tick."""
        return {
            "agent_id": self.agent_id,
            "tick_ns": self._last_tick_ns,
            "consecutive_errors": self._consecutive_errors,
        }

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_tick_ns(self) -> int:
        return self._last_tick_ns

    def __repr__(self) -> str:
        return (
            f"<BaseAgent id={self.agent_id!r} running={self._running} "
            f"errors={self._consecutive_errors}>"
        )
