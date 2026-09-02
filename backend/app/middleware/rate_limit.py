"""Per-key token-bucket rate limiting with standard headers."""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.cache import get_cache


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window counter per (principal, minute).

    Falls back to an in-process counter when Redis is unavailable so the limit still
    applies in local development rather than silently disappearing.
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._local: dict[str, tuple[int, int]] = {}

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        identity = request.headers.get(settings.api_key_header) or (
            request.client.host if request.client else "anonymous"
        )
        limit = settings.default_rate_limit_per_min
        window = int(time.time() // 60)
        key = f"ratelimit:api:{identity}:{window}"

        cache = await get_cache()
        count = await self._increment(cache, key, window, identity)

        if count > limit:
            retry_after = 60 - int(time.time() % 60)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": f"rate limit of {limit} requests/minute exceeded",
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str((window + 1) * 60),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        response.headers["X-RateLimit-Reset"] = str((window + 1) * 60)
        return response

    async def _increment(self, cache, key: str, window: int, identity: str) -> int:
        if cache.redis is not None:
            try:
                count = await cache.redis.incr(key)
                if count == 1:
                    await cache.redis.expire(key, 120)
                return int(count)
            except Exception:
                pass
        stored_window, stored_count = self._local.get(identity, (window, 0))
        count = stored_count + 1 if stored_window == window else 1
        self._local[identity] = (window, count)
        return count
