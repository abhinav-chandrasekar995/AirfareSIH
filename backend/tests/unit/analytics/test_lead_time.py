"""Lead-time curve, elasticity and premium tests."""
from __future__ import annotations

from app.analytics.lead_time import (
    booking_pressure,
    build_curve,
    estimate_elasticity,
    last_minute_premium,
)
from app.core.constants import Band, LeadBucket


def _fixture_curve():
    fares = {
        LeadBucket.T45: [5200.0] * 6,
        LeadBucket.T30: [5600.0] * 6,
        LeadBucket.T15: [6300.0] * 6,
        LeadBucket.T7: [7900.0] * 6,
        LeadBucket.T1: [11800.0] * 6,
    }
    return build_curve(fares)


def test_curve_is_ordered_earliest_to_latest():
    curve = _fixture_curve()
    assert [p.lead_bucket for p in curve] == [LeadBucket.T45, LeadBucket.T30, LeadBucket.T15, LeadBucket.T7, LeadBucket.T1]


def test_curve_is_monotonically_increasing_toward_departure():
    curve = _fixture_curve()
    values = [p.avg_fare for p in curve]
    assert values == sorted(values)


def test_last_minute_premium_matches_source_spec_example():
    """Values mirror the source spec's worked example (T+45=5200, T+1=11800)."""
    curve = _fixture_curve()
    premium = last_minute_premium(curve)
    assert premium == round((11800 - 5200) / 5200 * 100, 2)


def test_booking_pressure_bands_high_premium_as_high():
    assert booking_pressure(126.9) == Band.HIGH
    assert booking_pressure(50.0) == Band.MEDIUM
    assert booking_pressure(10.0) == Band.LOW
    assert booking_pressure(None) is None


def test_elasticity_is_negative_for_a_normal_rising_curve():
    """Fares rise as lead time shrinks, so elasticity (fare vs lead_days) is negative."""
    curve = _fixture_curve()
    elasticity = estimate_elasticity(curve)
    assert elasticity is not None
    assert elasticity < 0


def test_elasticity_requires_at_least_three_points():
    from app.analytics.lead_time.curve import LeadTimePoint

    short_curve = [LeadTimePoint(LeadBucket.T45, 45, 5200.0, 6), LeadTimePoint(LeadBucket.T1, 1, 11800.0, 6)]
    assert estimate_elasticity(short_curve) is None
