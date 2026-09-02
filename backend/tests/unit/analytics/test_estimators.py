"""Golden-file tests for the robust estimators.

These fix known inputs against known outputs so a future refactor cannot silently
change the index math (build prompt Sec.34, NFR-8).
"""
from __future__ import annotations

from app.analytics import estimators


def test_mean_is_pulled_by_outlier():
    fares = [6000, 6200, 5800, 6100, 25000, 6050, 5950, 6300]
    assert estimators.mean(fares) == 8425.0


def test_trimmed_mean_resists_the_same_outlier():
    """Regression test for D-008: floor(n*0.10)==0 below n=10 used to silently disable
    trimming. This must never happen again."""
    fares = [6000, 6200, 5800, 6100, 25000, 6050, 5950, 6300]
    trimmed = estimators.trimmed_mean(fares)
    assert trimmed == 6100.0
    assert trimmed != estimators.mean(fares)


def test_trimmed_mean_single_value_falls_back_to_median():
    assert estimators.trimmed_mean([6000.0]) == 6000.0


def test_median_unaffected_by_extreme_outlier():
    fares = [6000, 6200, 5800, 6100, 25000, 6050, 5950, 6300]
    assert estimators.median(fares) == 6075.0


def test_weighted_median_with_uniform_weights_matches_median():
    fares = [100.0, 200.0, 300.0, 400.0, 500.0]
    assert estimators.weighted_median(fares) == estimators.median(fares)


def test_weighted_median_shifts_toward_heavier_weight():
    fares = [100.0, 500.0]
    assert estimators.weighted_median(fares, weights=[9.0, 1.0]) == 100.0
    assert estimators.weighted_median(fares, weights=[1.0, 9.0]) == 500.0


def test_all_estimators_returns_all_four_variants():
    result = estimators.all_estimators([100.0, 200.0, 300.0])
    assert set(result) == {"mean_fare", "median_fare", "trimmed_mean_fare", "weighted_median_fare"}


def test_all_estimators_rejects_empty_sample():
    import pytest

    with pytest.raises(ValueError):
        estimators.all_estimators([])


def test_estimator_recomputation_is_deterministic():
    """Reproducibility: the same input always produces the identical output (NFR-8)."""
    fares = [6034.5, 6102.0, 5988.75, 6410.25, 6055.0, 25000.0, 5999.99, 6120.5]
    first = estimators.all_estimators(fares)
    second = estimators.all_estimators(fares)
    assert first == second
