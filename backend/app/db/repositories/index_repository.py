"""Queries over published index values and the observations behind them."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import IndexLevel
from app.db.models import FareObservation, IndexValue, Route, RouteWeight


def _base_query(level: IndexLevel, scope: str | None) -> Select:
    """No ordering applied here deliberately.

    BUG HISTORY: this used to bake in `.order_by(IndexValue.date)` (ascending), and
    `latest()`/`value_on_or_before()` each called `.order_by(desc(IndexValue.date))` on
    top expecting it to take over. SQLAlchemy's `Select.order_by()` APPENDS successive
    calls rather than replacing them, so the effective query became
    `ORDER BY date ASC, date DESC` - the first (ascending) clause still won as the
    primary sort key, so `.limit(1)` silently returned the OLDEST row every time
    "latest" was requested. This is what made the dashboard headline and the index
    trend chart disagree (the headline showed the first day's value). Each caller below
    now applies its own single, explicit ordering instead.
    """
    conditions = [
        IndexValue.level == level.value,
        IndexValue.methodology_version == settings.methodology_version,
    ]
    if scope:
        conditions.append(IndexValue.scope == scope)
    return select(IndexValue).where(and_(*conditions))


async def series(
    session: AsyncSession,
    level: IndexLevel,
    scope: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 2000,
) -> list[IndexValue]:
    stmt = _base_query(level, scope).order_by(IndexValue.date)
    if date_from:
        stmt = stmt.where(IndexValue.date >= date_from)
    if date_to:
        stmt = stmt.where(IndexValue.date <= date_to)
    return list((await session.execute(stmt.limit(limit))).scalars())


async def latest(
    session: AsyncSession, level: IndexLevel, scope: str | None = None
) -> IndexValue | None:
    stmt = _base_query(level, scope).order_by(desc(IndexValue.date)).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def value_on_or_before(
    session: AsyncSession, level: IndexLevel, scope: str, on: date
) -> IndexValue | None:
    stmt = (
        _base_query(level, scope)
        .where(IndexValue.date <= on)
        .order_by(desc(IndexValue.date))
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def latest_by_scope(session: AsyncSession, level: IndexLevel) -> dict[str, IndexValue]:
    """Most recent value for every scope at a level, in one round trip."""
    newest = (
        select(IndexValue.scope, func.max(IndexValue.date).label("max_date"))
        .where(
            IndexValue.level == level.value,
            IndexValue.methodology_version == settings.methodology_version,
        )
        .group_by(IndexValue.scope)
        .subquery()
    )
    stmt = select(IndexValue).join(
        newest,
        and_(IndexValue.scope == newest.c.scope, IndexValue.date == newest.c.max_date),
    ).where(IndexValue.level == level.value)
    return {row.scope: row for row in (await session.execute(stmt)).scalars()}


async def route_fares(
    session: AsyncSession,
    route_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    quality_threshold: float | None = None,
) -> list[float]:
    """Quality-filtered total fares for a route - the input to the index engine."""
    stmt = select(FareObservation.total_fare).where(
        FareObservation.route_id == route_id,
        FareObservation.quality_score >= (quality_threshold or settings.quality_threshold),
    )
    if date_from:
        stmt = stmt.where(FareObservation.observed_at >= date_from)
    if date_to:
        stmt = stmt.where(FareObservation.observed_at <= date_to)
    return [float(v) for v in (await session.execute(stmt)).scalars()]


async def active_weights(session: AsyncSession) -> dict[str, float]:
    """Current route weights keyed by route code."""
    stmt = (
        select(Route.route_code, RouteWeight.weight)
        .join(RouteWeight, RouteWeight.route_id == Route.route_id)
        .where(RouteWeight.effective_to.is_(None))
    )
    return {code: float(weight) for code, weight in (await session.execute(stmt)).all()}


async def weight_set_version(session: AsyncSession) -> tuple[str | None, str | None]:
    stmt = (
        select(RouteWeight.weight_set_version, RouteWeight.source_description)
        .where(RouteWeight.effective_to.is_(None))
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    return (row[0], row[1]) if row else (None, None)
