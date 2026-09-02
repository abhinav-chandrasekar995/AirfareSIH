"""Index and methodology response models."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class IndexPoint(BaseModel):
    date: date
    level: str
    scope: str
    index_value: float
    n_observations: int
    estimator: str
    weight: float | None = None
    notes: str | None = None


class IndexSummary(BaseModel):
    scope: str
    level: str
    current_value: float
    previous_value: float | None = None
    change_pct: float | None = None
    change_direction: str = "flat"
    base_period: date
    as_of: date
    n_observations: int


class EstimatorVariants(BaseModel):
    mean_fare: float | None = None
    median_fare: float | None = None
    trimmed_mean_fare: float | None = None
    weighted_median_fare: float | None = None


class MethodologyResponse(BaseModel):
    """Everything a reader needs to reproduce an index value by hand."""

    methodology_version: str
    base_period: date
    estimator: str
    quality_threshold: float
    min_observations_per_period: int
    weight_set_version: str | None
    weight_source: str | None
    route_index_formula: str
    aggregate_formula: str
    missing_route_policy: str
    basket_size: int
    weights: list[dict]
