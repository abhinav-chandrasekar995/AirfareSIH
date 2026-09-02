"""Prediction intervals.

A point forecast without bounds overstates certainty. Every model in the registry is
wrapped by this function, and the API response schema requires the bounds, so a bare
point forecast cannot reach the UI (build prompt Sec.17).
"""
from __future__ import annotations

import numpy as np

# z-multipliers for common two-sided levels.
_Z = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600}


def prediction_interval(
    predictions: list[float],
    residual_std: float,
    confidence: float = 0.80,
) -> list[tuple[float, float]]:
    """Widen the interval with the square root of the horizon step.

    Uncertainty compounds the further ahead a forecast reaches; a constant-width band
    would understate risk at day 14 relative to day 1.
    """
    z = _Z.get(round(confidence, 2), 1.2816)
    return [
        (
            round(float(p - z * residual_std * np.sqrt(step + 1)), 2),
            round(float(p + z * residual_std * np.sqrt(step + 1)), 2),
        )
        for step, p in enumerate(predictions)
    ]


def residual_std(actual: list[float], fitted: list[float]) -> float:
    a, f = np.asarray(actual, dtype=float), np.asarray(fitted, dtype=float)
    n = min(a.size, f.size)
    if n < 2:
        return 0.0
    return float(np.std(a[-n:] - f[-n:], ddof=1))


def pressure_band(predictions: list[float], recent_level: float) -> str:
    """Translate the forecast into an interpretable pressure band."""
    if not predictions or recent_level <= 0:
        return "LOW"
    change = (float(np.mean(predictions)) - recent_level) / recent_level * 100.0
    if change >= 10:
        return "HIGH"
    if change >= 3:
        return "MEDIUM"
    return "LOW"
