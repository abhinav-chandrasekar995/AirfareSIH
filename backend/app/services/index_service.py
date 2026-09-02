"""Index service: orchestrates repository reads and the pure index engine."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.index_engine.national_index import compute_aggregate_index
from app.analytics.index_engine.route_index import compute_route_index, compute_route_measure
from app.config import settings
from app.core.constants import Estimator, IndexLevel
from app.db.repositories import analytics_repository as analytics_repo
from app.db.repositories import index_repository as index_repo

ROUTE_INDEX_FORMULA = "Route Index = (current route price measure / base-period measure) x 100"
AGGREGATE_FORMULA = "Aggregate Index = SUM(route index x weight) / SUM(weight), weights renormalised over observed routes"
MISSING_ROUTE_POLICY = (
    "A route-period with fewer than the minimum observations is excluded from the index "
    "and its weight renormalised across the observed routes. Every exclusion is recorded "
    "in the index value notes rather than absorbed silently."
)


async def get_series(
    session: AsyncSession,
    level: IndexLevel,
    scope: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    rows = await index_repo.series(session, level, scope, date_from, date_to)
    return [
        {
            "date": row.date,
            "level": row.level,
            "scope": row.scope,
            "index_value": float(row.index_value),
            "n_observations": row.n_observations,
            "estimator": row.estimator,
            "weight": float(row.weight) if row.weight is not None else None,
            "notes": row.notes,
        }
        for row in rows
    ]


async def get_summary(
    session: AsyncSession, level: IndexLevel, scope: str | None = None
) -> dict | None:
    """Current value, prior value and month-over-month movement."""
    latest = await index_repo.latest(session, level, scope)
    if latest is None:
        return None

    previous = await index_repo.value_on_or_before(
        session, level, latest.scope, latest.date - timedelta(days=30)
    )
    change_pct = None
    direction = "flat"
    if previous and float(previous.index_value) > 0:
        change_pct = round(
            (float(latest.index_value) - float(previous.index_value))
            / float(previous.index_value)
            * 100,
            2,
        )
        # In a price index a rise is the adverse direction; the UI colours it that way.
        direction = "up" if change_pct > 0.5 else "down" if change_pct < -0.5 else "flat"

    return {
        "scope": latest.scope,
        "level": latest.level,
        "current_value": float(latest.index_value),
        "previous_value": float(previous.index_value) if previous else None,
        "change_pct": change_pct,
        "change_direction": direction,
        "base_period": latest.base_period,
        "as_of": latest.date,
        "n_observations": latest.n_observations,
    }


async def get_regional_summaries(session: AsyncSession) -> list[dict]:
    latest_by_scope = await index_repo.latest_by_scope(session, IndexLevel.REGIONAL)
    return [
        {
            "scope": scope,
            "level": "REGIONAL",
            "current_value": float(row.index_value),
            "as_of": row.date,
            "n_observations": row.n_observations,
        }
        for scope, row in sorted(latest_by_scope.items())
    ]


async def get_methodology(session: AsyncSession) -> dict:
    """Everything a reader needs to reproduce an index value by hand."""
    version, source = await index_repo.weight_set_version(session)
    weights = await analytics_repo.route_weights_detail(session)
    return {
        "methodology_version": settings.methodology_version,
        "base_period": date.fromisoformat(settings.index_base_period),
        "estimator": settings.default_estimator,
        "quality_threshold": settings.quality_threshold,
        "min_observations_per_period": settings.min_observations_per_period,
        "weight_set_version": version,
        "weight_source": source,
        "route_index_formula": ROUTE_INDEX_FORMULA,
        "aggregate_formula": AGGREGATE_FORMULA,
        "missing_route_policy": MISSING_ROUTE_POLICY,
        "basket_size": len(weights),
        "weights": weights,
    }


async def recompute_national(
    session: AsyncSession,
    as_of: date,
    estimator: Estimator | None = None,
) -> dict | None:
    """Recompute the national index live from observations.

    Used by the methodology page to demonstrate reproducibility: the number shown is
    derived from stored observations on demand, not read back from a cached row.
    """
    estimator = estimator or Estimator(settings.default_estimator)
    routes = await analytics_repo.all_routes(session, basket_only=True)
    weights = await index_repo.active_weights(session)

    route_indices = []
    for route in routes:
        current = await index_repo.route_fares(
            session, route.route_id, date_from=as_of - timedelta(days=7), date_to=as_of
        )
        measure = compute_route_measure(
            route.route_code, current, estimator, settings.min_observations_per_period
        )
        if measure is None:
            continue

        base_period = date.fromisoformat(settings.index_base_period)
        base_fares = await index_repo.route_fares(
            session, route.route_id, date_from=base_period, date_to=base_period + timedelta(days=30)
        )
        base_measure = compute_route_measure(
            route.route_code, base_fares, estimator, settings.min_observations_per_period
        )
        if base_measure is None:
            continue

        route_indices.append(compute_route_index(measure, base_measure.value))

    aggregate = compute_aggregate_index(route_indices, weights)
    if aggregate is None:
        return None

    return {
        "index_value": aggregate.index_value,
        "n_routes": aggregate.n_routes,
        "n_observations": aggregate.n_observations,
        "excluded_routes": aggregate.excluded,
        "notes": aggregate.notes,
        "estimator": estimator.value,
        "as_of": as_of,
    }
