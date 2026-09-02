"""Fare elasticity with respect to booking lead time."""
from __future__ import annotations

import numpy as np

from app.analytics.lead_time.curve import LeadTimePoint


def estimate_elasticity(points: list[LeadTimePoint]) -> float | None:
    """OLS slope of ln(fare) on ln(lead_days).

    A negative value is the expected shape: fares fall as the booking window lengthens.
    Needs at least three windows to be meaningful, so returns None below that.
    """
    usable = [p for p in points if p.avg_fare > 0 and p.lead_days > 0]
    if len(usable) < 3:
        return None
    x = np.log([p.lead_days for p in usable])
    y = np.log([p.avg_fare for p in usable])
    slope, _intercept = np.polyfit(x, y, 1)
    return round(float(slope), 4)
