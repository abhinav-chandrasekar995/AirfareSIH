"""Stage 2.5 - Outlier detection.

Outliers are FLAGGED, never dropped. A genuine surge and a scraping error both look
extreme; discarding them at this stage would delete exactly the observations the
anomaly engine exists to explain.
"""
from __future__ import annotations

import numpy as np

IQR_MULTIPLIER = 3.0  # deliberately wide: this stage flags, the anomaly engine judges


def flag_outliers(fares: list[float]) -> list[bool]:
    if len(fares) < 4:
        return [False] * len(fares)
    arr = np.asarray(fares, dtype=float)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return [False] * len(fares)
    low, high = q1 - IQR_MULTIPLIER * iqr, q3 + IQR_MULTIPLIER * iqr
    return [bool(f < low or f > high) for f in arr]
