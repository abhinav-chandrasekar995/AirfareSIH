"""End-to-end test of the fixed seven-step cleaning pipeline (in-process, no DB)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.pipeline.pipeline_runner import run_pipeline


def _payload(**overrides):
    now = datetime.now(timezone.utc)
    base = dict(
        source_code="makemytrip", origin="del", destination="bom", airline_code="6E",
        flight_number="6E 2134", departure_datetime=now + timedelta(days=15), observed_at=now,
        base_fare=5400, taxes=1120, udf=480, airport_charges=390, convenience_fee=210,
        total_fare=7600, currency="INR", fare_class="economy", seats_available=7,
    )
    base.update(overrides)
    return base


def test_valid_payload_produces_one_high_quality_observation():
    result = run_pipeline([_payload()], known_routes={"DEL-BOM"})
    assert len(result.cleaned) == 1
    assert result.cleaned[0].route_code == "DEL-BOM"
    assert result.cleaned[0].lead_bucket == "T15"
    assert result.cleaned[0].quality_band == "HIGH"


def test_negative_total_fare_is_rejected_at_validation():
    result = run_pipeline([_payload(total_fare=-100)])
    assert len(result.cleaned) == 0
    assert result.rejected[0]["stage"] == "validation"


def test_same_origin_and_destination_is_rejected():
    result = run_pipeline([_payload(destination="DEL")])
    assert len(result.cleaned) == 0


def test_duplicate_within_the_same_batch_is_flagged():
    payload = _payload()
    result = run_pipeline([payload, dict(payload)])
    assert len(result.cleaned) == 2
    # One of the two carries the duplicate penalty.
    scores = sorted(c.quality_score for c in result.cleaned)
    assert scores[0] < scores[1]


def test_lead_time_outside_the_five_windows_is_rejected():
    """Only T+1/7/15/30/45 (+/-2 days) are admitted - build prompt Sec.10 lead-time
    windows are fixed, not arbitrary."""
    off_window = _payload(departure_datetime=datetime.now(timezone.utc) + timedelta(days=22))
    result = run_pipeline([off_window])
    assert len(result.cleaned) == 0
    assert any("lead time" in r["reason"] for r in result.rejected)


def test_raw_is_never_mutated_by_the_pipeline():
    """The pipeline must not overwrite raw payloads (build prompt Sec.4) - this test
    asserts the input list is untouched after processing."""
    payload = _payload()
    original = dict(payload)
    run_pipeline([payload])
    assert payload == original


def test_pipeline_stats_reflect_every_batch_outcome():
    payloads = [_payload(), _payload(total_fare=-5), dict(_payload())]
    result = run_pipeline(payloads)
    assert result.stats["received"] == 3
    assert result.stats["rejected"] >= 1
    assert result.stats["cleaned"] + result.stats["rejected"] <= result.stats["received"]
