"""Expected-fare baseline.

The baseline is conditioned on the lead-time bucket, not just the route. Comparing a
T+1 fare against a lead-time-agnostic route average would flag every last-minute
booking as an anomaly, which is why the lead-time model feeds this stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.constants import LeadBucket


@dataclass(frozen=True)
class Baseline:
    expected_fare: float
    lower: float
    upper: float
    n_observations: int
    lead_bucket: LeadBucket | None


def build_baseline(
    historical_fares: list[float],
    lead_bucket: LeadBucket | None = None,
    weekend_uplift: float = 0.0,
    event_uplift: float = 0.0,
) -> Baseline | None:
    """Median expected fare with an interquartile band, adjusted for known context.

    Uplifts shift the expectation for conditions we already know about (weekend,
    festival), so those effects are not re-reported as surprises.
    """
    if len(historical_fares) < 5:
        return None
    arr = np.asarray(historical_fares, dtype=float)
    expected = float(np.median(arr)) * (1.0 + weekend_uplift + event_uplift)
    q1, q3 = np.percentile(arr, [25, 75])
    return Baseline(
        expected_fare=round(expected, 2),
        lower=round(float(q1) * (1.0 + weekend_uplift + event_uplift), 2),
        upper=round(float(q3) * (1.0 + weekend_uplift + event_uplift), 2),
        n_observations=int(arr.size),
        lead_bucket=lead_bucket,
    )


def deviation_pct(observed: float, expected: float) -> float:
    if expected <= 0:
        raise ValueError("expected fare must be positive")
    return round((observed - expected) / expected * 100.0, 2)


def classify_severity(dev_pct: float) -> str:
    """Severity by absolute deviation from the expected baseline."""
    magnitude = abs(dev_pct)
    if magnitude >= 60:
        return "CRITICAL"
    if magnitude >= 35:
        return "HIGH"
    if magnitude >= 20:
        return "MEDIUM"
    return "LOW"
