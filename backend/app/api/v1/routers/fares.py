"""Data Explorer endpoints: observation search, raw-vs-cleaned comparison, export."""
from __future__ import annotations

import csv
import io
import json
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ResponseContext, get_context
from app.api.v1.schemas.envelope import envelope
from app.core.exceptions import NotFoundError
from app.db.repositories import fare_repository as fare_repo
from app.db.session import get_session
from app.middleware.auth import Principal, require_analyst

router = APIRouter(prefix="/fares", tags=["fares"])

# Exports are capped. An uncapped export of a multi-million-row observation table is a
# denial-of-service against our own database (build prompt Sec.18).
MAX_EXPORT_ROWS = 10_000

EXPORT_COLUMNS = [
    "observed_at", "route_code", "origin", "destination", "airline_code", "airline",
    "flight_number", "departure_datetime", "lead_days", "lead_bucket", "fare_class",
    "base_fare", "taxes", "udf", "airport_charges", "convenience_fee", "total_fare",
    "source", "source_type", "seats_available", "availability_status",
    "is_outlier", "quality_score", "quality_band",
]


def _serialise(observation) -> dict:
    return {
        "observation_id": observation.observation_id,
        "observed_at": observation.observed_at,
        "route_code": observation.route.route_code,
        "origin": observation.route.origin.iata_code,
        "destination": observation.route.destination.iata_code,
        "airline": observation.airline.name,
        "airline_code": observation.airline.iata_code,
        "flight_number": observation.flight_number,
        "departure_datetime": observation.departure_datetime,
        "lead_days": observation.lead_days,
        "lead_bucket": observation.lead_bucket,
        "fare_class": observation.fare_class,
        "base_fare": float(observation.base_fare),
        "taxes": float(observation.taxes),
        "udf": float(observation.udf),
        "airport_charges": float(observation.airport_charges),
        "convenience_fee": float(observation.convenience_fee),
        "total_fare": float(observation.total_fare),
        "source": observation.source.source_name,
        "source_type": observation.source.source_type,
        "seats_available": observation.seats_available,
        "availability_status": observation.availability_status,
        "is_outlier": observation.is_outlier,
        "imputed_fields": observation.imputed_fields or [],
        "quality_score": float(observation.quality_score),
        "quality_band": observation.quality_band,
    }


@router.get("", summary="Search fare observations")
async def search_fares(
    route: str | None = None,
    airline: str | None = None,
    source: str | None = None,
    fare_class: str | None = None,
    lead_bucket: str | None = None,
    quality_min: float | None = Query(default=None, ge=0, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
) -> dict:
    conditions = fare_repo.build_filter(
        route, airline, source, fare_class, lead_bucket, quality_min, date_from, date_to
    )
    rows, total = await fare_repo.search(session, conditions, page, page_size)
    data = [_serialise(r) for r in rows]
    return envelope(data, meta=ctx.meta(count=len(data), total=total, page=page, page_size=page_size))


@router.get("/{observation_id}/raw", summary="Raw payload behind a cleaned observation")
async def get_raw(
    observation_id: int,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
    principal: Principal = Depends(require_analyst),
) -> dict:
    """The raw-vs-cleaned comparison that makes the pipeline auditable."""
    rows, _ = await fare_repo.search(session, [], page=1, page_size=1)
    cleaned = next((r for r in rows if r.observation_id == observation_id), None)
    if cleaned is None:
        from sqlalchemy import select

        from app.db.models import FareObservation

        cleaned = (
            await session.execute(
                select(FareObservation).where(FareObservation.observation_id == observation_id)
            )
        ).scalar_one_or_none()
    if cleaned is None:
        raise NotFoundError(f"observation {observation_id} not found")

    raw = await fare_repo.raw_for_observation(session, cleaned.raw_id) if cleaned.raw_id else None
    return envelope(
        {
            "cleaned": _serialise(cleaned),
            "raw": {
                "raw_id": raw.raw_id,
                "observed_at": raw.observed_at,
                "adapter_version": raw.adapter_version,
                "payload": raw.payload,
            }
            if raw
            else None,
            "imputed_fields": cleaned.imputed_fields or [],
            "is_outlier": cleaned.is_outlier,
        },
        meta=ctx.meta(),
    )


@router.get("/export", summary="Export the filtered observation set")
async def export_fares(
    fmt: str = Query(default="csv", pattern="^(csv|json)$"),
    route: str | None = None,
    airline: str | None = None,
    source: str | None = None,
    quality_min: float | None = Query(default=None, ge=0, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=1000, ge=1, le=MAX_EXPORT_ROWS),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require_analyst),
) -> StreamingResponse:
    conditions = fare_repo.build_filter(
        route, airline, source, None, None, quality_min, date_from, date_to
    )
    rows, _ = await fare_repo.search(session, conditions, page=1, page_size=limit)
    records = [_serialise(r) for r in rows]

    if fmt == "json":
        payload = json.dumps(records, default=str, indent=2)
        return StreamingResponse(
            io.StringIO(payload),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=airfare_observations.json"},
        )

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow({k: record.get(k) for k in EXPORT_COLUMNS})
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=airfare_observations.csv"},
    )
