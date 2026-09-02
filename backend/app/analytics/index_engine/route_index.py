"""Route-level price measure and route index."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics import estimators
from app.core.constants import Estimator


@dataclass(frozen=True)
class RouteMeasure:
    """The robust price measure for one route in one period, with all variants retained."""
    route_code: str
    value: float
    estimator: Estimator
    n_observations: int
    variants: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteIndexValue:
    route_code: str
    index_value: float
    current_measure: float
    base_measure: float
    estimator: Estimator
    n_observations: int
    variants: dict[str, float] = field(default_factory=dict)


def compute_route_measure(
    route_code: str,
    fares: list[float],
    estimator: Estimator = Estimator.TRIMMED_MEAN_10,
    min_observations: int = 5,
) -> RouteMeasure | None:
    """Return the route's robust price measure, or None if the sample is too thin.

    Returning None rather than a noisy number is deliberate: a route-period below the
    minimum is EXCLUDED from the index and its weight renormalised, with the exclusion
    recorded. Silently publishing a one-observation "average" would be worse than a gap.
    """
    if len(fares) < min_observations:
        return None
    return RouteMeasure(
        route_code=route_code,
        value=round(estimators.apply(fares, estimator), 2),
        estimator=estimator,
        n_observations=len(fares),
        variants=estimators.all_estimators(fares),
    )


def compute_route_index(
    measure: RouteMeasure,
    base_measure: float,
) -> RouteIndexValue:
    """Route Index = (current price measure / base-period price measure) x 100."""
    if base_measure <= 0:
        raise ValueError(f"base measure for {measure.route_code} must be positive")
    return RouteIndexValue(
        route_code=measure.route_code,
        index_value=round((measure.value / base_measure) * 100.0, 3),
        current_measure=measure.value,
        base_measure=round(base_measure, 2),
        estimator=measure.estimator,
        n_observations=measure.n_observations,
        variants=measure.variants,
    )
