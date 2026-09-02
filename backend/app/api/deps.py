"""Shared request dependencies.

`ResponseContext` resolves the data mode once per request and builds the envelope meta,
so every endpoint reports the mode consistently and no router can forget it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.envelope import Meta
from app.config import settings
from app.data_mode.resolver import describe, resolve
from app.db.repositories import analytics_repository as analytics_repo
from app.db.repositories import fare_repository as fare_repo
from app.db.session import get_session


@dataclass
class ResponseContext:
    data_mode: dict
    sources: list[str]

    def meta(self, **overrides: Any) -> Meta:
        meta = Meta(
            data_mode=self.data_mode["mode"],
            data_mode_label=self.data_mode["label"],
            data_mode_description=self.data_mode["description"],
            is_live=self.data_mode["is_live"],
            sources_included=self.sources,
            quality_threshold=settings.quality_threshold,
            estimator=settings.default_estimator,
        )
        for key, value in overrides.items():
            if value is not None and hasattr(meta, key):
                setattr(meta, key, value)
        return meta


async def get_context(session: AsyncSession = Depends(get_session)) -> ResponseContext:
    latest_scrape = await analytics_repo.latest_scrape_at(session)
    latest_observation = await fare_repo.latest_observation_at(session)
    # No real scrape run means the data came from the seeded dataset, so the mode is
    # REPLAY and the UI badge says so.
    mode = resolve(latest_observation, is_seeded=latest_scrape is None)
    sources = [s.source_code for s in await analytics_repo.sources(session)]
    return ResponseContext(data_mode=describe(mode), sources=sources)
