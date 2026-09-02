"""Yatra OTA adapter.

OTA quotes matter to this platform for a specific reason: comparing the same itinerary
across sources is what exposes convenience-fee spread and cross-source inconsistency,
which feeds both the divergence module and the data-quality framework.

See D-023 in IMPLEMENTATION_LOG.md regarding live-collection status.
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


class YatraAdapter(BaseSourceAdapter):
    source_code = "yatra"
    source_name = "Yatra"
    source_type = SourceType.OTA
    adapter_version = "1.0.0"
    base_url = "https://www.yatra.com"
    rate_limit = RateLimit(requests_per_minute=12, max_concurrency=2, backoff_seconds=3.0)

    def search_url(self, query: FareQuery) -> str:
        return (
            f"{self.base_url}/flight/search"
            f"?itinerary={query.origin}-{query.destination}-"
            f"{query.departure_date.isoformat()}&paxType=A-1&cabinClass=E"
        )

    async def fetch(self, query: FareQuery) -> RawPayload:
        if not settings.collection_enabled:
            raise SourceUnavailableError(
                "live collection is disabled (settings.collection_enabled=False); "
                "the platform is serving the seeded REPLAY dataset"
            )
        return await playwright_pool.pool.render(self.source_code, self.search_url(query))

    def parse(self, payload: RawPayload, query: FareQuery) -> list[dict]:
        # airline_code is left to the payload: an OTA returns many carriers per query.
        return parse_fare_cards(payload=payload, query=query, source_code=self.source_code)
