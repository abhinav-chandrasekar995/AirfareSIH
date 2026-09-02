"""IndiGo (6E) airline-direct adapter.

See D-023 in IMPLEMENTATION_LOG.md: the structure, guards and parser contract are real,
but the parser has not been calibrated against live traffic and collection is disabled
by default. `fetch()` refuses to run unless collection is explicitly enabled.
"""
from __future__ import annotations

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


class IndiGoAdapter(BaseSourceAdapter):
    source_code = "indigo"
    source_name = "IndiGo"
    source_type = SourceType.AIRLINE_DIRECT
    adapter_version = "1.0.0"
    base_url = "https://www.goindigo.in"
    # Deliberately conservative: airline-direct pages are heavy and we have no
    # commercial relationship entitling us to volume.
    rate_limit = RateLimit(requests_per_minute=10, max_concurrency=1, backoff_seconds=4.0)

    def search_url(self, query: FareQuery) -> str:
        return (
            f"{self.base_url}/booking/flight-select"
            f"?origin={query.origin}&destination={query.destination}"
            f"&departure={query.departure_date.isoformat()}&adults=1&class=economy"
        )

    async def fetch(self, query: FareQuery) -> RawPayload:
        if not settings.collection_enabled:
            raise SourceUnavailableError(
                "live collection is disabled (settings.collection_enabled=False); "
                "the platform is serving the seeded REPLAY dataset"
            )
        return await playwright_pool.pool.render(
            self.source_code, self.search_url(query), wait_selector="[data-test=fare-card]"
        )

    def parse(self, payload: RawPayload, query: FareQuery) -> list[dict]:
        """Map fare cards onto the RawFareObservation contract.

        IndiGo quotes an all-inclusive total with the breakdown behind a fare-rules
        panel, so components arrive partially populated and the pipeline's imputation
        step reconciles them against the total.
        """
        from app.collection.adapters.parsing import parse_fare_cards

        return parse_fare_cards(
            payload=payload,
            query=query,
            source_code=self.source_code,
            airline_code="6E",
            card_selector="[data-test=fare-card]",
        )
