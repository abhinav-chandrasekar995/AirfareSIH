"""Pooled Playwright contexts for JavaScript-rendered fare pages.

One persistent browser context per source, reused across queries. Session reuse is not
an optimisation here - it is what keeps the request count low enough to stay within the
courtesy limits the platform commits to.

Playwright is used only to render pages a normal browser would render. It is never used
to defeat a CAPTCHA, log in behind a wall, or evade a block.
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.collection.base_adapter import RawPayload
from app.collection.guards.robots_guard import USER_AGENT


class PlaywrightPool:
    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._contexts: dict[str, object] = {}

    async def start(self) -> None:
        if self._browser is not None:
            return
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def context_for(self, source_code: str):
        await self.start()
        if source_code not in self._contexts:
            self._contexts[source_code] = await self._browser.new_context(
                user_agent=USER_AGENT,
                locale="en-IN",
                timezone_id="Asia/Kolkata",
            )
        return self._contexts[source_code]

    async def render(self, source_code: str, url: str, wait_selector: str | None = None) -> RawPayload:
        context = await self.context_for(source_code)
        page = await context.new_page()
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=15_000)
            return RawPayload(
                content=await page.content(),
                url=url,
                fetched_at=datetime.now(UTC),
                http_status=response.status if response else None,
            )
        finally:
            await page.close()

    async def close(self) -> None:
        for context in self._contexts.values():
            await context.close()
        self._contexts.clear()
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


pool = PlaywrightPool()
