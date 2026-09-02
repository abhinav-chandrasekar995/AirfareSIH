"""Golden-file tests for the index engine: route measures, route index, national
aggregation, missing-route exclusion, and weight renormalisation."""
from __future__ import annotations

import pytest

from app.analytics.index_engine import (
    compute_aggregate_index,
    compute_route_index,
    compute_route_measure,
)
from app.core.constants import Estimator


def test_route_measure_below_minimum_observations_returns_none():
    measure = compute_route_measure("DEL-BOM", [6000.0, 6100.0], Estimator.MEDIAN, min_observations=5)
    assert measure is None


def test_route_measure_at_minimum_observations_computes():
    fares = [6000.0, 6100.0, 5900.0, 6050.0, 5950.0]
    measure = compute_route_measure("DEL-BOM", fares, Estimator.MEDIAN, min_observations=5)
    assert measure is not None
    assert measure.n_observations == 5
    assert measure.value == 6000.0


def test_route_index_formula():
    fares = [8000.0] * 6
    measure = compute_route_measure("DEL-BOM", fares, Estimator.MEDIAN, 5)
    index = compute_route_index(measure, base_measure=6000.0)
    # (8000 / 6000) * 100 = 133.333...
    assert index.index_value == pytest.approx(133.333, abs=0.01)


def test_route_index_rejects_zero_base():
    fares = [8000.0] * 6
    measure = compute_route_measure("DEL-BOM", fares, Estimator.MEDIAN, 5)
    with pytest.raises(ValueError):
        compute_route_index(measure, base_measure=0.0)


def test_aggregate_index_is_weighted_average_of_route_indices():
    idx_a = compute_route_index(compute_route_measure("A-B", [12000.0] * 6, Estimator.MEDIAN, 5), 10000.0)
    idx_b = compute_route_index(compute_route_measure("C-D", [9000.0] * 6, Estimator.MEDIAN, 5), 10000.0)

    agg = compute_aggregate_index([idx_a, idx_b], {"A-B": 0.6, "C-D": 0.4})
    # A-B index = 120, C-D index = 90 -> 120*0.6 + 90*0.4 = 108
    assert agg.index_value == pytest.approx(108.0, abs=0.01)
    assert agg.excluded == []


def test_aggregate_index_excludes_and_renormalises_missing_routes():
    idx_a = compute_route_index(compute_route_measure("A-B", [12000.0] * 6, Estimator.MEDIAN, 5), 10000.0)
    # Only A-B observed this period; C-D's weight must be dropped and renormalised, and
    # the exclusion recorded rather than silently absorbed (build prompt Sec.12 policy).
    agg = compute_aggregate_index([idx_a], {"A-B": 0.6, "C-D": 0.4})
    assert agg.index_value == pytest.approx(120.0, abs=0.01)
    assert agg.excluded == ["C-D"]
    assert agg.notes is not None and "C-D" in agg.notes
    assert agg.weights_used == {"A-B": 1.0}


def test_aggregate_index_returns_none_when_no_routes_observed():
    assert compute_aggregate_index([], {"A-B": 0.6}) is None


def test_index_recomputation_is_deterministic():
    """Reproducibility (NFR-8): identical inputs always yield an identical index value."""
    fares = [6034.5, 6102.0, 5988.75, 6410.25, 6055.0, 5999.99]
    measure1 = compute_route_measure("DEL-BOM", fares, Estimator.TRIMMED_MEAN_10, 5)
    measure2 = compute_route_measure("DEL-BOM", fares, Estimator.TRIMMED_MEAN_10, 5)
    idx1 = compute_route_index(measure1, 6000.0)
    idx2 = compute_route_index(measure2, 6000.0)
    assert idx1.index_value == idx2.index_value
