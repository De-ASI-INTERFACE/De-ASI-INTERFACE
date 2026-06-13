"""
src/api/auth/token_store.py

ACTION 1 (SEC-001) + ACTION 3 (SEC-007) + ACTION 5 (SEC-010)

In-memory JWT revocation store and WebSocket ticket store.
In production, replace with Redis (aioredis) for:
  - Persistence across restarts
  - Shared state across horizontal replicas
  - Native TTL support

Redis drop-in:
    redis = aioredis.from_url(settings.REDIS_URL)
    await redis.setex(f'jti:{jti}', ttl, '1')        # store
    exists = await redis.exists(f'jti:{jti}')         # is_valid
    await redis.delete(f'jti:{jti}')                  # revoke
"""

import asyncio
import time
from typing import Dict, Optional, Tuple

from loguru import logger


class TokenStore:
    def __init__(self) -> None:
        # {jti: expiry_timestamp}
        self._valid_tokens: Dict[str, float] = {}
        # {ticket: (user_id, expiry_timestamp)}
        self._ws_tickets: Dict[str, Tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    async def store(self, jti: str, ttl_seconds: int = 3600) -> None:
        """Register a JWT JTI as valid."""
        async with self._lock:
            self._valid_tokens[jti] = time.monotonic() + ttl_seconds
            self._cleanup_expired_tokens()

    async def is_valid(self, jti: str) -> bool:
        """Returns True if JTI exists and has not expired or been revoked."""
        async with self._lock:
            expiry = self._valid_tokens.get(jti)
            if expiry is None:
                return False
            return time.monotonic() < expiry

    async def revoke(self, jti: str) -> None:
        """Revoke a JWT by removing its JTI from the valid set."""
        async with self._lock:
            removed = self._valid_tokens.pop(jti, None)
            if removed:
                logger.debug(f"JWT revoked | jti={jti[:8]}...")
            else:
                logger.warning(f"Revoke called on unknown JTI | jti={jti[:8]}...")

    async def store_ws_ticket(
        self, ticket: str, user_id: str, ttl_seconds: int = 30
    ) -> None:
        """Store a single-use WebSocket ticket with TTL."""
        async with self._lock:
            expiry = time.monotonic() + ttl_seconds
            self._ws_tickets[ticket] = (user_id, expiry)

    async def consume_ws_ticket(self, ticket: str) -> Optional[str]:
        """
        Consume a WebSocket ticket (single-use).
        Returns user_id if valid, None if expired or not found.
        """
        async with self._lock:
            entry = self._ws_tickets.pop(ticket, None)
            if entry is None:
                logger.warning(f"WS ticket not found or already consumed | ticket={ticket[:8]}...")
                return None
            user_id, expiry = entry
            if time.monotonic() > expiry:
                logger.warning(f"WS ticket expired | user={user_id} | ticket={ticket[:8]}...")
                return None
            logger.debug(f"WS ticket consumed | user={user_id}")
            return user_id

    def _cleanup_expired_tokens(self) -> None:
        """Prune expired entries — call periodically or on write."""
        now = time.monotonic()
        self._valid_tokens = {
            jti: exp for jti, exp in self._valid_tokens.items() if exp > now
        }
        self._ws_tickets = {
            t: v for t, v in self._ws_tickets.items() if v[1] > now
        }
