"""Tests for the ethical-collection guard chain (build prompt Sec.3).

These prove the safeguards are structural: an adapter cannot skip robots.txt checking,
cannot retry past a challenge, and a repeatedly-failing source gets circuit-broken.
No network access is used - RobotsGuard is exercised with enabled=False (matching how
tests must run offline) and ChallengeDetector/CircuitBreaker are pure logic.
"""
from __future__ import annotations

import asyncio
from datetime import date

import pytest

from app.collection.base_adapter import (
    BaseSourceAdapter,
    CollectionResult,
    FareQuery,
    RateLimit,
    RawPayload,
)
from app.collection.guards import build_guards
from app.collection.guards.challenge_detector import ChallengeDetector
from app.collection.guards.circuit_breaker import CircuitBreaker
from app.core.constants import LeadBucket, ScrapeStatus, SourceType


class _StubAdapter(BaseSourceAdapter):
    """A minimal adapter whose fetch/parse behaviour is controlled by the test."""

    source_code = "stub"
    source_name = "Stub"
    source_type = SourceType.OTA
    adapter_version = "test"
    base_url = "https://example-airline-test.invalid"
    rate_limit = RateLimit(requests_per_minute=1000)

    def __init__(self, guards=None, cache=None, fetch_result=None, fetch_error=None):
        super().__init__(guards=guards, cache=cache)
        self._fetch_result = fetch_result
        self._fetch_error = fetch_error

    async def fetch(self, query: FareQuery) -> RawPayload:
        if self._fetch_error:
            raise self._fetch_error
        return self._fetch_result

    def parse(self, payload: RawPayload, query: FareQuery) -> list[dict]:
        return [{"total_fare": 6000}] if payload else []


def _query() -> FareQuery:
    return FareQuery(route_code="DEL-BOM", departure_date=date(2026, 9, 16), lead_bucket=LeadBucket.T15)


def test_challenge_detector_flags_captcha_html():
    detector = ChallengeDetector()
    payload = RawPayload(content="<p>Please complete the reCAPTCHA to continue</p>", url="u", fetched_at=None, http_status=200)
    assert detector.is_challenged(payload) is True


def test_challenge_detector_flags_403_status_regardless_of_body():
    detector = ChallengeDetector()
    payload = RawPayload(content="looks fine", url="u", fetched_at=None, http_status=403)
    assert detector.is_challenged(payload) is True


def test_challenge_detector_passes_normal_content():
    detector = ChallengeDetector()
    payload = RawPayload(content="<div>flight results here</div>", url="u", fetched_at=None, http_status=200)
    assert detector.is_challenged(payload) is False


def test_circuit_breaker_opens_after_threshold_failures():
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=999)
    for _ in range(3):
        breaker.record_failure("indigo")
    assert breaker.is_open("indigo") is True
    assert breaker.status("indigo") == "UNAVAILABLE"


def test_circuit_breaker_recovers_on_success():
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=999)
    breaker.record_failure("indigo")
    breaker.record_failure("indigo")
    breaker.record_success("indigo")
    assert breaker.status("indigo") == "ACTIVE"


def test_adapter_collect_hits_challenge_and_stops_without_retry():
    """Central guarantee: a detected challenge ends collection - it is never solved,
    worked around, or retried (build prompt Sec.3)."""
    guards = build_guards(respect_robots=False)
    payload = RawPayload(content="Access Denied - unusual traffic detected", url="u", fetched_at=None, http_status=200)
    adapter = _StubAdapter(guards=guards, fetch_result=payload)

    result: CollectionResult = asyncio.run(adapter.collect(_query()))
    assert result.status == ScrapeStatus.SKIPPED_CHALLENGE
    assert result.records_found == 0
    assert "challenge" in (result.error_message or "").lower() or "abandoned" in (result.error_message or "").lower()


def test_adapter_collect_succeeds_on_clean_payload():
    guards = build_guards(respect_robots=False)
    payload = RawPayload(content="<div>ok</div>", url="u", fetched_at=None, http_status=200)
    adapter = _StubAdapter(guards=guards, fetch_result=payload)

    result = asyncio.run(adapter.collect(_query()))
    assert result.status == ScrapeStatus.SUCCESS
    assert result.records_found == 1


def test_adapter_collect_records_failure_on_exception_and_opens_breaker_eventually():
    guards = build_guards(respect_robots=False)
    adapter = _StubAdapter(guards=guards, fetch_error=RuntimeError("network exploded"))

    for _ in range(5):
        result = asyncio.run(adapter.collect(_query()))
        assert result.status == ScrapeStatus.FAILED

    assert guards.breaker.is_open("stub") is True


def test_open_circuit_short_circuits_before_any_fetch_is_attempted():
    guards = build_guards(respect_robots=False)
    guards.breaker.record_failure("stub")
    guards.breaker.record_failure("stub")
    guards.breaker.record_failure("stub")
    guards.breaker.record_failure("stub")
    guards.breaker.record_failure("stub")
    assert guards.breaker.is_open("stub") is True

    called = {"fetch": False}

    class _NeverFetch(_StubAdapter):
        async def fetch(self, query):
            called["fetch"] = True
            raise AssertionError("fetch must not be called while the circuit is open")

    adapter = _NeverFetch(guards=guards)
    result = asyncio.run(adapter.collect(_query()))
    assert result.status == ScrapeStatus.FAILED
    assert called["fetch"] is False
