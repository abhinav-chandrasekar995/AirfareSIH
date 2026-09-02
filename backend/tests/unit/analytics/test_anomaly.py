"""Anomaly baseline, severity, attribution and scraper-vs-market separation tests."""
from __future__ import annotations

import pytest

from app.analytics.anomaly import (
    AttributionContext,
    attribute,
    build_baseline,
    check_batch,
    classify_severity,
    deviation_pct,
    run_detectors,
)
from app.core.constants import LeadBucket


def test_baseline_requires_minimum_history():
    assert build_baseline([6000.0, 6100.0]) is None


def test_baseline_expected_fare_is_the_median():
    history = [6000.0, 6200.0, 5800.0, 6100.0, 5950.0]
    baseline = build_baseline(history)
    assert baseline.expected_fare == 6000.0


def test_deviation_and_severity_for_del_bom_surge_example():
    """Mirrors the source spec's worked example: expected 6200, observed 10450."""
    dev = deviation_pct(10450, 6200)
    assert dev == pytest.approx(68.55, abs=0.1)
    assert classify_severity(dev) == "CRITICAL"


def test_severity_bands_are_ordered():
    assert classify_severity(15) == "LOW"
    assert classify_severity(25) == "MEDIUM"
    assert classify_severity(40) == "HIGH"
    assert classify_severity(70) == "CRITICAL"
    # Deviation is judged on magnitude, not direction.
    assert classify_severity(-70) == "CRITICAL"


def test_deviation_pct_rejects_non_positive_expected_fare():
    with pytest.raises(ValueError):
        deviation_pct(1000, 0)


def test_attribution_always_sums_to_100():
    ctx = AttributionContext(is_weekend=True, seats_available=4, days_to_event=3, lead_days=2)
    factors = attribute(ctx)
    assert sum(f.pct for f in factors) == pytest.approx(100.0, abs=0.01)


def test_attribution_with_no_known_factors_is_fully_unexplained():
    factors = attribute(AttributionContext())
    assert len(factors) == 1
    assert factors[0].factor == "unexplained"
    assert factors[0].pct == 100.0


def test_detectors_fire_on_a_clear_outlier():
    history = [6000.0, 6100.0, 5950.0, 6050.0, 5980.0, 6020.0, 6070.0, 5990.0, 6010.0, 6040.0,
               6030.0, 5970.0, 6060.0, 6000.0, 5960.0, 6080.0, 5940.0, 6110.0, 5920.0, 6120.0]
    fired = run_detectors(15000.0, history)
    assert "zscore" in fired
    assert "iqr" in fired


def test_detectors_stay_silent_on_normal_variation():
    history = [6000.0, 6100.0, 5950.0, 6050.0, 5980.0]
    fired = run_detectors(6020.0, history)
    assert fired == []


def test_scraper_anomaly_flags_duplicate_flood_not_market_surge():
    """This is the central guarantee of build prompt Sec.11: identical fares across a
    large batch must be routed to data quality, never classified as a market surge."""
    identical_fares = [6000.0] * 40
    result = check_batch(identical_fares, "makemytrip")
    assert result.is_scraper_anomaly is True
    assert result.flag_type == "DUPLICATE_FLOOD"


def test_scraper_anomaly_ignores_small_batches():
    result = check_batch([6000.0] * 5, "makemytrip", min_batch=20)
    assert result.is_scraper_anomaly is False


def test_scraper_anomaly_silent_on_healthy_batch():
    import random

    rng = random.Random(1)
    healthy = [6000.0 + rng.gauss(0, 300) for _ in range(40)]
    result = check_batch(healthy, "makemytrip")
    assert result.is_scraper_anomaly is False
