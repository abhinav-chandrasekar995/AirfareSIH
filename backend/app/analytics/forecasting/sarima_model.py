"""SARIMA forecast, degrading to a baseline where statsmodels is unavailable or the
series is too short to fit."""
from __future__ import annotations

import warnings

from app.analytics.forecasting.baselines import seasonal_baseline


def sarima_forecast(series: list[float], horizon: int, season: int = 7) -> list[float]:
    if len(series) < season * 3:
        return seasonal_baseline(series, horizon, season)
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except ImportError:
        return seasonal_baseline(series, horizon, season)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = SARIMAX(
                series,
                order=(1, 1, 1),
                seasonal_order=(1, 0, 1, season),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
            return [round(float(v), 2) for v in model.forecast(steps=horizon)]
    except Exception:
        # A failed fit must not take the pipeline down; the baseline still publishes.
        return seasonal_baseline(series, horizon, season)
