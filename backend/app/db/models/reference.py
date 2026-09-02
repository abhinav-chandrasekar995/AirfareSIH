"""Reference / master tables: airports, airlines, routes, weights, sources, events,
and the external benchmark series (DGCA, CPI)."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Airport(Base):
    __tablename__ = "airports"

    airport_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "region IN ('NORTH','SOUTH','EAST','WEST','NORTHEAST','CENTRAL')",
            name="chk_airport_region",
        ),
    )


class Airline(Base):
    __tablename__ = "airlines"

    airline_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    airline_type: Mapped[str] = mapped_column(String(20), default="LCC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Route(Base):
    __tablename__ = "routes"

    route_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_code: Mapped[str] = mapped_column(String(9), unique=True, nullable=False, index=True)
    origin_id: Mapped[int] = mapped_column(ForeignKey("airports.airport_id"), nullable=False)
    destination_id: Mapped[int] = mapped_column(ForeignKey("airports.airport_id"), nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Numeric(7, 1))
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    in_basket: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    origin: Mapped[Airport] = relationship(foreign_keys=[origin_id], lazy="selectin")
    destination: Mapped[Airport] = relationship(foreign_keys=[destination_id], lazy="selectin")

    __table_args__ = (
        CheckConstraint("origin_id <> destination_id", name="chk_route_distinct"),
        UniqueConstraint("origin_id", "destination_id", name="uq_route_pair"),
    )


class RouteWeight(Base):
    """Versioned DGCA passenger-traffic-derived weights."""

    __tablename__ = "route_weights"

    weight_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    weight_set_version: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.route_id"), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    source_description: Mapped[str] = mapped_column(String(200), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    route: Mapped[Route] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("weight_set_version", "route_id", name="uq_weight_version_route"),
        CheckConstraint("weight > 0 AND weight <= 1", name="chk_weight_range"),
    )


class Source(Base):
    __tablename__ = "sources"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    base_url: Mapped[str] = mapped_column(String(300), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(20), nullable=False)
    robots_txt_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    reliability_score: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("source_type IN ('AIRLINE_DIRECT','OTA')", name="chk_source_type"),
        CheckConstraint(
            "status IN ('ACTIVE','DEGRADED','UNAVAILABLE','DISABLED')", name="chk_source_status"
        ),
    )


class Event(Base):
    """Festival / holiday / seasonal calendar feeding anomaly and forecast features."""

    __tablename__ = "events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    affected_regions: Mapped[list[str] | None] = mapped_column(ARRAY(String(20)))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (CheckConstraint("end_date >= start_date", name="chk_event_dates"),)


class DgcaBenchmark(Base):
    """Publicly available DGCA monthly average fares - the external validation series."""

    __tablename__ = "dgca_benchmarks"

    benchmark_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("routes.route_id"))
    period_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    avg_fare: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    publication_ref: Mapped[str] = mapped_column(String(200), nullable=False)
    vintage: Mapped[str] = mapped_column(String(20), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("route_id", "period_month", "vintage", name="uq_dgca_route_month"),
    )


class CpiReference(Base):
    """MoSPI CPI reference series.

    Vintage and base year are mandatory columns, not optional metadata: silently mixing
    a 2012-base and a 2024-base series would be a material statistical error, so the
    schema makes it impossible to store a CPI figure without saying which series it is
    (build prompt Sec.15).
    """

    __tablename__ = "cpi_reference"

    cpi_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_vintage: Mapped[str] = mapped_column(String(20), nullable=False)
    base_year: Mapped[str] = mapped_column(String(9), nullable=False)
    weight_source: Mapped[str] = mapped_column(String(100), nullable=False)
    coicop_version: Mapped[str | None] = mapped_column(String(20))
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    cpi_general: Mapped[float | None] = mapped_column(Numeric(8, 2))
    cpi_transport_communication: Mapped[float | None] = mapped_column(Numeric(8, 2))
    airfare_sub_index: Mapped[float | None] = mapped_column(Numeric(8, 2))
    airfare_weight_pct: Mapped[float | None] = mapped_column(Numeric(5, 3))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("series_vintage", "period_month", name="uq_cpi_vintage_month"),
    )


class MethodologyVersion(Base):
    """Every published statistic references one of these rows, so any number on screen
    can be traced to the exact configuration that produced it."""

    __tablename__ = "methodology_versions"

    version: Mapped[str] = mapped_column(String(20), primary_key=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimator_default: Mapped[str] = mapped_column(String(20), nullable=False)
    quality_threshold: Mapped[float] = mapped_column(Numeric(5, 2), default=60, nullable=False)
    min_observations_per_period: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    base_period: Mapped[date] = mapped_column(Date, nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text)
