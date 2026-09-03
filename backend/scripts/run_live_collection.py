"""One real, deliberate live-collection run: SerpApi (Google Flights) -> Tier 0 raw
archive -> the real Stage 2 pipeline (app/pipeline/pipeline_runner.run_pipeline, the
same function production collection would use) -> Tier 1 fare_observations -> a real
route/national/regional Airfare Index for TODAY (the actual calendar date this script
runs, not the seed's fixed 2026-09-01).

Consumes up to 15 routes x 5 lead-buckets = 75 SerpApi queries - run once, by hand, not
on a schedule. Every raw API response is archived to data/raw/ before anything is
parsed, matching this project's own debugging-archive convention.

Deliberately standalone rather than going through Celery: app/tasks/pipeline_tasks.py's
process_pending() and app/tasks/analytics_tasks.py's compute_all_indices() are both
still stubs (log a line, return COMPLETE) - the real work they'd eventually wrap already
exists as pure, tested functions, which is what this script calls directly.
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, text

from app.config import settings

# In-process only - this script is the explicit, manual trigger; it does not flip the
# app's own persisted default, which stays off for the scheduler.
settings.collection_enabled = True

from app.analytics.index_engine import (
    compute_aggregate_index,
    compute_route_index,
    compute_route_measure,
)
from app.collection.base_adapter import FareQuery
from app.collection.guards import build_guards
from app.collection.orchestrator import build_work_matrix
from app.collection.registry import get_adapter
from app.core.constants import Estimator, IndexLevel, LeadBucket, ScrapeStatus
from app.db.models import (
    Airline,
    FareObservation,
    FareObservationRaw,
    IndexValue,
    Route,
    ScrapeRun,
    Source,
)
from app.db.session import SessionLocal, dispose_engine
from app.pipeline.pipeline_runner import run_pipeline
from seeds.generate_seed import BASE_PERIOD, BASE_WINDOW_DAYS, ROUTES
from seeds.load_seed import ROUTE_REGION, WEIGHT_SET_VERSION

SOURCE_CODE = "google_flights"
TODAY = date.today()
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ROUTE_WEIGHTS = {r[0]: r[3] for r in ROUTES}

# Optional pilot scope: `python run_live_collection.py DEL-BOM DEL-BLR` runs only those
# routes (still all 5 lead-buckets each) instead of the full 15-route basket - a cheap
# way to validate the whole DB-write path before committing the rest of the quota to it.
ROUTE_CODES = sys.argv[1:] if len(sys.argv) > 1 else [r[0] for r in ROUTES]


async def ensure_source(session) -> int:
    result = await session.execute(select(Source).where(Source.source_code == SOURCE_CODE))
    source = result.scalar_one_or_none()
    if source:
        return source.source_id
    source = Source(
        source_code=SOURCE_CODE,
        source_name="Google Flights (via SerpApi)",
        source_type="AGGREGATOR",
        base_url="https://serpapi.com",
        adapter_version="1.0.0",
        rate_limit_rpm=6,
        status="ACTIVE",
        reliability_score=100.0,
    )
    session.add(source)
    await session.flush()
    print(f"  created sources row for '{SOURCE_CODE}' (source_id={source.source_id})")
    return source.source_id


async def collect_all_routes() -> tuple[list[dict], dict]:
    """Runs the real guarded adapter (rate limit, circuit breaker, challenge detection)
    across every (route, lead-bucket) pair. Returns (all parsed observations, stats)."""
    plan = build_work_matrix(ROUTE_CODES, [SOURCE_CODE], reference_date=TODAY)
    guards = build_guards(redis=None, respect_robots=settings.respect_robots_txt)
    adapter = get_adapter(SOURCE_CODE)(guards=guards, cache=None)

    all_observations: list[dict] = []
    stats = {"queries": len(plan), "succeeded": 0, "failed": 0, "skipped": 0, "total_flights": 0}

    for i, (source_code, query) in enumerate(plan.queries, start=1):
        print(
            f"[{i}/{len(plan)}] {query.route_code} {query.lead_bucket.value} "
            f"(departs {query.departure_date.isoformat()})...",
            end=" ",
            flush=True,
        )
        result = await adapter.collect(query)

        if result.status in (ScrapeStatus.SUCCESS, ScrapeStatus.PARTIAL):
            stats["succeeded"] += 1
            stats["total_flights"] += len(result.observations)
            all_observations.extend(result.observations)
            print(f"OK - {len(result.observations)} flights")
        elif result.status in (ScrapeStatus.SKIPPED_ROBOTS, ScrapeStatus.SKIPPED_CHALLENGE):
            stats["skipped"] += 1
            print(f"SKIPPED ({result.status.value}): {result.error_message}")
        else:
            stats["failed"] += 1
            print(f"FAILED ({result.status.value}): {result.error_message}")

    # Archive every parsed observation this run collected, in one file, alongside the
    # per-query raw JSON already saved during development (test_serpapi_single_query.py).
    archive_path = RAW_DIR / f"live_collection_{TODAY.isoformat()}.json"
    archive_path.write_text(
        json.dumps(all_observations, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nArchived {len(all_observations)} parsed observations to {archive_path}")
    return all_observations, stats


async def persist_raw_and_scrape_run(session, source_id: int, observations: list[dict], stats: dict) -> None:
    started = datetime.now(timezone.utc)
    scrape_run = ScrapeRun(
        source_id=source_id,
        started_at=started,
        completed_at=started,
        records_found=stats["total_flights"],
        records_valid=stats["total_flights"],
        records_failed=0,
        latency_ms=0,
        status="SUCCESS" if stats["succeeded"] else "PARTIAL",
        adapter_version="1.0.0",
        triggered_by="MANUAL",
    )
    session.add(scrape_run)
    await session.flush()

    for obs in observations:
        session.add(
            FareObservationRaw(
                observed_at=obs["observed_at"],
                source_id=source_id,
                scrape_run_id=scrape_run.run_id,
                # build_observation()'s output has origin/destination, not a combined
                # route_code key - construct it the same way FareQuery.origin/
                # destination do (route_code.split("-")), just in reverse.
                route_code=f"{obs['origin']}-{obs['destination']}",
                payload=json.loads(json.dumps(obs, default=str)),
                adapter_version="1.0.0",
            )
        )
    await session.commit()
    print(f"  persisted {len(observations)} Tier-0 raw rows under scrape_run_id={scrape_run.run_id}")


async def persist_cleaned_observations(session, route_ids: dict[str, int], airline_ids: dict[str, int], observations: list[dict]) -> list:
    result = run_pipeline(
        observations,
        source_reliability={SOURCE_CODE: 100.0},
        known_routes=set(ROUTE_CODES),
    )
    print(
        f"  pipeline: {result.stats['received']} received -> {result.stats['cleaned']} cleaned, "
        f"{result.stats['rejected']} rejected, {result.stats['duplicates']} duplicates, "
        f"{result.stats['outliers_flagged']} outliers flagged"
    )

    inserted = 0
    for c in result.cleaned:
        route_id = route_ids.get(c.route_code)
        airline_id = airline_ids.get(c.airline_code)
        if route_id is None or airline_id is None:
            continue  # not one of this basket's tracked routes/airlines
        session.add(
            FareObservation(
                # raw_id intentionally left unset for this live run - see
                # IMPLEMENTATION_LOG.md for why exact raw_id back-reference was scoped
                # out rather than reconstructed through the pipeline's own reordering.
                observed_at=c.observed_at,
                source_id=source_ids_cache[SOURCE_CODE],
                route_id=route_id,
                airline_id=airline_id,
                flight_number=c.flight_number,
                departure_datetime=c.departure_datetime,
                lead_days=c.lead_days,
                lead_bucket=c.lead_bucket,
                fare_class=c.fare_class,
                base_fare=c.base_fare,
                taxes=c.taxes,
                udf=c.udf,
                airport_charges=c.airport_charges,
                convenience_fee=c.convenience_fee,
                total_fare=c.total_fare,
                currency=c.currency,
                seats_available=c.seats_available,
                availability_status=c.availability_status,
                is_outlier=c.is_outlier,
                imputed_fields=c.imputed_fields or None,
                quality_score=c.quality_score,
                quality_band=c.quality_band,
                pipeline_version=c.pipeline_version,
            )
        )
        inserted += 1
    await session.commit()
    print(f"  persisted {inserted} Tier-1 fare_observations rows")
    return result.cleaned


source_ids_cache: dict[str, int] = {}


async def compute_and_persist_index(session, route_ids: dict[str, int]) -> None:
    """Recomputes TODAY's entire index (route/national/regional) fresh from whatever
    real fare_observations exist for today in the database - not just this run's
    in-memory batch. That's what makes running this script multiple times across
    different route subsets (e.g. a pilot, then the rest of the basket) safe: each run
    re-derives a consistent, complete picture instead of accumulating duplicate or
    partial NATIONAL/REGIONAL rows for the same date."""
    # Wipe today's previously-computed index rows (any level) before recomputing, so
    # re-running this script never leaves stale or duplicate rows behind for this date.
    await session.execute(text("DELETE FROM index_values WHERE date = :d"), {"d": TODAY})

    # Base-period measure per route, from the existing (synthetic) fare_observations -
    # a live run indexes against the SAME fixed base period the whole system already
    # uses, exactly like adding a new day of real prices to any CPI-style series would.
    base_window_end = BASE_PERIOD + timedelta(days=BASE_WINDOW_DAYS)
    base_measures: dict[str, object] = {}
    fares_by_route: dict[str, list[float]] = defaultdict(list)
    for route_code, route_id in route_ids.items():
        base_rows = (
            await session.execute(
                text(
                    "SELECT total_fare FROM fare_observations "
                    "WHERE route_id = :rid AND observed_at::date BETWEEN :start AND :end"
                ),
                {"rid": route_id, "start": BASE_PERIOD, "end": base_window_end},
            )
        ).scalars().all()
        measure = compute_route_measure(route_code, [float(f) for f in base_rows], Estimator.TRIMMED_MEAN_10)
        if measure:
            base_measures[route_code] = measure

        today_rows = (
            await session.execute(
                text(
                    "SELECT total_fare FROM fare_observations "
                    "WHERE route_id = :rid AND observed_at::date = :d AND source_id = :sid"
                ),
                {"rid": route_id, "d": TODAY, "sid": source_ids_cache[SOURCE_CODE]},
            )
        ).scalars().all()
        if today_rows:
            fares_by_route[route_code] = [float(f) for f in today_rows]

    route_indices = []
    index_rows = []
    for route_code, fares in fares_by_route.items():
        base = base_measures.get(route_code)
        if base is None:
            continue
        measure = compute_route_measure(route_code, fares, Estimator.TRIMMED_MEAN_10)
        if measure is None:
            continue
        ri = compute_route_index(measure, base.value)
        route_indices.append(ri)
        index_rows.append(
            IndexValue(
                date=TODAY,
                level=IndexLevel.ROUTE.value,
                scope=route_code,
                index_value=ri.index_value,
                base_period=BASE_PERIOD,
                weight=ROUTE_WEIGHTS.get(route_code),
                estimator=Estimator.TRIMMED_MEAN_10.value,
                mean_fare=ri.variants.get("mean_fare"),
                median_fare=ri.variants.get("median_fare"),
                trimmed_mean_fare=ri.variants.get("trimmed_mean_fare"),
                weighted_median_fare=ri.variants.get("weighted_median_fare"),
                n_observations=ri.n_observations,
                weight_set_version=WEIGHT_SET_VERSION,
                methodology_version=settings.methodology_version,
            )
        )

    if route_indices:
        national = compute_aggregate_index(route_indices, ROUTE_WEIGHTS)
        if national:
            index_rows.append(
                IndexValue(
                    date=TODAY,
                    level=IndexLevel.NATIONAL.value,
                    scope="NATIONAL",
                    index_value=national.index_value,
                    base_period=BASE_PERIOD,
                    estimator=Estimator.TRIMMED_MEAN_10.value,
                    n_observations=national.n_observations,
                    weight_set_version=WEIGHT_SET_VERSION,
                    methodology_version=settings.methodology_version,
                    notes=national.notes,
                )
            )

        region_indices: dict[str, list] = defaultdict(list)
        for ri in route_indices:
            region_indices[ROUTE_REGION[ri.route_code]].append(ri)
        for region, ris in region_indices.items():
            region_weights = {ri.route_code: ROUTE_WEIGHTS[ri.route_code] for ri in ris}
            regional = compute_aggregate_index(ris, region_weights)
            if regional:
                index_rows.append(
                    IndexValue(
                        date=TODAY,
                        level=IndexLevel.REGIONAL.value,
                        scope=region,
                        index_value=regional.index_value,
                        base_period=BASE_PERIOD,
                        estimator=Estimator.TRIMMED_MEAN_10.value,
                        n_observations=regional.n_observations,
                        weight_set_version=WEIGHT_SET_VERSION,
                        methodology_version=settings.methodology_version,
                    )
                )

    session.add_all(index_rows)
    await session.commit()
    print(f"\n  persisted {len(index_rows)} index_values rows for {TODAY.isoformat()} "
          f"({len(route_indices)} route, {'1' if route_indices else '0'} national, "
          f"{len(set(ROUTE_REGION[ri.route_code] for ri in route_indices))} regional)")
    if route_indices:
        print("\n  Route indices computed today:")
        for ri in sorted(route_indices, key=lambda r: r.route_code):
            print(f"    {ri.route_code}: {ri.index_value}  (n={ri.n_observations}, base={ri.base_measure})")


async def main() -> None:
    if not settings.serpapi_key:
        print("SERPAPI_KEY is not set - aborting before spending any quota.")
        return

    print(f"Live collection run for {TODAY.isoformat()} - {len(ROUTE_CODES)} routes x "
          f"{len(LeadBucket)} lead-buckets = up to {len(ROUTE_CODES) * len(LeadBucket)} queries\n")

    observations, stats = await collect_all_routes()
    print(f"\nCollection summary: {stats['succeeded']} succeeded, {stats['skipped']} skipped, "
          f"{stats['failed']} failed, {stats['total_flights']} total flight quotes\n")

    if not observations:
        print("No observations collected - nothing to persist.")
        return

    async with SessionLocal() as session:
        await session.execute(text("SELECT set_config('app.role', 'ADMIN', false)"))

        source_id = await ensure_source(session)
        source_ids_cache[SOURCE_CODE] = source_id
        await session.commit()

        routes = (await session.execute(select(Route))).scalars().all()
        route_ids = {r.route_code: r.route_id for r in routes}
        airlines = (await session.execute(select(Airline))).scalars().all()
        airline_ids = {a.iata_code: a.airline_id for a in airlines}

        await persist_raw_and_scrape_run(session, source_id, observations, stats)
        await persist_cleaned_observations(session, route_ids, airline_ids, observations)
        await compute_and_persist_index(session, route_ids)

    await dispose_engine()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
