"""Quality-scoring tests: the eight-factor model, bands, and threshold behaviour."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.constants import QualityBand
from app.pipeline.quality_score import score_observation


def _good_observation(**overrides):
    now = datetime.now(timezone.utc)
    base = dict(
        route_code="DEL-BOM", airline_code="6E", flight_number="6E-2134",
        departure_datetime=now + timedelta(days=15), observed_at=now,
        base_fare=5400, taxes=1120, udf=480, airport_charges=390, convenience_fee=210,
        total_fare=7600, seats_available=7, availability_status="AVAILABLE",
    )
    base.update(overrides)
    return base


def test_clean_observation_scores_high_confidence():
    result = score_observation(_good_observation(), source_reliability=100.0, known_routes={"DEL-BOM"})
    assert result.band == QualityBand.HIGH
    assert result.score >= 85


def test_duplicate_observation_is_penalised():
    clean = score_observation(_good_observation(), is_duplicate=False)
    dup = score_observation(_good_observation(), is_duplicate=True)
    assert dup.score < clean.score
    assert dup.factors["duplicate_status"] == 0.0


def test_future_observed_at_scores_zero_on_timestamp_validity():
    future = datetime.now(timezone.utc) + timedelta(days=5)
    result = score_observation(_good_observation(observed_at=future))
    assert result.factors["timestamp_validity"] == 0.0


def test_departure_before_observation_scores_zero_on_timestamp_validity():
    now = datetime.now(timezone.utc)
    result = score_observation(_good_observation(observed_at=now, departure_datetime=now - timedelta(days=1)))
    assert result.factors["timestamp_validity"] == 0.0


def test_fare_component_mismatch_lowers_tax_consistency():
    mismatched = _good_observation(total_fare=9999)  # components sum to 7600
    result = score_observation(mismatched)
    assert result.factors["tax_consistency"] < 1.0
    assert any("reconcile" in n or "differ" in n for n in result.notes)


def test_missing_required_fields_lowers_completeness():
    incomplete = _good_observation(flight_number=None)
    result = score_observation(incomplete)
    assert result.factors["completeness"] < 1.0


def test_route_outside_basket_scores_partial_validity():
    result = score_observation(_good_observation(), known_routes={"BOM-BLR"})
    assert result.factors["route_validity"] == 0.5


def test_malformed_route_code_scores_zero_validity():
    result = score_observation(_good_observation(route_code="INVALID"))
    assert result.factors["route_validity"] == 0.0


def test_implausible_fare_is_penalised():
    result = score_observation(_good_observation(total_fare=500, base_fare=400))
    assert result.factors["fare_consistency"] < 1.0


def test_sold_out_with_available_seats_is_inconsistent():
    result = score_observation(_good_observation(availability_status="SOLD_OUT", seats_available=12))
    assert result.factors["availability_validity"] < 1.0


def test_quality_bands_boundaries():
    assert QualityBand.from_score(85) == QualityBand.HIGH
    assert QualityBand.from_score(84.99) == QualityBand.MEDIUM
    assert QualityBand.from_score(60) == QualityBand.MEDIUM
    assert QualityBand.from_score(59.99) == QualityBand.LOW
