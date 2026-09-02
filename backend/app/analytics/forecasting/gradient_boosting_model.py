"""Gradient-boosted regression on lag features."""
from __future__ import annotations

import numpy as np

from app.analytics.forecasting.baselines import seasonal_baseline

N_LAGS = 7


def gradient_boosting_forecast(series: list[float], horizon: int) -> list[float]:
    if len(series) < N_LAGS * 3:
        return seasonal_baseline(series, horizon)
    try:
        from sklearn.ensemble import GradientBoostingRegressor
    except ImportError:
        return seasonal_baseline(series, horizon)

    arr = np.asarray(series, dtype=float)
    x = np.array([arr[i : i + N_LAGS] for i in range(arr.size - N_LAGS)])
    y = arr[N_LAGS:]

    model = GradientBoostingRegressor(n_estimators=120, max_depth=3, random_state=42)
    model.fit(x, y)

    # Recursive multi-step: each prediction becomes an input to the next.
    window, out = list(arr[-N_LAGS:]), []
    for _ in range(horizon):
        pred = float(model.predict(np.array([window]))[0])
        out.append(round(pred, 2))
        window = window[1:] + [pred]
    return out
