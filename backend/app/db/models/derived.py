"""Derived statistical products: the numbers the platform actually publishes.

Every table here carries a version column (`methodology_version` or `model_version`)
so a value displayed today remains interpretable after the methodology changes.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.reference import Route


class IndexValue(Base):
    """A published index number at one level (national/regional/route/airline).

    All four estimator variants are stored alongside the chosen one (ADR-006), so the
    Backtesting Lab can compare methodologies retroactively without recomputation.
    """

    __tablename__ = "index_values"

    index_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    index_value: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    base_period: Mapped[date] = mapped_column(Date, nullable=False)
    weight: Mapped[float | None] = mapped_column(Numeric(6, 4))

    estimator: Mapped[str] = mapped_column(String(20), nullable=False)
    mean_fare: Mapped[float | None] = mapped_column(Numeric(10, 2))
    median_fare: Mapped[float | None] = mapped_column(Numeric(10, 2))
    trimmed_mean_fare: Mapped[float | None] = mapped_column(Numeric(10, 2))
    weighted_median_fare: Mapped[float | None] = mapped_column(Numeric(10, 2))

    n_observations: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_set_version: Mapped[str | None] = mapped_column(String(30))
    methodology_version: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("date", "level", "scope", "methodology_version", name="uq_index_value"),
        CheckConstraint(
            "level IN ('NATIONAL','REGIONAL','ROUTE','AIRLINE')", name="chk_index_level"
        ),
        Index("idx_index_values_lookup", "level", "scope", "date"),
    )


class LeadTimeCurve(Base):
    __tablename__ = "leadtime_curves"

    curve_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("routes.route_id"), index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    lead_bucket: Mapped[str] = mapped_column(String(4), nullable=False)
    avg_fare: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    n_observations: Mapped[int] = mapped_column(Integer, nullable=False)
    elasticity: Mapped[float | None] = mapped_column(Numeric(6, 4))
    last_minute_premium_pct: Mapped[float | None] = mapped_column(Numeric(8, 2))
    booking_pressure: Mapped[str | None] = mapped_column(String(10))
    methodology_version: Mapped[str] = mapped_column(String(20), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    route: Mapped[Route | None] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "route_id", "date", "lead_bucket", "methodology_version", name="uq_leadtime"
        ),
    )


class VolatilityMetric(Base):
    __tablename__ = "volatility_metrics"

    volatility_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.route_id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    std_dev: Mapped[float | None] = mapped_column(Numeric(10, 2))
    coefficient_of_variation: Mapped[float | None] = mapped_column(Numeric(6, 4))
    price_range_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    price_range_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    abnormal_move_frequency: Mapped[float | None] = mapped_column(Numeric(5, 2))
    volatility_score: Mapped[str | None] = mapped_column(String(10))
    methodology_version: Mapped[str] = mapped_column(String(20), nullable=False)

    route: Mapped[Route] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "route_id", "date", "window_days", "methodology_version", name="uq_volatility"
        ),
    )


class Anomaly(Base):
    """A detected deviation from the expected-fare baseline.

    `anomaly_class` separates MARKET from SCRAPER. Conflating the two would let a
    parser failure be published as a price surge, which is the most damaging error
    this platform could make (build prompt Sec.11).
    """

    __tablename__ = "anomalies"

    anomaly_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.route_id"), nullable=False, index=True)
    observation_id: Mapped[int | None] = mapped_column(BigInteger)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    fare_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fare_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    expected_fare: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    observed_fare: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deviation_pct: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    lead_bucket: Mapped[str | None] = mapped_column(String(4))

    detectors_fired: Mapped[list[str] | None] = mapped_column(ARRAY(String(30)))
    anomaly_class: Mapped[str] = mapped_column(String(20), default="MARKET", nullable=False)

    factor_attribution: Mapped[list | None] = mapped_column(JSONB)
    attribution_note: Mapped[str] = mapped_column(String(200), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)

    route: Mapped[Route] = relationship(lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="chk_anomaly_severity"
        ),
        CheckConstraint("anomaly_class IN ('MARKET','SCRAPER')", name="chk_anomaly_class"),
        CheckConstraint(
            "status IN ('OPEN','ACKNOWLEDGED','RESOLVED','FALSE_POSITIVE')",
            name="chk_anomaly_status",
        ),
    )


class Forecast(Base):
    """A forecast row. The bounds are NOT NULL and a CHECK enforces their ordering, so
    the database itself refuses to store a point forecast without an interval."""

    __tablename__ = "forecasts"

    forecast_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)

    prediction: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    lower_bound: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    upper_bound: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    confidence_level: Mapped[float] = mapped_column(Numeric(4, 2), default=0.80, nullable=False)
    pressure_band: Mapped[str | None] = mapped_column(String(10))

    model_name: Mapped[str] = mapped_column(String(40), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    validation_mape: Mapped[float | None] = mapped_column(Numeric(8, 3))

    __table_args__ = (
        CheckConstraint(
            "lower_bound <= prediction AND prediction <= upper_bound", name="chk_forecast_bounds"
        ),
        UniqueConstraint("scope", "forecast_date", "model_version", name="uq_forecast"),
    )


class BacktestRun(Base):
    """One out-of-sample validation of our index against the DGCA benchmark."""

    __tablename__ = "backtest_runs"

    backtest_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    route_scope: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)
    estimator: Mapped[str] = mapped_column(String(20), nullable=False)

    train_start: Mapped[date] = mapped_column(Date, nullable=False)
    train_end: Mapped[date] = mapped_column(Date, nullable=False)
    test_start: Mapped[date] = mapped_column(Date, nullable=False)
    test_end: Mapped[date] = mapped_column(Date, nullable=False)
    n_test_days: Mapped[int] = mapped_column(Integer, nullable=False)

    mae: Mapped[float | None] = mapped_column(Numeric(10, 2))
    rmse: Mapped[float | None] = mapped_column(Numeric(10, 2))
    mape: Mapped[float | None] = mapped_column(Numeric(8, 3))
    correlation: Mapped[float | None] = mapped_column(Numeric(6, 4))
    directional_accuracy: Mapped[float | None] = mapped_column(Numeric(5, 2))

    dgca_vintage: Mapped[str] = mapped_column(String(20), nullable=False)
    alignment_method: Mapped[str] = mapped_column(String(200), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(20), nullable=False)
    series_json: Mapped[list | None] = mapped_column(JSONB)

    # The 30-day floor from the problem statement, enforced by the database.
    __table_args__ = (CheckConstraint("n_test_days >= 30", name="chk_backtest_min_days"),)


class CpiSimulation(Base):
    __tablename__ = "cpi_simulations"

    simulation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    base_cpi: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    cpi_vintage: Mapped[str] = mapped_column(String(20), nullable=False)
    cpi_base_year: Mapped[str] = mapped_column(String(9), nullable=False)
    airfare_index: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    airfare_weight_pct: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    augmented_index: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    scenario_label: Mapped[str | None] = mapped_column(String(60))
    disclaimer: Mapped[str] = mapped_column(String(300), nullable=False)
    created_by_key_id: Mapped[int | None] = mapped_column(BigInteger)
