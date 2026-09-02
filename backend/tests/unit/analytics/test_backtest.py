"""Back-test metrics and DGCA alignment tests."""
from __future__ import annotations

from datetime import date

import pytest

from app.analytics.backtest import align_series, all_metrics, correlation, directional_accuracy, mape


def test_perfect_match_yields_zero_error_and_full_correlation():
    series = [100.0, 102.0, 99.0, 105.0, 110.0]
    metrics = all_metrics(series, series)
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["mape"] == 0.0
    assert metrics["correlation"] == 1.0
    assert metrics["directional_accuracy"] == 100.0


def test_mape_ignores_zero_actuals_rather_than_dividing_by_zero():
    assert mape([0.0, 100.0], [10.0, 105.0]) == pytest.approx(5.0, abs=0.01)


def test_directional_accuracy_penalises_wrong_turning_points():
    actual = [100.0, 110.0, 105.0, 115.0]
    predicted = [100.0, 108.0, 109.0, 112.0]  # misses the down-tick at step 2
    acc = directional_accuracy(actual, predicted)
    assert acc == pytest.approx(66.67, abs=0.5)


def test_correlation_handles_constant_series_without_crashing():
    assert correlation([5.0, 5.0, 5.0], [1.0, 2.0, 3.0]) == 0.0


def test_align_series_aggregates_daily_to_monthly_and_intersects():
    ours = [
        (date(2026, 6, 1), 100.0), (date(2026, 6, 15), 110.0),
        (date(2026, 7, 1), 120.0), (date(2026, 7, 20), 130.0),
    ]
    benchmark = [(date(2026, 7, 1), 118.0), (date(2026, 8, 1), 140.0)]

    months, ours_values, bench_values = align_series(ours, benchmark)
    # Only July is present in both series.
    assert months == [date(2026, 7, 1)]
    assert ours_values == [125.0]  # mean of 120 and 130
    assert bench_values == [118.0]
