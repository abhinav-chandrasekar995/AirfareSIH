"""Shared query parameter models."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.core.constants import Granularity

MAX_PAGE_SIZE = 500


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class DateRange(BaseModel):
    date_from: date | None = None
    date_to: date | None = None


class SeriesPoint(BaseModel):
    date: date
    value: float
    n_observations: int | None = None


class GranularityParam(BaseModel):
    granularity: Granularity = Granularity.DAILY
