"""Median absolute deviation test - the most outlier-resistant of the four."""
from __future__ import annotations

import numpy as np

# Scale factor making MAD a consistent estimator of sigma for normal data.
MAD_SCALE = 1.4826


def detect_mad(value: float, sample: list[float], threshold: float = 3.0) -> bool:
    if len(sample) < 3:
        return False
    arr = np.asarray(sample, dtype=float)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    if mad == 0:
        return False
    return abs(value - med) / (MAD_SCALE * mad) > threshold
