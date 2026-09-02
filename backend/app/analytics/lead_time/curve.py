"""Lead-time fare curve: average fare at each advance-purchase window."""
from __future__ import annotations

from dataclasses import dataclass

from app.analytics import estimators
from app.core.constants import Estimator, LeadBucket


@dataclass(frozen=True)
class LeadTimePoint:
    lead_bucket: LeadBucket
    lead_days: int
    avg_fare: float
    n_observations: int


def build_curve(
    fares_by_bucket: dict[LeadBucket, list[float]],
    estimator: Estimator = Estimator.MEDIAN,
) -> list[LeadTimePoint]:
    """Build the curve ordered from earliest booking (T+45) to latest (T+1).

    The median is the default here rather than the trimmed mean: within a single
    lead-time bucket the sample is smaller, and the median degrades more gracefully.
    """
    points: list[LeadTimePoint] = []
    for bucket in LeadBucket.ordered():
        fares = fares_by_bucket.get(bucket, [])
        if not fares:
            continue
        points.append(
            LeadTimePoint(
                lead_bucket=bucket,
                lead_days=bucket.days,
                avg_fare=round(estimators.apply(fares, estimator), 2),
                n_observations=len(fares),
            )
        )
    return points


def curve_as_dict(points: list[LeadTimePoint]) -> dict[LeadBucket, float]:
    return {p.lead_bucket: p.avg_fare for p in points}
