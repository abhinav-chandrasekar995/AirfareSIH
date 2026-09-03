"""One real, single query against SerpApi's Google Flights engine, to verify the
adapter's parsing assumptions against the ACTUAL live response shape rather than just
documentation. Costs exactly one of your monthly quota.

Deliberately standalone (bypasses settings.collection_enabled) so this can run without
touching global config - it directly constructs the adapter and calls fetch()/parse().
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.collection.adapters.aggregators.google_flights_serpapi_adapter import (
    GoogleFlightsSerpApiAdapter,
)
from app.collection.base_adapter import FareQuery
from app.config import settings
from app.core.constants import LeadBucket

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    if not settings.serpapi_key:
        print("SERPAPI_KEY is not set in backend/.env - nothing to test.")
        return

    query = FareQuery(
        route_code="DEL-BOM",
        departure_date=date.today() + timedelta(days=15),
        lead_bucket=LeadBucket.T15,
    )

    adapter = GoogleFlightsSerpApiAdapter()
    print(f"Querying SerpApi (Google Flights): {query.origin} -> {query.destination}, "
          f"departing {query.departure_date.isoformat()} (T+15)")
    print("(1 request, consumes 1 of your monthly quota)\n")

    # Bypass the collection_enabled gate deliberately for this one-off verification -
    # the gate exists to stop the app's own background scheduler from running live,
    # not to block a manual, explicit, single test invocation like this one.
    payload = await _fetch_raw(adapter, query)

    (RAW_DIR / "serpapi_google_flights_probe.json").write_text(
        json.dumps(payload.content, indent=2, default=str), encoding="utf-8"
    )
    print(f"HTTP status: {payload.http_status}")
    print(f"Raw response saved to: {RAW_DIR / 'serpapi_google_flights_probe.json'}")

    if isinstance(payload.content, dict) and payload.content.get("error"):
        print(f"\nSerpApi returned an error: {payload.content['error']}")
        return

    observations = adapter.parse(payload, query)
    print(f"\nParsed {len(observations)} usable observation(s) (direct flights, tracked carriers only):")
    for obs in observations:
        print(
            f"   {obs['airline_code']} {obs['flight_number']}  "
            f"dep {obs['departure_datetime']}  total_fare INR {obs['total_fare']}"
        )

    if not observations and isinstance(payload.content, dict):
        n_best = len(payload.content.get("best_flights", []))
        n_other = len(payload.content.get("other_flights", []))
        print(
            f"\n0 parsed, but the raw response had {n_best} best_flights + {n_other} "
            "other_flights entries - inspect the saved JSON to see why (e.g. layovers, "
            "an untracked carrier, or a field name that doesn't match what the parser "
            "expects)."
        )


async def _fetch_raw(adapter: GoogleFlightsSerpApiAdapter, query: FareQuery):
    from app.collection.transports.httpx_client import fetch_json

    return await fetch_json(
        "https://serpapi.com/search.json", params=adapter.search_params(query)
    )


if __name__ == "__main__":
    asyncio.run(main())
