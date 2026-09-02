"""Stage 2.2 - Normalisation. Everything downstream assumes canonical shapes."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from app.core.constants import AvailabilityStatus, FareClass

FLIGHT_NUMBER_RE = re.compile(r"^([A-Z0-9]{2})[\s-]*(\d{1,4})$")

FARE_CLASS_ALIASES = {
    "eco": FareClass.ECONOMY, "economy": FareClass.ECONOMY, "y": FareClass.ECONOMY,
    "premium economy": FareClass.PREMIUM_ECONOMY, "premium": FareClass.PREMIUM_ECONOMY,
    "w": FareClass.PREMIUM_ECONOMY,
    "business": FareClass.BUSINESS, "biz": FareClass.BUSINESS, "j": FareClass.BUSINESS,
    "c": FareClass.BUSINESS,
}

AVAILABILITY_ALIASES = {
    "available": AvailabilityStatus.AVAILABLE,
    "limited": AvailabilityStatus.LIMITED, "few left": AvailabilityStatus.LIMITED,
    "sold out": AvailabilityStatus.SOLD_OUT, "soldout": AvailabilityStatus.SOLD_OUT,
}


def normalise_iata(code: str | None) -> str | None:
    if not code:
        return None
    cleaned = str(code).strip().upper()
    return cleaned if len(cleaned) == 3 and cleaned.isalpha() else None


def normalise_route_code(origin: str | None, destination: str | None) -> str | None:
    o, d = normalise_iata(origin), normalise_iata(destination)
    return f"{o}-{d}" if o and d and o != d else None


def normalise_flight_number(value: str | None) -> str | None:
    if not value:
        return None
    match = FLIGHT_NUMBER_RE.match(str(value).strip().upper().replace(" ", ""))
    return f"{match.group(1)}-{int(match.group(2))}" if match else None


def normalise_fare_class(value: str | None) -> FareClass:
    return FARE_CLASS_ALIASES.get(str(value or "").strip().lower(), FareClass.ECONOMY)


def normalise_availability(value: str | None, seats: int | None = None) -> AvailabilityStatus:
    mapped = AVAILABILITY_ALIASES.get(str(value or "").strip().lower())
    if mapped:
        return mapped
    if seats is None:
        return AvailabilityStatus.UNKNOWN
    if seats <= 0:
        return AvailabilityStatus.SOLD_OUT
    return AvailabilityStatus.LIMITED if seats <= 9 else AvailabilityStatus.AVAILABLE


def normalise_currency(amount: float | str | None, currency: str = "INR") -> float | None:
    """Strip formatting and reject non-INR values rather than guessing a rate.

    Applying an invented FX rate would silently corrupt the index, so an unconvertible
    amount is dropped and flagged instead.
    """
    if amount is None or str(currency).upper() != "INR":
        return None
    cleaned = re.sub(r"[^\d.]", "", str(amount))
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def normalise_timestamp(value: datetime | str | None) -> datetime | None:
    """All timestamps are stored in UTC; naive input is assumed to be IST."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if value.tzinfo is None:
        from datetime import timedelta
        return (value - timedelta(hours=5, minutes=30)).replace(tzinfo=UTC)
    return value.astimezone(UTC)


def compute_lead_days(observed_at: datetime, departure: datetime) -> int:
    return max(0, (departure.date() - observed_at.date()).days)
