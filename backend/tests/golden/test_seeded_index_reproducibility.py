"""Golden-file test: the deterministic seed dataset must reproduce an identical
national index value on every run (fixed RNG seed, build prompt Sec.34/Sec.33).

This is the test that makes the "our demo shows the same numbers every time" claim
(design doc, D-030) checkable rather than asserted. It needs no database - it exercises
the seed generator and the pure analytics engine directly, exactly as
seeds/load_seed.py does internally.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import pytest

from app.analytics.index_engine import compute_aggregate_index, compute_route_index, compute_route_measure
from app.core.constants import Estimator
from seeds.generate_seed import BASE_PERIOD, BASE_WINDOW_DAYS, ROUTES, generate_observations

TODAY = date(2026, 9, 1)
ESTIMATOR = Estimator.TRIMMED_MEAN_10

# Frozen expected value from the first verified run of the seed generator
# (see IMPLEMENTATION_LOG.md D-030/D-031). If this ever legitimately changes because the
# seed generator or the index math changed on purpose, update this constant deliberately
# - a silent change here means the demo numbers drifted between rehearsal and judging.
# Updated after ENGINEERED_ANOMALIES was expanded from one route to six (see
# IMPLEMENTATION_LOG.md, anomaly-engineering entry) - that deliberately changed several
# routes' fare distributions, so the aggregate index shifted along with it.
EXPECTED_NATIONAL_INDEX = 110.218
EXPECTED_ROUTE_COUNT = 15


def _compute_national_index():
    observations = generate_observations(TODAY)
    weights = {r[0]: r[3] for r in ROUTES}

    recent = defaultdict(list)
    base = defaultdict(list)
    for o in observations:
        d = o.observed_at.date()
        if TODAY - timedelta(days=7) <= d <= TODAY:
            recent[o.route_code].append(o.total_fare)
        if BASE_PERIOD <= d <= BASE_PERIOD + timedelta(days=BASE_WINDOW_DAYS):
            base[o.route_code].append(o.total_fare)

    route_indices = []
    for route_code in weights:
        measure = compute_route_measure(route_code, recent[route_code], ESTIMATOR, 5)
        base_measure = compute_route_measure(route_code, base[route_code], ESTIMATOR, 5)
        if measure and base_measure:
            route_indices.append(compute_route_index(measure, base_measure.value))

    return compute_aggregate_index(route_indices, weights)


def test_seed_generator_is_deterministic_across_calls():
    """Same seed, same 'today' -> byte-identical observation set."""
    first = generate_observations(TODAY)
    second = generate_observations(TODAY)
    assert len(first) == len(second)
    assert [o.total_fare for o in first] == [o.total_fare for o in second]


def test_national_index_from_seeded_data_matches_the_frozen_golden_value():
    aggregate = _compute_national_index()
    assert aggregate is not None
    assert aggregate.n_routes == EXPECTED_ROUTE_COUNT
    assert aggregate.index_value == pytest.approx(EXPECTED_NATIONAL_INDEX, abs=0.01)


def test_no_route_is_silently_excluded_from_the_seeded_basket():
    aggregate = _compute_national_index()
    assert aggregate.excluded == []
