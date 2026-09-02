"""Interquartile-range fence test. Distribution-free, so it survives skewed fare data."""
from __future__ import annotations

import numpy as np


def detect_iqr(value: float, sample: list[float], multiplier: float = 1.5) -> bool:
    if len(sample) < 4:
        return False
    q1, q3 = np.percentile(np.asarray(sample, dtype=float), [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return False
    return value < q1 - multiplier * iqr or value > q3 + multiplier * iqr
