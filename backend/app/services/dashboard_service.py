"""Dashboard service.

Every KPI and every insight string is derived from computed data. Build prompt Sec.7 is
explicit that insight text must not be hardcoded independently of the underlying data,
so insights here are templates filled from real statistics, and an insight that has no
supporting statistic simply is not emitted.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import IndexLevel
from app.db.repositories import analytics_repository as analytics_repo
from app.db.repositories import fare_repository as fare_repo
from app.db.repositories import index_repository as index_repo
from app.services import index_service

# Pressure banding on deviation of the route index from its own base of 100.
PRESSURE_HIGH = 115.0
PRESSURE_MEDIUM = 105.0


def _pressure_band(index_value: float) -> str:
    if index_value >= PRESSURE_HIGH:
        return "HIGH"
    if index_value >= PRESSURE_MEDIUM:
        return "MEDIUM"
    return "LOW"


async def get_dashboard(session: AsyncSession) -> dict:
    counts = await fare_repo.platform_counts(session)
    national = await index_service.get_summary(session, IndexLevel.NATIONAL)
    increases, decreases = await analytics_repo.index_movers(session, window_days=7, limit=5)
    routes = {r.route_code: r for r in await analytics_repo.all_routes(session)}
    route_index = await index_repo.latest_by_scope(session, IndexLevel.ROUTE)

    def to_mover(entry: dict, direction: str) -> dict | None:
        route = routes.get(entry["route_code"])
        row = route_index.get(entry["route_code"])
        if not route or not row:
            return None
        return {
            "route_code": route.route_code,
            "origin_city": route.origin.city,
            "destination_city": route.destination.city,
            "current_fare": float(row.median_fare or row.trimmed_mean_fare or 0),
            "change_pct": entry["change_pct"],
            "direction": direction,
        }

    top_increases = [m for m in (to_mover(e, "up") for e in increases) if m]
    top_decreases = [m for m in (to_mover(e, "down") for e in decreases) if m]

    pressure_map = [
        {
            "route_code": code,
            "origin": routes[code].origin.iata_code,
            "destination": routes[code].destination.iata_code,
            "origin_lat": float(routes[code].origin.latitude),
            "origin_lon": float(routes[code].origin.longitude),
            "destination_lat": float(routes[code].destination.latitude),
            "destination_lon": float(routes[code].destination.longitude),
            "origin_city": routes[code].origin.city,
            "destination_city": routes[code].destination.city,
            "region": routes[code].region,
            "index_value": float(row.index_value),
            "pressure": _pressure_band(float(row.index_value)),
        }
        for code, row in route_index.items()
        if code in routes
    ]

    insights = await _build_insights(session, national, top_increases, pressure_map)

    return {
        "index_value": national["current_value"] if national else None,
        "index_change_mom_pct": national["change_pct"] if national else None,
        "routes_tracked": counts["routes_tracked"],
        "airlines_tracked": counts["airlines_tracked"],
        "ota_sources": counts["ota_sources"],
        "flights_monitored": counts["flights_monitored"],
        "total_data_points": counts["total_data_points"],
        "base_period": date.fromisoformat(settings.index_base_period),
        "as_of": national["as_of"] if national else None,
        "top_increases": top_increases,
        "top_decreases": top_decreases,
        "insights": insights,
        "pressure_map": pressure_map,
    }


async def _build_insights(
    session: AsyncSession,
    national: dict | None,
    top_increases: list[dict],
    pressure_map: list[dict],
) -> list[dict]:
    """Generate insight cards from computed statistics only.

    Each insight carries the metric that produced it, so a reader can check the claim
    rather than take it on trust.
    """
    insights: list[dict] = []

    if national and national.get("change_pct") is not None:
        change = national["change_pct"]
        direction = "above" if change > 0 else "below"
        insights.append(
            {
                "id": "national-mom",
                "text": (
                    f"The national airfare index stands at {national['current_value']:.1f}, "
                    f"{abs(change):.1f}% {direction} its level 30 days ago."
                ),
                "severity": "warning" if change > 5 else "info",
                "href": "/index",
                "metric": change,
            }
        )

    if top_increases:
        top = top_increases[0]
        insights.append(
            {
                "id": "top-riser",
                "text": (
                    f"{top['origin_city']} to {top['destination_city']} shows the largest "
                    f"7-day increase at {top['change_pct']:+.1f}%."
                ),
                "severity": "warning" if top["change_pct"] > 10 else "info",
                "href": f"/routes/{top['route_code']}",
                "metric": top["change_pct"],
            }
        )

    high_pressure = [p for p in pressure_map if p["pressure"] == "HIGH"]
    if high_pressure:
        insights.append(
            {
                "id": "pressure-breadth",
                "text": (
                    f"{len(high_pressure)} of {len(pressure_map)} tracked routes are under "
                    f"high price pressure, indicating broad rather than isolated movement."
                ),
                "severity": "warning" if len(high_pressure) > len(pressure_map) / 3 else "info",
                "href": "/anomalies",
                "metric": float(len(high_pressure)),
            }
        )

    curve = await analytics_repo.leadtime_curve(session, route_id=None)
    premium = next((float(c.last_minute_premium_pct) for c in curve if c.last_minute_premium_pct), None)
    if premium:
        insights.append(
            {
                "id": "lead-time-premium",
                "text": (
                    f"Booking at T+1 instead of T+45 costs {premium:.0f}% more on average "
                    f"across the tracked basket."
                ),
                "severity": "warning" if premium > 90 else "info",
                "href": "/lead-time",
                "metric": premium,
            }
        )

    flags = await analytics_repo.quality_flags(session, unresolved_only=True, limit=5)
    if flags:
        insights.append(
            {
                "id": "data-quality",
                "text": (
                    f"{len(flags)} unresolved data-quality flag(s) are open; affected "
                    f"observations are excluded from index computation."
                ),
                "severity": "warning",
                "href": "/collection",
                "metric": float(len(flags)),
            }
        )

    return insights
