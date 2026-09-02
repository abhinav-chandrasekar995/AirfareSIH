"""Load the deterministic seed into the database.

This does NOT insert pre-baked results. It inserts reference data and observations, then
runs those observations through the SAME analytics code the live pipeline uses to derive
index values, lead-time curves, volatility, anomalies, forecasts, the DGCA back-test and
the CPI simulation. The seeded platform therefore exercises the real statistical path.

Idempotent: it truncates the tables it owns before loading, so `make seed` can be run
repeatedly and always yields the identical dataset (fixed RNG seed).
"""
from __future__ import annotations

import asyncio
import random
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from app.analytics.anomaly import (
    AttributionContext,
    attribute,
    build_baseline,
    classify_severity,
    deviation_pct,
    run_detectors,
)
from app.analytics.backtest import ALIGNMENT_METHOD, all_metrics
from app.analytics.cpi import simulate as cpi_simulate
from app.analytics.forecasting import select_and_forecast
from app.analytics.index_engine import (
    compute_aggregate_index,
    compute_route_index,
    compute_route_measure,
)
from app.analytics.lead_time import (
    booking_pressure,
    build_curve,
    estimate_elasticity,
    last_minute_premium,
)
from app.analytics.volatility import compute_volatility
from app.config import settings
from app.core.constants import Estimator, IndexLevel, LeadBucket
from app.core.security import generate_api_key, hash_key
from app.db.models import (
    Airline,
    Airport,
    Anomaly,
    ApiKey,
    BacktestRun,
    CpiReference,
    CpiSimulation,
    DgcaBenchmark,
    Event,
    FareObservation,
    Forecast,
    IndexValue,
    LeadTimeCurve,
    MethodologyVersion,
    Route,
    RouteWeight,
    ScrapeRun,
    Source,
    VolatilityMetric,
)
from app.db.session import SessionLocal, dispose_engine, get_engine
from seeds.generate_seed import (
    AIRLINES,
    AIRPORTS,
    BASE_FARES,
    BASE_PERIOD,
    BASE_WINDOW_DAYS,
    EVENTS,
    ROUTES,
    SEED,
    SOURCES,
    generate_observations,
    summarise,
)

TODAY = date(2026, 9, 1)
ESTIMATOR = Estimator(settings.default_estimator)
WEIGHT_SET_VERSION = "dgca-traffic-2025q2"

# Region assignment for the four aggregation regions the index publishes.
ROUTE_REGION = {
    "DEL-BOM": "WEST", "DEL-BLR": "SOUTH", "BOM-BLR": "WEST", "DEL-CCU": "EAST",
    "BLR-HYD": "SOUTH", "MAA-DEL": "SOUTH", "BOM-GOI": "WEST", "DEL-HYD": "SOUTH",
    "BOM-AMD": "WEST", "BLR-MAA": "SOUTH", "DEL-JAI": "NORTH", "BOM-COK": "SOUTH",
    "DEL-SXR": "NORTH", "CCU-GAU": "EAST", "DEL-LKO": "NORTH",
}


async def _truncate(session) -> None:
    tables = [
        "cpi_simulations", "backtest_runs", "forecasts", "anomalies",
        "volatility_metrics", "leadtime_curves", "index_values",
        "fare_observations", "fare_observations_raw",
        "route_weights", "routes", "airlines", "airports", "sources",
        "events", "dgca_benchmarks", "cpi_reference", "methodology_versions",
        "api_keys", "audit_log", "data_quality_flags", "scrape_runs",
    ]
    # RLS is FORCED even for the table owner, so loading runs as ADMIN.
    await session.execute(text("SELECT set_config('app.role', 'ADMIN', false)"))
    for table_name in tables:
        await session.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
    await session.commit()


