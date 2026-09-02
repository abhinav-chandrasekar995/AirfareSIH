"""Response models for the analytical modules."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, model_validator


class RouteSummary(BaseModel):
    route_code: str
    origin: str
    destination: str
    origin_city: str
    destination_city: str
    region: str
    distance_km: float | None
    in_basket: bool
    weight: float | None = None
    current_fare: float | None = None
    avg_7d: float | None = None
    avg_30d: float | None = None
    avg_yearly: float | None = None
    route_index: float | None = None
    change_mom_pct: float | None = None
    change_yoy_pct: float | None = None
    volatility_score: str | None = None
    n_observations: int = 0


class Mover(BaseModel):
    route_code: str
    origin_city: str
    destination_city: str
    current_fare: float
    change_pct: float
    direction: str


class LeadTimePointOut(BaseModel):
    lead_bucket: str
    lead_days: int
    avg_fare: float
    n_observations: int
    vs_earliest_pct: float | None = None


class LeadTimeResponse(BaseModel):
    route_code: str | None
    curve: list[LeadTimePointOut]
    elasticity: float | None
    last_minute_premium_pct: float | None
    early_booking_advantage_pct: float | None
    booking_pressure: str | None
    method_note: str


class FactorOut(BaseModel):
    factor: str
    label: str
    pct: float


class AnomalyOut(BaseModel):
    anomaly_id: int
    route_code: str
    origin_city: str
    destination_city: str
    detected_at: datetime
    expected_fare: float
    observed_fare: float
    deviation_pct: float
    severity: str
    anomaly_class: str
    lead_bucket: str | None
    detectors_fired: list[str]
    factor_attribution: list[FactorOut]
    attribution_note: str
    status: str
    model_version: str


class ForecastPoint(BaseModel):
    forecast_date: date
    prediction: float
    lower_bound: float
    upper_bound: float

    @model_validator(mode="after")
    def _bounds_required(self) -> ForecastPoint:
        """A point forecast without an interval overstates certainty; the schema
        refuses to serialise one (build prompt Sec.17)."""
        if not (self.lower_bound <= self.prediction <= self.upper_bound):
            raise ValueError("forecast bounds must bracket the prediction")
        return self


class ModelScoreOut(BaseModel):
    model_name: str
    validation_mape: float
    validation_rmse: float
    selected: bool


class ForecastResponse(BaseModel):
    scope: str
    horizon_days: int
    confidence_level: float
    pressure_band: str
    forecast_range: list[float]
    points: list[ForecastPoint]
    model_name: str
    model_version: str
    model_comparison: list[ModelScoreOut]


class BacktestResponse(BaseModel):
    backtest_id: int
    run_at: datetime
    route_scope: str
    estimator: str
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    n_test_days: int
    mae: float | None
    rmse: float | None
    mape: float | None
    correlation: float | None
    directional_accuracy: float | None
    dgca_vintage: str
    alignment_method: str
    series: list[dict]
    estimator_comparison: list[dict] = []


class CpiSimulationResponse(BaseModel):
    period_month: date
    base_cpi: float
    cpi_vintage: str
    cpi_base_year: str
    airfare_index: float
    airfare_weight_pct: float
    augmented_index: float
    delta: float
    formula: str
    sensitivity: list[dict]


class VolatilityOut(BaseModel):
    route_code: str
    date: date
    window_days: int
    std_dev: float | None
    coefficient_of_variation: float | None
    price_range_min: float | None
    price_range_max: float | None
    abnormal_move_frequency: float | None
    volatility_score: str | None


class SourceDivergence(BaseModel):
    source: str
    source_type: str
    avg_fare: float
    vs_direct_pct: float | None
    avg_convenience_fee: float
    n_observations: int


class DataQualitySource(BaseModel):
    source_code: str
    source_name: str
    source_type: str
    status: str
    reliability_score: float
    last_run_at: datetime | None
    records_found: int
    records_valid: int
    records_failed: int
    success_rate: float
    latency_ms: int | None
    rate_limit_rpm: int


class DataQualityFlagOut(BaseModel):
    flag_id: int
    raised_at: datetime
    scope_type: str
    scope_ref: str
    flag_type: str
    severity: str
    description: str
    resolved_at: datetime | None


class InsightOut(BaseModel):
    """Dashboard insight generated from computed statistics, never hand-written text."""

    id: str
    text: str
    severity: str
    href: str | None = None
    metric: float | None = None


class DashboardResponse(BaseModel):
    index_value: float | None
    index_change_mom_pct: float | None
    routes_tracked: int
    airlines_tracked: int
    ota_sources: int
    flights_monitored: int
    total_data_points: int
    base_period: date
    as_of: date | None
    top_increases: list[Mover]
    top_decreases: list[Mover]
    insights: list[InsightOut]
    pressure_map: list[dict]
