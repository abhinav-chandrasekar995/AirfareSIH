"""Classical z-score outlier test."""
from __future__ import annotations

import numpy as np


def detect_zscore(value: float, sample: list[float], threshold: float = 2.5) -> bool:
    if len(sample) < 3:
        return False
    arr = np.asarray(sample, dtype=float)
    std = float(np.std(arr, ddof=1))
    if std == 0:
        return False
    return abs((value - float(np.mean(arr))) / std) > threshold
