"""Source adapter base class.

ARCHITECTURE DECISION (ADR-004 / build prompt Sec.3): the ethical safeguards live in
`collect()`, which subclasses do NOT override. Adapters implement only `fetch()` and
`parse()`. Compliance that depends on each contributor remembering to add a robots check
will eventually fail; making it structural means an adapter that skips it cannot be
written.

The guard chain, in order:
    robots.txt -> rate limit -> circuit breaker -> cache -> fetch
    -> challenge detection -> parse -> schema validation -> audit record

Explicitly out of scope by design: CAPTCHA solving, credentialed login to gated fare
inventory, proxy rotation for evasion, ignoring Retry-After. Where a source cannot be
collected ethically it is not collected, and the index reports reduced coverage rather
than substituting silently.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from app.core.constants import LeadBucket, ScrapeStatus, SourceType


@dataclass(frozen=True)
class RateLimit:
    requests_per_minute: int = 20
    max_concurrency: int = 2
    backoff_seconds: float = 2.0


@dataclass(frozen=True)
class FareQuery:
    """One unit of collection work: a route, a departure date, and a booking window."""

    route_code: str
    departure_date: date
    lead_bucket: LeadBucket
    fare_class: str = "ECONOMY"

    @property
    def origin(self) -> str:
        return self.route_code.split("-")[0]

    @property
    def destination(self) -> str:
        return self.route_code.split("-")[1]


@dataclass
class RawPayload:
    content: object
    url: str
    fetched_at: datetime
    http_status: int | None = None


@dataclass
class CollectionResult:
    source_code: str
    status: ScrapeStatus
    observations: list[dict] = field(default_factory=list)
    records_found: int = 0
    records_valid: int = 0
    records_failed: int = 0
    latency_ms: int = 0
    error_message: str | None = None
    adapter_version: str = "0.0.0"


class SourceUnavailableError(Exception):
    """Raised when a source cannot be collected from ethically or at all."""


class BaseSourceAdapter(ABC):
    source_code: str = "base"
    source_name: str = "Base"
    source_type: SourceType = SourceType.OTA
    adapter_version: str = "1.0.0"
    base_url: str = ""
    rate_limit: RateLimit = RateLimit()

    def __init__(self, guards=None, cache=None) -> None:
        # Guards are injected so tests can assert the chain ran without network access.
        self.guards = guards
        self.cache = cache

    # ------------------------------------------------------------------ contract
    @abstractmethod
    async def fetch(self, query: FareQuery) -> RawPayload:
        """Retrieve the source response for one query."""

    @abstractmethod
    def parse(self, payload: RawPayload, query: FareQuery) -> list[dict]:
        """Turn a source response into RawFareObservation-shaped dicts."""

    # ------------------------------------------------------------------ final
    async def collect(self, query: FareQuery) -> CollectionResult:
        """Run the full guarded collection. Deliberately not overridable."""
        started = time.monotonic()
        result = CollectionResult(
            source_code=self.source_code,
            status=ScrapeStatus.RUNNING,
            adapter_version=self.adapter_version,
        )

        try:
            # 1. robots.txt. A disallowed path is not fetched, full stop.
            if self.guards and not await self.guards.robots.is_allowed(self.base_url, self.source_code):
                result.status = ScrapeStatus.SKIPPED_ROBOTS
                result.error_message = (
                    f"robots.txt disallows collection from {self.source_code}; skipped"
                )
                return result

            # 2. Circuit breaker: stop hammering a source that is already failing.
            if self.guards and self.guards.breaker.is_open(self.source_code):
                raise SourceUnavailableError(f"circuit breaker open for {self.source_code}")

            # 3. Rate limit, shared across all workers via Redis.
            if self.guards:
                await self.guards.limiter.acquire(self.source_code, self.rate_limit.requests_per_minute)

            # 4. Cache: never re-request what we already have.
            cache_key = f"scrape:{self.source_code}:{query.route_code}:{query.departure_date}:{query.lead_bucket.value}"
            payload = None
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached is not None:
                    payload = RawPayload(cached, self.base_url, datetime.now(UTC))

            # 5. Fetch.
            if payload is None:
                payload = await self.fetch(query)
                if self.cache:
                    await self.cache.set_json(cache_key, payload.content, ttl=1800)

            # 6. Challenge detection. A CAPTCHA or login wall ends collection for this
            #    source - it is never solved, worked around, or retried.
            if self.guards and self.guards.challenge.is_challenged(payload):
                if self.guards:
                    self.guards.breaker.record_failure(self.source_code)
                result.status = ScrapeStatus.SKIPPED_CHALLENGE
                result.error_message = (
                    f"{self.source_code} returned an anti-bot challenge; collection "
                    f"abandoned for this source (no bypass attempted)"
                )
                return result

            # 7. Parse.
            observations = self.parse(payload, query)
            result.records_found = len(observations)
            result.observations = observations
            result.records_valid = len(observations)
            result.status = ScrapeStatus.SUCCESS if observations else ScrapeStatus.PARTIAL

            if self.guards:
                self.guards.breaker.record_success(self.source_code)

        except SourceUnavailableError as exc:
            result.status = ScrapeStatus.FAILED
            result.error_message = str(exc)
        except Exception as exc:
            if self.guards:
                self.guards.breaker.record_failure(self.source_code)
            result.status = ScrapeStatus.FAILED
            result.error_message = f"{type(exc).__name__}: {exc}"
            result.records_failed = 1
        finally:
            result.latency_ms = int((time.monotonic() - started) * 1000)

        return result
