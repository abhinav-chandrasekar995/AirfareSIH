"""RBI APIx module endpoints: Core vs Headline series, price breakdown, WoW alert.

New, additive namespace (/api/v1/apix/*) rather than extending /index - the existing
index endpoints are DGCA-backtested and stay untouched. See RBI_APIX_MODULE_LOG.md.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ResponseContext, get_context
from app.api.v1.schemas.envelope import envelope
from app.core.constants import IndexLevel
from app.db.session import get_session
from app.services import apix_service

router = APIRouter(prefix="/apix", tags=["apix"])


@router.get("/core", summary="Core APIx series (base-fare only)")
async def get_core_series(
    level: IndexLevel = Query(default=IndexLevel.NATIONAL),
    scope: str | None = Query(default=None, description="Region name, route code or airline code"),
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await apix_service.get_core_series(session, level, scope, date_from, date_to)
    return envelope(data, meta=ctx.meta(count=len(data)))


@router.get("/comparison", summary="Core and Headline APIx series together, for the toggle chart")
async def get_comparison(
    level: IndexLevel = Query(default=IndexLevel.NATIONAL),
    scope: str | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await apix_service.get_comparison(session, level, scope)
    return envelope(data, meta=ctx.meta())


@router.get("/price-breakdown", summary="Average base fare / taxes & fees / total fare, most recent day")
async def get_price_breakdown(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await apix_service.get_price_breakdown(session)
    return envelope(data, meta=ctx.meta())


@router.get("/alert", summary="Week-over-week Core APIx inflation alert status")
async def get_alert(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await apix_service.get_alert_status(session)
    return envelope(data, meta=ctx.meta())
