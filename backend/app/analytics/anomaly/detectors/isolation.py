"""Isolation Forest - the one multivariate detector, kept optional so the pipeline
still runs where scikit-learn is unavailable."""
from __future__ import annotations

import numpy as np


def detect_isolation_forest(value: float, sample: list[float], contamination: float = 0.1) -> bool:
    if len(sample) < 20:
        return False
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return False
    x = np.asarray(sample, dtype=float).reshape(-1, 1)
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    model.fit(x)
    return bool(model.predict(np.array([[value]]))[0] == -1)
