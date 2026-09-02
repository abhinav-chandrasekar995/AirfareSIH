"""Robust central-tendency estimators.

Airfare data contains sold-out flights, promotions, premium fares, scraping errors and
genuine spikes. An arithmetic mean is misleading in that setting, so the index computes
ALL four estimators for every route-period and stores them (ADR-006). That turns the
choice of estimator into an empirical question answerable in the Backtesting Lab rather
than an assertion.
"""
from __future__ import annotations

import numpy as np

from app.core.constants import Estimator

TRIM_FRACTION = 0.10


def mean(values: list[float]) -> float:
    return float(np.mean(values))


def median(values: list[float]) -> float:
    return float(np.median(values))


MIN_N_FOR_TRIM = 5


def trimmed_mean(values: list[float], fraction: float = TRIM_FRACTION) -> float:
    """Discard `fraction` of observations from each tail, then average the rest.

    At the sample sizes a single route-period actually produces, floor(n * 0.10) rounds
    to zero below n=10, which would silently turn the "robust" estimator back into a
    plain mean and let a single sold-out or promotional fare drive the index. So once
    the sample is large enough to afford it, at least one observation is trimmed from
    each tail.
    """
    arr = np.sort(np.asarray(values, dtype=float))
    n = arr.size
    k = int(np.floor(n * fraction))
    if n >= MIN_N_FOR_TRIM:
        k = max(1, k)
    # Trimming must never empty the sample; fall back to the median for tiny samples.
    if n - 2 * k < 1:
        return float(np.median(arr))
    return float(np.mean(arr[k : n - k]))


def weighted_median(values: list[float], weights: list[float] | None = None) -> float:
    """Value at which cumulative weight crosses half of total weight."""
    arr = np.asarray(values, dtype=float)
    w = np.ones_like(arr) if weights is None else np.asarray(weights, dtype=float)
    order = np.argsort(arr)
    arr, w = arr[order], w[order]
    cumulative = np.cumsum(w)
    cutoff = cumulative[-1] / 2.0
    idx = int(np.searchsorted(cumulative, cutoff))
    return float(arr[min(idx, arr.size - 1)])


_DISPATCH = {
    Estimator.MEAN: lambda v: mean(v),
    Estimator.MEDIAN: lambda v: median(v),
    Estimator.TRIMMED_MEAN_10: lambda v: trimmed_mean(v),
    Estimator.WEIGHTED_MEDIAN: lambda v: weighted_median(v),
}


def apply(values: list[float], estimator: Estimator) -> float:
    if not values:
        raise ValueError("cannot estimate central tendency of an empty sample")
    return _DISPATCH[estimator](values)


def all_estimators(values: list[float]) -> dict[str, float]:
    """Every variant at once - persisted alongside each index value (ADR-006)."""
    if not values:
        raise ValueError("cannot estimate central tendency of an empty sample")
    return {
        "mean_fare": round(mean(values), 2),
        "median_fare": round(median(values), 2),
        "trimmed_mean_fare": round(trimmed_mean(values), 2),
        "weighted_median_fare": round(weighted_median(values), 2),
    }
