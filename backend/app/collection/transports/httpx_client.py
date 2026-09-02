"""Shared HTTP transport for sources exposing a JSON endpoint."""
from __future__ import annotations

from datetime import UTC, datetime

from app.collection.base_adapter import RawPayload
from app.collection.guards.robots_guard import USER_AGENT

DEFAULT_TIMEOUT = 20.0


async def fetch_json(url: str, params: dict | None = None, headers: dict | None = None) -> RawPayload:
    import httpx

    merged = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
        response = await client.get(url, params=params, headers=merged)
        try:
            content = response.json()
        except Exception:
            content = response.text
        return RawPayload(
            content=content,
            url=str(response.url),
            fetched_at=datetime.now(UTC),
            http_status=response.status_code,
        )
