"""Quality scoring: eight weighted factors producing a 0-100 confidence score.

This is what makes the platform auditable rather than merely plausible. Every observation
carries its score, the Data Explorer exposes the per-factor breakdown, and only
observations at or above the threshold enter index computation.

The scorer is pure (no DB, no I/O) so it can be golden-tested alongside the index math.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.core.constants import QualityBand

# Weights sum to 1.0. Fare consistency and completeness dominate because a fare that is
# internally contradictory is useless regardless of how trustworthy its source is.
FACTOR_WEIGHTS: dict[str, float] = {
    "completeness": 0.20,
    "source_reliability": 0.15,
    "timestamp_validity": 0.10,
    "fare_consistency": 0.20,
    "duplicate_status": 0.10,
    "route_validity": 0.10,
    "tax_consistency": 0.10,
    "availability_validity": 0.05,
}

REQUIRED_FIELDS = (
    "route_code",
    "airline_code",
    "flight_number",
    "departure_datetime",
    "observed_at",
    "total_fare",
    "base_fare",
)

# Plausible domestic one-way economy range, used as a sanity band rather than a filter.
PLAUSIBLE_MIN_FARE = 1_000.0
PLAUSIBLE_MAX_FARE = 200_000.0
TAX_TOLERANCE = 0.02  # 2% tolerance on component-sum reconciliation


@dataclass
class QualityResult:
    score: float
    band: QualityBand
    factors: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _completeness(obs: dict) -> tuple[float, str | None]:
    present = sum(1 for f in REQUIRED_FIELDS if obs.get(f) not in (None, "", 0))
    ratio = present / len(REQUIRED_FIELDS)
    missing = [f for f in REQUIRED_FIELDS if obs.get(f) in (None, "", 0)]
    return ratio, (f"missing fields: {', '.join(missing)}" if missing else None)


def _timestamp_validity(obs: dict) -> tuple[float, str | None]:
    observed_at, departure = obs.get("observed_at"), obs.get("departure_datetime")
    if not isinstance(observed_at, datetime) or not isinstance(departure, datetime):
        return 0.0, "timestamps missing or not datetimes"

    now = datetime.now(UTC)
    observed_at = observed_at if observed_at.tzinfo else observed_at.replace(tzinfo=UTC)
    departure = departure if departure.tzinfo else departure.replace(tzinfo=UTC)

    if observed_at > now:
        return 0.0, "observation timestamp is in the future"
    if departure <= observed_at:
        return 0.0, "departure is not after the observation"
    return 1.0, None


def _fare_consistency(obs: dict) -> tuple[float, str | None]:
    total = obs.get("total_fare")
    base = obs.get("base_fare")
    if not total or not base:
        return 0.0, "total or base fare missing"
    if total <= 0 or base <= 0:
        return 0.0, "non-positive fare"
    if base > total:
        return 0.0, "base fare exceeds total fare"
    if not PLAUSIBLE_MIN_FARE <= total <= PLAUSIBLE_MAX_FARE:
        return 0.3, f"total fare {total:.0f} outside plausible domestic range"
    return 1.0, None


def _tax_consistency(obs: dict) -> tuple[float, str | None]:
    """Components must reconcile to the total, which is what makes the fare-composition
    panel trustworthy rather than decorative."""
    total = obs.get("total_fare") or 0
    if total <= 0:
        return 0.0, "no total to reconcile against"
    components = sum(
        float(obs.get(k) or 0)
        for k in ("base_fare", "taxes", "udf", "airport_charges", "convenience_fee")
    )
    drift = abs(components - float(total)) / float(total)
    if drift <= TAX_TOLERANCE:
        return 1.0, None
    if drift <= 0.10:
        return 0.5, f"fare components differ from total by {drift * 100:.1f}%"
    return 0.0, f"fare components do not reconcile (off by {drift * 100:.1f}%)"


def _route_validity(obs: dict, known_routes: set[str] | None) -> tuple[float, str | None]:
    code = obs.get("route_code")
    if not code or "-" not in str(code):
        return 0.0, "route code malformed"
    origin, _, destination = str(code).partition("-")
    if len(origin) != 3 or len(destination) != 3 or origin == destination:
        return 0.0, f"route code {code} is not a valid distinct IATA pair"
    if known_routes is not None and code not in known_routes:
        # Structurally valid but outside the tracked basket: usable, not index-eligible.
        return 0.5, f"route {code} is not in the active basket"
    return 1.0, None


def _availability_validity(obs: dict) -> tuple[float, str | None]:
    seats, status = obs.get("seats_available"), obs.get("availability_status")
    if seats is None and status in (None, "UNKNOWN"):
        return 0.4, "no availability information"
    if seats is not None and (seats < 0 or seats > 500):
        return 0.0, f"implausible seat count {seats}"
    if status == "SOLD_OUT" and (seats or 0) > 0:
        return 0.2, "marked sold out but reports available seats"
    return 1.0, None


def score_observation(
    obs: dict,
    source_reliability: float = 100.0,
    is_duplicate: bool = False,
    known_routes: set[str] | None = None,
) -> QualityResult:
    """Score one observation across all eight factors."""
    notes: list[str] = []
    factors: dict[str, float] = {}

    def record(name: str, result: tuple[float, str | None]) -> None:
        value, note = result
        factors[name] = round(value, 3)
        if note:
            notes.append(note)

    record("completeness", _completeness(obs))
    record("timestamp_validity", _timestamp_validity(obs))
    record("fare_consistency", _fare_consistency(obs))
    record("tax_consistency", _tax_consistency(obs))
    record("route_validity", _route_validity(obs, known_routes))
    record("availability_validity", _availability_validity(obs))

    factors["source_reliability"] = round(max(0.0, min(source_reliability / 100.0, 1.0)), 3)
    factors["duplicate_status"] = 0.0 if is_duplicate else 1.0
    if is_duplicate:
        notes.append("duplicate of an existing observation")

    score = round(sum(FACTOR_WEIGHTS[name] * value for name, value in factors.items()) * 100.0, 2)
    return QualityResult(score=score, band=QualityBand.from_score(score), factors=factors, notes=notes)
