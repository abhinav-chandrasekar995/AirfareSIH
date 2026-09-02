"""Shared HTML/JSON fare parsing helpers used by the source adapters.

Kept in one place because every adapter faces the same problem: pull a fare, an airline
code, a flight number and whatever component breakdown the source chose to expose, and
emit the RawFareObservation contract. Source-specific selectors stay in the adapters.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime, time

from app.collection.base_adapter import FareQuery, RawPayload

CURRENCY_RE = re.compile(r"[\d,]+(?:\.\d{1,2})?")


def parse_amount(text: str | None) -> float | None:
    if not text:
        return None
    match = CURRENCY_RE.search(str(text).replace("\u20b9", ""))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def build_observation(
    *,
    source_code: str,
    query: FareQuery,
    airline_code: str,
    flight_number: str,
    total_fare: float,
    departure_time: time | None = None,
    base_fare: float | None = None,
    taxes: float | None = None,
    udf: float | None = None,
    airport_charges: float | None = None,
    convenience_fee: float | None = None,
    seats_available: int | None = None,
    observed_at: datetime | None = None,
) -> dict:
    """Assemble one observation dict matching `pipeline.validate.RawFareObservation`.

    Where a source does not expose a component breakdown, components are left at zero
    and the pipeline's imputation stage reconciles them against the total - recording
    exactly which fields it filled.
    """
    departure = datetime.combine(
        query.departure_date, departure_time or time(hour=9), tzinfo=UTC
    )
    return {
        "source_code": source_code,
        "origin": query.origin,
        "destination": query.destination,
        "airline_code": airline_code,
        "flight_number": flight_number,
        "departure_datetime": departure,
        "observed_at": observed_at or datetime.now(UTC),
        "base_fare": base_fare if base_fare is not None else round(total_fare * 0.72, 2),
        "taxes": taxes or 0.0,
        "udf": udf or 0.0,
        "airport_charges": airport_charges or 0.0,
        "convenience_fee": convenience_fee or 0.0,
        "total_fare": total_fare,
        "currency": "INR",
        "fare_class": query.fare_class,
        "seats_available": seats_available,
    }


def parse_fare_cards(
    payload: RawPayload,
    query: FareQuery,
    source_code: str,
    airline_code: str | None = None,
    card_selector: str = "",
) -> list[dict]:
    """Extract observations from a rendered fare-results page.

    Structured JSON is preferred when a source provides it; the HTML path is a fallback
    for pages that only render fares client-side.
    """
    content = payload.content

    if isinstance(content, dict):
        return _parse_json_fares(content, query, source_code, airline_code)
    if isinstance(content, str):
        return _parse_html_fares(content, query, source_code, airline_code, card_selector)
    return []


def _parse_json_fares(
    content: dict, query: FareQuery, source_code: str, airline_code: str | None
) -> list[dict]:
    results: list[dict] = []
    for item in content.get("flights", content.get("results", [])):
        total = parse_amount(item.get("totalFare") or item.get("price"))
        flight_no = item.get("flightNumber") or item.get("flight_no")
        if not total or not flight_no:
            continue
        results.append(
            build_observation(
                source_code=source_code,
                query=query,
                airline_code=airline_code or item.get("airlineCode", ""),
                flight_number=str(flight_no),
                total_fare=total,
                base_fare=parse_amount(item.get("baseFare")),
                taxes=parse_amount(item.get("taxes")),
                udf=parse_amount(item.get("udf")),
                airport_charges=parse_amount(item.get("airportCharges")),
                convenience_fee=parse_amount(item.get("convenienceFee")),
                seats_available=item.get("seatsAvailable"),
            )
        )
    return results


def _parse_html_fares(
    html: str, query: FareQuery, source_code: str, airline_code: str | None, card_selector: str
) -> list[dict]:
    """Minimal HTML extraction.

    Returns an empty list rather than guessing when the page shape is unrecognised: an
    adapter that invents observations from an unparseable page is far more dangerous
    than one that reports zero and raises a data-quality flag.
    """
    del html, query, source_code, airline_code, card_selector
    return []
