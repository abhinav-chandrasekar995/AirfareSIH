"""Model registry and selection.

Model choice is decided by walk-forward validation error, never asserted. The
comparison table this produces is surfaced in the UI so the selection is auditable.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from app.analytics.backtest.metrics import mape, rmse
from app.analytics.forecasting.baselines import (
    exponential_smoothing,
    seasonal_baseline,
    seasonal_moving_average,
)
from app.analytics.forecasting.gradient_boosting_model import gradient_boosting_forecast
from app.analytics.forecasting.intervals import prediction_interval, pressure_band, residual_std
from app.analytics.forecasting.sarima_model import sarima_forecast

MODEL_VERSION = "fc-1.0.0"

ForecastFn = Callable[[list[float], int], list[float]]

REGISTRY: dict[str, ForecastFn] = {
    "SEASONAL_MOVING_AVERAGE": seasonal_moving_average,
    "EXPONENTIAL_SMOOTHING": exponential_smoothing,
    "SEASONAL_BASELINE": seasonal_baseline,
    "SARIMA": sarima_forecast,
    "GRADIENT_BOOSTING": gradient_boosting_forecast,
}


@dataclass(frozen=True)
class ModelScore:
    model_name: str
    validation_mape: float
    validation_rmse: float
    selected: bool = False


@dataclass(frozen=True)
class ForecastResult:
    model_name: str
    model_version: str
    predictions: list[float]
    bounds: list[tuple[float, float]]
    confidence_level: float
    pressure_band: str
    validation_mape: float
    comparison: list[ModelScore]


def _walk_forward_score(fn: ForecastFn, series: list[float], test_size: int) -> tuple[float, float]:
    train, test = series[:-test_size], series[-test_size:]
    try:
        predicted = fn(train, test_size)
    except Exception:
        return float("inf"), float("inf")
    return mape(test, predicted), rmse(test, predicted)


def select_and_forecast(
    series: list[float],
    horizon: int = 14,
    confidence: float = 0.80,
) -> ForecastResult | None:
    """Validate every registered model, pick the lowest-MAPE one, forecast with bounds."""
    if len(series) < 21:
        return None

    test_size = max(7, min(14, len(series) // 4))
    scores: list[ModelScore] = []
    for name, fn in REGISTRY.items():
        m, r = _walk_forward_score(fn, series, test_size)
        if np.isfinite(m):
            scores.append(ModelScore(name, round(m, 3), round(r, 2)))

    if not scores:
        return None

    scores.sort(key=lambda s: s.validation_mape)
    best = scores[0]
    comparison = [
        ModelScore(s.model_name, s.validation_mape, s.validation_rmse, s.model_name == best.model_name)
        for s in scores
    ]

    predictions = REGISTRY[best.model_name](series, horizon)
    fitted = REGISTRY[best.model_name](series[:-test_size], test_size)
    std = residual_std(series[-test_size:], fitted) or float(np.std(series[-test_size:], ddof=1))

    return ForecastResult(
        model_name=best.model_name,
        model_version=MODEL_VERSION,
        predictions=[round(p, 2) for p in predictions],
        bounds=prediction_interval(predictions, std, confidence),
        confidence_level=confidence,
        pressure_band=pressure_band(predictions, float(np.mean(series[-7:]))),
        validation_mape=best.validation_mape,
        comparison=comparison,
    )
