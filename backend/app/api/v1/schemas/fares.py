"""Fare observation response models (Data Explorer)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FareObservationOut(BaseModel):
    observation_id: int
    observed_at: datetime
    route_code: str
    origin: str
    destination: str
    airline: str
    airline_code: str
    flight_number: str
    departure_datetime: datetime
    lead_days: int
    lead_bucket: str
    fare_class: str
    base_fare: float
    taxes: float
    udf: float
    airport_charges: float
    convenience_fee: float
    total_fare: float
    source: str
    source_type: str
    seats_available: int | None
    availability_status: str
    is_outlier: bool
    imputed_fields: list[str]
    quality_score: float
    quality_band: str


class FareComposition(BaseModel):
    base_fare: float
    taxes: float
    udf: float
    airport_charges: float
    convenience_fee: float
    total_fare: float
    base_fare_pct: float
    taxes_pct: float
    udf_pct: float
    airport_charges_pct: float
    convenience_fee_pct: float
    reconciles: bool
