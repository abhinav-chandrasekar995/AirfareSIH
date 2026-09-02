"""Stage 2 orchestrator: the fixed seven-step cleaning chain.

The order is not configurable. Each step assumes the previous one has run - scoring a
fare before normalisation, for instance, would penalise a perfectly good observation for
formatting. Keeping the sequence fixed and in one place is what makes the pipeline
reproducible (build prompt Sec.4).

    1 schema validation -> 2 normalisation -> 3 deduplication -> 4 missing values
    -> 5 outlier detection -> 6 fare decomposition -> 7 quality scoring
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.constants import LeadBucket, QualityBand
from app.pipeline import decompose, deduplicate, impute, normalise, outliers, quality_score
from app.pipeline.validate import validate_payload

PIPELINE_VERSION = "pipe-1.0.0"


@dataclass
class CleanedObservation:
    """One fully-processed observation, ready for the analytical table."""

    source_code: str
    route_code: str
    airline_code: str
    flight_number: str
    departure_datetime: object
    observed_at: object
    lead_days: int
    lead_bucket: str
    fare_class: str
    base_fare: float
    taxes: float
    udf: float
    airport_charges: float
    convenience_fee: float
    total_fare: float
    currency: str
    seats_available: int | None
    availability_status: str
    is_outlier: bool
    imputed_fields: list[str]
    quality_score: float
    quality_band: str
    quality_factors: dict
    pipeline_version: str = PIPELINE_VERSION


@dataclass
class PipelineResult:
    cleaned: list[CleanedObservation] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def run_pipeline(
    payloads: list[dict],
    source_reliability: dict[str, float] | None = None,
    known_routes: set[str] | None = None,
) -> PipelineResult:
    """Process a batch of raw payloads through all seven stages."""
    source_reliability = source_reliability or {}
    result = PipelineResult()

    # --- 1. Schema validation -------------------------------------------------
    validated = []
    for payload in payloads:
        observation, error = validate_payload(payload)
        if observation is None:
            result.rejected.append({"payload": payload, "stage": "validation", "reason": error})
        else:
            validated.append(observation)

    # --- 2. Normalisation -----------------------------------------------------
    normalised: list[dict] = []
    for obs in validated:
        route_code = normalise.normalise_route_code(obs.origin, obs.destination)
        flight_number = normalise.normalise_flight_number(obs.flight_number)
        observed_at = normalise.normalise_timestamp(obs.observed_at)
        departure = normalise.normalise_timestamp(obs.departure_datetime)
        total = normalise.normalise_currency(obs.total_fare, obs.currency)

        if not all([route_code, flight_number, observed_at, departure, total]):
            result.rejected.append(
                {
                    "payload": obs.model_dump(),
                    "stage": "normalisation",
                    "reason": "route, flight, timestamp or currency could not be normalised",
                }
            )
            continue

        lead_days = normalise.compute_lead_days(observed_at, departure)
        bucket = LeadBucket.from_lead_days(lead_days)
        if bucket is None:
            # Outside the five collection windows: valid data, but not comparable
            # against the lead-time curve, so it is not admitted to the index.
            result.rejected.append(
                {
                    "payload": obs.model_dump(),
                    "stage": "normalisation",
                    "reason": f"lead time {lead_days}d does not map to a collection window",
                }
            )
            continue

        normalised.append(
            {
                "source_code": obs.source_code,
                "route_code": route_code,
                "airline_code": obs.airline_code,
                "flight_number": flight_number,
                "departure_datetime": departure,
                "observed_at": observed_at,
                "lead_days": lead_days,
                "lead_bucket": bucket.value,
                "fare_class": normalise.normalise_fare_class(obs.fare_class).value,
                "base_fare": normalise.normalise_currency(obs.base_fare, obs.currency) or 0.0,
                "taxes": normalise.normalise_currency(obs.taxes, obs.currency) or 0.0,
                "udf": normalise.normalise_currency(obs.udf, obs.currency) or 0.0,
                "airport_charges": normalise.normalise_currency(obs.airport_charges, obs.currency) or 0.0,
                "convenience_fee": normalise.normalise_currency(obs.convenience_fee, obs.currency) or 0.0,
                "total_fare": total,
                "currency": "INR",
                "seats_available": obs.seats_available,
                "availability_status": normalise.normalise_availability(
                    obs.availability_status, obs.seats_available
                ).value,
            }
        )

    # --- 3. Deduplication -----------------------------------------------------
    keys = [
        deduplicate.natural_key(
            o["source_code"], o["route_code"], o["flight_number"],
            o["departure_datetime"], o["fare_class"], o["observed_at"],
        )
        for o in normalised
    ]
    duplicate_indices = deduplicate.find_duplicates(keys)

    # --- 4. Missing-value handling -------------------------------------------
    imputed_batch: list[tuple[dict, list[str]]] = [impute.impute_components(o) for o in normalised]

    # --- 5. Outlier detection (within route groups) --------------------------
    outlier_flags: dict[int, bool] = {}
    by_route: dict[str, list[int]] = {}
    for i, (obs, _) in enumerate(imputed_batch):
        by_route.setdefault(obs["route_code"], []).append(i)
    for indices in by_route.values():
        fares = [float(imputed_batch[i][0]["total_fare"]) for i in indices]
        for idx, is_outlier in zip(indices, outliers.flag_outliers(fares), strict=True):
            outlier_flags[idx] = is_outlier

    # --- 6 & 7. Decomposition and quality scoring ----------------------------
    for i, (obs, imputed_fields) in enumerate(imputed_batch):
        reconciles, drift = decompose.reconcile(obs)
        quality = quality_score.score_observation(
            {**obs, "airline_code": obs["airline_code"]},
            source_reliability=source_reliability.get(obs["source_code"], 100.0),
            is_duplicate=i in duplicate_indices,
            known_routes=known_routes,
        )
        if not reconciles:
            quality.notes.append(f"fare components drift {drift * 100:.1f}% from total")

        result.cleaned.append(
            CleanedObservation(
                source_code=obs["source_code"],
                route_code=obs["route_code"],
                airline_code=obs["airline_code"],
                flight_number=obs["flight_number"],
                departure_datetime=obs["departure_datetime"],
                observed_at=obs["observed_at"],
                lead_days=obs["lead_days"],
                lead_bucket=obs["lead_bucket"],
                fare_class=obs["fare_class"],
                base_fare=obs["base_fare"],
                taxes=obs["taxes"],
                udf=obs["udf"],
                airport_charges=obs["airport_charges"],
                convenience_fee=obs["convenience_fee"],
                total_fare=obs["total_fare"],
                currency=obs["currency"],
                seats_available=obs["seats_available"],
                availability_status=obs["availability_status"],
                is_outlier=outlier_flags.get(i, False),
                imputed_fields=imputed_fields,
                quality_score=quality.score,
                quality_band=quality.band.value,
                quality_factors=quality.factors,
            )
        )

    result.stats = {
        "received": len(payloads),
        "validated": len(validated),
        "normalised": len(normalised),
        "duplicates": len(duplicate_indices),
        "outliers_flagged": sum(1 for v in outlier_flags.values() if v),
        "cleaned": len(result.cleaned),
        "rejected": len(result.rejected),
        "high_confidence": sum(
            1 for c in result.cleaned if c.quality_band == QualityBand.HIGH.value
        ),
        "pipeline_version": PIPELINE_VERSION,
    }
    return result
