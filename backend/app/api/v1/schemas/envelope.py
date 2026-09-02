"""The response envelope every endpoint returns.

    { "data": ..., "meta": {...}, "methodology_version": "...", "disclaimer": null }

`meta.data_mode` is always populated so the frontend badge is derived from the server's
view of the data rather than a client-side constant (build prompt Sec.33).
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.config import settings

T = TypeVar("T")


class Meta(BaseModel):
    count: int = 0
    page: int = 1
    page_size: int = 100
    total: int | None = None
    granularity: str | None = None

    data_mode: str = "REPLAY"
    data_mode_label: str = "Demo data (replayed dataset)"
    data_mode_description: str | None = None
    is_live: bool = False

    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sources_included: list[str] = Field(default_factory=list)
    quality_threshold: float = settings.quality_threshold
    estimator: str | None = None
    notes: str | None = None


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: Meta = Field(default_factory=Meta)
    methodology_version: str = settings.methodology_version
    disclaimer: str | None = None


def envelope(
    data: Any,
    *,
    meta: Meta | None = None,
    disclaimer: str | None = None,
    **meta_overrides: Any,
) -> dict:
    """Build a response envelope. Used by every router so the shape cannot drift."""
    resolved = meta or Meta()
    for key, value in meta_overrides.items():
        if value is not None and hasattr(resolved, key):
            setattr(resolved, key, value)
    if isinstance(data, list) and not resolved.count:
        resolved.count = len(data)
    return {
        "data": data,
        "meta": resolved.model_dump(mode="json"),
        "methodology_version": settings.methodology_version,
        "disclaimer": disclaimer,
    }
