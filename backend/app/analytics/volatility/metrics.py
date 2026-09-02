"""Airfare volatility. Two routes can share an average fare and behave completely
differently; the volatility score is what separates them."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.constants import Band


@dataclass(frozen=True)
class VolatilityResult:
    std_dev: float
    coefficient_of_variation: float
    price_range_min: float
    price_range_max: float
    abnormal_move_frequency: float
    volatility_score: Band


def compute_volatility(fares: list[float], abnormal_threshold_pct: float = 15.0) -> VolatilityResult | None:
    """Dispersion metrics plus a composite LOW/MEDIUM/HIGH band.

    `abnormal_move_frequency` is the share of day-over-day moves exceeding the
    threshold - a route can have low dispersion overall yet jump frequently.
    """
    if len(fares) < 2:
        return None
    arr = np.asarray(fares, dtype=float)
    mean_fare = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    cv = std / mean_fare if mean_fare > 0 else 0.0

    changes = np.abs(np.diff(arr) / arr[:-1]) * 100.0
    abnormal_freq = float(np.mean(changes > abnormal_threshold_pct) * 100.0) if changes.size else 0.0

    if cv >= 0.30:
        band = Band.HIGH
    elif cv >= 0.15:
        band = Band.MEDIUM
    else:
        band = Band.LOW

    return VolatilityResult(
        std_dev=round(std, 2),
        coefficient_of_variation=round(cv, 4),
        price_range_min=round(float(np.min(arr)), 2),
        price_range_max=round(float(np.max(arr)), 2),
        abnormal_move_frequency=round(abnormal_freq, 2),
        volatility_score=band,
    )
