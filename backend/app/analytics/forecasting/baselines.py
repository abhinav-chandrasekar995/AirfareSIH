"""Baseline forecasting models. Deliberately simple and fully deterministic."""
from __future__ import annotations

import numpy as np


def seasonal_moving_average(series: list[float], horizon: int, season: int = 7) -> list[float]:
    """Repeat the mean of each position within the last full season."""
    if len(series) < season:
        return [float(np.mean(series))] * horizon
    last = np.asarray(series[-season:], dtype=float)
    return [float(last[i % season]) for i in range(horizon)]


def exponential_smoothing(series: list[float], horizon: int, alpha: float = 0.3) -> list[float]:
    """Simple exponential smoothing; the flat forecast is the final smoothed level."""
    level = float(series[0])
    for value in series[1:]:
        level = alpha * float(value) + (1 - alpha) * level
    return [round(level, 2)] * horizon


def seasonal_baseline(series: list[float], horizon: int, season: int = 7) -> list[float]:
    """Trend-adjusted seasonal naive: seasonal shape plus a fitted linear drift."""
    arr = np.asarray(series, dtype=float)
    if arr.size < season * 2:
        return exponential_smoothing(series, horizon)
    x = np.arange(arr.size)
    slope, intercept = np.polyfit(x, arr, 1)
    detrended = arr - (slope * x + intercept)
    seasonal = np.array([detrended[i::season].mean() for i in range(season)])
    return [
        round(float(slope * (arr.size + h) + intercept + seasonal[(arr.size + h) % season]), 2)
        for h in range(horizon)
    ]
