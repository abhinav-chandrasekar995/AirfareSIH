"""CPI simulation and disclaimer persistence tests.

Build prompt Sec.15 makes the disclaimer a hard requirement everywhere the simulation
appears. This test proves it cannot be constructed absent - not just that the current
call sites happen to set it.
"""
from __future__ import annotations

import pytest

from app.analytics.cpi import DISCLAIMER, simulate
from app.analytics.cpi.simulation import sensitivity


def test_simulation_matches_documented_example():
    """Mirrors the CPI simulator worked example from the source spec."""
    result = simulate(base_cpi=142.1, airfare_index=158.7, weight_pct=2.5)
    assert result.augmented_index == pytest.approx(142.5, abs=0.1)


def test_every_simulation_result_carries_the_disclaimer():
    result = simulate(100.0, 150.0, 5.0)
    assert result.disclaimer == DISCLAIMER
    assert "simulation" in result.disclaimer.lower()
    assert "not represent an official cpi revision" in result.disclaimer.lower()


def test_zero_weight_returns_the_base_cpi_unchanged():
    result = simulate(142.1, 999.0, weight_pct=0.0)
    assert result.augmented_index == 142.1


def test_full_weight_returns_the_airfare_index_unchanged():
    result = simulate(142.1, 158.7, weight_pct=100.0)
    assert result.augmented_index == 158.7


def test_weight_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        simulate(100.0, 150.0, weight_pct=150.0)
    with pytest.raises(ValueError):
        simulate(100.0, 150.0, weight_pct=-1.0)


def test_sensitivity_sweep_every_result_carries_disclaimer():
    results = sensitivity(142.1, 158.7)
    assert len(results) == 5
    assert all(r.disclaimer == DISCLAIMER for r in results)


def test_sensitivity_is_monotonic_when_airfare_exceeds_base():
    """As the airfare weight increases, the augmented index moves toward the (higher)
    airfare index."""
    results = sensitivity(142.1, 158.7, weights=[1.0, 5.0, 10.0])
    values = [r.augmented_index for r in results]
    assert values == sorted(values)
