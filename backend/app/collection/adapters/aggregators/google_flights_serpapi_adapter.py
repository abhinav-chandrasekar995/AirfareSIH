"""Google Flights (via SerpApi) aggregator adapter.

SerpApi is a paid, authorized third-party API - not a site this platform scrapes. See
IMPLEMENTATION_LOG.md for why this exists: direct scraping of this basket's actual
airline/OTA sites was found to be blocked by their own robots.txt, confirmed live, not
assumed (EaseMyTrip disallows /flight-search/listing*; SpiceJet disallows /api/v1, which
its own flight-search page calls internally just to render). An authorized aggregator
API is what makes real fare data reachable for this pipeline at all, without evading
anyone's stated wishes.

Response shape is SerpApi's own (`best_flights`/`other_flights` arrays, each one
itinerary with its own `price` and one or more `flights` legs) - different enough from
the OTA/airline JSON shape in parsing.py's _parse_json_fares to warrant its own parser
here rather than forcing it into that one.
"""
from __future__ import annotations

from datetime import datetime

from app.collection.adapters.parsing import build_observation, parse_amount
from app.collection.base_adapter import (
    BaseSourceAdapter,
    FareQuery,
    RateLimit,
    RawPayload,
    SourceUnavailableError,
)
from app.collection.transports.httpx_client import fetch_json
from app.config import settings
from app.core.constants import SourceType

SERPAPI_URL = "https://serpapi.com/search.json"

# SerpApi returns a free-text airline name, not the IATA code this platform's schema
# uses elsewhere (seeds/generate_seed.py's AIRLINES) - best-effort lookup, skip the
# observation rather than guess when a carrier isn't one of this basket's tracked five.
AIRLINE_NAME_TO_CODE = {
    "indigo": "6E",
    "air india": "AI",
    "air india express": "IX",
    "akasa air": "QP",
    "spicejet": "SG",
}


class GoogleFlightsSerpApiAdapter(BaseSourceAdapter):
    source_code = "google_flights"
    source_name = "Google Flights (via SerpApi)"
    source_type = SourceType.AGGREGATOR
    adapter_version = "1.0.0"
    base_url = "https://serpapi.com"
    # Conservative on purpose: SerpApi's free tier is 250 searches/month, so this rate
    # is about not burning quota carelessly, not about being polite to a scraped site.
    rate_limit = RateLimit(requests_per_minute=6, max_concurrency=1, backoff_seconds=5.0)

    def search_params(self, query: FareQuery) -> dict:
        return {
            "engine": "google_flights",
            "departure_id": query.origin,
            "arrival_id": query.destination,
            "outbound_date": query.departure_date.isoformat(),
            "type": "2",  # one-way
            "currency": "INR",
            "hl": "en",
            "gl": "in",
            "api_key": settings.serpapi_key,
        }

    async def fetch(self, query: FareQuery) -> RawPayload:
        if not settings.collection_enabled:
            raise SourceUnavailableError(
                "live collection is disabled (settings.collection_enabled=False); "
                "the platform is serving the seeded REPLAY dataset"
            )
        if not settings.serpapi_key:
            raise SourceUnavailableError(
                "SERPAPI_KEY is not configured; this adapter fails closed rather than "
                "silently reporting zero fares so a missing key is never mistaken for "
                "an empty market"
            )
        return await fetch_json(SERPAPI_URL, params=self.search_params(query))

    def parse(self, payload: RawPayload, query: FareQuery) -> list[dict]:
        content = payload.content
        if not isinstance(content, dict) or content.get("error"):
            # A bad key, exhausted quota, or an unsupported route surfaces here as a
            # normal 200 JSON body with an "error" field, not an HTTP failure - treat it
            # as zero observations rather than crash the collection run.
            return []

        observations: list[dict] = []
        for itinerary in (*content.get("best_flights", []), *content.get("other_flights", [])):
            legs = itinerary.get("flights") or []
            if not legs or itinerary.get("layovers"):
                continue  # direct flights only - a connection isn't one comparable fare
            leg = legs[0]

            total = parse_amount(itinerary.get("price"))
            flight_no = leg.get("flight_number")
            if not total or not flight_no:
                continue

            airline_code = AIRLINE_NAME_TO_CODE.get((leg.get("airline") or "").strip().lower())
            if not airline_code:
                continue

            departure_time = None
            raw_dep = (leg.get("departure_airport") or {}).get("time")
            if raw_dep:
                for fmt in ("%Y-%m-%d %H:%M", "%b %d, %Y %I:%M %p"):
                    try:
                        departure_time = datetime.strptime(raw_dep, fmt).time()
                        break
                    except ValueError:
                        continue

            observations.append(
                build_observation(
                    source_code=self.source_code,
                    query=query,
                    airline_code=airline_code,
                    flight_number=str(flight_no),
                    total_fare=total,
                    departure_time=departure_time,
                )
            )
        return observations
