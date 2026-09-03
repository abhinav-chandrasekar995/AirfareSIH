"""Reconnaissance-only probe of SpiceJet's flight-search page.

This is deliberately NOT a scraper. It makes exactly one page load - no retries, no
stealth flags (no --disable-blink-features, no fingerprint spoofing), the project's own
self-identifying User-Agent (app/collection/guards/robots_guard.py's USER_AGENT) - and
reports what actually happens:

  1. Every distinct network request the page itself triggers while rendering, checked
     against spicejet.com/robots.txt's real Disallow list (/cgi-bin/, /api/v1, /public/,
     /externalBooking). robots.txt governs which URLs get fetched, not who explicitly
     asked for them - if the page's own client-side JS calls a disallowed path to load
     live fares, rendering the page at all is the disallowed act, even though the entry
     URL (/flight-search) is not itself listed. This script checks for exactly that
     before treating anything as usable.
  2. Whether the response looks like an anti-bot challenge (reusing this project's own
     CHALLENGE_MARKERS/CHALLENGE_STATUS_CODES from app/collection/guards/challenge_detector.py,
     for the same reasons that module gives: detect and stop, never solve or bypass).
  3. A saved copy of the rendered HTML, a screenshot, and any JSON XHR/fetch response
     bodies seen from ALLOWED paths only - for human inspection to judge feasibility,
     not for feeding into the CPI pipeline. Nothing here is parsed into fare records.

Run once, by hand, when you actually want an answer to "does this work" - not on a
schedule, not in a loop.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.collection.guards.challenge_detector import CHALLENGE_MARKERS, CHALLENGE_STATUS_CODES
from app.collection.guards.robots_guard import USER_AGENT

BASE_URL = "https://www.spicejet.com"
DISALLOWED_PATHS = ["/cgi-bin/", "/api/v1", "/public/", "/externalBooking"]

# Real calendar T+15 from the actual day this probe runs, not the project's seeded date.
TODAY = date.today()
DEPARTURE = TODAY + timedelta(days=15)
SEARCH_URL = f"{BASE_URL}/flight-search?from=DEL&to=BOM&depart={DEPARTURE.isoformat()}&adults=1"

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def is_disallowed(url: str) -> bool:
    path = urlparse(url).path
    return any(path.startswith(p) for p in DISALLOWED_PATHS)


def looks_like_challenge(status: int | None, text: str) -> bool:
    if status in CHALLENGE_STATUS_CODES:
        return True
    lowered = text.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)


async def main() -> None:
    from playwright.async_api import async_playwright

    requests_seen: list[tuple[str, str]] = []  # (url, resource_type)
    disallowed_hits: list[str] = []
    xhr_responses: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        def on_request(request):
            requests_seen.append((request.url, request.resource_type))
            if is_disallowed(request.url):
                disallowed_hits.append(request.url)

        async def on_response(response):
            if response.request.resource_type not in ("xhr", "fetch"):
                return
            ctype = response.headers.get("content-type", "")
            entry = {"url": response.url, "status": response.status, "content_type": ctype}
            if "json" in ctype and not is_disallowed(response.url):
                try:
                    entry["body_preview"] = (await response.text())[:2000]
                except Exception as exc:
                    entry["body_preview"] = f"<could not read body: {exc}>"
            xhr_responses.append(entry)

        page.on("request", on_request)
        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        print(f"Navigating to: {SEARCH_URL}")
        print("(single request, no retries, no stealth flags, self-identifying UA)\n")
        status = None
        try:
            response = await page.goto(SEARCH_URL, wait_until="networkidle", timeout=30_000)
            status = response.status if response else None
        except Exception as exc:
            print(f"Navigation failed or timed out: {exc}")

        await asyncio.sleep(2)  # let any trailing XHRs settle, no repeated polling

        # Read the rendered content into memory for the disallowed/challenge checks below
        # regardless of outcome - but only PERSIST it to disk (data/raw/) if the run
        # turns out to be clean. A blocked or challenged run must leave nothing behind.
        html = await page.content()
        if not disallowed_hits:
            await page.screenshot(path=str(RAW_DIR / "spicejet_probe.png"), full_page=True)

        await browser.close()

    if not disallowed_hits:
        (RAW_DIR / "spicejet_probe.html").write_text(html, encoding="utf-8")

    print(f"HTTP status of entry page: {status}")
    print(f"Distinct requests triggered by rendering this one page: {len({u for u, _ in requests_seen})}")
    print(f"Of those, XHR/fetch requests: {len(xhr_responses)}")

    if disallowed_hits:
        print(f"\n[BLOCKED] {len(set(disallowed_hits))} request(s) hit a robots.txt-DISALLOWED path:")
        for url in sorted(set(disallowed_hits)):
            print(f"   {url}")
        print(
            "\nConclusion: rendering this page necessarily triggers a disallowed fetch. "
            "Live collection from SpiceJet's flight-search page is not ethically viable "
            "via this route, regardless of what data it contains. No fare data is being "
            "extracted from this probe."
        )
    elif looks_like_challenge(status, html):
        print(
            "\n[CHALLENGED] The response looks like an anti-bot challenge/block page "
            "(matches this project's own CHALLENGE_MARKERS or a CHALLENGE_STATUS_CODE). "
            "Per this project's design, collection stops here - not solved, not retried."
        )
    else:
        print(
            "\n[OK] No disallowed paths were triggered, and the page doesn't look like "
            "a challenge/block page."
        )
        print(f"Raw HTML saved to: {RAW_DIR / 'spicejet_probe.html'}")
        print(f"Screenshot saved to: {RAW_DIR / 'spicejet_probe.png'}")
        if xhr_responses:
            print(f"\n{len(xhr_responses)} XHR/fetch response(s) observed on allowed paths:")
            for r in xhr_responses:
                print(f"   [{r['status']}] {r['url']}  ({r['content_type']})")
        else:
            print("\nNo XHR/fetch calls were observed at all - if fares appear on the")
            print("page, they are likely server-rendered directly into the initial HTML.")
        print(
            "\nInspect the saved HTML/screenshot manually to judge whether fare data is "
            "actually present and in what shape, before writing any real parser."
        )


if __name__ == "__main__":
    asyncio.run(main())
