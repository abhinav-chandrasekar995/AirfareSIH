"""Queries over the derived analytical products: routes, anomalies, lead-time,
volatility, forecasts, back-tests, CPI, and collection health."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    Airport,
    Anomaly,
    BacktestRun,
    CpiReference,
    DataQualityFlag,
    DgcaBenchmark,
    Event,
    Forecast,
    IndexValue,
    LeadTimeCurve,
    Route,
    RouteWeight,
    ScrapeRun,
    Source,
    VolatilityMetric,
)

# ----------------------------------------------------------------- routes


async def all_routes(session: AsyncSession, basket_only: bool = False) -> list[Route]:
    stmt = select(Route).where(Route.is_active.is_(True))
    if basket_only:
        stmt = stmt.where(Route.in_basket.is_(True))
    return list((await session.execute(stmt.order_by(Route.route_code))).scalars())


async def route_by_code(session: AsyncSession, route_code: str) -> Route | None:
    stmt = select(Route).where(Route.route_code == route_code.upper())
    return (await session.execute(stmt)).scalar_one_or_none()


async def airports(session: AsyncSession) -> list[Airport]:
    return list((await session.execute(select(Airport).order_by(Airport.iata_code))).scalars())


# ----------------------------------------------------------------- anomalies


async def anomalies(
    session: AsyncSession,
    severity: str | None = None,
    status: str | None = None,
    route_code: str | None = None,
    anomaly_class: str = "MARKET",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Anomaly], int]:
    conditions = [Anomaly.anomaly_class == anomaly_class]
    if severity:
        conditions.append(Anomaly.severity == severity)
    if status:
        conditions.append(Anomaly.status == status)
    if route_code:
        conditions.append(Route.route_code == route_code.upper())

    stmt = select(Anomaly).join(Route, Route.route_id == Anomaly.route_id).where(and_(*conditions))
    total_stmt = (
        select(func.count())
        .select_from(Anomaly)
        .join(Route, Route.route_id == Anomaly.route_id)
        .where(and_(*conditions))
    )
    total = int((await session.execute(total_stmt)).scalar() or 0)

    stmt = stmt.order_by(desc(Anomaly.detected_at)).limit(page_size).offset((page - 1) * page_size)
    return list((await session.execute(stmt)).scalars()), total


async def anomaly_by_id(session: AsyncSession, anomaly_id: int) -> Anomaly | None:
    stmt = select(Anomaly).where(Anomaly.anomaly_id == anomaly_id)
    return (await session.execute(stmt)).scalar_one_or_none()


# ----------------------------------------------------------------- lead time


async def leadtime_curve(
    session: AsyncSession, route_id: int | None = None
) -> list[LeadTimeCurve]:
    stmt = select(LeadTimeCurve).where(
        LeadTimeCurve.methodology_version == settings.methodology_version
    )
    stmt = stmt.where(
        LeadTimeCurve.route_id == route_id if route_id else LeadTimeCurve.route_id.is_(None)
    )
    newest = (await session.execute(select(func.max(LeadTimeCurve.date)))).scalar()
    if newest:
        stmt = stmt.where(LeadTimeCurve.date == newest)
    return list((await session.execute(stmt)).scalars())


async def leadtime_all_routes(session: AsyncSession) -> list[LeadTimeCurve]:
    newest = (await session.execute(select(func.max(LeadTimeCurve.date)))).scalar()
    stmt = select(LeadTimeCurve).where(
        LeadTimeCurve.route_id.isnot(None),
        LeadTimeCurve.elasticity.isnot(None),
    )
    if newest:
        stmt = stmt.where(LeadTimeCurve.date == newest)
    return list((await session.execute(stmt)).scalars())


# ----------------------------------------------------------------- volatility


async def volatility(
    session: AsyncSession, route_id: int | None = None, window_days: int = 30
) -> list[VolatilityMetric]:
    stmt = select(VolatilityMetric).where(VolatilityMetric.window_days == window_days)
    if route_id:
        stmt = stmt.where(VolatilityMetric.route_id == route_id)
    newest = (await session.execute(select(func.max(VolatilityMetric.date)))).scalar()
    if newest:
        stmt = stmt.where(VolatilityMetric.date == newest)
    return list((await session.execute(stmt)).scalars())


# ----------------------------------------------------------------- forecast


async def forecasts(session: AsyncSession, scope: str = "NATIONAL") -> list[Forecast]:
    newest = (
        await session.execute(
            select(func.max(Forecast.generated_at)).where(Forecast.scope == scope)
        )
    ).scalar()
    if not newest:
        return []
    stmt = (
        select(Forecast)
        .where(Forecast.scope == scope, Forecast.generated_at == newest)
        .order_by(Forecast.forecast_date)
    )
    return list((await session.execute(stmt)).scalars())


# ----------------------------------------------------------------- backtest


async def latest_backtest(session: AsyncSession) -> BacktestRun | None:
    stmt = select(BacktestRun).order_by(desc(BacktestRun.run_at)).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def backtest_by_id(session: AsyncSession, backtest_id: int) -> BacktestRun | None:
    stmt = select(BacktestRun).where(BacktestRun.backtest_id == backtest_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def dgca_series(session: AsyncSession, route_id: int | None = None) -> list[DgcaBenchmark]:
    stmt = select(DgcaBenchmark).order_by(DgcaBenchmark.period_month)
    stmt = stmt.where(
        DgcaBenchmark.route_id == route_id if route_id else DgcaBenchmark.route_id.is_(None)
    )
    return list((await session.execute(stmt)).scalars())


# ----------------------------------------------------------------- cpi


async def latest_cpi(session: AsyncSession, vintage: str | None = None) -> CpiReference | None:
    stmt = select(CpiReference)
    if vintage:
        stmt = stmt.where(CpiReference.series_vintage == vintage)
    stmt = stmt.order_by(desc(CpiReference.period_month)).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def cpi_vintages(session: AsyncSession) -> list[str]:
    stmt = select(CpiReference.series_vintage).distinct()
    return list((await session.execute(stmt)).scalars())


# ----------------------------------------------------------------- collection health


async def source_health(session: AsyncSession) -> list[dict]:
    """Per-source status board for the Collection page."""
    newest = (
        select(ScrapeRun.source_id, func.max(ScrapeRun.started_at).label("last_run"))
        .group_by(ScrapeRun.source_id)
        .subquery()
    )
    stmt = (
        select(Source, ScrapeRun)
        .outerjoin(newest, newest.c.source_id == Source.source_id)
        .outerjoin(
            ScrapeRun,
            and_(
                ScrapeRun.source_id == Source.source_id,
                ScrapeRun.started_at == newest.c.last_run,
            ),
        )
        .order_by(Source.source_type, Source.source_name)
    )

    health: list[dict] = []
    for source, run in (await session.execute(stmt)).all():
        found = run.records_found if run else 0
        valid = run.records_valid if run else 0
        health.append(
            {
                "source_code": source.source_code,
                "source_name": source.source_name,
                "source_type": source.source_type,
                "status": source.status,
                "reliability_score": float(source.reliability_score),
                "rate_limit_rpm": source.rate_limit_rpm,
                "last_run_at": run.started_at if run else None,
                "records_found": found,
                "records_valid": valid,
                "records_failed": run.records_failed if run else 0,
                "latency_ms": run.latency_ms if run else None,
                "success_rate": round(valid / found * 100, 2) if found else 0.0,
            }
        )
    return health


async def quality_flags(
    session: AsyncSession, unresolved_only: bool = True, limit: int = 100
) -> list[DataQualityFlag]:
    stmt = select(DataQualityFlag)
    if unresolved_only:
        stmt = stmt.where(DataQualityFlag.resolved_at.is_(None))
    return list((await session.execute(stmt.order_by(desc(DataQualityFlag.raised_at)).limit(limit))).scalars())


async def scrape_runs(session: AsyncSession, limit: int = 50) -> list[ScrapeRun]:
    stmt = select(ScrapeRun).order_by(desc(ScrapeRun.started_at)).limit(limit)
    return list((await session.execute(stmt)).scalars())


async def sources(session: AsyncSession) -> list[Source]:
    return list((await session.execute(select(Source).order_by(Source.source_name))).scalars())


async def events(session: AsyncSession, upcoming_from: date | None = None) -> list[Event]:
    stmt = select(Event).order_by(Event.start_date)
    if upcoming_from:
        stmt = stmt.where(Event.end_date >= upcoming_from)
    return list((await session.execute(stmt)).scalars())


async def route_weights_detail(session: AsyncSession) -> list[dict]:
    stmt = (
        select(Route.route_code, RouteWeight.weight, RouteWeight.source_description)
        .join(RouteWeight, RouteWeight.route_id == Route.route_id)
        .where(RouteWeight.effective_to.is_(None))
        .order_by(desc(RouteWeight.weight))
    )
    return [
        {"route_code": code, "weight": float(w), "source": src}
        for code, w, src in (await session.execute(stmt)).all()
    ]


async def index_movers(
    session: AsyncSession, window_days: int = 7, limit: int = 5
) -> tuple[list[dict], list[dict]]:
    """Top risers and fallers by route index change over the window."""
    newest = (
        await session.execute(
            select(func.max(IndexValue.date)).where(IndexValue.level == "ROUTE")
        )
    ).scalar()
    if not newest:
        return [], []

    current = {
        row.scope: float(row.index_value)
        for row in (
            await session.execute(
                select(IndexValue).where(
                    IndexValue.level == "ROUTE",
                    IndexValue.date == newest,
                    IndexValue.methodology_version == settings.methodology_version,
                )
            )
        ).scalars()
    }

    from datetime import timedelta

    prior_date = newest - timedelta(days=window_days)
    prior_rows = (
        await session.execute(
            select(IndexValue).where(
                IndexValue.level == "ROUTE",
                IndexValue.date <= prior_date,
                IndexValue.methodology_version == settings.methodology_version,
            ).order_by(desc(IndexValue.date))
        )
    ).scalars()

    prior: dict[str, float] = {}
    for row in prior_rows:
        prior.setdefault(row.scope, float(row.index_value))

    changes = [
        {"route_code": scope, "change_pct": round((value - prior[scope]) / prior[scope] * 100, 2)}
        for scope, value in current.items()
        if scope in prior and prior[scope] > 0
    ]
    changes.sort(key=lambda c: c["change_pct"], reverse=True)
    return changes[:limit], list(reversed(changes[-limit:]))


async def latest_index_date(session: AsyncSession) -> date | None:
    return (await session.execute(select(func.max(IndexValue.date)))).scalar()


async def latest_scrape_at(session: AsyncSession) -> datetime | None:
    return (await session.execute(select(func.max(ScrapeRun.started_at)))).scalar()
