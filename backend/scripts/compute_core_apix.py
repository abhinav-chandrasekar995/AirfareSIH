"""Backfills the Core APIx (base-fare-only) series across the ENTIRE existing
fare_observations history - not just "today". base_fare has always been a separate
column, for every observation ever inserted (synthetic seed and live SerpApi rows
alike), so Core APIx gets the exact same historical depth as the existing Headline
(total_fare) series immediately, with no waiting for new days to accumulate.

Reuses the real index engine functions (compute_route_measure/compute_route_index/
compute_aggregate_index) - the only difference from the existing Headline computation is
which fare column feeds them. Idempotent: wipes and recomputes every date each run, same
principle as run_live_collection.py's index step, for the same reason (safe to re-run
after new data arrives without producing duplicates).
"""
from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.analytics.index_engine import (
    compute_aggregate_index,
    compute_route_measure,
    compute_route_index,
)
from app.config import settings
from app.core.constants import Estimator, IndexLevel
from app.db.models import CoreIndexValue, Route
from app.db.session import SessionLocal, dispose_engine
from seeds.generate_seed import BASE_PERIOD, BASE_WINDOW_DAYS, ROUTES
from seeds.load_seed import ROUTE_REGION, TODAY as SEED_TODAY, WEIGHT_SET_VERSION
from sqlalchemy import select

ROUTE_WEIGHTS = {r[0]: r[3] for r in ROUTES}

# Match the Headline (total_fare) series' own window exactly - generate_seed.py/
# load_seed.py restrict Headline to the last 120 days from the seed's reference "today",
# even though raw fare_observations actually goes back to 2025-07-28 (403 distinct
# days). Toggling Core/Headline on the same chart needs a consistent x-axis range;
# computing Core over the full raw history would make the two series' available date
# ranges wildly different for no methodological reason.
SPAN_START = SEED_TODAY - timedelta(days=120)


async def main() -> None:
    async with SessionLocal() as session:
        await session.execute(text("SELECT set_config('app.role', 'ADMIN', false)"))

        routes = (await session.execute(select(Route))).scalars().all()
        route_id_to_code = {r.route_id: r.route_code for r in routes}

        print("Loading all fare_observations (date, route, base_fare)...")
        rows = (
            await session.execute(
                text(
                    "SELECT observed_at::date AS d, route_id, base_fare "
                    "FROM fare_observations WHERE base_fare IS NOT NULL AND base_fare > 0"
                )
            )
        ).all()
        print(f"  {len(rows)} rows loaded")

        by_route_day: dict = defaultdict(lambda: defaultdict(list))
        for d, route_id, base_fare in rows:
            code = route_id_to_code.get(route_id)
            if code:
                by_route_day[d][code].append(float(base_fare))

        base_window_end = BASE_PERIOD + timedelta(days=BASE_WINDOW_DAYS)

        # Base-period measure per route, from base_fare within the fixed base window -
        # exactly mirroring how the Headline series' own base measure is derived.
        base_fares_by_route: dict = defaultdict(list)
        for d, route_fares in by_route_day.items():
            if BASE_PERIOD <= d <= base_window_end:
                for route_code, fares in route_fares.items():
                    base_fares_by_route[route_code].extend(fares)

        base_measures = {}
        for route_code, fares in base_fares_by_route.items():
            m = compute_route_measure(route_code, fares, Estimator.TRIMMED_MEAN_10)
            if m:
                base_measures[route_code] = m

        print(f"  base measures computed for {len(base_measures)} routes")

        # Wipe and recompute every date this run touches - idempotent re-runs.
        await session.execute(text("DELETE FROM core_index_values"))

        index_rows = []
        dates_processed = 0
        for d in sorted(d for d in by_route_day if d >= SPAN_START):
            route_indices = []
            region_indices: dict = defaultdict(list)
            for route_code, fares in by_route_day[d].items():
                base = base_measures.get(route_code)
                if base is None:
                    continue
                measure = compute_route_measure(route_code, fares, Estimator.TRIMMED_MEAN_10)
                if measure is None:
                    continue
                ri = compute_route_index(measure, base.value)
                route_indices.append(ri)
                if route_code in ROUTE_REGION:
                    region_indices[ROUTE_REGION[route_code]].append(ri)

                index_rows.append(
                    CoreIndexValue(
                        date=d,
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
                        CoreIndexValue(
                            date=d,
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
                for region, ris in region_indices.items():
                    region_weights = {ri.route_code: ROUTE_WEIGHTS[ri.route_code] for ri in ris}
                    regional = compute_aggregate_index(ris, region_weights)
                    if regional:
                        index_rows.append(
                            CoreIndexValue(
                                date=d,
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
            dates_processed += 1

        session.add_all(index_rows)
        await session.commit()
        print(f"\nPersisted {len(index_rows)} core_index_values rows across {dates_processed} dates")

        latest = (
            await session.execute(
                text(
                    "SELECT date, index_value FROM core_index_values "
                    "WHERE level='NATIONAL' ORDER BY date DESC LIMIT 3"
                )
            )
        ).all()
        print("\nLatest NATIONAL Core APIx:")
        for d, v in latest:
            print(f"  {d}: {v}")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
