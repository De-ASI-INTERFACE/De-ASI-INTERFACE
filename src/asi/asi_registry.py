"""ASI Ecosystem Registry — liveness-tracked, stale-agent reaping.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_HEARTBEAT_TTL_S: float = 10.0   # agent considered stale after this
REAPER_INTERVAL_S: float = 5.0          # how often the reaper loop runs


class ASIRegistry:
    """
    Registry of active ASI validator agents with continuous liveness tracking.

    Each registered agent is expected to call heartbeat(agent_id) at least
    once every DEFAULT_HEARTBEAT_TTL_S seconds. Agents that miss the window
    are automatically marked inactive by the background reaper task.

    Methods:
      register()        — add agent with capabilities and initial heartbeat
      deregister()      — remove agent entirely
      heartbeat()       — reset the agent's liveness timer
      mark_unhealthy()  — force-mark an agent inactive without deregistering
      lookup()          — list active agents that have a given capability
      get_live()        — list all currently-active agent IDs
      get_agent()       — get full metadata for one agent
      list_all()        — list every registered agent (active + inactive)
      count()           — total registered count
      health_check()    — True if registry data structure is intact
      start_reaper()    — launch background stale-agent reaper coroutine
      stop_reaper()     — cancel reaper task
    """

    def __init__(self, heartbeat_ttl: float = DEFAULT_HEARTBEAT_TTL_S) -> None:
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._heartbeat_ttl = heartbeat_ttl
        self._lock = asyncio.Lock()
        self._reaper_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(
        self,
        agent_id: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        async with self._lock:
            self._agents[agent_id] = {
                "capabilities": capabilities,
                "metadata": metadata or {},
                "active": True,
                "last_heartbeat": time.monotonic(),
                "registered_at": time.time(),
                "heartbeat_count": 0,
            }
        logger.info("ASIRegistry: registered agent={!r} caps={}", agent_id, capabilities)
        return True

    async def deregister(self, agent_id: str) -> bool:
        async with self._lock:
            if agent_id not in self._agents:
                return False
            del self._agents[agent_id]
        logger.info("ASIRegistry: deregistered agent={!r}", agent_id)
        return True

    # ------------------------------------------------------------------
    # Liveness
    # ------------------------------------------------------------------

    async def heartbeat(self, agent_id: str) -> bool:
        """
        Reset the liveness timer for *agent_id*.
        Reactivates the agent if it was previously marked inactive.
        Returns False if the agent is not registered.
        """
        async with self._lock:
            entry = self._agents.get(agent_id)
            if entry is None:
                return False
            entry["last_heartbeat"] = time.monotonic()
            entry["heartbeat_count"] += 1
            if not entry["active"]:
                entry["active"] = True
                logger.info("ASIRegistry: agent={!r} reactivated via heartbeat", agent_id)
        return True

    async def mark_unhealthy(self, agent_id: str) -> bool:
        """Force-mark an agent as inactive without removing it."""
        async with self._lock:
            entry = self._agents.get(agent_id)
            if entry is None:
                return False
            entry["active"] = False
        logger.warning("ASIRegistry: agent={!r} marked unhealthy", agent_id)
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def lookup(self, capability: str) -> List[str]:
        """Return IDs of active agents that have *capability*."""
        async with self._lock:
            return [
                aid for aid, d in self._agents.items()
                if capability in d["capabilities"] and d["active"]
            ]

    async def get_live(self) -> List[str]:
        """Return all currently-active agent IDs."""
        async with self._lock:
            return [aid for aid, d in self._agents.items() if d["active"]]

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            entry = self._agents.get(agent_id)
            return dict(entry) if entry else None

    async def list_all(self) -> List[str]:
        async with self._lock:
            return list(self._agents.keys())

    async def count(self) -> int:
        async with self._lock:
            return len(self._agents)

    # ------------------------------------------------------------------
    # Background reaper
    # ------------------------------------------------------------------

    def start_reaper(self) -> None:
        """Launch the background stale-agent reaper as an asyncio task."""
        if self._reaper_task and not self._reaper_task.done():
            logger.warning("ASIRegistry: reaper already running")
            return
        self._reaper_task = asyncio.get_event_loop().create_task(
            self._reaper_loop(), name="asi-registry-reaper"
        )
        logger.info("ASIRegistry: reaper started | ttl={}s", self._heartbeat_ttl)

    def stop_reaper(self) -> None:
        """Cancel the background reaper task."""
        if self._reaper_task and not self._reaper_task.done():
            self._reaper_task.cancel()
            logger.info("ASIRegistry: reaper stopped")

    async def _reaper_loop(self) -> None:
        """
        Runs every REAPER_INTERVAL_S. Any agent whose last_heartbeat is
        older than _heartbeat_ttl is marked inactive (not deregistered —
        the agent may recover and call heartbeat() to reactivate).
        """
        while True:
            try:
                await asyncio.sleep(REAPER_INTERVAL_S)
                now = time.monotonic()
                async with self._lock:
                    for agent_id, entry in self._agents.items():
                        if not entry["active"]:
                            continue
                        age = now - entry["last_heartbeat"]
                        if age > self._heartbeat_ttl:
                            entry["active"] = False
                            logger.warning(
                                "ASIRegistry: agent={!r} marked stale "
                                "(no heartbeat for {:.1f}s)",
                                agent_id, age,
                            )
            except asyncio.CancelledError:
                break
            except Exception as exc:  # noqa: BLE001
                logger.error("ASIRegistry reaper error: {}", exc)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        return isinstance(self._agents, dict)

    def __repr__(self) -> str:
        total = len(self._agents)
        active = sum(1 for d in self._agents.values() if d["active"])
        return f"<ASIRegistry total={total} active={active}>"
