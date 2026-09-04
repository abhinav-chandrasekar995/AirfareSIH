"""RBI APIx module: Core (base-fare) vs Headline (total-fare) series, the price
breakdown card, and the week-over-week inflation alert. See RBI_APIX_MODULE_LOG.md.

Deliberately its own service file, not additions to index_service.py/dashboard_service.py
- same reasoning as the separate repository module: the existing Headline-series code
paths are DGCA-backtested and stay untouched.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import IndexLevel
from app.db.repositories import core_index_repository as core_repo
from app.db.repositories import index_repository as index_repo

WOW_ALERT_THRESHOLD_PCT = 6.0
ROUTE_SPIKE_THRESHOLD_PCT = 20.0


def _to_point(row) -> dict:
    return {
        "date": row.date,
        "level": row.level,
        "scope": row.scope,
        "index_value": float(row.index_value),
        "n_observations": row.n_observations,
    }


async def get_core_series(
    session: AsyncSession,
    level: IndexLevel = IndexLevel.NATIONAL,
    scope: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    rows = await core_repo.series(session, level, scope, date_from, date_to)
    return [_to_point(r) for r in rows]


async def get_comparison(
    session: AsyncSession, level: IndexLevel = IndexLevel.NATIONAL, scope: str | None = None
) -> dict:
    """Core and Headline series for the same scope, aligned by date, for the toggle /
    dual-line chart. Two independent queries rather than a SQL join - the two tables
    have no foreign relationship by design (see the CoreIndexValue model docstring)."""
    core_rows = await core_repo.series(session, level, scope)
    headline_rows = await index_repo.series(session, level, scope)
    return {
        "core": [_to_point(r) for r in core_rows],
        "headline": [_to_point(r) for r in headline_rows],
    }


async def get_price_breakdown(session: AsyncSession) -> dict | None:
    """Average base fare / taxes+fees / total fare, from the most recent date that has
    any observations at all - "current", not a fixed historical window."""
    latest_date = (
        await session.execute(text("SELECT max(observed_at::date) FROM fare_observations"))
    ).scalar()
    if latest_date is None:
        return None

    row = (
        await session.execute(
            text(
                "SELECT avg(base_fare) AS avg_base, "
                "avg(taxes + udf + airport_charges + convenience_fee) AS avg_taxes_fees, "
                "avg(total_fare) AS avg_total, count(*) AS n "
                "FROM fare_observations WHERE observed_at::date = :d"
            ),
            {"d": latest_date},
        )
    ).mappings().one()

    return {
        "as_of": latest_date,
        "avg_base_fare": round(float(row["avg_base"]), 2) if row["avg_base"] else None,
        "avg_taxes_and_fees": round(float(row["avg_taxes_fees"]), 2) if row["avg_taxes_fees"] else None,
        "avg_total_fare": round(float(row["avg_total"]), 2) if row["avg_total"] else None,
        "n_observations": row["n"],
    }


async def get_alert_status(session: AsyncSession) -> dict:
    """Week-over-week Core APIx threshold check (national), plus a per-route base-fare
    spike check. Deliberately a *different* comparison window than the existing anomaly
    detector (which compares against a 10-60-day-old lead-time-conditioned baseline) -
    this is specifically "how much did the headline policy number move in the last
    week," the RBI-facing question, not a per-observation data-quality check."""
    latest = await core_repo.latest(session, IndexLevel.NATIONAL)
    if latest is None:
        return {"triggered": False, "reason": "no Core APIx data available"}

    week_ago = await core_repo.value_on_or_before(
        session, IndexLevel.NATIONAL, "NATIONAL", latest.date - timedelta(days=7)
    )
    wow_pct = None
    if week_ago and float(week_ago.index_value) > 0:
        wow_pct = round(
            (float(latest.index_value) - float(week_ago.index_value))
            / float(week_ago.index_value)
            * 100,
            2,
        )

    route_rows = await core_repo.series(session, IndexLevel.ROUTE, date_to=latest.date)
    by_route: dict[str, list] = {}
    for r in route_rows:
        by_route.setdefault(r.scope, []).append(r)

    spiking_route = None
    spiking_route_pct = None
    for route_code, points in by_route.items():
        points.sort(key=lambda p: p.date)
        current = next((p for p in reversed(points) if p.date <= latest.date), None)
        if current is None:
            continue
        prior = next(
            (p for p in reversed(points) if p.date <= current.date - timedelta(days=7)), None
        )
        if not prior or float(prior.index_value) <= 0:
            continue
        change = (float(current.index_value) - float(prior.index_value)) / float(prior.index_value) * 100
        if spiking_route_pct is None or abs(change) > abs(spiking_route_pct):
            spiking_route, spiking_route_pct = route_code, round(change, 2)

    national_triggered = wow_pct is not None and wow_pct > WOW_ALERT_THRESHOLD_PCT
    route_triggered = (
        spiking_route_pct is not None and abs(spiking_route_pct) > ROUTE_SPIKE_THRESHOLD_PCT
    )
    triggered = national_triggered or route_triggered

    message = None
    if triggered:
        if route_triggered and (not national_triggered or abs(spiking_route_pct) > (wow_pct or 0)):
            message = (
                f"INFLATION WARNING: Severe base-fare volatility detected on {spiking_route}. "
                f"Core APIx projected to breach RBI tolerance band ({spiking_route_pct:+.1f}% WoW)."
            )
        else:
            message = (
                f"INFLATION WARNING: Core APIx has moved {wow_pct:+.1f}% week-over-week, "
                f"breaching the RBI upper tolerance band (+{WOW_ALERT_THRESHOLD_PCT:.1f}%)."
            )

    return {
        "triggered": triggered,
        "status": "HIGH_INFLATION_RISK" if triggered else "NORMAL",
        "national_wow_pct": wow_pct,
        "national_threshold_pct": WOW_ALERT_THRESHOLD_PCT,
        "spiking_route": spiking_route if route_triggered else None,
        "spiking_route_wow_pct": spiking_route_pct if route_triggered else None,
        "route_threshold_pct": ROUTE_SPIKE_THRESHOLD_PCT,
        "message": message,
        "as_of": latest.date,
    }