async def _load_reference(session) -> tuple[dict, dict, dict, dict]:
    methodology = MethodologyVersion(
        version=settings.methodology_version,
        description="Baseline methodology: trimmed-mean route measure, DGCA-weighted aggregation.",
        estimator_default=settings.default_estimator,
        quality_threshold=settings.quality_threshold,
        min_observations_per_period=settings.min_observations_per_period,
        base_period=BASE_PERIOD,
        changelog="Initial published methodology.",
    )
    session.add(methodology)

    airports: dict[str, Airport] = {}
    for iata, name, city, state, region, lat, lon in AIRPORTS:
        airport = Airport(
            iata_code=iata, name=name, city=city, state=state, region=region,
            latitude=lat, longitude=lon,
        )
        session.add(airport)
        airports[iata] = airport

    airlines: dict[str, Airline] = {}
    for code, name, atype, _share in AIRLINES:
        airline = Airline(iata_code=code, name=name, airline_type=atype)
        session.add(airline)
        airlines[code] = airline

    sources: dict[str, Source] = {}
    for code, name, stype, url, rpm, reliability in SOURCES:
        source = Source(
            source_code=code, source_name=name, source_type=stype, base_url=url,
            adapter_version="1.0.0", rate_limit_rpm=rpm, reliability_score=reliability,
            status="ACTIVE",
        )
        session.add(source)
        sources[code] = source

    await session.flush()

    routes: dict[str, Route] = {}
    for route_code, distance, _region, weight in ROUTES:
        origin_code, dest_code = route_code.split("-")
        route = Route(
            route_code=route_code,
            origin_id=airports[origin_code].airport_id,
            destination_id=airports[dest_code].airport_id,
            distance_km=distance,
            region=ROUTE_REGION[route_code],
            in_basket=True,
        )
        session.add(route)
        routes[route_code] = route
    await session.flush()

    for route_code, _distance, _region, weight in ROUTES:
        session.add(
            RouteWeight(
                weight_set_version=WEIGHT_SET_VERSION,
                route_id=routes[route_code].route_id,
                weight=weight,
                source_description="DGCA domestic passenger traffic, FY2024-25 (illustrative)",
                effective_from=BASE_PERIOD,
            )
        )

    for name, kind, start, end in EVENTS:
        session.add(Event(name=name, event_type=kind, start_date=start, end_date=end))

    # CPI reference: two vintages, so the UI can demonstrate vintage labelling.
    session.add(
        CpiReference(
            series_vintage="cpi-2024-base", base_year="2024=100",
            weight_source="HCES 2023-24", coicop_version="COICOP 2018",
            period_month=date(2026, 8, 1), cpi_general=142.1,
            cpi_transport_communication=151.4, airfare_sub_index=158.7, airfare_weight_pct=2.5,
        )
    )
    session.add(
        CpiReference(
            series_vintage="cpi-2012-base", base_year="2012=100",
            weight_source="CES 2011-12", coicop_version=None,
            period_month=date(2026, 8, 1), cpi_general=185.3,
            cpi_transport_communication=196.2, airfare_sub_index=204.1, airfare_weight_pct=1.9,
        )
    )

    await session.flush()
    return airports, airlines, sources, routes


def _print_api_keys(session) -> None:
    pass


async def _load_api_keys(session) -> dict[str, str]:
    """Create one key per role. Raw keys are printed once; only hashes are stored."""
    issued: dict[str, str] = {}
    for role, name, rpm in [
        ("ADMIN", "Demo Administrator", 240),
        ("ANALYST", "Demo Analyst (NSO)", 120),
        ("PUBLIC", "Demo Public Consumer", 60),
    ]:
        full_key, prefix = generate_api_key()
        session.add(
            ApiKey(
                key_prefix=prefix, key_hash=hash_key(full_key),
                owner_name=name, owner_org="India Airfare Intelligence (demo)",
                role=role, rate_limit_per_min=rpm, daily_quota=100000,
            )
        )
        issued[role] = full_key
    await session.flush()
    return issued


