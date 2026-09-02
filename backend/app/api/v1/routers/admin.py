"""Admin endpoints. Every action here is audit-logged and requires the ADMIN role,
enforced by dependency AND by RLS policy on the underlying tables."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ResponseContext, get_context
from app.api.v1.schemas.envelope import envelope
from app.core.exceptions import NotFoundError
from app.db.models import AuditLog, ScrapeRun, Source
from app.db.session import get_session
from app.middleware.auth import Principal, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


def _audit(
    session: AsyncSession,
    request: Request,
    principal: Principal,
    action: str,
    target_type: str | None = None,
    target_ref: str | None = None,
    detail: dict | None = None,
) -> None:
    """Stage an audit row. Deliberately does NOT commit.

    `db/rls.py:apply_principal()` sets the session's RLS role with `set_config(...,
    true)` - scoped to the CURRENT transaction only. A commit here would end that
    transaction and silently drop the role for any further write later in the same
    request (which is exactly what happened before this was fixed: a later UPDATE on
    `scrape_runs` came back "0 rows matched" because RLS quietly filtered it out with no
    role set). One request, one transaction, one commit - the caller commits once, after
    every write it needs is staged.
    """
    session.add(
        AuditLog(
            actor_key_id=principal.key_id,
            actor_label=principal.label,
            action=action,
            target_type=target_type,
            target_ref=target_ref,
            detail=detail,
            ip_address=request.client.host if request.client else None,
        )
    )


@router.post("/collection/trigger", summary="Manually trigger collection for a source")
async def trigger_collection(
    source_code: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
    principal: Principal = Depends(require_admin),
) -> dict:
    source = (
        await session.execute(select(Source).where(Source.source_code == source_code))
    ).scalar_one_or_none()
    if source is None:
        raise NotFoundError(f"unknown source '{source_code}'")

    run = ScrapeRun(
        source_id=source.source_id,
        adapter_version=source.adapter_version,
        triggered_by="MANUAL",
        status="RUNNING",
        started_at=datetime.now(UTC),
    )
    session.add(run)
    await session.flush()

    _audit(
        session, request, principal, "MANUAL_SCRAPE_TRIGGERED", "source", source_code,
        {"run_id": run.run_id},
    )

    from app.tasks.collect_tasks import collect_source

    # `apply_async` is a synchronous, network-calling function. Called directly inside
    # this `async def` handler it would block the ENTIRE ASGI event loop - not just this
    # request, every concurrent request the API is serving - for as long as the broker
    # connection attempt takes. `asyncio.to_thread` moves it off the event loop, and
    # `wait_for` puts a hard ceiling on it independent of whatever Celery/kombu's own
    # timeout settings resolve to (celery_app.py sets broker_connection_retry=False and
    # a 2s connect timeout as the primary fix; this is the defense-in-depth backstop).
    queued = True
    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                collect_source.apply_async, args=[source_code, run.run_id], retry=False
            ),
            timeout=5.0,
        )
    except Exception as exc:
        queued = False
        run.status = "FAILED"
        run.error_message = f"could not reach the task broker: {exc}"

    # One commit for the whole request: the ScrapeRun insert, the audit row, and the
    # possible failure-status update all land in the same transaction the resolved
    # principal's RLS role was set for.
    await session.commit()

    return envelope(
        {"run_id": run.run_id, "source_code": source_code, "status": "QUEUED" if queued else "BROKER_UNAVAILABLE"},
        meta=ctx.meta(
            notes="collection queued; see the Collection page for progress"
            if queued
            else "the task broker could not be reached; the run was recorded but not dispatched"
        ),
    )


@router.get("/audit-log", summary="Sensitive-action audit trail")
async def get_audit_log(
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    ctx: ResponseContext = Depends(get_context),
    principal: Principal = Depends(require_admin),
) -> dict:
    rows = (
        await session.execute(select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit))
    ).scalars()
    data = [
        {
            "audit_id": r.audit_id,
            "occurred_at": r.occurred_at,
            "actor_label": r.actor_label,
            "action": r.action,
            "target_type": r.target_type,
            "target_ref": r.target_ref,
            "detail": r.detail,
        }
        for r in rows
    ]
    return envelope(data, meta=ctx.meta(count=len(data)))
