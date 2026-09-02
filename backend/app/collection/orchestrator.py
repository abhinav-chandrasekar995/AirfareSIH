"""Stage 1 orchestration: builds the collection work matrix and dispatches adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.collection.base_adapter import CollectionResult, FareQuery
from app.collection.guards import build_guards
from app.collection.registry import fallback_for, get_adapter
from app.core.constants import LeadBucket, ScrapeStatus


@dataclass
class OrchestrationPlan:
    queries: list[tuple[str, FareQuery]]

    def __len__(self) -> int:
        return len(self.queries)


def build_work_matrix(
    route_codes: list[str],
    source_codes: list[str],
    reference_date: date | None = None,
) -> OrchestrationPlan:
    """routes x lead-time windows x sources.

    Each of the five windows is collected as a departure date that is exactly that many
    days ahead, which is what makes the five buckets comparable across routes and days.
    """
    today = reference_date or date.today()
    queries: list[tuple[str, FareQuery]] = []
    for source_code in source_codes:
        for route_code in route_codes:
            for bucket in LeadBucket.ordered():
                queries.append(
                    (
                        source_code,
                        FareQuery(
                            route_code=route_code,
                            departure_date=today + timedelta(days=bucket.days),
                            lead_bucket=bucket,
                        ),
                    )
                )
    return OrchestrationPlan(queries=queries)


class ScrapingOrchestrator:
    """Dispatches guarded collection and applies the source-fallback policy."""

    def __init__(self, redis=None, cache=None, respect_robots: bool = True) -> None:
        self.guards = build_guards(redis=redis, respect_robots=respect_robots)
        self.cache = cache

    async def collect_one(self, source_code: str, query: FareQuery) -> CollectionResult:
        adapter = get_adapter(source_code)(guards=self.guards, cache=self.cache)
        return await adapter.collect(query)

    async def collect_with_fallback(
        self,
        source_code: str,
        query: FareQuery,
        available_sources: set[str],
    ) -> tuple[CollectionResult, str | None]:
        """SOURCE DOWN -> FALLBACK SOURCE -> DATA QUALITY FLAG -> INDEX CONTINUES.

        Returns the result plus a data-quality flag description when a fallback was
        used, so the substitution is recorded rather than hidden.
        """
        result = await self.collect_one(source_code, query)
        if result.status in (ScrapeStatus.SUCCESS, ScrapeStatus.PARTIAL):
            return result, None

        fallback = fallback_for(source_code, available_sources)
        if not fallback:
            return result, (
                f"Source '{source_code}' unavailable ({result.status.value}) and no "
                f"fallback source is available for {query.route_code}. Coverage reduced."
            )

        fallback_result = await self.collect_one(fallback, query)
        return fallback_result, (
            f"Source '{source_code}' unavailable ({result.status.value}); fell back to "
            f"'{fallback}' for {query.route_code} {query.lead_bucket.value}."
        )
