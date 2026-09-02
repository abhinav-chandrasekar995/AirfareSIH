"""Forecasting: models produce bounded output, intervals widen with horizon, and the
model registry selects by validation error rather than a fixed preference."""
from __future__ import annotations

import math

from app.analytics.forecasting import select_and_forecast
from app.analytics.forecasting.intervals import prediction_interval, pressure_band


def _synthetic_series(n=90):
    """A gently trending, weekly-seasonal series - enough structure for every model in
    the registry to fit without external data."""
    return [
        6000 + 15 * i + 400 * math.sin(2 * math.pi * i / 7) for i in range(n)
    ]


def test_forecast_requires_minimum_history():
    assert select_and_forecast([1.0, 2.0, 3.0], horizon=14) is None


def test_forecast_always_returns_bounds_that_bracket_the_prediction():
    result = select_and_forecast(_synthetic_series(), horizon=14)
    assert result is not None
    assert len(result.predictions) == 14
    assert len(result.bounds) == 14
    for pred, (lower, upper) in zip(result.predictions, result.bounds):
        assert lower <= pred <= upper


def test_model_selection_is_justified_by_lowest_validation_mape():
    result = select_and_forecast(_synthetic_series(), horizon=14)
    selected = [m for m in result.comparison if m.selected]
    assert len(selected) == 1
    assert selected[0].model_name == result.model_name
    assert all(selected[0].validation_mape <= m.validation_mape for m in result.comparison)


def test_prediction_interval_widens_with_horizon():
    predictions = [100.0] * 10
    bounds = prediction_interval(predictions, residual_std=5.0, confidence=0.80)
    widths = [u - l for l, u in bounds]
    # Each successive step's interval must be at least as wide as the previous one.
    assert all(widths[i] <= widths[i + 1] for i in range(len(widths) - 1))


def test_pressure_band_reflects_direction_of_forecast():
    assert pressure_band([120.0, 122.0], recent_level=100.0) == "HIGH"
    assert pressure_band([101.0, 102.0], recent_level=100.0) == "LOW"
