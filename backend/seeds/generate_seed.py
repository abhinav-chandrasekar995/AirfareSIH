"""Deterministic seed dataset generator.

Build prompt Sec.33 requires the platform be fully demonstrable with external network
access disabled. This script produces the REPLAY dataset that makes that true.

Determinism matters as much as coverage: with a fixed RNG seed the demo shows the same
numbers every time it is loaded, so a rehearsed walkthrough stays valid and a judge who
recomputes a figure gets the same answer twice.

The generator produces *observations*, not results. Index values, anomalies, curves and
forecasts are then computed from those observations by the same analytics code the live
pipeline uses - so the seeded platform exercises the real statistical path rather than
displaying pre-baked numbers.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

SEED = 20260901
random.seed(SEED)

HISTORY_DAYS = 400  # long enough for a 90-day out-of-sample back-test plus YoY context
# The base period must sit INSIDE the generated history, otherwise no route has a base
# measure and the index cannot be computed at all. Anchored 12 months before the end of
# the window so year-on-year comparisons line up on the same calendar month.
BASE_PERIOD = date(2025, 9, 1)
BASE_WINDOW_DAYS = 30

# ---------------------------------------------------------------- reference data

AIRPORTS = [
    ("DEL", "Indira Gandhi International", "Delhi", "Delhi", "NORTH", 28.5562, 77.1000),
    ("BOM", "Chhatrapati Shivaji Maharaj International", "Mumbai", "Maharashtra", "WEST", 19.0896, 72.8656),
    ("BLR", "Kempegowda International", "Bengaluru", "Karnataka", "SOUTH", 13.1986, 77.7066),
    ("MAA", "Chennai International", "Chennai", "Tamil Nadu", "SOUTH", 12.9941, 80.1709),
    ("CCU", "Netaji Subhas Chandra Bose International", "Kolkata", "West Bengal", "EAST", 22.6547, 88.4467),
    ("HYD", "Rajiv Gandhi International", "Hyderabad", "Telangana", "SOUTH", 17.2403, 78.4294),
    ("GOI", "Goa International (Dabolim)", "Goa", "Goa", "WEST", 15.3808, 73.8314),
    ("PNQ", "Pune Airport", "Pune", "Maharashtra", "WEST", 18.5821, 73.9197),
    ("AMD", "Sardar Vallabhbhai Patel International", "Ahmedabad", "Gujarat", "WEST", 23.0772, 72.6347),
    ("COK", "Cochin International", "Kochi", "Kerala", "SOUTH", 10.1520, 76.4019),
    ("LKO", "Chaudhary Charan Singh International", "Lucknow", "Uttar Pradesh", "NORTH", 26.7606, 80.8893),
    ("JAI", "Jaipur International", "Jaipur", "Rajasthan", "NORTH", 26.8242, 75.8122),
    ("SXR", "Sheikh ul-Alam International", "Srinagar", "Jammu and Kashmir", "NORTH", 33.9871, 74.7742),
    ("GAU", "Lokpriya Gopinath Bordoloi International", "Guwahati", "Assam", "NORTHEAST", 26.1061, 91.5859),
    ("BBI", "Biju Patnaik International", "Bhubaneswar", "Odisha", "EAST", 20.2444, 85.8178),
    ("NAG", "Dr. Babasaheb Ambedkar International", "Nagpur", "Maharashtra", "CENTRAL", 21.0922, 79.0472),
]

AIRLINES = [
    ("6E", "IndiGo", "LCC", 0.62),
    ("AI", "Air India", "FSC", 0.13),
    ("IX", "Air India Express", "LCC", 0.09),
    ("QP", "Akasa Air", "LCC", 0.08),
    ("SG", "SpiceJet", "LCC", 0.08),
]

SOURCES = [
    ("indigo", "IndiGo", "AIRLINE_DIRECT", "https://www.goindigo.in", 10, 99.2),
    ("airindia", "Air India", "AIRLINE_DIRECT", "https://www.airindia.com", 8, 97.5),
    ("akasa", "Akasa Air", "AIRLINE_DIRECT", "https://www.akasaair.com", 10, 98.1),
    ("makemytrip", "MakeMyTrip", "OTA", "https://www.makemytrip.com", 12, 96.4),
    ("goibibo", "Goibibo", "OTA", "https://www.goibibo.com", 12, 95.8),
    ("cleartrip", "Cleartrip", "OTA", "https://www.cleartrip.com", 12, 94.9),
    ("yatra", "Yatra", "OTA", "https://www.yatra.com", 12, 93.2),
    ("easemytrip", "EaseMyTrip", "OTA", "https://www.easemytrip.com", 12, 92.6),
]

# route_code, distance_km, region, DGCA-traffic-derived weight
ROUTES = [
    ("DEL-BOM", 1138, "NORTH-WEST", 0.180),
    ("DEL-BLR", 1712, "NORTH-SOUTH", 0.150),
    ("BOM-BLR", 842, "WEST-SOUTH", 0.120),
    ("DEL-CCU", 1305, "NORTH-EAST", 0.090),
    ("BLR-HYD", 500, "SOUTH", 0.080),
    ("MAA-DEL", 1760, "SOUTH-NORTH", 0.070),
    ("BOM-GOI", 424, "WEST", 0.055),
    ("DEL-HYD", 1256, "NORTH-SOUTH", 0.050),
    ("BOM-AMD", 441, "WEST", 0.045),
    ("BLR-MAA", 284, "SOUTH", 0.040),
    ("DEL-JAI", 241, "NORTH", 0.035),
    ("BOM-COK", 1080, "WEST-SOUTH", 0.030),
    ("DEL-SXR", 640, "NORTH", 0.022),
    ("CCU-GAU", 519, "EAST-NORTHEAST", 0.018),
    ("DEL-LKO", 420, "NORTH", 0.015),
]

EVENTS = [
    ("Diwali", "FESTIVAL", date(2025, 10, 18), date(2025, 10, 24)),
    ("Christmas and New Year", "TRAVEL_PEAK", date(2025, 12, 20), date(2026, 1, 2)),
    ("Republic Day long weekend", "LONG_WEEKEND", date(2026, 1, 24), date(2026, 1, 26)),
    ("Holi", "FESTIVAL", date(2026, 3, 3), date(2026, 3, 5)),
    ("Summer travel peak", "SEASONAL", date(2026, 5, 1), date(2026, 6, 15)),
    ("Independence Day long weekend", "LONG_WEEKEND", date(2026, 8, 15), date(2026, 8, 17)),
    ("Onam", "FESTIVAL", date(2026, 8, 26), date(2026, 8, 29)),
]

# Lead-time multipliers applied to the route's baseline fare. Shape is monotonic and
# steepens sharply inside a week, which is the effect the module exists to measure.
LEAD_MULTIPLIERS = {"T45": 0.86, "T30": 0.93, "T15": 1.05, "T7": 1.32, "T1": 1.96}

# Baseline one-way economy fare per route at T+30, in INR.
BASE_FARES = {
    "DEL-BOM": 6100, "DEL-BLR": 6800, "BOM-BLR": 5200, "DEL-CCU": 6400,
    "BLR-HYD": 3400, "MAA-DEL": 7100, "BOM-GOI": 3900, "DEL-HYD": 5900,
    "BOM-AMD": 3200, "BLR-MAA": 2900, "DEL-JAI": 2600, "BOM-COK": 5600,
    "DEL-SXR": 5400, "CCU-GAU": 3800, "DEL-LKO": 3100,
}

SOURCE_MARKUP = {
    "indigo": 1.000, "airindia": 1.000, "akasa": 1.000,
    "makemytrip": 1.024, "goibibo": 0.997, "cleartrip": 1.016,
    "yatra": 1.035, "easemytrip": 1.008,
}

# Engineered demo anomalies: genuine, explainable deviations across several routes,
# lead-time windows and severities (including one price DROP), so the Anomaly
# Intelligence page has more than a single data point to demonstrate against. Each
# entry is (route_code, affected lead buckets, day-offset window from "today",
# multiplier applied to the baseline fare). A multiplier > 1 is a surge, < 1 is a drop.
ENGINEERED_ANOMALIES: list[tuple[str, tuple[str, ...], int, float]] = [
    ("DEL-BOM", ("T15", "T7"), 3, 1.68),    # CRITICAL surge - short booking window, high pressure
    ("BOM-GOI", ("T7", "T1"), 2, 1.52),     # HIGH surge - leisure route, last-minute premium spike
    ("DEL-SXR", ("T15",), 4, 1.41),         # HIGH surge - single window, still clears the threshold
    ("BLR-HYD", ("T30",), 5, 1.29),         # MEDIUM surge - early-window pressure
    ("BOM-COK", ("T15", "T7"), 3, 0.74),    # price DROP - a genuine promotional dip, not just surges
    ("CCU-GAU", ("T7",), 2, 1.31),          # MEDIUM surge on an East-Northeast route
]


@dataclass
class GeneratedObservation:
    observed_at: datetime
    route_code: str
    airline_code: str
    source_code: str
    flight_number: str
    departure_datetime: datetime
    lead_days: int
    lead_bucket: str
    fare_class: str
    base_fare: float
    taxes: float
    udf: float
    airport_charges: float
    convenience_fee: float
    total_fare: float
    seats_available: int
    availability_status: str


def _event_multiplier(day: date) -> float:
    """Fares lift near and during travel events."""
    for _name, _kind, start, end in EVENTS:
        if start <= day <= end:
            return 1.34
        days_before = (start - day).days
        if 0 < days_before <= 14:
            return 1.0 + 0.20 * (1 - days_before / 14)
    return 1.0


def _seasonal_multiplier(day: date) -> float:
    """Smooth annual cycle: summer and winter peaks, monsoon trough."""
    return 1.0 + 0.07 * math.sin(2 * math.pi * (day.timetuple().tm_yday - 80) / 365.25)


def _weekend_multiplier(day: date) -> float:
    return 1.11 if day.weekday() in (4, 6) else 1.0  # Friday and Sunday


def _trend_multiplier(day: date, today: date) -> float:
    """Gentle upward drift so year-on-year comparisons are meaningful."""
    return 1.0 + 0.00022 * (HISTORY_DAYS - (today - day).days)


def decompose(total: float, source_code: str) -> tuple[float, float, float, float, float]:
    """Split a consumer total into its regulated components.

    Shares approximate the real structure of an Indian domestic fare: base fare,
    GST-bearing taxes, the airport User Development Fee, other airport charges, and an
    OTA convenience fee that airline-direct channels do not levy.
    """
    convenience = round(total * 0.028, 2) if SOURCE_MARKUP[source_code] != 1.000 else 0.0
    remainder = total - convenience
    base = round(remainder * 0.712, 2)
    taxes = round(remainder * 0.148, 2)
    udf = round(remainder * 0.083, 2)
    charges = round(remainder - base - taxes - udf, 2)
    return base, taxes, udf, charges, convenience


def generate_observations(today: date | None = None) -> list[GeneratedObservation]:
    """Produce the full observation history across routes, windows, airlines, sources."""
    today = today or date.today()
    rng = random.Random(SEED)
    observations: list[GeneratedObservation] = []

    airline_codes = [a[0] for a in AIRLINES]
    airline_weights = [a[3] for a in AIRLINES]
    source_codes = [s[0] for s in SOURCES]

    for route_code, _dist, _region, _weight in ROUTES:
        baseline = BASE_FARES[route_code]

        for day_offset in range(HISTORY_DAYS, -1, -1):
            observed_day = today - timedelta(days=day_offset)

            for bucket, lead_mult in LEAD_MULTIPLIERS.items():
                lead_days = {"T1": 1, "T7": 7, "T15": 15, "T30": 30, "T45": 45}[bucket]
                departure_day = observed_day + timedelta(days=lead_days)

                context = (
                    _seasonal_multiplier(departure_day)
                    * _event_multiplier(departure_day)
                    * _weekend_multiplier(departure_day)
                    * _trend_multiplier(observed_day, today)
                )

                # Engineered anomalies: apply whichever configured deviation (if any)
                # matches this route/window/day combination.
                surge = 1.0
                for anomaly_route, anomaly_buckets, day_window, multiplier in ENGINEERED_ANOMALIES:
                    if (
                        route_code == anomaly_route
                        and bucket in anomaly_buckets
                        and 0 <= (today - observed_day).days <= day_window
                    ):
                        surge = multiplier
                        break

                # Two carriers and two sources per (route, day, window): enough to clear
                # the minimum-observation threshold without inflating the dataset.
                for airline_code in rng.choices(airline_codes, weights=airline_weights, k=2):
                    for source_code in rng.sample(source_codes, k=2):
                        noise = rng.gauss(1.0, 0.055)
                        carrier_factor = 1.09 if airline_code == "AI" else 1.0
                        total = (
                            baseline * lead_mult * context * surge
                            * SOURCE_MARKUP[source_code] * carrier_factor * noise
                        )
                        total = round(max(1200.0, total), 2)

                        base, taxes, udf, charges, convenience = decompose(total, source_code)
                        seats = max(1, int(rng.gauss(28, 14))) if bucket != "T1" else rng.randint(1, 8)

                        observations.append(
                            GeneratedObservation(
                                observed_at=datetime.combine(
                                    observed_day, time(hour=rng.randint(6, 21)), tzinfo=timezone.utc
                                ),
                                route_code=route_code,
                                airline_code=airline_code,
                                source_code=source_code,
                                flight_number=f"{airline_code}-{rng.randint(100, 9999)}",
                                departure_datetime=datetime.combine(
                                    departure_day, time(hour=rng.randint(5, 22)), tzinfo=timezone.utc
                                ),
                                lead_days=lead_days,
                                lead_bucket=bucket,
                                fare_class="ECONOMY",
                                base_fare=base,
                                taxes=taxes,
                                udf=udf,
                                airport_charges=charges,
                                convenience_fee=convenience,
                                total_fare=total,
                                seats_available=seats,
                                availability_status=(
                                    "LIMITED" if seats <= 9 else "AVAILABLE"
                                ),
                            )
                        )

    return observations


def summarise(observations: list[GeneratedObservation]) -> dict:
    routes = {o.route_code for o in observations}
    return {
        "observations": len(observations),
        "routes": len(routes),
        "airlines": len({o.airline_code for o in observations}),
        "sources": len({o.source_code for o in observations}),
        "lead_buckets": sorted({o.lead_bucket for o in observations}),
        "date_from": min(o.observed_at for o in observations).date().isoformat(),
        "date_to": max(o.observed_at for o in observations).date().isoformat(),
        "seed": SEED,
    }


if __name__ == "__main__":
    generated = generate_observations()
    for key, value in summarise(generated).items():
        print(f"{key:16s} {value}")
