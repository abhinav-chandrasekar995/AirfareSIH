"""Redis cache with graceful degradation.

Cache keys embed the methodology version, so publishing a new methodology invalidates
every derived value automatically rather than serving a stale number computed under
different rules.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from app.config import settings

TTL_BY_GRANULARITY = {"daily": 3600, "weekly": 21600, "monthly": 86400}
DEFAULT_TTL = 900


def cache_key(endpoint: str, params: dict[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"api:{settings.methodology_version}:{endpoint}:{digest}"


class Cache:
    def __init__(self, redis=None) -> None:
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        if self.redis is None:
            return None
        try:
            raw = await self.redis.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            # A cache failure must never take the API down.
            return None

    async def set_json(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            return

    async def invalidate_prefix(self, prefix: str) -> int:
        if self.redis is None:
            return 0
        try:
            deleted = 0
            async for key in self.redis.scan_iter(match=f"{prefix}*", count=500):
                await self.redis.delete(key)
                deleted += 1
            return deleted
        except Exception:
            return 0


_cache: Cache | None = None


async def get_cache() -> Cache:
    global _cache
    if _cache is None:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(settings.redis_url, decode_responses=True)
            await client.ping()
            _cache = Cache(client)
        except Exception:
            _cache = Cache(None)
    return _cache
