"""Air India (AI) airline-direct adapter.

See D-023 in IMPLEMENTATION_LOG.md: structure and guards are real; the parser is written
against the documented response shape but is not calibrated against live traffic, and
collection is disabled by default.
"""
from __future__ import annotations

from app.collection.adapters.parsing import parse_fare_cards
from app.collection.base_adapter import (
    BaseSourceAdapter,
    FareQuery,
    RateLimit,
    RawPayload,
    SourceUnavailableError,
)
from app.collection.transports import playwright_pool
from app.config import settings
from app.core.constants import SourceType


class AirIndiaAdapter(BaseSourceAdapter):
    source_code = "airindia"
    source_name = "Air India"
    source_type = SourceType.AIRLINE_DIRECT
    adapter_version = "1.0.0"
    base_url = "https://www.airindia.com"
    rate_limit = RateLimit(requests_per_minute=8, max_concurrency=1, backoff_seconds=4.0)

    def search_url(self, query: FareQuery) -> str:
        return (
            f"{self.base_url}/flight-search"
            f"?from={query.origin}&to={query.destination}"
            f"&depart={query.departure_date.isoformat()}&adults=1"
        )

    async def fetch(self, query: FareQuery) -> RawPayload:
        if not settings.collection_enabled:
            raise SourceUnavailableError(
                "live collection is disabled (settings.collection_enabled=False); "
                "the platform is serving the seeded REPLAY dataset"
            )
        return await playwright_pool.pool.render(self.source_code, self.search_url(query))

    def parse(self, payload: RawPayload, query: FareQuery) -> list[dict]:
        return parse_fare_cards(
            payload=payload, query=query, source_code=self.source_code, airline_code="AI"
        )
