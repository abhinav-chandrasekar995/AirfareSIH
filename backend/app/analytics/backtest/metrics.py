"""Back-test error metrics. Every one is computed from stored series - never hardcoded."""
from __future__ import annotations

import numpy as np


def _aligned(actual: list[float], predicted: list[float]) -> tuple[np.ndarray, np.ndarray]:
    n = min(len(actual), len(predicted))
    if n == 0:
        raise ValueError("cannot compute metrics over empty series")
    return (
        np.asarray(actual[:n], dtype=float),
        np.asarray(predicted[:n], dtype=float),
    )


def mae(actual: list[float], predicted: list[float]) -> float:
    a, p = _aligned(actual, predicted)
    return round(float(np.mean(np.abs(a - p))), 2)


def rmse(actual: list[float], predicted: list[float]) -> float:
    a, p = _aligned(actual, predicted)
    return round(float(np.sqrt(np.mean((a - p) ** 2))), 2)


def mape(actual: list[float], predicted: list[float]) -> float:
    """Mean absolute percentage error, guarding against division by zero."""
    a, p = _aligned(actual, predicted)
    mask = a != 0
    if not mask.any():
        return float("inf")
    return round(float(np.mean(np.abs((a[mask] - p[mask]) / a[mask])) * 100.0), 3)


def correlation(actual: list[float], predicted: list[float]) -> float:
    a, p = _aligned(actual, predicted)
    if a.size < 2 or np.std(a) == 0 or np.std(p) == 0:
        return 0.0
    return round(float(np.corrcoef(a, p)[0, 1]), 4)


def directional_accuracy(actual: list[float], predicted: list[float]) -> float:
    """Share of periods where both series moved in the same direction.

    Level accuracy alone can hide a series that tracks magnitude but misses turning
    points, which for a price index is the failure that matters most.
    """
    a, p = _aligned(actual, predicted)
    if a.size < 2:
        return 0.0
    return round(float(np.mean(np.sign(np.diff(a)) == np.sign(np.diff(p))) * 100.0), 2)


def all_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    return {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "mape": mape(actual, predicted),
        "correlation": correlation(actual, predicted),
        "directional_accuracy": directional_accuracy(actual, predicted),
    }
