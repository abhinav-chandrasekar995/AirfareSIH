"""Index endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ResponseContext, get_context
from app.api.v1.schemas.envelope import envelope
from app.core.constants import Estimator, IndexLevel
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.services import index_service

router = APIRouter(prefix="/index", tags=["index"])


@router.get("", summary="Index series")
async def get_index(
    level: IndexLevel = Query(default=IndexLevel.NATIONAL),
    scope: str | None = Query(default=None, description="Region name, route code or airline code"),
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await index_service.get_series(session, level, scope, date_from, date_to)
    return envelope(data, meta=ctx.meta(count=len(data)))


@router.get("/summary", summary="Headline index with movement")
async def get_summary(
    level: IndexLevel = Query(default=IndexLevel.NATIONAL),
    scope: str | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    summary = await index_service.get_summary(session, level, scope)
    regional = await index_service.get_regional_summaries(session)
    return envelope({"headline": summary, "regional": regional}, meta=ctx.meta())


@router.get("/methodology", summary="How the index is constructed")
async def get_methodology(
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    return envelope(await index_service.get_methodology(session), meta=ctx.meta())


@router.get("/verify", summary="Recompute the national index live from observations")
async def verify_index(
    as_of: date | None = None,
    estimator: Estimator | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    """Reproducibility check.

    Recomputes the headline number from stored observations rather than reading back a
    cached row, so a reader can confirm the published value is derivable.
    """
    result = await index_service.recompute_national(session, as_of or date.today(), estimator)
    return envelope(result, meta=ctx.meta(notes="recomputed live from stored observations"))


@router.get("/route/{route_code}", summary="Route index series")
async def get_route_index(
    route_code: str,
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    data = await index_service.get_series(
        session, IndexLevel.ROUTE, route_code.upper(), date_from, date_to
    )
    if not data:
        raise NotFoundError(f"no index series for route '{route_code}'")
    return envelope(data, meta=ctx.meta(count=len(data)))
