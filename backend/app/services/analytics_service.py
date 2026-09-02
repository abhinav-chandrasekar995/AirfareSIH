"""Services for routes, lead-time, anomalies, volatility, divergence, forecast,
backtest, CPI and data quality. Each one reads via a repository and computes via the
pure analytics package - no SQL and no statistics live in this layer."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.cpi import simulate as cpi_simulate
from app.analytics.cpi.simulation import sensitivity as cpi_sensitivity
from app.analytics.lead_time.curve import LeadTimePoint
from app.analytics.lead_time.elasticity import estimate_elasticity
from app.analytics.lead_time.premium import (
    booking_pressure,
    early_booking_advantage,
    last_minute_premium,
)
from app.config import settings
from app.core.constants import IndexLevel, LeadBucket
from app.core.exceptions import NotFoundError
from app.db.repositories import analytics_repository as analytics_repo
from app.db.repositories import fare_repository as fare_repo
from app.db.repositories import index_repository as index_repo
from app.pipeline.decompose import reconcile

LEAD_TIME_METHOD_NOTE = (
    "Fares are grouped into the five advance-purchase windows and summarised with the "
    "median. Elasticity is the OLS slope of ln(fare) on ln(lead days) - a model-based "
    "estimate, not a measured quantity."
)


# --------------------------------------------------------------------- routes


async def list_routes(session: AsyncSession) -> list[dict]:
    routes = await analytics_repo.all_routes(session)
    weights = await index_repo.active_weights(session)
    route_index = await index_repo.latest_by_scope(session, IndexLevel.ROUTE)
    volatility = {v.route_id: v for v in await analytics_repo.volatility(session)}

    out = []
    for route in routes:
        row = route_index.get(route.route_code)
        vol = volatility.get(route.route_id)
        out.append(
            {
                "route_code": route.route_code,
                "origin": route.origin.iata_code,
                "destination": route.destination.iata_code,
                "origin_city": route.origin.city,
                "destination_city": route.destination.city,
                "region": route.region,
                "distance_km": float(route.distance_km) if route.distance_km else None,
                "in_basket": route.in_basket,
                "weight": weights.get(route.route_code),
                "current_fare": float(row.median_fare) if row and row.median_fare else None,
                "route_index": float(row.index_value) if row else None,
                "n_observations": row.n_observations if row else 0,
                "volatility_score": vol.volatility_score if vol else None,
            }
        )
    return out


async def get_route_detail(session: AsyncSession, route_code: str) -> dict:
    route = await analytics_repo.route_by_code(session, route_code)
    if route is None:
        raise NotFoundError(f"route '{route_code}' is not tracked")

    weights = await index_repo.active_weights(session)
    index_row = await index_repo.latest(session, IndexLevel.ROUTE, route.route_code)

    today = date.today()
    fares_7d = await index_repo.route_fares(session, route.route_id, date_from=today - timedelta(days=7))
    fares_30d = await index_repo.route_fares(session, route.route_id, date_from=today - timedelta(days=30))
    fares_all = await index_repo.route_fares(session, route.route_id)

    def avg(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    mom = None
    previous = await index_repo.value_on_or_before(
        session, IndexLevel.ROUTE, route.route_code, (index_row.date if index_row else today) - timedelta(days=30)
    )
    if index_row and previous and float(previous.index_value) > 0:
        mom = round(
            (float(index_row.index_value) - float(previous.index_value))
            / float(previous.index_value) * 100, 2
        )

    composition = await fare_repo.composition(session, route.route_id)
    if composition:
        reconciles, _ = reconcile(composition)
        total = composition["total_fare"]
        for key in ("base_fare", "taxes", "udf", "airport_charges", "convenience_fee"):
            composition[f"{key}_pct"] = round(composition[key] / total * 100, 2) if total else 0.0
        composition["reconciles"] = reconciles

    volatility = await analytics_repo.volatility(session, route.route_id)

    return {
        "route_code": route.route_code,
        "origin": route.origin.iata_code,
        "destination": route.destination.iata_code,
        "origin_city": route.origin.city,
        "destination_city": route.destination.city,
        "origin_airport": route.origin.name,
        "destination_airport": route.destination.name,
        "region": route.region,
        "distance_km": float(route.distance_km) if route.distance_km else None,
        "in_basket": route.in_basket,
        "weight": weights.get(route.route_code),
        "route_index": float(index_row.index_value) if index_row else None,
        "current_fare": avg(fares_7d[-20:]) if fares_7d else None,
        "avg_7d": avg(fares_7d),
        "avg_30d": avg(fares_30d),
        "avg_yearly": avg(fares_all),
        "change_mom_pct": mom,
        "n_observations": len(fares_all),
        "trend": [
            {"date": d, "value": v, "n_observations": n}
            for d, v, n in await fare_repo.route_daily_series(session, route.route_id)
        ],
        "airlines": [
            {"airline_code": code, "airline": name, "median_fare": fare, "n_observations": n}
            for code, name, fare, n in await fare_repo.by_airline(session, route.route_id)
        ],
        "sources": await _divergence(session, route.route_id),
        "composition": composition,
        "volatility": (
            {
                "std_dev": float(volatility[0].std_dev or 0),
                "coefficient_of_variation": float(volatility[0].coefficient_of_variation or 0),
                "volatility_score": volatility[0].volatility_score,
                "abnormal_move_frequency": float(volatility[0].abnormal_move_frequency or 0),
            }
            if volatility
            else None
        ),
    }


async def _divergence(session: AsyncSession, route_id: int) -> list[dict]:
    rows = await fare_repo.by_source(session, route_id)
    direct = next((avg for _, _, stype, avg, _, _ in rows if stype == "AIRLINE_DIRECT"), None)
    return [
        {
            "source": name,
            "source_code": code,
            "source_type": stype,
            "avg_fare": round(avg, 2),
            "vs_direct_pct": round((avg - direct) / direct * 100, 2) if direct else None,
            "avg_convenience_fee": round(fee, 2),
            "n_observations": n,
        }
        for code, name, stype, avg, fee, n in rows
    ]


# ------------------------------------------------------------------ lead time


async def get_lead_time(session: AsyncSession, route_code: str | None = None) -> dict:
    route_id = None
    if route_code:
        route = await analytics_repo.route_by_code(session, route_code)
        if route is None:
            raise NotFoundError(f"route '{route_code}' is not tracked")
        route_id = route.route_id

    stored = await analytics_repo.leadtime_curve(session, route_id)
    if stored:
        points = [
            LeadTimePoint(LeadBucket(c.lead_bucket), LeadBucket(c.lead_bucket).days,
                          float(c.avg_fare), c.n_observations)
            for c in sorted(stored, key=lambda c: -LeadBucket(c.lead_bucket).days)
        ]
    else:
        grouped = await fare_repo.fares_by_lead_bucket(session, route_id)
        from app.analytics.lead_time.curve import build_curve

        points = build_curve({LeadBucket(k): v for k, v in grouped.items()})

    if not points:
        return {
            "route_code": route_code,
            "curve": [],
            "elasticity": None,
            "last_minute_premium_pct": None,
            "early_booking_advantage_pct": None,
            "booking_pressure": None,
            "method_note": LEAD_TIME_METHOD_NOTE,
        }

    earliest = points[0].avg_fare
    premium = last_minute_premium(points)
    return {
        "route_code": route_code,
        "curve": [
            {
                "lead_bucket": p.lead_bucket.value,
                "lead_days": p.lead_days,
                "avg_fare": p.avg_fare,
                "n_observations": p.n_observations,
                "vs_earliest_pct": round((p.avg_fare - earliest) / earliest * 100, 2) if earliest else None,
            }
            for p in points
        ],
        "elasticity": estimate_elasticity(points),
        "last_minute_premium_pct": premium,
        "early_booking_advantage_pct": early_booking_advantage(points),
        "booking_pressure": booking_pressure(premium).value if booking_pressure(premium) else None,
        "method_note": LEAD_TIME_METHOD_NOTE,
    }


async def lead_time_by_route(session: AsyncSession) -> list[dict]:
    routes = {r.route_id: r for r in await analytics_repo.all_routes(session)}
    return [
        {
            "route_code": routes[c.route_id].route_code if c.route_id in routes else None,
            "elasticity": float(c.elasticity) if c.elasticity else None,
            "last_minute_premium_pct": float(c.last_minute_premium_pct) if c.last_minute_premium_pct else None,
            "booking_pressure": c.booking_pressure,
        }
        for c in await analytics_repo.leadtime_all_routes(session)
        if c.route_id in routes
    ]


# ------------------------------------------------------------------- anomalies


def _serialise_anomaly(anomaly, route) -> dict:
    return {
        "anomaly_id": anomaly.anomaly_id,
        "route_code": route.route_code,
        "origin_city": route.origin.city,
        "destination_city": route.destination.city,
        "detected_at": anomaly.detected_at,
        "expected_fare": float(anomaly.expected_fare),
        "observed_fare": float(anomaly.observed_fare),
        "deviation_pct": float(anomaly.deviation_pct),
        "severity": anomaly.severity,
        "anomaly_class": anomaly.anomaly_class,
        "lead_bucket": anomaly.lead_bucket,
        "detectors_fired": anomaly.detectors_fired or [],
        "factor_attribution": anomaly.factor_attribution or [],
        "attribution_note": anomaly.attribution_note,
        "status": anomaly.status,
        "model_version": anomaly.model_version,
    }


async def list_anomalies(
    session: AsyncSession,
    severity: str | None = None,
    status: str | None = None,
    route_code: str | None = None,
    anomaly_class: str = "MARKET",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict], int]:
    rows, total = await analytics_repo.anomalies(
        session, severity, status, route_code, anomaly_class, page, page_size
    )
    return [_serialise_anomaly(a, a.route) for a in rows], total


async def get_anomaly(session: AsyncSession, anomaly_id: int) -> dict:
    anomaly = await analytics_repo.anomaly_by_id(session, anomaly_id)
    if anomaly is None:
        raise NotFoundError(f"anomaly {anomaly_id} not found")
    return _serialise_anomaly(anomaly, anomaly.route)


# -------------------------------------------------------------------- forecast


async def get_forecast(session: AsyncSession, scope: str = "NATIONAL") -> dict | None:
    rows = await analytics_repo.forecasts(session, scope)
    if not rows:
        return None

    predictions = [float(r.prediction) for r in rows]
    return {
        "scope": scope,
        "horizon_days": rows[0].horizon_days,
        "confidence_level": float(rows[0].confidence_level),
        "pressure_band": rows[0].pressure_band or "LOW",
        "forecast_range": [round(min(predictions), 2), round(max(predictions), 2)],
        "points": [
            {
                "forecast_date": r.forecast_date,
                "prediction": float(r.prediction),
                "lower_bound": float(r.lower_bound),
                "upper_bound": float(r.upper_bound),
            }
            for r in rows
        ],
        "model_name": rows[0].model_name,
        "model_version": rows[0].model_version,
        "model_comparison": [],
    }


# -------------------------------------------------------------------- backtest


async def get_backtest(session: AsyncSession, backtest_id: int | None = None) -> dict | None:
    run = (
        await analytics_repo.backtest_by_id(session, backtest_id)
        if backtest_id
        else await analytics_repo.latest_backtest(session)
    )
    if run is None:
        return None
    return {
        "backtest_id": run.backtest_id,
        "run_at": run.run_at,
        "route_scope": run.route_scope,
        "estimator": run.estimator,
        "train_start": run.train_start,
        "train_end": run.train_end,
        "test_start": run.test_start,
        "test_end": run.test_end,
        "n_test_days": run.n_test_days,
        "mae": float(run.mae) if run.mae else None,
        "rmse": float(run.rmse) if run.rmse else None,
        "mape": float(run.mape) if run.mape else None,
        "correlation": float(run.correlation) if run.correlation else None,
        "directional_accuracy": float(run.directional_accuracy) if run.directional_accuracy else None,
        "dgca_vintage": run.dgca_vintage,
        "alignment_method": run.alignment_method,
        "series": run.series_json or [],
        "estimator_comparison": [],
    }


# ------------------------------------------------------------------------ cpi


async def get_cpi_simulation(
    session: AsyncSession, weight_pct: float | None = None, vintage: str | None = None
) -> dict:
    cpi = await analytics_repo.latest_cpi(session, vintage)
    if cpi is None:
        raise NotFoundError("no CPI reference data has been ingested")

    national = await index_repo.latest(session, IndexLevel.NATIONAL)
    airfare_index = float(national.index_value) if national else 100.0
    weight = weight_pct if weight_pct is not None else settings.default_cpi_weight_pct

    result = cpi_simulate(float(cpi.cpi_general or 0), airfare_index, weight)
    curve = cpi_sensitivity(float(cpi.cpi_general or 0), airfare_index)

    return {
        "period_month": cpi.period_month,
        "base_cpi": result.base_cpi,
        # Vintage and base year always travel with the number (build prompt Sec.15).
        "cpi_vintage": cpi.series_vintage,
        "cpi_base_year": cpi.base_year,
        "airfare_index": result.airfare_index,
        "airfare_weight_pct": result.weight_pct,
        "augmented_index": result.augmented_index,
        "delta": result.delta,
        "formula": result.formula,
        "sensitivity": [
            {"weight_pct": s.weight_pct, "augmented_index": s.augmented_index, "delta": s.delta}
            for s in curve
        ],
    }


# ---------------------------------------------------------------- data quality


async def get_data_quality(session: AsyncSession) -> dict:
    return {
        "sources": await analytics_repo.source_health(session),
        "flags": [
            {
                "flag_id": f.flag_id,
                "raised_at": f.raised_at,
                "scope_type": f.scope_type,
                "scope_ref": f.scope_ref,
                "flag_type": f.flag_type,
                "severity": f.severity,
                "description": f.description,
                "resolved_at": f.resolved_at,
            }
            for f in await analytics_repo.quality_flags(session, unresolved_only=False)
        ],
        "recent_runs": [
            {
                "run_id": r.run_id,
                "source_id": r.source_id,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "status": r.status,
                "records_found": r.records_found,
                "records_valid": r.records_valid,
                "records_failed": r.records_failed,
                "latency_ms": r.latency_ms,
                "triggered_by": r.triggered_by,
                "error_message": r.error_message,
            }
            for r in await analytics_repo.scrape_runs(session)
        ],
    }


async def get_volatility(session: AsyncSession, route_code: str | None = None) -> list[dict]:
    route_id = None
    if route_code:
        route = await analytics_repo.route_by_code(session, route_code)
        if route is None:
            raise NotFoundError(f"route '{route_code}' is not tracked")
        route_id = route.route_id

    routes = {r.route_id: r.route_code for r in await analytics_repo.all_routes(session)}
    return [
        {
            "route_code": routes.get(v.route_id, ""),
            "date": v.date,
            "window_days": v.window_days,
            "std_dev": float(v.std_dev) if v.std_dev else None,
            "coefficient_of_variation": float(v.coefficient_of_variation) if v.coefficient_of_variation else None,
            "price_range_min": float(v.price_range_min) if v.price_range_min else None,
            "price_range_max": float(v.price_range_max) if v.price_range_max else None,
            "abnormal_move_frequency": float(v.abnormal_move_frequency) if v.abnormal_move_frequency else None,
            "volatility_score": v.volatility_score,
        }
        for v in await analytics_repo.volatility(session, route_id)
    ]
