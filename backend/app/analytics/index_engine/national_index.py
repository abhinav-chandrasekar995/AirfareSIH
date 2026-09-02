"""Weighted aggregation of route indices into national / regional / airline indices."""
from __future__ import annotations

from dataclasses import dataclass

from app.analytics.index_engine.route_index import RouteIndexValue
from app.analytics.index_engine.weights import excluded_routes, renormalise


@dataclass(frozen=True)
class AggregateIndexValue:
    index_value: float
    n_routes: int
    n_observations: int
    weights_used: dict[str, float]
    excluded: list[str]
    notes: str | None


def compute_aggregate_index(
    route_indices: list[RouteIndexValue],
    weights: dict[str, float],
) -> AggregateIndexValue | None:
    """Laspeyres-style fixed-weight aggregation:

        Index = SUM( route_index * weight ) / SUM( weight )

    Weights are renormalised over the routes actually observed in the period, and any
    exclusion is recorded in `notes` so the omission is visible rather than silent.
    """
    if not route_indices:
        return None

    observed = {ri.route_code for ri in route_indices}
    normalised = renormalise(weights, observed)
    if not normalised:
        return None

    value = sum(ri.index_value * normalised.get(ri.route_code, 0.0) for ri in route_indices)
    dropped = excluded_routes(weights, observed)
    note = (
        f"{len(dropped)} route(s) excluded for insufficient observations; "
        f"weights renormalised over {len(normalised)} route(s): {', '.join(dropped)}"
        if dropped
        else None
    )
    return AggregateIndexValue(
        index_value=round(value, 3),
        n_routes=len(normalised),
        n_observations=sum(ri.n_observations for ri in route_indices),
        weights_used={k: round(v, 6) for k, v in normalised.items()},
        excluded=dropped,
        notes=note,
    )
