"""Stage 2.3 - Deduplication on the observation natural key."""
from __future__ import annotations

from datetime import datetime

# Observations within the same 15-minute bucket are treated as the same quote; sources
# frequently re-serve an identical fare within a single collection window.
BUCKET_MINUTES = 15


def natural_key(
    source_code: str,
    route_code: str,
    flight_number: str,
    departure_datetime: datetime,
    fare_class: str,
    observed_at: datetime,
) -> str:
    bucket = observed_at.replace(
        minute=(observed_at.minute // BUCKET_MINUTES) * BUCKET_MINUTES,
        second=0,
        microsecond=0,
    )
    return "|".join(
        [
            source_code,
            route_code,
            flight_number,
            departure_datetime.isoformat(),
            fare_class,
            bucket.isoformat(),
        ]
    )


def find_duplicates(keys: list[str]) -> set[int]:
    """Indices of entries whose key was already seen earlier in the batch."""
    seen: set[str] = set()
    duplicates: set[int] = set()
    for i, key in enumerate(keys):
        if key in seen:
            duplicates.add(i)
        seen.add(key)
    return duplicates
