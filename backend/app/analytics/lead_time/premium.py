"""Last-minute premium, early-booking advantage, and booking pressure banding."""
from __future__ import annotations

from app.analytics.lead_time.curve import LeadTimePoint, curve_as_dict
from app.core.constants import Band, LeadBucket


def last_minute_premium(points: list[LeadTimePoint]) -> float | None:
    """Percentage uplift of the T+1 fare over the T+45 fare."""
    curve = curve_as_dict(points)
    earliest, latest = curve.get(LeadBucket.T45), curve.get(LeadBucket.T1)
    if not earliest or not latest or earliest <= 0:
        return None
    return round((latest - earliest) / earliest * 100.0, 2)


def early_booking_advantage(points: list[LeadTimePoint]) -> float | None:
    """Percentage saved by booking at T+45 instead of T+1."""
    curve = curve_as_dict(points)
    earliest, latest = curve.get(LeadBucket.T45), curve.get(LeadBucket.T1)
    if not earliest or not latest or latest <= 0:
        return None
    return round((latest - earliest) / latest * 100.0, 2)


def booking_pressure(premium_pct: float | None) -> Band | None:
    """Band the last-minute premium. Thresholds are conservative and documented."""
    if premium_pct is None:
        return None
    if premium_pct >= 90:
        return Band.HIGH
    if premium_pct >= 45:
        return Band.MEDIUM
    return Band.LOW
