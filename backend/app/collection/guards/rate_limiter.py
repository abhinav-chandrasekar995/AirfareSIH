"""Per-source rate limiting.

Backed by Redis so the limit is shared across every worker process. A per-process
limiter would multiply the real request rate by the number of workers, which is exactly
the failure that gets a collector blocked.
"""
from __future__ import annotations

import asyncio
import time


class RateLimiter:
    def __init__(self, redis=None) -> None:
        self.redis = redis
        self._local: dict[str, list[float]] = {}

    async def acquire(self, source_code: str, requests_per_minute: int) -> None:
        """Block until a request slot is available for this source."""
        if self.redis is not None:
            await self._acquire_redis(source_code, requests_per_minute)
        else:
            await self._acquire_local(source_code, requests_per_minute)

    async def _acquire_redis(self, source_code: str, rpm: int) -> None:
        key = f"ratelimit:{source_code}:{int(time.time() // 60)}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 120)
        if count > rpm:
            # Wait out the remainder of the current minute rather than dropping work.
            await asyncio.sleep(60 - (time.time() % 60))

    async def _acquire_local(self, source_code: str, rpm: int) -> None:
        now = time.time()
        window = [t for t in self._local.get(source_code, []) if now - t < 60]
        if len(window) >= rpm:
            await asyncio.sleep(max(0.0, 60 - (now - window[0])))
            window = []
        window.append(time.time())
        self._local[source_code] = window
