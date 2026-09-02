"""Data-mode resolution.

The UI must never present replayed data as live (build prompt Sec.33). The mode is
decided server-side from the age of the newest observation and attached to every API
response, so the badge the user sees is derived from the data rather than from a
frontend constant somebody might forget to update.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.config import settings
from app.core.constants import DataMode

MODE_LABELS = {
    DataMode.LIVE: "Live data",
    DataMode.CACHED: "Cached data",
    DataMode.REPLAY: "Demo data (replayed dataset)",
}

MODE_DESCRIPTIONS = {
    DataMode.LIVE: "Collected from live sources within the freshness window.",
    DataMode.CACHED: "Served from stored observations; live collection is stale or paused.",
    DataMode.REPLAY: (
        "Served from a deterministic seeded dataset for demonstration. "
        "These values are reproducible and are not live market observations."
    ),
}


def resolve(latest_observation_at: datetime | None, is_seeded: bool = False) -> DataMode:
    if settings.force_data_mode:
        return DataMode(settings.force_data_mode)
    if is_seeded or latest_observation_at is None:
        return DataMode.REPLAY
    age = datetime.now(UTC) - latest_observation_at
    return DataMode.LIVE if age <= timedelta(hours=settings.live_freshness_hours) else DataMode.CACHED


def describe(mode: DataMode) -> dict:
    return {
        "mode": mode.value,
        "label": MODE_LABELS[mode],
        "description": MODE_DESCRIPTIONS[mode],
        "is_live": mode == DataMode.LIVE,
    }
