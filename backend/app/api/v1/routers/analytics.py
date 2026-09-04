"""Routers for dashboard, routes, lead-time, anomalies, volatility, forecast,
backtest, CPI simulation, data quality and events."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.cpi import DISCLAIMER
from app.api.deps import ResponseContext, get_context
from app.api.v1.schemas.envelope import envelope
from app.core.exceptions import NotFoundError
from app.db.repositories import analytics_repository as analytics_repo
from app.db.session import get_session
from app.services import analytics_service, dashboard_service, mospi_service

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
routes_router = APIRouter(prefix="/routes", tags=["routes"])
airlines_router = APIRouter(prefix="/airlines", tags=["reference"])
leadtime_router = APIRouter(prefix="/lead-time", tags=["lead-time"])
anomalies_router = APIRouter(prefix="/anomalies", tags=["anomalies"])
volatility_router = APIRouter(prefix="/volatility", tags=["volatility"])
forecast_router = APIRouter(prefix="/forecast", tags=["forecast"])
backtest_router = APIRouter(prefix="/backtest", tags=["backtest"])
cpi_router = APIRouter(prefix="/cpi-simulation", tags=["cpi"])
quality_router = APIRouter(prefix="/data-quality", tags=["data-quality"])
events_router = APIRouter(prefix="/events", tags=["reference"])


@dashboard_router.get("", summary="Executive dashboard")
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    return envelope(await dashboard_service.get_dashboard(session), meta=ctx.meta())


@routes_router.get("", summary="All tracked routes")
async def list_routes(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await analytics_service.list_routes(session)
    return envelope(data, meta=ctx.meta(count=len(data)))


@routes_router.get("/{route_code}", summary="Route intelligence detail")
async def get_route(
    route_code: str,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    return envelope(await analytics_service.get_route_detail(session, route_code), meta=ctx.meta())


@airlines_router.get("", summary="Airline master")
async def list_airlines(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    from sqlalchemy import select

    from app.db.models import Airline

    rows = (await session.execute(select(Airline).order_by(Airline.name))).scalars()
    data = [
        {
            "airline_code": a.iata_code,
            "name": a.name,
            "airline_type": a.airline_type,
            "is_active": a.is_active,
        }
        for a in rows
    ]
    return envelope(data, meta=ctx.meta(count=len(data)))


@leadtime_router.get("", summary="Lead-time curve and elasticity")
async def get_lead_time(
    route: str | None = Query(default=None, description="Route code, e.g. DEL-BOM"),
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await analytics_service.get_lead_time(session, route)
    by_route = await analytics_service.lead_time_by_route(session)
    return envelope({**data, "by_route": by_route}, meta=ctx.meta())


@anomalies_router.get("", summary="Detected anomalies")
async def list_anomalies(
    severity: str | None = None,
    status: str | None = None,
    route: str | None = None,
    anomaly_class: str = Query(default="MARKET", pattern="^(MARKET|SCRAPER)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data, total = await analytics_service.list_anomalies(
        session, severity, status, route, anomaly_class, page, page_size
    )
    return envelope(data, meta=ctx.meta(count=len(data), total=total, page=page, page_size=page_size))


@anomalies_router.get("/{anomaly_id}", summary="Anomaly detail with factor attribution")
async def get_anomaly(
    anomaly_id: int,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    return envelope(await analytics_service.get_anomaly(session, anomaly_id), meta=ctx.meta())


@volatility_router.get("", summary="Route volatility metrics")
async def get_volatility(
    route: str | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await analytics_service.get_volatility(session, route)
    return envelope(data, meta=ctx.meta(count=len(data)))


@forecast_router.get("", summary="Forecast with prediction intervals")
async def get_forecast(
    scope: str = Query(default="NATIONAL"),
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await analytics_service.get_forecast(session, scope.upper())
    if data is None:
        raise NotFoundError(f"no forecast has been generated for scope '{scope}'")
    return envelope(data, meta=ctx.meta())


@backtest_router.get("", summary="DGCA benchmark back-test")
async def get_backtest(
    backtest_id: int | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await analytics_service.get_backtest(session, backtest_id)
    if data is None:
        raise NotFoundError("no back-test run is available")
    return envelope(data, meta=ctx.meta())


@backtest_router.get(
    "/mospi-comparison",
    summary="Our Headline APIx vs the real MoSPI Airfare CPI, rebased and validated over the real overlap",
)
async def get_mospi_comparison(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await mospi_service.get_mospi_comparison(session)
    if data is None:
        raise NotFoundError("no MoSPI CPI reference data has been ingested")
    return envelope(data, meta=ctx.meta())


@cpi_router.get("", summary="CPI augmentation simulation")
async def get_cpi_simulation(
    weight: float | None = Query(default=None, ge=0, le=100, description="Airfare weight %"),
    vintage: str | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await analytics_service.get_cpi_simulation(session, weight, vintage)
    # Disclaimer set explicitly here AND injected by middleware - two independent
    # mechanisms, because this is the highest-consequence labelling in the product.
    return envelope(data, meta=ctx.meta(), disclaimer=DISCLAIMER)


@quality_router.get("", summary="Collection health and data-quality flags")
async def get_data_quality(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    return envelope(await analytics_service.get_data_quality(session), meta=ctx.meta())


@events_router.get("", summary="Event and holiday calendar")
async def list_events(
    upcoming: bool = False,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    rows = await analytics_repo.events(session, date.today() if upcoming else None)
    data = [
        {
            "event_id": e.event_id,
            "name": e.name,
            "event_type": e.event_type,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "affected_regions": e.affected_regions,
            "notes": e.notes,
        }
        for e in rows
    ]
    return envelope(data, meta=ctx.meta(count=len(data)))
