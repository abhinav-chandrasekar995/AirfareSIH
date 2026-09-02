"""Queries over fare observations: Data Explorer, route analytics, divergence."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Select, and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Airline, FareObservation, FareObservationRaw, Route, Source


def build_filter(
    route_code: str | None = None,
    airline_code: str | None = None,
    source_code: str | None = None,
    fare_class: str | None = None,
    lead_bucket: str | None = None,
    quality_min: float | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list:
    conditions = []
    if route_code:
        conditions.append(Route.route_code == route_code)
    if airline_code:
        conditions.append(Airline.iata_code == airline_code)
    if source_code:
        conditions.append(Source.source_code == source_code)
    if fare_class:
        conditions.append(FareObservation.fare_class == fare_class)
    if lead_bucket:
        conditions.append(FareObservation.lead_bucket == lead_bucket)
    if quality_min is not None:
        conditions.append(FareObservation.quality_score >= quality_min)
    if date_from:
        conditions.append(func.date(FareObservation.observed_at) >= date_from)
    if date_to:
        conditions.append(func.date(FareObservation.observed_at) <= date_to)
    return conditions


def _joined() -> Select:
    return (
        select(FareObservation)
        .join(Route, Route.route_id == FareObservation.route_id)
        .join(Airline, Airline.airline_id == FareObservation.airline_id)
        .join(Source, Source.source_id == FareObservation.source_id)
    )


async def search(
    session: AsyncSession,
    conditions: list,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[FareObservation], int]:
    """Paginated observation search. Never unbounded (build prompt Sec.18)."""
    stmt = _joined()
    if conditions:
        stmt = stmt.where(and_(*conditions))

    total_stmt = select(func.count()).select_from(FareObservation)
    total_stmt = (
        total_stmt.join(Route, Route.route_id == FareObservation.route_id)
        .join(Airline, Airline.airline_id == FareObservation.airline_id)
        .join(Source, Source.source_id == FareObservation.source_id)
    )
    if conditions:
        total_stmt = total_stmt.where(and_(*conditions))
    total = int((await session.execute(total_stmt)).scalar() or 0)

    stmt = stmt.order_by(desc(FareObservation.observed_at)).limit(page_size).offset((page - 1) * page_size)
    return list((await session.execute(stmt)).scalars()), total


async def raw_for_observation(session: AsyncSession, raw_id: int) -> FareObservationRaw | None:
    stmt = select(FareObservationRaw).where(FareObservationRaw.raw_id == raw_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def route_daily_series(
    session: AsyncSession, route_id: int, days: int = 90
) -> list[tuple[date, float, int]]:
    """Daily median fare for one route - the route trend chart."""
    day = func.date(FareObservation.observed_at).label("day")
    stmt = (
        select(
            day,
            func.percentile_cont(0.5).within_group(FareObservation.total_fare).label("median_fare"),
            func.count().label("n"),
        )
        .where(
            FareObservation.route_id == route_id,
            FareObservation.quality_score >= settings.quality_threshold,
        )
        .group_by(day)
        .order_by(day)
        .limit(days)
    )
    return [(r.day, float(r.median_fare), int(r.n)) for r in (await session.execute(stmt)).all()]


async def fares_by_lead_bucket(
    session: AsyncSession, route_id: int | None = None
) -> dict[str, list[float]]:
    stmt = select(FareObservation.lead_bucket, FareObservation.total_fare).where(
        FareObservation.quality_score >= settings.quality_threshold
    )
    if route_id:
        stmt = stmt.where(FareObservation.route_id == route_id)

    grouped: dict[str, list[float]] = {}
    for bucket, fare in (await session.execute(stmt)).all():
        grouped.setdefault(bucket, []).append(float(fare))
    return grouped


async def by_airline(session: AsyncSession, route_id: int) -> list[tuple[str, str, float, int]]:
    stmt = (
        select(
            Airline.iata_code,
            Airline.name,
            func.percentile_cont(0.5).within_group(FareObservation.total_fare),
            func.count(),
        )
        .join(Airline, Airline.airline_id == FareObservation.airline_id)
        .where(
            FareObservation.route_id == route_id,
            FareObservation.quality_score >= settings.quality_threshold,
        )
        .group_by(Airline.iata_code, Airline.name)
        .order_by(Airline.name)
    )
    return [(c, n, float(f), int(k)) for c, n, f, k in (await session.execute(stmt)).all()]


async def by_source(session: AsyncSession, route_id: int) -> list[tuple[str, str, str, float, float, int]]:
    """Source-level fare comparison, the input to the divergence module."""
    stmt = (
        select(
            Source.source_code,
            Source.source_name,
            Source.source_type,
            func.avg(FareObservation.total_fare),
            func.avg(FareObservation.convenience_fee),
            func.count(),
        )
        .join(Source, Source.source_id == FareObservation.source_id)
        .where(
            FareObservation.route_id == route_id,
            FareObservation.quality_score >= settings.quality_threshold,
        )
        .group_by(Source.source_code, Source.source_name, Source.source_type)
        .order_by(Source.source_type, Source.source_name)
    )
    return [
        (code, name, stype, float(avg), float(fee or 0), int(n))
        for code, name, stype, avg, fee, n in (await session.execute(stmt)).all()
    ]


async def composition(session: AsyncSession, route_id: int) -> dict[str, float]:
    """Mean fare composition for a route - the stacked breakdown on the route page."""
    stmt = select(
        func.avg(FareObservation.base_fare),
        func.avg(FareObservation.taxes),
        func.avg(FareObservation.udf),
        func.avg(FareObservation.airport_charges),
        func.avg(FareObservation.convenience_fee),
        func.avg(FareObservation.total_fare),
    ).where(
        FareObservation.route_id == route_id,
        FareObservation.quality_score >= settings.quality_threshold,
    )
    row = (await session.execute(stmt)).first()
    if not row or row[5] is None:
        return {}
    base, taxes, udf, charges, fee, total = (float(v or 0) for v in row)
    return {
        "base_fare": round(base, 2),
        "taxes": round(taxes, 2),
        "udf": round(udf, 2),
        "airport_charges": round(charges, 2),
        "convenience_fee": round(fee, 2),
        "total_fare": round(total, 2),
    }


async def platform_counts(session: AsyncSession) -> dict[str, int]:
    """Dashboard KPI counts, all computed - never hardcoded (build prompt Sec.7)."""
    total_points = int((await session.execute(select(func.count()).select_from(FareObservation))).scalar() or 0)
    routes = int(
        (await session.execute(select(func.count()).select_from(Route).where(Route.is_active.is_(True)))).scalar() or 0
    )
    airlines = int(
        (await session.execute(select(func.count()).select_from(Airline).where(Airline.is_active.is_(True)))).scalar() or 0
    )
    otas = int(
        (await session.execute(select(func.count()).select_from(Source).where(Source.source_type == "OTA"))).scalar() or 0
    )
    flights = int(
        (await session.execute(select(func.count(func.distinct(FareObservation.flight_number))))).scalar() or 0
    )
    return {
        "total_data_points": total_points,
        "routes_tracked": routes,
        "airlines_tracked": airlines,
        "ota_sources": otas,
        "flights_monitored": flights,
    }


async def latest_observation_at(session: AsyncSession) -> datetime | None:
    return (await session.execute(select(func.max(FareObservation.observed_at)))).scalar()
