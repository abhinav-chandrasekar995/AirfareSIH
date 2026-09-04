"""Queries over CoreIndexValue (base-fare-only "Core APIx").

Deliberately a separate module from index_repository.py rather than a generic/
parameterized version of it: the existing Headline-series queries are already
DGCA-backtested and in production use, and this module's only job is to add the Core
series alongside it without touching that code at all. See RBI_APIX_MODULE_LOG.md.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import IndexLevel
from app.db.models import CoreIndexValue


def _base_query(level: IndexLevel, scope: str | None):
    # No ordering baked in here either, for the same reason index_repository.py's
    # _base_query() documents at length: SQLAlchemy's order_by() appends rather than
    # replaces, so a second .order_by() call downstream would silently lose to this one.
    conditions = [
        CoreIndexValue.level == level.value,
        CoreIndexValue.methodology_version == settings.methodology_version,
    ]
    if scope:
        conditions.append(CoreIndexValue.scope == scope)
    return select(CoreIndexValue).where(and_(*conditions))


async def series(
    session: AsyncSession,
    level: IndexLevel,
    scope: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 2000,
) -> list[CoreIndexValue]:
    stmt = _base_query(level, scope).order_by(CoreIndexValue.date)
    if date_from:
        stmt = stmt.where(CoreIndexValue.date >= date_from)
    if date_to:
        stmt = stmt.where(CoreIndexValue.date <= date_to)
    return list((await session.execute(stmt.limit(limit))).scalars())


async def latest(
    session: AsyncSession, level: IndexLevel, scope: str | None = None
) -> CoreIndexValue | None:
    stmt = _base_query(level, scope).order_by(desc(CoreIndexValue.date)).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def value_on_or_before(
    session: AsyncSession, level: IndexLevel, scope: str, on: date
) -> CoreIndexValue | None:
    stmt = (
        _base_query(level, scope)
        .where(CoreIndexValue.date <= on)
        .order_by(desc(CoreIndexValue.date))
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()
