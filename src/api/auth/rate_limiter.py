"""
src/api/auth/rate_limiter.py

ACTION 4 — SEC-005: In-memory rate limiter for 2FA attempts.
In production, swap AttemptStore for a Redis-backed implementation
to persist limits across process restarts and horizontal scaling.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from loguru import logger


@dataclass
class AttemptRecord:
    timestamps: List[float] = field(default_factory=list)


class RateLimiter:
    """
    Sliding-window rate limiter.

    Usage:
        limiter = RateLimiter()
        allowed = await limiter.check('2fa:richard', max_attempts=5, window_seconds=900)
        if not allowed:
            raise HTTPException(429, ...)
        # on failure:
        await limiter.record_failure('2fa:richard')
        # on success:
        await limiter.reset('2fa:richard')
    """

    def __init__(self) -> None:
        self._records: Dict[str, AttemptRecord] = defaultdict(AttemptRecord)
        self._lock = asyncio.Lock()

    async def check(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Returns True if the action is allowed (under limit)."""
        async with self._lock:
            record = self._records[key]
            now = time.monotonic()
            # Prune timestamps outside the window
            record.timestamps = [
                t for t in record.timestamps
                if now - t < window_seconds
            ]
            return len(record.timestamps) < max_attempts

    async def record_failure(self, key: str) -> None:
        """Record a failed attempt."""
        async with self._lock:
            self._records[key].timestamps.append(time.monotonic())

    async def attempts_remaining(self, key: str, max_attempts: int, window_seconds: int = 900) -> int:
        """Returns how many attempts remain in the current window."""
        async with self._lock:
            record = self._records[key]
            now = time.monotonic()
            recent = [t for t in record.timestamps if now - t < window_seconds]
            return max(0, max_attempts - len(recent))

    async def reset(self, key: str) -> None:
        """Clear all attempts for a key (call on successful auth)."""
        async with self._lock:
            if key in self._records:
                del self._records[key]
                logger.debug(f"Rate limiter reset | key={key}")