async def _load_observations(session, airlines, sources, routes) -> None:
    """Insert cleaned observations. The generator already emits clean, reconciled fares,
    so quality scores land in the HIGH band; the pipeline's scoring runs identically on
    live data."""
    from app.pipeline.quality_score import score_observation

    generated = generate_observations(TODAY)
    known_routes = set(routes)
    batch = []
    for obs in generated:
        quality = score_observation(
            {
                "route_code": obs.route_code,
                "airline_code": obs.airline_code,
                "flight_number": obs.flight_number,
                "departure_datetime": obs.departure_datetime,
                "observed_at": obs.observed_at,
                "total_fare": obs.total_fare,
                "base_fare": obs.base_fare,
                "taxes": obs.taxes,
                "udf": obs.udf,
                "airport_charges": obs.airport_charges,
                "convenience_fee": obs.convenience_fee,
                "seats_available": obs.seats_available,
                "availability_status": obs.availability_status,
            },
            source_reliability=100.0,
            is_duplicate=False,
            known_routes=known_routes,
        )
        batch.append(
            {
                "observed_at": obs.observed_at,
                "source_id": sources[obs.source_code].source_id,
                "route_id": routes[obs.route_code].route_id,
                "airline_id": airlines[obs.airline_code].airline_id,
                "flight_number": obs.flight_number,
                "departure_datetime": obs.departure_datetime,
                "lead_days": obs.lead_days,
                "lead_bucket": obs.lead_bucket,
                "fare_class": obs.fare_class,
                "base_fare": obs.base_fare,
                "taxes": obs.taxes,
                "udf": obs.udf,
                "airport_charges": obs.airport_charges,
                "convenience_fee": obs.convenience_fee,
                "total_fare": obs.total_fare,
                "currency": "INR",
                "seats_available": obs.seats_available,
                "availability_status": obs.availability_status,
                "is_outlier": False,
                "imputed_fields": [],
                "quality_score": quality.score,
                "quality_band": quality.band.value,
                "pipeline_version": "pipe-1.0.0",
            }
        )

    # Bulk insert in chunks to keep memory flat on 120k rows.
    for i in range(0, len(batch), 5000):
        await session.execute(FareObservation.__table__.insert(), batch[i : i + 5000])
    await session.commit()
    print(f"  observations inserted: {len(batch)}")


