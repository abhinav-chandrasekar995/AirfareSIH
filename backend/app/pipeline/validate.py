"""Stage 2.1 - Schema validation of raw adapter payloads."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RawFareObservation(BaseModel):
    """The contract every source adapter must produce. Anything that fails to parse
    here is rejected before it can reach the analytical tables."""

    source_code: str
    origin: str
    destination: str
    airline_code: str
    flight_number: str
    departure_datetime: datetime
    observed_at: datetime

    base_fare: float = Field(gt=0)
    taxes: float = Field(default=0, ge=0)
    udf: float = Field(default=0, ge=0)
    airport_charges: float = Field(default=0, ge=0)
    convenience_fee: float = Field(default=0, ge=0)
    total_fare: float = Field(gt=0)
    currency: str = "INR"

    fare_class: str = "ECONOMY"
    seats_available: int | None = Field(default=None, ge=0)
    availability_status: str | None = None

    @field_validator("origin", "destination", "airline_code")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("destination")
    @classmethod
    def _distinct(cls, v: str, info) -> str:
        if v == (info.data.get("origin") or ""):
            raise ValueError("origin and destination must differ")
        return v


def validate_payload(payload: dict) -> tuple[RawFareObservation | None, str | None]:
    """Return the validated observation, or None plus the reason it was rejected."""
    try:
        return RawFareObservation(**payload), None
    except Exception as exc:
        return None, str(exc)