async def _load_scrape_runs(session, sources) -> None:
    """One realistic ScrapeRun per source, derived from the actual seeded data rather
    than invented numbers - so the Collection page's found/valid/failed/success-rate
    fields are consistent with what was really generated instead of showing nulls or
    zeros (the previous state: the seed loader never wrote to scrape_runs at all, so
    every source showed 'last run: never' and 0 for every count).

    "Found" is the count of today's observations attributed to that source before
    quality filtering; "valid" applies each source's configured reliability_score
    (SOURCES tuple in generate_seed.py) as the fraction that passed cleaning, and
    "failed" is the remainder - the same shape a real collection run reports.
    """
    generated = generate_observations(TODAY)
    today_by_source: dict[str, int] = defaultdict(int)
    for o in generated:
        if o.observed_at.date() == TODAY:
            today_by_source[o.source_code] += 1

    reliability_by_code = {code: reliability for code, _n, _t, _u, _r, reliability in SOURCES}
    rng = random.Random(SEED + 1)

    for source_code, source in sources.items():
        found = today_by_source.get(source_code, 0)
        reliability = reliability_by_code.get(source_code, 95.0)
        valid = round(found * (reliability / 100.0))
        failed = max(0, found - valid)
        started = datetime.combine(TODAY, datetime.min.time(), tzinfo=timezone.utc).replace(hour=2, minute=rng.randint(0, 45))
        latency_ms = rng.randint(600, 3400)

        session.add(
            ScrapeRun(
                source_id=source.source_id,
                started_at=started,
                completed_at=started + timedelta(milliseconds=latency_ms * max(1, found // 20)),
                records_found=found,
                records_valid=valid,
                records_failed=failed,
                latency_ms=latency_ms,
                status="SUCCESS" if found > 0 else "PARTIAL",
                adapter_version="1.0.0",
                triggered_by="SCHEDULER",
            )
        )
    await session.commit()
    print(f"  scrape runs seeded: {len(sources)} sources")


def _daily_index_series(observations, route_code) -> list[tuple[date, float]]:
    by_day = defaultdict(list)
    for o in observations:
        if o.route_code == route_code:
            by_day[o.observed_at.date()].append(o.total_fare)
    return [(day, statistics.median(fares)) for day, fares in sorted(by_day.items())]


async def _compute_and_load_derived(session, routes) -> None:
    """Run the real analytics over the generated observations and persist the results."""
    observations = generate_observations(TODAY)
    weights = {r[0]: r[3] for r in ROUTES}

    # --- base-period measures -------------------------------------------------
    base_fares = defaultdict(list)
    for o in observations:
        if BASE_PERIOD <= o.observed_at.date() <= BASE_PERIOD + timedelta(days=BASE_WINDOW_DAYS):
            base_fares[o.route_code].append(o.total_fare)
    base_measures = {
        rc: compute_route_measure(rc, base_fares[rc], ESTIMATOR, settings.min_observations_per_period)
        for rc in weights
    }

    # --- daily route + national index over the last 120 days ------------------
    by_route_day = defaultdict(lambda: defaultdict(list))
    for o in observations:
        by_route_day[o.observed_at.date()][o.route_code].append(o.total_fare)

    index_rows = []
    national_series: list[tuple[date, float]] = []
    regional_series: dict[str, list[tuple[date, float]]] = defaultdict(list)

    span_start = TODAY - timedelta(days=120)
    for day in sorted(d for d in by_route_day if d >= span_start):
        route_indices = []
        region_indices: dict[str, list] = defaultdict(list)
        for route_code, fares in by_route_day[day].items():
            base = base_measures.get(route_code)
            if base is None:
                continue
            measure = compute_route_measure(
                route_code, fares, ESTIMATOR, settings.min_observations_per_period
            )
            if measure is None:
                continue
            ri = compute_route_index(measure, base.value)
            route_indices.append(ri)
            region_indices[ROUTE_REGION[route_code]].append((ri, weights[route_code]))

            index_rows.append(
                IndexValue(
                    date=day, level="ROUTE", scope=route_code,
                    index_value=ri.index_value, base_period=BASE_PERIOD,
                    weight=weights[route_code], estimator=ESTIMATOR.value,
                    mean_fare=ri.variants["mean_fare"], median_fare=ri.variants["median_fare"],
                    trimmed_mean_fare=ri.variants["trimmed_mean_fare"],
                    weighted_median_fare=ri.variants["weighted_median_fare"],
                    n_observations=ri.n_observations, weight_set_version=WEIGHT_SET_VERSION,
                    methodology_version=settings.methodology_version,
                )
            )

        national = compute_aggregate_index(route_indices, weights)
        if national:
            index_rows.append(
                IndexValue(
                    date=day, level="NATIONAL", scope="NATIONAL",
                    index_value=national.index_value, base_period=BASE_PERIOD,
                    estimator=ESTIMATOR.value, n_observations=national.n_observations,
                    weight_set_version=WEIGHT_SET_VERSION,
                    methodology_version=settings.methodology_version, notes=national.notes,
                )
            )
            national_series.append((day, national.index_value))

        for region, pairs in region_indices.items():
            region_agg = compute_aggregate_index(
                [ri for ri, _ in pairs], {ri.route_code: w for ri, w in pairs}
            )
            if region_agg:
                index_rows.append(
                    IndexValue(
                        date=day, level="REGIONAL", scope=region,
                        index_value=region_agg.index_value, base_period=BASE_PERIOD,
                        estimator=ESTIMATOR.value, n_observations=region_agg.n_observations,
                        weight_set_version=WEIGHT_SET_VERSION,
                        methodology_version=settings.methodology_version,
                    )
                )
                regional_series[region].append((day, region_agg.index_value))

    session.add_all(index_rows)
    await session.flush()
    print(f"  index values: {len(index_rows)}")

    # --- lead-time curves (national + per route) ------------------------------
    recent = [o for o in observations if o.observed_at.date() >= TODAY - timedelta(days=30)]
    await _load_leadtime(session, recent, routes, national=True)
    for route_code in weights:
        await _load_leadtime(
            session, [o for o in recent if o.route_code == route_code], routes,
            route_code=route_code,
        )

    # --- volatility -----------------------------------------------------------
    for route_code, route in routes.items():
        series = [v for _, v in _daily_index_series(observations, route_code)][-30:]
        vol = compute_volatility(series)
        if vol:
            session.add(
                VolatilityMetric(
                    route_id=route.route_id, date=TODAY, window_days=30,
                    std_dev=vol.std_dev, coefficient_of_variation=vol.coefficient_of_variation,
                    price_range_min=vol.price_range_min, price_range_max=vol.price_range_max,
                    abnormal_move_frequency=vol.abnormal_move_frequency,
                    volatility_score=vol.volatility_score.value,
                    methodology_version=settings.methodology_version,
                )
            )

    # --- anomalies ------------------------------------------------------------
    await _load_anomalies(session, observations, routes)

    # --- forecast (national) --------------------------------------------------
    await _load_forecast(session, national_series)

    # --- back-test vs DGCA ----------------------------------------------------
    await _load_backtest(session, national_series, routes)

    # --- CPI simulation -------------------------------------------------------
    latest_national = national_series[-1][1] if national_series else 100.0
    sim = cpi_simulate(142.1, latest_national, settings.default_cpi_weight_pct)
    session.add(
        CpiSimulation(
            period_month=date(2026, 8, 1), base_cpi=sim.base_cpi,
            cpi_vintage="cpi-2024-base", cpi_base_year="2024=100",
            airfare_index=sim.airfare_index, airfare_weight_pct=sim.weight_pct,
            augmented_index=sim.augmented_index, scenario_label="Baseline 2.5% weight",
            disclaimer=sim.disclaimer,
        )
    )

    await session.commit()


async def _load_leadtime(session, observations, routes, route_code=None, national=False) -> None:
    buckets = defaultdict(list)
    for o in observations:
        buckets[LeadBucket(o.lead_bucket)].append(o.total_fare)
    curve = build_curve(buckets)
    if not curve:
        return
    premium = last_minute_premium(curve)
    elasticity = estimate_elasticity(curve)
    pressure = booking_pressure(premium)
    route_id = routes[route_code].route_id if route_code else None
    for point in curve:
        session.add(
            LeadTimeCurve(
                route_id=route_id, date=TODAY, lead_bucket=point.lead_bucket.value,
                avg_fare=point.avg_fare, n_observations=point.n_observations,
                elasticity=elasticity, last_minute_premium_pct=premium,
                booking_pressure=pressure.value if pressure else None,
                methodology_version=settings.methodology_version,
            )
        )


async def _load_anomalies(session, observations, routes) -> None:
    """Detect anomalies against the lead-time-conditioned baseline, exactly as the live
    ML task would."""
    count = 0
    for route_code, route in routes.items():
        for bucket in LeadBucket:
            history = [
                o.total_fare for o in observations
                if o.route_code == route_code and o.lead_bucket == bucket.value
                and TODAY - timedelta(days=60) <= o.observed_at.date() <= TODAY - timedelta(days=10)
            ]
            recent = [
                o for o in observations
                if o.route_code == route_code and o.lead_bucket == bucket.value
                and o.observed_at.date() >= TODAY - timedelta(days=2)
            ]
            if len(history) < 10 or not recent:
                continue

            baseline = build_baseline(history, bucket)
            if baseline is None:
                continue
            observed = statistics.median([o.total_fare for o in recent])
            dev = deviation_pct(observed, baseline.expected_fare)
            if abs(dev) < 20:
                continue

            severity = classify_severity(dev)
            detectors = run_detectors(observed, history)
            sample_obs = recent[0]
            factors = attribute(
                AttributionContext(
                    is_weekend=sample_obs.departure_datetime.weekday() in (4, 6),
                    seats_available=sample_obs.seats_available,
                    days_to_event=None,
                    lead_days=bucket.days,
                    is_seasonal_peak=False,
                )
            )
            session.add(
                Anomaly(
                    route_id=route.route_id,
                    detected_at=datetime.now(timezone.utc),
                    fare_period_start=sample_obs.observed_at,
                    fare_period_end=recent[-1].observed_at,
                    expected_fare=baseline.expected_fare, observed_fare=round(observed, 2),
                    deviation_pct=dev, severity=severity, lead_bucket=bucket.value,
                    detectors_fired=detectors, anomaly_class="MARKET",
                    factor_attribution=[{"factor": f.factor, "label": f.label, "pct": f.pct} for f in factors],
                    attribution_note=settings.ATTRIBUTION_NOTE,
                    status="OPEN", model_version="anomaly-1.0.0",
                )
            )
            count += 1
    print(f"  anomalies detected: {count}")


async def _load_forecast(session, national_series) -> None:
    series = [v for _, v in national_series]
    result = select_and_forecast(series, horizon=settings.forecast_horizon_days)
    if result is None:
        print("  forecast: insufficient series length")
        return
    last_date = national_series[-1][0]
    for i, (pred, (lower, upper)) in enumerate(zip(result.predictions, result.bounds), start=1):
        session.add(
            Forecast(
                scope="NATIONAL", forecast_date=last_date + timedelta(days=i),
                horizon_days=settings.forecast_horizon_days,
                prediction=pred, lower_bound=lower, upper_bound=upper,
                confidence_level=result.confidence_level, pressure_band=result.pressure_band,
                model_name=result.model_name, model_version=result.model_version,
                validation_mape=result.validation_mape,
            )
        )
    print(f"  forecast: {result.model_name} (MAPE {result.validation_mape}%), {len(result.predictions)} days")


async def _load_backtest(session, national_series, routes) -> None:
    """Aggregate our daily index to monthly and compare to a DGCA benchmark series.

    The benchmark is derived from our own monthly aggregate with a small realistic offset
    so the demo shows a credible - not suspiciously perfect - correlation. In production
    this row is replaced by ingested DGCA data.
    """
    from app.analytics.backtest import to_monthly

    monthly = to_monthly(national_series)
    if len(monthly) < 2:
        print("  backtest: not enough monthly points")
        return

    import random

    rng = random.Random(42)
    months = sorted(monthly)
    ours = [monthly[m] for m in months]
    # DGCA benchmark tracks ours with modest noise and a slight lag.
    benchmark = [round(v * (1 + rng.gauss(0, 0.03)) + rng.gauss(0, 0.8), 2) for v in ours]

    # Persist a DGCA benchmark series so the ingest is represented in the schema too.
    for m, b in zip(months, benchmark):
        session.add(
            DgcaBenchmark(
                route_id=None, period_month=m, avg_fare=b * 60,  # index -> pseudo-fare scale
                publication_ref="DGCA monthly average domestic fares (illustrative)",
                vintage="dgca-2026",
            )
        )

    metrics = all_metrics(benchmark, ours)
    test_days = max(30, (months[-1] - months[max(0, len(months) - 4)]).days)
    split = max(1, len(months) // 2)

    session.add(
        BacktestRun(
            route_scope="ALL", estimator=ESTIMATOR.value,
            train_start=months[0], train_end=months[split - 1],
            test_start=months[split], test_end=months[-1],
            n_test_days=max(30, test_days),
            mae=metrics["mae"], rmse=metrics["rmse"], mape=metrics["mape"],
            correlation=metrics["correlation"], directional_accuracy=metrics["directional_accuracy"],
            dgca_vintage="dgca-2026", alignment_method=ALIGNMENT_METHOD,
            methodology_version=settings.methodology_version,
            series_json=[
                {"month": m.isoformat(), "ours": o, "dgca": b}
                for m, o, b in zip(months, ours, benchmark)
            ],
        )
    )
    print(f"  backtest: corr={metrics['correlation']} mape={metrics['mape']}%")


async def main() -> None:
    print("Loading India Airfare Intelligence seed dataset...")
    print(f"  seed summary: {summarise(generate_observations(TODAY))}")

    async with SessionLocal() as session:
        await _truncate(session)
        airports, airlines, sources, routes = await _load_reference(session)
        keys = await _load_api_keys(session)
        await session.commit()

        await _load_observations(session, airlines, sources, routes)
        await _load_scrape_runs(session, sources)

        # Reload route ORM objects bound to this session for the derived stage.
        from sqlalchemy import select

        route_map = {
            r.route_code: r for r in (await session.execute(select(Route))).scalars()
        }
        await _compute_and_load_derived(session, route_map)

    await dispose_engine()

    print("\nSeed load complete. Demo API keys (shown once):")
    for role, key in keys.items():
        print(f"  {role:8s} {key}")
    print("\nStore these in frontend/.env.local as needed. Only hashes are in the DB.")


if __name__ == "__main__":
    # Ensure the engine picks up DATABASE_URL from the environment.
    get_engine()
    asyncio.run(main())
